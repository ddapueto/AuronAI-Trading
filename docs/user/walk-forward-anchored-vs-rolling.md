# Walk-Forward: Anchored vs Rolling - Aclaración Crítica

## 🎯 Tu Pregunta (Muy Válida)

> "¿Por qué el top_k se evalúa con toda la info del test y no con la info al momento del trade?"

**Respuesta corta**: Tienes razón en cuestionar esto. Hay DOS tipos de walk-forward:

1. **Anchored Walk-Forward** (lo que expliqué antes - más simple)
2. **Rolling Walk-Forward** (lo que sugieres - más realista)

## 📊 Diferencia Fundamental

### Anchored Walk-Forward (Simplificado)

```
Período 1:
├─ TRAIN (6 meses) ─┤─ TEST (3 meses) ─┤
2020-01 ──> 2020-06   2020-07 ──> 2020-09
     ↓                      ↓
  Optimizar              Operar TODO el período
  top_k=5                con top_k=5 fijo

❌ PROBLEMA: top_k=5 se usa para TODOS los trades en el test
   Pero en la vida real, re-optimizarías periódicamente
```

### Rolling Walk-Forward (Realista)

```
Día 1 (2020-07-01):
├─ TRAIN (últimos 6 meses) ─┤
2020-01 ──────────> 2020-06
         ↓
    Optimizar → top_k=5
         ↓
    Trade hoy con top_k=5

Día 2 (2020-07-02):
├─ TRAIN (últimos 6 meses) ─┤
2020-01-02 ────────> 2020-07-01
         ↓
    Optimizar → top_k=5 (puede cambiar)
         ↓
    Trade hoy con top_k=5

Día 30 (2020-07-30):
├─ TRAIN (últimos 6 meses) ─┤
2020-01-30 ────────> 2020-07-29
         ↓
    Optimizar → top_k=4 (cambió!)
         ↓
    Trade hoy con top_k=4

✅ CORRECTO: Cada trade usa parámetros optimizados
   con información disponible HASTA ese momento
```

## 🔍 Ejemplo Concreto

### Escenario: Long Momentum en Julio 2020

**Anchored (Simplificado)**:

```python
# 1. Optimizar UNA VEZ al inicio del test
train_data = get_data('2020-01-01', '2020-06-30')
best_top_k = optimize(train_data)  # → top_k=5

# 2. Usar top_k=5 para TODO julio
for date in july_2020:
    signals = generate_signals(date, top_k=5)
    execute_trades(signals)

# Problema: ¿Y si el mercado cambió en julio?
# top_k=5 puede ya no ser óptimo
```

**Rolling (Realista)**:

```python
# Cada día de julio
for date in july_2020:
    # 1. Optimizar con datos hasta AYER
    train_data = get_data(
        start=date - timedelta(days=180),  # 6 meses atrás
        end=date - timedelta(days=1)       # hasta ayer
    )
    best_top_k = optimize(train_data)
    
    # 2. Operar HOY con parámetros optimizados
    signals = generate_signals(date, top_k=best_top_k)
    execute_trades(signals)

# Resultado: Parámetros se adaptan al mercado
# 2020-07-01: top_k=5
# 2020-07-15: top_k=4 (mercado cambió)
# 2020-07-30: top_k=6 (mercado cambió otra vez)
```

## 📈 Comparación Visual

### Anchored Walk-Forward

```
TRAIN                    TEST
├────────────────┤  ├──────────────┤
2020-01 → 2020-06  2020-07 → 2020-09
      ↓                    ↓
  Optimizar          Usar parámetros
  top_k=5            FIJOS (top_k=5)
                     para TODO el test

Trades en TEST:
2020-07-01: top_k=5 ✓
2020-07-15: top_k=5 ✓
2020-08-01: top_k=5 ✓
2020-08-15: top_k=5 ✓
2020-09-01: top_k=5 ✓

❌ Parámetros no se adaptan durante el test
```

### Rolling Walk-Forward

```
Cada día del test:

2020-07-01:
├─ TRAIN (6 meses) ─┤
2020-01 ──> 2020-06
      ↓
  Optimizar → top_k=5
      ↓
  Trade con top_k=5

2020-07-15:
├─ TRAIN (6 meses) ─┤
2020-01-15 ──> 2020-07-14
      ↓
  Optimizar → top_k=4 (cambió!)
      ↓
  Trade con top_k=4

2020-08-01:
├─ TRAIN (6 meses) ─┤
2020-02-01 ──> 2020-07-31
      ↓
  Optimizar → top_k=6 (cambió otra vez!)
      ↓
  Trade con top_k=6

✅ Parámetros se adaptan continuamente
```

