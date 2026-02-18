#!/usr/bin/env python3
"""
Test Momentum Strategy with Libertex (Fractional Shares + 100% Capital)

Libertex allows:
- Fractional shares (0.01, 0.5, etc.)
- Using 100% of capital per position
- Rotating positions completely
"""

import sys
from datetime import datetime
from pathlib import Path
import json
import pandas as pd
import numpy as np

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


def run_momentum_test(
    frequency_name: str,
    rebalance_days: int,
    risk_budget: float,
    symbols: list,
    start_date: datetime,
    end_date: datetime
) -> dict:
    """Run momentum backtest with specified risk budget (Libertex style)."""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing {frequency_name} with {risk_budget*100:.0f}% Capital (Libertex)")
    logger.info(f"{'='*80}")
    
    # Create strategy with specified risk budget
    params = DualMomentumParams(
        lookback_period=252,
        top_n=1,
        rebalance_frequency='weekly',  # Dummy, we override
        risk_budget=risk_budget
    )
    
    # Use custom frequency class
    strategy = CustomFrequencyDualMomentum(params, rebalance_days)
    backtest_runner = BacktestRunner()
    
    config = BacktestConfig(
        strategy_id=f"libertex_{frequency_name}_{int(risk_budget*100)}pct",
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_capital=1000.0,
        commission_rate=0.001,  # 0.1% commission
        slippage_rate=0.0005,
        benchmark='SPY',
        strategy_params=params.__dict__
    )
    
    try:
        result = backtest_runner.run(config, strategy)
        
        # Extract trades
        trades_list = []
        if hasattr(result, 'trades') and result.trades is not None:
            for trade in result.trades:
                if isinstance(trade, dict):
                    entry_date = trade.get('entry_date')
                    exit_date = trade.get('exit_date')
                    
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
                        'exit_date': exit_date.strftime('%Y-%m-%d') if exit_date and hasattr(exit_date, 'strftime') else 'OPEN',
                        'entry_price': float(trade.get('entry_price', 0)),
                        'exit_price': float(trade.get('exit_price')) if trade.get('exit_price') else None,
                        'shares': float(trade.get('shares', 0)),
                        'pnl': float(trade.get('pnl', 0)),
                        'return_pct': float(trade.get('return_pct', 0)),
                        'days_held': days_held
                    })
        
        # Calculate metrics
        num_trades = result.metrics.get('num_trades', 0)
        commission_per_trade = 1.0
        total_commissions = num_trades * commission_per_trade
        commission_impact = total_commissions / 1000.0
        
        gross_return = result.metrics['total_return']
        net_return = gross_return - commission_impact
        
        years = (end_date - start_date).days / 365.25
        annualized_return = (1 + net_return) ** (1 / years) - 1
        
        final_equity = 1000.0 * (1 + net_return)
        
        logger.info(f"\n📊 Results for {frequency_name}:")
        logger.info(f"  Trades: {num_trades}")
        logger.info(f"  Annual Return: {annualized_return:.2%}")
        logger.info(f"  Final Equity: ${final_equity:.2f}")
        logger.info(f"  Sharpe: {result.metrics['sharpe_ratio']:.2f}")
        
        return {
            'frequency_name': frequency_name,
            'rebalance_days': int(rebalance_days),
            'risk_budget': float(risk_budget),
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
    """Test momentum with Libertex - Multiple risk levels."""
    
    logger.info("="*80)
    logger.info("MOMENTUM STRATEGY - LIBERTEX SIMULATION")
    logger.info("Testing: 50%, 70%, 90% Capital Allocation")
    logger.info("="*80)
    
    # Initialize
    market_data_provider = MarketDataProvider(cache_ttl_seconds=3600, max_retries=3)
    symbol_manager = SymbolUniverseManager(market_data_provider)
    
    # Validate symbols
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2025, 2, 1)
    
    validation_result = symbol_manager.validate_universe(
        start_date=start_date,
        end_date=end_date,
        min_data_points=756
    )
    
    logger.info(f"\nValid symbols: {len(validation_result.valid)}")
    symbols = validation_result.valid
    
    # Test combinations: frequency + risk budget (simplified)
    test_configs = [
        # Weekly with different risk levels
        ('Weekly-50%', 7, 0.50),
        ('Weekly-70%', 7, 0.70),
        ('Weekly-90%', 7, 0.90),
    ]
    
    results = []
    
    for name, days, risk_budget in test_configs:
        result = run_momentum_test(
            frequency_name=name,
            rebalance_days=days,
            risk_budget=risk_budget,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        results.append(result)
    
    # Display comparison
    logger.info("\n" + "="*80)
    logger.info("RESULTS COMPARISON - LIBERTEX (FRACTIONAL SHARES)")
    logger.info("="*80)
    
    logger.info("\n📊 Performance by Configuration:\n")
    logger.info(f"{'Config':<18} {'Risk%':<8} {'Trades':<8} {'Annual':<10} {'Sharpe':<8} {'Max DD':<10} {'Final $':<10}")
    logger.info("-" * 90)
    
    for r in results:
        if r['success']:
            logger.info(
                f"{r['frequency_name']:<18} "
                f"{r['risk_budget']*100:<7.0f}% "
                f"{r['num_trades']:<8} "
                f"{r['annualized_return']:<9.1%} "
                f"{r['sharpe_ratio']:<7.2f} "
                f"{r['max_drawdown']:<9.1%} "
                f"${r['final_equity']:<9.0f}"
            )
    
    # Find best by different criteria
    successful_results = [r for r in results if r['success']]
    if successful_results:
        best_return = max(successful_results, key=lambda x: x['annualized_return'])
        best_sharpe = max(successful_results, key=lambda x: x['sharpe_ratio'])
        lowest_dd = max(successful_results, key=lambda x: -x['max_drawdown'])
        
        logger.info("\n" + "="*80)
        logger.info("ANALYSIS")
        logger.info("="*80)
        logger.info(f"\n🏆 Best Return: {best_return['frequency_name']} ({best_return['annualized_return']:.1%})")
        logger.info(f"📈 Best Sharpe: {best_sharpe['frequency_name']} ({best_sharpe['sharpe_ratio']:.2f})")
        logger.info(f"🛡️  Lowest Drawdown: {lowest_dd['frequency_name']} ({lowest_dd['max_drawdown']:.1%})")
        
        # Recommendation
        logger.info("\n" + "="*80)
        logger.info("💡 RECOMMENDATION FOR $1,000")
        logger.info("="*80)
        logger.info("\n✅ CONSERVATIVE (Recommended): 50-70% capital")
        logger.info("   - Keeps $300-500 in cash as buffer")
        logger.info("   - Can handle market volatility")
        logger.info("   - Lower stress")
        
        logger.info("\n⚠️  AGGRESSIVE: 90% capital")
        logger.info("   - Only $100 cash buffer")
        logger.info("   - Higher returns but higher risk")
        logger.info("   - Need strong stomach for drawdowns")
    
    # Save results
    results_dir = Path(__file__).parent.parent / 'results'
    output_file = results_dir / 'momentum_libertex_risk_levels.json'
    
    output_data = {
        'test_date': datetime.now().isoformat(),
        'broker': 'Libertex',
        'features': ['fractional_shares', 'multiple_risk_levels'],
        'initial_capital': 1000.0,
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
            'years': round((end_date - start_date).days / 365.25, 2)
        },
        'results': results,
        'best_return': {
            'config': best_return['frequency_name'],
            'risk_budget': best_return['risk_budget'],
            'annualized_return': best_return['annualized_return'],
            'sharpe_ratio': best_return['sharpe_ratio'],
            'num_trades': best_return['num_trades'],
            'final_equity': best_return['final_equity']
        } if successful_results else None,
        'best_sharpe': {
            'config': best_sharpe['frequency_name'],
            'risk_budget': best_sharpe['risk_budget'],
            'annualized_return': best_sharpe['annualized_return'],
            'sharpe_ratio': best_sharpe['sharpe_ratio'],
            'num_trades': best_sharpe['num_trades'],
            'final_equity': best_sharpe['final_equity']
        } if successful_results else None
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"\n💾 Results saved to: {output_file}")
    
    logger.info("\n" + "="*80)
    logger.info("TEST COMPLETE")
    logger.info("="*80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
