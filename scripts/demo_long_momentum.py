#!/usr/bin/env python3
"""
Demo interactivo de la estrategia Long Momentum.

Este script te permite:
1. Ver cómo funciona la estrategia paso a paso
2. Ejecutar backtest con diferentes parámetros
3. Generar señales actuales para trading real
4. Comparar con buy-and-hold

Uso:
    python scripts/demo_long_momentum.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import datetime, timedelta
import pandas as pd

from auronai.backtesting.backtest_config import BacktestConfig
from auronai.backtesting.backtest_runner import BacktestRunner
from auronai.strategies.base_strategy import StrategyParams
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_section(text: str):
    """Print formatted section."""
    print(f"\n--- {text} ---\n")


def demo_basic_concept():
    """Explicar el concepto básico de momentum."""
    print_header("📚 CONCEPTO: ¿Qué es Long Momentum?")
    
    print("""
Long Momentum es una estrategia que:

1. 🎯 IDENTIFICA ganadores recientes (acciones con mejor performance)
2. 📈 COMPRA los top performers (asumiendo que continuarán subiendo)
3. ⏱️  MANTIENE por período corto-medio (días/semanas)
4. 🔄 REBALANCEA regularmente para capturar nuevos ganadores

Filosofía: "La tendencia es tu amiga" - Las acciones que suben tienden a seguir subiendo.

Ejemplo Real:
- Enero 2024: NVDA sube +20% (momentum fuerte)
- Febrero 2024: Estrategia compra NVDA
- Marzo 2024: NVDA sube otro +15%
- Resultado: Capturamos parte de la tendencia alcista
    """)
    
    input("Presiona Enter para continuar...")


def demo_regime_filter():
    """Explicar el filtro de régimen."""
    print_header("🌡️ FILTRO DE RÉGIMEN: ¿Cuándo Operar?")
    
    print("""
La estrategia SOLO opera en mercados BULL (alcistas).

Detección de Régimen (usando QQQ como benchmark):
┌─────────────────────────────────────────────────────┐
│ BULL:    Precio > EMA200 Y EMA200 con pendiente ↗   │
│ BEAR:    Precio < EMA200 Y EMA200 con pendiente ↘   │
│ NEUTRAL: Otros casos (mercado lateral/choppy)       │
└─────────────────────────────────────────────────────┘

¿Por qué este filtro?
✅ Momentum funciona mejor en tendencias claras
✅ Evita whipsaws en mercados laterales
✅ Protege en crashes (sale a cash)

Ejemplo:
- 2023: Mercado BULL → Estrategia activa → +25% retorno
- 2022: Mercado BEAR → Estrategia en cash → 0% retorno (vs -20% del mercado)
    """)
    
    input("Presiona Enter para continuar...")


def demo_selection_criteria():
    """Explicar criterios de selección."""
    print_header("🎯 SELECCIÓN: ¿Qué Comprar?")
    
    print("""
Proceso de Selección (3 pasos):

1️⃣ FILTRO INICIAL:
   - EMA20 > EMA50 (tendencia alcista de corto plazo)
   - RSI < 70 (no sobrecomprado)
   - Relative Strength positivo vs benchmark

2️⃣ RANKING:
   - Ordenar por Relative Strength (descendente)
   - Relative Strength = (Precio actual / Precio hace N días) - 1

3️⃣ SELECCIÓN:
   - Top K símbolos (default: 3)
   - Peso igual entre seleccionados (33.3% cada uno)

Ejemplo con 5 candidatos:
┌────────┬──────────┬─────────┬─────┬──────────────┐
│ Symbol │ RS (%)   │ EMA20>50│ RSI │ Seleccionado │
├────────┼──────────┼─────────┼─────┼──────────────┤
│ NVDA   │ +25.3%   │ ✅      │ 65  │ ✅ Top 1     │
│ TSLA   │ +18.7%   │ ✅      │ 62  │ ✅ Top 2     │
│ AAPL   │ +12.4%   │ ✅      │ 58  │ ✅ Top 3     │
│ MSFT   │ +8.2%    │ ✅      │ 55  │ ❌           │
│ GOOGL  │ +5.1%    │ ✅      │ 52  │ ❌           │
└────────┴──────────┴─────────┴─────┴──────────────┘

Portfolio resultante:
- NVDA: 33.3% ($3,333 con $10K)
- TSLA: 33.3% ($3,333)
- AAPL: 33.3% ($3,334)
- Cash: 0% (100% invertido en BULL)
    """)
    
    input("Presiona Enter para continuar...")


def demo_risk_management():
    """Explicar gestión de riesgo."""
    print_header("🛡️ GESTIÓN DE RIESGO: Protegiendo tu Capital")
    
    print("""
