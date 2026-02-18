# 💰 Costos y Presupuesto de AuronAI

## Resumen Ejecutivo

```
Costo Mínimo para Empezar: $0 (modo demo)
Costo Mensual Típico: $5-50 (dependiendo del uso)
Capital Recomendado: $1,000-10,000
```

---

## 📊 Desglose de Costos

### 1. Software y Herramientas (GRATIS)

```
✅ Python: GRATIS
✅ AuronAI (este sistema): GRATIS (open source)
✅ yfinance (datos de mercado): GRATIS
✅ pandas, numpy, matplotlib: GRATIS
✅ Alpaca Paper Trading: GRATIS
✅ Demo Mode (sin internet): GRATIS

Total: $0/mes
```

---

### 2. APIs y Servicios

#### Claude API (Anthropic) - Análisis AI

**Modelo: Claude 3.5 Sonnet**

```
Precio por análisis:
├─ Input:  ~1,000 tokens × $3/1M tokens = $0.003
├─ Output: ~500 tokens × $15/1M tokens = $0.0075
└─ Total por análisis: ~$0.01

Uso según modo:
├─ Swing Trading:    1-3 análisis/día × 20 días = 20-60/mes
├─ Day Trading:      10-30 análisis/día × 20 días = 200-600/mes
├─ Híbrido:          5-10 análisis/día × 20 días = 100-200/mes
└─ Auto:             20-50 análisis/día × 20 días = 400-1000/mes

Costo mensual:
├─ Swing Trading:    $0.20 - $0.60
├─ Day Trading:      $2.00 - $6.00
├─ Híbrido:          $1.00 - $2.00
└─ Auto:             $4.00 - $10.00
```

**Alternativa: Sin Claude API**
- Sistema funciona con análisis rule-based
- Costo: $0
- Calidad: Buena pero menos sofisticada

#### Yahoo Finance (yfinance) - Datos de Mercado

```
Costo: GRATIS
Límites: Ninguno oficial (uso razonable)
Confiabilidad: Alta para datos diarios, media para intradiarios
```

#### Alpaca API - Ejecución de Trades

**Paper Trading (Simulado)**
```
Costo: GRATIS
Límites: Ilimitado
Datos: Tiempo real
Ideal para: Aprender y probar estrategias
```

**Live Trading (Real)**
```
Costo de cuenta: GRATIS
Comisiones: $0 (sin comisiones en acciones)
Mínimo de cuenta: $0 (pero recomendado $1,000+)
Rate limits: 200 requests/minuto

Costos ocultos:
├─ Spread bid-ask: ~$0.01-0.05 por acción
└─ Slippage: ~0.1-0.5% en market orders
```

---

### 3. Costos por Modo de Trading

#### Modo 1: Swing Trading

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COSTOS MENSUALES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Claude API:
├─ 2 análisis/día × 20 días = 40 análisis
└─ 40 × $0.01 = $0.40/mes

Alpaca Paper Trading:
└─ GRATIS

Alpaca Live Trading:
├─ Comisiones: $0
├─ Spread (estimado): 2 trades/semana × 8 semanas × $0.02 = $0.32
└─ Total: $0.32/mes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL MENSUAL: $0.72 (con Claude) o $0.32 (sin Claude)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Capital recomendado: $1,000 - $5,000
Tiempo requerido: 15 min/día
```

#### Modo 2: Day Trading

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COSTOS MENSUALES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Claude API:
├─ 20 análisis/día × 20 días = 400 análisis
└─ 400 × $0.01 = $4.00/mes

Alpaca Live Trading:
├─ Comisiones: $0
├─ Spread: 3 trades/día × 20 días × $0.03 = $1.80
└─ Total: $1.80/mes

Datos en Tiempo Real (opcional):
├─ Alpaca: Incluido GRATIS
└─ Alternativa premium: $10-50/mes (no necesario)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL MENSUAL: $5.80 (con Claude) o $1.80 (sin Claude)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Capital recomendado: $5,000 - $25,000
Tiempo requerido: 4-6 horas/día
Requisito PDT: $25,000 (si haces >3 day trades/semana en USA)
```

