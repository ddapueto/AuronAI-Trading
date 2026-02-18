# ADR-003: Swing Baseline Strategy Design

## Estado
Aceptado

## Contexto

Se necesitaba implementar una estrategia swing "baseline mejorada" para backtesting que:
- Use market regime filters para adaptarse a condiciones de mercado
- Implemente protecciones automáticas contra drawdowns
- Seleccione símbolos por fuerza relativa
- Gestione salidas con TP/SL y holding máximo

El objetivo era crear una estrategia robusta que pueda compararse con una baseline sin protecciones para evaluar el valor de los filtros y protecciones.

## Decisión

Implementar `SwingBaselineStrategy` como clase independiente en `src/auronai/backtesting/` con las siguientes características:

### 1. Market Regime Filter (QQQ)
- EMA200 + slope20 + ADX para determinar market_ok
- Risk budget dinámico: 20% normal, 5% defensivo

### 2. Kill Switch por Drawdown
- 3 niveles: 5%, 8%, 10%
- Cooldown de 10 días en nivel 3

### 3. Selección por Fuerza Relativa
- rs_score = return_20d(symbol) - return_20d(QQQ)
- Top K símbolos (default: 3)

### 4. Gestión de Salidas
- TP fijo: 5%
- SL dinámico: 1.5x ATR
- Holding máximo: 10 días
- Regla conservadora: si toca SL y TP el mismo día, asumir SL primero

### 5. Convención de Entrada
- Señal calculada en cierre del día t
- Entrada en open del día t+1 (evita lookahead bias)

## Consecuencias

### Positivas
- Estrategia modular y reutilizable
- Fácil de comparar con baseline sin protecciones
- Previene lookahead bias con convención de entrada clara
- Protecciones automáticas contra drawdowns excesivos
- Adaptación a condiciones de mercado

### Negativas
- Requiere datos históricos completos (warmup period)
- No incluye costos de transacción (simplificación)
- Asume ejecución perfecta en TP/SL
- No considera gaps overnight

## Alternativas Consideradas

### 1. Integrar en BacktestEngine existente
**Por qué no:** BacktestEngine es más genérico y orientado a estrategias de señales. Esta estrategia swing tiene lógica específica de portfolio management y market regime que justifica una clase separada.

### 2. Usar ML para selección de símbolos
**Por qué no:** Para baseline, queremos algo simple y explicable. Fuerza relativa es transparente y efectivo. ML puede agregarse después como mejora.

### 3. TP/SL dinámicos basados en volatilidad
**Por qué no:** Para baseline, TP fijo es más simple y predecible. SL ya es dinámico con ATR. Podemos agregar TP dinámico en versiones futuras.

## Implementación

Archivos creados:
- `src/auronai/backtesting/swing_baseline_strategy.py` - Estrategia principal
- `scripts/run_swing_baseline_backtest.py` - Script de ejecución
- `scripts/compare_baseline_strategies.py` - Comparación con/sin protecciones
- `scripts/test_swing_baseline_quick.py` - Prueba rápida
- `docs/user/swing-baseline-strategy.md` - Documentación de usuario

## Referencias

- [Candlestick Data Flow](../technical/candlestick-data-flow.md)
- [Indicator Combinations Research](../technical/indicator-combinations-research.md)
- [Future Enhancements](../technical/future-enhancements.md)
