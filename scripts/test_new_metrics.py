"""
Test script for new metrics.

This script runs a backtest and displays all metrics including the new ones:
- Sortino Ratio
- Recovery Factor
- Average Drawdown Duration
- Max Drawdown Duration
- Ulcer Index
- Max Consecutive Wins/Losses
"""

from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auronai.backtesting import BacktestConfig, BacktestRunner
from auronai.strategies import SwingTPStrategy, StrategyParams


def main():
    """Run backtest and display new metrics."""
    
    print("=" * 80)
    print("Testing New Metrics")
    print("=" * 80)
    print()
    
    # Configuration
    config = BacktestConfig(
        strategy_id="swing_tp",
        strategy_params={
            'top_k': 3,
            'holding_days': 10,
            'tp_multiplier': 1.05,
            'risk_budget': 0.20,
            'defensive_risk_budget': 0.05
        },
        symbols=[
            "AAPL", "MSFT", "GOOGL", "NVDA", "TSLA",
            "META", "AMZN", "NFLX", "AMD", "INTC"
        ],
        benchmark="QQQ",
        start_date=datetime(2024, 7, 1),
        end_date=datetime(2025, 2, 1),
        initial_capital=1000.0,
        commission_rate=0.0000,  # Libertex no cobra comisión directa
        slippage_rate=0.0010     # 0.10% (spread + slippage + swap)
    )
    
    # Create strategy
    params = StrategyParams(
        top_k=config.strategy_params['top_k'],
        holding_days=config.strategy_params['holding_days'],
        tp_multiplier=config.strategy_params['tp_multiplier'],
        risk_budget=config.strategy_params['risk_budget'],
        defensive_risk_budget=config.strategy_params['defensive_risk_budget']
    )
    
    strategy = SwingTPStrategy(params)
    
    # Run backtest
    print("Running backtest...")
    print(f"Period: {config.start_date.date()} to {config.end_date.date()}")
    print(f"Symbols: {len(config.symbols)}")
    print(f"Initial Capital: ${config.initial_capital:,.2f}")
    print(f"Costs: Commission {config.commission_rate:.2%}, Slippage {config.slippage_rate:.2%}")
    print()
    
    runner = BacktestRunner()
    result = runner.run(config, strategy)
    
    # Display results
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    
    metrics = result.metrics
    
    # Return Metrics
    print("📈 RETURN METRICS")
    print("-" * 80)
    print(f"Total Return:        {metrics['total_return']:.2%}")
    print(f"CAGR:                {metrics['cagr']:.2%}")
    print(f"Final Equity:        ${metrics['final_equity']:,.2f}")
    print()
    
    # Risk Metrics
    print("⚠️  RISK METRICS")
    print("-" * 80)
    print(f"Max Drawdown:        {metrics['max_drawdown']:.2%}")
    print(f"Volatility:          {metrics['volatility']:.2%}")
    print(f"Avg DD Duration:     {metrics.get('avg_dd_duration', 0):.1f} days")
    print(f"Max DD Duration:     {metrics.get('max_dd_duration', 0):.1f} days")
    print(f"Ulcer Index:         {metrics.get('ulcer_index', 0):.2f}")
    print()
    
    # Risk-Adjusted Metrics
    print("🎯 RISK-ADJUSTED METRICS")
    print("-" * 80)
    print(f"Sharpe Ratio:        {metrics['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio:       {metrics.get('sortino_ratio', 0):.2f} ⭐ NEW")
    print(f"Calmar Ratio:        {metrics['calmar_ratio']:.2f}")
    print(f"Recovery Factor:     {metrics.get('recovery_factor', 0):.2f} ⭐ NEW")
    print()
    
    # Trading Metrics
    print("💼 TRADING METRICS")
    print("-" * 80)
    print(f"Number of Trades:    {metrics['num_trades']}")
    print(f"Win Rate:            {metrics['win_rate']:.2%}")
    print(f"Profit Factor:       {metrics['profit_factor']:.2f}")
    print(f"Expectancy:          ${metrics['expectancy']:.2f}")
    print(f"Avg Win:             ${metrics['avg_win']:.2f}")
    print(f"Avg Loss:            ${metrics['avg_loss']:.2f}")
    print(f"Largest Win:         ${metrics['largest_win']:.2f}")
    print(f"Largest Loss:        ${metrics['largest_loss']:.2f}")
    print(f"Max Consecutive Wins:   {metrics.get('max_consecutive_wins', 0)} ⭐ NEW")
    print(f"Max Consecutive Losses: {metrics.get('max_consecutive_losses', 0)} ⭐ NEW")
    print()
    
    # Interpretation
    print("=" * 80)
    print("INTERPRETATION")
    print("=" * 80)
    print()
    
    # Sharpe
    sharpe = metrics['sharpe_ratio']
    if sharpe > 2.0:
        sharpe_rating = "Excelente ⭐⭐⭐⭐⭐"
    elif sharpe > 1.5:
        sharpe_rating = "Muy bueno ⭐⭐⭐⭐"
    elif sharpe > 1.0:
        sharpe_rating = "Bueno ⭐⭐⭐"
    elif sharpe > 0.5:
        sharpe_rating = "Mediocre ⭐⭐"
    else:
        sharpe_rating = "Malo ⭐"
    
    print(f"Sharpe Ratio: {sharpe_rating}")
    
    # Sortino
    sortino = metrics.get('sortino_ratio', 0)
    if sortino > 2.5:
        sortino_rating = "Excelente ⭐⭐⭐⭐⭐"
    elif sortino > 2.0:
        sortino_rating = "Muy bueno ⭐⭐⭐⭐"
    elif sortino > 1.5:
        sortino_rating = "Bueno ⭐⭐⭐"
    else:
        sortino_rating = "Revisar ⭐⭐"
    
    print(f"Sortino Ratio: {sortino_rating}")
    
    # Max Drawdown
    dd = abs(metrics['max_drawdown'])
    if dd < 0.10:
        dd_rating = "Excelente (bajo riesgo) ⭐⭐⭐⭐⭐"
    elif dd < 0.15:
        dd_rating = "Bueno (riesgo moderado) ⭐⭐⭐⭐"
    elif dd < 0.20:
        dd_rating = "Aceptable (riesgo medio) ⭐⭐⭐"
    elif dd < 0.30:
        dd_rating = "Alto riesgo ⭐⭐"
    else:
        dd_rating = "Muy alto riesgo ⭐"
    
    print(f"Max Drawdown: {dd_rating}")
    
    # Calmar
    calmar = metrics['calmar_ratio']
    if calmar > 3.0:
        calmar_rating = "Excelente ⭐⭐⭐⭐⭐"
    elif calmar > 2.0:
        calmar_rating = "Muy bueno ⭐⭐⭐⭐"
    elif calmar > 1.0:
        calmar_rating = "Bueno ⭐⭐⭐"
    else:
        calmar_rating = "Revisar ⭐⭐"
    
    print(f"Calmar Ratio: {calmar_rating}")
    
    # Recovery Factor
    recovery = metrics.get('recovery_factor', 0)
    if recovery > 5.0:
        recovery_rating = "Excelente resiliencia ⭐⭐⭐⭐⭐"
    elif recovery > 3.0:
        recovery_rating = "Muy buena resiliencia ⭐⭐⭐⭐"
    elif recovery > 2.0:
        recovery_rating = "Buena resiliencia ⭐⭐⭐"
    else:
        recovery_rating = "Revisar resiliencia ⭐⭐"
    
    print(f"Recovery Factor: {recovery_rating}")
    
    # Consecutive Losses
    max_losses = metrics.get('max_consecutive_losses', 0)
    if max_losses < 5:
        losses_rating = "Excelente ⭐⭐⭐⭐⭐"
    elif max_losses < 8:
        losses_rating = "Bueno ⭐⭐⭐⭐"
    elif max_losses < 12:
        losses_rating = "Aceptable ⭐⭐⭐"
    else:
        losses_rating = "Difícil psicológicamente ⭐⭐"
    
    print(f"Max Consecutive Losses: {losses_rating}")
    
    print()
    print("=" * 80)
    print(f"Run ID: {result.run_id}")
    print("=" * 80)


if __name__ == "__main__":
    main()
