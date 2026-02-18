# Libertex: Niveles de Riesgo para Momentum Strategy 📊

## Resumen Ejecutivo

Probamos la estrategia Long Momentum con **$1,000 iniciales** en Libertex usando **acciones fraccionarias** y tres niveles de exposición al capital:

- **50% del capital** (conservador)
- **70% del capital** (moderado)  
- **90% del capital** (agresivo)

**Período:** 2021-2025 (4.08 años)  
**Rebalanceo:** Semanal (7 días)

---

## 🏆 Resultados Comparativos

### 1. Nivel Conservador (50% del capital)

```
Capital Final:     $1,396.10
Retorno Total:     +39.61%
Retorno Anual:     8.51%
Sharpe Ratio:      0.47
Max Drawdown:      -27.78%
Trades:            2
Comisiones:        $2.00
```

**Posiciones:**
- IWM (Russell 2000): 2.38 acciones
- USO (Oil ETF): 11.05 acciones

✅ **Mejor rendimiento ajustado por riesgo**

### 2. Nivel Moderado (70% del capital)

```
Capital Final:     $1,044.40
Retorno Total:     +4.44%
Retorno Anual:     1.07%
Sharpe Ratio:      0.15
Max Drawdown:      -22.95%
Win Rate:          0%
Trades:            1
Comisiones:        $1.00
```

**Posiciones:**
- IWM (Russell 2000): 3.33 acciones

⚠️ **Rendimiento muy bajo**

### 3. Nivel Agresivo (90% del capital)

```
Capital Final:     $1,057.37
Retorno Total:     +5.74%
Retorno Anual:     1.37%
Sharpe Ratio:      0.17
Max Drawdown:      -29.00%
Win Rate:          0%
Trades:            1
Comisiones:        $1.00
```

**Posiciones:**
- IWM (Russell 2000): 4.29 acciones

⚠️ **Mayor riesgo sin recompensa proporcional**

---

## 📈 Análisis Detallado

### ¿Por qué 50% ganó por tanto margen?

**Diversificación:**
- 50% hizo **2 trades** (IWM + USO)
- 70% y 90% solo hicieron **1 trade** (IWM)

**Rotación activa:**
- Con 50% del capital, el sistema tuvo más flexibilidad para rotar entre activos
- Capturó momentum en commodities (USO) además de small caps (IWM)

**Menor concentración:**
- 70% y 90% quedaron "atrapados" en una sola posición
- No pudieron aprovechar otras oportunidades de momentum

### El Problema de la Sobre-Exposición

Cuando usas 70-90% del capital:
1. **Menos liquidez** para nuevas oportunidades
2. **Menor diversificación** (1 activo vs 2)
3. **Mayor riesgo de concentración**
4. **Drawdowns similares** pero sin mayor retorno

---

## 🎯 Recomendación para Libertex

### Para $1,000 iniciales:

**Usa 50% del capital (conservador)**

**Ventajas:**
- ✅ Mejor Sharpe Ratio (0.47 vs 0.15-0.17)
- ✅ Mayor diversificación (2 activos)
- ✅ Más flexibilidad para rotar
- ✅ Retorno anual 8.51% (vs 1-1.4%)
- ✅ Drawdown controlado (-27.78%)

**Configuración recomendada:**
```python
initial_capital = 1000
risk_budget = 0.50  # 50% del capital
rebalance_days = 7  # Semanal
```

---

## 💡 Insights Clave

### 1. Más capital ≠ Mejor rendimiento

En momentum, **la flexibilidad importa más que la exposición**:
- 50% del capital → 2 trades → +39.61%
- 90% del capital → 1 trade → +5.74%

### 2. Diversificación en cuentas pequeñas

Con $1,000, las acciones fraccionarias de Libertex permiten:
- Diversificar entre 2-3 activos
- Mantener liquidez para rotación
- Reducir riesgo de concentración

### 3. Rebalanceo semanal funciona

7 días es suficiente para:
- Capturar cambios de momentum
- No sobre-operar (solo 1-2 trades)
- Minimizar comisiones ($1-2 total)

---

## 📊 Comparación Visual

```
Retorno Anual:
50%: ████████▌ 8.51%
70%: █ 1.07%
90%: █▌ 1.37%

Sharpe Ratio (riesgo-ajustado):
50%: ████▋ 0.47
70%: █▌ 0.15
90%: █▋ 0.17

Número de Trades:
50%: ██ 2 trades
70%: █ 1 trade
90%: █ 1 trade
```

---

## 🚀 Plan de Acción

### Fase 1: Arranque ($1,000)
- **Risk Budget:** 50%
- **Rebalanceo:** Semanal (7 días)
- **Objetivo:** Crecer a $1,500-2,000

### Fase 2: Crecimiento ($2,000+)
- **Risk Budget:** 60%
- **Rebalanceo:** Semanal
- **Objetivo:** Mantener diversificación

### Fase 3: Consolidación ($5,000+)
- **Risk Budget:** 70%
- **Rebalanceo:** Bi-semanal (14 días)
- **Objetivo:** Optimizar costos

---

## ⚠️ Advertencias

### No uses 90% del capital si:
- Tienes menos de $5,000
- Necesitas flexibilidad para rotar
- Quieres diversificar entre 2+ activos

### Usa 50% del capital si:
- Estás empezando ($1,000-2,000)
- Quieres mejor Sharpe Ratio
- Prefieres menor concentración

---

## 🔧 Implementación en Libertex

### Paso 1: Configurar la estrategia

```python
from src.auronai.strategies.long_momentum import LongMomentumStrategy

strategy = LongMomentumStrategy(
    lookback_period=90,      # 3 meses de momentum
    rebalance_days=7,        # Semanal
    risk_budget=0.50,        # 50% del capital
    max_positions=3          # Hasta 3 activos
)
```

### Paso 2: Ejecutar backtest

```bash
python scripts/test_momentum_libertex.py
```

### Paso 3: Revisar resultados

```bash
cat results/momentum_libertex_risk_levels.json
```

---

## 📚 Recursos Relacionados

- [Estrategia Long Momentum Explicada](estrategia-long-momentum.md)
- [Guía Libertex + MetaTrader](libertex-metatrader-guide.md)
- [Plan de Crecimiento $1,000 Inicial](plan-crecimiento-1000-inicial.md)
- [Todas las Estrategias para $1,000](todas-las-estrategias-1000-dolares.md)

---

## 🎓 Conclusión

Para cuentas pequeñas en Libertex ($1,000-2,000):

**50% del capital es óptimo** porque:
1. Permite diversificar entre 2-3 activos
2. Mantiene liquidez para rotación
3. Mejor rendimiento ajustado por riesgo (Sharpe 0.47)
4. Retorno anual superior (8.51% vs 1-1.4%)

**No caigas en la trampa** de usar 90% del capital pensando que más exposición = más ganancia. En momentum, **la flexibilidad y diversificación importan más**.

---

*Última actualización: Febrero 2026*  
*Basado en backtest real 2021-2025*
