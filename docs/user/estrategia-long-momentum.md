# Estrategia Long Momentum - Guía Completa

## ¿Es Real y Aplicable?

**SÍ, la estrategia Long Momentum es 100% real y ampliamente utilizada en la vida real.** Es una de las estrategias más estudiadas y documentadas en finanzas cuantitativas.

### Evidencia Académica y Profesional

1. **Investigación Académica**
   - Jegadeesh y Titman (1993): "Returns to Buying Winners and Selling Losers" - Paper seminal que demostró la persistencia del momentum
   - Carhart (1997): Incluyó momentum como el 4º factor en su modelo de 4 factores
   - Asness, Moskowitz y Pedersen (2013): Documentaron momentum en múltiples clases de activos

2. **Uso Institucional**
   - AQR Capital Management: Gestiona miles de millones usando estrategias momentum
   - Dimensional Fund Advisors: Ofrece fondos basados en momentum
   - Muchos hedge funds cuantitativos usan variantes de momentum

3. **ETFs Comerciales**
   - MTUM (iShares MSCI USA Momentum Factor ETF): $15B+ en activos
   - PDP (Invesco DWA Momentum ETF): $1B+ en activos
   - SPMO (Invesco S&P 500 Momentum ETF)

## ¿Cómo Funciona en AuronAI?

### Implementación Técnica

```python
# Criterios de Selección
1. Filtro de Régimen: Solo opera en mercados BULL
   - Precio > EMA200 del benchmark (QQQ)
   - EMA200 con pendiente positiva

2. Filtro de Candidatos:
   - EMA20 > EMA50 (tendencia alcista de corto plazo)
   - RSI < 70 (no sobrecomprado)
   - Relative Strength positivo vs benchmark

3. Selección:
   - Top K símbolos por Relative Strength (default: 3)
   - Peso igual entre seleccionados

4. Gestión de Riesgo:
   - Exposición máxima: 20% del portfolio
   - Máximo por posición: 20% / K = 6.67% (para K=3)
```

### Parámetros Configurables

```python
StrategyParams(
    top_k=3,                    # Número de posiciones
    holding_days=10,            # Período de tenencia objetivo
    tp_multiplier=1.05,         # Take profit: +5%
    risk_budget=0.20,           # 20% exposición máxima
    defensive_risk_budget=0.05  # 5% en regímenes defensivos
)
```

## Cómo Aplicarla en la Vida Real

### Paso 1: Configuración Inicial

**Capital Recomendado**: Mínimo $10,000 USD
- Con menos capital, las comisiones erosionan las ganancias
- Necesitas diversificar en al menos 3 símbolos

**Broker Requerido**:
- Acceso a mercado US (NYSE, NASDAQ)
- Comisiones bajas (idealmente $0 por trade)
- Ejecución rápida
- Ejemplos: Interactive Brokers, TD Ameritrade, Alpaca

### Paso 2: Implementación Práctica

#### Opción A: Manual (Recomendado para Principiantes)

```
1. Cada semana (lunes por la mañana):
   - Verificar régimen de mercado (QQQ > EMA200?)
   - Si NO es BULL → No operar, mantener cash
   
2. Si es BULL:
   - Calcular Relative Strength de tu universo de símbolos
   - Filtrar: EMA20 > EMA50 y RSI < 70
   - Seleccionar top 3 por Relative Strength
   
3. Rebalancear portfolio:
   - Vender posiciones que ya no están en top 3
   - Comprar nuevas posiciones
   - Peso igual: 6.67% del portfolio por símbolo
   
4. Gestión de posiciones:
   - Take profit: +5% (vender)
   - Time exit: 10 días (vender si no alcanzó TP)
   - Trend reversal: EMA20 cruza bajo EMA50 (vender)
```

#### Opción B: Semi-Automatizada (AuronAI + Ejecución Manual)

