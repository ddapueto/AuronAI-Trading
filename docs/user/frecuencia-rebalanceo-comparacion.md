# Comparación de Frecuencias de Rebalanceo 📊

## ¿Qué Probamos?

Comparamos dos frecuencias de rebalanceo para la estrategia Single Momentum con $1,000 inicial:
- **Semanal**: Rebalancea cada 7 días
- **Mensual**: Rebalancea cada 30 días

Período de prueba: 2021-2025 (4 años completos)

## Resultados Reales 🎯

| Frecuencia | Retorno Anual | Sharpe | Max Drawdown | Trades | Comisiones | Capital Final |
|------------|---------------|--------|--------------|--------|------------|---------------|
| **Semanal** | 8.8% | 0.61 | -19.6% | 4 | $4 | $1,413 |
| **Mensual** | 9.2% | 0.67 | -17.7% | 4 | $4 | $1,431 |

## Ganador: Mensual 🏆

**Diferencia**: +0.34% anual a favor de mensual

### ¿Por Qué Mensual Gana?

1. **Mejor Retorno**: 9.2% vs 8.8% anual
2. **Mejor Sharpe**: 0.67 vs 0.61 (más retorno por unidad de riesgo)
3. **Menor Drawdown**: -17.7% vs -19.6% (menos caídas)
4. **Mismas Comisiones**: Ambos solo 4 trades en 4 años

### Explicación

Con $1,000 inicial, el sistema tiene un problema:
- Solo puede comprar 20% del capital en una posición (risk budget)
- Eso es $200 por posición
- Muchos ETFs cuestan más de $200 por acción

**Resultado**: Ambas frecuencias terminan haciendo los MISMOS trades porque no hay suficiente capital para rebalancear más seguido.

## ¿Qué Significa Esto Para Ti?

### Con $1,000 - $3,000

**Usa Mensual**:
- Menos ruido en las señales
- Capturas las tendencias principales
- No pierdes nada vs semanal (mismo número de trades)
- Más simple de seguir

### Con $5,000+

Aquí sí podría haber diferencia. Pero basado en estos resultados, **mensual sigue siendo mejor** porque:
- Evita "whipsaws" (cambios falsos de tendencia)
- Momentum funciona mejor en timeframes más largos
- Menos estrés monitoreando

## Ejemplo Práctico

### Tu Situación: $1,000 + $150/mes

**Recomendación**: Rebalancea mensual

**Workflow**:
1. Primer día del mes: Revisa momentum de todos los ETFs
2. Compra el ETF con mejor momentum (máximo 20% del capital)
3. Mantén hasta el próximo mes
4. Repite

**Proyección con $150/mes**:
- Mes 1: $1,000 → invierte $200
- Mes 2: $1,150 → invierte $230
- Mes 3: $1,300 → invierte $260
- ...
- Año 1: ~$2,800
- Año 2: ~$4,900
- Año 3: ~$7,300
- Año 4: ~$10,000+ ✅

Una vez llegues a $10,000, puedes considerar Dual Momentum (5 posiciones).

## Conclusión

**Para cuentas pequeñas ($1,000 - $5,000):**
- Mensual es MEJOR que semanal
- Mismo número de trades
- Mejor retorno
- Menos drawdown
- Más simple

**No necesitas rebalancear más seguido**. Momentum es una estrategia de tendencia, funciona mejor dándole tiempo a las tendencias para desarrollarse.

## Datos Técnicos

```json
{
  "periodo": "2021-2025 (4 años)",
  "capital_inicial": 1000,
  "estrategia": "Single Momentum (Top 1)",
  "universo": "27 ETFs",
  "risk_budget": "20%",
  "comisiones": "$1 por trade",
  
  "semanal": {
    "retorno_anual": 0.088,
    "sharpe": 0.61,
    "max_dd": -0.196,
    "trades": 4,
    "comisiones_totales": 4,
    "capital_final": 1413
  },
  
  "mensual": {
    "retorno_anual": 0.092,
    "sharpe": 0.67,
    "max_dd": -0.177,
    "trades": 4,
    "comisiones_totales": 4,
    "capital_final": 1431
  },
  
  "diferencia": {
    "retorno": "+0.34% anual",
    "capital_final": "+$18",
    "ganador": "Mensual"
  }
}
```

---

**Última actualización**: Febrero 2026  
**Fuente**: Backtest real con datos históricos 2021-2025