## 🎯 ¿Cuál es Mejor?

### Para Empezar: Anchored Walk-Forward

**Ventajas**:
- Más simple de implementar
- Más rápido de ejecutar
- Suficiente para detectar overfitting básico
- Bueno para validación inicial

**Desventajas**:
- No simula re-optimización periódica
- Parámetros pueden quedar obsoletos
- Menos realista

**Cuándo usar**: Primera validación de estrategia

### Para Producción: Rolling Walk-Forward

**Ventajas**:
- Simula operación real exactamente
- Parámetros se adaptan al mercado
- Más robusto
- Detecta overfitting mejor

**Desventajas**:
- Más complejo de implementar
- MUCHO más lento (optimiza cada día)
- Puede sobre-adaptar (overfitting a corto plazo)

**Cuándo usar**: Validación final antes de producción

## 🛠️ Implementación en AuronAI

### Anchored Walk-Forward (Fase 1)

```python
# scripts/anchored_walk_forward.py

class AnchoredWalkForward:
    """
    Walk-forward simple: optimiza al inicio de cada período.
    """
    
    def run(self, symbols, start_date, end_date):
        periods = self._generate_periods(start_date, end_date)
        
        results = []
        for period in periods:
            # 1. Optimizar UNA VEZ al inicio
            train_data = self._load_data(
                symbols,
                period.train_start,
                period.train_end
            )
            
            best_params = self._optimize(train_data)
            
            # 2. Operar TODO el test con esos parámetros
            test_data = self._load_data(
                symbols,
                period.test_start,
                period.test_end
            )
            
            result = self._backtest(test_data, best_params)
            results.append(result)
        
        return results

# Uso:
wf = AnchoredWalkForward(
    train_window_months=6,
    test_window_months=3
)

results = wf.run(
    symbols=['AAPL', 'MSFT', 'GOOGL'],
    start_date='2020-01-01',
    end_date='2025-12-31'
)

# Tiempo: ~30 minutos (20 períodos × 1.5 min/período)
```

### Rolling Walk-Forward (Fase 2)

```python
# scripts/rolling_walk_forward.py

class RollingWalkForward:
    """
    Walk-forward realista: optimiza antes de cada trade.
    """
    
    def run(
        self,
        symbols,
        start_date,
        end_date,
        reoptimize_frequency='weekly'  # daily, weekly, monthly
    ):
        all_dates = self._get_trading_dates(start_date, end_date)
        
        results = []
        current_params = None
        
        for date in all_dates:
            # 1. ¿Necesitamos re-optimizar?
            if self._should_reoptimize(date, reoptimize_frequency):
                # Optimizar con datos hasta AYER
                train_data = self._load_data(
                    symbols,
                    start=date - timedelta(days=180),  # 6 meses
                    end=date - timedelta(days=1)       # hasta ayer
                )
                
                current_params = self._optimize(train_data)
                
                logger.info(
                    f"{date}: Re-optimized → top_k={current_params.top_k}"
                )
            
            # 2. Operar HOY con parámetros actuales
            daily_data = self._load_data(symbols, date, date)
            
            signals = self._generate_signals(
                daily_data,
                current_params
            )
            
            trades = self._execute_trades(signals)
            results.append({
                'date': date,
                'params': current_params,
                'trades': trades
            })
        
        return results

# Uso:
wf = RollingWalkForward(
    train_window_days=180,
    reoptimize_frequency='weekly'  # re-optimizar cada semana
)

results = wf.run(
    symbols=['AAPL', 'MSFT', 'GOOGL'],
    start_date='2020-01-01',
    end_date='2025-12-31'
)

# Tiempo: ~5 horas (1500 días × 12 segundos/día)
# Con reoptimize_frequency='weekly': ~1 hora
```

## ⚙️ Frecuencia de Re-Optimización

### Opciones

| Frecuencia | Pros | Contras | Recomendado para |
|------------|------|---------|------------------|
| **Diaria** | Máxima adaptación | Muy lento, overfitting | Estrategias intraday |
| **Semanal** | Balance adaptación/estabilidad | Moderado | Swing trading ✅ |
| **Mensual** | Rápido, estable | Menos adaptación | Position trading |
| **Por período** | Muy rápido | Menos realista | Validación inicial |

### Recomendación para Long Momentum

