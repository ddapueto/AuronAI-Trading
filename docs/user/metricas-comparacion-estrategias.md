# Guía de Métricas para Comparar Estrategias

## 📊 Resumen Ejecutivo

Para comparar estrategias de trading, necesitas evaluar **3 dimensiones**:
1. **Rentabilidad** (¿Cuánto gano?)
2. **Riesgo** (¿Cuánto puedo perder?)
3. **Consistencia** (¿Qué tan confiable es?)

## 🎯 Métricas Actuales en el Sistema

### ✅ Métricas que YA tienes

| Métrica | Qué Mide | Valor Bueno | Valor Malo |
|---------|----------|-------------|------------|
| **total_return** | Ganancia total | >10% | <5% |
| **cagr** | Ganancia anualizada | >15% | <8% |
| **sharpe_ratio** | Return ajustado por riesgo | >1.5 | <1.0 |
| **max_drawdown** | Pérdida máxima | <-10% | >-20% |
| **calmar_ratio** | CAGR / Drawdown | >2.0 | <1.0 |
| **volatility** | Variabilidad de returns | <20% | >40% |
| **win_rate** | % de trades ganadores | >55% | <45% |
| **profit_factor** | Ganancias / Pérdidas | >1.5 | <1.2 |
| **expectancy** | Ganancia promedio por trade | >$10 | <$5 |
| **num_trades** | Número de trades | 50-200 | <20 o >500 |

## 🏆 Ranking de Métricas por Importancia

### 1. Sharpe Ratio (⭐⭐⭐⭐⭐)
**La métrica MÁS importante para comparar estrategias**

```
Sharpe Ratio = (Return - Risk Free Rate) / Volatility
```

**Por qué es importante**:
- Combina rentabilidad Y riesgo
- Ajusta por volatilidad
- Permite comparar estrategias diferentes

**Interpretación**:
- **>2.0**: Excelente (estrategia institucional)
- **1.5-2.0**: Muy bueno (estrategia sólida)
- **1.0-1.5**: Bueno (estrategia viable)
- **0.5-1.0**: Mediocre (revisar)
- **<0.5**: Malo (no usar)

**Ejemplo**:
```
Estrategia A: Return 20%, Volatility 15% → Sharpe = 1.33
Estrategia B: Return 15%, Volatility 8%  → Sharpe = 1.88

Ganador: Estrategia B (mejor ajustado por riesgo)
```

### 2. Max Drawdown (⭐⭐⭐⭐⭐)
**La métrica de RIESGO más importante**

```
Max Drawdown = (Peak - Trough) / Peak
```

**Por qué es importante**:
- Muestra la peor pérdida posible
- Indica si puedes soportar psicológicamente la estrategia
- Determina el capital necesario

**Interpretación**:
- **<-10%**: Excelente (bajo riesgo)
- **-10% a -15%**: Bueno (riesgo moderado)
- **-15% a -20%**: Aceptable (riesgo medio)
- **-20% a -30%**: Alto riesgo (solo para expertos)
- **>-30%**: Muy alto riesgo (peligroso)

**Regla de oro**: Si no puedes soportar ver tu cuenta bajar X%, no uses una estrategia con drawdown de X%.

### 3. Calmar Ratio (⭐⭐⭐⭐)
**Combina rentabilidad y drawdown**

```
Calmar Ratio = CAGR / abs(Max Drawdown)
```

**Por qué es importante**:
- Muestra cuánto ganas por cada % de drawdown
- Mejor que Sharpe para estrategias con drawdowns grandes
- Fácil de interpretar

**Interpretación**:
- **>3.0**: Excelente
- **2.0-3.0**: Muy bueno
- **1.0-2.0**: Bueno
- **0.5-1.0**: Mediocre
- **<0.5**: Malo

**Ejemplo**:
```
Estrategia A: CAGR 15%, DD -10% → Calmar = 1.5
Estrategia B: CAGR 12%, DD -5%  → Calmar = 2.4

Ganador: Estrategia B (mejor relación return/riesgo)
```

### 4. Win Rate (⭐⭐⭐)
**% de trades ganadores**

```
Win Rate = Winning Trades / Total Trades
```

**Por qué es importante**:
- Indica consistencia
- Afecta psicología del trader
- Debe combinarse con profit factor

**Interpretación**:
- **>60%**: Excelente
- **50-60%**: Bueno
- **45-50%**: Aceptable (si profit factor >1.5)
- **<45%**: Malo (necesitas profit factor >2.0)

