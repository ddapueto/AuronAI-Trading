"""Test SwingTPStrategy with daily exit checking."""

from datetime import datetime
from auronai.backtesting.backtest_config import BacktestConfig
from auronai.backtesting.backtest_runner import BacktestRunner
from auronai.strategies.swing_tp import SwingTPStrategy, StrategyParams

# Config matching original script
config = BacktestConfig(
    strategy_id='swing_tp_test',
    symbols=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'COST', 'NFLX'],
    benchmark='QQQ',
    start_date=datetime(2025, 7, 1),
    end_date=datetime(2026, 1, 31),
    initial_capital=100000.0,
    strategy_params={
        'top_k': 3,
        'holding_days': 7,
        'tp_multiplier': 1.05,
        'risk_budget': 0.20,
        'defensive_risk_budget': 0.05
    }
)

# Create strategy
params = StrategyParams(
    top_k=3,
    holding_days=7,
    tp_multiplier=1.05,
    risk_budget=0.20,
    defensive_risk_budget=0.05
)
strategy = SwingTPStrategy(params)

# Run backtest
runner = BacktestRunner()
result = runner.run(config, strategy)

# Print results
print(f'\n=== BACKTEST RESULTS ===')
print(f'Total Return: {result.metrics.get("total_return", 0):.2f}%')
print(f'Sharpe Ratio: {result.metrics.get("sharpe_ratio", 0):.2f}')
print(f'Max Drawdown: {result.metrics.get("max_drawdown", 0):.2f}%')
print(f'Trades: {len(result.trades)}')
print(f'\nExpected (original script): 5.58% return, 113 trades')
print(f'Previous UI result: 2.94% return, 81 trades')
