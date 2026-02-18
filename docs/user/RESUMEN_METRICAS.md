# Resumen: Métricas para Comparar Estrategias

## 🎯 Las 5 Métricas MÁS Importantes

### 1. Sharpe Ratio (⭐⭐⭐⭐⭐)
**Qué mide**: Return ajustado por riesgo

**Valores**:
- >2.0 = Excelente
- 1.5-2.0 = Muy bueno
- 1.0-1.5 = Bueno
- <1.0 = Revisar

**Por qué es importante**: Combina rentabilidad Y riesgo en un solo número.

### 2. Sortino Ratio (⭐⭐⭐⭐⭐) - NUEVO
**Qué mide**: Sharpe mejorado (solo penaliza volatilidad negativa)

**Valores**:
- >2.5 = Excelente
- 2.0-2.5 = Muy bueno
- 1.5-2.0 = Bueno
- <1.5 = Revisar

**Por qué es importante**: Más realista que Sharpe porque no penaliza ganancias.

### 3. Max Drawdown (⭐⭐⭐⭐⭐)
**Qué mide**: Pérdida máxima desde el pico

**Valores**:
- <-10% = Excelente
- -10% a -15% = Bueno
- -15% a -20% = Aceptable
- >-20% = Alto riesgo

**Por qué es importante**: Muestra cuánto puedes perder en el peor caso.

### 4. Calmar Ratio (⭐⭐⭐⭐)
**Qué mide**: CAGR / Drawdown

**Valores**:
- >3.0 = Excelente
- 2.0-3.0 = Muy bueno
- 1.0-2.0 = Bueno
- <1.0 = Revisar

**Por qué es importante**: Muestra cuánto ganas por cada % de riesgo.

### 5. Recovery Factor (⭐⭐⭐⭐) - NUEVO
**Qué mide**: Total Return / Drawdown

**Valores**:
- >5.0 = Excelente
- 3.0-5.0 = Muy bueno
- 2.0-3.0 = Bueno
- <2.0 = Revisar

**Por qué es importante**: Muestra qué tan rápido recuperas de pérdidas.

## 📊 Métricas Adicionales Útiles

### Max Consecutive Losses (NUEVO)
- <5 = Excelente
- 5-8 = Bueno
- 8-12 = Aceptable
- >12 = Difícil psicológicamente

### Avg Drawdown Duration (NUEVO)
- <10 días = Excelente
- 10-20 días = Bueno
- 20-40 días = Aceptable
- >40 días = Difícil psicológicamente

### Win Rate
- >60% = Excelente
- 50-60% = Bueno
- 45-50% = Aceptable (si profit factor >1.5)
- <45% = Necesitas profit factor >2.0

### Profit Factor
- >2.0 = Excelente
- 1.5-2.0 = Muy bueno
- 1.2-1.5 = Bueno
- <1.2 = Marginal

## 🏆 Cómo Comparar 2 Estrategias

### Paso 1: Filtro de Viabilidad
Elimina estrategias que NO cumplen:
- Sharpe Ratio >= 1.0
- Max Drawdown >= -25%
- Profit Factor >= 1.2
- Num Trades >= 30

### Paso 2: Compara Métricas Clave

```
Estrategia A vs Estrategia B

Sharpe:    1.85  vs  2.15  → B gana
Sortino:   2.20  vs  2.50  → B gana
Max DD:    -8.2% vs  -4.5% → B gana
Calmar:    2.25  vs  4.78  → B gana
Recovery:  1.85  vs  4.67  → B gana

GANADOR: Estrategia B (mejor en todas las métricas)
```

### Paso 3: Verifica Psicología

¿Puedes soportar el Max Drawdown?
- Estrategia A: -8.2% → Sí
- Estrategia B: -4.5% → Sí

¿Puedes soportar las pérdidas consecutivas?
- Estrategia A: 6 pérdidas → Sí
- Estrategia B: 4 pérdidas → Sí

## ✅ Decisión Final

**Prioriza en este orden**:
1. Sharpe/Sortino Ratio (rentabilidad ajustada por riesgo)
2. Max Drawdown (riesgo máximo)
3. Calmar/Recovery Factor (resiliencia)
4. Verifica que puedas soportar psicológicamente

## 🚀 Cómo Usar

### En el Sistema

1. Corre múltiples backtests
2. Ve a "Compare Runs" en la UI
3. Selecciona 2-4 estrategias
4. Revisa las 4 tabs:
   - Returns
   - Risk
   - Risk-Adjusted (MÁS IMPORTANTE)
   - Trading

### En Scripts

```bash
# Prueba las nuevas métricas
uv run python scripts/test_new_metrics.py
```

## 📚 Documentación Completa

Para más detalles, lee:
- `docs/user/metricas-comparacion-estrategias.md` - Guía completa
- `docs/user/costos-trading-reales.md` - Costos por broker
- `docs/user/libertex-metatrader-guide.md` - Guía de Libertex

## Fecha
2026-02-13