Controles de Riesgo Integrados:

1️⃣ EXPOSICIÓN MÁXIMA: 20% del portfolio
   - Con $10K → Máximo $2K en riesgo
   - Resto en cash como colchón

2️⃣ LÍMITE POR POSICIÓN: 20% / K
   - Con K=3 → Máximo 6.67% por símbolo
   - Evita concentración excesiva

3️⃣ TAKE PROFIT: +5% (configurable)
   - Vende automáticamente al alcanzar objetivo
   - Cristaliza ganancias

4️⃣ TIME EXIT: 10 días (configurable)
   - Vende si no alcanza TP en tiempo límite
   - Evita posiciones estancadas

5️⃣ TREND REVERSAL: EMA20 cruza bajo EMA50
   - Señal de cambio de tendencia
   - Salida anticipada

Ejemplo de Trade:
┌──────────────────────────────────────────────────┐
│ Día 0:  Compra NVDA @ $500 (6.67% del portfolio) │
│ Día 3:  NVDA @ $525 (+5%) → TAKE PROFIT ✅       │
│ Ganancia: $25 × shares = +$333                   │
│ Retorno: +5% en 3 días = +608% anualizado       │
└──────────────────────────────────────────────────┘

Escenario de Pérdida:
┌──────────────────────────────────────────────────┐
│ Día 0:  Compra TSLA @ $200                       │
│ Día 5:  EMA20 cruza bajo EMA50 → VENTA ❌        │
│ Precio: $195 (-2.5%)                             │
│ Pérdida: -$25 × shares = -$166                   │
│ Impacto: -1.66% del portfolio total              │
└──────────────────────────────────────────────────┘
    """)
    
    input("Presiona Enter para continuar...")


def run_sample_backtest():
    """Ejecutar backtest de ejemplo."""
    print_header("🔬 BACKTEST: Validando la Estrategia")
    
    print("Ejecutando backtest con parámetros estándar...")
    print("Símbolos: AAPL, MSFT, GOOGL, NVDA, TSLA")
    print("Período: Últimos 2 años")
    print("Capital inicial: $10,000\n")
    
    try:
        # Configurar backtest
        config = BacktestConfig(
            strategy_name="long_momentum",
            symbols=["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"],
            start_date=datetime.now() - timedelta(days=730),
            end_date=datetime.now(),
            initial_capital=10000.0,
            commission=0.0,
            slippage=0.0005,
            strategy_params=StrategyParams(
                top_k=3,
                holding_days=10,
                tp_multiplier=1.05,
                risk_budget=0.20
            )
        )
        
        # Ejecutar
        runner = BacktestRunner(config)
        results = runner.run()
        
        # Mostrar resultados
        print_section("📊 RESULTADOS")
        
        metrics = results['metrics']
        print(f"Retorno Total:        {metrics['total_return']:.2%}")
        print(f"Retorno Anualizado:   {metrics['annualized_return']:.2%}")
        print(f"Sharpe Ratio:         {metrics['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:         {metrics['max_drawdown']:.2%}")
        print(f"Win Rate:             {metrics['win_rate']:.2%}")
        print(f"Profit Factor:        {metrics['profit_factor']:.2f}")
        print(f"Total Trades:         {metrics['total_trades']}")
        
        # Comparación con buy-and-hold
        if 'benchmark_return' in metrics:
            print(f"\n📈 vs Buy-and-Hold:")
            print(f"Benchmark Return:     {metrics['benchmark_return']:.2%}")
            alpha = metrics['total_return'] - metrics['benchmark_return']
            print(f"Alpha (exceso):       {alpha:.2%}")
        
        print("\n✅ Backtest completado exitosamente!")
        print(f"📁 Resultados guardados en: {results['output_dir']}")
        
    except Exception as e:
        logger.error(f"Error en backtest: {e}")
        print(f"\n❌ Error: {e}")
        print("Verifica que tienes conexión a internet y datos disponibles.")
    
    input("\nPresiona Enter para continuar...")


def show_implementation_guide():
    """Mostrar guía de implementación."""
    print_header("🚀 IMPLEMENTACIÓN: Cómo Empezar")
    
    print("""
OPCIÓN 1: Paper Trading (Recomendado para empezar)
──────────────────────────────────────────────────
1. Ejecuta el sistema en modo simulación:
   $ python main.py --mode paper --strategy long_momentum

2. Monitorea resultados durante 1-2 meses

3. Si los resultados son buenos → Pasa a real con capital pequeño


