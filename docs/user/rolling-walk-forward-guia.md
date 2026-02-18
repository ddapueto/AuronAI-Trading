# Guía de Rolling Walk-Forward Optimization

## ¿Qué es Rolling Walk-Forward?

Rolling walk-forward es una técnica de validación que simula cómo operarías en la vida real:

1. **Optimizas parámetros** usando datos históricos (ej: últimos 6 meses)
2. **Operas con esos parámetros** durante un período (ej: 1 semana)
3. **Re-optimizas** la siguiente semana con datos actualizados
4. **Repites** este proceso durante todo el período de prueba

## ¿Por qué es importante?

### Problema con Backtest Simple

```
❌ Backtest Simple:
   Optimizas: 2020-2023 (una sola vez)
   Pruebas:   2024-2025 (parámetros fijos)
   
   Problema: Los parámetros de 2020 pueden no funcionar en 2024
```

### Solución: Rolling Walk-Forward

```
✅ Rolling Walk-Forward:
   Semana 1: Optimizas con Oct-Dic 2023 → Operas Ene 1-7, 2024
   Semana 2: Optimizas con Oct 2023-Ene 7 → Operas Ene 8-14, 2024
   Semana 3: Optimizas con Oct 2023-Ene 14 → Operas Ene 15-21, 2024
   ...
   
   Ventaja: Parámetros siempre actualizados, como en trading real
```

## Cómo Usar

### 1. Test Rápido (Recomendado Primero)

```bash
python scripts/test_rolling_walk_forward.py
```

**Configuración del test**:
- Símbolos: AAPL, MSFT, GOOGL (3 símbolos)
- Período: Enero-Febrero 2024 (2 meses)
- Ventana de entrenamiento: 90 días
- Ventana de prueba: 7 días
- Re-optimización: Semanal
- Tiempo estimado: ~1 minuto

**Qué hace**:
- Genera 6 períodos de optimización
- Prueba 4 combinaciones de parámetros por período
- Total: 24 backtests

### 2. Optimización Completa

```bash
python scripts/run_rolling_walk_forward.py
```

**Configuración completa**:
- Símbolos: AAPL, MSFT, GOOGL, NVDA, TSLA (5 símbolos)
- Período: 2020-2025 (6 años)
- Ventana de entrenamiento: 180 días (6 meses)
- Ventana de prueba: 7 días (1 semana)
- Re-optimización: Semanal
- Tiempo estimado: 1-2 horas

**Qué hace**:
- Genera ~260 períodos (52 semanas × 5 años)
- Prueba 36 combinaciones por período
- Total: ~9,360 backtests

⚠️ **Advertencia**: La optimización completa toma tiempo. Déjala correr durante la noche.

## Interpretando Resultados

### Métricas Clave

#### 1. Sharpe Ratio

```
In-Sample (TRAIN):  2.74
Out-of-Sample (TEST): 1.85 ± 0.45

✅ Bueno: El Sharpe out-of-sample es positivo
```

**Interpretación**:
- **In-Sample**: Rendimiento durante optimización (puede estar inflado)
- **Out-of-Sample**: Rendimiento real esperado (lo que importa)
- **± Desviación**: Variabilidad entre períodos

#### 2. Degradación

```
Degradación: 32.5%

Cálculo: (2.74 - 1.85) / 2.74 = 32.5%
```

**Interpretación**:
- **< 20%**: ✅ Excelente - Estrategia muy robusta
- **20-30%**: ✅ Buena - Estrategia robusta
- **30-40%**: ⚠️ Aceptable - Algo de sobreajuste
- **> 40%**: ❌ Mala - Mucho sobreajuste

**¿Qué significa?**
- Degradación baja = Los parámetros funcionan bien en datos nuevos
- Degradación alta = Los parámetros solo funcionan en datos de entrenamiento

#### 3. Retorno Promedio

```
Avg Test Return: 0.8% por semana
```

**Anualizado**:
```
Retorno anual ≈ 0.8% × 52 semanas = 41.6%
```

⚠️ **Nota**: Este es el retorno promedio por período de prueba (1 semana).

#### 4. Max Drawdown Promedio

```
Avg Test Max DD: -5.2%
```

**Interpretación**:
- Pérdida máxima promedio durante cada período de prueba
- Útil para dimensionar el riesgo

### Frecuencia de Parámetros

```
Parameter Frequency:
  top_k=3: 45 veces (86.5%)
  top_k=2: 7 veces (13.5%)
  holding_days=7: 35 veces (67.3%)
  holding_days=10: 17 veces (32.7%)
```

**Interpretación**:
- **Alta frecuencia (> 50%)**: Parámetro estable, funciona en muchas condiciones
- **Baja frecuencia (< 20%)**: Parámetro inestable, solo funciona en condiciones específicas

**Ejemplo**:
- `top_k=3` se eligió 86.5% del tiempo → Parámetro robusto
- `top_k=2` se eligió 13.5% del tiempo → Menos robusto

## Ejemplo Real

### Escenario

Quieres validar la estrategia Long Momentum antes de operar con dinero real.

### Paso 1: Test Rápido

```bash
python scripts/test_rolling_walk_forward.py
```

**Resultados**:
```
In-Sample:  Sharpe 2.74
Out-of-Sample: Sharpe 1.85 ± 0.45
Degradación: 32.5%
```

**Análisis**:
- ✅ Sharpe out-of-sample positivo (1.85)
- ⚠️ Degradación 32.5% (aceptable pero no excelente)
- ✅ Desviación estándar razonable (0.45)

**Decisión**: Continuar con optimización completa.

### Paso 2: Optimización Completa

```bash
python scripts/run_rolling_walk_forward.py
```

