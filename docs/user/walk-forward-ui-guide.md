# Guía de Walk-Forward en la UI

## Acceso Rápido

1. Inicia la aplicación:
```bash
streamlit run main.py
```

2. En el menú lateral, selecciona **"🔄 Walk-Forward"**

## Configuración Paso a Paso

### 1. Estrategia y Símbolos

**Estrategia**:
- `long_momentum`: Solo posiciones largas en mercado alcista
- `short_momentum`: Solo posiciones cortas en mercado bajista
- `neutral`: Mean reversion en mercado neutral

**Símbolos**:
- Selecciona 3-10 símbolos para diversificación
- Recomendado: AAPL, MSFT, GOOGL, NVDA, TSLA

### 2. Período de Análisis

**Fecha Inicio**: Inicio del walk-forward (ej: 2020-01-01)

**Fecha Fin**: Fin del walk-forward (ej: 2025-12-31)

⚠️ **Nota**: Períodos más largos = más confiables pero más lentos

### 3. Ventanas de Optimización

**Ventana de Entrenamiento**:
- Días de datos históricos para optimizar
- Recomendado: 180 días (6 meses)
- Más días = más estable, menos días = más adaptable

**Ventana de Prueba**:
- Días para probar con parámetros optimizados
- Recomendado: 7 días (1 semana)
- Debe coincidir con tu frecuencia de re-optimización real

**Frecuencia de Re-optimización**:
- `weekly`: Re-optimiza cada semana (más realista)
- `monthly`: Re-optimiza cada mes (más rápido)

### 4. Capital y Costos

**Capital Inicial**: $10,000 (ajusta según tu capital real)

**Comisión**: 0% (si usas broker gratuito como Robinhood/Webull)

**Slippage**: 0.05% (realista para acciones líquidas)

### 5. Grid de Parámetros

Define qué valores probar para cada parámetro:

**top_k** (posiciones simultáneas):
- Valores típicos: 2, 3, 4, 5
- Más posiciones = más diversificación

**holding_days** (días de retención):
- Valores típicos: 7, 10, 14
- Más días = menos trades, menos costos

**tp_multiplier** (take profit):
- Valores típicos: 1.03, 1.05, 1.07
- 1.05 = +5% de ganancia objetivo

## Interpretando Resultados

### Métricas Principales

**Sharpe In-Sample vs Out-of-Sample**:
```
In-Sample:  2.74  ← Performance durante optimización
Out-of-Sample: 1.85 ← Performance real esperada
```

**Degradación**:
```
32.5% = (2.74 - 1.85) / 2.74

✅ < 20%: Excelente
✅ 20-30%: Buena
⚠️ 30-40%: Aceptable
❌ > 40%: Mala (overfitting)
```

**Retorno Promedio**:
```
0.8% por semana
≈ 41.6% anualizado (0.8% × 52 semanas)
```

### Gráficos

**Sharpe Ratio por Período**:
- Línea azul: Performance in-sample (entrenamiento)
- Línea verde: Performance out-of-sample (prueba)
- Línea roja punteada: Promedio out-of-sample

**Retorno por Período**:
- Barras verdes: Períodos ganadores
- Barras rojas: Períodos perdedores
- Muestra consistencia de la estrategia

### Frecuencia de Parámetros

```
top_k=3: 86.5%  ← Parámetro muy estable
top_k=2: 13.5%  ← Parámetro poco usado
```

**Interpretación**:
- Alta frecuencia (> 50%) = Parámetro robusto
- Baja frecuencia (< 20%) = Parámetro inestable

## Ejemplos de Uso

### Ejemplo 1: Test Rápido (Recomendado Primero)

**Configuración**:
- Estrategia: long_momentum
- Símbolos: AAPL, MSFT, GOOGL (3 símbolos)
- Período: 2024-01-01 a 2024-03-01 (2 meses)
- Ventana entrenamiento: 90 días
- Ventana prueba: 7 días
- Re-optimización: Semanal
- Parámetros: top_k=[2,3], holding_days=[7,10], tp_multiplier=[1.05]

**Tiempo estimado**: ~1 minuto

**Objetivo**: Verificar que todo funciona antes de ejecutar optimización completa

### Ejemplo 2: Optimización Completa