**CUIDADO**: Win rate alto NO significa estrategia buena.

**Ejemplo**:
```
Estrategia A: Win Rate 70%, Avg Win $10, Avg Loss -$50 → MALA
Estrategia B: Win Rate 40%, Avg Win $100, Avg Loss -$30 → BUENA
```

### 5. Profit Factor (⭐⭐⭐⭐)
**Relación ganancias/pérdidas**

```
Profit Factor = Total Wins / abs(Total Losses)
```

**Por qué es importante**:
- Muestra si la estrategia es rentable
- Debe ser >1.0 para ganar dinero
- Combina win rate y avg win/loss

**Interpretación**:
- **>2.0**: Excelente
- **1.5-2.0**: Muy bueno
- **1.2-1.5**: Bueno
- **1.0-1.2**: Marginal
- **<1.0**: Perdedor (no usar)

### 6. Expectancy (⭐⭐⭐⭐)
**Ganancia promedio por trade**

```
Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)
```

**Por qué es importante**:
- Muestra cuánto esperas ganar por trade
- Debe ser positivo
- Permite calcular ganancia esperada

**Interpretación**:
- **>$50**: Excelente
- **$20-$50**: Muy bueno
- **$10-$20**: Bueno
- **$5-$10**: Marginal
- **<$5**: Malo

**Ejemplo**:
```
Con expectancy de $20 y 100 trades:
Ganancia esperada = $20 × 100 = $2,000
```

### 7. CAGR (⭐⭐⭐)
**Compound Annual Growth Rate**

```
CAGR = (Final / Initial)^(1/Years) - 1
```

**Por qué es importante**:
- Normaliza returns por tiempo
- Permite comparar períodos diferentes
- Muestra crecimiento sostenible

**Interpretación**:
- **>20%**: Excelente (difícil de mantener)
- **15-20%**: Muy bueno
- **10-15%**: Bueno
- **5-10%**: Aceptable
- **<5%**: Malo (mejor invertir en índices)

## 📈 Métricas que DEBERÍAS Agregar

### 1. Sortino Ratio (⭐⭐⭐⭐⭐)
**Sharpe mejorado (solo penaliza volatilidad negativa)**

```python
def calculate_sortino_ratio(returns: pd.Series, target_return: float = 0) -> float:
    """
    Calculate Sortino Ratio.
    
    Args:
        returns: Daily returns
        target_return: Minimum acceptable return (default: 0)
    
    Returns:
        Sortino ratio (annualized)
    """
    excess_returns = returns - target_return
    downside_returns = excess_returns[excess_returns < 0]
    
    if len(downside_returns) == 0:
        return 0.0
    
    downside_std = downside_returns.std()
    
    if downside_std == 0:
        return 0.0
    
    sortino = (returns.mean() - target_return) / downside_std * np.sqrt(252)
    
    return sortino
```

**Por qué agregarlo**:
- Sharpe penaliza volatilidad positiva (malo)
- Sortino solo penaliza volatilidad negativa (mejor)
- Más realista para evaluar riesgo

**Interpretación**:
- **>2.5**: Excelente
- **2.0-2.5**: Muy bueno
- **1.5-2.0**: Bueno
- **<1.5**: Revisar

### 2. Recovery Factor (⭐⭐⭐⭐)
**Qué tan rápido recuperas de drawdowns**

```python
def calculate_recovery_factor(equity_curve: pd.Series) -> float:
    """
    Calculate Recovery Factor.
    
    Recovery Factor = Total Return / abs(Max Drawdown)
    
    Args:
        equity_curve: Equity over time
    
    Returns:
        Recovery factor
    """
    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
    
    cummax = equity_curve.cummax()
    drawdown = (equity_curve - cummax) / cummax
    max_drawdown = drawdown.min()
    
    if max_drawdown == 0:
        return 0.0
    
    recovery_factor = total_return / abs(max_drawdown)
    
    return recovery_factor
```

**Por qué agregarlo**:
- Muestra resiliencia de la estrategia
- Importante para psicología del trader
- Complementa Calmar Ratio

**Interpretación**:
- **>5.0**: Excelente
- **3.0-5.0**: Muy bueno
- **2.0-3.0**: Bueno
- **<2.0**: Revisar

### 3. Average Drawdown Duration (⭐⭐⭐)
**Cuánto tiempo tardas en recuperar**

