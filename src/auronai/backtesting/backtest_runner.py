"""
Backtest runner orchestrator.

This module orchestrates backtest execution by coordinating data loading,
feature computation, regime detection, signal generation, and trade execution.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib

import pandas as pd
import numpy as np

from auronai.backtesting.backtest_config import (
    BacktestConfig,
    BacktestResult,
    Trade
)
from auronai.backtesting.run_manager import RunManager
from auronai.backtesting.metrics import MetricsCalculator
from auronai.data.parquet_cache import ParquetCache
from auronai.data.feature_store import FeatureStore
from auronai.data.market_data_provider import MarketDataProvider
from auronai.strategies.base_strategy import BaseStrategy, MarketRegime
from auronai.strategies.regime_engine import RegimeEngine
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


class BacktestRunner:
    """
    Orchestrates backtest execution.
    
    Responsibilities:
    1. Load data from cache (or fetch if missing)
    2. Compute features if needed
    3. Detect market regime day-by-day
    4. Execute strategy signals
    5. Track trades and equity
    6. Calculate metrics
    7. Save run to database
    
    **Validates: Requirements FR-9, FR-10**
    """
    
    def __init__(
        self,
        parquet_cache: Optional[ParquetCache] = None,
        feature_store: Optional[FeatureStore] = None,
        regime_engine: Optional[RegimeEngine] = None,
        run_manager: Optional[RunManager] = None,
        market_data_provider: Optional[MarketDataProvider] = None
    ):
        """
        Initialize backtest runner.
        
        Args:
            parquet_cache: Cache for OHLCV data
            feature_store: Cache for computed features
            regime_engine: Market regime detector
            run_manager: Run metadata manager
            market_data_provider: Data provider for fetching market data
        """
        self.parquet_cache = parquet_cache or ParquetCache()
        self.feature_store = feature_store or FeatureStore()
        self.regime_engine = regime_engine or RegimeEngine()
        self.run_manager = run_manager or RunManager()
        self.market_data_provider = market_data_provider or MarketDataProvider()
        
        logger.info("BacktestRunner initialized")
    
    def run(
        self,
        config: BacktestConfig,
        strategy: BaseStrategy
    ) -> BacktestResult:
        """
        Execute backtest.
        
        Args:
            config: Backtest configuration
            strategy: Trading strategy instance
        
        Returns:
            BacktestResult with metrics, trades, equity curve
        """
        logger.info(
            f"Starting backtest: {config.strategy_id}, "
            f"{len(config.symbols)} symbols, "
            f"{config.start_date.date()} to {config.end_date.date()}"
        )
        
        # 1. Load/fetch data
        data = self._load_data(config)
        
        # 2. Compute features
        features = self._compute_features(data, config)
        
        # 3. Get benchmark features for regime detection
        benchmark_features = features[features.index.get_level_values('symbol') == config.benchmark]
        
        # 4. Initialize state
        equity = config.initial_capital
        cash = config.initial_capital
        positions = {}  # symbol -> shares
        trades = []
        equity_curve = []
        
        # Get unique dates
        all_dates = features.index.get_level_values('date').unique().sort_values()
        
        # Convert to timezone-naive if needed (yfinance returns tz-aware dates)
        if hasattr(all_dates, 'tz') and all_dates.tz is not None:
            all_dates = all_dates.tz_localize(None)
        
        # Filter to only backtest period (after warmup)
        backtest_dates = all_dates[all_dates >= config.start_date]
        
        logger.info(
            f"Total dates loaded: {len(all_dates)} "
            f"(warmup: {len(all_dates) - len(backtest_dates)}, "
            f"backtest: {len(backtest_dates)})"
        )
        
        # Track last rebalance date
        last_rebalance_date = None
        holding_days = strategy.get_params().get('holding_days', 10)
        
        # 5. Simulate day-by-day (only during backtest period)
        for i, date in enumerate(backtest_dates):
            # Get index in full dataset (for regime detection)
            full_idx = all_dates.get_loc(date)
            
            # Get features for this date
            daily_features = features.loc[features.index.get_level_values('date') == date]
            
            # Detect regime (using full dataset index for proper lookback)
            regime = self.regime_engine.detect_regime(
                benchmark_features.reset_index(level='symbol', drop=True),
                full_idx
            )
            
            # Check for exits EVERY day (for strategies that need it)
            # This allows TP and TimeExit to trigger between rebalance days
            if hasattr(strategy, '_check_exits_with_data'):
                # Pass daily features so strategy can check TP using High price
                exit_info = strategy._check_exits_with_data(
                    daily_features.reset_index(level='date', drop=True),
                    date
                )
                
                # Close positions in backtest runner
                for symbol, exit_data in exit_info.items():
                    if symbol in positions:
                        exit_price = exit_data['exit_price']
                        reason = exit_data['reason']
                        shares = positions[symbol]
                        
                        # Calculate P&L
                        # Find the entry trade for this symbol
                        entry_trade = None
                        for trade in reversed(trades):
                            if trade['symbol'] == symbol and trade['exit_date'] is None:
                                entry_trade = trade
                                break
                        
                        if entry_trade:
                            pnl_dollar = (exit_price - entry_trade['entry_price']) * shares
                            pnl_percent = ((exit_price / entry_trade['entry_price']) - 1) * 100
                            
                            # Update trade record
                            entry_trade['exit_date'] = date.isoformat()
                            entry_trade['exit_price'] = exit_price
                            entry_trade['pnl_dollar'] = pnl_dollar
                            entry_trade['pnl_percent'] = pnl_percent
                            entry_trade['reason'] = reason
                            
                            # Add position value back to cash
                            cash += shares * exit_price
                        
                        # Remove position
                        del positions[symbol]
                        
                        logger.info(f"Closed {symbol} at ${exit_price:.2f} (reason: {reason})")
            
            # Check if we should rebalance
            # For swing strategies, we try to fill the portfolio EVERY day
            # (not just every holding_days)
            should_rebalance = True
            
            # Generate signals
            # Check if strategy needs full historical data (for momentum calculations)
            if hasattr(strategy, 'needs_full_history') and strategy.needs_full_history:
                # Pass ALL historical data (including warmup period) for momentum strategies
                # Filter only up to current date to avoid look-ahead bias
                historical_data = features[features.index.get_level_values('date') <= date]
                
                logger.debug(
                    f"Passing full history to strategy: {len(historical_data)} rows "
                    f"up to {date.date()}"
                )
                
                signals = strategy.generate_signals(
                    historical_data,
                    regime,
                    date
                )
            else:
                # Pass only current day's data for regular strategies
                signals = strategy.generate_signals(
                    daily_features.reset_index(level='date', drop=True),
                    regime,
                    date
                )
            
            # Only execute trades if we have signals
            if signals:
                # Apply risk model
                target_weights = strategy.risk_model(
                    signals,
                    daily_features.reset_index(level='date', drop=True),
                    self._get_current_weights(positions, equity)
                )
                
                # Set entry date for strategy positions (if strategy supports it)
                if hasattr(strategy, 'set_entry_date'):
                    strategy.set_entry_date(date)
                
                # Execute trades (returns updated cash)
                new_trades, cash = self._execute_rebalance(
                    date,
                    target_weights,
                    positions,
                    cash,
                    equity,
                    daily_features,
                    config
                )
                
                trades.extend(new_trades)
                last_rebalance_date = date
            
            # Update equity
            equity, cash = self._calculate_equity(
                positions,
                cash,
                daily_features
            )
            
            equity_curve.append({
                'date': date.isoformat(),
                'equity': equity,
                'cash': cash
            })
            
            if (i + 1) % 50 == 0:
                logger.debug(f"Day {i+1}/{len(backtest_dates)}: Equity=${equity:,.2f}")
        
        # 6. Calculate metrics
        metrics = self._calculate_metrics(trades, equity_curve, config)
        
        # 7. Calculate data version
        data_version = self._calculate_data_version(data)
        
        # 8. Get code version (simplified - use timestamp for MVP)
        code_version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 9. Save run
        equity_df = pd.DataFrame(equity_curve)
        
        run_id = self.run_manager.save_run(
            strategy_id=config.strategy_id,
            strategy_params=config.strategy_params,
            symbols=config.symbols,
            benchmark=config.benchmark,
            start_date=config.start_date,
            end_date=config.end_date,
            initial_capital=config.initial_capital,
            data_version=data_version,
            code_version=code_version,
            metrics=metrics,
            trades=trades,
            equity_curve=equity_df
        )
        
        logger.info(
            f"Backtest complete: {len(trades)} trades, "
            f"final equity=${equity:,.2f}, run_id={run_id}"
        )
        
        return BacktestResult(
            run_id=run_id,
            config=config,
            metrics=metrics,
            trades=trades,
            equity_curve=equity_df
        )
    
    def _load_data(self, config: BacktestConfig) -> pd.DataFrame:
        """
        Load OHLCV data for all symbols + benchmark.
        
        Loads extra data before start_date to ensure indicators like EMA200
        have sufficient warmup period.
        
        Args:
            config: Backtest configuration
        
        Returns:
            DataFrame with OHLCV data for all symbols (includes warmup period)
        """
        # Add warmup period for indicators (300 trading days ≈ 1.5 years)
        # This ensures EMA200 and other long-period indicators are accurate
        warmup_days = 300
        data_start_date = config.start_date - timedelta(days=warmup_days)
        
        logger.info(
            f"Loading data with warmup: {data_start_date.date()} to {config.end_date.date()} "
            f"(backtest starts {config.start_date.date()})"
        )
        
        all_symbols = list(set(config.symbols + [config.benchmark]))
        
        dfs = []
        for symbol in all_symbols:
            # Try cache first (with extended date range)
            data = self.parquet_cache.get_data(
                symbol,
                data_start_date,
                config.end_date
            )
            
            # Fetch if not in cache
            if data is None:
                logger.info(f"Fetching data for {symbol} (with warmup)")
                data = self.market_data_provider.get_historical_data_range(
                    symbol,
                    data_start_date,
                    config.end_date
                )
                
                if data is not None and not data.empty:
                    self.parquet_cache.save_data(symbol, data)
            
            if data is not None and not data.empty:
                data['symbol'] = symbol
                dfs.append(data)
        
        if not dfs:
            raise ValueError("No data loaded for any symbols")
        
        combined = pd.concat(dfs, ignore_index=False)
        combined = combined.set_index(['symbol', combined.index])
        combined.index.names = ['symbol', 'date']
        
        logger.info(
            f"Loaded {len(combined)} rows across {len(all_symbols)} symbols "
            f"(includes warmup period)"
        )
        
        return combined
    
    def _compute_features(
        self,
        data: pd.DataFrame,
        config: BacktestConfig
    ) -> pd.DataFrame:
        """
        Compute technical indicators for all symbols.
        
        Args:
            data: OHLCV data
            config: Backtest configuration
        
        Returns:
            DataFrame with OHLCV + indicators
        """
        # Get benchmark data for relative strength
        benchmark_data = data.loc[config.benchmark].copy()
        
        features_list = []
        
        for symbol in data.index.get_level_values('symbol').unique():
            symbol_data = data.loc[symbol].copy()
            
            # Compute features
            features = self.feature_store.compute_and_save(
                symbol,
                symbol_data,
                benchmark_data if symbol != config.benchmark else None
            )
            
            features['symbol'] = symbol
            features_list.append(features)
        
        combined = pd.concat(features_list, ignore_index=False)
        combined = combined.set_index(['symbol', combined.index])
        combined.index.names = ['symbol', 'date']
        
        return combined
    
    def _get_current_weights(
        self,
        positions: Dict[str, float],
        equity: float
    ) -> Dict[str, float]:
        """Calculate current portfolio weights."""
        if equity == 0:
            return {}
        
        # This is simplified - in reality we'd need current prices
        # For now, just return empty dict
        return {}
    
    def _execute_rebalance(
        self,
        date: datetime,
        target_weights: Dict[str, float],
        positions: Dict[str, float],
        cash: float,
        equity: float,
        daily_features: pd.DataFrame,
        config: BacktestConfig
    ) -> tuple[List[Dict], float]:
        """
        Execute rebalancing trades.
        
        For swing strategies: Only ADD new positions (don't close existing ones).
        Exits are handled separately by the strategy's _check_exits() method.
        
        Returns:
            Tuple of (trades list, updated cash)
        """
        trades = []
        
        # For swing strategies: DON'T close existing positions
        # They will be closed by _check_exits() when TP or TimeExit triggers
        
        # Open new positions (only for symbols not already held)
        for symbol, target_weight in target_weights.items():
            if target_weight == 0:
                continue
            
            # Skip if we already have this position
            if symbol in positions:
                continue
            
            try:
                symbol_data = daily_features.loc[symbol]
                # Ensure we get a scalar value
                if isinstance(symbol_data, pd.DataFrame):
                    price = float(symbol_data['Close'].iloc[0])
                else:
                    price = float(symbol_data['Close'])
                
                # Calculate target dollar amount
                target_value = equity * abs(target_weight)
                
                # Calculate shares
                shares = target_value / price
                
                # Apply commission and slippage
                commission = target_value * config.commission_rate
                slippage = target_value * config.slippage_rate
                total_cost = target_value + commission + slippage
                
                # Check if we have enough cash
                if total_cost > cash:
                    logger.warning(f"Insufficient cash for {symbol}: need ${total_cost:.2f}, have ${cash:.2f}")
                    continue
                
                # Deduct from cash
                cash -= total_cost
                
                # Update positions
                positions[symbol] = shares if target_weight > 0 else -shares
                
                # Record trade (entry only for now)
                trades.append({
                    'symbol': symbol,
                    'entry_date': date.isoformat(),
                    'exit_date': None,
                    'entry_price': price,
                    'exit_price': None,
                    'shares': shares,
                    'direction': 'long' if target_weight > 0 else 'short',
                    'pnl_dollar': None,
                    'pnl_percent': None,
                    'reason': None
                })
                
            except (KeyError, IndexError) as e:
                logger.warning(f"Could not execute trade for {symbol}: {e}")
        
        return trades, cash
    
    def _calculate_equity(
        self,
        positions: Dict[str, float],
        cash: float,
        daily_features: pd.DataFrame
    ) -> tuple:
        """
        Calculate current equity.
        
        Returns:
            (equity, cash) tuple
        """
        position_value = 0.0
        
        for symbol, shares in positions.items():
            try:
                symbol_data = daily_features.loc[symbol]
                # Ensure we get a scalar value
                if isinstance(symbol_data, pd.DataFrame):
                    price = symbol_data['Close'].iloc[0]
                else:
                    price = symbol_data['Close']
                position_value += shares * price
            except (KeyError, IndexError):
                pass
        
        equity = cash + position_value
        
        return float(equity), float(cash)
    
    def _calculate_metrics(
        self,
        trades: List[Dict],
        equity_curve: List[Dict],
        config: BacktestConfig
    ) -> Dict[str, float]:
        """
        Calculate performance metrics using MetricsCalculator.
        
        Args:
            trades: List of trade dicts
            equity_curve: List of equity snapshots
            config: Backtest configuration
        
        Returns:
            Dictionary of metrics
        """
        if not equity_curve:
            return {}
        
        equity_df = pd.DataFrame(equity_curve)
        
        metrics = MetricsCalculator.calculate_all_metrics(
            equity_curve=equity_df,
            trades=trades,
            initial_capital=config.initial_capital,
            regime_history=None  # TODO: Add regime history tracking
        )
        
        return metrics
    
    def _calculate_data_version(self, data: pd.DataFrame) -> str:
        """
        Calculate SHA256 hash of data for versioning.
        
        Args:
            data: OHLCV data
        
        Returns:
            SHA256 hash string
        """
        # Simple hash of data shape and date range
        data_str = f"{len(data)}_{data.index.min()}_{data.index.max()}"
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