OPCIÓN 2: Trading Manual (Más control)
───────────────────────────────────────
1. Cada lunes por la mañana:
   $ python main.py --mode signals --strategy long_momentum

2. Revisa las señales generadas

3. Ejecuta manualmente en tu broker:
   - Vende posiciones que ya no están en top 3
   - Compra nuevas posiciones
   - Usa órdenes limit para mejor precio

4. Configura alertas para take profits y stops


OPCIÓN 3: Automatización Completa (Avanzado)
─────────────────────────────────────────────
1. Configura integración con broker API (Alpaca, IB)

2. Ejecuta en servidor/cloud 24/7

3. Monitoreo automático y alertas

4. Ver: docs/technical/live-trading-integration.md


CHECKLIST ANTES DE EMPEZAR:
───────────────────────────
☐ Capital mínimo: $10,000 (recomendado)
☐ Broker con comisiones $0
☐ Backtest validado en tu universo de símbolos
☐ Entiendes los riesgos (drawdowns hasta -25%)
☐ Puedes monitorear semanalmente
☐ Tienes plan de salida si no funciona


RECURSOS:
─────────
📖 Documentación completa: docs/user/estrategia-long-momentum.md
🔬 Scripts de backtest: scripts/run_backtest.py
💡 Ejemplos: examples/
    """)
    
    input("\nPresiona Enter para continuar...")


def show_pros_cons_summary():
    """Mostrar resumen de pros y contras."""
    print_header("⚖️ PROS Y CONTRAS: Decisión Informada")
    
    print("""
✅ PROS:
────────
1. Respaldo académico sólido (décadas de investigación)
2. Simplicidad conceptual (fácil de entender)
3. Reglas objetivas (no requiere intuición)
4. Backtesteable (puedes validar antes de arriesgar)
5. Gestión de riesgo integrada (filtros y stops)
6. Funciona en múltiples mercados y períodos


❌ CONTRAS:
───────────
1. Momentum crashes (reversiones bruscas -20 a -30%)
2. Alta rotación (costos de transacción)
3. Solo opera ~60% del tiempo (cuando es BULL)
4. Crowding (estrategia muy popular)
5. Underperformance en mercados laterales
6. Riesgo de concentración (solo 3 posiciones)
7. Desafío psicológico (compras "caro")


💡 VEREDICTO:
─────────────
Long Momentum es una estrategia REAL y PROBADA, pero NO es perfecta.

✅ Úsala si:
   - Tienes capital suficiente ($10K+)
   - Toleras volatilidad (-15 a -25% drawdowns)
   - Entiendes que no opera siempre
   - Tienes disciplina para seguir señales

❌ Evítala si:
   - Necesitas ingresos constantes
   - No toleras volatilidad
   - Capital muy pequeño (<$5K)
   - No puedes monitorear regularmente


🎯 MEJOR ENFOQUE:
─────────────────
Combínala con otras estrategias para crear un portfolio robusto:
- Long Momentum (BULL) + Short Momentum (BEAR)
- Momentum + Mean Reversion (diversificación)
- Momentum + Value (factores complementarios)
    """)
    
    input("\nPresiona Enter para finalizar...")


def main():
    """Ejecutar demo interactivo."""
    print_header("🎓 DEMO INTERACTIVO: Estrategia Long Momentum")
    
    print("""
Este demo te guiará paso a paso para entender:
- Qué es Long Momentum
- Cómo funciona en la práctica
- Pros y contras
- Cómo implementarla en la vida real

Duración: ~10 minutos
    """)
    
    input("Presiona Enter para comenzar...")
    
    # Secciones del demo
    demo_basic_concept()
    demo_regime_filter()
    demo_selection_criteria()
    demo_risk_management()
    
    # Preguntar si quiere ejecutar backtest
    print_section("¿Ejecutar Backtest Real?")
    response = input("¿Quieres ejecutar un backtest con datos reales? (s/n): ")
    if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        run_sample_backtest()
    
    show_implementation_guide()
    show_pros_cons_summary()
    
    print_header("✅ DEMO COMPLETADO")
    print("""
Próximos pasos:

1. Lee la documentación completa:
   $ cat docs/user/estrategia-long-momentum.md

2. Ejecuta backtests con diferentes parámetros:
   $ python scripts/run_backtest.py --strategy long_momentum

3. Prueba en paper trading:
   $ python main.py --mode paper --strategy long_momentum

4. Únete a la comunidad para compartir resultados

¡Buena suerte con tu trading! 🚀
    """)


if __name__ == "__main__":
    main()