```python
def calculate_avg_drawdown_duration(equity_curve: pd.Series) -> float:
    """
    Calculate average drawdown duration in days.
    
    Args:
        equity_curve: Equity over time
    
    Returns:
        Average drawdown duration in days
    """
    cummax = equity_curve.cummax()
    drawdown = (equity_curve - cummax) / cummax
    
    # Find drawdown periods
    in_drawdown = drawdown < 0
    
    # Calculate duration of each drawdown
    durations = []
    current_duration = 0
    
    for is_dd in in_drawdown:
        if is_dd:
            current_duration += 1
        elif current_duration > 0:
            durations.append(current_duration)
            current_duration = 0
    
    if current_duration > 0:
        durations.append(current_duration)
    
    if not durations:
        return 0.0
    
    return np.mean(durations)
```

**Por qué agregarlo**:
- Muestra cuánto tiempo estás "bajo el agua"
- Importante para psicología
- Ayuda a decidir si puedes soportar la estrategia

**Interpretación**:
- **<10 días**: Excelente
- **10-20 días**: Bueno
- **20-40 días**: Aceptable
- **>40 días**: Difícil psicológicamente

### 4. Consecutive Losses (⭐⭐⭐)
**Máximo número de pérdidas consecutivas**

```python
def calculate_max_consecutive_losses(trades: List[Dict]) -> int:
    """
    Calculate maximum consecutive losing trades.
    
    Args:
        trades: List of trade dicts with pnl_dollar
    
    Returns:
        Maximum consecutive losses
    """
    if not trades:
        return 0
    
    max_consecutive = 0
    current_consecutive = 0
    
    for trade in trades:
        if trade.get('pnl_dollar', 0) < 0:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0
    
    return max_consecutive
```

**Por qué agregarlo**:
- Muestra peor racha de pérdidas
- Importante para psicología
- Ayuda a calcular capital necesario

**Interpretación**:
- **<5**: Excelente
- **5-8**: Bueno
- **8-12**: Aceptable
- **>12**: Difícil psicológicamente

### 5. Ulcer Index (⭐⭐⭐)
**Mide el "dolor" de los drawdowns**

```python
def calculate_ulcer_index(equity_curve: pd.Series, period: int = 14) -> float:
    """
    Calculate Ulcer Index.
    
    Measures the depth and duration of drawdowns.
    
    Args:
        equity_curve: Equity over time
        period: Lookback period (default: 14)
    
    Returns:
        Ulcer index
    """
    cummax = equity_curve.rolling(window=period, min_periods=1).max()
    drawdown_pct = ((equity_curve - cummax) / cummax) * 100
    
    ulcer_index = np.sqrt((drawdown_pct ** 2).mean())
    
    return ulcer_index
```

**Por qué agregarlo**:
- Combina profundidad Y duración de drawdowns
- Más completo que max drawdown
- Mejor para evaluar "dolor" psicológico

**Interpretación**:
- **<5**: Excelente
- **5-10**: Bueno
- **10-15**: Aceptable
- **>15**: Alto estrés

## 🎯 Cómo Comparar Estrategias: Framework Completo

### Paso 1: Filtro de Viabilidad
**Elimina estrategias que NO cumplen mínimos**

```python
def is_viable_strategy(metrics: Dict) -> bool:
    """Check if strategy meets minimum requirements."""
    return (
        metrics['sharpe_ratio'] >= 1.0 and
        metrics['max_drawdown'] >= -0.25 and  # -25%
        metrics['profit_factor'] >= 1.2 and
        metrics['num_trades'] >= 30
    )
```

### Paso 2: Ranking por Categoría
**Asigna puntos en cada dimensión**

```python
def score_strategy(metrics: Dict) -> Dict[str, float]:
    """Score strategy across multiple dimensions."""
    
    # Rentabilidad (0-10 puntos)
    return_score = min(10, metrics['cagr'] * 50)  # 20% CAGR = 10 puntos
    
    # Riesgo (0-10 puntos)
    risk_score = min(10, (1 - abs(metrics['max_drawdown'])) * 10)
    
    # Consistencia (0-10 puntos)
    consistency_score = min(10, metrics['sharpe_ratio'] * 5)
    
    # Eficiencia (0-10 puntos)
    efficiency_score = min(10, metrics['profit_factor'] * 5)
    
    return {
        'return_score': return_score,
        'risk_score': risk_score,
        'consistency_score': consistency_score,
        'efficiency_score': efficiency_score,
        'total_score': return_score + risk_score + consistency_score + efficiency_score
    }
```

### Paso 3: Ponderación por Prioridades
**Ajusta según tu perfil de riesgo**

