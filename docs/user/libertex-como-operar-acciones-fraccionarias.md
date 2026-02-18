# Libertex: Cómo Abrir y Cerrar Acciones Fraccionarias 📱

## Guía Práctica Paso a Paso

Esta guía te explica cómo ejecutar las operaciones de la estrategia Long Momentum en Libertex usando acciones fraccionarias.

---

## 🎯 Ejemplo Real del Backtest

Según nuestro test con $1,000 y 50% de capital, las posiciones fueron:

```
Posición 1: IWM (Russell 2000)
- Acciones: 2.38 (fraccionarias)
- Precio entrada: $210.03
- Inversión: ~$500

Posición 2: USO (Oil ETF)
- Acciones: 11.05 (fraccionarias)
- Precio entrada: $44.87
- Inversión: ~$496
```

---

## 📱 Paso 1: Abrir Posiciones en Libertex

### Opción A: Comprar por Monto en Dólares (Recomendado)

1. **Abre la app Libertex**
2. **Busca el símbolo** (ej: "IWM")
3. **Toca "Comprar"**
4. **Selecciona "Monto"** (no "Cantidad")
5. **Ingresa el monto en USD**: `$500`
6. **Revisa el resumen:**
   ```
   Monto: $500
   Precio actual: $210.03
   Acciones: ~2.38 (calculado automáticamente)
   Comisión: $1.00
   ```
7. **Confirma la operación**

✅ **Libertex calcula automáticamente las acciones fraccionarias**

### Opción B: Comprar por Cantidad de Acciones

1. **Abre la app Libertex**
2. **Busca el símbolo** (ej: "USO")
3. **Toca "Comprar"**
4. **Selecciona "Cantidad"**
5. **Ingresa acciones fraccionarias**: `11.05`
6. **Revisa el resumen:**
   ```
   Cantidad: 11.05 acciones
   Precio actual: $44.87
   Monto total: ~$495.81
   Comisión: $1.00
   ```
7. **Confirma la operación**

---

## 🔄 Paso 2: Monitorear Posiciones

### En la App Libertex

1. **Ve a "Portfolio"** o "Mis Posiciones"
2. **Verás tus posiciones abiertas:**
   ```
   IWM
   Cantidad: 2.38 acciones
   Precio entrada: $210.03
   Precio actual: $215.50
   P&L: +$13.02 (+2.60%)
   
   USO
   Cantidad: 11.05 acciones
   Precio entrada: $44.87
   Precio actual: $48.20
   P&L: +$36.80 (+7.42%)
   ```

### Alertas Recomendadas

Configura alertas de precio para:
- **Stop Loss**: -10% del precio de entrada
- **Take Profit**: +15% del precio de entrada

---

## 🚪 Paso 3: Cerrar Posiciones

### Cuándo Cerrar (según la estrategia)

La estrategia Long Momentum cierra posiciones cuando:
1. **Rebalanceo semanal**: Cada 7 días revisa momentum
2. **Pérdida de momentum**: El activo ya no está en top 3
3. **Stop Loss**: Pérdida del 10% (opcional)
4. **Rotación**: Aparece mejor oportunidad

### Cómo Cerrar en Libertex

#### Método 1: Cerrar Posición Completa

1. **Ve a "Portfolio"**
2. **Selecciona la posición** (ej: IWM)
3. **Toca "Cerrar"** o "Vender"
4. **Confirma:**
   ```
   Cerrar posición: IWM
   Cantidad: 2.38 acciones
   Precio actual: $215.50
   Valor total: ~$512.89
   P&L: +$13.02
   Comisión: $1.00
   ```
5. **Confirma la venta**

✅ **Libertex vende automáticamente todas las acciones fraccionarias**

#### Método 2: Cerrar Parcialmente

1. **Selecciona la posición**
2. **Toca "Cerrar Parcialmente"**
3. **Ingresa cantidad a cerrar**: `1.19` (50% de 2.38)
4. **Confirma la operación**

---

## 💰 Paso 4: Rebalanceo Semanal

### Proceso de Rotación

Cada 7 días, la estrategia puede indicar:

