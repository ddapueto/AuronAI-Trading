# 📊 Entendiendo Velas Japonesas y Timeframes

## ¿Qué son las Velas Japonesas?

Cada vela representa el movimiento del precio durante un período de tiempo específico:

```
Componentes de una Vela:
┌─────────┐
│  High   │ ← Precio más alto del período
│    │    │
│  ┌───┐  │
│  │   │  │ ← Open (apertura) y Close (cierre)
│  └───┘  │
│    │    │
│  Low    │ ← Precio más bajo del período
└─────────┘

+ Volume: Cantidad de acciones negociadas
```

### Ejemplo Real

```
Vela del Lunes (AAPL):
- Open:   $150.00 (precio a las 9:30 AM)
- High:   $152.50 (máximo del día)
- Low:    $148.00 (mínimo del día)
- Close:  $151.00 (precio a las 4:00 PM)
- Volume: 50M acciones
```

## 🕐 Timeframes (Marcos de Tiempo)

### Timeframes Disponibles

| Timeframe | Cada Vela Representa | Uso Típico |
|-----------|---------------------|------------|
| 1m | 1 minuto | Scalping (muy corto plazo) |
| 5m | 5 minutos | Day trading activo |
| 15m | 15 minutos | Day trading |
| 1h | 1 hora | Trading intradiario |
| 1d | 1 día completo | Swing trading ⭐ |
| 1wk | 1 semana | Position trading |

⭐ = Recomendado para AuronAI

## ⚠️ El Problema de la Vela Actual

### Durante el Horario de Mercado (9:30 AM - 4:00 PM)

La vela del día actual está **INCOMPLETA** y cambia constantemente:

```
Lunes 10:00 AM:
Vela actual: Open=$150, High=$151, Low=$149, Close=$150.50
RSI calculado: 65 → Señal: "MANTENER"

Lunes 2:00 PM:
Vela actual: Open=$150, High=$152, Low=$148, Close=$148.50
RSI calculado: 58 → Señal: "COMPRAR" ❌ ¡Cambió!

Lunes 4:00 PM (cierre):
Vela actual: Open=$150, High=$152, Low=$148, Close=$151.00
RSI calculado: 62 → Señal: "MANTENER" ✅ FINAL
```

**Problema:** Los indicadores técnicos cambian todo el día porque la vela no está completa.

### Después del Cierre del Mercado (4:00 PM)

La vela está **COMPLETA** y los valores son **FINALES**:

```
✅ Open:  $150.00 (fijo)
✅ High:  $152.00 (final)
✅ Low:   $148.00 (final)
✅ Close: $151.00 (final)
✅ RSI:   62 (confiable)
```

## 🎯 Solución de AuronAI: Análisis al Cierre del Día

### Configuración por Defecto

```
Timeframe: Diario (1d)
Análisis: Después del cierre (5:00 PM)
Vela actual: Excluida si el mercado está abierto
Estilo: Swing trading (mantener días/semanas)
```

### ¿Por Qué Esta Configuración?

✅ **Datos Confiables**: Todas las velas están completas
✅ **Sin Confusión**: Los indicadores no cambian durante el día
✅ **Menos Estrés**: No necesitas vigilar el mercado todo el día
✅ **Mejores Decisiones**: Tienes tiempo para pensar y planificar
✅ **Para Principiantes**: Fácil de entender y usar
✅ **Probado**: El swing trading es una estrategia sostenible

## 📅 Rutina Diaria Recomendada

### Opción 1: Análisis Nocturno (Recomendado)

```bash
# Después del cierre (5:00 PM - 11:00 PM)
python src/trading_agent.py

# El sistema analiza:
# - Vela de HOY (completa)
# - Todas las velas históricas
# - Genera plan para MAÑANA

# Resultado:
📈 Plan para Mañana:
   Símbolo: AAPL
   Acción: COMPRAR si baja a $150
   Stop Loss: $147
   Take Profit: $155
   Confianza: 8/10
```

### Opción 2: Análisis Matutino

```bash
# Antes de la apertura (7:00 AM - 9:00 AM)
python src/trading_agent.py

# El sistema analiza:
# - Vela de AYER (completa)
# - Genera plan para HOY

# Ejecutas el plan durante el día
```

### ❌ NO Recomendado: Análisis Durante el Mercado

```bash
# Durante horario (9:30 AM - 4:00 PM)
python src/trading_agent.py

# ⚠️ Advertencia:
# "Mercado abierto. Análisis basado en cierre de ayer."
# "Para señales finales de hoy, ejecuta después de 4:00 PM"
```

## 🎮 Modos de Trading

### Swing Trading (Por Defecto) ⭐

```
Timeframe: 1d (diario)
Duración: Días a semanas
Análisis: Después del cierre
Ventajas:
  ✅ Señales confiables
  ✅ Menos estrés
  ✅ Tiempo para pensar
  ✅ Menores costos
Desventajas:
  ❌ No aprovecha movimientos intradiarios
  ❌ Riesgo de gaps nocturnos
```

### Day Trading (Avanzado)

