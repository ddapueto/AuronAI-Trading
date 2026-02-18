# ¿Qué es el Slippage? - Explicación Completa

## 📊 Definición Simple

**Slippage** es la diferencia entre el precio que ESPERAS pagar y el precio que REALMENTE pagas cuando ejecutas un trade.

## 🎯 Ejemplo Práctico

Imagina que quieres comprar acciones de Apple (AAPL):

### Sin Slippage (Ideal - NO REAL)
```
Ves en la pantalla: $200.00
Haces click en "Comprar"
Precio de ejecución: $200.00 ✅
```

### Con Slippage (Real)
```
Ves en la pantalla: $200.00
Haces click en "Comprar"
Precio de ejecución: $200.06 ❌ (pagaste $0.06 más)
```

**Slippage = $200.06 - $200.00 = $0.06 = 0.03%**

## 🤔 ¿Por Qué Ocurre el Slippage?

### 1. **Spread Bid-Ask**

El mercado tiene DOS precios simultáneos:

- **BID (Compra)**: $199.98 ← Precio al que otros VENDEN
- **ASK (Venta)**: $200.02 ← Precio al que otros COMPRAN

**Spread = $200.02 - $199.98 = $0.04**

Cuando TÚ compras:
- Pagas el precio ASK: $200.02
- Pero el precio "medio" que ves es: $200.00
- **Slippage = $0.02 (0.01%)**

Cuando TÚ vendes:
- Recibes el precio BID: $199.98
- Pero el precio "medio" que ves es: $200.00
- **Slippage = $0.02 (0.01%)**

**Total por trade completo (compra + venta) = 0.02%**

### 2. **Movimiento del Precio**

Entre el momento que decides comprar y el momento que se ejecuta:

```
T=0: Ves $200.00, haces click
T=1: Tu orden llega al mercado
T=2: Precio ahora es $200.05
T=3: Tu orden se ejecuta a $200.05
```

**Slippage adicional = $0.05 (0.025%)**

### 3. **Liquidez**

En acciones MUY líquidas (AAPL, MSFT, GOOGL):
- Hay muchos compradores y vendedores
- Spread pequeño: 0.01% - 0.02%
- Slippage bajo: 0.01% - 0.03%

En acciones POCO líquidas:
- Pocos compradores y vendedores
- Spread grande: 0.10% - 0.50%
- Slippage alto: 0.10% - 1.00%

### 4. **Tamaño de la Orden**

**Orden pequeña ($100 - $1,000)**:
- No mueve el mercado
- Slippage: 0.01% - 0.03%

**Orden grande ($10,000 - $100,000)**:
- Puede mover el precio contra ti
- Slippage: 0.05% - 0.20%

**Orden muy grande ($1,000,000+)**:
- Definitivamente mueve el precio
- Slippage: 0.20% - 1.00%

## 💰 Slippage en Diferentes Escenarios

### Acciones Líquidas (AAPL, MSFT, GOOGL)

| Horario | Tamaño Orden | Slippage Típico |
|---------|--------------|-----------------|
| Horario normal (9:30-16:00) | $100-$1,000 | 0.01% - 0.03% |
| Horario normal | $1,000-$10,000 | 0.02% - 0.05% |
| Pre-market/After-hours | $100-$1,000 | 0.05% - 0.15% |
| Pre-market/After-hours | $1,000-$10,000 | 0.10% - 0.30% |

### Acciones Menos Líquidas

| Horario | Tamaño Orden | Slippage Típico |
|---------|--------------|-----------------|
| Horario normal | $100-$1,000 | 0.05% - 0.15% |
| Horario normal | $1,000-$10,000 | 0.10% - 0.50% |

## 🎮 Slippage en Backtesting

En nuestro sistema, `slippage_rate` simula este costo:

```python
# Ejemplo: Comprar $1,000 de AAPL
entry_price = 200.00  # Precio que ves
slippage_rate = 0.0003  # 0.03%

# Precio real que pagas
actual_price = entry_price * (1 + slippage_rate)
actual_price = 200.00 * 1.0003 = $200.06

# Costo adicional
slippage_cost = $1,000 * 0.0003 = $0.30
```

