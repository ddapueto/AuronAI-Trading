#!/usr/bin/env python3
"""
Quick test for SwingTPStrategy to verify it works correctly.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from auronai.backtesting import BacktestRunner, BacktestConfig
from auronai.strategies import SwingTPStrategy, StrategyParams


def main():
    print("=" * 80)
    print("🧪 Testing SwingTPStrategy")
    print("=" * 80)
    print()
    
    # Create strategy
    params = StrategyParams(
        top_k=3,
        holding_days=10,
        tp_multiplier=1.05,  # 5% TP
        risk_budget=0.20
    )
    
    strategy = SwingTPStrategy(params)
    
    print(f"Strategy: {strategy.name}")
    print(f"Description: {strategy.description}")
    print(f"Parameters: {strategy.get_params()}")
    print()
    
    # Create config
    config = BacktestConfig(
        strategy_id="swing_tp",
        strategy_params={'top_k': 3, 'holding_days': 10},
        symbols=['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA'],
        benchmark='SPY',
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        initial_capital=100000.0
    )
    
    print("Running backtest...")
    print(f"  Symbols: {config.symbols}")
    print(f"  Period: {config.start_date.date()} to {config.end_date.date()}")
    print(f"  Capital: ${config.initial_capital:,.0f}")
    print()
    
    # Run backtest
    runner = BacktestRunner()
    
    try:
        result = runner.run(config, strategy)
        
        print("=" * 80)
        print("📊 Results")
        print("=" * 80)
        print(f"Run ID: {result.run_id}")
        print(f"Total Return: {result.metrics.get('total_return', 0):.2f}%")
        print(f"Sharpe Ratio: {result.metrics.get('sharpe_ratio', 0):.2f}")
        print(f"Max Drawdown: {result.metrics.get('max_drawdown', 0):.2f}%")
        print(f"Number of Trades: {result.metrics.get('num_trades', 0)}")
        print(f"Win Rate: {result.metrics.get('win_rate', 0):.2f}%")
        print()
        
        print("✅ SwingTPStrategy test passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