```python
def weighted_score(scores: Dict, profile: str = 'balanced') -> float:
    """Calculate weighted score based on risk profile."""
    
    weights = {
        'conservative': {
            'return_score': 0.20,
            'risk_score': 0.40,
            'consistency_score': 0.30,
            'efficiency_score': 0.10
        },
        'balanced': {
            'return_score': 0.30,
            'risk_score': 0.30,
            'consistency_score': 0.25,
            'efficiency_score': 0.15
        },
        'aggressive': {
            'return_score': 0.40,
            'risk_score': 0.20,
            'consistency_score': 0.20,
            'efficiency_score': 0.20
        }
    }
    
    w = weights[profile]
    
    return (
        scores['return_score'] * w['return_score'] +
        scores['risk_score'] * w['risk_score'] +
        scores['consistency_score'] * w['consistency_score'] +
        scores['efficiency_score'] * w['efficiency_score']
    )
```

## 📊 Tabla de Comparación Recomendada

```python
def create_comparison_table(strategies: List[Dict]) -> pd.DataFrame:
    """Create comprehensive comparison table."""
    
    comparison = []
    
    for strategy in strategies:
        metrics = strategy['metrics']
        
        comparison.append({
            'Strategy': strategy['name'],
            
            # Rentabilidad
            'Total Return': f"{metrics['total_return']:.2%}",
            'CAGR': f"{metrics['cagr']:.2%}",
            
            # Riesgo
            'Max DD': f"{metrics['max_drawdown']:.2%}",
            'Volatility': f"{metrics['volatility']:.2%}",
            
            # Risk-Adjusted
            'Sharpe': f"{metrics['sharpe_ratio']:.2f}",
            'Calmar': f"{metrics['calmar_ratio']:.2f}",
            'Sortino': f"{metrics.get('sortino_ratio', 0):.2f}",
            
            # Trading
            'Win Rate': f"{metrics['win_rate']:.2%}",
            'Profit Factor': f"{metrics['profit_factor']:.2f}",
            'Expectancy': f"${metrics['expectancy']:.2f}",
            'Trades': metrics['num_trades'],
            
            # Score
            'Total Score': f"{strategy['score']:.1f}/40"
        })
    
    return pd.DataFrame(comparison)
```

## 🏆 Ejemplo de Comparación

```
Estrategia A (Swing TP):
- Total Return: 15.2%
- CAGR: 18.5%
- Sharpe: 1.85
- Max DD: -8.2%
- Win Rate: 58%
- Profit Factor: 1.75
→ Score: 32.5/40 (Excelente)

Estrategia B (Long Momentum):
- Total Return: 22.1%
- CAGR: 25.3%
- Sharpe: 1.42
- Max DD: -15.8%
- Win Rate: 52%
- Profit Factor: 1.55
→ Score: 28.3/40 (Bueno)

Estrategia C (Short Momentum):
- Total Return: 8.5%
- CAGR: 10.2%
- Sharpe: 2.15
- Max DD: -4.5%
- Win Rate: 62%
- Profit Factor: 1.92
→ Score: 34.1/40 (Excelente)

GANADOR: Estrategia C (mejor ajustado por riesgo)
```

## ✅ Recomendación Final

### Métricas ESENCIALES (ya las tienes):
1. Sharpe Ratio
2. Max Drawdown
3. Calmar Ratio
4. Win Rate
5. Profit Factor

### Métricas a AGREGAR (prioridad alta):
1. **Sortino Ratio** (mejor que Sharpe)
2. **Recovery Factor** (resiliencia)
3. **Max Consecutive Losses** (psicología)

### Métricas a AGREGAR (prioridad media):
4. **Avg Drawdown Duration** (tiempo bajo el agua)
5. **Ulcer Index** (dolor de drawdowns)

### Para Comparar Estrategias:
1. Filtra por viabilidad (Sharpe >1.0, DD <-25%)
2. Calcula score ponderado según tu perfil
3. Prioriza Sharpe y Calmar para decisión final
4. Verifica que puedas soportar el Max DD psicológicamente

## 📚 Recursos Adicionales

- [Investopedia: Sharpe Ratio](https://www.investopedia.com/terms/s/sharperatio.asp)
- [Investopedia: Sortino Ratio](https://www.investopedia.com/terms/s/sortinoratio.asp)
- [Investopedia: Calmar Ratio](https://www.investopedia.com/terms/c/calmarratio.asp)

## Fecha
2026-02-13
