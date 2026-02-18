# Guía de Trading con Libertex y MetaTrader 5

## 📱 Resumen Ejecutivo

Libertex es un broker europeo regulado que ofrece:
- **Comisiones**: $0 en acciones (spread incluido)
- **Plataforma**: MetaTrader 5 (MT5)
- **Regulación**: CySEC (Chipre)
- **Depósito mínimo**: Variable según país

## 💰 Estructura de Costos en Libertex

### 1. Comisiones Oficiales

Libertex opera con **spread** en lugar de comisión directa:

| Instrumento | Spread Típico | Equivalente en % |
|-------------|---------------|------------------|
| **Acciones Líquidas** (AAPL, MSFT, GOOGL) | 0.02% - 0.05% | 0.02% - 0.05% |
| **Acciones Medianas** | 0.05% - 0.10% | 0.05% - 0.10% |
| **Acciones Pequeñas** | 0.10% - 0.30% | 0.10% - 0.30% |

**Importante**: El spread es el costo TOTAL (no hay comisión adicional).

### 2. Costos Ocultos

#### Swap (Overnight Fees)
Si mantienes posiciones abiertas más de 1 día:
- **Acciones**: -0.01% a -0.05% por noche
- **Para swing trading**: Puede sumar 0.10% - 0.50% en 10 días

#### Slippage Adicional
En horarios de baja liquidez:
- **Pre-market/After-hours**: +0.05% - 0.15%
- **Noticias importantes**: +0.10% - 0.50%

### 3. Cálculo de Costos Totales

**Trade típico en AAPL ($200) con $1,000**:

```
Entrada:
- Spread: 0.03% × $1,000 = $0.30
- Slippage: 0.02% × $1,000 = $0.20
Total entrada: $0.50 = 0.05%

Salida (después de 5 días):
- Spread: 0.03% × $1,000 = $0.30
- Slippage: 0.02% × $1,000 = $0.20
- Swap (5 noches): 0.03% × 5 × $1,000 = $1.50
Total salida: $2.00 = 0.20%

TOTAL TRADE: 0.25%
```

## 🎯 Configuración para Backtesting

### Opción 1: Sin Swap (Trades Cortos <1 día)

```python
config = BacktestConfig(
    initial_capital=1000.0,
    commission_rate=0.0000,   # Sin comisión directa
    slippage_rate=0.0005,     # 0.05% (spread + slippage)
)
```

**Uso**: Para day trading o trades que cierran el mismo día.

### Opción 2: Con Swap (Swing Trading 5-10 días)

```python
config = BacktestConfig(
    initial_capital=1000.0,
    commission_rate=0.0000,   # Sin comisión directa
    slippage_rate=0.0010,     # 0.10% (spread + slippage + swap promedio)
)
```

**Uso**: Para swing trading típico (5-10 días de holding).

### Opción 3: Conservador (Peor Caso)

```python
config = BacktestConfig(
    initial_capital=1000.0,
    commission_rate=0.0000,   # Sin comisión directa
    slippage_rate=0.0015,     # 0.15% (spread + slippage + swap + buffer)
)
```

**Uso**: Para ser muy conservador y evitar sorpresas.

## 📊 Comparativa con Otros Brokers

| Broker | Comisión | Spread | Swap | Total (5 días) |
|--------|----------|--------|------|----------------|
| **Libertex** | $0 | 0.03% | 0.15% | 0.18% |
| **Interactive Brokers** | $1 | 0.02% | 0% | 0.12% |
| **Robinhood** | $0 | 0.05% | 0% | 0.05% |
| **TD Ameritrade** | $0 | 0.03% | 0% | 0.03% |

**Conclusión**: Libertex es competitivo para trades cortos, pero el swap lo hace más caro para swing trading.

## 🔧 Configuración de MetaTrader 5

### 1. Instalación

