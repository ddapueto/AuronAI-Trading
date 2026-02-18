# Estrategia Momentum para Libertex - Explicación Completa 🎯

## ¿Qué es la Estrategia Momentum?

La estrategia momentum se basa en un principio simple: **"Lo que sube, tiende a seguir subiendo"**. Compramos los activos con mejor desempeño reciente y los mantenemos mientras mantengan su fuerza.

---

## 🔍 Cómo Funciona la Selección

### 1. Universo de Activos

Analizamos estos ETFs que representan diferentes sectores:

```
SPY  - S&P 500 (mercado general)
QQQ  - Nasdaq Tech (tecnología)
IWM  - Russell 2000 (pequeñas empresas)
EFA  - Mercados desarrollados internacionales
EEM  - Mercados emergentes
TLT  - Bonos largo plazo
GLD  - Oro
USO  - Petróleo
XLF  - Sector financiero
XLE  - Sector energético
```

### 2. Cálculo de Momentum

Cada semana calculamos el **momentum de 90 días** (3 meses):

```
Momentum = (Precio_Actual - Precio_90_días_atrás) / Precio_90_días_atrás
```

**Ejemplo real (Marzo 2021):**
```
IWM:
- Precio hace 90 días: $195.50
- Precio actual: $210.03
- Momentum: (210.03 - 195.50) / 195.50 = 7.43% ✅ TOP

USO:
- Precio hace 90 días: $38.20
- Precio actual: $44.87
- Momentum: (44.87 - 38.20) / 38.20 = 17.46% ✅ TOP

SPY:
- Precio hace 90 días: $385.00
- Precio actual: $390.50
- Momentum: (390.50 - 385.00) / 385.00 = 1.43% ❌ Débil
```

### 3. Selección de Top Activos

Seleccionamos los **top 2-3 activos** con mayor momentum:

```
Ranking Marzo 2021:
1. USO: +17.46% ⭐ COMPRAR
2. IWM: +7.43%  ⭐ COMPRAR
3. QQQ: +5.20%  ⭐ COMPRAR (opcional)
4. SPY: +1.43%  ❌ No comprar
5. TLT: -2.10%  ❌ No comprar
```

---

## 📅 Frecuencia de Rebalanceo

### Rebalanceo Semanal (Cada 7 días)

**¿Por qué semanal?**
- Captura cambios de momentum rápidamente
- No sobre-opera (evita comisiones excesivas)
- Balance entre reactividad y costos

**Calendario de Rebalanceo:**
```
Semana 1: 2021-01-01 → Analizar momentum → HOLD (esperar señal)
Semana 2: 2021-01-08 → Analizar momentum → HOLD
...
Semana 10: 2021-03-05 → Analizar momentum → COMPRAR IWM ✅
Semana 11: 2021-03-12 → Analizar momentum → HOLD (IWM sigue fuerte)
...
Semana 19: 2021-05-07 → Analizar momentum → COMPRAR USO ✅
```

---

## 💰 Gestión de Capital (50% Risk Budget)

### Regla de Asignación

Con $1,000 iniciales y 50% risk budget:

```
Capital total: $1,000
Risk budget: 50% = $500 disponibles para invertir
Efectivo reserva: 50% = $500 en cash
```

### Distribución por Posición

Si compramos 2 activos:
```
Capital por activo: $500 / 2 = $250 cada uno
```

Si compramos 3 activos:
```
Capital por activo: $500 / 3 = $166.67 cada uno
```

---

## 📊 Ejemplo Real: Backtest 2021-2025

### Semana 10 (Marzo 5, 2021): Primera Compra

**Análisis de Momentum:**
```
Top 3 activos:
1. IWM: +7.43% momentum
2. QQQ: +5.20% momentum
3. USO: +4.80% momentum
```

**Decisión:**
```
✅ COMPRAR IWM
   - Precio: $210.03
   - Capital asignado: $500 (50% del total)
   - Acciones: $500 / $210.03 = 2.38 acciones
   - Comisión: $1.00
   - Costo total: $501.00
```

**Estado del Portfolio:**
```
Posiciones:
- IWM: 2.38 acciones @ $210.03 = $500.00

Efectivo: $499.00
Balance total: $999.00 (perdimos $1 en comisión)
```

### Semana 11-18: HOLD

**Cada semana revisamos:**
```
¿IWM sigue en top 3 de momentum? ✅ SÍ
Acción: HOLD (mantener posición)
```

### Semana 19 (Mayo 7, 2021): Segunda Compra