**Resultados** (ejemplo):
```
Total períodos: 260
In-Sample:  Sharpe 2.50
Out-of-Sample: Sharpe 1.75 ± 0.60
Degradación: 30.0%
Avg Return: 0.7% por semana
Avg Max DD: -6.5%
```

**Análisis**:
- ✅ Sharpe consistente (~1.75)
- ✅ Degradación 30% (aceptable)
- ⚠️ Desviación estándar 0.60 (variabilidad moderada)
- ✅ Retorno anualizado ~36%
- ✅ Max DD promedio -6.5% (manejable)

**Decisión**: Estrategia validada, lista para paper trading.

### Paso 3: Paper Trading

Antes de operar con dinero real:
1. Ejecuta la estrategia en paper trading durante 1-2 meses
2. Compara resultados con walk-forward
3. Si coinciden, considera operar con dinero real

## Comparación con Otros Métodos

### 1. Backtest Simple

```
Ventajas:
  ✅ Rápido (minutos)
  ✅ Fácil de entender

Desventajas:
  ❌ Sobreajuste (overfitting)
  ❌ No simula re-optimización
  ❌ Resultados optimistas
```

### 2. Anchored Walk-Forward

```
Ventajas:
  ✅ Detecta overfitting
  ✅ Más realista que backtest simple

Desventajas:
  ⚠️ Ventana de entrenamiento crece indefinidamente
  ⚠️ Datos antiguos pueden no ser relevantes
```

### 3. Rolling Walk-Forward (Recomendado)

```
Ventajas:
  ✅ Simula trading real
  ✅ Ventana de entrenamiento fija (datos recientes)
  ✅ Re-optimización periódica
  ✅ Resultados realistas

Desventajas:
  ⚠️ Lento (horas)
  ⚠️ Computacionalmente intensivo
```

## Preguntas Frecuentes

### ¿Por qué tarda tanto?

Cada período requiere:
- Optimizar: 36 backtests (probar todas las combinaciones)
- Probar: 1 backtest (con mejores parámetros)

Total: 260 períodos × 37 backtests = 9,620 backtests

### ¿Puedo usar menos períodos?

Sí, puedes:
1. Reducir el rango de fechas (ej: 2023-2025 en lugar de 2020-2025)
2. Re-optimizar mensualmente en lugar de semanalmente
3. Usar menos combinaciones de parámetros

**Ejemplo**:
```python
# En scripts/run_rolling_walk_forward.py
config = {
    'start_date': datetime(2023, 1, 1),  # Solo 2 años
    'end_date': datetime(2025, 12, 31),
    'reoptimize_frequency': 'monthly',  # Mensual en lugar de semanal
    'param_grid': {
        'top_k': [3, 4],  # Solo 2 valores en lugar de 4
        'holding_days': [7, 10],  # Solo 2 valores
        'tp_multiplier': [1.05]  # Solo 1 valor
    }
}
```

Esto reduce el tiempo a ~15 minutos.

### ¿Qué degradación es aceptable?

Depende de tu tolerancia al riesgo:

- **Conservador**: < 20% (muy robusto)
- **Moderado**: 20-30% (robusto)
- **Agresivo**: 30-40% (aceptable)
- **Muy agresivo**: > 40% (riesgoso)

### ¿Debo usar los parámetros más frecuentes?

No necesariamente. La frecuencia indica estabilidad, pero:

1. **Parámetros frecuentes**: Funcionan en muchas condiciones (más seguros)
2. **Parámetros infrecuentes**: Pueden funcionar mejor en condiciones específicas

**Recomendación**: Usa parámetros con frecuencia > 30% para mayor robustez.

### ¿Cómo sé si puedo confiar en los resultados?

Verifica:
1. ✅ Degradación < 30%
2. ✅ Sharpe out-of-sample > 1.0
3. ✅ Desviación estándar < 1.0
4. ✅ Parámetros estables (frecuencia > 30%)
5. ✅ Resultados consistentes en diferentes períodos

Si cumple 4-5 criterios, los resultados son confiables.

### ¿Puedo usar esto para otras estrategias?

Sí, el rolling walk-forward funciona con cualquier estrategia:
- Long Momentum
- Short Momentum
- Neutral (Mean Reversion)
- Estrategias personalizadas

Solo necesitas ajustar el `param_grid` según los parámetros de tu estrategia.

## Próximos Pasos

Después de ejecutar rolling walk-forward:

1. **Si degradación < 30%**:
   - ✅ Estrategia validada
   - Continúa con paper trading
   - Considera operar con dinero real

2. **Si degradación 30-40%**:
   - ⚠️ Estrategia aceptable pero mejorable
   - Simplifica parámetros
   - Prueba con más datos
   - Considera paper trading extendido

3. **Si degradación > 40%**:
   - ❌ Estrategia sobreajustada
   - Revisa lógica de la estrategia
   - Reduce número de parámetros
   - Considera estrategia más simple

## Recursos Adicionales

- [Walk-Forward Optimization Explicado](walk-forward-optimization-explicado.md) - Conceptos básicos
- [Anchored vs Rolling](walk-forward-anchored-vs-rolling.md) - Comparación detallada
- [Implementación Técnica](../technical/rolling-walk-forward-implementation.md) - Detalles técnicos
- [Roadmap Estratégico](../decisions/009-roadmap-estrategico-2026.md) - Plan de desarrollo

## Conclusión

Rolling walk-forward es la forma más realista de validar una estrategia de trading. Aunque toma tiempo, los resultados son mucho más confiables que un backtest simple.

**Recuerda**: Los resultados out-of-sample son los que importan. Si tu estrategia tiene buen rendimiento out-of-sample con baja degradación, tienes una estrategia robusta lista para trading real.
