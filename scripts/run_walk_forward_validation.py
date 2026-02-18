"""
Walk-Forward Validation Script - Multi-Asset V1 Strategy

Tests strategy across multiple market cycles:
- 2022: Bear market (-33% QQQ)
- 2023: Recovery (+55% QQQ)
- 2024: Bull market (+25% QQQ)
- 2025: Continuation

Goal: Validate strategy robustness across different market conditions
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from auronai.backtesting.swing_multi_asset_v1 import SwingMultiAssetV1

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_period_backtest(period_name, start_date, end_date, test_start_date):
    """Run backtest for a specific period."""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING PERIOD: {period_name}")
    logger.info(f"{'='*80}")
    
    # Universo Multi-Asset V1
    symbols = [
        # Tech stocks
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
        'NVDA', 'TSLA', 'NFLX', 'AVGO', 'COST',
        # Tech ETFs
        'SMH', 'XLK', 'SOXX', 'IGV', 'HACK',
    ]
    
    # Configuración baseline
    strategy = SwingMultiAssetV1(
        symbols=symbols,
        benchmark='QQQ',
        initial_capital=1000.0,
        base_risk_budget=0.20,
        defensive_risk_budget=0.05,
        top_k=3,
        tp_multiplier=1.05,
        max_holding_days=7,
        dd_threshold_1=0.05,
        dd_threshold_2=0.08,
        dd_threshold_3=0.10,
        cooldown_days=10
    )
    
    # Run backtest
    results = strategy.run_backtest(
        start_date=start_date,
        end_date=end_date,
        test_start_date=test_start_date
    )
    
    if 'error' in results:
        logger.error(f"Error in {period_name}: {results['error']}")
        return None
    
    # Display results
    metrics = results['metrics']
    
    print(f"\n{period_name} RESULTS:")
    print(f"  Period: {test_start_date} to {end_date}")
    print(f"  Return: {metrics['total_return']:.2f}%")
    print(f"  CAGR: {metrics['cagr']:.2f}%")
    print(f"  Sharpe: {metrics['sharpe_ratio']:.2f}")
    print(f"  Max DD: {metrics['max_drawdown']:.2f}%")
    print(f"  Win Rate: {metrics['win_rate']:.2f}%")
    print(f"  Trades: {metrics['num_trades']}")
    print(f"  Expectancy: {metrics['expectancy']:.2f}%")
    
    return results


def main():
    """Run walk-forward validation across multiple periods."""
    
    logger.info("="*80)
    logger.info("WALK-FORWARD VALIDATION - MULTI-ASSET V1")
    logger.info("="*80)
    logger.info("\nTesting strategy across 4 market cycles:")
    logger.info("  2022: Bear market")
    logger.info("  2023: Recovery")
    logger.info("  2024: Bull market")
    logger.info("  2025: Continuation")
    
    # Define test periods
    # Format: (name, full_start, full_end, test_start)
    # full_start needs to be ~200 days before test_start for EMA200
    periods = [
        ('2022_BEAR', '2021-01-01', '2022-12-31', '2022-01-01'),
        ('2023_RECOVERY', '2022-01-01', '2023-12-31', '2023-01-01'),
        ('2024_BULL', '2023-01-01', '2024-12-31', '2024-01-01'),
        ('2025_CONTINUATION', '2024-01-01', '2025-12-31', '2025-01-01'),
    ]
    
    all_results = {}
    
    # Run backtest for each period
    for period_name, start_date, end_date, test_start_date in periods:
        results = run_period_backtest(period_name, start_date, end_date, test_start_date)
        
        if results:
            all_results[period_name] = results
    
    # Save individual results
    results_dir = project_root / 'results' / 'walk_forward'
    results_dir.mkdir(exist_ok=True, parents=True)
    
    for period_name, results in all_results.items():
        # Save JSON
        json_file = results_dir / f'{period_name.lower()}_results.json'
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save trades CSV
        trades_df = pd.DataFrame(results['trades'])
        csv_file = results_dir / f'{period_name.lower()}_trades.csv'
        trades_df.to_csv(csv_file, index=False)
    
    logger.info(f"\nIndividual results saved to: {results_dir}")
    
    # Aggregate analysis
    print("\n" + "="*80)
    print("AGGREGATE ANALYSIS")
    print("="*80)
    
    summary_data = []
    
    for period_name, results in all_results.items():
        metrics = results['metrics']
        summary_data.append({
            'Period': period_name.replace('_', ' '),
            'Return (%)': metrics['total_return'],
            'CAGR (%)': metrics['cagr'],
            'Sharpe': metrics['sharpe_ratio'],
            'Max DD (%)': metrics['max_drawdown'],
            'Win Rate (%)': metrics['win_rate'],
            'Trades': metrics['num_trades'],
            'Expectancy (%)': metrics['expectancy'],
            'Profit Factor': metrics['profit_factor']
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    print("\n" + summary_df.to_string(index=False))
    
    # Calculate aggregate metrics
    print("\n" + "="*80)
    print("AGGREGATE METRICS")
    print("="*80)
    
    avg_return = summary_df['Return (%)'].mean()
    avg_cagr = summary_df['CAGR (%)'].mean()
    avg_sharpe = summary_df['Sharpe'].mean()
    avg_dd = summary_df['Max DD (%)'].mean()
    avg_wr = summary_df['Win Rate (%)'].mean()
    total_trades = summary_df['Trades'].sum()
    avg_expectancy = summary_df['Expectancy (%)'].mean()
    
    print(f"\nAverage Return: {avg_return:.2f}%")
    print(f"Average CAGR: {avg_cagr:.2f}%")
    print(f"Average Sharpe: {avg_sharpe:.2f}")
    print(f"Average Max DD: {avg_dd:.2f}%")
    print(f"Average Win Rate: {avg_wr:.2f}%")
    print(f"Total Trades: {total_trades}")
    print(f"Average Expectancy: {avg_expectancy:.2f}%")
    
    # Consistency check
    print("\n" + "="*80)
    print("CONSISTENCY CHECK")
    print("="*80)
    
    positive_periods = sum(1 for r in summary_df['Return (%)'] if r > 0)
    sharpe_above_1 = sum(1 for s in summary_df['Sharpe'] if s > 1.0)
    dd_below_10 = sum(1 for dd in summary_df['Max DD (%)'] if dd < 10.0)
    
    print(f"\nPositive return periods: {positive_periods}/4 ({positive_periods/4*100:.0f}%)")
    print(f"Sharpe > 1.0: {sharpe_above_1}/4 ({sharpe_above_1/4*100:.0f}%)")
    print(f"Max DD < 10%: {dd_below_10}/4 ({dd_below_10/4*100:.0f}%)")
    
    # Verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    
    if positive_periods >= 3 and avg_sharpe > 0.8 and avg_dd < 15:
        print("\n✅ STRATEGY IS ROBUST")
        print("La estrategia funciona consistentemente en múltiples ciclos.")
        print("Puedes proceder con confianza.")
        verdict = "ROBUST"
    elif positive_periods >= 2 and avg_sharpe > 0.5:
        print("\n⚠️  STRATEGY NEEDS IMPROVEMENT")
        print("La estrategia funciona pero tiene debilidades.")
        print("Considera agregar short capability para bear markets.")
        verdict = "NEEDS_IMPROVEMENT"
    else:
        print("\n❌ STRATEGY IS NOT ROBUST")
        print("La estrategia no funciona consistentemente.")
        print("Requiere rediseño fundamental.")
        verdict = "NOT_ROBUST"
    
    # Save summary
    summary_file = results_dir / 'walk_forward_summary.csv'
    summary_df.to_csv(summary_file, index=False)
    logger.info(f"\nSummary saved to: {summary_file}")
    
    # Save aggregate metrics
    aggregate_metrics = {
        'verdict': verdict,
        'avg_return': avg_return,
        'avg_cagr': avg_cagr,
        'avg_sharpe': avg_sharpe,
        'avg_max_dd': avg_dd,
        'avg_win_rate': avg_wr,
        'total_trades': int(total_trades),
        'avg_expectancy': avg_expectancy,
        'positive_periods': int(positive_periods),
        'sharpe_above_1': int(sharpe_above_1),
        'dd_below_10': int(dd_below_10),
        'periods_tested': len(all_results)
    }
    
    aggregate_file = results_dir / 'aggregate_metrics.json'
    with open(aggregate_file, 'w') as f:
        json.dump(aggregate_metrics, f, indent=2)
    
    # Create comparison chart
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Return by period
    axes[0, 0].bar(summary_df['Period'], summary_df['Return (%)'], color='steelblue')
    axes[0, 0].axhline(y=0, color='red', linestyle='--', alpha=0.5)
    axes[0, 0].set_title('Return by Period', fontsize=14, fontweight='bold')
    axes[0, 0].set_ylabel('Return (%)')
    axes[0, 0].tick_params(axis='x', rotation=45)
    axes[0, 0].grid(True, alpha=0.3)
    
    # Sharpe by period
    axes[0, 1].bar(summary_df['Period'], summary_df['Sharpe'], color='green')
    axes[0, 1].axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Target: 1.0')
    axes[0, 1].set_title('Sharpe Ratio by Period', fontsize=14, fontweight='bold')
    axes[0, 1].set_ylabel('Sharpe Ratio')
    axes[0, 1].tick_params(axis='x', rotation=45)
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Max DD by period
    axes[1, 0].bar(summary_df['Period'], summary_df['Max DD (%)'], color='red')
    axes[1, 0].axhline(y=10, color='orange', linestyle='--', alpha=0.5, label='Warning: 10%')
    axes[1, 0].set_title('Max Drawdown by Period', fontsize=14, fontweight='bold')
    axes[1, 0].set_ylabel('Max DD (%)')
    axes[1, 0].tick_params(axis='x', rotation=45)
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Win Rate by period
    axes[1, 1].bar(summary_df['Period'], summary_df['Win Rate (%)'], color='purple')
    axes[1, 1].axhline(y=50, color='red', linestyle='--', alpha=0.5, label='Breakeven: 50%')
    axes[1, 1].set_title('Win Rate by Period', fontsize=14, fontweight='bold')
    axes[1, 1].set_ylabel('Win Rate (%)')
    axes[1, 1].tick_params(axis='x', rotation=45)
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    chart_file = results_dir / 'walk_forward_comparison.png'
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    logger.info(f"Comparison chart saved to: {chart_file}")
    
    print("\n" + "="*80)
    print("WALK-FORWARD VALIDATION COMPLETE")
    print("="*80)
    print(f"\nResults directory: {results_dir}")
    print(f"  - Individual period results (JSON + CSV)")
    print(f"  - Summary CSV")
    print(f"  - Aggregate metrics JSON")
    print(f"  - Comparison chart PNG")


if __name__ == '__main__':
    main()
