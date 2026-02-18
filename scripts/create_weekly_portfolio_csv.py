#!/usr/bin/env python3
"""
Create weekly portfolio CSV from Libertex backtest results.
Simple script to generate actionable weekly trading plan.
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path


def create_weekly_portfolio_csv():
    """Create weekly portfolio tracking CSV from backtest results."""
    
    print("\n" + "="*60)
    print("📊 CREANDO REPORTE SEMANAL DE PORTFOLIO")
    print("="*60 + "\n")
    
    # Load results
    results_file = Path("results/momentum_libertex_risk_levels.json")
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    # Get best config (50% risk budget)
    best_config = data['results'][0]  # Weekly-50%
    
    print(f"Configuración: {best_config['frequency_name']}")
    print(f"Risk Budget: {best_config['risk_budget']*100:.0f}%")
    print(f"Capital Inicial: $1,000.00")
    print(f"Capital Final: ${best_config['final_equity']:,.2f}")
    print(f"Retorno: {best_config['net_return']*100:.2f}%\n")
    
    # Extract trades
    trades = best_config['trades']
    
    # Create weekly schedule
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2025, 2, 1)
    
    weekly_data = []
    current_date = start_date
    week_num = 0
    
    # Initial state
    cash = 1000.0
    positions = {}
    
    while current_date <= end_date:
        week_num += 1
        week_end = current_date + timedelta(days=6)
        
        # Check for trades this week
        week_trades = []
        for trade in trades:
            entry_date = datetime.fromisoformat(trade['entry_date'].replace('T00:00:00', ''))
            if current_date <= entry_date <= week_end:
                week_trades.append(trade)
        
        # Determine action
        action = "HOLD"
        symbols_bought = []
        shares_bought = []
        cost = 0
        
        if week_trades:
            action = "BUY"
            for trade in week_trades:
                symbol = trade['symbol']
                shares = trade['shares']
                price = trade['entry_price']
                trade_cost = shares * price + 1.0  # +$1 commission
                
                symbols_bought.append(symbol)
                shares_bought.append(f"{shares:.2f}")
                cost += trade_cost
                
                # Update positions
                positions[symbol] = {
                    'shares': shares,
                    'entry_price': price,
                    'entry_date': entry_date
                }
                
                # Update cash
                cash -= trade_cost
        
        # Calculate portfolio value
        positions_value = sum(
            pos['shares'] * pos['entry_price'] 
            for pos in positions.values()
        )
        total_value = cash + positions_value
        
        # Create weekly record
        record = {
            'Semana': week_num,
            'Fecha_Inicio': current_date.strftime('%Y-%m-%d'),
            'Fecha_Fin': week_end.strftime('%Y-%m-%d'),
            'Accion': action,
            'Simbolos_Comprados': ', '.join(symbols_bought) if symbols_bought else '-',
            'Acciones_Compradas': ', '.join(shares_bought) if shares_bought else '-',
            'Costo_Compras': f"${cost:.2f}" if cost > 0 else '-',
            'Comision': f"${len(week_trades) * 1.0:.2f}" if week_trades else '-',
            'Posiciones_Activas': len(positions),
            'Simbolos_Activos': ', '.join(positions.keys()) if positions else '-',
            'Acciones_Activas': ', '.join([f"{p['shares']:.2f}" for p in positions.values()]) if positions else '-',
            'Valor_Posiciones': f"${positions_value:.2f}",
            'Efectivo_Disponible': f"${cash:.2f}",
            'Balance_Total': f"${total_value:.2f}",
            'Ganancia': f"${total_value - 1000:.2f}",
            'Retorno_Pct': f"{((total_value / 1000) - 1) * 100:.2f}%"
        }
        
        weekly_data.append(record)
        
        # Move to next week
        current_date = week_end + timedelta(days=1)
    
    # Create DataFrame
    df = pd.DataFrame(weekly_data)
    
    # Save to CSV
    output_file = Path("results/libertex_weekly_portfolio.csv")
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"✅ CSV creado: {output_file}")
    print(f"\n📊 RESUMEN:")
    print(f"   Total semanas: {len(df)}")
    print(f"   Semanas con compras: {len(df[df['Accion'] == 'BUY'])}")
    print(f"   Semanas en HOLD: {len(df[df['Accion'] == 'HOLD'])}")
    
    # Show key weeks
    buy_weeks = df[df['Accion'] == 'BUY']
    
    print(f"\n📋 SEMANAS CON COMPRAS:")
    for _, row in buy_weeks.iterrows():
        print(f"\n   Semana {row['Semana']} ({row['Fecha_Inicio']}):")
        print(f"   Comprar: {row['Simbolos_Comprados']}")
        print(f"   Acciones: {row['Acciones_Compradas']}")
        print(f"   Costo: {row['Costo_Compras']}")
        print(f"   Balance después: {row['Balance_Total']}")
    
    # Show final state
    final_row = df.iloc[-1]
    print(f"\n💰 ESTADO FINAL (Semana {final_row['Semana']}):")
    print(f"   Posiciones: {final_row['Simbolos_Activos']}")
    print(f"   Acciones: {final_row['Acciones_Activas']}")
    print(f"   Valor posiciones: {final_row['Valor_Posiciones']}")
    print(f"   Efectivo: {final_row['Efectivo_Disponible']}")
    print(f"   Balance total: {final_row['Balance_Total']}")
    print(f"   Ganancia: {final_row['Ganancia']}")
    print(f"   Retorno: {final_row['Retorno_Pct']}")
    
    print(f"\n{'='*60}")
    print("✅ REPORTE COMPLETADO")
    print(f"{'='*60}\n")
    
    print("💡 Abre el CSV en Excel/Google Sheets para ver el detalle completo")
    print("📱 Usa este reporte para ejecutar las operaciones en Libertex\n")
    
    return df


if __name__ == "__main__":
    df = create_weekly_portfolio_csv()
