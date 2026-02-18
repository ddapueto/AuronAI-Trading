"""Compare SwingTPStrategy results with original script."""

from datetime import datetime
from auronai.backtesting.backtest_config import BacktestConfig
from auronai.backtesting.backtest_runner import BacktestRunner
from auronai.strategies.swing_tp import SwingTPStrategy, StrategyParams

# Config matching original script
config = BacktestConfig(
    strategy_id='swing_tp_comparison',
    symbols=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'COST', 'NFLX'],
    benchmark='QQQ',
    start_date=datetime(2025, 7, 1),
    end_date=datetime(2026, 1, 31),
    initial_capital=1000.0,  # Same as original
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

# Print comparison
print(f'\n=== COMPARISON ===')
print(f'\nOriginal Script (swing_no_sl_10symbols_7days):')
print(f'  Return: 5.58%')
print(f'  Trades: 113')
print(f'  Sharpe: 0.92')
print(f'  Max DD: -3.24%')

print(f'\nCurrent Implementation (SwingTPStrategy):')
print(f'  Return: {result.metrics.get("total_return", 0)*100:.2f}%')
print(f'  Trades: {len(result.trades)}')
print(f'  Sharpe: {result.metrics.get("sharpe_ratio", 0):.2f}')
print(f'  Max DD: {result.metrics.get("max_drawdown", 0):.2f}%')

print(f'\nDifference:')
print(f'  Return: {result.metrics.get("total_return", 0)*100 - 5.58:.2f}%')
print(f'  Trades: {len(result.trades) - 113}')

# Analyze trades
if result.trades:
    closed_trades = [t for t in result.trades if t['exit_date'] is not None]
    print(f'\nTrade Analysis:')
    print(f'  Total trades: {len(result.trades)}')
    print(f'  Closed trades: {len(closed_trades)}')
    print(f'  Open trades: {len(result.trades) - len(closed_trades)}')
    
    if closed_trades:
        winners = [t for t in closed_trades if t.get('pnl_dollar', 0) > 0]
        print(f'  Winners: {len(winners)} ({len(winners)/len(closed_trades)*100:.1f}%)')
