#!/usr/bin/env python3
"""
Test walk-forward with 30-day test window.

This tests if a longer test window (30 days vs 7 days) produces trades.
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
    """Test walk-forward with 30-day test window."""
    print("\n" + "="*80)
    print("TESTING WALK-FORWARD WITH 30-DAY TEST WINDOW")
    print("="*80)
    print("\nThis tests if longer test periods produce trades.")
    print("="*80 + "\n")
    
    # Configuration - 30 day test window
    config = {
        'strategy_name': 'long_momentum',
        'symbols': ['AAPL', 'MSFT', 'GOOGL'],  # 3 symbols for speed
        'start_date': datetime(2024, 1, 1),
        'end_date': datetime(2024, 4, 1),  # 3 months
        'train_window_days': 180,  # 6 months
        'test_window_days': 30,    # 1 MONTH (instead of 7 days)
        'reoptimize_frequency': 'monthly',  # Monthly for speed
        'param_grid': {
            'top_k': [3, 4],  # Only 2 values
            'holding_days': [7],  # Only 1 value
            'tp_multiplier': [1.05],  # Only 1 value
            'risk_budget': [0.20],
            'defensive_risk_budget': [0.05]
        }
    }
    
    print("Configuration:")
    print(f"  Strategy: {config['strategy_name']}")
    print(f"  Symbols: {', '.join(config['symbols'])}")
    print(f"  Period: {config['start_date'].date()} to {config['end_date'].date()}")
    print(f"  Train window: {config['train_window_days']} days")
    print(f"  Test window: {config['test_window_days']} days (1 MONTH)")
    print(f"  Re-optimize: {config['reoptimize_frequency']}")
    
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
        print("RESULTS")
        print("="*80)
        
        print(f"\nTotal periods: {result.total_periods}")
        
        # Count periods with trades
        periods_with_train_trades = sum(1 for p in result.periods if p.train_sharpe != 0)
        periods_with_test_trades = sum(1 for p in result.periods if p.test_sharpe != 0)
        
        print(f"\nPeriods with trades:")
        print(f"  Training: {periods_with_train_trades}/{result.total_periods} ({periods_with_train_trades/result.total_periods*100:.1f}%)")
        print(f"  Testing:  {periods_with_test_trades}/{result.total_periods} ({periods_with_test_trades/result.total_periods*100:.1f}%)")
        
        if periods_with_test_trades > 0:
            print("\n✅ SUCCESS: Test periods have trades!")
            print(f"\nMetrics:")
            print(f"  Avg Train Sharpe: {result.avg_train_sharpe:.2f}")
            print(f"  Avg Test Sharpe: {result.avg_test_sharpe:.2f} ± {result.std_test_sharpe:.2f}")
            print(f"  Degradation: {result.degradation:.1%}")
            print(f"  Avg Test Return: {result.avg_test_return:.2%}")
        else:
            print("\n❌ PROBLEM: Still no trades in test periods")
            print("This may indicate:")
            print("  1. Market regime not suitable (not BULL)")
            print("  2. Strategy filters too restrictive")
            print("  3. Need even longer test window")
        
        # Show first few periods
        print(f"\nFirst 3 periods:")
        for period in result.periods[:3]:
            print(f"  Period {period.period_id}:")
            print(f"    Train: {period.train_start.date()} to {period.train_end.date()}")
            print(f"    Test:  {period.test_start.date()} to {period.test_end.date()}")
            print(f"    Train Sharpe: {period.train_sharpe:.2f}")
            print(f"    Test Sharpe:  {period.test_sharpe:.2f}")
            print(f"    Test Return:  {period.test_return:.2%}")
        
        # Save results
        output_dir = Path("results/walk_forward")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "test_30day_window.json"
        
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        print(f"\n📁 Results saved to: {output_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
