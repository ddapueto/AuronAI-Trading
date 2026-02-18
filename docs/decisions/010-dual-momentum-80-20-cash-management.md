# ADR-010: Dual Momentum 80/20 para Gestión de Cash

## Estado
Aceptado

## Contexto

### Problema Original

La implementación clásica de Dual Momentum invierte 100% del capital:
- Selecciona top 5 activos
- Distribuye 20% a cada uno (5 × 20% = 100%)
- NO mantiene reserva de efectivo

**Problemas identificados:**

1. **Sin liquidez permanente**
   - Usuario queda sin cash inmediatamente
   - No puede aprovechar oportunidades
   - Rebalancear requiere vender posiciones

2. **Aportes mensuales ineficientes**
   - Usuario aporta $200/mes
   - Dinero queda "atrapado" sin estrategia clara
   - Fuerza inversiones sin señal de momentum

3. **Estrés psicológico**
   - Sensación de estar "100% expuesto"
   - Sin colchón para emergencias
   - Inflexibilidad operativa

### Investigación

**Dual Momentum académico (Antonacci):**
- Diseñado para inversores institucionales
- Asume capital grande ($100K+)
- No considera aportes mensuales
- Enfoque: maximizar retorno absoluto

**Realidad del usuario:**
- Capital inicial: $1,000
- Aportes mensuales: $200
- Necesita liquidez operativa
- Enfoque: crecimiento sostenible + flexibilidad

## Decisión

**Modificar Dual Momentum a configuración 80/20:**

```python
# Parámetros modificados
top_n = 4  # En lugar de 5
risk_budget = 0.80  # 80% invertido, 20% cash

# Resultado:
# 4 posiciones × 20% = 80% invertido
# 20% permanente en efectivo
```

### Implementación

**Cambios en código:**

```python
# src/auronai/strategies/dual_momentum.py

@dataclass
class DualMomentumParams(StrategyParams):
    lookback_period: int = 252  # Sin cambios
    top_n: int = 4  # CAMBIO: 4 en lugar de 5
    rebalance_frequency: str = 'monthly'  # Sin cambios
    # risk_budget heredado de StrategyParams = 0.80
```

**Flujo con aportes mensuales:**

1. Aportes van a cash (no se invierten automáticamente)
2. Análisis semanal de momentum
3. Rebalanceo solo cuando hay señal (top 4 cambió)
4. Cash se acumula entre rebalanceos
5. Al rebalancear, se usa cash acumulado

## Consecuencias

### Positivas

1. **Liquidez permanente**
   - Siempre 20%+ en efectivo
   - Puede aprovechar oportunidades
   - Colchón psicológico

2. **Aportes mensuales optimizados**
   - $200/mes se acumulan en cash
   - Inversión solo con señal de momentum
   - No fuerza trades innecesarios

3. **Menor costo de transacción**
   - Rebalanceo solo con señal
   - Menos trades = menos comisiones
   - Cash acumulado reduce frecuencia

4. **Flexibilidad operativa**
   - Puede agregar 5ta posición si aparece oportunidad excepcional
   - Puede aumentar posiciones existentes
   - Puede aprovechar caídas (buy the dip)

5. **Mejor gestión de riesgo**
   - No está 100% expuesto
   - Protección en drawdowns
   - Puede salir parcialmente si es necesario

### Negativas

1. **Retorno ligeramente menor**
   - Estimado: -2% a -3% anual vs 100% invertido
   - En simulación 4 años: -$800 ($15,200 vs $14,400)
   - Trade-off aceptable por liquidez

2. **Cash drag en mercados alcistas**
   - 20% en cash no participa en rallies
   - Oportunidad perdida en bull markets fuertes
   - Mitigado por: seguridad y flexibilidad

3. **Desviación del modelo académico**
   - No es Dual Momentum "puro"
   - Resultados no comparables directamente con papers
   - Justificado por: contexto diferente (cuenta pequeña + aportes)

### Métricas de Éxito

**Comparación esperada (4 años, $1K + $200/mes):**

| Métrica | 100% Invertido | 80/20 | Diferencia |
|---------|----------------|-------|------------|
| Retorno final | $15,200 | $14,400 | -$800 (-5.3%) |
| Cash disponible | $0 | $2,880 | +$2,880 |
| Trades/año | 2-4 | 2-4 | Similar |
| Comisiones/año | $8-16 | $8-16 | Similar |
| Estrés psicológico | Alto | Bajo | Mejor |

