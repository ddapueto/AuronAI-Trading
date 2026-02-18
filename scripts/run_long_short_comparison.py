"""
Long/Short vs Long-Only Comparison - Walk-Forward Validation

Compara estrategia Long/Short V1 vs Long-Only (Multi-Asset V1)
a través de múltiples ciclos de mercado (2022-2025).

Goal: Validar si short capability mejora performance en bear markets
sin destruir performance en bull markets.
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
from auronai.backtesting.swing_long_short_v1 import SwingLongShortV1

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_period_comparison(period_name, start_date, end_date, test_start_date):
    """Run both strategies for a specific period and compare."""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING PERIOD: {period_name}")
    logger.info(f"{'='*80}")
    
    # Universo (mismo para ambas estrategias)
    symbols = [
        # Tech stocks
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
        'NVDA', 'TSLA', 'NFLX', 'AVGO', 'COST',
        # Tech ETFs
        'SMH', 'XLK', 'SOXX', 'IGV', 'HACK',
    ]
    
    # Strategy A: Long-Only (baseline)
    logger.info("\n--- Running LONG-ONLY strategy ---")
    strategy_long_only = SwingMultiAssetV1(
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
    
    results_long_only = strategy_long_only.run_backtest(
        start_date=start_date,
        end_date=end_date,
        test_start_date=test_start_date
    )
    
    # Strategy B: Long/Short
    logger.info("\n--- Running LONG/SHORT strategy ---")
    strategy_long_short = SwingLongShortV1(
        symbols=symbols,
        benchmark='QQQ',
        initial_capital=1000.0,
        bull_risk_budget=0.20,
        bear_risk_budget=0.15,
        neutral_risk_budget=0.05,
        top_k=3,
        tp_multiplier=1.05,
        max_holding_days=7,
        dd_threshold_pause=0.12,
        dd_threshold_resume=0.08,
        cooldown_days=10
    )
    
    results_long_short = strategy_long_short.run_backtest(
        start_date=start_date,
        end_date=end_date,
        test_start_date=test_start_date
    )
    
    # Display comparison
    print(f"\n{period_name} COMPARISON:")
    print(f"  Period: {test_start_date} to {end_date}")
    print(f"\n  {'Metric':<20} {'Long-Only':>12} {'Long/Short':>12} {'Diff':>12}")
    print(f"  {'-'*60}")
    
    m_lo = results_long_only['metrics']
    m_ls = results_long_short['metrics']
    
    metrics_to_compare = [
        ('Return (%)', 'total_return'),
        ('CAGR (%)', 'cagr'),
        ('Sharpe', 'sharpe_ratio'),
        ('Max DD (%)', 'max_drawdown'),
        ('Win Rate (%)', 'win_rate'),
        ('Trades', 'num_trades'),
        ('Expectancy (%)', 'expectancy'),
        ('Profit Factor', 'profit_factor'),
    ]
    
    for label, key in metrics_to_compare:
        val_lo = m_lo[key]
        val_ls = m_ls[key]
        diff = val_ls - val_lo
        print(f"  {label:<20} {val_lo:>12.2f} {val_ls:>12.2f} {diff:>12.2f}")
    
    # Long/Short specific metrics
    if 'pct_long_trades' in m_ls:
        print(f"\n  Long/Short Breakdown:")
        print(f"    Long trades: {m_ls['num_long_trades']} ({m_ls['pct_long_trades']:.1f}%)")
        print(f"    Short trades: {m_ls['num_short_trades']} ({m_ls['pct_short_trades']:.1f}%)")
        print(f"    Long WR: {m_ls['long_win_rate']:.2f}%")
        print(f"    Short WR: {m_ls['short_win_rate']:.2f}%")
        print(f"    Long Avg P&L: {m_ls['long_avg_pnl']:.2f}%")
        print(f"    Short Avg P&L: {m_ls['short_avg_pnl']:.2f}%")
    
    return {
        'long_only': results_long_only,
        'long_short': results_long_short
    }


def main():
    """Run walk-forward comparison across multiple periods."""
    
    logger.info("="*80)
    logger.info("LONG/SHORT VS LONG-ONLY COMPARISON")
    logger.info("="*80)
    logger.info("\nTesting across 4 market cycles:")
    logger.info("  2022: Bear market")
    logger.info("  2023: Recovery")
    logger.info("  2024: Bull market")
    logger.info("  2025: Continuation")
    
    # Define test periods
    periods = [
        ('2022_BEAR', '2021-01-01', '2022-12-31', '2022-01-01'),
        ('2023_RECOVERY', '2022-01-01', '2023-12-31', '2023-01-01'),
        ('2024_BULL', '2023-01-01', '2024-12-31', '2024-01-01'),
        ('2025_CONTINUATION', '2024-01-01', '2025-12-31', '2025-01-01'),
    ]
    
    all_results = {}
    
    # Run comparison for each period
    for period_name, start_date, end_date, test_start_date in periods:
        results = run_period_comparison(period_name, start_date, end_date, test_start_date)
        all_results[period_name] = results
    
    # Save results
    results_dir = project_root / 'results' / 'long_short_comparison'
    results_dir.mkdir(exist_ok=True, parents=True)
    
    for period_name, results in all_results.items():
        # Save Long/Short results
        ls_json = results_dir / f'{period_name.lower()}_long_short_results.json'
        with open(ls_json, 'w') as f:
            json.dump(results['long_short'], f, indent=2, default=str)
        
        ls_trades = pd.DataFrame(results['long_short']['trades'])
        ls_csv = results_dir / f'{period_name.lower()}_long_short_trades.csv'
        ls_trades.to_csv(ls_csv, index=False)
    
    logger.info(f"\nResults saved to: {results_dir}")

    
    # Create consolidated comparison table
    print("\n" + "="*80)
    print("CONSOLIDATED COMPARISON TABLE (2022-2025)")
    print("="*80)
    
    comparison_data = []
    
    for period_name, results in all_results.items():
        m_lo = results['long_only']['metrics']
        m_ls = results['long_short']['metrics']
        
        comparison_data.append({
            'Period': period_name.replace('_', ' '),
            'Strategy': 'Long-Only',
            'Return (%)': m_lo['total_return'],
            'Sharpe': m_lo['sharpe_ratio'],
            'Max DD (%)': m_lo['max_drawdown'],
            'Win Rate (%)': m_lo['win_rate'],
            'Trades': m_lo['num_trades']
        })
        
        comparison_data.append({
            'Period': period_name.replace('_', ' '),
            'Strategy': 'Long/Short',
            'Return (%)': m_ls['total_return'],
            'Sharpe': m_ls['sharpe_ratio'],
            'Max DD (%)': m_ls['max_drawdown'],
            'Win Rate (%)': m_ls['win_rate'],
            'Trades': m_ls['num_trades']
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    print("\n" + comparison_df.to_string(index=False))
    
    # Save comparison table
    comparison_file = results_dir / 'comparison_table.csv'
    comparison_df.to_csv(comparison_file, index=False)
    
    # Aggregate comparison
    print("\n" + "="*80)
    print("AGGREGATE COMPARISON")
    print("="*80)
    
    aggregate_data = []
    
    for strategy_name in ['Long-Only', 'Long/Short']:
        strategy_results = [
            all_results[p]['long_only' if strategy_name == 'Long-Only' else 'long_short']
            for p in all_results.keys()
        ]
        
        avg_return = np.mean([r['metrics']['total_return'] for r in strategy_results])
        avg_sharpe = np.mean([r['metrics']['sharpe_ratio'] for r in strategy_results])
        avg_dd = np.mean([r['metrics']['max_drawdown'] for r in strategy_results])
        avg_wr = np.mean([r['metrics']['win_rate'] for r in strategy_results])
        total_trades = sum([r['metrics']['num_trades'] for r in strategy_results])
        
        positive_periods = sum(1 for r in strategy_results if r['metrics']['total_return'] > 0)
        
        aggregate_data.append({
            'Strategy': strategy_name,
            'Avg Return (%)': avg_return,
            'Avg Sharpe': avg_sharpe,
            'Avg Max DD (%)': avg_dd,
            'Avg Win Rate (%)': avg_wr,
            'Total Trades': total_trades,
            'Positive Periods': f"{positive_periods}/4"
        })
    
    aggregate_df = pd.DataFrame(aggregate_data)
    print("\n" + aggregate_df.to_string(index=False))
    
    # Save aggregate comparison
    aggregate_file = results_dir / 'aggregate_comparison.csv'
    aggregate_df.to_csv(aggregate_file, index=False)
    
    # Key improvements analysis
    print("\n" + "="*80)
    print("KEY IMPROVEMENTS ANALYSIS")
    print("="*80)
    
    for period_name in all_results.keys():
        m_lo = all_results[period_name]['long_only']['metrics']
        m_ls = all_results[period_name]['long_short']['metrics']
        
        return_improvement = m_ls['total_return'] - m_lo['total_return']
        sharpe_improvement = m_ls['sharpe_ratio'] - m_lo['sharpe_ratio']
        
        print(f"\n{period_name.replace('_', ' ')}:")
        print(f"  Return improvement: {return_improvement:+.2f}% "
              f"({m_lo['total_return']:.2f}% → {m_ls['total_return']:.2f}%)")
        print(f"  Sharpe improvement: {sharpe_improvement:+.2f} "
              f"({m_lo['sharpe_ratio']:.2f} → {m_ls['sharpe_ratio']:.2f})")
    
    # Verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    
    # Check if 2022 improved
    bear_lo = all_results['2022_BEAR']['long_only']['metrics']['total_return']
    bear_ls = all_results['2022_BEAR']['long_short']['metrics']['total_return']
    bear_improvement = bear_ls - bear_lo
    
    # Check if 2024 maintained
    bull_lo = all_results['2024_BULL']['long_only']['metrics']['total_return']
    bull_ls = all_results['2024_BULL']['long_short']['metrics']['total_return']
    bull_degradation = bull_ls - bull_lo
    
    # Overall metrics
    lo_avg_return = aggregate_df[aggregate_df['Strategy'] == 'Long-Only']['Avg Return (%)'].values[0]
    ls_avg_return = aggregate_df[aggregate_df['Strategy'] == 'Long/Short']['Avg Return (%)'].values[0]
    
    lo_avg_sharpe = aggregate_df[aggregate_df['Strategy'] == 'Long-Only']['Avg Sharpe'].values[0]
    ls_avg_sharpe = aggregate_df[aggregate_df['Strategy'] == 'Long/Short']['Avg Sharpe'].values[0]
    
    print(f"\n2022 Bear Market:")
    print(f"  Long-Only: {bear_lo:.2f}%")
    print(f"  Long/Short: {bear_ls:.2f}%")
    print(f"  Improvement: {bear_improvement:+.2f}%")
    
    print(f"\n2024 Bull Market:")
    print(f"  Long-Only: {bull_lo:.2f}%")
    print(f"  Long/Short: {bull_ls:.2f}%")
    print(f"  Change: {bull_degradation:+.2f}%")
    
    print(f"\nOverall (2022-2025):")
    print(f"  Long-Only Avg Return: {lo_avg_return:.2f}%")
    print(f"  Long/Short Avg Return: {ls_avg_return:.2f}%")
    print(f"  Improvement: {ls_avg_return - lo_avg_return:+.2f}%")
    
    print(f"\n  Long-Only Avg Sharpe: {lo_avg_sharpe:.2f}")
    print(f"  Long/Short Avg Sharpe: {ls_avg_sharpe:.2f}")
    print(f"  Improvement: {ls_avg_sharpe - lo_avg_sharpe:+.2f}")
    
    # Success criteria
    success_criteria = {
        '2022 improved (>0%)': bear_ls > 0,
        '2022 Sharpe improved (>0.5)': all_results['2022_BEAR']['long_short']['metrics']['sharpe_ratio'] > 0.5,
        'Avg return improved (>8%)': ls_avg_return > 8,
        'Avg Sharpe improved (>1.2)': ls_avg_sharpe > 1.2,
        '2024 not destroyed (>10%)': bull_ls > 10
    }
    
    print(f"\nSuccess Criteria:")
    for criterion, passed in success_criteria.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {criterion}")
    
    passed_count = sum(success_criteria.values())
    total_count = len(success_criteria)
    
    if passed_count >= 4:
        print(f"\n✅ LONG/SHORT STRATEGY IS SUPERIOR ({passed_count}/{total_count} criteria)")
        print("La estrategia Long/Short mejora significativamente el performance.")
        verdict = "SUPERIOR"
    elif passed_count >= 3:
        print(f"\n⚠️  LONG/SHORT SHOWS PROMISE ({passed_count}/{total_count} criteria)")
        print("La estrategia Long/Short mejora algunos aspectos pero necesita ajustes.")
        verdict = "PROMISING"
    else:
        print(f"\n❌ LONG/SHORT NEEDS WORK ({passed_count}/{total_count} criteria)")
        print("La estrategia Long/Short no mejora suficientemente el performance.")
        verdict = "NEEDS_WORK"
    
    # Create comparison charts
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    periods = [p.replace('_', ' ') for p in all_results.keys()]
    
    # Return comparison
    lo_returns = [all_results[p]['long_only']['metrics']['total_return'] for p in all_results.keys()]
    ls_returns = [all_results[p]['long_short']['metrics']['total_return'] for p in all_results.keys()]
    
    x = np.arange(len(periods))
    width = 0.35
    
    axes[0, 0].bar(x - width/2, lo_returns, width, label='Long-Only', color='steelblue')
    axes[0, 0].bar(x + width/2, ls_returns, width, label='Long/Short', color='orange')
    axes[0, 0].axhline(y=0, color='red', linestyle='--', alpha=0.5)
    axes[0, 0].set_title('Return Comparison by Period', fontsize=14, fontweight='bold')
    axes[0, 0].set_ylabel('Return (%)')
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(periods, rotation=45)
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Sharpe comparison
    lo_sharpe = [all_results[p]['long_only']['metrics']['sharpe_ratio'] for p in all_results.keys()]
    ls_sharpe = [all_results[p]['long_short']['metrics']['sharpe_ratio'] for p in all_results.keys()]
    
    axes[0, 1].bar(x - width/2, lo_sharpe, width, label='Long-Only', color='steelblue')
    axes[0, 1].bar(x + width/2, ls_sharpe, width, label='Long/Short', color='orange')
    axes[0, 1].axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Target: 1.0')
    axes[0, 1].set_title('Sharpe Ratio Comparison', fontsize=14, fontweight='bold')
    axes[0, 1].set_ylabel('Sharpe Ratio')
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(periods, rotation=45)
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Max DD comparison
    lo_dd = [all_results[p]['long_only']['metrics']['max_drawdown'] for p in all_results.keys()]
    ls_dd = [all_results[p]['long_short']['metrics']['max_drawdown'] for p in all_results.keys()]
    
    axes[1, 0].bar(x - width/2, lo_dd, width, label='Long-Only', color='steelblue')
    axes[1, 0].bar(x + width/2, ls_dd, width, label='Long/Short', color='orange')
    axes[1, 0].axhline(y=10, color='red', linestyle='--', alpha=0.5, label='Warning: 10%')
    axes[1, 0].set_title('Max Drawdown Comparison', fontsize=14, fontweight='bold')
    axes[1, 0].set_ylabel('Max DD (%)')
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(periods, rotation=45)
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Improvement summary
    improvements = [ls_returns[i] - lo_returns[i] for i in range(len(periods))]
    colors = ['green' if imp > 0 else 'red' for imp in improvements]
    
    axes[1, 1].bar(periods, improvements, color=colors)
    axes[1, 1].axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    axes[1, 1].set_title('Return Improvement (Long/Short - Long-Only)', fontsize=14, fontweight='bold')
    axes[1, 1].set_ylabel('Improvement (%)')
    axes[1, 1].tick_params(axis='x', rotation=45)
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    chart_file = results_dir / 'long_short_comparison.png'
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    logger.info(f"Comparison chart saved to: {chart_file}")
    
    # Save verdict
    verdict_data = {
        'verdict': verdict,
        'bear_market_improvement': bear_improvement,
        'bull_market_change': bull_degradation,
        'avg_return_improvement': ls_avg_return - lo_avg_return,
        'avg_sharpe_improvement': ls_avg_sharpe - lo_avg_sharpe,
        'success_criteria': success_criteria,
        'passed_criteria': f"{passed_count}/{total_count}"
    }
    
    verdict_file = results_dir / 'verdict.json'
    with open(verdict_file, 'w') as f:
        json.dump(verdict_data, f, indent=2)
    
    print("\n" + "="*80)
    print("COMPARISON COMPLETE")
    print("="*80)
    print(f"\nResults directory: {results_dir}")
    print(f"  - Individual period results (JSON + CSV)")
    print(f"  - Comparison table (CSV)")
    print(f"  - Aggregate comparison (CSV)")
    print(f"  - Comparison chart (PNG)")
    print(f"  - Verdict (JSON)")


if __name__ == '__main__':
    main()
