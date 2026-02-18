#!/usr/bin/env python3
"""
Test ALL Rebalance Frequencies for Single Momentum Strategy

Compares: Weekly, Bi-weekly (14d), Tri-weekly (21d), Monthly, Bi-monthly (60d)
Period: 2021-2025 (4 years)
Shows ALL trades with open/close dates
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
import json
import pandas as pd
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


class CustomFrequencyDualMomentum(DualMomentumStrategy):
    """Extended Dual Momentum with custom rebalance frequencies."""
    
    def __init__(self, params: DualMomentumParams, rebalance_days: int):
        """
        Initialize with custom rebalance frequency.
        
        Args:
            params: Strategy parameters
            rebalance_days: Days between rebalances (7, 14, 21, 30, 60, etc.)
        """
        super().__init__(params)
        self.rebalance_days = rebalance_days
        logger.info(f"Custom rebalance frequency: every {rebalance_days} days")
    
    def _should_rebalance(self, current_date: datetime) -> bool:
        """Check if rebalancing is needed based on custom frequency."""
        if isinstance(current_date, str):
            current_date = pd.to_datetime(current_date)
        
        if self.last_rebalance is None:
            return True
        
        days_diff = (current_date - self.last_rebalance).days
        return days_diff >= self.rebalance_days


def run_frequency_test(
    frequency_name: str,
    rebalance_days: int,
    symbols: list,
    start_date: datetime,
    end_date: datetime
) -> dict:
    """Run backtest with specific rebalance frequency and extract all trades."""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing {frequency_name} Rebalance (every {rebalance_days} days)")
    logger.info(f"{'='*80}")
    
    # Create strategy with custom rebalance frequency
    params = DualMomentumParams(
        lookback_period=252,
        top_n=1,  # Single momentum
        rebalance_frequency='monthly'  # Dummy value, we override _should_rebalance
    )
    
    strategy = CustomFrequencyDualMomentum(params, rebalance_days)
    backtest_runner = BacktestRunner()
    
    # Run backtest
    config = BacktestConfig(
        strategy_id=f"single_momentum_{frequency_name}",
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_capital=1000.0,
        commission_rate=0.0,
        slippage_rate=0.0005,
        benchmark='SPY',
        strategy_params=params.__dict__
    )
    
    try:
        result = backtest_runner.run(config, strategy)
        
        # Extract trades from result
        trades_list = []
        if hasattr(result, 'trades') and result.trades is not None:
            for trade in result.trades:
                # Handle both dict and object formats
                if isinstance(trade, dict):
                    entry_date = trade.get('entry_date')
                    exit_date = trade.get('exit_date')
                    
                    # Calculate days held
                    days_held = None
                    if entry_date and exit_date:
                        if isinstance(entry_date, str):
                            entry_date = pd.to_datetime(entry_date)
                        if isinstance(exit_date, str):
                            exit_date = pd.to_datetime(exit_date)
                        days_held = (exit_date - entry_date).days
                    
                    trades_list.append({
                        'symbol': trade.get('symbol'),
                        'entry_date': entry_date.strftime('%Y-%m-%d') if hasattr(entry_date, 'strftime') else str(entry_date),
                        'exit_date': exit_date.strftime('%Y-%m-%d') if exit_date and hasattr(exit_date, 'strftime') else str(exit_date) if exit_date else 'OPEN',
                        'entry_price': float(trade.get('entry_price', 0)),
                        'exit_price': float(trade.get('exit_price')) if trade.get('exit_price') else None,
                        'shares': float(trade.get('shares', 0)),
                        'pnl': float(trade.get('pnl', 0)),
                        'return_pct': float(trade.get('return_pct', 0)),
                        'days_held': days_held
                    })
                else:
                    # Object format
                    days_held = (trade.exit_date - trade.entry_date).days if trade.exit_date else None
                    trades_list.append({
                        'symbol': trade.symbol,
                        'entry_date': trade.entry_date.strftime('%Y-%m-%d') if hasattr(trade.entry_date, 'strftime') else str(trade.entry_date),
                        'exit_date': trade.exit_date.strftime('%Y-%m-%d') if trade.exit_date and hasattr(trade.exit_date, 'strftime') else str(trade.exit_date) if trade.exit_date else 'OPEN',
                        'entry_price': float(trade.entry_price),
                        'exit_price': float(trade.exit_price) if trade.exit_price else None,
                        'shares': float(trade.shares),
                        'pnl': float(trade.pnl) if trade.pnl else 0.0,
                        'return_pct': float(trade.return_pct) if trade.return_pct else 0.0,
                        'days_held': days_held
                    })
        
        # Calculate commission costs
        num_trades = result.metrics.get('num_trades', 0)
        commission_per_trade = 1.0
        total_commissions = num_trades * commission_per_trade
        commission_impact = total_commissions / 1000.0
        
        # Adjust return for commissions
        gross_return = result.metrics['total_return']
        net_return = gross_return - commission_impact
        
        # Annualize
        years = (end_date - start_date).days / 365.25
        annualized_return = (1 + net_return) ** (1 / years) - 1
        
        # Calculate final equity
        final_equity = 1000.0 * (1 + net_return)
        
        # Log trades summary
        logger.info(f"\n📊 Trades Summary for {frequency_name}:")
        logger.info(f"Total trades: {len(trades_list)}")
        if trades_list:
            logger.info(f"\nFirst 5 trades:")
            for i, trade in enumerate(trades_list[:5], 1):
                logger.info(
                    f"  {i}. {trade['symbol']}: "
                    f"{trade['entry_date']} → {trade['exit_date']} "
                    f"({trade['days_held']} days) "
                    f"Return: {trade['return_pct']:.2%}"
                )
        
        return {
            'frequency_name': frequency_name,
            'rebalance_days': int(rebalance_days),
            'num_trades': int(num_trades),
            'trades': trades_list,
            'gross_return': float(gross_return),
            'total_commissions': float(total_commissions),
            'commission_impact': float(commission_impact),
            'net_return': float(net_return),
            'annualized_return': float(annualized_return),
            'sharpe_ratio': float(result.metrics['sharpe_ratio']),
            'max_drawdown': float(result.metrics['max_drawdown']),
            'win_rate': float(result.metrics.get('win_rate', 0)),
            'avg_trade': float(result.metrics.get('avg_trade_return', 0)),
            'final_equity': float(final_equity),
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error testing {frequency_name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'frequency_name': frequency_name,
            'rebalance_days': int(rebalance_days),
            'error': str(e),
            'success': False
        }


def main():
    """Test all rebalance frequencies."""
    
    logger.info("="*80)
    logger.info("COMPREHENSIVE REBALANCE FREQUENCY TEST")
    logger.info("Testing: 7d, 14d, 21d, 30d, 60d (Single Momentum)")
    logger.info("Initial Capital: $1,000")
    logger.info("="*80)
    
    # Initialize
    logger.info("\n📊 Step 1: Initialize")
    market_data_provider = MarketDataProvider(cache_ttl_seconds=3600, max_retries=3)
    symbol_manager = SymbolUniverseManager(market_data_provider)
    
    # Validate symbols
    logger.info("\n✅ Step 2: Validate Symbol Universe")
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2025, 2, 1)
    
    validation_result = symbol_manager.validate_universe(
        start_date=start_date,
        end_date=end_date,
        min_data_points=756
    )
    
    logger.info(f"Valid symbols: {len(validation_result.valid)}")
    symbols = validation_result.valid
    
    # Define frequencies to test
    frequencies = [
        ('Weekly (7d)', 7),
        ('Bi-weekly (14d)', 14),
        ('Tri-weekly (21d)', 21),
        ('Monthly (30d)', 30),
        ('Bi-monthly (60d)', 60)
    ]
    
    # Run tests
    logger.info("\n🚀 Step 3: Run Frequency Tests")
    results = []
    
    for name, days in frequencies:
        result = run_frequency_test(
            frequency_name=name,
            rebalance_days=days,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        results.append(result)
    
    # Display results
    logger.info("\n" + "="*80)
    logger.info("RESULTS COMPARISON")
    logger.info("="*80)
    
    # Create comparison table
    logger.info("\n📊 Performance by Frequency:\n")
    logger.info(f"{'Frequency':<20} {'Trades':<8} {'Commissions':<12} {'Net Return':<12} {'Annual':<10} {'Sharpe':<8} {'Max DD':<10} {'Final $':<10}")
    logger.info("-" * 110)
    
    for r in results:
        if r['success']:
            logger.info(
                f"{r['frequency_name']:<20} "
                f"{r['num_trades']:<8} "
                f"${r['total_commissions']:<11.0f} "
                f"{r['net_return']:<11.1%} "
                f"{r['annualized_return']:<9.1%} "
                f"{r['sharpe_ratio']:<7.2f} "
                f"{r['max_drawdown']:<9.1%} "
                f"${r['final_equity']:<9.0f}"
            )
    
    # Find optimal
    successful_results = [r for r in results if r['success']]
    if successful_results:
        best_return = max(successful_results, key=lambda x: x['annualized_return'])
        best_sharpe = max(successful_results, key=lambda x: x['sharpe_ratio'])
        lowest_cost = min(successful_results, key=lambda x: x['total_commissions'])
        
        logger.info("\n" + "="*80)
        logger.info("COMPARISON ANALYSIS")
        logger.info("="*80)
        logger.info(f"\n🏆 Best Return: {best_return['frequency_name']} ({best_return['annualized_return']:.1%} annual)")
        logger.info(f"📈 Best Sharpe: {best_sharpe['frequency_name']} ({best_sharpe['sharpe_ratio']:.2f})")
        logger.info(f"💰 Lowest Cost: {lowest_cost['frequency_name']} (${lowest_cost['total_commissions']:.0f})")
        
        # Calculate cost-adjusted score
        for r in successful_results:
            r['score'] = r['annualized_return'] - (r['commission_impact'] * 2)
        
        best_overall = max(successful_results, key=lambda x: x['score'])
        
        logger.info("\n" + "="*80)
        logger.info("RECOMMENDATION FOR $1,000 ACCOUNT")
        logger.info("="*80)
        logger.info(f"\n✅ OPTIMAL FREQUENCY: {best_overall['frequency_name']}")
        logger.info(f"   Annual Return: {best_overall['annualized_return']:.1%}")
        logger.info(f"   Sharpe Ratio: {best_overall['sharpe_ratio']:.2f}")
        logger.info(f"   Total Commissions: ${best_overall['total_commissions']:.0f}")
        logger.info(f"   Number of Trades: {best_overall['num_trades']}")
        logger.info(f"   Final Equity: ${best_overall['final_equity']:.0f}")
    
    # Save results with trades
    logger.info("\n💾 Step 4: Save Results")
    results_dir = Path(__file__).parent.parent / 'results'
    output_file = results_dir / 'all_rebalance_frequencies.json'
    
    output_data = {
        'test_date': datetime.now().isoformat(),
        'initial_capital': 1000.0,
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
            'years': round((end_date - start_date).days / 365.25, 2)
        },
        'results': results,
        'recommendation': {
            'frequency': best_overall['frequency_name'],
            'rebalance_days': best_overall['rebalance_days'],
            'annualized_return': best_overall['annualized_return'],
            'sharpe_ratio': best_overall['sharpe_ratio'],
            'total_commissions': best_overall['total_commissions'],
            'final_equity': best_overall['final_equity'],
            'num_trades': best_overall['num_trades']
        } if successful_results else None
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Results saved to: {output_file}")
    
    # Also save trades to CSV for easy viewing
    for r in successful_results:
        if r['trades']:
            trades_df = pd.DataFrame(r['trades'])
            csv_file = results_dir / f"trades_{r['frequency_name'].replace(' ', '_').replace('(', '').replace(')', '')}.csv"
            trades_df.to_csv(csv_file, index=False)
            logger.info(f"Trades saved to: {csv_file}")
    
    logger.info("\n" + "="*80)
    logger.info("TEST COMPLETE")
    logger.info("="*80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