**Configuración**:
- Estrategia: long_momentum
- Símbolos: AAPL, MSFT, GOOGL, NVDA, TSLA (5 símbolos)
- Período: 2020-01-01 a 2025-12-31 (6 años)
- Ventana entrenamiento: 180 días
- Ventana prueba: 7 días
- Re-optimización: Semanal
- Parámetros: top_k=[2,3,4,5], holding_days=[7,10,14], tp_multiplier=[1.03,1.05,1.07]

**Tiempo estimado**: 1-2 horas

**Objetivo**: Validación completa de la estrategia

### Ejemplo 3: Optimización Rápida (Compromiso)

**Configuración**:
- Estrategia: long_momentum
- Símbolos: AAPL, MSFT, GOOGL, NVDA (4 símbolos)
- Período: 2023-01-01 a 2025-12-31 (3 años)
- Ventana entrenamiento: 180 días
- Ventana prueba: 7 días
- Re-optimización: Mensual (en lugar de semanal)
- Parámetros: top_k=[3,4], holding_days=[7,10], tp_multiplier=[1.05]

**Tiempo estimado**: ~15 minutos

**Objetivo**: Balance entre velocidad y validación

## Consejos Prácticos

### 1. Empieza Pequeño

Siempre ejecuta un test rápido primero:
- 2-3 meses de datos
- 3 símbolos
- Pocos valores de parámetros

Esto te permite:
- Verificar que todo funciona
- Estimar tiempo real
- Ajustar configuración si es necesario

### 2. Monitorea el Progreso

La UI muestra:
- Barra de progreso
- Texto de estado
- Período actual

Si tarda mucho, puedes:
- Reducir el rango de fechas
- Usar re-optimización mensual
- Reducir número de parámetros

### 3. Guarda los Resultados

Los resultados se guardan automáticamente en:
```
results/walk_forward/long_momentum_wf_YYYYMMDD_HHMMSS.json
```

También puedes descargarlos con el botón "📥 Descargar Resultados"

### 4. Compara Múltiples Runs

Ejecuta walk-forward con diferentes configuraciones:
- Diferentes estrategias
- Diferentes períodos
- Diferentes parámetros

Compara degradación y Sharpe out-of-sample para elegir la mejor.

### 5. Valida con Paper Trading

Después de walk-forward exitoso:
1. Usa los parámetros más frecuentes
2. Ejecuta en paper trading 1-2 meses
3. Compara resultados con walk-forward
4. Si coinciden, considera trading real

## Troubleshooting

### "No valid periods found"

**Causa**: Período muy corto o ventana de entrenamiento muy larga

**Solución**: 
- Aumenta el rango de fechas
- Reduce la ventana de entrenamiento
- Asegúrate que: (end_date - start_date) > train_window_days

### "Error fetching data"

**Causa**: Problemas con Yahoo Finance o símbolo inválido

**Solución**:
- Verifica que los símbolos sean correctos
- Intenta con menos símbolos
- Espera unos minutos y reintenta

### "Optimization taking too long"

**Causa**: Demasiadas combinaciones de parámetros

**Solución**:
- Reduce número de valores en param grid
- Usa re-optimización mensual
- Reduce el rango de fechas

### "High degradation (> 40%)"

**Causa**: Estrategia sobreajustada (overfitting)

**Solución**:
- Simplifica la estrategia
- Reduce número de parámetros
- Usa ventana de entrenamiento más larga
- Considera estrategia diferente

## Próximos Pasos

Después de ejecutar walk-forward:

1. **Si degradación < 30%**:
   - ✅ Estrategia validada
   - Anota los parámetros más frecuentes
   - Ejecuta backtest normal con esos parámetros
   - Considera paper trading

2. **Si degradación 30-40%**:
   - ⚠️ Estrategia mejorable
   - Prueba con más datos
   - Simplifica parámetros
   - Ejecuta otro walk-forward con ajustes

3. **Si degradación > 40%**:
   - ❌ Estrategia no robusta
   - Revisa lógica de la estrategia
   - Considera estrategia más simple
   - Consulta documentación de estrategias

## Recursos Adicionales

- [Guía Completa de Walk-Forward](rolling-walk-forward-guia.md)
- [Walk-Forward Explicado](walk-forward-optimization-explicado.md)
- [Comparación Anchored vs Rolling](walk-forward-anchored-vs-rolling.md)
- [Implementación Técnica](../technical/rolling-walk-forward-implementation.md)
