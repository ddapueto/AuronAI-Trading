# Estrategia Swing Baseline Mejorada

## Descripción

La estrategia swing "baseline mejorada" es una estrategia de trading que combina:

1. **Market Regime Filter**: Usa QQQ para determinar si el mercado está en modo alcista o defensivo
2. **Risk Budget Dinámico**: Ajusta el capital en riesgo según condiciones de mercado
3. **Kill Switch por Drawdown**: Protección automática cuando las pérdidas exceden umbrales
4. **Selección por Fuerza Relativa**: Elige los mejores símbolos basándose en performance relativa
5. **Gestión de Salidas**: TP fijo 5%, SL por ATR, holding máximo 10 días

## Características Principales

### 1. Market Regime Filter (QQQ)

Determina si el mercado está en modo alcista o defensivo usando tres condiciones:

- **EMA200**: QQQ_close > EMA200
- **Slope20**: EMA200[t] - EMA200[t-20] > 0 (tendencia alcista)
- **ADX**: ADX >= 15 (tendencia definida)

Si las tres condiciones se cumplen → `market_ok = True` (modo normal)
Si alguna falla → `market_ok = False` (modo defensivo)

### 2. Risk Budget Dinámico

El capital en riesgo se ajusta según:

| Condición | Risk Budget |
|-----------|-------------|
| Market OK | 20% |
| Market Defensivo | 5% |
| Drawdown >= 5% | Cap a 10% |
| Drawdown >= 8% | Cap a 5% |
| Drawdown >= 10% | 0% + Cooldown 10 días |

### 3. Kill Switch por Drawdown

Protección automática en tres niveles:

- **5% DD**: Reduce risk budget a máximo 10%
- **8% DD**: Reduce risk budget a máximo 5%
- **10% DD**: PAUSA completa por 10 días (cooldown)

Durante el cooldown no se abren nuevas posiciones.

### 4. Selección por Fuerza Relativa

Cada día se calcula:

```
rs_score[symbol] = return_20d(symbol) - return_20d(QQQ)
```

Se seleccionan los **top 3 símbolos** con mayor rs_score.

El capital se distribuye equitativamente:
```
allocation_per_symbol = risk_budget / num_selected
```

### 5. Reglas de Entrada y Salida

#### Entrada
- **Convención**: Abrir al OPEN del día t+1 usando señal del cierre del día t
- **TP**: entry_price * 1.05 (5% fijo)
- **SL**: entry_price - 1.5 * ATR(14)
- **Holding máximo**: 10 días

#### Salida (Simulación día a día)

Reglas conservadoras usando OHLC:

1. Si `low <= SL` y `high >= TP` en el mismo día → Asumir **SL primero** (conservador)
2. Else si `low <= SL` → Salir en **SL**
3. Else si `high >= TP` → Salir en **TP**
4. Si no toca TP ni SL hasta día 10 → Salir en **Close** (TimeExit)

## Uso

### Ejecutar Backtest Simple

```bash
python scripts/run_swing_baseline_backtest.py
```

Este script ejecuta el backtest con la configuración por defecto:
- Símbolos: AAPL, TSLA, MSFT, NVDA, GOOGL
- Benchmark: QQQ
- Período completo: 2024-01-01 a 2026-01-31
- Período de test: 2025-07-01 a 2026-01-31
- Capital inicial: $1,000

### Comparar Con y Sin Protecciones

```bash
python scripts/compare_baseline_strategies.py
```

Este script compara:
1. **Baseline sin protecciones**: Siempre 20% risk budget, siempre las 5 acciones
2. **Baseline mejorada**: Con todas las protecciones activadas

## Resultados

Los scripts generan:

### 1. Archivos JSON
- `results/swing_baseline_results.json`: Resultados completos del backtest
- `results/baseline_no_protection.json`: Resultados sin protecciones
- `results/baseline_with_protection.json`: Resultados con protecciones

### 2. Archivos CSV
- `results/swing_baseline_trades.csv`: Tabla de todos los trades

### 3. Gráficos
- `results/equity_curve.png`: Curva de equity
- `results/comparison_equity_curves.png`: Comparación de estrategias

## Métricas Reportadas

### Performance
- **Total Return**: Retorno total en el período de test
- **CAGR**: Compound Annual Growth Rate
- **Number of Trades**: Número total de trades ejecutados

### Calidad
- **Win Rate**: Porcentaje de trades ganadores
- **Avg Winner**: Ganancia promedio en trades ganadores
- **Avg Loser**: Pérdida promedio en trades perdedores
- **Profit Factor**: Total wins / Total losses

### Riesgo
- **Max Drawdown**: Máxima caída desde peak
- **Exposure**: Porcentaje de días con capital en mercado

## Ejemplo de Salida

```
📊 MÉTRICAS DE PERFORMANCE (Test Period)
============================================================
Total Return:           45.23%
CAGR:                   67.89%
Number of Trades:          42
Win Rate:               57.14%
Avg Winner:              8.45%
Avg Loser:              -3.21%
Profit Factor:           2.34
Max Drawdown:            8.76%
Exposure:               65.43%
============================================================
```

## Personalización

Puedes modificar los parámetros en el código:

```python
strategy = SwingBaselineStrategy(
    symbols=['AAPL', 'TSLA', 'MSFT', 'NVDA', 'GOOGL'],
    benchmark='QQQ',
    initial_capital=1000.0,
    base_risk_budget=0.20,        # 20% normal
    defensive_risk_budget=0.05,   # 5% defensivo
    top_k=3,                      # Top 3 símbolos
    tp_multiplier=1.05,           # TP 5%
    sl_atr_multiplier=1.5,        # SL 1.5x ATR
    max_holding_days=10,          # Máximo 10 días
    dd_threshold_1=0.05,          # 5% DD
    dd_threshold_2=0.08,          # 8% DD
    dd_threshold_3=0.10,          # 10% DD
    cooldown_days=10              # 10 días cooldown
)
```

## Notas Importantes

### Convención de Datos
- Se usa **Adj Close** para cálculos de returns y señales
- Se usa **OHLC no ajustado** para simulación intradía de TP/SL
- Esto es consistente y evita lookahead bias

### Prevención de Lookahead Bias
- Las señales se calculan en el cierre del día t
- Las entradas se ejecutan en el open del día t+1
- No se usan datos futuros para decisiones

### Limitaciones
- No incluye costos de transacción (comisiones, slippage)
- Asume ejecución perfecta en TP/SL
- No considera gaps overnight
- No incluye dividendos

## Próximos Pasos

Para mejorar la estrategia considera:

1. **Agregar costos de transacción**: Comisiones y slippage realistas
2. **Optimizar parámetros**: Grid search para TP, SL, holding period
3. **Agregar filtros adicionales**: Volatilidad, volumen, sector rotation
4. **Walk-forward analysis**: Validar robustez en diferentes períodos
5. **Monte Carlo simulation**: Evaluar distribución de resultados

## Referencias

- [Market Regime Detection](../technical/indicator-combinations-research.md)
- [Risk Management](../technical/future-enhancements.md)
- [Backtesting Best Practices](../technical/candlestick-data-flow.md)
