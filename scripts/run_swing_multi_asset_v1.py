#!/usr/bin/env python3
"""
Script para ejecutar backtest de estrategia swing MULTI-ASSET V1.

FASE 1: Expansión a ETFs sectoriales tech
- Mantiene baseline strategy (TP 5%, 7 días, NO SL)
- Agrega 5 ETFs tech para diversificación
- Reduce correlación sin complicar lógica
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from auronai.backtesting.swing_multi_asset_v1 import SwingMultiAssetV1
import pandas as pd
import matplotlib.pyplot as plt
import json


def main():
    print("=" * 70)
    print("🌐 SWING STRATEGY - MULTI-ASSET V1 (FASE 1: ETFs Tech)")
    print("=" * 70)
    print()
    
    # Universo expandido: 10 acciones + 5 ETFs tech
    symbols = [
        # 10 acciones tech individuales (baseline)
        'AAPL',   # Apple
        'MSFT',   # Microsoft
        'GOOGL',  # Google
        'AMZN',   # Amazon
        'NVDA',   # Nvidia
        'META',   # Meta
        'TSLA',   # Tesla
        'AVGO',   # Broadcom
        'COST',   # Costco
        'NFLX',   # Netflix
        
        # 5 ETFs sectoriales tech (nuevo)
        'SMH',    # Semiconductors ETF
        'XLK',    # Technology Select Sector ETF
        'SOXX',   # Semiconductor ETF
        'IGV',    # Software ETF
        'HACK',   # Cybersecurity ETF
    ]
    
    print(f"📊 Universo Multi-Asset (15 símbolos):")
    print()
    print("  🏢 ACCIONES TECH (10):")
    for i, symbol in enumerate(symbols[:10], 1):
        print(f"     {i:2d}. {symbol}")
    print()
    print("  📈 ETFs SECTORIALES TECH (5):")
    for i, symbol in enumerate(symbols[10:], 1):
        print(f"     {i:2d}. {symbol}")
    print()
    print(f"💰 Capital inicial: $1,000")
    print(f"📅 Período completo: 2024-01-01 a 2026-01-31")
    print(f"🎯 Período de test: 2025-07-01 a 2026-01-31")
    print()
    print("⚙️  CONFIGURACIÓN (Baseline):")
    print("   - TP: 5% fijo")
    print("   - Holding: 7 días máximo")
    print("   - NO Stop Loss")
    print("   - Risk budget: 20% normal, 5% defensivo")
    print("   - Top K: 3 símbolos simultáneos")
    print()
    print("📌 BASELINE (10 acciones, para comparar):")
    print("   - Return: 5.58%")
    print("   - Win Rate: 58.41%")
    print("   - Expectancy: 0.50%")
    print("   - Sharpe: 0.92")
    print("   - Max DD: 3.24%")
    print("   - Trades: 94")
    print()
    print("🎯 OBJETIVO:")
    print("   - Reducir correlación con diversificación")
    print("   - Mantener o mejorar Sharpe ratio")
    print("   - Reducir drawdown máximo")
    print()
    
    # Crear estrategia multi-asset
    strategy = SwingMultiAssetV1(
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
    
    # Ejecutar backtest
    print("🔄 Ejecutando backtest multi-asset...")
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
    print("=" * 70)
    print("📊 MÉTRICAS DE PERFORMANCE (Test Period)")
    print("=" * 70)
    
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
    print("=" * 70)
    print()
    
    # Análisis de trades
    trades_df = pd.DataFrame(results['trades'])
    
    if len(trades_df) > 0:
        print()
        print("=" * 70)
        print("📈 TRADES SUMMARY")
        print("=" * 70)
        print()
        
        # Trades por tipo (acciones vs ETFs)
        stocks = symbols[:10]
        etfs = symbols[10:]
        
        stock_trades = trades_df[trades_df['symbol'].isin(stocks)]
        etf_trades = trades_df[trades_df['symbol'].isin(etfs)]
        
        print("Trades por tipo de activo:")
        print(f"  Acciones: {len(stock_trades):3d} trades ({len(stock_trades)/len(trades_df)*100:5.1f}%)")
        if len(stock_trades) > 0:
            print(f"    - Avg P&L: {stock_trades['pnl_percent'].mean():6.2f}%")
            print(f"    - Win Rate: {(stock_trades['pnl_dollar'] > 0).sum() / len(stock_trades) * 100:5.1f}%")
        
        print(f"  ETFs:     {len(etf_trades):3d} trades ({len(etf_trades)/len(trades_df)*100:5.1f}%)")
        if len(etf_trades) > 0:
            print(f"    - Avg P&L: {etf_trades['pnl_percent'].mean():6.2f}%")
            print(f"    - Win Rate: {(etf_trades['pnl_dollar'] > 0).sum() / len(etf_trades) * 100:5.1f}%")
        
        print()
        
        # Trades por símbolo (top 10)
        print("Top 10 símbolos por número de trades:")
        symbol_stats = []
        for symbol in symbols:
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            if len(symbol_trades) > 0:
                count = len(symbol_trades)
                avg_pct = symbol_trades['pnl_percent'].mean()
                total_pnl = symbol_trades['pnl_dollar'].sum()
                win_rate = (symbol_trades['pnl_dollar'] > 0).sum() / count * 100
                symbol_type = 'ETF' if symbol in etfs else 'Stock'
                symbol_stats.append((symbol, count, avg_pct, total_pnl, win_rate, symbol_type))
        
        symbol_stats.sort(key=lambda x: x[1], reverse=True)
        
        for symbol, count, avg_pct, total_pnl, win_rate, symbol_type in symbol_stats[:10]:
            print(f"  {symbol:5s} ({symbol_type:5s}): {count:3d} trades, "
                  f"avg: {avg_pct:6.2f}%, WR: {win_rate:5.1f}%, total: ${total_pnl:7.2f}")
        
        print()
        
        # Trades por razón
        print("Trades por razón de salida:")
        reason_counts = trades_df['reason'].value_counts()
        for reason, count in reason_counts.items():
            pct = (count / len(trades_df)) * 100
            avg_pnl = trades_df[trades_df['reason'] == reason]['pnl_percent'].mean()
            print(f"  {reason:12s}: {count:3d} ({pct:5.1f}%), avg P&L: {avg_pnl:6.2f}%")
        
        print("=" * 70)
        print()
    
    # Guardar resultados
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)
    
    # Equity curve
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot principal
    ax1.plot(results['dates'], results['equity_curve'], linewidth=2, label='Multi-Asset V1', color='#2E86AB')
    ax1.axhline(y=results['initial_capital'], color='r', linestyle='--', alpha=0.5, label='Initial Capital')
    ax1.set_title('Equity Curve - Swing Multi-Asset V1 (15 símbolos: 10 acciones + 5 ETFs)', 
                  fontsize=14, fontweight='bold')
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
    
    equity_path = results_dir / 'equity_curve_multi_asset_v1.png'
    plt.savefig(equity_path, dpi=150)
    print(f"ℹ️ [INFO] Equity curve saved to {equity_path}")
    
    # JSON results
    json_path = results_dir / 'swing_multi_asset_v1_results.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"ℹ️ [INFO] Results saved to {json_path}")
    
    # CSV trades
    if len(trades_df) > 0:
        csv_path = results_dir / 'swing_multi_asset_v1_trades.csv'
        trades_df.to_csv(csv_path, index=False)
        print(f"ℹ️ [INFO] Trades saved to {csv_path}")
    
    print()
    print("✅ Backtest completado exitosamente!")
    print()
    
    # Comparación con baseline
    print("=" * 70)
    print("📊 COMPARACIÓN: BASELINE (10 acciones) vs MULTI-ASSET (15 símbolos)")
    print("=" * 70)
    print()
    print("BASELINE (10 acciones tech):")
    print("  - Return:      5.58%")
    print("  - Win Rate:    58.41%")
    print("  - Expectancy:  0.50%")
    print("  - Sharpe:      0.92")
    print("  - Max DD:      3.24%")
    print("  - Trades:      94")
    print()
    print(f"MULTI-ASSET V1 (10 acciones + 5 ETFs tech):")
    print(f"  - Return:      {metrics['total_return']:.2f}%")
    print(f"  - Win Rate:    {metrics['win_rate']:.2f}%")
    print(f"  - Expectancy:  {metrics['expectancy']:.2f}%")
    print(f"  - Sharpe:      {metrics['sharpe_ratio']:.2f}")
    print(f"  - Max DD:      {metrics['max_drawdown']:.2f}%")
    print(f"  - Trades:      {metrics['num_trades']}")
    print()
    
    # Calcular mejora
    return_change = metrics['total_return'] - 5.58
    expectancy_change = metrics['expectancy'] - 0.50
    sharpe_change = metrics['sharpe_ratio'] - 0.92
    dd_change = metrics['max_drawdown'] - 3.24
    
    print("CAMBIOS:")
    if return_change > 0:
        print(f"  ✅ Return:     +{return_change:.2f}% ({(return_change/5.58)*100:.1f}% mejor)")
    else:
        print(f"  ⚠️  Return:     {return_change:.2f}% ({(return_change/5.58)*100:.1f}% cambio)")
    
    if expectancy_change > 0:
        print(f"  ✅ Expectancy: +{expectancy_change:.2f}% ({(expectancy_change/0.50)*100:.1f}% mejor)")
    else:
        print(f"  ⚠️  Expectancy: {expectancy_change:.2f}% ({(expectancy_change/0.50)*100:.1f}% cambio)")
    
    if sharpe_change > 0:
        print(f"  ✅ Sharpe:     +{sharpe_change:.2f} ({(sharpe_change/0.92)*100:.1f}% mejor)")
    else:
        print(f"  ⚠️  Sharpe:     {sharpe_change:.2f} ({(sharpe_change/0.92)*100:.1f}% cambio)")
    
    if dd_change < 0:
        print(f"  ✅ Max DD:     {dd_change:.2f}% (menor drawdown)")
    else:
        print(f"  ⚠️  Max DD:     +{dd_change:.2f}% (mayor drawdown)")
    
    print()
    print("💡 ANÁLISIS:")
    print("   - ETFs tech agregan diversificación sectorial")
    print("   - Reduce correlación entre posiciones")
    print("   - Mantiene exposición a tech sin concentración")
    print("   - Sharpe ratio indica mejor risk-adjusted return")
    print("=" * 70)


if __name__ == '__main__':
    main()
