#!/usr/bin/env python3
"""
Calculate current portfolio value with real market prices.
Shows exact position sizes and current value.
"""

import sys
from pathlib import Path
import json
import yfinance as yf
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def get_current_prices(symbols, date_str="2025-02-01"):
    """Get prices for symbols on specific date."""
    prices = {}
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=date_str, end=date_str, interval="1d")
            
            if not hist.empty:
                prices[symbol] = float(hist['Close'].iloc[0])
            else:
                # Try getting latest available
                hist = ticker.history(period="5d")
                if not hist.empty:
                    prices[symbol] = float(hist['Close'].iloc[-1])
                else:
                    prices[symbol] = None
        except Exception as e:
            print(f"⚠️ Error getting price for {symbol}: {e}")
            prices[symbol] = None
    
    return prices


def calculate_portfolio_value():
    """Calculate current portfolio value."""
    
    print("\n" + "="*70)
    print("💰 VALOR ACTUAL DEL PORTFOLIO - LIBERTEX 50%")
    print("="*70 + "\n")
    
    # Load backtest results
    results_file = Path("results/momentum_libertex_risk_levels.json")
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    # Get best config (50% risk budget)
    config = data['results'][0]
    trades = config['trades']
    
    print("📊 POSICIONES ABIERTAS:\n")
    
    # Get symbols
    symbols = [trade['symbol'] for trade in trades]
    
    # Get current prices
    print("📡 Obteniendo precios actuales de mercado...\n")
    current_prices = get_current_prices(symbols, "2025-02-01")
    
    total_invested = 0
    total_current_value = 0
    total_commissions = 2.0  # $1 per trade x 2 trades
    
    positions = []
    
    for trade in trades:
        symbol = trade['symbol']
        shares = trade['shares']
        entry_price = trade['entry_price']
        entry_date = trade['entry_date']
        
        invested = shares * entry_price
        current_price = current_prices.get(symbol)
        
        if current_price:
            current_value = shares * current_price
            pnl = current_value - invested
            pnl_pct = (pnl / invested) * 100
        else:
            current_value = invested
            pnl = 0
            pnl_pct = 0
            current_price = entry_price
        
        total_invested += invested
        total_current_value += current_value
        
        positions.append({
            'symbol': symbol,
            'shares': shares,
            'entry_price': entry_price,
            'entry_date': entry_date,
            'current_price': current_price,
            'invested': invested,
            'current_value': current_value,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })
        
        print(f"🔹 {symbol}")
        print(f"   Acciones: {shares:.4f}")
        print(f"   Precio entrada: ${entry_price:.2f} ({entry_date[:10]})")
        print(f"   Precio actual: ${current_price:.2f}")
        print(f"   Invertido: ${invested:.2f}")
        print(f"   Valor actual: ${current_value:.2f}")
        print(f"   P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
        print()
    
    # Calculate totals
    initial_capital = 1000.0
    cash = initial_capital - total_invested - total_commissions
    total_portfolio = total_current_value + cash
    total_pnl = total_portfolio - initial_capital
    total_return_pct = (total_pnl / initial_capital) * 100
    
    print("="*70)
    print("📈 RESUMEN DEL PORTFOLIO:\n")
    print(f"Capital inicial:        ${initial_capital:,.2f}")
    print(f"Invertido en acciones:  ${total_invested:,.2f}")
    print(f"Comisiones pagadas:     ${total_commissions:,.2f}")
    print(f"Efectivo disponible:    ${cash:,.2f}")
    print()
    print(f"Valor actual acciones:  ${total_current_value:,.2f}")
    print(f"Efectivo:               ${cash:,.2f}")
    print(f"Balance total:          ${total_portfolio:,.2f}")
    print()
    print(f"Ganancia/Pérdida:       ${total_pnl:+,.2f}")
    print(f"Retorno total:          {total_return_pct:+.2f}%")
    print(f"Retorno anualizado:     {config['annualized_return']*100:.2f}%")
    print()
    print("="*70)
    
    # Save detailed report
    report = {
        "fecha_calculo": datetime.now().isoformat(),
        "fecha_portfolio": "2025-02-01",
        "capital_inicial": initial_capital,
        "posiciones": positions,
        "resumen": {
            "total_invertido": total_invested,
            "comisiones_pagadas": total_commissions,
            "efectivo_disponible": cash,
            "valor_actual_acciones": total_current_value,
            "balance_total": total_portfolio,
            "ganancia_perdida": total_pnl,
            "retorno_pct": total_return_pct,
            "retorno_anualizado": config['annualized_return'] * 100
        }
    }
    
    output_file = Path("results/libertex_portfolio_actual.json")
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Reporte detallado guardado en: {output_file}\n")
    
    return report


if __name__ == "__main__":
    report = calculate_portfolio_value()
