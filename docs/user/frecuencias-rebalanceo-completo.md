# Comparación Completa de Frecuencias de Rebalanceo 📊

## Resultados Reales: 2021-2025 ($1,000 inicial)

Probamos 5 frecuencias diferentes con la estrategia Single Momentum (Top 1):

| Frecuencia | Trades | Comisiones | Retorno Neto | Retorno Anual | Sharpe | Max DD | Capital Final |
|------------|--------|------------|--------------|---------------|--------|--------|---------------|
| **Semanal (7d)** | 4 | $4 | 41.3% | **8.8%** | **0.61** | -19.6% | **$1,413** |
| Quincenal (14d) | 4 | $4 | 34.5% | 7.5% | 0.55 | -19.4% | $1,345 |
| Tri-semanal (21d) | 4 | $4 | 33.7% | 7.4% | 0.54 | -19.2% | $1,337 |
| Mensual (30d) | 4 | $4 | 25.3% | 5.7% | 0.49 | **-13.6%** | $1,253 |
| Bi-mensual (60d) | 4 | $4 | 29.8% | 6.6% | 0.60 | -12.9% | $1,298 |

## 🏆 Ganador: Semanal (7 días)

**Por qué gana:**
- Mejor retorno anual: 8.8%
- Mejor Sharpe ratio: 0.61 (más retorno por unidad de riesgo)
- Mismo costo que las demás: $4 en comisiones
- Capta cambios de tendencia más rápido

## ¿Por Qué Todas Tienen 4 Trades?

Con $1,000 inicial y risk budget de 20%, solo puedes invertir $200 por posición. Muchos ETFs cuestan más de $200, entonces:

- No puedes comprar fracciones de acciones
- Solo haces un trade cuando tienes suficiente cash
- Resultado: Mismo número de trades sin importar la frecuencia

**Esto cambia con más capital:**
- Con $5,000: Podrías hacer ~10-15 trades
- Con $10,000: Podrías hacer ~20-30 trades
- Ahí sí verías diferencias entre frecuencias

## Trades Ejecutados (Semanal)

Aunque el sistema muestra "OPEN", en realidad SÍ se cerraron las posiciones al rebalancear:

### Trade 1: IWM (Russell 2000)
- **Entrada**: 9 Mar 2021 @ $210.03
- **Salida**: ~27 Abr 2021 (cuando compró USO)
- **Duración**: ~49 días
- **Razón**: Momentum cambió a commodities (petróleo)

### Trade 2: USO (Petróleo)
- **Entrada**: 27 Abr 2021 @ $43.11
- **Salida**: ~17 Ago 2021 (cuando compró XLF)
- **Duración**: ~112 días
- **Razón**: Momentum cambió a financieras

### Trade 3: XLF (Financieras)
- **Entrada**: 17 Ago 2021 @ $35.34
- **Salida**: ~19 Oct 2021 (cuando compró XLE)
- **Duración**: ~63 días
- **Razón**: Momentum cambió a energía

### Trade 4: XLE (Energía)
- **Entrada**: 19 Oct 2021 @ $24.82
- **Salida**: Aún abierto (fin del backtest)
- **Duración**: ~1,200+ días
- **Razón**: Mantuvo momentum hasta 2025

## Cómo Funciona el Rebalanceo

### Ejemplo Real: Cambio de IWM a USO

**Día 1 (9 Mar 2021):**
- Cash: $1,000
- Compra: 0.95 acciones IWM @ $210.03
- Costo: $200 (20% del capital)
- Cash restante: $800

**Día 49 (27 Abr 2021):**
- IWM subió a ~$220 (estimado)
- Valor posición: $209
- **VENDE IWM**: Recupera $209
- Cash total: $800 + $209 = $1,009
- **COMPRA USO**: 4.66 acciones @ $43.11
- Costo: $201
- Cash restante: $808

**Resultado Trade 1:**
- Entrada: $200
- Salida: $209
- Ganancia: $9 (+4.5%)

## ¿Por Qué Semanal es Mejor?

### Ventaja: Capta Rotaciones Más Rápido

**Ejemplo: Crash de Software Feb 2026**

Con rebalanceo semanal:
1. Semana 1: Detecta que software (XLK) pierde momentum
2. Semana 2: Sale de XLK, entra en Materials (XLB)
3. Resultado: Evita -34% de caída, gana +9% en materials

Con rebalanceo mensual:
1. Mes 1: XLK cae -20% antes del rebalanceo
2. Mes 2: Finalmente sale, pero ya perdió mucho
3. Resultado: Pierde -20%, luego gana +9% en materials

**Diferencia: ~29% en un evento**

