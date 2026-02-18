#!/usr/bin/env python3
"""
Test rápido para verificar que Long Momentum cierra posiciones.

Ejecuta un backtest corto y verifica que:
1. Se abren posiciones
2. Se cierran posiciones (TP, TimeExit, TrendReversal)
3. Se calcula P&L correctamente
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import datetime, timedelta
import pandas as pd

from auronai.backtesting.backtest_config import BacktestConfig
from auronai.backtesting.backtest_runner import BacktestRunner
from auronai.strategies.long_momentum import LongMomentumStrategy
from auronai.strategies.base_strategy import StrategyParams
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Ejecutar test de Long Momentum."""
    print("=" * 80)
    print("  TEST: Long Momentum - Verificación de Exits")
    print("=" * 80)
    print()
    
    # Configurar backtest (período corto para test rápido)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # 3 meses
    
    print(f"📅 Período: {start_date.date()} a {end_date.date()}")
    print(f"💰 Capital inicial: $10,000")
    print(f"📊 Símbolos: AAPL, MSFT, GOOGL, NVDA, TSLA")
    print()
    
    # Crear estrategia
    params = StrategyParams(
        top_k=3,
        holding_days=10,
        tp_multiplier=1.05,  # +5% TP
        risk_budget=0.20,
        defensive_risk_budget=0.05
    )
    
    strategy = LongMomentumStrategy(params)
    
    # Configurar backtest
    config = BacktestConfig(
        strategy_id="long_momentum_test",
        symbols=["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"],
        benchmark="QQQ",
        start_date=start_date,
        end_date=end_date,
        initial_capital=10000.0,
        commission_rate=0.0,  # Libertex 0%
        slippage_rate=0.001,  # 0.10%
        strategy_params=params.__dict__
    )
    
    print("🔄 Ejecutando backtest...")
    print()
    
    try:
        # Ejecutar backtest
        runner = BacktestRunner()
        result = runner.run(config, strategy)
        
        # Analizar resultados
        print("=" * 80)
        print("  RESULTADOS")
        print("=" * 80)
        print()
        
        metrics = result.metrics
        trades = result.trades
        
        # Verificar trades
        print(f"📈 Total Trades: {len(trades)}")
        
        if len(trades) == 0:
            print("❌ ERROR: No se generaron trades")
            return
        
        # Contar trades cerrados vs abiertos
        closed_trades = [t for t in trades if t['exit_date'] is not None]
        open_trades = [t for t in trades if t['exit_date'] is None]
        
        print(f"✅ Trades Cerrados: {len(closed_trades)}")
        print(f"⏳ Trades Abiertos: {len(open_trades)}")
        print()
        
        if len(closed_trades) == 0:
            print("❌ ERROR: Ningún trade fue cerrado")
            print("   La estrategia NO está cerrando posiciones correctamente")
            return
        
        # Analizar razones de salida
        print("📊 Razones de Salida:")
        exit_reasons = {}
        for trade in closed_trades:
            reason = trade.get('reason', 'Unknown')
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        for reason, count in sorted(exit_reasons.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(closed_trades)) * 100
            print(f"   {reason}: {count} ({pct:.1f}%)")
        print()
        
        # Verificar P&L
        trades_with_pnl = [t for t in closed_trades if t.get('pnl_dollar') is not None]
        
        if len(trades_with_pnl) == 0:
            print("❌ ERROR: Ningún trade tiene P&L calculado")
            return
        
        print(f"💵 Trades con P&L: {len(trades_with_pnl)} / {len(closed_trades)}")
        print()
        
        # Mostrar métricas clave
        print("📊 MÉTRICAS CLAVE:")
        print(f"   Total Return: {metrics.get('total_return', 0):.2%}")
        print(f"   Win Rate: {metrics.get('win_rate', 0):.2%}")
        print(f"   Profit Factor: {metrics.get('profit_factor', 0):.2f}")
        print(f"   Avg Win: ${metrics.get('avg_win', 0):.2f}")
        print(f"   Avg Loss: ${metrics.get('avg_loss', 0):.2f}")
        print(f"   Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
        print()
        
        # Mostrar algunos trades de ejemplo
        print("📋 EJEMPLOS DE TRADES CERRADOS:")
        print()
        
        for i, trade in enumerate(closed_trades[:5], 1):
            symbol = trade['symbol']
            entry_date = trade['entry_date']
            exit_date = trade['exit_date']
            entry_price = trade['entry_price']
            exit_price = trade['exit_price']
            pnl_pct = trade.get('pnl_percent', 0)
            pnl_dollar = trade.get('pnl_dollar', 0)
            reason = trade.get('reason', 'Unknown')
            
            # Calcular días
            if isinstance(entry_date, str):
                entry_dt = datetime.fromisoformat(entry_date)
                exit_dt = datetime.fromisoformat(exit_date)
                days = (exit_dt - entry_dt).days
            else:
                days = 0
            
            print(f"{i}. {symbol}")
            print(f"   Entry: {entry_date[:10]} @ ${entry_price:.2f}")
            print(f"   Exit:  {exit_date[:10]} @ ${exit_price:.2f}")
            print(f"   P&L: ${pnl_dollar:.2f} ({pnl_pct:+.2f}%)")
            print(f"   Días: {days} | Razón: {reason}")
            print()
        
        # Verificación final
        print("=" * 80)
        print("  VERIFICACIÓN")
        print("=" * 80)
        print()
        
        checks = []
        
        # Check 1: Trades generados
        if len(trades) > 0:
            checks.append(("✅", "Trades generados"))
        else:
            checks.append(("❌", "Trades generados"))
        
        # Check 2: Trades cerrados
        if len(closed_trades) > 0:
            checks.append(("✅", "Trades cerrados"))
        else:
            checks.append(("❌", "Trades cerrados"))
        
        # Check 3: P&L calculado
        if len(trades_with_pnl) > 0:
            checks.append(("✅", "P&L calculado"))
        else:
            checks.append(("❌", "P&L calculado"))
        
        # Check 4: Win rate > 0
        if metrics.get('win_rate', 0) > 0:
            checks.append(("✅", "Win rate > 0%"))
        else:
            checks.append(("❌", "Win rate > 0%"))
        
        # Check 5: Múltiples razones de salida
        if len(exit_reasons) > 1:
            checks.append(("✅", "Múltiples exit reasons"))
        else:
            checks.append(("⚠️", "Solo 1 exit reason (esperado: TP, TimeExit, TrendReversal)"))
        
        for status, check in checks:
            print(f"{status} {check}")
        
        print()
        
        # Resultado final
        failed_checks = [c for c in checks if c[0] == "❌"]
        
        if len(failed_checks) == 0:
            print("🎉 ¡ÉXITO! Long Momentum está cerrando posiciones correctamente")
            print()
            print(f"   Run ID: {result.run_id}")
            print(f"   Puedes ver los resultados completos en la UI")
        else:
            print("❌ FALLÓ: Hay problemas con el cierre de posiciones")
            print()
            for _, check in failed_checks:
                print(f"   - {check}")
        
    except Exception as e:
        logger.error(f"Error en test: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        print("\nVerifica:")
        print("  1. Conexión a internet")
        print("  2. Datos disponibles para los símbolos")
        print("  3. Logs en logs/auronai_errors.log")


if __name__ == "__main__":
    main()
