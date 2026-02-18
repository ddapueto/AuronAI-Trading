#!/usr/bin/env python3
"""
Walk-Forward with FIXED parameters and diversified portfolio.

This tests if the strategy works WITHOUT optimization (no overfitting).
If it works with fixed params, the strategy is solid.
If it doesn't, we need to fix the strategy logic itself.
"""

from datetime import datetime
import json

from auronai.backtesting.rolling_walk_forward import RollingWalkForwardOptimizer
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Run walk-forward with fixed parameters."""
    
    print("\n" + "="*80)
    print("WALK-FORWARD WITH FIXED PARAMETERS (NO OPTIMIZATION)")
    print("="*80)
    print("\nTesting if strategy works WITHOUT overfitting to past data.")
    print("This will take approximately 30-40 minutes.")
    print("="*80 + "\n")
    
    # Diversified portfolio: 15 symbols across sectors
    symbols = [
        # Technology (5)
        'AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA',
        # Financials (3)
        'JPM', 'BAC', 'WFC',
        # Energy (2)
        'XOM', 'CVX',
        # Healthcare (2)
        'JNJ', 'PFE',
        # Consumer (3)
        'WMT', 'HD', 'MCD'
    ]
    
    # Date range: 2023-2025 (3 years)
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2025, 12, 31)
    
    # FIXED parameters (NO optimization)
    # These are reasonable defaults based on momentum research
    param_grid = {
        'top_k': [5],              # Hold top 5 stocks
        'holding_days': [10],      # 10-day holding period
        'tp_multiplier': [1.05],   # 5% take profit
        'risk_budget': [0.2],      # 20% total exposure
        'defensive_risk_budget': [0.05]
    }
    
    print(f"Configuration:")
    print(f"  Strategy: long_momentum")
    print(f"  Symbols: {len(symbols)} diversified across sectors")
    print(f"    Tech: AAPL, MSFT, GOOGL, NVDA, TSLA")
    print(f"    Financials: JPM, BAC, WFC")
    print(f"    Energy: XOM, CVX")
    print(f"    Healthcare: JNJ, PFE")
    print(f"    Consumer: WMT, HD, MCD")
    print(f"  Period: {start_date.date()} to {end_date.date()}")
    print(f"  Train window: 180 days (6 months)")
    print(f"  Test window: 30 days (1 month)")
    print(f"  Re-optimize: monthly")
    print(f"\nFIXED Parameters (NO optimization):")
    print(f"  top_k: 5")
    print(f"  holding_days: 10")
    print(f"  tp_multiplier: 1.05 (5% TP)")
    print(f"  risk_budget: 20%")
    print(f"\nExpected:")
    print(f"  Periods: ~36")
    print(f"  Combinations per period: 1 (fixed params)")
    print(f"  Total backtests: ~36")
    print(f"  Estimated time: ~30-40 minutes")
    print("="*80 + "\n")
    
    # Create optimizer with longer training window
    optimizer = RollingWalkForwardOptimizer(
        train_window_days=180,  # 6 months (was 90)
        test_window_days=30,    # 1 month
        reoptimize_frequency='monthly',
        initial_capital=10000.0,
        commission_rate=0.0,
        slippage_rate=0.0005
    )
    
    # Run optimization
    try:
        print("STARTING OPTIMIZATION...")
        print("="*80 + "\n")
        
        result = optimizer.run(
            strategy_name='long_momentum',
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            param_grid=param_grid
        )
        
        # Print results
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        
        print(f"\nTotal periods: {result.total_periods}")
        
        # Count periods with trades
        train_with_trades = sum(1 for p in result.periods if p.train_sharpe != 0)
        test_with_trades = sum(1 for p in result.periods if p.test_sharpe != 0)
        
        print(f"\nPeriods with trades:")
        print(f"  Training: {train_with_trades}/{result.total_periods} ({train_with_trades/result.total_periods*100:.1f}%)")
        print(f"  Testing:  {test_with_trades}/{result.total_periods} ({test_with_trades/result.total_periods*100:.1f}%)")
        
        print(f"\nMetrics:")
        print(f"  Avg Train Sharpe: {result.avg_train_sharpe:.2f}")
        print(f"  Avg Test Sharpe: {result.avg_test_sharpe:.2f} ± {result.std_test_sharpe:.2f}")
        print(f"  Degradation: {result.degradation:.1%}")
        print(f"  Avg Test Return: {result.avg_test_return:.2%} per month")
        print(f"  Avg Test Max DD: {result.avg_test_max_dd:.2%}")
        
        # Interpretation
        print(f"\nInterpretation:")
        if result.degradation < 0.2:  # Less than 20%
            print(f"  ✅ EXCELLENT: Low overfitting (< 20% degradation)")
            print(f"     Strategy is robust and generalizes well!")
        elif result.degradation < 0.4:  # 20-40%
            print(f"  ⚠️  ACCEPTABLE: Moderate overfitting (20-40% degradation)")
            print(f"     Strategy works but could be improved")
        else:  # > 40%
            print(f"  ❌ POOR: High overfitting (> 40% degradation)")
            print(f"     Strategy doesn't generalize to new data")
        
        if result.avg_test_sharpe > 1.0:
            print(f"  ✅ Test Sharpe > 1.0: Good risk-adjusted returns")
        elif result.avg_test_sharpe > 0:
            print(f"  ⚠️  Test Sharpe > 0: Positive but modest returns")
        else:
            print(f"  ❌ Test Sharpe < 0: Losing money on average")
        
        # Best/worst periods
        print(f"\nBest period:")
        print(f"  Period {result.best_period.period_id}: Test Sharpe = {result.best_period.test_sharpe:.2f}")
        print(f"  {result.best_period.test_start.date()} to {result.best_period.test_end.date()}")
        
        print(f"\nWorst period:")
        print(f"  Period {result.worst_period.period_id}: Test Sharpe = {result.worst_period.test_sharpe:.2f}")
        print(f"  {result.worst_period.test_start.date()} to {result.worst_period.test_end.date()}")
        
        # Parameter stability (should be 100% since fixed)
        print(f"\nParameter stability:")
        for param, count in sorted(result.param_frequency.items(), key=lambda x: x[1], reverse=True):
            pct = count / result.total_periods * 100
            print(f"  {param}: {count} times ({pct:.1f}%)")
        
        # Save results
        output_file = 'results/walk_forward/fixed_params_15symbols.json'
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        print(f"\n✅ Results saved to: {output_file}")
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        if result.degradation < 0.4 and result.avg_test_sharpe > 0:
            print("\n✅ Strategy shows promise with fixed parameters!")
            print("   Next steps:")
            print("   1. Analyze which market conditions work best")
            print("   2. Add regime filters to avoid bad periods")
            print("   3. Consider position sizing adjustments")
        else:
            print("\n⚠️  Strategy needs improvement:")
            print("   Issues:")
            if result.degradation >= 0.4:
                print("   - High degradation: Strategy doesn't generalize")
            if result.avg_test_sharpe <= 0:
                print("   - Negative returns: Losing money on average")
            print("\n   Recommendations:")
            print("   1. Review entry/exit logic")
            print("   2. Strengthen regime detection")
            print("   3. Add more filters (volatility, trend strength)")
            print("   4. Consider different holding periods")
        
        print("\n" + "="*80 + "\n")
        
        return 0
        
    except Exception as e:
        print("\n" + "="*80)
        print("❌ ERROR")
        print("="*80)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