```
Timeframe: 15m o 1h
Duración: Minutos a horas (cierra todo al final del día)
Análisis: Durante el mercado
Ventajas:
  ✅ Más oportunidades
  ✅ Sin riesgo nocturno
Desventajas:
  ❌ Más ruido y señales falsas
  ❌ Requiere monitoreo constante
  ❌ Más estresante
  ❌ Mayores costos
```

### Position Trading (Largo Plazo)

```
Timeframe: 1d o 1wk
Duración: Semanas a meses
Análisis: Semanal
Ventajas:
  ✅ Muy estable
  ✅ Mínimo ruido
Desventajas:
  ❌ Muy lento
  ❌ Menos oportunidades
```

## 🔧 Configuración en .env

```bash
# Timeframe para análisis
TIMEFRAME=1d  # Opciones: 1m, 5m, 15m, 1h, 1d, 1wk

# Estilo de trading
TRADING_STYLE=swing  # Opciones: scalping, day, swing, position

# ¿Usar vela incompleta? (solo para intradiario)
USE_INCOMPLETE_CANDLE=false

# Hora preferida para análisis (formato 24h)
ANALYSIS_TIME=17:00  # 5:00 PM (después del cierre)
```

## 💡 Estrategia Híbrida (Avanzado)

Combina lo mejor de ambos mundos:

```
1. Análisis Diario (Dirección)
   - Ejecuta después del cierre
   - Determina tendencia general
   - Ejemplo: "AAPL alcista según RSI diario"

2. Análisis Intradiario (Timing)
   - Durante el mercado
   - Busca punto de entrada óptimo
   - Ejemplo: "Espera pullback en 15m para entrar"

Resultado:
- Dirección confiable (diario)
- Entrada precisa (intradiario)
- Mejor risk/reward
```

## 📊 Ejemplo Práctico

### Escenario: Análisis de AAPL

```python
# Lunes 5:00 PM (después del cierre)
python src/trading_agent.py

# Output:
📈 Análisis de AAPL (Diario)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 INDICADORES TÉCNICOS:
   Precio: $151.00 (+0.67%)
   RSI: 62.5 (neutral)
   MACD: 1.2 vs Signal: 1.0 (alcista)
   EMA20: $149.50 (precio por encima)
   Tendencia: Alcista

🎯 RECOMENDACIÓN: COMPRAR
💪 Confianza: 8/10

✅ Señales Alcistas:
   • MACD cruzó por encima de signal
   • Precio por encima de EMA20
   • RSI en zona neutral (espacio para subir)
   • Volumen por encima del promedio

⚠️ Señales Bajistas:
   • Resistencia en $152 (máximo anterior)

💼 PLAN DE TRADE:
   Entrada: $151.00 (precio actual)
   Stop Loss: $147.00 (-2.65%)
   Take Profit: $159.00 (+5.30%)
   Tamaño: 66 acciones
   Riesgo: $264 (2% del portfolio)
   R/R Ratio: 2.00:1

📅 Ejecutar: Mañana en la apertura (9:30 AM)
```

## ❓ Preguntas Frecuentes

### ¿Por qué no puedo analizar en tiempo real?

Porque la vela actual cambia constantemente durante el día, haciendo que los indicadores sean poco confiables. Es mejor esperar al cierre para tener datos finales.

### ¿Puedo usar timeframes más cortos?

Sí, pero requiere más experiencia. Configura `TIMEFRAME=15m` en tu `.env` para day trading, pero prepárate para más señales falsas y mayor estrés.

### ¿Qué pasa si hay noticias importantes durante el día?

El análisis diario no captura eventos intradiarios. Para eso necesitarías monitoreo manual o configurar alertas de noticias por separado.

### ¿Cómo manejo los gaps nocturnos?

Los gaps (diferencia entre cierre de ayer y apertura de hoy) son un riesgo del swing trading. Mitígalo con:
- Stop loss bien colocado
- Diversificación (múltiples posiciones)
- Tamaño de posición conservador (2% max)

### ¿Puedo combinar timeframes?

Sí, la estrategia híbrida es muy efectiva:
1. Usa diario para dirección general
2. Usa 15m o 1h para timing de entrada
3. Requiere más experiencia pero mejora resultados

## 🎓 Recomendación para Empezar

```
Semana 1-2: Usa timeframe diario (1d)
           Ejecuta análisis después del cierre
           Observa cómo funcionan los indicadores
           NO hagas trades reales todavía

Semana 3-4: Paper trading con señales diarias
           Registra tus trades simulados
           Aprende de los resultados

Mes 2-3:   Si resultados son positivos
           Considera trading real con capital pequeño
           Mantén timeframe diario

Mes 4+:    Si dominas el diario
           Experimenta con timeframes más cortos
           Pero solo si te sientes cómodo
```

## 📚 Recursos Adicionales

- [Documentación Técnica: Candlestick Data Flow](../technical/candlestick-data-flow.md)
- [ADR-001: Daily Timeframe Decision](../decisions/001-daily-timeframe-default.md)
- [Guía de Inicio Rápido](INICIO_RAPIDO.md)

---

**Recuerda:** El trading exitoso requiere paciencia y disciplina. No hay prisa por usar timeframes más cortos. Domina el análisis diario primero. 📈✨
