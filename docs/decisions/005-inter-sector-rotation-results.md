# ADR-005: Inter-Sector Rotation Results (Multi-Asset V2)

## Estado
Rechazado - Los sectores no-tech empeoran el performance

## Fecha
2026-02-13

## Contexto

Después del éxito de Multi-Asset V1 (tech stocks + tech ETFs), se implementó la Fase 2 de expansión multi-activo para lograr rotación inter-sectorial completa y reducir dependencia del Nasdaq.

### Hipótesis
Si la diversificación con tech ETFs mejoró el performance, agregar sectores no-tech (energía, finanzas, healthcare, industriales, consumo, utilities, bonos) debería:
1. Reducir correlación con Nasdaq
2. Mejorar Sharpe ratio por diversificación
3. Proteger en mercados bajistas
4. Mantener o mejorar returns

### Universo Expandido (22 símbolos)
- 10 acciones tech (baseline)
- 5 ETFs tech (Fase 1)
- 7 ETFs sectores no-tech + bonos (Fase 2):
  - XLE (Energy)
  - XLF (Financials)
  - XLV (Healthcare)
  - XLI (Industrials)
  - XLP (Consumer Staples)
  - XLU (Utilities)
  - TLT (20+ Year Treasury Bonds)

## Resultados

### Performance Comparison

**Período**: 2024-01-01 a 2026-01-31 (test desde 2025-07-01)

| Métrica | V1 (Tech Only) | V2 (Inter-Sector) | Cambio |
|---------|----------------|-------------------|--------|
| Return | 7.61% | 3.61% | -53% ❌ |
| CAGR | 13.30% | 6.23% | -53% ❌ |
| Sharpe | 1.27 | 0.62 | -51% ❌ |
| Max DD | 2.88% | 3.95% | +37% ❌ |
| Win Rate | 57.14% | 54.78% | -4% ❌ |
| Expectancy | 0.47% | 0.22% | -53% ❌ |
| Trades | 112 | 115 | +3 |

### Performance por Tipo de Activo (V2)

| Categoría | Trades | Win Rate | Avg P&L | Contribución |
|-----------|--------|----------|---------|--------------|
| Tech Stocks | 280 (68%) | 56.4% | +0.42% | ✅ Positiva |
| Tech ETFs | 58 (14%) | 62.1% | +0.54% | ✅ Positiva |
| Sector ETFs | 67 (16%) | 44.8% | -0.12% | ❌ Negativa |
| Bonds (TLT) | 9 (2%) | 22.2% | -0.64% | ❌❌ Muy negativa |

### Análisis Detallado

**Tech Assets (stocks + ETFs):**
- 338 trades (82% del total)
- 57.4% win rate promedio
- +0.44% avg P&L
- Comportamiento consistente con V1

**Non-Tech Sectors:**
- 67 trades (16% del total)
- 44.8% win rate (BAJO)
- -0.12% avg P&L (NEGATIVO)
- Arrastrando performance hacia abajo

**Bonds (TLT):**
- 9 trades (2% del total)
- 22.2% win rate (MUY BAJO)
- -0.64% avg P&L (MUY NEGATIVO)
- Peor categoría por mucho

## Decisión

**RECHAZAR** la estrategia Multi-Asset V2 (inter-sector rotation).

**MANTENER** Multi-Asset V1 (tech-focused) como estrategia principal.

### Razones:

1. **Performance significativamente peor**: -53% en return y Sharpe
2. **Sectores no-tech tienen win rate negativo**: 44.8% WR, -0.12% avg P&L
3. **Bonos completamente inefectivos**: 22.2% WR, -0.64% avg P&L
4. **No hay beneficio de diversificación**: Mayor DD (3.95% vs 2.88%)
5. **La estrategia baseline NO funciona fuera de tech**: Relative strength vs QQQ favorece tech

## Consecuencias

### Positivas
- Aprendizaje valioso: La estrategia baseline está optimizada para tech
- Confirmación de que tech-focus es correcto para este sistema
- Evitamos implementar algo que empeora performance

### Negativas
- No logramos reducir dependencia del Nasdaq
- No logramos diversificación efectiva
- Seguimos expuestos a riesgo de sector tech

## Alternativas Consideradas

### 1. Ajustar filtros por sector
**Idea**: Usar diferentes filtros para sectores no-tech (ej: no usar QQQ como benchmark para XLE)

**Por qué no**: Complejidad alta, y los resultados sugieren que el problema es fundamental, no de filtros

### 2. Solo agregar sectores defensivos en mercado bajista
**Idea**: Usar XLP, XLU, TLT solo cuando market regime = False

**Por qué no**: TLT tuvo 22% WR incluso en período completo, no hay evidencia de que funcione defensivamente

### 3. Agregar más tech ETFs en lugar de sectores
**Idea**: Expandir con QQQ, VGT, FTEC en lugar de sectores no-tech

**Por qué considerarla**: Tech ETFs tuvieron 62% WR en V2, mejor que stocks (56%)

**Estado**: Propuesta para futura evaluación

## Lecciones Aprendidas

1. **La estrategia baseline está diseñada para tech**: Relative strength vs QQQ naturalmente favorece tech
2. **Diversificación no siempre mejora**: Agregar activos con mal performance empeora el resultado
3. **Bonos no funcionan con esta estrategia**: TLT requiere estrategia diferente (mean reversion, no momentum)
4. **Win rate < 50% es inaceptable**: Sectores no-tech no cumplen criterio mínimo
5. **Tech-focus no es un bug, es una feature**: El sistema funciona mejor especializado

## Próximos Pasos

1. ✅ Documentar resultados en este ADR
2. ✅ Mantener V1 como estrategia principal
3. ⏳ Evaluar agregar más tech ETFs (QQQ, VGT, FTEC)
4. ⏳ Considerar estrategia separada para sectores defensivos (diferente lógica)
5. ⏳ Investigar por qué tech ETFs (62% WR) superan tech stocks (56% WR)

## Referencias

- ADR-004: Multi-Asset Expansion Results (V1)
- `src/auronai/backtesting/swing_multi_asset_v2.py`
- `scripts/run_swing_multi_asset_v2.py`
- `results/swing_multi_asset_v2_results.json`

## Archivos Relacionados

### Mantenidos (para referencia)
- `src/auronai/backtesting/swing_multi_asset_v2.py` - Estrategia V2 (no usar en producción)
- `scripts/run_swing_multi_asset_v2.py` - Script de backtest V2
- `results/swing_multi_asset_v2_*` - Resultados V2

### Estrategia Principal
- `src/auronai/backtesting/swing_multi_asset_v1.py` - USAR ESTA
- `scripts/run_swing_multi_asset_v1.py`
- `results/swing_multi_asset_v1_*`