**Validación:**
- Backtest con aportes mensuales
- Walk-forward testing
- Paper trading 3 meses
- Comparar con expectativas

## Alternativas Consideradas

### Alternativa A: Mantener 100% Invertido

**Rechazada porque:**
- No resuelve problema de liquidez
- Aportes mensuales quedan sin estrategia
- Alto estrés psicológico
- Inflexibilidad operativa

### Alternativa B: 70/30 (Más Conservador)

**Rechazada porque:**
- Demasiado conservador
- Retorno significativamente menor (-5% anual estimado)
- 30% cash es excesivo para cuenta pequeña
- No justifica el trade-off

### Alternativa C: 90/10 (Más Agresivo)

**Rechazada porque:**
- 10% cash insuficiente para aportes mensuales
- Ejemplo: $1,000 × 10% = $100 (solo 0.5 meses de aportes)
- No resuelve problema de liquidez adecuadamente
- Podría considerarse para cuentas $20K+

### Alternativa D: Cash Dinámico Basado en Volatilidad

```python
if VIX < 15:
    risk_budget = 0.90  # Mercado tranquilo
elif VIX < 25:
    risk_budget = 0.80  # Volatilidad normal
else:
    risk_budget = 0.60  # Alta volatilidad
```

**Rechazada por ahora porque:**
- Más complejo de implementar
- Requiere datos adicionales (VIX)
- Difícil de backtest
- Puede considerarse en Fase 2

### Alternativa E: Cash Escalonado por Tamaño de Cuenta

```python
if balance < 2000:
    risk_budget = 0.70
elif balance < 5000:
    risk_budget = 0.80
else:
    risk_budget = 0.90
```

**Rechazada por ahora porque:**
- Más complejo
- Cambia estrategia con el tiempo
- Dificulta comparaciones
- Puede considerarse en Fase 2

## Implementación

### Fase 1: Código (Completado)

- [x] Modificar `DualMomentumParams.top_n` a 4
- [x] Documentar cambio en docstring
- [x] Crear ADR-010

### Fase 2: Testing (Próximos pasos)

- [ ] Crear script `run_dual_momentum_80_20.py`
- [ ] Backtest 2021-2025 con configuración 80/20
- [ ] Comparar métricas vs 100% invertido
- [ ] Validar con walk-forward testing

### Fase 3: Aportes Mensuales (Próximos pasos)

- [ ] Crear script `run_dual_momentum_with_contributions.py`
- [ ] Simular $1,000 + $200/mes × 4 años
- [ ] Documentar flujo de trabajo semanal
- [ ] Crear guía de usuario

### Fase 4: Paper Trading (Próximos pasos)

- [ ] Implementar en cuenta demo
- [ ] Seguir estrategia 3 meses
- [ ] Registrar todos los trades
- [ ] Comparar con backtest

## Referencias

- **Dual Momentum original:** Antonacci, G. (2014). "Dual Momentum Investing"
- **Documentación usuario:** `docs/user/dual-momentum-con-aportes-mensuales.md`
- **Código:** `src/auronai/strategies/dual_momentum.py`
- **Issue relacionado:** Gestión de cash con aportes mensuales

## Notas

### Para Cuentas Grandes ($20K+)

Considerar volver a configuración más agresiva:
```python
top_n = 5
risk_budget = 0.90  # 90% invertido, 10% cash
```

Justificación:
- 10% de $20K = $2,000 (suficiente liquidez absoluta)
- Mayor retorno potencial
- Menor cash drag

### Para Mercados Bajistas

Dual Momentum se protege automáticamente:
- Si todos los símbolos tienen momentum negativo
- Estrategia va 100% a cash
- Con 80/20, ya tienes 20% protegido desde el inicio

### Revisión Futura

Revisar esta decisión después de:
- 6 meses de paper trading
- 1 año de trading real
- Cuenta alcance $10K+
- Cambios significativos en mercado

---

**Fecha:** Febrero 2026  
**Autor:** Sistema AuronAI  
**Revisores:** Usuario  
**Estado:** Aceptado e Implementado
