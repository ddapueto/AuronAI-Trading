#!/usr/bin/env python3
"""
Test walk-forward optimization fix.

Quick test with 2 periods to verify the fix works.
"""

from datetime import datetime
import json

from auronai.backtesting.rolling_walk_forward import RollingWalkForwardOptimizer
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Run quick walk-forward test."""
    
    print("\n" + "="*80)
    print("TESTING WALK-FORWARD FIX")
    print("="*80)
    print("\nThis will test 2 periods to verify the error is fixed.")
    print("="*80 + "\n")
    
    # Configuration
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 3, 31)  # Just 3 months for quick test
    
    # Parameter grid (smaller for quick test)
    param_grid = {
        'top_k': [3, 5],
        'holding_days': [10],
        'tp_multiplier': [1.05],
        'risk_budget': [0.2],
        'defensive_risk_budget': [0.05]
    }
    
    print(f"Configuration:")
    print(f"  Strategy: long_momentum")
    print(f"  Symbols: {', '.join(symbols)}")
    print(f"  Period: {start_date.date()} to {end_date.date()}")
    print(f"  Train window: 90 days")
    print(f"  Test window: 30 days")
    print(f"  Re-optimize: monthly")
    print(f"\nParameter grid:")
    print(f"  top_k: {param_grid['top_k']}")
    print(f"  holding_days: {param_grid['holding_days']}")
    print(f"  tp_multiplier: {param_grid['tp_multiplier']}")
    print(f"\nExpected: ~2 periods, 2 combinations each = 4 backtests")
    print("="*80 + "\n")
    
    # Create optimizer
    optimizer = RollingWalkForwardOptimizer(
        train_window_days=90,
        test_window_days=30,
        reoptimize_frequency='monthly',
        initial_capital=10000.0,
        commission_rate=0.0,
        slippage_rate=0.0005
    )
    
    # Run optimization
    try:
        result = optimizer.run(
            strategy_name='long_momentum',
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            param_grid=param_grid
        )
        
        # Print results
        print("\n" + "="*80)
        print("✅ TEST PASSED - NO ERRORS!")
        print("="*80)
        print(f"\nResults:")
        print(f"  Total periods: {result.total_periods}")
        print(f"  Avg Train Sharpe: {result.avg_train_sharpe:.2f}")
        print(f"  Avg Test Sharpe: {result.avg_test_sharpe:.2f} ± {result.std_test_sharpe:.2f}")
        print(f"  Degradation: {result.degradation:.1%}")
        print(f"  Avg Test Return: {result.avg_test_return:.1%}")
        print(f"  Avg Test Max DD: {result.avg_test_max_dd:.1%}")
        
        # Save results
        output_file = 'results/walk_forward/test_fix.json'
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        print(f"\n✅ Results saved to: {output_file}")
        print("\n" + "="*80)
        print("FIX VERIFIED - Walk-forward optimization is working!")
        print("="*80 + "\n")
        
        return 0
        
    except Exception as e:
        print("\n" + "="*80)
        print("❌ TEST FAILED")
        print("="*80)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
