#!/usr/bin/env python3
"""
Run rolling walk-forward optimization.

This script implements rolling walk-forward optimization where parameters
are re-optimized weekly using only past data, simulating real-world trading.

Usage:
    python scripts/run_rolling_walk_forward.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import datetime
import json

from auronai.backtesting.rolling_walk_forward import RollingWalkForwardOptimizer
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Run rolling walk-forward optimization."""
    print("\n" + "="*80)
    print("ROLLING WALK-FORWARD OPTIMIZATION")
    print("="*80)
    print("\nThis will:")
    print("1. Re-optimize parameters WEEKLY using only past data")
    print("2. Test with optimized parameters for the following week")
    print("3. Repeat for entire period (2020-2025)")
    print("\nThis simulates real-world trading where you re-optimize regularly.")
    print("\n⚠️  WARNING: This will take 1-2 hours to complete!")
    print("="*80 + "\n")
    
    # Configuration
    config = {
        'strategy_name': 'long_momentum',
        'symbols': ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA'],
        'start_date': datetime(2020, 1, 1),
        'end_date': datetime(2025, 12, 31),
        'train_window_days': 180,  # 6 months
        'test_window_days': 7,     # 1 week
        'reoptimize_frequency': 'weekly',
        'param_grid': {
            'top_k': [2, 3, 4, 5],
            'holding_days': [7, 10, 14],
            'tp_multiplier': [1.03, 1.05, 1.07],
            'risk_budget': [0.20],  # Fixed
            'defensive_risk_budget': [0.05]  # Fixed
        }
    }
    
    print("Configuration:")
    print(f"  Strategy: {config['strategy_name']}")
    print(f"  Symbols: {', '.join(config['symbols'])}")
    print(f"  Period: {config['start_date'].date()} to {config['end_date'].date()}")
    print(f"  Train window: {config['train_window_days']} days (~6 months)")
    print(f"  Test window: {config['test_window_days']} days (1 week)")
    print(f"  Re-optimize: {config['reoptimize_frequency']}")
    print(f"\nParameter grid:")
    for param, values in config['param_grid'].items():
        print(f"  {param}: {values}")
    
    # Calculate expected periods
    total_days = (config['end_date'] - config['start_date']).days
    usable_days = total_days - config['train_window_days']
    expected_periods = usable_days // 7  # Weekly
    expected_optimizations = expected_periods * len(config['param_grid']['top_k']) * \
                            len(config['param_grid']['holding_days']) * \
                            len(config['param_grid']['tp_multiplier'])
    
    print(f"\nExpected:")
    print(f"  Periods: ~{expected_periods}")
    print(f"  Total backtests: ~{expected_optimizations}")
    print(f"  Estimated time: ~{expected_optimizations * 2 / 60:.0f} minutes")
    
    response = input("\nContinue? (y/n): ")
    if response.lower() not in ['y', 'yes', 's', 'si', 'sí']:
        print("Cancelled.")
        return 0
    
    print("\n" + "="*80)
    print("STARTING OPTIMIZATION...")
    print("="*80 + "\n")
    
    try:
        # Create optimizer
        optimizer = RollingWalkForwardOptimizer(
            train_window_days=config['train_window_days'],
            test_window_days=config['test_window_days'],
            reoptimize_frequency=config['reoptimize_frequency'],
            initial_capital=10000.0,
            commission_rate=0.0,
            slippage_rate=0.0005
        )
        
        # Run optimization
        result = optimizer.run(
            strategy_name=config['strategy_name'],
            symbols=config['symbols'],
            start_date=config['start_date'],
            end_date=config['end_date'],
            param_grid=config['param_grid']
        )
        
        # Print results
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        
        print(f"\nStrategy: {result.strategy_name}")
        print(f"Total periods: {result.total_periods}")
        print(f"Re-optimize frequency: {result.reoptimize_frequency}")
        
        print(f"\nIn-Sample (TRAIN):")
        print(f"  Avg Sharpe: {result.avg_train_sharpe:.2f}")
        
        print(f"\nOut-of-Sample (TEST):")
        print(f"  Avg Sharpe: {result.avg_test_sharpe:.2f} ± {result.std_test_sharpe:.2f}")
        print(f"  Avg Return: {result.avg_test_return:.1%}")
        print(f"  Avg Max DD: {result.avg_test_max_dd:.1%}")
        
        print(f"\nDegradation: {result.degradation:.1%}")
        
        if result.degradation < 0.20:
            print("✅ EXCELLENT: Strategy is very robust (< 20% degradation)")
        elif result.degradation < 0.30:
            print("✅ GOOD: Strategy is robust (< 30% degradation)")
        else:
            print("⚠️  WARNING: High degradation (> 30%), possible overfitting")
        
        print(f"\nBest Period:")
        print(f"  Period {result.best_period.period_id}")
        print(f"  Test Sharpe: {result.best_period.test_sharpe:.2f}")
        print(f"  Params: top_k={result.best_period.best_params.top_k}, "
              f"holding_days={result.best_period.best_params.holding_days}, "
              f"tp_multiplier={result.best_period.best_params.tp_multiplier:.3f}")
        
        print(f"\nWorst Period:")
        print(f"  Period {result.worst_period.period_id}")
        print(f"  Test Sharpe: {result.worst_period.test_sharpe:.2f}")
        print(f"  Params: top_k={result.worst_period.best_params.top_k}, "
              f"holding_days={result.worst_period.best_params.holding_days}, "
              f"tp_multiplier={result.worst_period.best_params.tp_multiplier:.3f}")
        
        print(f"\nParameter Frequency (how often each value was chosen):")
        for param, count in sorted(result.param_frequency.items(), key=lambda x: x[1], reverse=True):
            percentage = count / result.total_periods * 100
            print(f"  {param}: {count} times ({percentage:.1f}%)")
        
        # Save results
        output_dir = Path("results/rolling_walk_forward")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{result.strategy_name}_rolling_wf.json"
        
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        print(f"\n📁 Results saved to: {output_file}")
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        print(f"\n✅ Rolling walk-forward optimization completed!")
        print(f"\nKey findings:")
        print(f"  • Out-of-sample Sharpe: {result.avg_test_sharpe:.2f} ± {result.std_test_sharpe:.2f}")
        print(f"  • Expected return: {result.avg_test_return:.1%} per period")
        print(f"  • Degradation: {result.degradation:.1%}")
        
        # Most common parameters
        top_k_counts = {k: v for k, v in result.param_frequency.items() if 'top_k' in k}
        most_common_top_k = max(top_k_counts.items(), key=lambda x: x[1])[0] if top_k_counts else None
        
        if most_common_top_k:
            print(f"  • Most common top_k: {most_common_top_k.split('=')[1]}")
        
        print(f"\nThis is the REAL expected performance in production.")
        print(f"Use these metrics for decision making, not simple backtest results.")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Error during optimization: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
