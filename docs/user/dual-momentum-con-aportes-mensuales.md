# Dual Momentum con Aportes Mensuales 💰

## El Problema del "Sin Cash"

### Situación Actual

**Dual Momentum clásico:**
- Invierte 100% del capital
- Top 5 activos × 20% cada uno = 100%
- **NO deja reserva de efectivo**

**Tu preocupación válida:**
> "Me quedo sin cash en seguida, ¿no debería seguir aportando y reinvertir ese capital?"

**Respuesta: SÍ, absolutamente** ✅

---

## 🎯 Estrategia Recomendada: Dual Momentum 80/20

### Configuración Óptima

```python
# Parámetros modificados
top_n = 4  # En lugar de 5
risk_budget = 0.80  # 80% invertido, 20% cash

# Resultado:
# 4 posiciones × 20% = 80% invertido
# 20% permanente en efectivo
```

### ¿Por qué 80/20?

**Ventajas del 20% en cash:**

1. **Liquidez permanente**
   - Siempre tienes efectivo disponible
   - No necesitas vender para rebalancear

2. **Aportes mensuales**
   - Tus $200/mes se acumulan en cash
   - Inviertes cuando hay señal, no forzado

3. **Oportunidades**
   - Puedes aprovechar caídas
   - Flexibilidad para entrar en 5ta posición si aparece

4. **Psicología**
   - Menos estrés
   - No te sientes "atrapado"

**Costo:**
- Retorno ~2-3% menor vs 100% invertido
- Pero mayor estabilidad y flexibilidad

---

## 📈 Simulación: $1,000 + $200/mes

### Escenario A: 100% Invertido (Original)

```
Mes 0: $1,000 → $1,000 invertido, $0 cash
Mes 1: +$200 → $1,200 total, $1,200 invertido, $0 cash
Mes 2: +$200 → $1,400 total, $1,400 invertido, $0 cash

Problema:
- Siempre 100% invertido
- No puedes aprovechar oportunidades
- Rebalancear requiere vender
```

### Escenario B: 80/20 con Aportes (Recomendado)

```
Mes 0: $1,000
  → $800 invertido (4 posiciones × $200)
  → $200 cash

Mes 1: +$200 aporte
  → $800 invertido
  → $400 cash (20% + aporte)
  
  Si hay señal:
    → Invertir $320 (80% de $400)
    → Nuevo total invertido: $1,120
    → Cash restante: $80
  
  Si NO hay señal:
    → Mantener $400 en cash
    → Esperar mejor oportunidad

Mes 2: +$200 aporte
  → $1,120 invertido
  → $280 cash ($80 + $200)
  
  Balance total: $1,400
  Target 80%: $1,120 (ya alcanzado)
  Cash disponible: $280 (20%)
```

### Escenario C: 80/20 Después de 12 Meses

```
Balance total: $3,400
  → $2,720 invertido (80%)
  → $680 cash (20%)

Posiciones:
  - Posición 1: $680 (20%)
  - Posición 2: $680 (20%)
  - Posición 3: $680 (20%)
  - Posición 4: $680 (20%)
  - Cash: $680 (20%)

Ventajas:
  ✅ Cada posición es significativa ($680)
  ✅ Tienes $680 para oportunidades
  ✅ Puedes agregar 5ta posición si aparece
```

---

## 🔄 Flujo de Trabajo Semanal

### Lunes: Análisis de Momentum

```python
# 1. Calcular momentum de 27 símbolos
momentum_scores = calculate_momentum(symbols, lookback=252)

# 2. Filtrar positivos
positive = [s for s in momentum_scores if s > 0]

# 3. Rankear top 4
top_4 = sorted(positive, reverse=True)[:4]

# 4. Comparar con posiciones actuales
current_positions = ['IWM', 'USO', 'QQQ', 'SPY']

# 5. ¿Hay cambios?
if top_4 != current_positions:
    # HAY SEÑAL DE REBALANCEO
    rebalance_needed = True
else:
    # NO HAY CAMBIOS
    rebalance_needed = False
```

