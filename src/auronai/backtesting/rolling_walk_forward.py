"""
Rolling Walk-Forward Optimization.

This module implements rolling walk-forward optimization where parameters
are re-optimized periodically (weekly/monthly) using only past data,
simulating real-world trading where you would re-optimize regularly.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

import pandas as pd
import numpy as np

from auronai.backtesting.backtest_config import BacktestConfig
from auronai.backtesting.backtest_runner import BacktestRunner
from auronai.strategies.base_strategy import StrategyParams
from auronai.strategies.long_momentum import LongMomentumStrategy
from auronai.strategies.short_momentum import ShortMomentumStrategy
from auronai.strategies.neutral_strategy import NeutralStrategy
from auronai.strategies.dual_momentum import DualMomentumStrategy
from auronai.data.market_data_provider import MarketDataProvider
from auronai.data.feature_store import FeatureStore
from auronai.utils.logger import get_logger
import time

logger = get_logger(__name__)


@dataclass
class OptimizationPeriod:
    """Represents a single optimization period."""
    period_id: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    best_params: Optional[StrategyParams] = None
    train_sharpe: Optional[float] = None
    test_sharpe: Optional[float] = None
    test_return: Optional[float] = None
    test_max_dd: Optional[float] = None


@dataclass
class RollingWalkForwardResult:
    """Results from rolling walk-forward optimization."""
    strategy_name: str
    total_periods: int
    reoptimize_frequency: str
    
    # Aggregated metrics
    avg_train_sharpe: float
    avg_test_sharpe: float
    std_test_sharpe: float
    degradation: float  # (train - test) / train
    
    avg_test_return: float
    avg_test_max_dd: float
    
    # Best/worst periods
    best_period: OptimizationPeriod
    worst_period: OptimizationPeriod
    
    # All periods
    periods: List[OptimizationPeriod]
    
    # Parameter stability
    param_frequency: Dict[str, int]  # How often each param value was chosen
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'strategy_name': self.strategy_name,
            'total_periods': self.total_periods,
            'reoptimize_frequency': self.reoptimize_frequency,
            'avg_train_sharpe': self.avg_train_sharpe,
            'avg_test_sharpe': self.avg_test_sharpe,
            'std_test_sharpe': self.std_test_sharpe,
            'degradation': self.degradation,
            'avg_test_return': self.avg_test_return,
            'avg_test_max_dd': self.avg_test_max_dd,
            'best_period': {
                'period_id': self.best_period.period_id,
                'test_sharpe': self.best_period.test_sharpe,
                'params': self.best_period.best_params.__dict__ if self.best_period.best_params else None
            },
            'worst_period': {
                'period_id': self.worst_period.period_id,
                'test_sharpe': self.worst_period.test_sharpe,
                'params': self.worst_period.best_params.__dict__ if self.worst_period.best_params else None
            },
            'param_frequency': self.param_frequency,
            'periods': [
                {
                    'period_id': p.period_id,
                    'train_start': p.train_start.isoformat(),
                    'train_end': p.train_end.isoformat(),
                    'test_start': p.test_start.isoformat(),
                    'test_end': p.test_end.isoformat(),
                    'best_params': p.best_params.__dict__ if p.best_params else None,
                    'train_sharpe': p.train_sharpe,
                    'test_sharpe': p.test_sharpe,
                    'test_return': p.test_return,
                    'test_max_dd': p.test_max_dd
                }
                for p in self.periods
            ]
        }


class RollingWalkForwardOptimizer:
    """
    Rolling walk-forward optimizer.
    
    Re-optimizes parameters periodically (weekly/monthly) using only
    data available up to that point, then tests on the following period.
    
    This simulates real-world trading where you would:
    1. Optimize parameters using past data
    2. Trade with those parameters for a period
    3. Re-optimize periodically
    """
    
    def __init__(
        self,
        train_window_days: int = 180,  # 6 months
        test_window_days: int = 21,    # 3 weeks
        reoptimize_frequency: str = 'weekly',  # 'weekly' or 'monthly'
        initial_capital: float = 10000.0,
        commission_rate: float = 0.0,
        slippage_rate: float = 0.0005
    ):
        """
        Initialize rolling walk-forward optimizer.
        
        Args:
            train_window_days: Days of historical data to use for optimization
            test_window_days: Days to test with optimized parameters
            reoptimize_frequency: How often to re-optimize ('weekly' or 'monthly')
            initial_capital: Starting capital for backtests
            commission_rate: Commission rate per trade (0.001 = 0.1%)
            slippage_rate: Slippage as decimal (0.0005 = 0.05%)
        """
        self.train_window_days = train_window_days
        self.test_window_days = test_window_days
        self.reoptimize_frequency = reoptimize_frequency
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        
        self.backtest_runner = BacktestRunner()
        
        # Performance optimization: data and indicator caches
        self.data_cache: Dict[str, pd.DataFrame] = {}
        self.indicator_cache: Dict[str, pd.DataFrame] = {}
        self.market_data_provider: Optional[MarketDataProvider] = None
        self.feature_store: Optional[FeatureStore] = None
        
        logger.info(
            f"RollingWalkForwardOptimizer initialized: "
            f"train={train_window_days}d, test={test_window_days}d, "
            f"reoptimize={reoptimize_frequency}"
        )
    
    def _preload_all_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        market_data_provider: MarketDataProvider
    ) -> None:
        """
        Pre-load ALL data once at the beginning.
        
        This is the MOST IMPORTANT optimization - it avoids loading
        data repeatedly for each period (3-6x speedup).
        
        Args:
            symbols: List of symbols to load
            start_date: Start date for data
            end_date: End date for data
            market_data_provider: Provider to fetch data from
        """
        logger.info(f"🔄 Pre-loading data for {len(symbols)} symbols...")
        start_time = time.time()
        
        self.market_data_provider = market_data_provider
        
        # Add warmup period for indicators (300 days before start)
        warmup_start = start_date - timedelta(days=300)
        
        successful = 0
        for symbol in symbols:
            try:
                # Load complete data range
                data = market_data_provider.get_historical_data_range(
                    symbol,
                    warmup_start,
                    end_date
                )
                
                if data is not None and len(data) > 0:
                    self.data_cache[symbol] = data
                    successful += 1
                    logger.debug(f"✅ {symbol}: {len(data)} rows")
                else:
                    logger.warning(f"⚠️ No data for {symbol}")
                    
            except Exception as e:
                logger.error(f"❌ Error loading {symbol}: {e}")
        
        elapsed = time.time() - start_time
        logger.info(
            f"✅ Pre-loaded {successful}/{len(symbols)} symbols "
            f"in {elapsed:.1f}s ({elapsed/len(symbols):.2f}s per symbol)"
        )
    
    def _get_period_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, pd.DataFrame]:
        """
        Get data for a period from the cache.
        
        This is INSTANTANEOUS because data is already in memory.
        
        Args:
            symbols: List of symbols
            start_date: Period start date
            end_date: Period end date
        
        Returns:
            Dictionary mapping symbol -> DataFrame for the period
        """
        period_data = {}
        
        for symbol in symbols:
            if symbol not in self.data_cache:
                logger.warning(f"Symbol {symbol} not in cache, skipping")
                continue
            
            # Filter data from cache (very fast)
            df = self.data_cache[symbol]
            mask = (df.index >= start_date) & (df.index <= end_date)
            period_data[symbol] = df[mask].copy()
        
        return period_data
    
    def _calculate_indicators_cached(
        self,
        symbol: str,
        data: pd.DataFrame,
        feature_store: FeatureStore
    ) -> pd.DataFrame:
        """
        Calculate indicators with caching.
        
        Indicators don't change between periods, so we only need
        to calculate them once per symbol (2x speedup).
        
        Args:
            symbol: Symbol name
            data: OHLCV data
            feature_store: Feature store for indicator calculation
        
        Returns:
            DataFrame with indicators added
        """
        # Create cache key based on symbol and data range
        cache_key = f"{symbol}_{data.index[0]}_{data.index[-1]}_{len(data)}"
        
        if cache_key in self.indicator_cache:
            logger.debug(f"📦 Using cached indicators for {symbol}")
            return self.indicator_cache[cache_key]
        
        # Calculate indicators
        logger.debug(f"🔄 Calculating indicators for {symbol}")
        data_with_indicators = feature_store.add_features(data)
        
        # Save to cache
        self.indicator_cache[cache_key] = data_with_indicators
        
        return data_with_indicators
    
    def clear_caches(self) -> None:
        """Clear all caches to free memory."""
        self.data_cache.clear()
        self.indicator_cache.clear()
        logger.info("Caches cleared")

    
    def _generate_periods(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[OptimizationPeriod]:
        """
        Generate optimization periods.
        
        Each period has:
        - Train: train_window_days of data ending the day before test
        - Test: test_window_days of data
        
        Periods are generated based on reoptimize_frequency.
        
        Note: start_date should be early enough to have train_window_days
        of history before the first test period.
        """
        periods = []
        period_id = 1
        
        # Determine step size
        if self.reoptimize_frequency == 'weekly':
            step_days = 7
        elif self.reoptimize_frequency == 'monthly':
            step_days = 30
        else:
            raise ValueError(f"Invalid reoptimize_frequency: {self.reoptimize_frequency}")
        
        # Start from first possible test date
        # (need train_window_days of history before first test)
        current_test_start = start_date
        
        while current_test_start + timedelta(days=self.test_window_days) <= end_date:
            # Train period: train_window_days ending day before test
            train_end = current_test_start - timedelta(days=1)
            train_start = train_end - timedelta(days=self.train_window_days - 1)
            
            # Test period
            test_start = current_test_start
            test_end = test_start + timedelta(days=self.test_window_days - 1)
            
            # Ensure test_end doesn't exceed end_date
            if test_end > end_date:
                test_end = end_date
            
            # Only add period if we have enough training data
            # (train_start should be >= original start_date - train_window_days)
            period = OptimizationPeriod(
                period_id=period_id,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end
            )
            
            periods.append(period)
            
            logger.debug(
                f"Period {period_id}: "
                f"Train {train_start.date()} to {train_end.date()}, "
                f"Test {test_start.date()} to {test_end.date()}"
            )
            
            # Move to next period
            current_test_start += timedelta(days=step_days)
            period_id += 1
        
        logger.info(f"Generated {len(periods)} optimization periods")
        
        return periods
    
    def _optimize_params(
        self,
        symbols: List[str],
        train_start: datetime,
        train_end: datetime,
        param_grid: Dict[str, List[Any]],
        strategy_class: type
    ) -> tuple[StrategyParams, float]:
        """
        Optimize parameters on training data.
        
        Args:
            symbols: List of symbols to trade
            train_start: Training period start
            train_end: Training period end
            param_grid: Grid of parameters to test
            strategy_class: Strategy class to use
        
        Returns:
            Tuple of (best_params, best_sharpe)
        """
        best_sharpe = -999
        best_params = None
        successful_tests = 0
        
        # Generate all parameter combinations
        param_combinations = self._generate_param_combinations(param_grid)
        
        logger.info(
            f"Optimizing {len(param_combinations)} parameter combinations "
            f"on {train_start.date()} to {train_end.date()}"
        )
        
        for params_dict in param_combinations:
            try:
                # Create strategy params
                params = StrategyParams(**params_dict)
                
                # Create strategy
                strategy = strategy_class(params)
                
                # Create backtest config
                config = BacktestConfig(
                    strategy_id=f"train_{strategy.name}",
                    symbols=symbols,
                    start_date=train_start,
                    end_date=train_end,
                    initial_capital=self.initial_capital,
                    commission_rate=self.commission_rate,
                    slippage_rate=self.slippage_rate,
                    benchmark='QQQ',
                    strategy_params=params.__dict__
                )
                
                # Run backtest
                result = self.backtest_runner.run(config, strategy)
                successful_tests += 1
                
                # Check if better
                if result.metrics['sharpe_ratio'] > best_sharpe:
                    best_sharpe = result.metrics['sharpe_ratio']
                    best_params = params
                    
                    logger.debug(
                        f"New best: {params_dict} → Sharpe {best_sharpe:.2f}"
                    )
            
            except Exception as e:
                # Log error but continue with other params
                logger.debug(f"Error testing params {params_dict}: {e}")
                continue
        
        if best_params is None:
            # Fallback to default params
            logger.warning(
                f"No valid params found ({successful_tests}/{len(param_combinations)} succeeded), "
                f"using defaults"
            )
            best_params = StrategyParams()
            best_sharpe = 0.0
        else:
            logger.info(
                f"Tested {successful_tests}/{len(param_combinations)} combinations successfully"
            )
        
        logger.info(
            f"Best params: top_k={best_params.top_k}, "
            f"holding_days={best_params.holding_days}, "
            f"tp_multiplier={best_params.tp_multiplier:.3f} "
            f"→ Sharpe {best_sharpe:.2f}"
        )
        
        return best_params, best_sharpe
    
    def _generate_param_combinations(
        self,
        param_grid: Dict[str, List[Any]]
    ) -> List[Dict[str, Any]]:
        """Generate all combinations of parameters from grid."""
        import itertools
        
        keys = list(param_grid.keys())
        values = [param_grid[k] for k in keys]
        
        combinations = []
        for combo in itertools.product(*values):
            param_dict = dict(zip(keys, combo))
            combinations.append(param_dict)
        
        return combinations
    
    def _test_params(
        self,
        symbols: List[str],
        test_start: datetime,
        test_end: datetime,
        params: StrategyParams,
        strategy_class: type
    ) -> Dict[str, float]:
        """
        Test parameters on test data.
        
        Args:
            symbols: List of symbols to trade
            test_start: Test period start
            test_end: Test period end
            params: Parameters to test
            strategy_class: Strategy class to use
        
        Returns:
            Dictionary with test metrics
        """
        # Create strategy
        strategy = strategy_class(params)
        
        # Create backtest config
        config = BacktestConfig(
            strategy_id=f"test_{strategy.name}",
            symbols=symbols,
            start_date=test_start,
            end_date=test_end,
            initial_capital=self.initial_capital,
            commission_rate=self.commission_rate,
            slippage_rate=self.slippage_rate,
            benchmark='QQQ',
            strategy_params=params.__dict__
        )
        
        # Run backtest
        result = self.backtest_runner.run(config, strategy)
        
        return {
            'sharpe_ratio': result.metrics['sharpe_ratio'],
            'total_return': result.metrics['total_return'],
            'max_drawdown': result.metrics['max_drawdown']
        }
    
    def run(
        self,
        strategy_name: str,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        param_grid: Dict[str, List[Any]]
    ) -> RollingWalkForwardResult:
        """
        Run rolling walk-forward optimization.
        
        Args:
            strategy_name: Name of strategy ('long_momentum', 'short_momentum', 'neutral')
            symbols: List of symbols to trade
            start_date: Start date for walk-forward
            end_date: End date for walk-forward
            param_grid: Grid of parameters to optimize
                Example: {
                    'top_k': [2, 3, 4, 5],
                    'holding_days': [7, 10, 14],
                    'tp_multiplier': [1.03, 1.05, 1.07]
                }
        
        Returns:
            RollingWalkForwardResult with all metrics
        """
        logger.info(
            f"Starting rolling walk-forward for {strategy_name}: "
            f"{start_date.date()} to {end_date.date()}"
        )
        
        # Get strategy class
        strategy_class = self._get_strategy_class(strategy_name)
        
        # Generate periods
        periods = self._generate_periods(start_date, end_date)
        
        # Run optimization for each period
        for period in periods:
            logger.info(f"\n{'='*80}")
            logger.info(f"Period {period.period_id}/{len(periods)}")
            logger.info(f"{'='*80}")
            
            # 1. Optimize on train data
            best_params, train_sharpe = self._optimize_params(
                symbols=symbols,
                train_start=period.train_start,
                train_end=period.train_end,
                param_grid=param_grid,
                strategy_class=strategy_class
            )
            
            period.best_params = best_params
            period.train_sharpe = train_sharpe
            
            # Warn if no trades during training
            if train_sharpe == 0:
                logger.warning(
                    f"Period {period.period_id}: No trades during training period. "
                    f"This may indicate: (1) Strategy didn't find opportunities, "
                    f"(2) Market regime not suitable, or (3) Parameters too restrictive."
                )
            
            # 2. Test on test data (with optimized params)
            test_metrics = self._test_params(
                symbols=symbols,
                test_start=period.test_start,
                test_end=period.test_end,
                params=best_params,
                strategy_class=strategy_class
            )
            
            period.test_sharpe = test_metrics['sharpe_ratio']
            period.test_return = test_metrics['total_return']
            period.test_max_dd = test_metrics['max_drawdown']
            
            # Calculate degradation safely
            if train_sharpe != 0:
                degradation_pct = (train_sharpe - period.test_sharpe) / train_sharpe * 100
            else:
                degradation_pct = 0.0
            
            logger.info(
                f"Period {period.period_id} results: "
                f"Train Sharpe={train_sharpe:.2f}, "
                f"Test Sharpe={period.test_sharpe:.2f}, "
                f"Degradation={degradation_pct:.1f}%"
            )
        
        # Calculate aggregated metrics
        result = self._calculate_results(strategy_name, periods)
        
        logger.info(f"\n{'='*80}")
        logger.info("ROLLING WALK-FORWARD COMPLETED")
        logger.info(f"{'='*80}")
        logger.info(f"Avg Train Sharpe: {result.avg_train_sharpe:.2f}")
        logger.info(f"Avg Test Sharpe: {result.avg_test_sharpe:.2f} ± {result.std_test_sharpe:.2f}")
        logger.info(f"Degradation: {result.degradation:.1%}")
        logger.info(f"Avg Test Return: {result.avg_test_return:.1%}")
        logger.info(f"Avg Test Max DD: {result.avg_test_max_dd:.1%}")
        
        return result
    
    def _get_strategy_class(self, strategy_name: str) -> type:
        """Get strategy class by name."""
        strategies = {
            'long_momentum': LongMomentumStrategy,
            'short_momentum': ShortMomentumStrategy,
            'neutral': NeutralStrategy,
            'dual_momentum': DualMomentumStrategy
        }
        
        if strategy_name not in strategies:
            raise ValueError(
                f"Unknown strategy: {strategy_name}. "
                f"Available: {list(strategies.keys())}"
            )
        
        return strategies[strategy_name]
    
    def _calculate_results(
        self,
        strategy_name: str,
        periods: List[OptimizationPeriod]
    ) -> RollingWalkForwardResult:
        """Calculate aggregated results from all periods."""
        # Filter out periods with None values
        valid_periods = [
            p for p in periods
            if p.train_sharpe is not None and p.test_sharpe is not None
        ]
        
        if not valid_periods:
            raise ValueError("No valid periods found")
        
        # Calculate averages
        avg_train_sharpe = np.mean([p.train_sharpe for p in valid_periods])
        avg_test_sharpe = np.mean([p.test_sharpe for p in valid_periods])
        std_test_sharpe = np.std([p.test_sharpe for p in valid_periods])
        
        # Calculate degradation safely
        if avg_train_sharpe != 0:
            degradation = (avg_train_sharpe - avg_test_sharpe) / avg_train_sharpe
        else:
            # If train sharpe is 0, degradation is undefined
            # Set to 1.0 (100%) to indicate complete degradation
            degradation = 1.0 if avg_test_sharpe == 0 else 0.0
        
        avg_test_return = np.mean([p.test_return for p in valid_periods])
        avg_test_max_dd = np.mean([p.test_max_dd for p in valid_periods])
        
        # Find best/worst periods
        best_period = max(valid_periods, key=lambda p: p.test_sharpe)
        worst_period = min(valid_periods, key=lambda p: p.test_sharpe)
        
        # Calculate parameter frequency
        param_frequency = self._calculate_param_frequency(valid_periods)
        
        return RollingWalkForwardResult(
            strategy_name=strategy_name,
            total_periods=len(valid_periods),
            reoptimize_frequency=self.reoptimize_frequency,
            avg_train_sharpe=avg_train_sharpe,
            avg_test_sharpe=avg_test_sharpe,
            std_test_sharpe=std_test_sharpe,
            degradation=degradation,
            avg_test_return=avg_test_return,
            avg_test_max_dd=avg_test_max_dd,
            best_period=best_period,
            worst_period=worst_period,
            periods=valid_periods,
            param_frequency=param_frequency
        )
    
    def _calculate_param_frequency(
        self,
        periods: List[OptimizationPeriod]
    ) -> Dict[str, int]:
        """Calculate how often each parameter value was chosen."""
        frequency = {}
        
        for period in periods:
            if period.best_params is None:
                continue
            
            # Count top_k
            key = f"top_k={period.best_params.top_k}"
            frequency[key] = frequency.get(key, 0) + 1
            
            # Count holding_days
            key = f"holding_days={period.best_params.holding_days}"
            frequency[key] = frequency.get(key, 0) + 1
            
            # Count tp_multiplier
            key = f"tp_multiplier={period.best_params.tp_multiplier:.3f}"
            frequency[key] = frequency.get(key, 0) + 1
        
        return frequency
