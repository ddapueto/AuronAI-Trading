# Costos Reales de Trading - Comparativa de Brokers

## Resumen Ejecutivo

Los costos de trading varían MUCHO según el broker. Para swing trading con acciones de $200-800, los costos típicos son:

- **Broker Premium (Interactive Brokers)**: 0.005% - 0.01% por trade
- **Broker Medio (TD Ameritrade, E*TRADE)**: $0 comisión + 0.01-0.02% slippage
- **Broker Económico (Robinhood, Webull)**: $0 comisión + 0.02-0.05% slippage

## Desglose Detallado

### 1. Comisiones Directas

| Broker | Comisión por Trade | Mínimo | Notas |
|--------|-------------------|---------|-------|
| **Interactive Brokers (IBKR)** | $0.005/acción | $1.00 | Mejor para traders activos |
| **TD Ameritrade** | $0 | $0 | Gratis pero con spread |
| **E*TRADE** | $0 | $0 | Gratis pero con spread |
| **Fidelity** | $0 | $0 | Gratis pero con spread |
| **Charles Schwab** | $0 | $0 | Gratis pero con spread |
| **Robinhood** | $0 | $0 | "Gratis" pero peor ejecución |
| **Webull** | $0 | $0 | "Gratis" pero peor ejecución |

### 2. Slippage (Diferencia Bid-Ask)

El slippage es la diferencia entre el precio que esperas y el precio que obtienes.

**Para acciones líquidas (AAPL, MSFT, GOOGL, etc.)**:
- **Horario de mercado**: 0.01% - 0.03%
- **Pre-market/After-hours**: 0.05% - 0.15%
- **Órdenes grandes**: 0.03% - 0.10%

**Ejemplo con AAPL a $200**:
- Bid: $199.98
- Ask: $200.02
- Spread: $0.04 = 0.02%
- Si compras en Ask y vendes en Bid: 0.02% de slippage

### 3. Costos Ocultos

#### Payment for Order Flow (PFOF)
Brokers "gratis" como Robinhood venden tus órdenes a market makers:
- **Costo estimado**: 0.01% - 0.05% en peor ejecución
- **No visible** pero real

#### Market Impact
Para órdenes grandes (>$10,000):
- **Costo adicional**: 0.01% - 0.10%
- Mueves el precio contra ti

## Cálculo de Costos Totales

### Escenario 1: Broker Premium (IBKR)

**Trade de $200 en AAPL**:
- Comisión: $1.00 (mínimo)
- Slippage: 0.02% × $200 = $0.04
- **Total entrada**: $1.04 = 0.52%
- **Total salida**: $1.04 = 0.52%
- **Total round-trip**: 1.04%

**Trade de $1,000 en AAPL**:
- Comisión: $1.00 (mínimo)
- Slippage: 0.02% × $1,000 = $0.20
- **Total entrada**: $1.20 = 0.12%
- **Total salida**: $1.20 = 0.12%
- **Total round-trip**: 0.24%

**Trade de $5,000 en AAPL**:
- Comisión: $1.00 (mínimo)
- Slippage: 0.02% × $5,000 = $1.00
- **Total entrada**: $2.00 = 0.04%
- **Total salida**: $2.00 = 0.04%
- **Total round-trip**: 0.08%

### Escenario 2: Broker "Gratis" (Robinhood)

**Trade de $1,000 en AAPL**:
- Comisión: $0
- Slippage visible: 0.02% × $1,000 = $0.20
- PFOF (oculto): 0.03% × $1,000 = $0.30
- **Total entrada**: $0.50 = 0.05%
- **Total salida**: $0.50 = 0.05%
- **Total round-trip**: 0.10%

### Escenario 3: Broker Medio (TD Ameritrade)

**Trade de $1,000 en AAPL**:
- Comisión: $0
- Slippage: 0.015% × $1,000 = $0.15
- **Total entrada**: $0.15 = 0.015%
- **Total salida**: $0.15 = 0.015%
- **Total round-trip**: 0.03%

## Recomendaciones para Backtesting

### Para Capital Pequeño ($1,000 - $5,000)