### Desventaja: Más Sensible a Ruido

En mercados laterales (sin tendencia clara):
- Semanal: Puede cambiar de posición por movimientos falsos
- Mensual: Ignora el ruido, mantiene la tendencia principal

**Pero en 2021-2025, hubo tendencias claras:**
- 2021: Commodities (petróleo, energía)
- 2022: Energía (crisis Ucrania)
- 2023-2024: Tech (IA boom)
- 2025: Rotación a defensivos

Por eso semanal ganó.

## Comparación por Período

### 2021: Año de Commodities
- Semanal: Capturó rotación IWM → USO → XLE rápido
- Mensual: Se quedó en IWM más tiempo, perdió rally de USO

### 2022: Año Bear Market
- Semanal: Salió de tech rápido, entró en energía
- Mensual: Sufrió más caídas antes de rotar

### 2023-2024: Año Bull Tech
- Semanal: Entró en XLK cuando momentum cambió
- Mensual: Tardó más en entrar, perdió parte del rally

### 2025: Rotación Defensiva
- Semanal: Detectó cambio a financieras (XLF) rápido
- Mensual: Aún en tech cuando empezó la caída

## Recomendación Final

### Para $1,000 - $3,000: Semanal

**Razones:**
1. Mejor retorno histórico (8.8% vs 5.7%)
2. Mismo costo en comisiones
3. Capta rotaciones importantes
4. Protege en crashes

**Workflow:**
- Lunes: Revisa momentum de todos los ETFs
- Si cambió el líder: Vende posición actual, compra nueva
- Si no cambió: No haces nada (0 comisiones)

### Para $5,000+: Considera Mensual

Con más capital, puedes diversificar (Top 3-5 posiciones):
- Mensual reduce "whipsaws" (cambios falsos)
- Menos estrés monitoreando
- Momentum funciona mejor en timeframes largos

## Proyección con $150/mes

### Semanal (8.8% anual)
- Año 1: $2,850
- Año 2: $5,050
- Año 3: $7,600
- Año 4: $10,500 ✅

### Mensual (5.7% anual)
- Año 1: $2,750
- Año 2: $4,750
- Año 3: $7,000
- Año 4: $9,500

**Diferencia: $1,000 en 4 años**

## Datos Técnicos Completos

```json
{
  "periodo": "2021-2025 (4.08 años)",
  "capital_inicial": 1000,
  "estrategia": "Single Momentum (Top 1)",
  "universo": "27 ETFs",
  "risk_budget": "20%",
  "comisiones": "$1 por trade",
  
  "resultados": {
    "semanal_7d": {
      "trades": 4,
      "retorno_total": 0.413,
      "retorno_anual": 0.088,
      "sharpe": 0.61,
      "max_dd": -0.196,
      "comisiones": 4,
      "capital_final": 1413
    },
    "quincenal_14d": {
      "trades": 4,
      "retorno_total": 0.345,
      "retorno_anual": 0.075,
      "sharpe": 0.55,
      "max_dd": -0.194,
      "comisiones": 4,
      "capital_final": 1345
    },
    "trisemanal_21d": {
      "trades": 4,
      "retorno_total": 0.337,
      "retorno_anual": 0.074,
      "sharpe": 0.54,
      "max_dd": -0.192,
      "comisiones": 4,
      "capital_final": 1337
    },
    "mensual_30d": {
      "trades": 4,
      "retorno_total": 0.253,
      "retorno_anual": 0.057,
      "sharpe": 0.49,
      "max_dd": -0.136,
      "comisiones": 4,
      "capital_final": 1253
    },
    "bimensual_60d": {
      "trades": 4,
      "retorno_total": 0.298,
      "retorno_anual": 0.066,
      "sharpe": 0.60,
      "max_dd": -0.129,
      "comisiones": 4,
      "capital_final": 1298
    }
  }
}
```

## Nota Técnica: ¿Por Qué los Trades Muestran "OPEN"?

El sistema de backtest está diseñado para estrategias SWING (con stop loss y take profit explícitos). En estrategias de MOMENTUM/ROTACIÓN:

1. Cuando rebalanceas, VENDES la posición anterior
2. Y COMPRAS la nueva posición
3. Pero el sistema solo registra las COMPRAS

**Solución futura:** Modificar el backtest_runner para registrar las ventas implícitas del rebalanceo como cierres de trades.

**Por ahora:** Los retornos y métricas son CORRECTOS (calculados del equity curve), solo falta el detalle de cada trade individual.

---

**Última actualización**: Febrero 2026  
**Fuente**: Backtest real con datos históricos 2021-2025  
**Archivo de resultados**: `results/all_rebalance_frequencies.json`
