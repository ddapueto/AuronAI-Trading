# ADR-008: Comparación de Metodologías de Estrategia Swing

## Estado
Propuesto

## Contexto

Tenemos dos implementaciones de la estrategia swing con diferencias fundamentales en su metodología:

### Metodología 1: Original (SwingNoSLStrategy)
- **Rebalanceo**: DIARIO - intenta llenar el portfolio cada día
- **Trades**: 113 trades en 7 meses
- **Return**: 5.58%
- **Sharpe**: 0.92
- **Max DD**: -3.24%
- **Lógica**: Busca activamente nuevas posiciones cada día, mantiene hasta TP o TimeExit

### Metodología 2: Actual (SwingTPStrategy con BacktestRunner)
- **Rebalanceo**: Cada 7 días (holding_days)
- **Trades**: 80 trades en 7 meses
- **Return**: 0.03%
- **Sharpe**: 1.00
- **Max DD**: -0.02%
- **Lógica**: Rebalancea completamente cada 7 días, cierra todas las posiciones y abre nuevas

## Análisis para Trading Real

### Ventajas Metodología 1 (Rebalanceo Diario)

**Pros:**
1. **Mayor adaptabilidad**: Responde rápido a cambios de mercado
2. **Mejor aprovechamiento de oportunidades**: Puede entrar en nuevas posiciones cuando hay espacio
3. **Más trades = más datos**: 113 trades dan más confianza estadística
4. **Return superior**: 5.58% vs 0.03%
5. **Realista para swing trading**: Los traders reales buscan oportunidades constantemente

**Contras:**
1. **Más comisiones**: 113 trades × 2 (entrada/salida) = 226 operaciones
2. **Más tiempo de monitoreo**: Requiere revisar el mercado diariamente
3. **Mayor complejidad de ejecución**: Más decisiones diarias
4. **Posible overtrading**: Riesgo de entrar en posiciones subóptimas

### Ventajas Metodología 2 (Rebalanceo Periódico)

**Pros:**
1. **Menos comisiones**: 80 trades vs 113 (-29%)
2. **Más simple de ejecutar**: Solo revisar cada 7 días
3. **Menos estrés**: No requiere monitoreo diario
4. **Sharpe ligeramente mejor**: 1.00 vs 0.92 (más consistente)
5. **Drawdown menor**: -0.02% vs -3.24% (mucho más conservador)

**Contras:**
1. **Return muy bajo**: 0.03% es prácticamente 0%
2. **Pierde oportunidades**: No puede entrar en nuevas posiciones entre rebalanceos
3. **Menos realista**: Los traders swing no esperan 7 días para actuar
4. **Cierra posiciones ganadoras prematuramente**: Al rebalancear, cierra TODO

## Decisión

**Para trading real, la Metodología 1 (Rebalanceo Diario) es SUPERIOR** por las siguientes razones:

### 1. Return Real
- 5.58% en 7 meses es ~9.5% anualizado
- 0.03% es prácticamente no hacer nada
- En trading real, necesitas generar returns para justificar el riesgo

### 2. Filosofía de Swing Trading
El swing trading se basa en:
- Capturar movimientos de 3-10 días
- Entrar cuando hay oportunidad (no esperar 7 días)
- Mantener posiciones hasta que se cumpla el objetivo
- Buscar activamente las mejores oportunidades

La Metodología 2 contradice estos principios al:
- Forzar rebalanceos cada 7 días
- Cerrar posiciones ganadoras prematuramente
- No permitir entradas entre rebalanceos

### 3. Gestión de Riesgo Real
Aunque el drawdown de -3.24% es mayor que -0.02%, es:
- Totalmente manejable (< 5%)
- Realista para swing trading
- Compensado por el return 186x superior

### 4. Costos de Transacción
Sí, 113 trades generan más comisiones, pero:
- Con comisiones de $1-2 por trade: ~$226-452 total
- Return de 5.58% en $100k = $5,580
- Comisiones = 4-8% del profit (aceptable)
- Return neto sigue siendo ~5%

### 5. Ejecución Práctica
En trading real:
- Revisar el mercado diariamente es NORMAL
- Los traders swing activos monitorean posiciones diariamente
- Esperar 7 días sin hacer nada es poco práctico
- Las oportunidades no esperan

## Recomendación Final

**Usar Metodología 1 (Rebalanceo Diario) con las siguientes mejoras:**

1. **Mantener la lógica de entrada diaria**
   - Buscar nuevas posiciones cada día
   - Llenar el portfolio hasta top_k
   - No forzar cierres prematuros

2. **Mejorar la gestión de salidas**
   - TP: 5% (mantener)
   - Time Exit: 7-10 días (mantener)
   - Considerar trailing stop para proteger ganancias

3. **Optimizar costos**
   - Usar broker con comisiones bajas ($0-1 por trade)
   - Considerar aumentar TP a 6-7% para reducir trades
   - Filtrar entradas con volumen mínimo

4. **Monitoreo realista**
   - Revisar posiciones 1-2 veces al día
   - Automatizar alertas de TP
   - No requiere monitoreo 24/7

## Implementación

Necesitamos arreglar SwingTPStrategy para que:
1. Genere señales DIARIAMENTE (no cada 7 días)
2. AGREGUE posiciones nuevas (no cierre todo)
3. Solo cierre por TP o TimeExit
4. Mantenga sincronización entre strategy.open_positions y runner.positions

## Consecuencias

### Positivas
- Return realista y atractivo (~9.5% anual)
- Metodología probada en trading real
- Mejor aprovechamiento de oportunidades
- Más datos para validar la estrategia

### Negativas
- Requiere monitoreo diario
- Más comisiones (pero justificadas)
- Mayor complejidad de implementación
- Drawdown ligeramente mayor (pero manejable)

## Alternativas Consideradas

### Alternativa A: Híbrido (Rebalanceo cada 3 días)
- Compromiso entre ambas metodologías
- Menos trades que diario, más que semanal
- **Rechazada**: No resuelve el problema fundamental de cerrar posiciones prematuramente

### Alternativa B: Mantener Metodología 2 pero aumentar holding_days
- Rebalancear cada 14-21 días
- Menos trades, más tiempo por posición
- **Rechazada**: Return seguiría siendo bajo, pierde más oportunidades

### Alternativa C: Metodología 2 con "top-up" diario
- Rebalanceo completo cada 7 días
- Agregar posiciones diariamente sin cerrar
- **Considerada**: Similar a Metodología 1, pero más compleja

## Referencias

- Original script: `src/auronai/backtesting/swing_no_sl_strategy.py`
- Implementación actual: `src/auronai/strategies/swing_tp.py`
- Resultados comparativos: `test_swing_comparison.py`

## Fecha
2026-02-13