**⚠️ Pattern Day Trader (PDT) Rule (USA)**
```
Si tienes < $25,000 en cuenta:
└─ Máximo 3 day trades en 5 días hábiles
   (day trade = comprar y vender mismo día)

Si tienes ≥ $25,000:
└─ Day trades ilimitados

Solución para < $25,000:
├─ Usar swing trading (mantener >1 día)
├─ Usar cash account (no margin)
└─ O usar broker internacional (sin PDT rule)
```

#### Modo 3: Híbrido

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COSTOS MENSUALES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Claude API:
├─ Análisis diario: 1/día × 20 = 20
├─ Análisis intradiario: 5/día × 20 = 100
├─ Total: 120 análisis
└─ 120 × $0.01 = $1.20/mes

Alpaca Live Trading:
├─ Comisiones: $0
├─ Spread: 1.5 trades/día × 20 días × $0.025 = $0.75
└─ Total: $0.75/mes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL MENSUAL: $1.95 (con Claude) o $0.75 (sin Claude)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Capital recomendado: $2,000 - $10,000
Tiempo requerido: 2-3 horas/día
```

#### Modo 4: Totalmente Automatizado

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COSTOS MENSUALES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Claude API:
├─ 30 análisis/día × 20 días = 600 análisis
└─ 600 × $0.01 = $6.00/mes

Alpaca Live Trading:
├─ Comisiones: $0
├─ Spread: 4 trades/día × 20 días × $0.03 = $2.40
└─ Total: $2.40/mes

Servidor/VPS (para correr 24/7):
├─ Opción 1: Tu computadora (GRATIS pero debe estar encendida)
├─ Opción 2: AWS EC2 t3.micro: ~$8/mes
├─ Opción 3: DigitalOcean Droplet: ~$6/mes
└─ Opción 4: Raspberry Pi: $50 one-time (luego ~$2/mes electricidad)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL MENSUAL: 
├─ Con tu PC: $8.40 (con Claude) o $2.40 (sin Claude)
├─ Con VPS: $14.40 - $16.40
└─ Con Raspberry Pi: $10.40 (después del primer mes: $8.40)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Capital recomendado: $5,000 - $25,000
Tiempo requerido: 0 min/día (solo monitoreo semanal)
```

---

## 📊 Tabla Comparativa de Costos

| Concepto | Swing | Day | Híbrido | Auto |
|----------|-------|-----|---------|------|
| **APIs** |
| Claude API | $0.40 | $4.00 | $1.20 | $6.00 |
| yfinance | GRATIS | GRATIS | GRATIS | GRATIS |
| Alpaca Paper | GRATIS | GRATIS | GRATIS | GRATIS |
| **Trading Real** |
| Comisiones | $0 | $0 | $0 | $0 |
| Spread/Slippage | $0.32 | $1.80 | $0.75 | $2.40 |
| **Infraestructura** |
| Servidor/VPS | - | - | - | $0-8 |
| **TOTAL/MES** |
| Con Claude | $0.72 | $5.80 | $1.95 | $8.40-16.40 |
| Sin Claude | $0.32 | $1.80 | $0.75 | $2.40-10.40 |
| **Capital Mínimo** | $1,000 | $5,000 | $2,000 | $5,000 |
| **Capital Ideal** | $5,000 | $25,000 | $10,000 | $25,000 |

---

## 💡 Escenarios de Presupuesto

### Presupuesto Mínimo ($0/mes)

```
Configuración:
├─ Modo: Swing Trading
├─ Claude API: NO (usar análisis rule-based)
├─ Trading: Paper Trading (simulado)
├─ Capital: $0 (solo práctica)
└─ Costo: $0/mes

Ideal para:
✅ Aprender el sistema
✅ Probar estrategias
✅ Ganar confianza
✅ Sin riesgo financiero
```

### Presupuesto Bajo ($1-5/mes)

```
Configuración:
├─ Modo: Swing Trading
├─ Claude API: SÍ ($0.40/mes)
├─ Trading: Live con capital pequeño ($1,000)
├─ Trades: 2-3/semana
└─ Costo: ~$0.72/mes

Retorno esperado (conservador):
├─ 2% mensual = $20/mes
└─ ROI: 2,777% sobre costo de APIs
```

