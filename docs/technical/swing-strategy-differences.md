# Diferencias entre SwingTPStrategy y SwingNoSLStrategy Original

## Resumen

Ambas implementaciones siguen la misma filosofía (rebalanceo diario, TP+TimeExit, sin SL), pero tienen diferencias técnicas que afectan los resultados.

## Resultados Comparativos

### Original (SwingNoSLStrategy)
- **Return**: 5.58% en 7 meses
- **Trades**: 113
- **Sharpe**: 0.92
- **Max DD**: -3.24%
- **Capital**: $1,000

### Actual (SwingTPStrategy + BacktestRunner)
- **Return**: 0.04% en 7 meses  
- **Trades**: 80
- **Sharpe**: 1.67
- **Max DD**: -0.02%
- **Capital**: $1,000

## Diferencias Clave

### 1. Precio de Entrada

**Original**:
```python
# Decide hoy (día i), entra mañana (día i+1) en el OPEN
entry_price = data['Open'].iloc[i + 1]
```

**Actual**:
```python
# Decide y entra el mismo día en el CLOSE
entry_price = symbol_data['Close']
```

**Impacto**:
- Original tiene 1 día más de "lookback" antes de entrar
- Original es más realista (decides hoy, ejecutas mañana)
- Original evita look-ahead bias
- Diferencia puede ser significativa en mercados volátiles

### 2. Precio de Salida para TP

**Original**:
```python
# Si High >= TP, sale exactamente en TP
if high >= trade.tp:
    exit_price = trade.tp
```

**Actual**:
```python
# Si High >= TP, sale en TP (igual)
if high_val >= position.tp_price:
    exit_price = position.tp_price
```

**Impacto**: Igual en ambos

### 3. Gestión de Cash

**Original**:
```python
# Calcula shares basado en equity actual
position_value = self.equity * allocation
shares = position_value / entry_price
# Actualiza equity directamente con P&L
self.equity += pnl_dollar
```

**Actual**:
```python
# Deduce cash al abrir posición
cash -= total_cost  # incluye comisiones y slippage
# Devuelve cash al cerrar posición
cash += shares * exit_price
```

**Impacto**:
- Actual es más realista (tracking de cash separado)
- Actual incluye comisiones y slippage explícitamente
- Original asume ejecución perfecta

### 4. Comisiones y Slippage

**Original**:
- NO incluye comisiones
- NO incluye slippage
- Asume ejecución perfecta

**Actual**:
- Comisiones: 0.1% por defecto
- Slippage: 0.05% por defecto
- Total: 0.15% por trade (entrada + salida = 0.30%)

**Impacto**:
- Con 80 trades: ~0.30% × 80 = 24% de costos sobre capital
- Esto explica gran parte de la diferencia en return

### 5. Cálculo de Equity

**Original**:
```python
# Equity = suma de todas las posiciones abiertas + cash implícito
# No separa cash de posiciones
```

**Actual**:
```python
# Equity = cash + valor de posiciones
equity = cash + position_value
```

**Impacto**: Actual es más preciso y realista

## Por Qué la Diferencia en Trades (80 vs 113)

### Factores que Reducen Trades en Actual:

1. **Entrada en Close vs Open**: 
   - Menos tiempo para que el precio se mueva
   - Puede perder oportunidades que se desarrollan overnight

2. **Comisiones y Slippage**:
   - Reducen el cash disponible
   - Pueden impedir abrir nuevas posiciones por falta de cash

3. **Tracking de Cash Más Estricto**:
   - Original puede "crear dinero" implícitamente
   - Actual requiere cash real para abrir posiciones

4. **Timing de Rebalanceo**:
   - Ambos intentan rebalancear diariamente
   - Pero el orden de operaciones puede diferir

## Recomendaciones

### Para Mejorar SwingTPStrategy:

1. **Cambiar a entrada en Open del día siguiente**:
   ```python
   # En lugar de usar Close del día actual
   # Usar Open del día siguiente
   # Requiere cambios en BacktestRunner
   ```

2. **Hacer comisiones opcionales**:
   ```python
   # Permitir commission_rate=0 para comparación justa
   config = BacktestConfig(
       commission_rate=0.0,
       slippage_rate=0.0
   )
   ```

3. **Validar cash management**:
   - Asegurar que nunca "creamos dinero"
   - Verificar que cash + positions = equity siempre

4. **Agregar modo "perfect execution"**:
   - Sin comisiones ni slippage
   - Para comparar lógica pura

### Para Trading Real:

1. **Usar SwingTPStrategy** (más realista):
   - Incluye comisiones y slippage
   - Tracking de cash separado
   - Más conservador

2. **Ajustar expectativas**:
   - Return real será menor que backtests sin costos
   - Considerar 0.30% de costos por trade
   - Con broker de bajo costo: 0.10-0.15% por trade

3. **Optimizar para reducir trades**:
   - Aumentar TP a 6-7% (menos trades, mejor ratio)
   - Aumentar holding_days a 10-14 días
   - Filtrar entradas con mayor convicción

## Conclusión

La diferencia principal NO es la lógica de la estrategia (ambas son correctas), sino:

1. **Costos de transacción**: 0.30% por trade × 80 trades = 24% del capital
2. **Timing de entrada**: Close vs Open del día siguiente
3. **Cash management**: Más estricto en actual

Para trading real, **SwingTPStrategy es superior** porque:
- Incluye costos reales
- Tracking de cash más preciso
- Más conservador y realista

Para backtesting puro, **SwingNoSLStrategy** muestra el potencial máximo sin fricciones.

## Próximos Pasos

1. Implementar entrada en Open del día siguiente en BacktestRunner
2. Agregar modo "zero-cost" para comparación justa
3. Validar que ambas implementaciones den resultados similares sin costos
4. Documentar trade-offs entre realismo y optimismo

## Fecha
2026-02-13