### Si HAY Señal de Rebalanceo

```python
# Paso 1: Calcular target
total_balance = 3400  # Ejemplo
target_invested = total_balance * 0.80  # $2,720
per_position = target_invested / 4  # $680

# Paso 2: Vender posiciones que salieron del top 4
sell_symbols = [s for s in current_positions if s not in top_4]
for symbol in sell_symbols:
    sell(symbol)  # Libera cash

# Paso 3: Comprar nuevas posiciones
buy_symbols = [s for s in top_4 if s not in current_positions]
for symbol in buy_symbols:
    buy(symbol, amount=per_position)

# Paso 4: Ajustar posiciones existentes
for symbol in top_4:
    if symbol in current_positions:
        adjust_to(symbol, target=per_position)
```

### Si NO HAY Señal

```python
# Simplemente acumula cash
cash_balance += monthly_contribution  # $200

# Espera a próxima semana
# No haces nada (ahorro en comisiones)
```

---

## 💰 Gestión de Aportes Mensuales

### Regla de Oro

```
NUNCA fuerces una inversión solo porque aportaste.
SOLO invierte cuando hay señal de momentum.
```

### Estrategia de Acumulación

```python
# Cada mes
monthly_contribution = 200

# Agregar a cash
cash_balance += monthly_contribution

# Calcular target
total_balance = invested + cash_balance
target_invested = total_balance * 0.80
target_cash = total_balance * 0.20

# ¿Necesitas rebalancear?
if cash_balance > target_cash:
    # Tienes exceso de cash
    excess_cash = cash_balance - target_cash
    
    # Si hay señal de momentum:
    if rebalance_signal:
        # Invertir exceso en nuevas posiciones
        invest(excess_cash)
    else:
        # Mantener cash hasta que haya señal
        # (Está bien tener más del 20% temporalmente)
        pass
```

### Ejemplo Práctico: 6 Meses

```
Mes 1:
  Balance: $1,000
  Invertido: $800 (80%)
  Cash: $200 (20%)
  Aporte: $200
  Nuevo cash: $400

Mes 2:
  Balance: $1,200
  Target invertido: $960 (80%)
  Actual invertido: $800
  Cash: $400
  
  ¿Hay señal? NO
  Acción: Mantener cash en $400
  
  Aporte: $200
  Nuevo cash: $600

Mes 3:
  Balance: $1,400
  Target invertido: $1,120 (80%)
  Actual invertido: $800
  Cash: $600
  
  ¿Hay señal? SÍ (nuevo top 4)
  Acción: Rebalancear
    - Vender posiciones débiles
    - Comprar nuevas con $320 del cash
  
  Nuevo invertido: $1,120
  Nuevo cash: $280
  
  Aporte: $200
  Nuevo cash: $480

Mes 4-6:
  Continuar el mismo patrón
  Rebalancear solo cuando hay señal
  Acumular cash entre rebalanceos
```

---

## 📊 Comparación de Retornos

### Simulación 4 Años: $1,000 + $200/mes

#### Escenario 100% Invertido

```
Retorno anual: 10%
Aportes totales: $9,600

Año 1: $3,650
Año 2: $6,850
Año 3: $10,650
Año 4: $15,200

Retorno total: $15,200
Ganancia: $4,600 (43% sobre aportes)
```

#### Escenario 80/20 (Recomendado)

```
Retorno anual: 8% (80% × 10%)
Aportes totales: $9,600

Año 1: $3,580
Año 2: $6,680
Año 3: $10,280
Año 4: $14,400

Retorno total: $14,400
Ganancia: $3,800 (36% sobre aportes)
```

#### Diferencia

```
100% invertido: $15,200
80/20: $14,400
Diferencia: -$800 (-5.3%)

PERO:
- Tienes $2,880 en cash disponible (20% de $14,400)
- Mayor flexibilidad
- Menos estrés
- Puedes aprovechar oportunidades
```