### Presupuesto Medio ($5-15/mes)

```
Configuración:
├─ Modo: Híbrido
├─ Claude API: SÍ ($1.20/mes)
├─ Trading: Live con capital medio ($5,000)
├─ Trades: 5-8/semana
└─ Costo: ~$1.95/mes

Retorno esperado (conservador):
├─ 3% mensual = $150/mes
└─ ROI: 7,692% sobre costo de APIs
```

### Presupuesto Alto ($15-50/mes)

```
Configuración:
├─ Modo: Auto
├─ Claude API: SÍ ($6.00/mes)
├─ VPS: AWS EC2 ($8/mes)
├─ Trading: Live con capital alto ($25,000)
├─ Trades: 15-20/semana
└─ Costo: ~$16.40/mes

Retorno esperado (conservador):
├─ 4% mensual = $1,000/mes
└─ ROI: 6,098% sobre costo de infraestructura
```

---

## 🎯 Recomendaciones por Capital

### $0 - $500: Solo Aprendizaje

```
✅ Usar: Demo Mode + Paper Trading
✅ Modo: Swing
✅ Claude: Opcional ($0.40/mes)
✅ Objetivo: Aprender sin riesgo
⏱️ Duración: 1-3 meses

Costo: $0-0.40/mes
```

### $500 - $2,000: Empezar Pequeño

```
✅ Usar: Paper Trading → Live pequeño
✅ Modo: Swing
✅ Claude: Recomendado ($0.40/mes)
✅ Position size: 2-5% por trade
⏱️ Duración: 3-6 meses

Costo: $0.72/mes
Retorno esperado: $10-40/mes (2%)
```

### $2,000 - $10,000: Crecimiento

```
✅ Usar: Live Trading
✅ Modo: Swing o Híbrido
✅ Claude: Sí ($0.40-1.20/mes)
✅ Position size: 5-10% por trade
⏱️ Objetivo: Crecimiento consistente

Costo: $0.72-1.95/mes
Retorno esperado: $40-300/mes (2-3%)
```

### $10,000 - $25,000: Serio

```
✅ Usar: Live Trading
✅ Modo: Híbrido o Day Trading
✅ Claude: Sí ($1.20-4.00/mes)
✅ Position size: 10-15% por trade
⏱️ Objetivo: Ingresos suplementarios

Costo: $1.95-5.80/mes
Retorno esperado: $300-1,000/mes (3-4%)
```

### $25,000+: Profesional

```
✅ Usar: Live Trading sin restricciones PDT
✅ Modo: Cualquiera (Day, Híbrido, Auto)
✅ Claude: Sí ($4-6/mes)
✅ VPS: Recomendado si Auto ($8/mes)
✅ Position size: 15-20% por trade
⏱️ Objetivo: Ingresos principales

Costo: $5.80-16.40/mes
Retorno esperado: $1,000-5,000/mes (4-5%)
```

---

## 💰 Costos Ocultos a Considerar

### 1. Impuestos

```
USA:
├─ Short-term gains (< 1 año): Tasa de income tax (10-37%)
├─ Long-term gains (> 1 año): 0-20%
└─ Day trading: Considerado short-term

Otros países: Varía (consulta con contador)

Tip: Mantén registro detallado de todos los trades
```

### 2. Tiempo = Dinero

```
Swing Trading:
├─ 15 min/día × 20 días = 5 horas/mes
└─ Si tu hora vale $50 → $250 de "costo"

Day Trading:
├─ 5 horas/día × 20 días = 100 horas/mes
└─ Si tu hora vale $50 → $5,000 de "costo"

Considera: ¿Vale la pena tu tiempo vs retorno esperado?
```

### 3. Educación y Aprendizaje

```
Cursos de trading: $0-500 (opcional, AuronAI incluye docs)
Libros: $0-100 (opcional)
Tiempo de aprendizaje: 1-6 meses

Inversión recomendada: $0-200
(AuronAI docs son suficientes para empezar)
```

