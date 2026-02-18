#!/usr/bin/env python3
"""
Generate detailed weekly portfolio report for Libertex momentum strategy.
Creates a CSV with week-by-week balance, positions, and actions.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auronai.strategies.dual_momentum import DualMomentumStrategy, DualMomentumParams
from auronai.backtesting.backtest_config import BacktestConfig
from auronai.backtesting.backtest_runner import BacktestRunner
from auronai.data.symbol_universe import SymbolUniverseManager


def generate_weekly_report(
    initial_capital: float = 1000.0,
    risk_budget: float = 0.50,
    start_date: str = "2021-01-01",
    end_date: str = "2025-02-01",
    output_file: str = "results/libertex_weekly_portfolio.csv"
):
    """Generate detailed weekly portfolio report."""
    
    print(f"\n{'='*60}")
    print("📊 GENERANDO REPORTE SEMANAL DE PORTFOLIO")
    print(f"{'='*60}\n")
    
    print(f"Capital inicial: ${initial_capital:,.2f}")
    print(f"Risk budget: {risk_budget*100:.0f}%")
    print(f"Período: {start_date} a {end_date}")
    print(f"Rebalanceo: Semanal (7 días)\n")
    
    # Get symbols
    universe_manager = SymbolUniverseManager()
    symbols = universe_manager.get_symbols('momentum_rotation')
    
    # Create strategy params
    params = DualMomentumParams(
        lookback_period=90,
        top_n=3,
        rebalance_frequency='weekly',
        risk_budget=risk_budget
    )
    
    # Create strategy
    strategy = DualMomentumStrategy(params)
    
    # Create config
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    config = BacktestConfig(
        strategy_id=f"libertex_weekly_{int(risk_budget*100)}pct",
        symbols=symbols,
        start_date=start_dt,
        end_date=end_dt,
        initial_capital=initial_capital,
        commission_rate=0.001,
        slippage_rate=0.0005,
        benchmark='SPY',
        strategy_params=params.__dict__
    )
    
    # Run backtest
    backtest_runner = BacktestRunner()
    results = backtest_runner.run(config, strategy)
    
    if not hasattr(results, 'metrics') or not results.metrics:
        print(f"❌ Error en backtest")
        return
    
    print(f"✅ Backtest completado")
    print(f"Trades ejecutados: {results.metrics.get('num_trades', 0)}")
    print(f"Capital final: ${results.metrics.get('final_equity', initial_capital):,.2f}\n")
    
    # Generate weekly report
    print("📝 Generando reporte semanal...\n")
    
    weekly_data = []
    equity_curve = results.equity_curve if hasattr(results, 'equity_curve') else []
    trades = results.trades if hasattr(results, 'trades') else []
    
    # Convert trades to DataFrame for easier processing
    trades_df = pd.DataFrame(trades)
    if not trades_df.empty:
        trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
        if 'exit_date' in trades_df.columns:
            trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'], errors='coerce')
    
    # Process equity curve week by week
    current_date = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    week_num = 0
    
    while current_date <= end_dt:
        week_num += 1
        week_end = current_date + timedelta(days=6)
        
        # Find equity at end of week
        week_equity = None
        for eq_point in equity_curve:
            eq_date = pd.to_datetime(eq_point['date'])
            if current_date <= eq_date <= week_end:
                week_equity = eq_point['equity']
        
        if week_equity is None:
            # Use last known equity
            if equity_curve:
                week_equity = equity_curve[-1]['equity']
            else:
                week_equity = initial_capital
        
        # Find trades opened this week
        opened_trades = []
        closed_trades = []
        
        if not trades_df.empty:
            # Trades opened this week
            week_opens = trades_df[
                (trades_df['entry_date'] >= current_date) & 
                (trades_df['entry_date'] <= week_end)
            ]
            
            for _, trade in week_opens.iterrows():
                opened_trades.append({
                    'symbol': trade['symbol'],
                    'shares': trade['shares'],
                    'entry_price': trade['entry_price'],
                    'cost': trade['shares'] * trade['entry_price']
                })
            
            # Trades closed this week
            if 'exit_date' in trades_df.columns:
                week_closes = trades_df[
                    (trades_df['exit_date'] >= current_date) & 
                    (trades_df['exit_date'] <= week_end)
                ]
                
                for _, trade in week_closes.iterrows():
                    closed_trades.append({
                        'symbol': trade['symbol'],
                        'shares': trade['shares'],
                        'exit_price': trade.get('exit_price', 0),
                        'pnl': trade.get('pnl', 0)
                    })
        
        # Calculate positions value and cash
        positions_value = 0
        active_positions = []
        
        if not trades_df.empty:
            # Find all open positions at end of week
            for _, trade in trades_df.iterrows():
                if trade['entry_date'] <= week_end:
                    # Check if still open
                    if pd.isna(trade.get('exit_date')) or trade.get('exit_date') > week_end:
                        position_value = trade['shares'] * trade['entry_price']
                        positions_value += position_value
                        active_positions.append({
                            'symbol': trade['symbol'],
                            'shares': trade['shares'],
                            'entry_price': trade['entry_price'],
                            'value': position_value
                        })
        
        cash = week_equity - positions_value
        
        # Determine action
        action = "HOLD"
        if opened_trades:
            action = "BUY"
        if closed_trades:
            action = "SELL" if not opened_trades else "REBALANCE"
        
        # Create weekly record
        weekly_record = {
            'Semana': week_num,
            'Fecha_Inicio': current_date.strftime('%Y-%m-%d'),
            'Fecha_Fin': week_end.strftime('%Y-%m-%d'),
            'Accion': action,
            'Posiciones_Abiertas': len(opened_trades),
            'Posiciones_Cerradas': len(closed_trades),
            'Simbolos_Comprados': ', '.join([t['symbol'] for t in opened_trades]) if opened_trades else '-',
            'Acciones_Compradas': ', '.join([f"{t['shares']:.2f}" for t in opened_trades]) if opened_trades else '-',
            'Costo_Compras': sum([t['cost'] for t in opened_trades]) if opened_trades else 0,
            'Simbolos_Vendidos': ', '.join([t['symbol'] for t in closed_trades]) if closed_trades else '-',
            'PnL_Ventas': sum([t['pnl'] for t in closed_trades]) if closed_trades else 0,
            'Posiciones_Activas': len(active_positions),
            'Simbolos_Activos': ', '.join([p['symbol'] for p in active_positions]) if active_positions else '-',
            'Valor_Posiciones': positions_value,
            'Efectivo': cash,
            'Balance_Total': week_equity,
            'Ganancia_Acumulada': week_equity - initial_capital,
            'Retorno_Pct': ((week_equity / initial_capital) - 1) * 100
        }
        
        weekly_data.append(weekly_record)
        
        # Move to next week
        current_date = week_end + timedelta(days=1)
    
    # Create DataFrame
    df = pd.DataFrame(weekly_data)
    
    # Save to CSV
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"✅ Reporte guardado en: {output_path}")
    print(f"\n📊 RESUMEN DEL REPORTE:")
    print(f"   Total semanas: {len(df)}")
    print(f"   Semanas con compras: {len(df[df['Accion'].isin(['BUY', 'REBALANCE'])])}")
    print(f"   Semanas con ventas: {len(df[df['Accion'].isin(['SELL', 'REBALANCE'])])}")
    print(f"   Capital inicial: ${initial_capital:,.2f}")
    print(f"   Capital final: ${df.iloc[-1]['Balance_Total']:,.2f}")
    print(f"   Ganancia total: ${df.iloc[-1]['Ganancia_Acumulada']:,.2f}")
    print(f"   Retorno total: {df.iloc[-1]['Retorno_Pct']:.2f}%")
    
    # Print first few weeks as preview
    print(f"\n📋 PRIMERAS 5 SEMANAS:")
    print(df.head(5)[['Semana', 'Fecha_Inicio', 'Accion', 'Simbolos_Comprados', 
                      'Balance_Total', 'Retorno_Pct']].to_string(index=False))
    
    # Print last few weeks
    print(f"\n📋 ÚLTIMAS 5 SEMANAS:")
    print(df.tail(5)[['Semana', 'Fecha_Inicio', 'Accion', 'Simbolos_Activos', 
                      'Balance_Total', 'Retorno_Pct']].to_string(index=False))
    
    # Also save summary JSON
    summary = {
        "generated_at": datetime.now().isoformat(),
        "config": {
            "initial_capital": initial_capital,
            "risk_budget": risk_budget,
            "start_date": start_date,
            "end_date": end_date,
            "rebalance_days": 7
        },
        "summary": {
            "total_weeks": len(df),
            "weeks_with_trades": len(df[df['Accion'] != 'HOLD']),
            "total_buys": len(df[df['Accion'].isin(['BUY', 'REBALANCE'])]),
            "total_sells": len(df[df['Accion'].isin(['SELL', 'REBALANCE'])]),
            "initial_capital": initial_capital,
            "final_capital": float(df.iloc[-1]['Balance_Total']),
            "total_gain": float(df.iloc[-1]['Ganancia_Acumulada']),
            "total_return_pct": float(df.iloc[-1]['Retorno_Pct']),
            "max_positions": int(df['Posiciones_Activas'].max()),
            "avg_cash_balance": float(df['Efectivo'].mean())
        }
    }
    
    summary_path = output_path.parent / f"{output_path.stem}_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ Resumen guardado en: {summary_path}")
    print(f"\n{'='*60}")
    print("✅ REPORTE COMPLETADO")
    print(f"{'='*60}\n")
    
    return df


if __name__ == "__main__":
    # Generate report for 50% risk budget (best performer)
    df = generate_weekly_report(
        initial_capital=1000.0,
        risk_budget=0.50,
        start_date="2021-01-01",
        end_date="2025-02-01",
        output_file="results/libertex_weekly_portfolio.csv"
    )
    
    print("\n💡 TIP: Abre el archivo CSV en Excel o Google Sheets para ver el detalle completo")
    print("📊 Columnas incluidas:")
    print("   - Semana, Fechas, Acción (BUY/SELL/HOLD/REBALANCE)")
    print("   - Símbolos comprados/vendidos, Acciones, Costos")
    print("   - Posiciones activas, Valor de posiciones")
    print("   - Efectivo disponible, Balance total")
    print("   - Ganancia acumulada, Retorno %")