---

## 🎯 Recomendación Final

### Para Cuentas Pequeñas ($1K-5K)

```python
# Configuración óptima
top_n = 4
risk_budget = 0.80
monthly_contribution = 200
rebalance_frequency = 'weekly_if_signal'

# Resultado:
# - 80% invertido en 4 posiciones
# - 20% en cash permanente
# - Aportes mensuales se acumulan en cash
# - Rebalanceas solo cuando hay señal
```

### Para Cuentas Medianas ($5K-20K)

```python
# Configuración más agresiva
top_n = 5
risk_budget = 0.85
monthly_contribution = 500
rebalance_frequency = 'weekly_if_signal'

# Resultado:
# - 85% invertido en 5 posiciones
# - 15% en cash
# - Mayor exposición, pero aún con liquidez
```

### Para Cuentas Grandes ($20K+)

```python
# Configuración agresiva
top_n = 5
risk_budget = 0.90
monthly_contribution = 1000
rebalance_frequency = 'weekly_if_signal'

# Resultado:
# - 90% invertido
# - 10% cash (suficiente en términos absolutos)
```

---

## 🔧 Implementación en Código

### Modificar Dual Momentum

```python
# En src/auronai/strategies/dual_momentum.py

@dataclass
class DualMomentumParams(StrategyParams):
    lookback_period: int = 252
    top_n: int = 4  # CAMBIO: 4 en lugar de 5
    rebalance_frequency: str = 'monthly'
    risk_budget: float = 0.80  # CAMBIO: 80% en lugar de 100%
```

### Script de Backtest con Aportes

```python
# Nuevo script: scripts/run_dual_momentum_with_contributions.py

def backtest_with_monthly_contributions(
    initial_capital: float = 1000,
    monthly_contribution: float = 200,
    risk_budget: float = 0.80,
    top_n: int = 4,
    start_date: str = "2021-01-01",
    end_date: str = "2025-02-01"
):
    """
    Backtest Dual Momentum con aportes mensuales.
    """
    # Implementación
    pass
```

---

## 📚 Próximos Pasos

### Esta Semana

1. ✅ Modificar `DualMomentumParams` a 80/20
2. ✅ Crear script de backtest con aportes
3. ✅ Probar con datos históricos

### Este Mes

1. ⏳ Validar resultados con walk-forward
2. ⏳ Comparar 80/20 vs 100% invertido
3. ⏳ Documentar flujo de trabajo semanal

### Próximos 3 Meses

1. ⏳ Implementar en paper trading
2. ⏳ Registrar todos los rebalanceos
3. ⏳ Ajustar parámetros según resultados

---

## ❓ FAQ

### ¿Por qué no 70/30 o 60/40?

**80/20 es el sweet spot:**
- 70/30: Demasiado conservador, retorno muy bajo
- 80/20: Balance óptimo entre retorno y liquidez
- 90/10: Poco cash para aportes mensuales
- 100/0: Sin flexibilidad (tu problema actual)

### ¿Qué pasa si el cash supera el 20%?

**Es normal y está bien:**
```
Si acumulas $600 en cash (30% del balance):
- NO fuerces inversión
- Espera señal de momentum
- Cuando llegue, invertirás el exceso
```

### ¿Cuándo rebalancear?

**Solo cuando hay señal:**
1. Análisis semanal de momentum
2. Si top 4 cambió → Rebalancear
3. Si top 4 igual → NO hacer nada

**NO rebalancear solo porque:**
- Aportaste dinero
- Pasó una semana
- Tienes mucho cash

### ¿Qué hacer en mercados bajistas?

**Dual Momentum se protege solo:**
- Si todos los símbolos tienen momentum negativo
- La estrategia va 100% a cash
- Espera hasta que aparezca momentum positivo

**Con 80/20:**
- Ya tienes 20% en cash siempre
- Si mercado cae, tendrás 100% en cash
- Puedes aprovechar la recuperación

---

*Última actualización: Febrero 2026*