### 4. Psicología y Errores

```
Errores típicos de principiantes:
├─ Overtrading: -10-30% del capital
├─ No usar stops: -20-50% en un mal trade
├─ FOMO (Fear of Missing Out): -5-15%
└─ Revenge trading: -10-40%

Costo estimado de aprendizaje: $100-1,000
(Por eso empezar con paper trading es clave)
```

---

## 📈 ROI Esperado vs Costos

### Escenario Conservador

```
Capital: $5,000
Modo: Swing Trading
Costo mensual: $0.72
Retorno mensual: 2% = $100

ROI sobre costos: 13,889%
ROI sobre capital: 2%
Ganancia neta: $99.28/mes
```

### Escenario Realista

```
Capital: $10,000
Modo: Híbrido
Costo mensual: $1.95
Retorno mensual: 3% = $300

ROI sobre costos: 15,385%
ROI sobre capital: 3%
Ganancia neta: $298.05/mes
```

### Escenario Optimista

```
Capital: $25,000
Modo: Auto
Costo mensual: $16.40
Retorno mensual: 4% = $1,000

ROI sobre costos: 6,098%
ROI sobre capital: 4%
Ganancia neta: $983.60/mes
```

---

## ⚠️ Advertencias Importantes

### 1. No Hay Garantías

```
❌ Estos son retornos ESPERADOS, no garantizados
❌ Puedes perder dinero, especialmente al inicio
❌ Pasado no predice futuro
❌ Mercados pueden ser impredecibles
```

### 2. Gestión de Riesgo es Clave

```
✅ Nunca arriesgues más del 2% por trade
✅ Usa stops siempre
✅ Diversifica (no todo en una acción)
✅ Mantén 20% en cash
```

### 3. Empieza Pequeño

```
✅ Paper trading primero (1-2 meses)
✅ Luego capital pequeño ($500-1,000)
✅ Aumenta gradualmente según resultados
✅ No inviertas dinero que necesites
```

---

## 🎯 Plan de Acción Recomendado

### Mes 1-2: Aprendizaje ($0)

```
1. Instalar AuronAI
2. Configurar paper trading
3. Ejecutar en modo demo
4. Aprender indicadores
5. Probar diferentes modos

Costo: $0
Objetivo: Familiarizarte con el sistema
```

### Mes 3-4: Paper Trading ($0.40/mes)

```
1. Activar Claude API
2. Paper trading con capital simulado ($10,000)
3. Seguir señales religiosamente
4. Registrar todos los trades
5. Evaluar resultados

Costo: $0.40/mes
Objetivo: Probar estrategia sin riesgo
```

### Mes 5-6: Live Pequeño ($0.72/mes + capital)

```
1. Abrir cuenta Alpaca con $1,000
2. Modo swing trading
3. Máximo 2% riesgo por trade
4. Seguir plan estrictamente
5. Evaluar después de 20 trades

Costo: $0.72/mes
Capital: $1,000
Objetivo: Primeros trades reales
```

### Mes 7+: Escalar ($1-16/mes + capital)

```
1. Si resultados positivos → aumentar capital
2. Considerar modo híbrido o day trading
3. Optimizar configuración
4. Posiblemente automatizar

Costo: Variable según modo
Capital: Aumentar gradualmente
Objetivo: Crecimiento sostenible
```

---

## 📊 Resumen Final

```
┌─────────────────────────────────────────────────────────────┐
│                    COSTOS TOTALES                           │
└─────────────────────────────────────────────────────────────┘

Mínimo para empezar: $0 (demo + paper trading)
Recomendado para empezar: $0.40/mes (con Claude)
Costo típico mensual: $1-5/mes
Capital recomendado: $1,000-5,000 para empezar

ROI sobre costos de APIs: 2,000-15,000%
(Los costos de APIs son insignificantes vs retornos potenciales)

El verdadero costo es tu TIEMPO y DISCIPLINA.
```

---

**¿Preguntas sobre costos? Revisa la [FAQ](FAQ.md) o consulta la documentación técnica.** 💰📈