```bash
# 1. Ejecutar backtest para validar
python scripts/run_backtest.py --strategy long_momentum

# 2. Generar señales actuales
python main.py --mode signals --strategy long_momentum

# 3. Revisar señales y ejecutar manualmente en tu broker
```

#### Opción C: Totalmente Automatizada (Avanzado)

```python
# Requiere integración con broker API (Alpaca, Interactive Brokers)
# Ver docs/technical/live-trading-integration.md
```

### Paso 3: Monitoreo y Ajustes

**Frecuencia de Revisión**: Semanal
- Lunes: Rebalanceo principal
- Diario: Verificar stops y take profits

**Métricas a Monitorear**:
- Win rate (objetivo: >50%)
- Profit factor (objetivo: >1.5)
- Max drawdown (límite: -15%)
- Sharpe ratio (objetivo: >1.0)

## Pros y Contras

### ✅ PROS

#### 1. Respaldo Académico Sólido
- Décadas de investigación confirman la anomalía del momentum
- Funciona en múltiples mercados y períodos temporales
- Explicación conductual: Herding behavior, under-reaction

#### 2. Simplicidad Conceptual
- Fácil de entender: "Compra lo que sube"
- Reglas claras y objetivas
- No requiere predicción del futuro

#### 3. Diversificación Temporal
- Funciona en diferentes ciclos de mercado (dentro de BULL)
- Complementa estrategias value (que son contrarias)

#### 4. Gestión de Riesgo Integrada
- Solo opera en mercados alcistas (filtro de régimen)
- Stops automáticos (trend reversal)
- Exposición limitada (20% máximo)

#### 5. Backtesteable
- Reglas objetivas permiten backtesting riguroso
- Puedes validar antes de arriesgar capital real

#### 6. Escalable
- Funciona con diferentes tamaños de capital
- Aplicable a diferentes universos de símbolos

### ❌ CONTRAS

#### 1. Momentum Crashes
- **Riesgo Principal**: Reversiones bruscas del momentum
- Ejemplo: Marzo 2020 (COVID crash) - momentum colapsó -30% en semanas
- Mitigación: Filtro de régimen ayuda, pero no elimina el riesgo

#### 2. Alta Rotación (Turnover)
- Rebalanceo frecuente genera costos de transacción
- Impacto fiscal: Ganancias de corto plazo (mayor impuesto)
- Slippage en símbolos menos líquidos

#### 3. Crowding
- Estrategia muy popular → Muchos traders hacen lo mismo
- Puede reducir efectividad con el tiempo
- Competencia por las mismas acciones

#### 4. Underperformance en Mercados Laterales
- Momentum necesita tendencias claras
- En mercados choppy: Whipsaws (señales falsas)
- Filtro de régimen ayuda, pero implica estar fuera del mercado

#### 5. Dependencia del Régimen
- Solo opera ~60% del tiempo (cuando es BULL)
- Oportunidad perdida en otros regímenes
- Necesitas estrategia complementaria para BEAR/NEUTRAL

#### 6. Riesgo de Concentración
- Solo 3 posiciones (con K=3)
- Riesgo idiosincrático alto
- Una mala posición puede dañar el portfolio

#### 7. Behavioral Challenges
- Difícil psicológicamente: Compras "caro" (después de subidas)
- FOMO cuando no estás en el mercado
- Tentación de override las señales

## Comparación con Otras Estrategias

| Aspecto | Long Momentum | Value | Mean Reversion |
|---------|---------------|-------|----------------|
| **Filosofía** | Compra ganadores | Compra baratos | Compra caídos |
| **Holding Period** | Semanas-meses | Años | Días-semanas |
| **Win Rate** | 50-60% | 40-50% | 60-70% |
| **Profit Factor** | 1.5-2.0 | 1.3-1.8 | 1.2-1.5 |
| **Max Drawdown** | -15 a -25% | -20 a -40% | -10 a -20% |
| **Mejor en** | Bull markets | Bear/Recovery | Sideways |
| **Peor en** | Reversiones | Burbujas | Trending |

