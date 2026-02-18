#!/usr/bin/env python3
"""
Test rolling walk-forward optimization with a small date range.

This script tests the implementation with just 2-3 periods to verify
it works correctly before running the full optimization.
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
    """Test rolling walk-forward with small date range."""
    print("\n" + "="*80)
    print("TESTING ROLLING WALK-FORWARD OPTIMIZATION")
    print("="*80)
    print("\nThis is a quick test with a small date range (2 months)")
    print("to verify the implementation works correctly.")
    print("="*80 + "\n")
    
    # Configuration - SMALL for testing
    config = {
        'strategy_name': 'long_momentum',
        'symbols': ['AAPL', 'MSFT', 'GOOGL'],  # Only 3 symbols
        'start_date': datetime(2024, 1, 1),  # First test period starts here
        'end_date': datetime(2024, 2, 15),  # About 6 weeks of testing
        'train_window_days': 90,  # 3 months (will use data from Oct-Dec 2023)
        'test_window_days': 7,    # 1 week
        'reoptimize_frequency': 'weekly',
        'param_grid': {
            'top_k': [2, 3],  # Only 2 values
            'holding_days': [7, 10],  # Only 2 values
            'tp_multiplier': [1.05],  # Only 1 value
            'risk_budget': [0.20],
            'defensive_risk_budget': [0.05]
        }
    }
    
    print("\n⚠️  Note: Training data will be fetched from ~3 months before start_date")
    print(f"    (approximately Oct 2023 - Dec 2023 for first period)")
    
    print("Test Configuration:")
    print(f"  Strategy: {config['strategy_name']}")
    print(f"  Symbols: {', '.join(config['symbols'])}")
    print(f"  Period: {config['start_date'].date()} to {config['end_date'].date()}")
    print(f"  Train window: {config['train_window_days']} days")
    print(f"  Test window: {config['test_window_days']} days")
    print(f"\nParameter grid (small for testing):")
    for param, values in config['param_grid'].items():
        print(f"  {param}: {values}")
    
    # Calculate expected periods
    total_days = (config['end_date'] - config['start_date']).days
    usable_days = total_days
    expected_periods = usable_days // 7  # Weekly
    expected_optimizations = expected_periods * len(config['param_grid']['top_k']) * \
                            len(config['param_grid']['holding_days']) * \
                            len(config['param_grid']['tp_multiplier'])
    
    print(f"\nExpected:")
    print(f"  Periods: ~{expected_periods}")
    print(f"  Total backtests: ~{expected_optimizations}")
    print(f"  Estimated time: ~{expected_optimizations * 2 / 60:.1f} minutes")
    
    print("\n" + "="*80)
    print("STARTING TEST...")
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
        print("TEST RESULTS")
        print("="*80)
        
        print(f"\nStrategy: {result.strategy_name}")
        print(f"Total periods: {result.total_periods}")
        
        print(f"\nIn-Sample (TRAIN):")
        print(f"  Avg Sharpe: {result.avg_train_sharpe:.2f}")
        
        print(f"\nOut-of-Sample (TEST):")
        print(f"  Avg Sharpe: {result.avg_test_sharpe:.2f} ± {result.std_test_sharpe:.2f}")
        print(f"  Avg Return: {result.avg_test_return:.1%}")
        print(f"  Avg Max DD: {result.avg_test_max_dd:.1%}")
        
        print(f"\nDegradation: {result.degradation:.1%}")
        
        print(f"\nParameter Frequency:")
        for param, count in sorted(result.param_frequency.items(), key=lambda x: x[1], reverse=True):
            percentage = count / result.total_periods * 100
            print(f"  {param}: {count} times ({percentage:.1f}%)")
        
        # Save results
        output_dir = Path("results/rolling_walk_forward")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "test_rolling_wf.json"
        
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        print(f"\n📁 Test results saved to: {output_file}")
        
        print("\n" + "="*80)
        print("✅ TEST COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\nThe implementation is working correctly.")
        print("You can now run the full optimization with:")
        print("  python scripts/run_rolling_walk_forward.py")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        print("\nPlease check the error above and fix before running full optimization.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