**Broker Premium (IBKR)**:
```python
commission_rate = 0.0010  # 0.10% (comisión mínima $1)
slippage_rate = 0.0002    # 0.02%
# Total por trade: 0.12% entrada + 0.12% salida = 0.24%
```

**Broker Gratis (Robinhood)**:
```python
commission_rate = 0.0000  # $0
slippage_rate = 0.0005    # 0.05% (incluye PFOF)
# Total por trade: 0.05% entrada + 0.05% salida = 0.10%
```

### Para Capital Medio ($10,000 - $50,000)

**Broker Premium (IBKR)**:
```python
commission_rate = 0.0001  # 0.01% (comisión diluida)
slippage_rate = 0.0002    # 0.02%
# Total por trade: 0.03% entrada + 0.03% salida = 0.06%
```

**Broker Medio (TD Ameritrade)**:
```python
commission_rate = 0.0000  # $0
slippage_rate = 0.0003    # 0.03%
# Total por trade: 0.03% entrada + 0.03% salida = 0.06%
```

### Para Capital Grande ($100,000+)

**Broker Premium (IBKR)**:
```python
commission_rate = 0.00005  # 0.005%
slippage_rate = 0.00020    # 0.02%
# Total por trade: 0.025% entrada + 0.025% salida = 0.05%
```

## Valores Actuales en BacktestConfig

```python
# Valores por defecto (DEMASIADO ALTOS)
commission_rate = 0.001   # 0.10%
slippage_rate = 0.0005    # 0.05%
# Total: 0.15% entrada + 0.15% salida = 0.30% por trade
```

**Problema**: Estos valores son para capital MUY pequeño (<$1,000) o broker muy malo.

## Valores Recomendados

### Para tu caso ($1,000 capital inicial)

**Opción 1: Broker Premium (IBKR) - MÁS REALISTA**
```python
commission_rate = 0.0010  # 0.10% (comisión mínima $1)
slippage_rate = 0.0002    # 0.02%
# Total: 0.12% por operación = 0.24% por trade completo
```

**Opción 2: Broker Gratis (Robinhood) - MÁS OPTIMISTA**
```python
commission_rate = 0.0000  # $0
slippage_rate = 0.0003    # 0.03% (incluye PFOF)
# Total: 0.03% por operación = 0.06% por trade completo
```

**Opción 3: Sin Costos (Solo para comparar lógica)**
```python
commission_rate = 0.0000  # $0
slippage_rate = 0.0000    # 0%
# Total: 0% (IRREAL pero útil para debugging)
```

## Impacto en tu Estrategia

Con 113 trades en 7 meses:

| Escenario | Costo por Trade | Costo Total | Impacto en Return |
|-----------|----------------|-------------|-------------------|
| **Actual (0.30%)** | 0.30% | 33.9% | -33.9% |
| **IBKR Realista (0.24%)** | 0.24% | 27.1% | -27.1% |
| **Robinhood (0.06%)** | 0.06% | 6.8% | -6.8% |
| **Sin Costos (0%)** | 0% | 0% | 0% |

**Conclusión**: Con costos actuales (0.30%), estás perdiendo 33.9% del capital en costos!

## Recomendación Final

Para backtesting realista con $1,000 capital:

```python
config = BacktestConfig(
    initial_capital=1000.0,
    commission_rate=0.0000,   # Usar broker gratis
    slippage_rate=0.0003,     # 0.03% (realista para broker gratis)
    # Total: 0.06% por trade completo
)
```

Esto te dará:
- Return más realista
- Costos manejables (6.8% vs 33.9%)
- Resultados más cercanos al original

## Referencias

- [Interactive Brokers Pricing](https://www.interactivebrokers.com/en/pricing/commissions-stocks.php)
- [Robinhood Order Execution Quality](https://cdn.robinhood.com/assets/robinhood/legal/RHS%20SEC%20Rule%20606%20Report%20Q4%202023.pdf)
- [SEC Payment for Order Flow Study](https://www.sec.gov/news/studies/ordpay.htm)

## Fecha
2026-02-13
