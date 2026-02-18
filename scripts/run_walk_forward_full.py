#!/usr/bin/env python3
"""
Run full walk-forward optimization (2023-2025).

This is the recommended configuration for robust validation.
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
    """Run full walk-forward optimization."""
    print("\n" + "="*80)
    print("FULL WALK-FORWARD OPTIMIZATION (2023-2025)")
    print("="*80)
    print("\nThis will take approximately 1 hour.")
    print("="*80 + "\n")
    
    # Configuration - Full validation
    config = {
        'strategy_name': 'long_momentum',
        'symbols': ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA'],
        'start_date': datetime(2023, 1, 1),
        'end_date': datetime(2025, 12, 31),
        'train_window_days': 90,   # 3 months
        'test_window_days': 30,    # 1 month
        'reoptimize_frequency': 'monthly',
        'param_grid': {
            'top_k': [2, 3, 4, 5],
            'holding_days': [7, 10, 14],
            'tp_multiplier': [1.03, 1.05, 1.07],
            'risk_budget': [0.20],
            'defensive_risk_budget': [0.05]
        }
    }
    
    print("Configuration:")
    print(f"  Strategy: {config['strategy_name']}")
    print(f"  Symbols: {', '.join(config['symbols'])}")
    print(f"  Period: {config['start_date'].date()} to {config['end_date'].date()}")
    print(f"  Train window: {config['train_window_days']} days (3 months)")
    print(f"  Test window: {config['test_window_days']} days (1 month)")
    print(f"  Re-optimize: {config['reoptimize_frequency']}")
    print(f"\nParameter grid:")
    for param, values in config['param_grid'].items():
        if param not in ['risk_budget', 'defensive_risk_budget']:
            print(f"  {param}: {values}")
    
    # Calculate expected
    total_months = 36  # 2023-2025
    combinations = 4 * 3 * 3  # 36
    total_backtests = total_months * combinations
    estimated_minutes = total_backtests * 3 / 60
    
    print(f"\nExpected:")
    print(f"  Periods: ~{total_months}")
    print(f"  Combinations per period: {combinations}")
    print(f"  Total backtests: ~{total_backtests}")
    print(f"  Estimated time: ~{estimated_minutes:.0f} minutes ({estimated_minutes/60:.1f} hours)")
    
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
        
        print(f"\nTotal periods: {result.total_periods}")
        
        # Count periods with trades
        periods_with_train_trades = sum(1 for p in result.periods if p.train_sharpe != 0)
        periods_with_test_trades = sum(1 for p in result.periods if p.test_sharpe != 0)
        
        print(f"\nPeriods with trades:")
        print(f"  Training: {periods_with_train_trades}/{result.total_periods} ({periods_with_train_trades/result.total_periods*100:.1f}%)")
        print(f"  Testing:  {periods_with_test_trades}/{result.total_periods} ({periods_with_test_trades/result.total_periods*100:.1f}%)")
        
        print(f"\nMetrics:")
        print(f"  Avg Train Sharpe: {result.avg_train_sharpe:.2f}")
        print(f"  Avg Test Sharpe: {result.avg_test_sharpe:.2f} ± {result.std_test_sharpe:.2f}")
        print(f"  Degradation: {result.degradation:.1%}")
        print(f"  Avg Test Return: {result.avg_test_return:.2%} per month")
        print(f"  Avg Test Max DD: {result.avg_test_max_dd:.2%}")
        
        # Interpretation
        print(f"\nInterpretation:")
        if result.degradation < 0.20:
            print("  ✅ EXCELLENT: Strategy is very robust (< 20% degradation)")
        elif result.degradation < 0.30:
            print("  ✅ GOOD: Strategy is robust (< 30% degradation)")
        elif result.degradation < 0.40:
            print("  ⚠️  ACCEPTABLE: Some overfitting (30-40% degradation)")
        else:
            print("  ❌ POOR: High overfitting (> 40% degradation)")
        
        # Parameter stability
        print(f"\nMost common parameters:")
        sorted_params = sorted(result.param_frequency.items(), key=lambda x: x[1], reverse=True)
        for param, count in sorted_params[:5]:
            percentage = count / result.total_periods * 100
            print(f"  {param}: {count} times ({percentage:.1f}%)")
        
        # Save results
        output_dir = Path("results/walk_forward")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"full_wf_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        print(f"\n📁 Results saved to: {output_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during optimization: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
