#!/usr/bin/env python3
"""
Test Different Rebalance Frequencies for Single Momentum Strategy

Compares: Weekly, Bi-weekly, Monthly, Bi-monthly, Quarterly
Period: 2021-2025 (4 years)
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
import json
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


def run_frequency_test(
    frequency_name: str,
    rebalance_freq: str,
    symbols: list,
    start_date: datetime,
    end_date: datetime
) -> dict:
    """Run backtest with specific rebalance frequency."""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing {frequency_name} Rebalance")
    logger.info(f"{'='*80}")
    
    # Create strategy with rebalance frequency
    params = DualMomentumParams(
        lookback_period=252,
        top_n=1,  # Single momentum
        rebalance_frequency=rebalance_freq
    )
    
    strategy = DualMomentumStrategy(params)
    backtest_runner = BacktestRunner()
    
    # Run backtest
    config = BacktestConfig(
        strategy_id=f"single_momentum_{frequency_name}",
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_capital=1000.0,  # User's actual capital
        commission_rate=0.0,  # We'll calculate separately
        slippage_rate=0.0005,
        benchmark='SPY',
        strategy_params=params.__dict__
    )
    
    try:
        result = backtest_runner.run(config, strategy)
        
        # Calculate commission costs
        num_trades = result.metrics.get('num_trades', 0)
        commission_per_trade = 1.0  # $1 per trade (realistic for modern brokers)
        total_commissions = num_trades * commission_per_trade
        commission_impact = total_commissions / 1000.0  # As percentage of initial capital
        
        # Adjust return for commissions
        gross_return = result.metrics['total_return']
        net_return = gross_return - commission_impact
        
        # Annualize
        years = (end_date - start_date).days / 365.25
        annualized_return = (1 + net_return) ** (1 / years) - 1
        
        # Calculate final equity
        final_equity = 1000.0 * (1 + net_return)
        
        return {
            'frequency_name': frequency_name,
            'rebalance_freq': rebalance_freq,
            'num_trades': int(num_trades),
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
            'rebalance_freq': rebalance_freq,
            'error': str(e),
            'success': False
        }


def main():
    """Test all rebalance frequencies."""
    
    logger.info("="*80)
    logger.info("REBALANCE FREQUENCY COMPARISON TEST")
    logger.info("Testing: Weekly vs Monthly (Single Momentum)")
    logger.info("Initial Capital: $1,000 (User's actual capital)")
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
    
    # Define frequencies to test (only what DualMomentumStrategy supports)
    frequencies = [
        ('Weekly', 'weekly'),
        ('Monthly', 'monthly')
    ]
    
    # Run tests
    logger.info("\n🚀 Step 3: Run Frequency Tests")
    results = []
    
    for name, freq in frequencies:
        result = run_frequency_test(
            frequency_name=name,
            rebalance_freq=freq,
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
    logger.info(f"{'Frequency':<15} {'Trades':<8} {'Commissions':<12} {'Net Return':<12} {'Annual':<10} {'Sharpe':<8} {'Max DD':<10} {'Final $':<10}")
    logger.info("-" * 100)
    
    for r in results:
        if r['success']:
            logger.info(
                f"{r['frequency_name']:<15} "
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
        
        # Calculate difference
        if len(successful_results) == 2:
            weekly = next(r for r in successful_results if r['frequency_name'] == 'Weekly')
            monthly = next(r for r in successful_results if r['frequency_name'] == 'Monthly')
            
            return_diff = weekly['annualized_return'] - monthly['annualized_return']
            cost_diff = weekly['total_commissions'] - monthly['total_commissions']
            equity_diff = weekly['final_equity'] - monthly['final_equity']
            
            logger.info("\n" + "="*80)
            logger.info("WEEKLY vs MONTHLY DIFFERENCE")
            logger.info("="*80)
            logger.info(f"\n📊 Return Difference: {return_diff:+.2%} annual")
            logger.info(f"💵 Cost Difference: ${cost_diff:+.0f}")
            logger.info(f"💰 Final Equity Difference: ${equity_diff:+.0f}")
            logger.info(f"📈 Trades Difference: {weekly['num_trades'] - monthly['num_trades']:+d}")
            
            if return_diff > 0:
                logger.info(f"\n✅ Weekly rebalancing OUTPERFORMS by {return_diff:.2%} annually")
                logger.info(f"   But costs ${cost_diff:.0f} more in commissions")
                if equity_diff > cost_diff:
                    logger.info(f"   Net benefit: ${equity_diff - cost_diff:.0f} (worth it!)")
                else:
                    logger.info(f"   Net benefit: ${equity_diff:.0f} (marginal)")
            else:
                logger.info(f"\n✅ Monthly rebalancing OUTPERFORMS by {-return_diff:.2%} annually")
                logger.info(f"   And saves ${-cost_diff:.0f} in commissions")
        
        # Recommendation
        logger.info("\n" + "="*80)
        logger.info("RECOMMENDATION FOR $1,000 ACCOUNT")
        logger.info("="*80)
        
        # Calculate cost-adjusted score
        for r in successful_results:
            # Score = Return - (Commission Impact * 2)
            r['score'] = r['annualized_return'] - (r['commission_impact'] * 2)
        
        best_overall = max(successful_results, key=lambda x: x['score'])
        
        logger.info(f"\n✅ OPTIMAL FREQUENCY: {best_overall['frequency_name']}")
        logger.info(f"   Annual Return: {best_overall['annualized_return']:.1%}")
        logger.info(f"   Sharpe Ratio: {best_overall['sharpe_ratio']:.2f}")
        logger.info(f"   Total Commissions: ${best_overall['total_commissions']:.0f}")
        logger.info(f"   Number of Trades: {best_overall['num_trades']}")
        logger.info(f"   Final Equity: ${best_overall['final_equity']:.0f}")
        
        logger.info("\n💡 Why this is optimal:")
        logger.info(f"   - Balances return vs transaction costs")
        logger.info(f"   - {best_overall['num_trades']} trades over 4 years")
        logger.info(f"   - Commission impact: {best_overall['commission_impact']:.2%} of capital")
        logger.info(f"   - Turns $1,000 into ${best_overall['final_equity']:.0f}")
    
    # Save results
    logger.info("\n💾 Step 4: Save Results")
    results_dir = Path(__file__).parent.parent / 'results'
    output_file = results_dir / 'rebalance_frequency_comparison.json'
    
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
            'rebalance_freq': best_overall['rebalance_freq'],
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
    
    logger.info("\n" + "="*80)
    logger.info("TEST COMPLETE")
    logger.info("="*80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