1. Descarga MT5 desde [Libertex](https://libertex.com)
2. Instala en tu computadora
3. Inicia sesión con tus credenciales de Libertex

### 2. Configuración Básica

#### Ver Spread en Tiempo Real

1. Click derecho en el símbolo (ej: AAPL)
2. "Specification" → Ver "Spread"
3. Anota el spread típico para tus símbolos

#### Calcular Swap

1. Click derecho en el símbolo
2. "Specification" → Ver "Swap long" y "Swap short"
3. Ejemplo: Swap long = -0.03% por noche

### 3. Órdenes en MT5

#### Market Order (Orden de Mercado)
```
Ventaja: Ejecución inmediata
Desventaja: Pagas el spread completo + slippage
Costo típico: 0.05% - 0.10%
```

#### Limit Order (Orden Limitada)
```
Ventaja: Controlas el precio de entrada
Desventaja: Puede no ejecutarse
Costo típico: 0.03% - 0.05% (menos slippage)
```

**Recomendación**: Usa Limit Orders para swing trading.

## 💡 Estrategias para Reducir Costos

### 1. Evitar Swap

**Opción A: Day Trading**
- Cierra todas las posiciones antes del cierre del mercado
- Swap = $0

**Opción B: Swing Trading Corto**
- Máximo 3-5 días de holding
- Swap = 0.09% - 0.15%

### 2. Operar en Horario Normal

**Horario de mercado (9:30 - 16:00 EST)**:
- Spread: 0.03%
- Slippage: 0.02%
- Total: 0.05%

**Pre-market/After-hours**:
- Spread: 0.10%
- Slippage: 0.10%
- Total: 0.20%

**Ahorro**: 0.15% por trade = 15% en 100 trades

### 3. Usar Limit Orders

**Market Order**:
- Spread: 0.03%
- Slippage: 0.03%
- Total: 0.06%

**Limit Order**:
- Spread: 0.03%
- Slippage: 0.01%
- Total: 0.04%

**Ahorro**: 0.02% por trade = 2% en 100 trades

### 4. Seleccionar Acciones Líquidas

**Acciones Top 50 (AAPL, MSFT, GOOGL)**:
- Spread: 0.03%
- Swap: 0.03%/noche

**Acciones Medianas**:
- Spread: 0.10%
- Swap: 0.05%/noche

**Ahorro**: 0.07% + 0.02%/noche

## 📈 Impacto en tu Estrategia

Con 80 trades en 7 meses (holding promedio: 5 días):

| Configuración | Costo por Trade | Costo Total | Impacto en Return |
|---------------|----------------|-------------|-------------------|
| **Sin costos** | 0% | 0% | 0% |
| **Libertex Optimista (0.10%)** | 0.10% | 8.0% | -8.0% |
| **Libertex Realista (0.18%)** | 0.18% | 14.4% | -14.4% |
| **Libertex Conservador (0.30%)** | 0.30% | 24.0% | -24.0% |

**Conclusión**: Con costos realistas de Libertex (0.18%), pierdes 14.4% en costos.

## ✅ Recomendación Final para Backtesting

Para tu estrategia swing con Libertex:

```python
config = BacktestConfig(
    strategy_id="swing_tp",
    symbols=["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "META", "AMZN"],
    benchmark="QQQ",
    start_date=datetime(2024, 7, 1),
    end_date=datetime(2025, 2, 1),
    initial_capital=1000.0,
    commission_rate=0.0000,   # Libertex no cobra comisión directa
    slippage_rate=0.0010,     # 0.10% (spread 0.03% + slippage 0.02% + swap 0.05%)
)
```

**Justificación**:
- `commission_rate=0.0000`: Libertex no cobra comisión directa
- `slippage_rate=0.0010`: Incluye spread (0.03%) + slippage (0.02%) + swap promedio (0.05% para 5 días)

**Resultado esperado**:
- Con 80 trades: Costo total = 8% (0.10% × 80)
- Return ajustado = Return bruto - 8%

## 🎓 Recursos Adicionales

### Documentación Oficial
- [Libertex Trading Conditions](https://libertex.com/trading-conditions)
- [MetaTrader 5 User Guide](https://www.metatrader5.com/en/terminal/help)

### Calculadoras
- [Libertex Swap Calculator](https://libertex.com/tools/swap-calculator)
- [Position Size Calculator](https://libertex.com/tools/position-calculator)

### Tutoriales
- [MT5 Basics](https://www.youtube.com/results?search_query=metatrader+5+tutorial)
- [Libertex Platform Guide](https://libertex.com/education)

## ⚠️ Advertencias Importantes

### 1. Apalancamiento
Libertex ofrece apalancamiento (leverage):
- **Máximo**: 1:30 para acciones (Europa)
- **Riesgo**: Puedes perder más de tu capital inicial
- **Recomendación**: NO uses apalancamiento para swing trading

### 2. Swap Negativo
El swap es SIEMPRE negativo (pagas por mantener posiciones):
- No hay "carry trade" positivo en acciones
- Cada día que mantienes una posición, pagas

### 3. Horarios de Trading
Libertex sigue horarios de mercado:
- **NYSE/NASDAQ**: 9:30 - 16:00 EST
- **Pre-market**: 4:00 - 9:30 EST (spread más alto)
- **After-hours**: 16:00 - 20:00 EST (spread más alto)

### 4. Regulación
Libertex está regulado en Europa (CySEC):
- Protección de fondos hasta €20,000
- Segregación de cuentas
- Auditorías regulares

## 📞 Soporte

Si tienes dudas sobre costos específicos:
1. Contacta soporte de Libertex
2. Pide el "Contract Specification" de cada símbolo
3. Verifica spread y swap en tiempo real en MT5

## Fecha
2026-02-13