## Costos Reales de Implementación

### Ejemplo con $10,000 USD

```
Capital Inicial: $10,000
Exposición: 20% = $2,000
Posiciones: 3 símbolos
Por posición: $666.67

Costos por Rebalanceo (semanal):
- Comisiones: $0 (broker moderno)
- Slippage: ~0.05% = $1 por trade
- Total por rebalanceo: ~$3-6

Costos Anuales:
- 52 rebalanceos × $5 = $260
- % del capital: 2.6%

Impacto en Retorno:
- Retorno bruto esperado: +15-20% anual
- Costos: -2.6%
- Retorno neto: +12.4-17.4% anual
```

### Optimización de Costos

1. **Reducir Frecuencia**: Rebalanceo quincenal en lugar de semanal
2. **Aumentar Capital**: Con $50K, costos bajan a ~0.5%
3. **Broker Correcto**: $0 comisiones es crítico
4. **Símbolos Líquidos**: Evitar small caps (mayor slippage)

## Recomendaciones Prácticas

### Para Principiantes

1. **Empieza con Paper Trading**
   ```bash
   python main.py --mode paper --strategy long_momentum
   ```

2. **Capital Pequeño**: Usa ETFs en lugar de acciones individuales
   - Menos diversificación requerida
   - Menores costos de transacción

3. **Frecuencia Menor**: Rebalanceo mensual
   - Reduce costos
   - Menos estrés psicológico

### Para Intermedios

1. **Backtest Exhaustivo**: Valida en diferentes períodos
   ```bash
   python scripts/run_walk_forward_validation.py
   ```

2. **Combina con Otras Estrategias**:
   - Long Momentum (BULL) + Short Momentum (BEAR)
   - Momentum + Mean Reversion (diversificación)

3. **Optimiza Parámetros**: Encuentra tu sweet spot
   - top_k: 3-5
   - holding_days: 7-14
   - tp_multiplier: 1.03-1.07

### Para Avanzados

1. **Machine Learning Enhancement**:
   - Usa ML para predecir cuándo momentum funcionará mejor
   - Feature engineering: Volatility regime, correlation, etc.

2. **Multi-Asset**: Aplica a diferentes clases
   - Acciones, ETFs, commodities, crypto

3. **Automatización Completa**:
   - Integración con broker API
   - Monitoreo 24/7
   - Alertas automáticas

## Recursos Adicionales

### Papers Académicos
1. Jegadeesh & Titman (1993): "Returns to Buying Winners and Selling Losers"
2. Asness et al. (2013): "Value and Momentum Everywhere"
3. Daniel & Moskowitz (2016): "Momentum Crashes"

### Libros
1. "Quantitative Momentum" - Wesley Gray & Jack Vogel
2. "Dual Momentum Investing" - Gary Antonacci
3. "Following the Trend" - Andreas Clenow

### Herramientas
1. **Backtesting**: AuronAI (este sistema)
2. **Screening**: Finviz, TradingView
3. **Ejecución**: Alpaca, Interactive Brokers

## Conclusión

La estrategia Long Momentum es **real, probada y aplicable**, pero no es una "bala de plata":

✅ **Úsala si**:
- Tienes capital suficiente ($10K+)
- Puedes tolerar drawdowns de -15 a -25%
- Entiendes que solo opera en mercados alcistas
- Tienes disciplina para seguir las señales

❌ **Evítala si**:
- Necesitas ingresos constantes (no opera siempre)
- No toleras volatilidad
- Capital muy pequeño (<$5K)
- No puedes monitorear semanalmente

**Mejor Enfoque**: Combínala con otras estrategias para crear un portfolio robusto que funcione en diferentes regímenes de mercado.

---

**Siguiente Paso**: Ejecuta un backtest para ver cómo habría funcionado en tu universo de símbolos:

```bash
python scripts/run_backtest.py --strategy long_momentum --symbols AAPL,MSFT,GOOGL,NVDA,TSLA
```