**Ejemplo de rebalanceo:**
```
Cerrar:
❌ USO (perdió momentum)
   - Vender 11.05 acciones
   - Recuperar ~$496

Mantener:
✅ IWM (sigue fuerte)
   - Mantener 2.38 acciones

Abrir:
🆕 QQQ (nuevo momentum)
   - Comprar con $496 recuperados
   - ~1.25 acciones a $397
```

### Pasos para Rebalancear

1. **Ejecuta el análisis semanal** (script o manual)
2. **Cierra posiciones sin momentum**
3. **Espera confirmación de venta** (instantáneo en Libertex)
4. **Abre nuevas posiciones** con el capital liberado
5. **Verifica que usas ~50% del capital total**

---

## 🔧 Configuración Recomendada en Libertex

### Ajustes de Cuenta

1. **Tipo de orden**: Market (ejecución inmediata)
2. **Comisiones**: $1 por operación (fijo)
3. **Acciones fraccionarias**: Habilitadas por defecto
4. **Apalancamiento**: 1:1 (sin apalancamiento)

### Alertas de Precio

Para cada posición, configura:

```
IWM (entrada $210.03):
- Alerta inferior: $189.03 (-10% stop loss)
- Alerta superior: $241.53 (+15% take profit)

USO (entrada $44.87):
- Alerta inferior: $40.38 (-10% stop loss)
- Alerta superior: $51.60 (+15% take profit)
```

---

## 📊 Ejemplo Completo: Primera Semana

### Lunes (Día 1): Apertura Inicial

**Capital disponible: $1,000**
**Risk budget: 50% = $500**

```
Operación 1:
Símbolo: IWM
Monto: $250 (25% del capital)
Precio: $210.03
Acciones: 1.19
Comisión: $1.00

Operación 2:
Símbolo: USO
Monto: $250 (25% del capital)
Precio: $44.87
Acciones: 5.57
Comisión: $1.00

Capital restante: $498 (49.8% en efectivo)
```

### Lunes (Día 8): Primer Rebalanceo

**Análisis de momentum:**
- ✅ IWM: Sigue fuerte → Mantener
- ❌ USO: Perdió momentum → Cerrar
- 🆕 QQQ: Nuevo momentum → Abrir

```
Paso 1: Cerrar USO
Vender: 5.57 acciones
Precio: $48.20
Recuperar: ~$268
Comisión: $1.00

Paso 2: Abrir QQQ
Comprar: $267
Precio: $397.50
Acciones: 0.67
Comisión: $1.00

Resultado:
- IWM: 1.19 acciones ($250)
- QQQ: 0.67 acciones ($267)
- Efectivo: $481
```

---

## ⚠️ Errores Comunes y Soluciones

### Error 1: "No puedo comprar acciones fraccionarias"

**Solución:**
- Verifica que estás en modo "Acciones" (no CFDs)
- Usa la opción "Monto en USD" en lugar de "Cantidad"
- Libertex permite fraccionarias en acciones reales

### Error 2: "La comisión es muy alta"

**Realidad:**
- Comisión fija: $1 por operación
- En $500 de inversión: 0.2% de costo
- Es competitivo para cuentas pequeñas

### Error 3: "No sé cuántas acciones comprar"

**Solución:**
- Usa "Monto en USD" y deja que Libertex calcule
- Para 50% de $1,000: compra por $250 cada activo
- Libertex calcula automáticamente las fraccionarias

### Error 4: "¿Cierro con ganancia o espero?"

**Regla de la estrategia:**
- Cierra solo en rebalanceo semanal
- O si el activo pierde momentum
- No cierres por ganancias pequeñas (deja correr)

---

## 📱 Interfaz de Libertex: Guía Visual

### Pantalla de Compra

```
┌─────────────────────────────┐
│ Comprar IWM                 │
├─────────────────────────────┤
│ Precio actual: $210.03      │
│                             │
│ ○ Monto    ● Cantidad       │
│                             │
│ Monto: [____$500____]       │
│                             │
│ Acciones: ~2.38             │
│ Comisión: $1.00             │
│ Total: $501.00              │
│                             │
│ [    Confirmar Compra    ]  │
└─────────────────────────────┘
```

### Pantalla de Portfolio