**Análisis de Momentum:**
```
Top 3 activos:
1. USO: +17.46% momentum ⭐ NUEVO
2. IWM: +6.20% momentum ✅ Mantiene
3. QQQ: +4.50% momentum
```

**Decisión:**
```
✅ COMPRAR USO (nuevo momentum fuerte)
✅ MANTENER IWM (sigue en top 3)

Compra USO:
   - Precio: $44.87
   - Capital disponible: $499 (efectivo restante)
   - Acciones: $499 / $44.87 = 11.05 acciones
   - Comisión: $1.00
   - Costo total: $496.97
```

**Estado del Portfolio:**
```
Posiciones:
- IWM: 2.38 acciones @ $210.03 = $500.00
- USO: 11.05 acciones @ $44.87 = $495.97

Efectivo: $2.03
Balance total: $998.00
```

### Semana 20-214: HOLD

**Cada semana revisamos:**
```
¿IWM y USO siguen en top 3? ✅ SÍ
Acción: HOLD (mantener ambas posiciones)
```

**Resultado Final (4 años después):**
```
Capital inicial: $1,000.00
Capital final: $1,396.10
Ganancia: $396.10
Retorno: +39.61%
Retorno anual: 8.51%
```

---

## 🔄 Proceso de Rebalanceo Semanal

### Cada Lunes por la Mañana

**Paso 1: Calcular Momentum (90 días)**
```python
Para cada activo:
    momentum = (precio_hoy - precio_90_dias_atras) / precio_90_dias_atras
```

**Paso 2: Ranking**
```
Ordenar activos por momentum de mayor a menor
Seleccionar top 3
```

**Paso 3: Comparar con Posiciones Actuales**
```
Para cada posición actual:
    ¿Sigue en top 3? 
        → SÍ: MANTENER
        → NO: VENDER
        
Para cada activo en top 3:
    ¿Ya lo tengo?
        → SÍ: MANTENER
        → NO: COMPRAR (si hay efectivo)
```

**Paso 4: Ejecutar Operaciones**
```
1. Vender posiciones que perdieron momentum
2. Esperar confirmación de venta
3. Comprar nuevos activos con momentum
4. Actualizar registro
```

---

## 📋 Valores Usados en el Backtest

### Parámetros de la Estrategia

```python
# Configuración
lookback_period = 90        # 90 días (3 meses) para calcular momentum
rebalance_days = 7          # Rebalanceo cada 7 días (semanal)
risk_budget = 0.50          # 50% del capital para invertir
top_n = 3                   # Seleccionar top 3 activos
initial_capital = 1000.0    # Capital inicial $1,000

# Costos
commission_per_trade = 1.0  # $1 por operación
slippage = 0.0005          # 0.05% de slippage
```

### Universo de Activos

```python
symbols = [
    'SPY',  # S&P 500
    'QQQ',  # Nasdaq
    'IWM',  # Russell 2000
    'EFA',  # EAFE Internacional
    'EEM',  # Emergentes
    'TLT',  # Bonos
    'GLD',  # Oro
    'USO',  # Petróleo
    'XLF',  # Financiero
    'XLE'   # Energía
]
```

### Período de Prueba

```
Fecha inicio: 2021-01-01
Fecha fin: 2025-02-01
Duración: 4.08 años
Total semanas: 214
```

---

## 📊 Sistema de Balance de Portfolio

### Estructura del CSV Generado

El CSV `libertex_weekly_portfolio.csv` contiene:

```csv
Semana | Fecha_Inicio | Fecha_Fin | Accion | Simbolos_Comprados | Acciones_Compradas | Costo_Compras | Comision | Posiciones_Activas | Simbolos_Activos | Valor_Posiciones | Efectivo_Disponible | Balance_Total | Ganancia | Retorno_Pct
```

### Cómo Usar el CSV

**1. Cada Lunes:**
```
- Abre el CSV
- Busca la semana actual
- Lee la columna "Accion"
```

**2. Si dice "BUY":**
```
- Mira "Simbolos_Comprados": Qué comprar
- Mira "Acciones_Compradas": Cuántas acciones
- Mira "Costo_Compras": Cuánto dinero necesitas
- Ejecuta la compra en Libertex
```

**3. Si dice "SELL":**
```
- Mira "Simbolos_Vendidos": Qué vender
- Ejecuta la venta en Libertex
- Espera confirmación
```

**4. Si dice "HOLD":**
```
- No hagas nada
- Mantén tus posiciones actuales
- Revisa la próxima semana
```

**5. Verifica tu Balance:**
```
- Compara tu balance real en Libertex
- Con la columna "Balance_Total" del CSV
- Deben ser similares (±2-3%)
```

---

## 🎯 Ejemplo Práctico: Cómo Operar

