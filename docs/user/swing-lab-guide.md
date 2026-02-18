# Guía del Swing Strategy Lab

## 📈 Introducción

El **Swing Strategy Lab** es un laboratorio visual para desarrollo y prueba de estrategias cuantitativas de trading. Te permite:

- Ejecutar backtests con diferentes estrategias
- Visualizar resultados de forma interactiva
- Comparar múltiples estrategias lado a lado
- Analizar rendimiento por régimen de mercado

## 🚀 Inicio Rápido

### 1. Lanzar la Aplicación

```bash
# Desde la raíz del proyecto
./scripts/run_streamlit_app.sh
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

### 2. Ejecutar tu Primer Backtest

1. Ve a la página **"🚀 Run Backtest"**
2. Selecciona una estrategia (recomendado: Long Momentum)
3. Configura los parámetros:
   - Top K: 3 símbolos
   - Holding Period: 10 días
4. Selecciona el rango de fechas (último año por defecto)
5. Haz clic en **"▶️ Run Backtest"**

### 3. Ver Resultados

1. Ve a **"📊 View Results"**
2. Revisa las métricas clave
3. Analiza la curva de equity
4. Explora los trades individuales

## 📚 Estrategias Disponibles

### Long Momentum Strategy

**Cuándo usar:** Mercados alcistas (bull markets)

**Cómo funciona:**
- Identifica los símbolos con mejor momentum relativo
- Compra los top K símbolos más fuertes
- Mantiene posiciones por N días
- Solo opera cuando el régimen es BULL

**Parámetros:**
- `top_k`: Número de símbolos a comprar (recomendado: 2-5)
- `holding_days`: Días de tenencia (recomendado: 7-14)

**Filtros aplicados:**
- EMA20 > EMA50 (tendencia alcista)
- RSI < 70 (no sobrecomprado)
- Relative Strength positivo vs benchmark

### Short Momentum Strategy

**Cuándo usar:** Mercados bajistas (bear markets)

**Cómo funciona:**
- Identifica los símbolos más débiles
- Vende en corto los bottom K símbolos
- Mantiene posiciones por N días
- Solo opera cuando el régimen es BEAR

**Parámetros:**
- `top_k`: Número de símbolos a shortear (recomendado: 2-3)
- `holding_days`: Días de tenencia (recomendado: 5-10)

**Filtros aplicados:**
- EMA20 < EMA50 (tendencia bajista)
- RSI > 30 (no sobrevendido)
- Relative Strength negativo vs benchmark

### Neutral Strategy

**Cuándo usar:** Mercados laterales o inciertos

**Cómo funciona:**
- Busca símbolos de baja volatilidad
- Posiciones defensivas con menor exposición (5% vs 20%)
- Prefiere símbolos con RS positivo pero ATR bajo
- Solo opera cuando el régimen es NEUTRAL

**Parámetros:**
- `top_k`: Número de símbolos (recomendado: 2-3)
- `holding_days`: Días de tenencia (recomendado: 14-21)

**Filtros aplicados:**
- ATR bajo (baja volatilidad)
- Relative Strength positivo
- Exposición reducida al 5%

## 🎯 Detección de Régimen

El sistema detecta automáticamente el régimen de mercado usando el benchmark (SPY/QQQ):

- **BULL**: EMA200 con pendiente positiva → Activa Long Momentum
- **BEAR**: EMA200 con pendiente negativa → Activa Short Momentum  
- **NEUTRAL**: EMA200 plana → Activa Neutral Strategy

Cada estrategia solo opera en su régimen correspondiente, lo que mejora la robustez.

## 📊 Métricas Explicadas

### Métricas de Retorno

- **Total Return**: Retorno total del período (%)
- **CAGR**: Tasa de crecimiento anual compuesta (%)
- **Final Equity**: Capital final en dólares

### Métricas de Riesgo

- **Sharpe Ratio**: Retorno ajustado por riesgo (>1 es bueno, >2 es excelente)
- **Max Drawdown**: Máxima caída desde un pico (%)
- **Calmar Ratio**: CAGR / |Max Drawdown| (>1 es bueno)
- **Volatility**: Volatilidad anualizada (%)

### Métricas de Trading

- **Win Rate**: Porcentaje de trades ganadores (%)
- **Profit Factor**: Ganancias totales / Pérdidas totales (>1.5 es bueno)
- **Expectancy**: Ganancia promedio por trade ($)
- **Num Trades**: Número total de trades ejecutados

## 🔍 Comparación de Estrategias

### Cómo Comparar

1. Ve a **"🔍 Compare Runs"**
2. Selecciona 2-4 runs del dropdown
3. Revisa la tabla comparativa
4. Analiza las curvas de equity superpuestas

### Qué Buscar

- **Consistencia**: Estrategias con menor drawdown
- **Risk-Adjusted Returns**: Mayor Sharpe Ratio
- **Robustez**: Buen rendimiento en diferentes períodos
- **Complementariedad**: Estrategias que funcionan en diferentes regímenes

### Ejemplo de Análisis

```
Long Momentum:  +65% return, Sharpe 1.71, MaxDD -4.4%
Short Momentum: -25% return, Sharpe -1.30, MaxDD -25%
Neutral:        +14% return, Sharpe 1.69, MaxDD -1.7%
```

**Interpretación:**
- Long Momentum excelente en mercado alcista
- Short Momentum perdió (esperado en bull market)
- Neutral ofreció retornos estables con bajo riesgo

**Recomendación:** Combinar Long + Neutral para balance riesgo/retorno

## ⚙️ Configuración Avanzada

### Universo de Símbolos

**Recomendaciones:**
- **Mínimo**: 5-10 símbolos para diversificación
- **Óptimo**: 10-20 símbolos para balance
- **Máximo**: 30-50 símbolos (más lento)

**Sectores sugeridos:**
- Tech: AAPL, MSFT, GOOGL, NVDA, AMD
- Finance: JPM, BAC, GS, MS
- Consumer: AMZN, TSLA, NKE, SBUX
- Healthcare: JNJ, UNH, PFE, ABBV

### Parámetros de Estrategia

**Top K:**
- Bajo (1-2): Mayor concentración, mayor riesgo
- Medio (3-5): Balance óptimo
- Alto (6-10): Mayor diversificación, menor retorno

**Holding Days:**
- Corto (1-5): Trading activo, más comisiones
- Medio (7-14): Swing trading óptimo
- Largo (15-30): Posiciones más estables

### Capital Inicial

- **$10,000**: Mínimo para diversificación básica
- **$100,000**: Óptimo para backtesting realista
- **$1,000,000+**: Para institucionales

## 💡 Tips y Mejores Prácticas

### Para Mejores Resultados

1. **Usa datos de al menos 1 año** para capturar diferentes condiciones
2. **Compara múltiples períodos** (2022 bear, 2023 recovery, 2024 bull)
3. **Ajusta parámetros gradualmente** (no optimices en exceso)
4. **Considera comisiones** (0.1% por defecto es realista)
5. **Valida en out-of-sample** (prueba en datos no usados para optimizar)

### Errores Comunes a Evitar

❌ **Overfitting**: Optimizar demasiado en un período específico
❌ **Look-ahead bias**: Usar información futura en decisiones
❌ **Survivorship bias**: Solo probar con símbolos que sobrevivieron
❌ **Ignorar costos**: No considerar comisiones y slippage
❌ **Tamaño de muestra pequeño**: Pocos trades = resultados no confiables

### Workflow Recomendado

1. **Exploración**: Prueba diferentes estrategias con parámetros por defecto
2. **Análisis**: Identifica qué funciona y por qué
3. **Refinamiento**: Ajusta parámetros basándote en el análisis
4. **Validación**: Prueba en diferentes períodos
5. **Comparación**: Compara las mejores variantes
6. **Decisión**: Selecciona la estrategia más robusta

## 🐛 Troubleshooting

### La aplicación no inicia

```bash
# Verifica que Streamlit esté instalado
pip install streamlit plotly

# Verifica el puerto
lsof -i :8501  # macOS/Linux
netstat -ano | findstr :8501  # Windows
```

### Backtest muy lento

- Reduce el rango de fechas
- Usa menos símbolos
- Verifica que los datos estén en cache (`data/cache/`)

### No se muestran resultados

- Verifica que `data/runs.db` existe
- Ejecuta un backtest primero
- Revisa los logs en la terminal

### Errores de datos

```bash
# Limpia el cache si hay problemas
rm -rf data/cache/ohlcv/*
rm -rf data/cache/features/*
```

## 📖 Recursos Adicionales

- [Documentación Técnica](../technical/swing-lab-architecture.md)
- [Decisiones de Arquitectura](../decisions/)
- [Ejemplos de Uso](../../examples/)
- [Tests End-to-End](../../scripts/test_backtest_end_to_end.py)

## 🆘 Soporte

Si encuentras problemas:

1. Revisa esta guía y el troubleshooting
2. Consulta los logs en la terminal
3. Revisa los issues en GitHub
4. Crea un nuevo issue con detalles del error

---

**¡Feliz trading cuantitativo! 📈🚀**
