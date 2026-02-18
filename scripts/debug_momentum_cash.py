#!/usr/bin/env python3
"""
Debug script to understand cash flow in momentum strategy.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from auronai.data.market_data_provider import MarketDataProvider
from auronai.data.symbol_universe import SymbolUniverseManager
from auronai.strategies.dual_momentum import DualMomentumStrategy, DualMomentumParams
from auronai.backtesting.backtest_config import BacktestConfig
from auronai.backtesting.backtest_runner import BacktestRunner
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Debug momentum strategy cash flow."""
    
    print("\n" + "="*80)
    print("DEBUGGING MOMENTUM STRATEGY CASH FLOW")
    print("="*80)
    
    # Initialize
    market_data_provider = MarketDataProvider(cache_ttl_seconds=3600, max_retries=3)
    symbol_manager = SymbolUniverseManager(market_data_provider)
    
    # Validate symbols
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2021, 6, 1)  # Solo 5 meses para debug
    
    validation_result = symbol_manager.validate_universe(
        start_date=start_date,
        end_date=end_date,
        min_data_points=100
    )
    
    symbols = validation_result.valid[:10]  # Solo 10 símbolos para debug
    print(f"\nUsing {len(symbols)} symbols: {symbols}")
    
    # Test with different risk budgets
    for risk_budget in [0.20, 1.0]:
        print(f"\n{'='*80}")
        print(f"TESTING WITH RISK BUDGET: {risk_budget*100}%")
        print(f"{'='*80}")
        
        params = DualMomentumParams(
            lookback_period=252,
            top_n=1,
            rebalance_frequency='weekly',
            risk_budget=risk_budget
        )
        
        strategy = DualMomentumStrategy(params)
        backtest_runner = BacktestRunner()
        
        config = BacktestConfig(
            strategy_id=f"debug_rb_{int(risk_budget*100)}",
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capital=1000.0,
            commission_rate=0.0,
            slippage_rate=0.0005,
            benchmark='SPY',
            strategy_params=params.__dict__
        )
        
        result = backtest_runner.run(config, strategy)
        
        print(f"\nRESULTS:")
        print(f"  Trades: {result.metrics.get('num_trades', 0)}")
        print(f"  Final Equity: ${result.metrics.get('final_equity', 0):.2f}")
        print(f"  Total Return: {result.metrics.get('total_return', 0):.2%}")
        
        # Show trades
        if hasattr(result, 'trades') and result.trades is not None:
            print(f"\n  Trades executed:")
            for i, trade in enumerate(result.trades, 1):
                if isinstance(trade, dict):
                    print(f"    {i}. {trade.get('symbol')}: Entry ${trade.get('entry_price', 0):.2f}, Shares: {trade.get('shares', 0):.4f}")
                    print(f"       Date: {trade.get('entry_date')}")
        
        # Show equity curve
        if hasattr(result, 'equity_curve') and result.equity_curve is not None:
            import pandas as pd
            if isinstance(result.equity_curve, pd.DataFrame):
                print(f"\n  First 10 equity points:")
                for i in range(min(10, len(result.equity_curve))):
                    row = result.equity_curve.iloc[i]
                    print(f"    {i+1}. Date: {row.get('date')}, Equity: ${row.get('equity', 0):.2f}, Cash: ${row.get('cash', 0):.2f}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