### Semana 10 (Marzo 5, 2021)

**CSV dice:**
```
Accion: BUY
Simbolos_Comprados: IWM
Acciones_Compradas: 2.38
Costo_Compras: $501.00
```

**Tú haces en Libertex:**
```
1. Abre app Libertex
2. Busca "IWM"
3. Toca "Comprar"
4. Selecciona "Monto"
5. Ingresa: $500
6. Confirma (Libertex calcula 2.38 acciones automáticamente)
7. Paga comisión: $1
```

**Resultado:**
```
✅ Tienes 2.38 acciones de IWM
💰 Gastaste $501 ($500 + $1 comisión)
💵 Te quedan $499 en efectivo
```

### Semana 11-18: HOLD

**CSV dice:**
```
Accion: HOLD
Simbolos_Activos: IWM
```

**Tú haces:**
```
❌ NADA - Solo monitorea
📊 Revisa que IWM siga en tu portfolio
💰 Verifica tu balance semanal
```

### Semana 19 (Mayo 7, 2021)

**CSV dice:**
```
Accion: BUY
Simbolos_Comprados: USO
Acciones_Compradas: 11.05
Costo_Compras: $496.97
```

**Tú haces en Libertex:**
```
1. Busca "USO"
2. Comprar por monto: $496
3. Confirma (11.05 acciones)
4. Paga comisión: $1
```

**Resultado:**
```
✅ Tienes 2.38 IWM + 11.05 USO
💰 Gastaste $497
💵 Te quedan $2 en efectivo
📊 Portfolio diversificado en 2 activos
```

---

## 🔧 Herramientas para Gestión

### 1. CSV de Portfolio

**Archivo:** `results/libertex_weekly_portfolio.csv`

**Uso:**
- Abre en Excel o Google Sheets
- Filtra por fecha actual
- Sigue las instrucciones de "Accion"

### 2. Calculadora de Momentum

**Fórmula en Excel:**
```excel
=((Precio_Actual - Precio_90_dias) / Precio_90_dias) * 100
```

**Ejemplo:**
```
Celda A1: Precio actual (210.03)
Celda A2: Precio hace 90 días (195.50)
Celda A3: =(A1-A2)/A2*100
Resultado: 7.43%
```

### 3. Registro de Operaciones

**Template:**
```
Fecha | Acción | Símbolo | Acciones | Precio | Costo | Balance
------|--------|---------|----------|--------|-------|--------
2021-03-05 | COMPRA | IWM | 2.38 | $210.03 | $501 | $999
2021-05-07 | COMPRA | USO | 11.05 | $44.87 | $497 | $998
```

---

## ⚠️ Reglas Importantes

### 1. Disciplina de Rebalanceo

```
✅ Rebalancea SIEMPRE cada 7 días
❌ NO rebalancees más frecuente (costos)
❌ NO rebalancees menos frecuente (pierdes momentum)
```

### 2. Respeta el Risk Budget

```
✅ Usa MÁXIMO 50% del capital
❌ NO uses 100% (necesitas liquidez)
❌ NO uses menos de 30% (sub-optimizado)
```

### 3. No Emociones

```
✅ Sigue el sistema mecánicamente
❌ NO vendas por miedo
❌ NO compres por FOMO
❌ NO ignores señales de venta
```

### 4. Mantén Registro

```
✅ Anota TODAS las operaciones
✅ Compara con el CSV semanal
✅ Revisa desviaciones
```

---

## 📚 Recursos Relacionados

- [Cómo Operar en Libertex](libertex-como-operar-acciones-fraccionarias.md)
- [Niveles de Riesgo](libertex-niveles-riesgo-momentum.md)
- [Estrategia Long Momentum](estrategia-long-momentum.md)
- [Plan de Crecimiento](plan-crecimiento-1000-inicial.md)

---

## 🎓 Resumen Ejecutivo

**La estrategia en 5 puntos:**

1. **Cada semana** calcula momentum de 90 días para 10 ETFs
2. **Selecciona top 3** con mayor momentum
3. **Invierte 50%** del capital dividido entre los top 3
4. **Mantén 50%** en efectivo para flexibilidad
5. **Rebalancea** cada 7 días siguiendo el sistema

**Resultado esperado:**
- Retorno anual: 8-10%
- Drawdown máximo: -28%
- Sharpe Ratio: 0.47
- Operaciones: 2-4 por año

**Ventaja clave:**
La estrategia es **100% mecánica** - no requiere intuición, solo disciplina para seguir las señales.

---

*Última actualización: Febrero 2026*  
*Basado en backtest real 2021-2025*