```python
# Para swing trading (holding_days=10):
reoptimize_frequency = 'weekly'  # ✅ Óptimo

# Razón: 
# - Estrategia rebalancea semanalmente
# - Re-optimizar más frecuente = overfitting
# - Re-optimizar menos = parámetros obsoletos
```

## 📊 Resultados Esperados

### Anchored Walk-Forward

```
Período 1 (2020-Q1):
  Train: top_k=5 (Sharpe 2.2)
  Test: top_k=5 (Sharpe 1.9)

Período 2 (2020-Q2):
  Train: top_k=4 (Sharpe 2.3)
  Test: top_k=4 (Sharpe 2.1)

Período 3 (2020-Q3):
  Train: top_k=3 (Sharpe 2.0)
  Test: top_k=3 (Sharpe 1.7)

Promedio TEST: Sharpe 1.9
```

### Rolling Walk-Forward (Weekly)

```
Semana 1 (2020-01-06):
  Optimizar → top_k=5
  Operar semana con top_k=5
  Resultado: Sharpe 2.0

Semana 2 (2020-01-13):
  Optimizar → top_k=5 (sin cambio)
  Operar semana con top_k=5
  Resultado: Sharpe 1.8

Semana 3 (2020-01-20):
  Optimizar → top_k=4 (cambió!)
  Operar semana con top_k=4
  Resultado: Sharpe 2.2

... (260 semanas)

Promedio: Sharpe 1.85
Std: 0.35
```

## 🎯 Recomendación Práctica

### Fase 1: Anchored Walk-Forward (Semanas 1-2)

**Objetivo**: Validación rápida

```bash
python scripts/anchored_walk_forward.py \
  --strategy long_momentum \
  --train-window 6 \
  --test-window 3 \
  --step 3

# Tiempo: 30 minutos
# Resultado: Detecta overfitting básico
```

### Fase 2: Rolling Walk-Forward Weekly (Semanas 3-4)

**Objetivo**: Validación realista

```bash
python scripts/rolling_walk_forward.py \
  --strategy long_momentum \
  --train-window 180 \
  --reoptimize weekly

# Tiempo: 1 hora
# Resultado: Simula operación real
```

### Fase 3: Rolling Walk-Forward Daily (Opcional)

**Objetivo**: Máxima precisión

```bash
python scripts/rolling_walk_forward.py \
  --strategy long_momentum \
  --train-window 180 \
  --reoptimize daily

# Tiempo: 5 horas
# Resultado: Máxima adaptación (riesgo de overfitting)
```

## ⚠️ Cuidado con Over-Optimization

### Problema: Re-optimizar Demasiado Frecuente

```python
# ❌ MAL: Re-optimizar cada día
# Resultado: Parámetros cambian constantemente
# 2020-07-01: top_k=5
# 2020-07-02: top_k=3
# 2020-07-03: top_k=7
# 2020-07-04: top_k=4
# ...

# Problema: Overfitting a ruido de corto plazo
```

### Solución: Frecuencia Apropiada

```python
# ✅ BIEN: Re-optimizar semanalmente
# Resultado: Parámetros estables pero adaptables
# 2020-07-01: top_k=5
# 2020-07-08: top_k=5 (sin cambio)
# 2020-07-15: top_k=5 (sin cambio)
# 2020-07-22: top_k=4 (cambio significativo)
# ...

# Beneficio: Balance entre adaptación y estabilidad
```

## 📝 Resumen

| Aspecto | Anchored | Rolling Weekly | Rolling Daily |
|---------|----------|----------------|---------------|
| **Realismo** | Bajo | Alto ✅ | Muy Alto |
| **Velocidad** | Rápido | Moderado | Lento |
| **Complejidad** | Baja | Media | Media |
| **Overfitting risk** | Medio | Bajo ✅ | Alto |
| **Recomendado para** | Validación inicial | Producción ✅ | Research |

## 🚀 Próximo Paso

**Tu pregunta fue excelente** porque identificaste una limitación real del anchored walk-forward.

**Plan recomendado**:

1. **Semanas 1-2**: Implementar anchored walk-forward
   - Más simple
   - Suficiente para detectar overfitting básico
   - Validación rápida

2. **Semanas 3-4**: Implementar rolling walk-forward weekly
   - Más realista
   - Simula re-optimización periódica
   - Listo para producción

3. **Opcional**: Rolling daily para research avanzado

¿Te ayudo a implementar el anchored primero y luego el rolling?