### ¿Por Qué es Importante?

**Sin slippage en backtest**:
- Return: 5.00%
- Parece genial ✅

**Con slippage realista (0.03%)**:
- 100 trades × 0.03% × 2 (entrada+salida) = 6%
- Return real: 5.00% - 6.00% = **-1.00%** ❌
- ¡Estrategia perdedora!

## 📱 Valores Recomendados

### Para Acciones Líquidas (Top 100 del S&P 500)

```python
# Broker gratis + horario normal + órdenes pequeñas
slippage_rate = 0.0003  # 0.03% (RECOMENDADO)

# Broker gratis + horario normal + órdenes medianas
slippage_rate = 0.0005  # 0.05%

# Broker gratis + pre-market/after-hours
slippage_rate = 0.0010  # 0.10%
```

### Para Acciones Menos Líquidas

```python
# Acciones medianas
slippage_rate = 0.0010  # 0.10%

# Acciones pequeñas
slippage_rate = 0.0020  # 0.20%
```

### Para Ser Conservador (Recomendado)

```python
# Usa el doble del slippage esperado
slippage_rate = 0.0006  # 0.06% (si esperas 0.03%)
```

## 🔍 Cómo Medir tu Slippage Real

1. **Ejecuta 10 trades reales**
2. **Anota para cada trade**:
   - Precio que viste antes de hacer click
   - Precio de ejecución real
   - Diferencia en %

3. **Calcula el promedio**:
   ```
   Slippage promedio = Suma de diferencias / 10
   ```

4. **Usa ese valor en backtesting**

## ⚠️ Errores Comunes

### Error 1: Slippage = 0%
```python
slippage_rate = 0.0000  # ❌ IRREAL
```
**Problema**: Backtests demasiado optimistas, resultados no replicables.

### Error 2: Slippage Muy Alto
```python
slippage_rate = 0.0100  # ❌ 1% es DEMASIADO
```
**Problema**: Backtests demasiado pesimistas, rechazas estrategias buenas.

### Error 3: Mismo Slippage para Todo
```python
# ❌ Usar 0.03% para:
# - Acciones líquidas (correcto)
# - Acciones ilíquidas (incorrecto, debería ser 0.10%+)
# - Pre-market (incorrecto, debería ser 0.10%+)
```

## ✅ Mejores Prácticas

1. **Usa slippage realista**: 0.03% para acciones líquidas
2. **Sé conservador**: Mejor sobrestimar que subestimar
3. **Mide tu slippage real**: Usa datos de tus trades reales
4. **Ajusta por horario**: Más slippage fuera de horario normal
5. **Ajusta por tamaño**: Más slippage para órdenes grandes

## 📊 Impacto en tu Estrategia

Con 80 trades en 7 meses:

| Slippage | Costo por Trade | Costo Total | Impacto en Return |
|----------|----------------|-------------|-------------------|
| 0% | 0% | 0% | 0% |
| 0.03% | 0.06% | 4.8% | -4.8% |
| 0.05% | 0.10% | 8.0% | -8.0% |
| 0.10% | 0.20% | 16.0% | -16.0% |

**Conclusión**: Con slippage de 0.03%, pierdes 4.8% de return en costos.

## 🎯 Recomendación Final

Para tu estrategia swing con acciones del QQQ:

```python
config = BacktestConfig(
    commission_rate=0.0000,  # Broker gratis
    slippage_rate=0.0003,    # 0.03% realista
)
```

Esto te da:
- **Backtests realistas**
- **Resultados replicables**
- **Expectativas correctas**

Si quieres ser MÁS conservador:
```python
slippage_rate=0.0005  # 0.05%
```

## 📚 Recursos Adicionales

- [Investopedia: Slippage](https://www.investopedia.com/terms/s/slippage.asp)
- [SEC: Order Execution Quality](https://www.sec.gov/fast-answers/answersexecqhtm.html)

## Fecha
2026-02-13
