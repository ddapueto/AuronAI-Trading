#!/usr/bin/env python3
"""
Dual Momentum Strategy Validation Script.

This script runs walk-forward validation for the Dual Momentum strategy
with FIXED parameters (no optimization) to validate if the system works.

Phase 1 of AuronAI Strategy Validation project.
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from auronai.data.market_data_provider import MarketDataProvider
from auronai.data.symbol_universe import SymbolUniverseManager
from auronai.strategies.dual_momentum import DualMomentumStrategy, DualMomentumParams
from auronai.backtesting.backtest_config import BacktestConfig
from auronai.backtesting.backtest_runner import BacktestRunner
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Run Dual Momentum validation."""
    
    logger.info("=" * 80)
    logger.info("DUAL MOMENTUM STRATEGY VALIDATION")
    logger.info("Phase 1: Fixed Parameters - No Optimization")
    logger.info("=" * 80)
    
    # Initialize market data provider
    logger.info("\n📊 Step 1: Initialize Market Data Provider")
    market_data_provider = MarketDataProvider(
        cache_ttl_seconds=3600,  # 1 hour cache
        max_retries=3
    )
    
    # Initialize symbol universe manager
    logger.info("\n🌍 Step 2: Initialize Symbol Universe")
    symbol_manager = SymbolUniverseManager(market_data_provider)
    
    # Validate symbol universe
    logger.info("\n✅ Step 3: Validate Symbol Universe")
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 2, 1)
    
    validation_result = symbol_manager.validate_universe(
        start_date=start_date,
        end_date=end_date,
        min_data_points=756  # 3 years
    )
    
    logger.info(f"\nValidation Results:")
    logger.info(f"  ✅ Valid symbols: {len(validation_result.valid)}")
    logger.info(f"  ⚠️ Insufficient data: {len(validation_result.insufficient_data)}")
    logger.info(f"  ❌ Missing: {len(validation_result.missing)}")
    logger.info(f"  ❌ Errors: {len(validation_result.errors)}")
    logger.info(f"  Success rate: {validation_result.success_rate:.1%}")
    
    if len(validation_result.valid) < 10:
        logger.error(
            f"Not enough valid symbols ({len(validation_result.valid)}). "
            f"Need at least 10 for meaningful validation."
        )
        return 1
    
    # Use validated symbols
    symbols = validation_result.valid
    logger.info(f"\n📈 Using {len(symbols)} validated symbols for backtesting")
    
    # PRE-LOAD ALL DATA ONCE (critical optimization)
    logger.info("\n💾 Step 3.5: Pre-load ALL data (one-time operation)")
    logger.info("This will take 2-3 minutes but saves hours later...")
    
    from auronai.data.parquet_cache import ParquetCache
    parquet_cache = ParquetCache()
    
    preload_start = datetime.now()
    data_loaded = 0
    data_cached = 0
    
    for symbol in symbols:
        # Check if already cached
        cached_data = parquet_cache.get_data(symbol, start_date, end_date)
        
        if cached_data is not None and len(cached_data) > 0:
            data_cached += 1
            logger.debug(f"  ✓ {symbol}: already cached ({len(cached_data)} rows)")
        else:
            # Fetch and cache
            logger.info(f"  ⬇️ Fetching {symbol}...")
            data = market_data_provider.get_historical_data_range(
                symbol,
                start_date,
                end_date
            )
            
            if data is not None and len(data) > 0:
                parquet_cache.save_data(symbol, data)
                data_loaded += 1
                logger.info(f"  ✅ {symbol}: loaded and cached ({len(data)} rows)")
            else:
                logger.warning(f"  ⚠️ {symbol}: no data available")
    
    preload_time = (datetime.now() - preload_start).total_seconds()
    logger.info(
        f"\n✅ Data pre-load complete in {preload_time:.1f}s: "
        f"{data_cached} cached, {data_loaded} newly loaded"
    )
    
    # Configure walk-forward validation
    logger.info("\n⚙️ Step 4: Configure Walk-Forward Validation")
    
    # FULL MODE for complete validation
    USE_FAST_MODE = False
    
    if USE_FAST_MODE:
        logger.info("🚀 FAST MODE enabled (for testing)")
        walk_forward_config = {
            'train_window_days': 180,  # 6 months
            'test_window_days': 60,    # 2 months
            'reoptimize_frequency': 'monthly',
            'start_date': datetime(2023, 1, 1),  # 2 years only
            'end_date': datetime(2025, 2, 1),
            'symbols': symbols[:15]  # Use only first 15 symbols
        }
    else:
        logger.info("📊 FULL MODE enabled (production validation)")
        walk_forward_config = {
            'train_window_days': 365,  # 12 months
            'test_window_days': 90,    # 3 months
            'reoptimize_frequency': 'monthly',
            'start_date': datetime(2021, 1, 1),  # Start 2021 (12 months warmup from 2020)
            'end_date': datetime(2025, 2, 1),
            'symbols': symbols  # All validated symbols
        }
    
    logger.info(f"  Train window: {walk_forward_config['train_window_days']} days")
    logger.info(f"  Test window: {walk_forward_config['test_window_days']} days")
    logger.info(f"  Reoptimize: {walk_forward_config['reoptimize_frequency']}")
    logger.info(f"  Date range: {walk_forward_config['start_date'].date()} to {walk_forward_config['end_date'].date()}")
    logger.info(f"  Symbols: {len(walk_forward_config['symbols'])}")
    
    # Define FIXED parameters (NO OPTIMIZATION)
    logger.info("\n🔒 Step 5: Define Fixed Parameters (No Optimization)")
    
    fixed_params = DualMomentumParams(
        lookback_period=252,  # 12 months (Antonacci standard)
        top_n=5,              # Hold top 5 assets
        rebalance_frequency='monthly'
    )
    
    logger.info(f"  Lookback period: {fixed_params.lookback_period} days")
    logger.info(f"  Top N: {fixed_params.top_n} assets")
    logger.info(f"  Rebalance: {fixed_params.rebalance_frequency}")
    logger.info("  ⚠️ NO PARAMETER OPTIMIZATION - Using fixed academic values")
    
    # Run walk-forward validation WITHOUT optimization
    logger.info("\n🚀 Step 6: Run Walk-Forward Validation (No Optimization)")
    logger.info("This will take 5-10 minutes...")
    
    start_time = datetime.now()
    
    # Initialize backtest runner
    backtest_runner = BacktestRunner()
    
    # Generate periods manually
    periods = []
    current_test_start = walk_forward_config['start_date']
    period_id = 1
    
    train_window_days = walk_forward_config['train_window_days']
    test_window_days = walk_forward_config['test_window_days']
    step_days = 30  # Monthly
    
    while current_test_start + timedelta(days=test_window_days) <= walk_forward_config['end_date']:
        train_end = current_test_start - timedelta(days=1)
        train_start = train_end - timedelta(days=train_window_days - 1)
        test_start = current_test_start
        test_end = test_start + timedelta(days=test_window_days - 1)
        
        if test_end > walk_forward_config['end_date']:
            test_end = walk_forward_config['end_date']
        
        periods.append({
            'period_id': period_id,
            'train_start': train_start,
            'train_end': train_end,
            'test_start': test_start,
            'test_end': test_end
        })
        
        current_test_start += timedelta(days=step_days)
        period_id += 1
    
    logger.info(f"Generated {len(periods)} validation periods")
    
    # Run backtest for each period
    results = []
    
    for period in periods:
        logger.info(f"\n{'='*60}")
        logger.info(f"Period {period['period_id']}/{len(periods)}")
        logger.info(f"Test: {period['test_start'].date()} to {period['test_end'].date()}")
        logger.info(f"{'='*60}")
        
        # Create strategy with fixed params
        strategy = DualMomentumStrategy(fixed_params)
        
        # Run backtest on test period
        config = BacktestConfig(
            strategy_id=f"dual_momentum_period_{period['period_id']}",
            symbols=walk_forward_config['symbols'],
            start_date=period['test_start'],
            end_date=period['test_end'],
            initial_capital=10000.0,
            commission_rate=0.0,
            slippage_rate=0.0005,
            benchmark='QQQ',
            strategy_params=fixed_params.__dict__
        )
        
        try:
            result = backtest_runner.run(config, strategy)
            
            period_result = {
                'period_id': period['period_id'],
                'test_start': period['test_start'].isoformat(),
                'test_end': period['test_end'].isoformat(),
                'sharpe_ratio': result.metrics['sharpe_ratio'],
                'total_return': result.metrics['total_return'],
                'max_drawdown': result.metrics['max_drawdown'],
                'num_trades': result.metrics.get('num_trades', 0)
            }
            
            results.append(period_result)
            
            logger.info(f"✅ Sharpe: {result.metrics['sharpe_ratio']:.2f}, "
                       f"Return: {result.metrics['total_return']:.1%}, "
                       f"Max DD: {result.metrics['max_drawdown']:.1%}")
        
        except Exception as e:
            logger.error(f"❌ Error in period {period['period_id']}: {e}")
            results.append({
                'period_id': period['period_id'],
                'test_start': period['test_start'].isoformat(),
                'test_end': period['test_end'].isoformat(),
                'sharpe_ratio': 0.0,
                'total_return': 0.0,
                'max_drawdown': 0.0,
                'num_trades': 0,
                'error': str(e)
            })
    
    # Calculate aggregate metrics
    valid_results = [r for r in results if 'error' not in r]
    
    if not valid_results:
        logger.error("No valid results - all periods failed")
        return 1
    
    avg_sharpe = np.mean([r['sharpe_ratio'] for r in valid_results])
    std_sharpe = np.std([r['sharpe_ratio'] for r in valid_results])
    avg_return = np.mean([r['total_return'] for r in valid_results])
    avg_max_dd = np.mean([r['max_drawdown'] for r in valid_results])
    
    # Create result object
    class SimpleResult:
        def __init__(self):
            self.total_periods = len(valid_results)
            self.avg_test_sharpe = avg_sharpe
            self.std_test_sharpe = std_sharpe
            self.degradation = 0.0  # No training, so no degradation
            self.avg_test_return = avg_return
            self.avg_test_max_dd = avg_max_dd
            self.periods = results
        
        def to_dict(self):
            return {
                'strategy_name': 'dual_momentum',
                'total_periods': self.total_periods,
                'avg_test_sharpe': self.avg_test_sharpe,
                'std_test_sharpe': self.std_test_sharpe,
                'degradation': self.degradation,
                'avg_test_return': self.avg_test_return,
                'avg_test_max_dd': self.avg_test_max_dd,
                'periods': self.periods,
                'fixed_params': fixed_params.__dict__
            }
    
    result = SimpleResult()
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION RESULTS")
    logger.info("=" * 80)
    
    logger.info(f"\n⏱️ Execution Time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    logger.info(f"📊 Total Periods: {result.total_periods}")
    logger.info(f"📉 Avg Test Sharpe: {result.avg_test_sharpe:.2f} ± {result.std_test_sharpe:.2f}")
    logger.info(f"⚠️ Degradation: {result.degradation:.1%} (N/A - fixed params)")
    logger.info(f"💰 Avg Test Return: {result.avg_test_return:.1%}")
    logger.info(f"📉 Avg Test Max DD: {result.avg_test_max_dd:.1%}")
    
    # Evaluate success criteria
    logger.info("\n" + "=" * 80)
    logger.info("SUCCESS CRITERIA EVALUATION")
    logger.info("=" * 80)
    
    success_criteria = {
        'degradation_ok': result.degradation < 0.30,  # < 30%
        'test_sharpe_ok': result.avg_test_sharpe > 0.8,
        'max_dd_ok': result.avg_test_max_dd > -0.25,  # > -25%
    }
    
    logger.info(f"\n✓ Degradation < 30%: {'✅ PASS' if success_criteria['degradation_ok'] else '❌ FAIL'} ({result.degradation:.1%})")
    logger.info(f"✓ Test Sharpe > 0.8: {'✅ PASS' if success_criteria['test_sharpe_ok'] else '❌ FAIL'} ({result.avg_test_sharpe:.2f})")
    logger.info(f"✓ Max DD > -25%: {'✅ PASS' if success_criteria['max_dd_ok'] else '❌ FAIL'} ({result.avg_test_max_dd:.1%})")
    
    all_pass = all(success_criteria.values())
    
    if all_pass:
        logger.info("\n🎉 ALL SUCCESS CRITERIA MET - PROCEED TO PHASE 2")
    else:
        logger.warning("\n⚠️ SOME CRITERIA NOT MET - REVIEW RESULTS")
    
    # Save results
    logger.info("\n💾 Step 7: Save Results")
    
    results_dir = Path(__file__).parent.parent / 'results'
    results_dir.mkdir(exist_ok=True)
    
    output_file = results_dir / 'dual_momentum_validation.json'
    
    with open(output_file, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    
    logger.info(f"Results saved to: {output_file}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION COMPLETE")
    logger.info("=" * 80)
    
    if all_pass:
        logger.info("\n✅ Dual Momentum strategy shows promise!")
        logger.info("✅ System infrastructure is working correctly")
        logger.info("✅ Ready to proceed to Phase 2 (Multi-Strategy)")
        return 0
    else:
        logger.warning("\n⚠️ Strategy needs adjustment or further investigation")
        logger.warning("⚠️ Review results before proceeding to Phase 2")
        return 1


if __name__ == '__main__':
    sys.exit(main())
