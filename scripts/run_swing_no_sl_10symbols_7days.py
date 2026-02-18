#!/usr/bin/env python3
"""
Script para ejecutar backtest de estrategia swing SIN Stop Loss.
Con 10 símbolos del QQQ, TP 5% y holding de 7 días (más corto).

Solo usa:
- Take Profit (5%)
- Time Exit (7 días máximo) ← Reducido de 10 días

NO usa Stop Loss para evitar imprecisión con datos diarios.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from auronai.backtesting.swing_no_sl_strategy import SwingNoSLStrategy
import pandas as pd
import matplotlib.pyplot as plt
import json


def main():
    print("=" * 60)
    print("🎯 SWING STRATEGY - SIN SL, TP 5%, 7 DÍAS (10 SÍMBOLOS)")
    print("=" * 60)
    print()
    
    # Top 10 símbolos del QQQ
    symbols = [
        'AAPL',   # Apple
        'MSFT',   # Microsoft
        'GOOGL',  # Google
        'AMZN',   # Amazon
        'NVDA',   # Nvidia
        'META',   # Meta (Facebook)
        'TSLA',   # Tesla
        'AVGO',   # Broadcom
        'COST',   # Costco
        'NFLX'    # Netflix
    ]
    
    print(f"📊 Símbolos (Top 10 QQQ):")
    for i, symbol in enumerate(symbols, 1):
        print(f"   {i:2d}. {symbol}")
    print()
    print(f"💰 Capital inicial: $1,000")
    print(f"📅 Período completo: 2024-01-01 a 2026-01-31")
    print(f"🎯 Período de test: 2025-07-01 a 2026-01-31")
    print()
    print("⚙️  CONFIGURACIÓN:")
    print("   ✅ Take Profit: 5%")
    print("   ✅ Time Exit: 7 días máximo ← REDUCIDO (antes 10)")
    print("   ❌ NO Stop Loss")
    print("   - Risk budget: 20% normal, 5% defensivo")
    print("   - Top K: 3 símbolos simultáneos")
    print()
    
    # Crear estrategia con 7 días de holding
    strategy = SwingNoSLStrategy(
        symbols=symbols,
        benchmark='QQQ',
        initial_capital=1000.0,
        base_risk_budget=0.20,
        defensive_risk_budget=0.05,
        top_k=3,
        tp_multiplier=1.05,  # 5% TP
        max_holding_days=7,  # 7 días (antes 10)
        dd_threshold_1=0.05,
        dd_threshold_2=0.08,
        dd_threshold_3=0.10,
        cooldown_days=10
    )
    
    # Ejecutar backtest
    print("🔄 Ejecutando backtest...")
    print()
    
    results = strategy.run_backtest(
        start_date='2024-01-01',
        end_date='2026-01-31',
        test_start_date='2025-07-01'
    )
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return
    
    # Mostrar métricas
    print()
    print("=" * 60)
    print("📊 MÉTRICAS DE PERFORMANCE (Test Period)")
    print("=" * 60)
    
    metrics = results['metrics']
    print(f"Total Return:        {metrics['total_return']:8.2f}%")
    print(f"CAGR:                {metrics['cagr']:8.2f}%")
    print(f"Number of Trades:    {metrics['num_trades']:8d}")
    print(f"Win Rate:            {metrics['win_rate']:8.2f}%")
    print(f"Avg Winner:          {metrics['avg_winner']:8.2f}%")
    print(f"Avg Loser:           {metrics['avg_loser']:8.2f}%")
    print(f"Profit Factor:       {metrics['profit_factor']:8.2f}")
    print(f"Expectancy:          {metrics['expectancy']:8.2f}%")
    print(f"Sharpe Ratio:        {metrics['sharpe_ratio']:8.2f}")
    print(f"Max Drawdown:        {metrics['max_drawdown']:8.2f}%")
    print(f"Exposure:            {metrics['exposure']:8.2f}%")
    print("=" * 60)
    print()
    
    # Análisis de trades
    trades_df = pd.DataFrame(results['trades'])
    
    if len(trades_df) > 0:
        print()
        print("=" * 60)
        print("📈 TRADES SUMMARY")
        print("=" * 60)
        print()
        
        # Trades por símbolo
        print("Trades por símbolo:")
        symbol_stats = []
        for symbol in symbols:
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            if len(symbol_trades) > 0:
                count = len(symbol_trades)
                avg_pct = symbol_trades['pnl_percent'].mean()
                total_pnl = symbol_trades['pnl_dollar'].sum()
                symbol_stats.append((symbol, count, avg_pct, total_pnl))
        
        symbol_stats.sort(key=lambda x: x[1], reverse=True)
        
        for symbol, count, avg_pct, total_pnl in symbol_stats:
            print(f"  {symbol:5s}: {count:3d} trades, avg: {avg_pct:6.2f}%, total: ${total_pnl:7.2f}")
        
        print()
        
        # Trades por razón
        print("Trades por razón de salida:")
        reason_counts = trades_df['reason'].value_counts()
        for reason, count in reason_counts.items():
            pct = (count / len(trades_df)) * 100
            avg_pnl = trades_df[trades_df['reason'] == reason]['pnl_percent'].mean()
            print(f"  {reason:12s}: {count:3d} ({pct:5.1f}%), avg P&L: {avg_pnl:6.2f}%")
        
        print()
        
        # Top trades
        print("Top 5 mejores trades:")
        top_trades = trades_df.nlargest(5, 'pnl_dollar')
        for _, trade in top_trades.iterrows():
            days = (pd.to_datetime(trade['exit_day']) - pd.to_datetime(trade['entry_day'])).days
            print(f"  {trade['symbol']:5s}: {trade['entry_day']} -> {trade['exit_day']} ({days:2d} días), "
                  f"P&L: ${trade['pnl_dollar']:6.2f} ({trade['pnl_percent']:5.2f}%), {trade['reason']}")
        
        print()
        
        print("Top 5 peores trades:")
        worst_trades = trades_df.nsmallest(5, 'pnl_dollar')
        for _, trade in worst_trades.iterrows():
            days = (pd.to_datetime(trade['exit_day']) - pd.to_datetime(trade['entry_day'])).days
            print(f"  {trade['symbol']:5s}: {trade['entry_day']} -> {trade['exit_day']} ({days:2d} días), "
                  f"P&L: ${trade['pnl_dollar']:6.2f} ({trade['pnl_percent']:5.2f}%), {trade['reason']}")
        
        print("=" * 60)
        print()
    
    # Guardar resultados
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)
    
    # Equity curve con comparación
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot principal
    ax1.plot(results['dates'], results['equity_curve'], linewidth=2, label='Equity (7 días)', color='#2E86AB')
    ax1.axhline(y=results['initial_capital'], color='r', linestyle='--', alpha=0.5, label='Initial Capital')
    ax1.set_title('Equity Curve - Swing Strategy (NO SL, TP 5%, 7 días, 10 Símbolos)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Equity ($)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Drawdown
    equity_series = pd.Series(results['equity_curve'])
    peak = equity_series.expanding(min_periods=1).max()
    drawdown = (equity_series - peak) / peak * 100
    ax2.fill_between(range(len(drawdown)), drawdown, 0, alpha=0.3, color='red')
    ax2.plot(drawdown, linewidth=1, color='darkred')
    ax2.set_title('Drawdown (%)', fontsize=12)
    ax2.set_ylabel('Drawdown (%)')
    ax2.set_xlabel('Days')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    equity_path = results_dir / 'equity_curve_no_sl_10symbols_7days.png'
    plt.savefig(equity_path, dpi=150)
    print(f"ℹ️ [INFO] Equity curve saved to {equity_path}")
    
    # JSON results
    json_path = results_dir / 'swing_no_sl_10symbols_7days_results.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"ℹ️ [INFO] Results saved to {json_path}")
    
    # CSV trades
    if len(trades_df) > 0:
        csv_path = results_dir / 'swing_no_sl_10symbols_7days_trades.csv'
        trades_df.to_csv(csv_path, index=False)
        print(f"ℹ️ [INFO] Trades saved to {csv_path}")
    
    print()
    print("✅ Backtest completado exitosamente!")
    print()
    
    # Comparación detallada
    print("=" * 60)
    print("📊 COMPARACIÓN: 10 días vs 7 días (ambos TP 5%)")
    print("=" * 60)
    print()
    print("10 días (anterior):")
    print("  - Return: 5.49%")
    print("  - Max DD: 5.04%")
    print("  - Trades: 94")
    print("  - Win Rate: 54.26%")
    print("  - TP exits: 39.8%")
    print("  - Time exits: 59.0%")
    print()
    print(f"7 días (actual):")
    print(f"  - Return: {metrics['total_return']:.2f}%")
    print(f"  - Max DD: {metrics['max_drawdown']:.2f}%")
    print(f"  - Trades: {metrics['num_trades']}")
    print(f"  - Win Rate: {metrics['win_rate']:.2f}%")
    
    if len(trades_df) > 0:
        tp_pct = (reason_counts.get('TP', 0) / len(trades_df)) * 100
        time_pct = (reason_counts.get('TimeExit', 0) / len(trades_df)) * 100
        print(f"  - TP exits: {tp_pct:.1f}%")
        print(f"  - Time exits: {time_pct:.1f}%")
    
    print()
    
    if metrics['total_return'] > 5.49:
        improvement = metrics['total_return'] - 5.49
        print(f"✅ Mejora: +{improvement:.2f}% de retorno")
    else:
        decline = 5.49 - metrics['total_return']
        print(f"⚠️  Decline: -{decline:.2f}% de retorno")
    
    print()
    print("💡 ANÁLISIS:")
    print("   - Holding más corto (7 días) = más rotación de capital")
    print("   - Más trades totales = más oportunidades")
    print("   - Menos tiempo expuesto a reversiones")
    print("   - Trade-off: menos tiempo para alcanzar TP vs más eficiencia")
    print("=" * 60)


if __name__ == '__main__':
    main()
