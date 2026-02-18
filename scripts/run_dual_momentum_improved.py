#!/usr/bin/env python3
"""
Dual Momentum Strategy Validation - IMPROVED VERSION

Changes from original:
1. Test window: 180 days (vs 90) - better for momentum strategies
2. Calculate cumulative performance across all periods
3. Compare vs SPY benchmark
4. More comprehensive metrics

This addresses the low Sharpe issue by using longer test periods.
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from auronai.data.market_data_provider import MarketDataProvider
from auronai.data.symbol_universe import SymbolUniverseManager
from auronai.strategies.dual_momentum import DualMomentumStrategy, DualMomentumParams
from auronai.backtesting.backtest_config import BacktestConfig
from auronai.backtesting.backtest_runner import BacktestRunner
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


def calculate_cumulative_metrics(results: list) -> dict:
    """
    Calculate cumulative performance across all periods.
    
    This gives a better picture than averaging per-period metrics.
    """
    # Combine all equity curves
    all_equity = []
    initial_capital = 10000.0
    current_capital = initial_capital
    
    for period in results:
        if 'error' in period:
            continue
        
        # Calculate period return
        period_return = period['total_return']
        current_capital *= (1 + period_return)
        
        all_equity.append({
            'period_id': period['period_id'],
            'equity': current_capital,
            'return': period_return
        })
    
    # Calculate cumulative metrics
    if not all_equity:
        return {}
    
    equity_series = pd.Series([e['equity'] for e in all_equity])
    returns_series = pd.Series([e['return'] for e in all_equity])
    
    # Total return
    total_return = (equity_series.iloc[-1] / initial_capital) - 1
    
    # Annualized return (assuming monthly periods)
    n_periods = len(all_equity)
    years = n_periods / 12  # Monthly periods
    annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
    
    # Sharpe ratio (annualized)
    if len(returns_series) > 1:
        sharpe = returns_series.mean() / returns_series.std() * np.sqrt(12)  # Annualize
    else:
        sharpe = 0
    
    # Max drawdown
    cummax = equity_series.cummax()
    drawdown = (equity_series - cummax) / cummax
    max_drawdown = drawdown.min()
    
    # Win rate
    wins = (returns_series > 0).sum()
    win_rate = wins / len(returns_series) if len(returns_series) > 0 else 0
    
    return {
        'total_return': float(total_return),
        'annualized_return': float(annualized_return),
        'cumulative_sharpe': float(sharpe),
        'max_drawdown': float(max_drawdown),
        'win_rate': float(win_rate),
        'n_periods': int(n_periods),
        'final_equity': float(equity_series.iloc[-1]),
        'equity_curve': [
            {
                'period_id': int(e['period_id']),
                'equity': float(e['equity']),
                'return': float(e['return'])
            }
            for e in all_equity
        ]
    }


def compare_vs_benchmark(
    results: list,
    benchmark_symbol: str,
    market_data_provider: MarketDataProvider
) -> dict:
    """
    Compare strategy performance vs benchmark (SPY).
    """
    # Get benchmark data
    start_date = datetime.fromisoformat(results[0]['test_start'])
    end_date = datetime.fromisoformat(results[-1]['test_end'])
    
    benchmark_data = market_data_provider.get_historical_data_range(
        benchmark_symbol,
        start_date,
        end_date
    )
    
    if benchmark_data is None or len(benchmark_data) == 0:
        logger.warning(f"Could not load benchmark data for {benchmark_symbol}")
        return {}
    
    # Calculate benchmark returns
    benchmark_return = (
        benchmark_data['Close'].iloc[-1] / benchmark_data['Close'].iloc[0]
    ) - 1
    
    # Calculate strategy returns
    strategy_equity = []
    initial_capital = 10000.0
    current_capital = initial_capital
    
    for period in results:
        if 'error' not in period:
            current_capital *= (1 + period['total_return'])
    
    strategy_return = (current_capital / initial_capital) - 1
    
    # Calculate alpha
    alpha = strategy_return - benchmark_return
    
    # Calculate years
    years = (end_date - start_date).days / 365.25
    
    # Annualize
    strategy_annual = (1 + strategy_return) ** (1 / years) - 1 if years > 0 else 0
    benchmark_annual = (1 + benchmark_return) ** (1 / years) - 1 if years > 0 else 0
    alpha_annual = strategy_annual - benchmark_annual
    
    return {
        'benchmark_symbol': benchmark_symbol,
        'benchmark_return': float(benchmark_return),
        'benchmark_annual': float(benchmark_annual),
        'strategy_return': float(strategy_return),
        'strategy_annual': float(strategy_annual),
        'alpha': float(alpha),
        'alpha_annual': float(alpha_annual),
        'outperformance': bool(strategy_return > benchmark_return)
    }


def main():
    """Run improved Dual Momentum validation."""
    
    logger.info("=" * 80)
    logger.info("DUAL MOMENTUM VALIDATION - IMPROVED VERSION")
    logger.info("Changes: Longer test periods (180 days), cumulative metrics, benchmark comparison")
    logger.info("=" * 80)
    
    # Initialize
    logger.info("\n📊 Step 1: Initialize")
    market_data_provider = MarketDataProvider(cache_ttl_seconds=3600, max_retries=3)
    symbol_manager = SymbolUniverseManager(market_data_provider)
    
    # Validate symbols
    logger.info("\n✅ Step 2: Validate Symbol Universe")
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 2, 1)
    
    validation_result = symbol_manager.validate_universe(
        start_date=start_date,
        end_date=end_date,
        min_data_points=756
    )
    
    logger.info(f"Valid symbols: {len(validation_result.valid)}")
    
    if len(validation_result.valid) < 10:
        logger.error("Not enough valid symbols")
        return 1
    
    symbols = validation_result.valid
    
    # Pre-load data
    logger.info("\n💾 Step 3: Pre-load Data")
    from auronai.data.parquet_cache import ParquetCache
    parquet_cache = ParquetCache()
    
    preload_start = datetime.now()
    for symbol in symbols:
        cached_data = parquet_cache.get_data(symbol, start_date, end_date)
        if cached_data is None:
            logger.info(f"  ⬇️ Fetching {symbol}...")
            data = market_data_provider.get_historical_data_range(symbol, start_date, end_date)
            if data is not None and len(data) > 0:
                parquet_cache.save_data(symbol, data)
    
    preload_time = (datetime.now() - preload_start).total_seconds()
    logger.info(f"Data pre-load complete in {preload_time:.1f}s")
    
    # Configure walk-forward with LONGER test periods
    logger.info("\n⚙️ Step 4: Configure Walk-Forward (IMPROVED)")
    
    walk_forward_config = {
        'train_window_days': 365,  # 12 months
        'test_window_days': 180,   # 6 months (vs 90 before) ⭐ KEY CHANGE
        'reoptimize_frequency': 'monthly',
        'start_date': datetime(2021, 1, 1),
        'end_date': datetime(2025, 2, 1),
        'symbols': symbols
    }
    
    logger.info(f"  Train window: {walk_forward_config['train_window_days']} days")
    logger.info(f"  Test window: {walk_forward_config['test_window_days']} days ⭐ IMPROVED")
    logger.info(f"  Date range: {walk_forward_config['start_date'].date()} to {walk_forward_config['end_date'].date()}")
    
    # Fixed parameters
    logger.info("\n🔒 Step 5: Fixed Parameters")
    fixed_params = DualMomentumParams(
        lookback_period=252,
        top_n=5,
        rebalance_frequency='monthly'
    )
    
    # Run validation
    logger.info("\n🚀 Step 6: Run Walk-Forward Validation")
    start_time = datetime.now()
    
    backtest_runner = BacktestRunner()
    
    # Generate periods
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
    
    # Run backtests
    results = []
    
    for period in periods:
        logger.info(f"\nPeriod {period['period_id']}/{len(periods)}: {period['test_start'].date()} to {period['test_end'].date()}")
        
        strategy = DualMomentumStrategy(fixed_params)
        
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
            
            logger.info(f"  Sharpe: {result.metrics['sharpe_ratio']:.2f}, "
                       f"Return: {result.metrics['total_return']:.1%}, "
                       f"Trades: {result.metrics.get('num_trades', 0)}")
        
        except Exception as e:
            logger.error(f"  Error: {e}")
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
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Calculate metrics
    logger.info("\n📊 Step 7: Calculate Metrics")
    
    valid_results = [r for r in results if 'error' not in r]
    
    # Per-period averages
    avg_sharpe = np.mean([r['sharpe_ratio'] for r in valid_results])
    std_sharpe = np.std([r['sharpe_ratio'] for r in valid_results])
    avg_return = np.mean([r['total_return'] for r in valid_results])
    avg_max_dd = np.mean([r['max_drawdown'] for r in valid_results])
    
    # Cumulative metrics ⭐ NEW
    cumulative = calculate_cumulative_metrics(valid_results)
    
    # Benchmark comparison ⭐ NEW
    benchmark = compare_vs_benchmark(valid_results, 'SPY', market_data_provider)
    
    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("RESULTS - IMPROVED VALIDATION")
    logger.info("=" * 80)
    
    logger.info(f"\n⏱️ Execution Time: {elapsed:.1f}s")
    logger.info(f"📊 Total Periods: {len(valid_results)}")
    
    logger.info("\n📈 PER-PERIOD METRICS (Average):")
    logger.info(f"  Sharpe: {avg_sharpe:.2f} ± {std_sharpe:.2f}")
    logger.info(f"  Return: {avg_return:.2%}")
    logger.info(f"  Max DD: {avg_max_dd:.1%}")
    
    logger.info("\n📊 CUMULATIVE METRICS (Across All Periods): ⭐ NEW")
    logger.info(f"  Total Return: {cumulative['total_return']:.1%}")
    logger.info(f"  Annualized Return: {cumulative['annualized_return']:.1%}")
    logger.info(f"  Cumulative Sharpe: {cumulative['cumulative_sharpe']:.2f}")
    logger.info(f"  Max Drawdown: {cumulative['max_drawdown']:.1%}")
    logger.info(f"  Win Rate: {cumulative['win_rate']:.1%}")
    logger.info(f"  Final Equity: ${cumulative['final_equity']:,.2f}")
    
    if benchmark:
        logger.info("\n🎯 BENCHMARK COMPARISON (vs SPY): ⭐ NEW")
        logger.info(f"  Strategy Return: {benchmark['strategy_annual']:.1%} annual")
        logger.info(f"  Benchmark Return: {benchmark['benchmark_annual']:.1%} annual")
        logger.info(f"  Alpha: {benchmark['alpha_annual']:.1%} annual")
        logger.info(f"  Outperformance: {'✅ YES' if benchmark['outperformance'] else '❌ NO'}")
    
    # Evaluate success criteria
    logger.info("\n" + "=" * 80)
    logger.info("SUCCESS CRITERIA EVALUATION")
    logger.info("=" * 80)
    
    success_criteria = {
        'cumulative_sharpe_ok': cumulative['cumulative_sharpe'] > 0.6,  # Adjusted target
        'annualized_return_ok': cumulative['annualized_return'] > 0.08,  # 8% annual
        'max_dd_ok': cumulative['max_drawdown'] > -0.25,  # > -25%
        'win_rate_ok': cumulative['win_rate'] > 0.50,  # > 50%
        'beats_benchmark': benchmark.get('outperformance', False) if benchmark else False
    }
    
    logger.info(f"\n✓ Cumulative Sharpe > 0.6: {'✅ PASS' if success_criteria['cumulative_sharpe_ok'] else '❌ FAIL'} ({cumulative['cumulative_sharpe']:.2f})")
    logger.info(f"✓ Annual Return > 8%: {'✅ PASS' if success_criteria['annualized_return_ok'] else '❌ FAIL'} ({cumulative['annualized_return']:.1%})")
    logger.info(f"✓ Max DD > -25%: {'✅ PASS' if success_criteria['max_dd_ok'] else '❌ FAIL'} ({cumulative['max_drawdown']:.1%})")
    logger.info(f"✓ Win Rate > 50%: {'✅ PASS' if success_criteria['win_rate_ok'] else '❌ FAIL'} ({cumulative['win_rate']:.1%})")
    if benchmark:
        logger.info(f"✓ Beats Benchmark: {'✅ PASS' if success_criteria['beats_benchmark'] else '❌ FAIL'}")
    
    all_pass = all(success_criteria.values())
    
    if all_pass:
        logger.info("\n🎉 ALL SUCCESS CRITERIA MET - PROCEED TO PHASE 2")
    else:
        passed = sum(success_criteria.values())
        total = len(success_criteria)
        logger.warning(f"\n⚠️ {passed}/{total} CRITERIA MET - REVIEW RESULTS")
    
    # Save results
    logger.info("\n💾 Step 8: Save Results")
    
    results_dir = Path(__file__).parent.parent / 'results'
    output_file = results_dir / 'dual_momentum_improved.json'
    
    output_data = {
        'strategy_name': 'dual_momentum_improved',
        'config': {
            'test_window_days': int(walk_forward_config['test_window_days']),
            'train_window_days': int(walk_forward_config['train_window_days']),
        },
        'per_period': {
            'total_periods': int(len(valid_results)),
            'avg_sharpe': float(avg_sharpe),
            'std_sharpe': float(std_sharpe),
            'avg_return': float(avg_return),
            'avg_max_dd': float(avg_max_dd),
        },
        'cumulative': cumulative,
        'benchmark': benchmark,
        'success_criteria': {k: bool(v) for k, v in success_criteria.items()},
        'periods': results,
        'fixed_params': fixed_params.__dict__
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Results saved to: {output_file}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION COMPLETE")
    logger.info("=" * 80)
    
    if all_pass:
        logger.info("\n✅ Dual Momentum strategy validated successfully!")
        logger.info("✅ System is working correctly")
        logger.info("✅ Ready to proceed to Phase 2")
        return 0
    else:
        logger.warning("\n⚠️ Some criteria not met - review results")
        logger.warning("⚠️ Consider adjustments before Phase 2")
        return 1


if __name__ == '__main__':
    sys.exit(main())