```
┌─────────────────────────────┐
│ Mis Posiciones              │
├─────────────────────────────┤
│ IWM                    ▲    │
│ 2.38 acciones              │
│ $210.03 → $215.50          │
│ P&L: +$13.02 (+2.60%)      │
│ [Cerrar] [Editar]          │
├─────────────────────────────┤
│ USO                    ▲    │
│ 11.05 acciones             │
│ $44.87 → $48.20            │
│ P&L: +$36.80 (+7.42%)      │
│ [Cerrar] [Editar]          │
└─────────────────────────────┘
```

---

## 🎓 Checklist de Operación

### Antes de Abrir Posición

- [ ] Ejecuté análisis de momentum
- [ ] Identifiqué top 2-3 activos
- [ ] Calculé 50% del capital disponible
- [ ] Dividí entre 2-3 posiciones
- [ ] Verifiqué precio actual en Libertex

### Al Abrir Posición

- [ ] Usé "Monto en USD" (no cantidad)
- [ ] Verifiqué comisión ($1)
- [ ] Confirmé acciones fraccionarias
- [ ] Guardé precio de entrada
- [ ] Configuré alertas de precio

### Durante la Semana

- [ ] Monitoreo diario de P&L
- [ ] Reviso alertas de stop loss
- [ ] No cierro por ganancias pequeñas
- [ ] Espero rebalanceo semanal

### En Rebalanceo (cada 7 días)

- [ ] Ejecuté nuevo análisis de momentum
- [ ] Identifiqué posiciones a cerrar
- [ ] Cerré posiciones sin momentum
- [ ] Abrí nuevas posiciones con capital liberado
- [ ] Verifiqué que uso ~50% del capital

---

## 💡 Tips Profesionales

### 1. Usa Órdenes Market

En Libertex, las órdenes market se ejecutan instantáneamente:
- No uses limit orders para momentum
- La velocidad importa más que centavos
- Evita perder oportunidades por $0.10

### 2. Opera en Horario de Mercado

Horario NYSE (hora de México):
- Apertura: 8:30 AM
- Cierre: 3:00 PM

Evita operar:
- Pre-market (alta volatilidad)
- After-hours (baja liquidez)

### 3. Rebalanceo los Lunes

Ejecuta análisis y rebalanceo:
- Lunes por la mañana (antes de apertura)
- Revisa momentum del fin de semana
- Opera en los primeros 30 minutos

### 4. Mantén Registro

Lleva un log simple:
```
Fecha: 2026-02-15
Acción: Compra IWM
Cantidad: 2.38 acciones
Precio: $210.03
Monto: $500
Razón: Top momentum 90 días
```

---

## 🚀 Automatización (Futuro)

### Con MetaTrader 5 + Libertex

Libertex permite conectar MetaTrader 5 para:
- Ejecutar scripts automáticos
- Rebalanceo programado
- Alertas avanzadas

Ver: [Guía Libertex + MetaTrader](libertex-metatrader-guide.md)

---

## 📚 Recursos Relacionados

- [Niveles de Riesgo en Libertex](libertex-niveles-riesgo-momentum.md)
- [Estrategia Long Momentum](estrategia-long-momentum.md)
- [Plan de Crecimiento $1,000](plan-crecimiento-1000-inicial.md)
- [Guía Libertex + MetaTrader](libertex-metatrader-guide.md)

---

## ❓ Preguntas Frecuentes

### ¿Puedo comprar 0.5 acciones en Libertex?

✅ Sí, Libertex permite acciones fraccionarias desde 0.01 acciones.

### ¿Cuánto cuesta cada operación?

💰 Comisión fija de $1 por operación (compra o venta).

### ¿Puedo vender solo parte de mis acciones?

✅ Sí, puedes cerrar parcialmente (ej: vender 1.19 de 2.38 acciones).

### ¿Qué pasa si el mercado está cerrado?

⏰ La orden queda pendiente y se ejecuta en la apertura del siguiente día hábil.

### ¿Libertex cobra por mantener posiciones?

❌ No, solo pagas comisión al comprar/vender. No hay cargos overnight.

### ¿Puedo usar stop loss automático?

✅ Sí, Libertex permite configurar stop loss y take profit automáticos.

---

*Última actualización: Febrero 2026*  
*Basado en Libertex app versión 2026*
