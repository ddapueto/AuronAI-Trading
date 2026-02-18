# Comparación: AuronAI Actual vs Swing/Quant Strategy Lab (Spec Propuesto)

## Resumen Ejecutivo

Este documento compara tu sistema actual (AuronAI) con el spec propuesto (Swing/Quant Strategy Lab) para identificar:
- ✅ Qué ya tienes implementado
- 🔄 Qué necesitas adaptar
- ⚠️ Qué falta construir
- 💡 Oportunidades de integración

---

## 1. ARQUITECTURA CORE

### 1.1 Data Layer (Ingesta y Cache)

#### Spec Propuesto
```
- Parquet particionado (symbol/year)
- DuckDB para queries rápidas
- Feature store precomputado (RS/EMA/ADX/ATR)
- Data versioning (hash/timestamp)
```

#### AuronAI Actual
```python
# ✅ YA TIENES:
- MarketDataProvider con cache en memoria (TTL 60s)
- Retry logic con exponential backoff
- Validación de datos OHLCV
- Soporte multi-símbolo

# ⚠️ FALTA:
- Persistencia en Parquet
- DuckDB para queries
- Feature store precomputado
- Data versioning
```

**Evaluación**: 40% implementado
- Cache funcional pero volátil (memoria)
- Necesitas persistencia para reproducibilidad

**Recomendación**: 
```python
# Agregar capa de persistencia
class DataCache:
    def __init__(self, cache_dir='data/cache'):
        self.cache_dir = cache_dir
        self.duckdb_conn = duckdb.connect('data/market_data.db')
    
    def save_ohlcv(self, symbol, data, version):
        # Guardar en Parquet particionado
        path = f"{self.cache_dir}/{symbol}/year={data.index.year[0]}/data.parquet"
        data.to_parquet(path)
        
        # Registrar en DuckDB
        self.duckdb_conn.execute(f"""
            INSERT INTO data_versions 
            VALUES ('{symbol}', '{version}', '{path}', NOW())
        """)
```

---

### 1.2 Feature Store

#### Spec Propuesto
```
- RS20 (relative strength vs benchmark)
- EMA200, EMA50, EMA20
- ADX (trend strength)
- ATR (volatility)
- Precomputado y guardado
```

#### AuronAI Actual
```python
# ✅ YA TIENES:
- TechnicalIndicators con 15+ indicadores
- RSI, MACD, Bollinger, EMA (20/50/200)
- Stochastic, ATR, OBV, Williams %R, CCI, ROC
- Cálculo on-demand

# ⚠️ FALTA:
- Relative Strength vs benchmark (RS20)
- ADX (trend strength)
- Precomputación y persistencia
```

**Evaluación**: 70% implementado
- Tienes MÁS indicadores de los que necesitas
- Falta RS20 (crítico para tu estrategia swing)
- Falta ADX (ya lo usas en swing strategies pero no está en TechnicalIndicators)

**Recomendación**:
```python
# Agregar a TechnicalIndicators
def calculate_relative_strength(
    self,
    symbol_data: pd.DataFrame,
    benchmark_data: pd.DataFrame,
    lookback: int = 20
) -> pd.Series:
    """Calculate relative strength vs benchmark."""
    symbol_return = symbol_data['Close'].pct_change(lookback)
    benchmark_return = benchmark_data['Close'].pct_change(lookback)
    return symbol_return - benchmark_return

def calculate_adx(
    self,
    data: pd.DataFrame,
    period: int = 14
) -> Optional[pd.Series]:
    """Calculate ADX (Average Directional Index)."""
    adx = ta.adx(data['High'], data['Low'], data['Close'], length=period)
    if adx is not None:
        adx_col = [col for col in adx.columns if col.startswith('ADX')][0]
        return adx[adx_col]
    return None
```

---

### 1.3 Strategy Layer (Plugins)

#### Spec Propuesto
```
Interfaz única:
- generate_signals(features, regime) -> target_weights
- risk_model(target_weights, features) -> final_weights
- execution_model(final_weights) -> trades

Estrategias:
1. Long Momentum (Bull)
2. Short Momentum (Bear) o Defensive Cash
3. Neutral (low exposure)
```

#### AuronAI Actual
```python
# ✅ YA TIENES:
- BacktestEngine con múltiples estrategias
- SwingMultiAssetV1 (long momentum)
- SwingMultiAssetV2 (inter-sector rotation)
- SwingLongShortV1 (long/short regime-based)
- RiskManager con Kelly Criterion

# 🔄 NECESITAS ADAPTAR:
- Interfaz no es pluggable (cada strategy es clase separada)
- Lógica de regime detection duplicada en cada strategy
- No hay abstracción común
```

**Evaluación**: 60% implementado
- Tienes las estrategias pero no son plugins
- Código duplicado entre strategies

**Recomendación**:
```python
# Crear interfaz base
class BaseStrategy(ABC):
    @abstractmethod
    def generate_signals(
        self,
        features: pd.DataFrame,
        regime: str
    ) -> Dict[str, float]:
        """Return target weights per symbol."""
        pass
    
    @abstractmethod
    def risk_model(
        self,
        target_weights: Dict[str, float],
        features: pd.DataFrame
    ) -> Dict[str, float]:
        """Apply risk constraints."""
        pass

# Implementar tus strategies existentes
class LongMomentumStrategy(BaseStrategy):
    def generate_signals(self, features, regime):
        if regime != 'BULL':
            return {}
        # Tu lógica de RS20 + Top3
        ...

class ShortMomentumStrategy(BaseStrategy):
    def generate_signals(self, features, regime):
        if regime != 'BEAR':
            return {}
        # Tu lógica de Bottom3
        ...
```

---

### 1.4 Runs Layer (Reproducibilidad)

#### Spec Propuesto
```
Cada run guarda:
- run_id (uuid)
- strategy_id + params_json
- universe_id
- data_version (hash)
- code_version (git commit)
- start/end date
- metrics, equity_curve, trades
```

#### AuronAI Actual
```python
# ✅ YA TIENES:
- Backtest results con metrics
- Equity curve tracking
- Trade history
- JSON export

# ⚠️ FALTA:
- run_id único
- data_version tracking
- code_version (git commit)
- Base de datos de runs
- Comparación entre runs
```

**Evaluación**: 50% implementado
- Guardas resultados pero no son reproducibles
- No puedes comparar runs fácilmente

**Recomendación**:
```python
# Agregar metadata a cada run
@dataclass
class BacktestRun:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    strategy_id: str
    params: Dict[str, Any]
    universe: List[str]
    data_version: str
    code_version: str  # git commit hash
    start_date: datetime
    end_date: datetime
    created_at: datetime = field(default_factory=datetime.now)
    
    metrics: Dict[str, float]
    equity_curve: List[float]
    trades: List[Dict]

# Guardar en SQLite
class RunDatabase:
    def __init__(self, db_path='data/runs.db'):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def save_run(self, run: BacktestRun):
        # Guardar metadata
        self.conn.execute("""
            INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (run.run_id, run.strategy_id, ...))
        
        # Guardar metrics
        # Guardar equity_curve
        # Guardar trades
```

---

## 2. BACKTESTING ENGINE

### 2.1 Comparación de Capacidades

| Feature | Spec Propuesto | AuronAI Actual | Status |
|---------|---------------|----------------|--------|
| Walk-forward validation | ✅ | ✅ | ✅ TIENES |
| Multi-asset | ✅ | ✅ | ✅ TIENES |
| Long/Short | ✅ | ✅ | ✅ TIENES |
| Regime detection | ✅ | ✅ | ✅ TIENES |
| Risk management | ✅ | ✅ | ✅ TIENES |
| Transaction costs | ✅ | ✅ | ✅ TIENES |
| Slippage | ✅ | ✅ | ✅ TIENES |
| Reproducible runs | ✅ | ❌ | ⚠️ FALTA |
| Run comparison UI | ✅ | ❌ | ⚠️ FALTA |
| Feature store | ✅ | ❌ | ⚠️ FALTA |

**Evaluación**: 70% implementado
- Motor de backtesting es SÓLIDO
- Falta infraestructura de reproducibilidad

---

## 3. UI/VISUALIZACIÓN

### 3.1 Spec Propuesto

```
Pantalla 1: Run Backtest
- Selector de estrategia
- Fechas
- Universo
- Parámetros
- Botón Run

Pantalla 2: Results
- KPIs (Return, Sharpe, MaxDD, WinRate)
- Equity curve
- Drawdown chart
- Trades table
- Top contributors

Pantalla 3: Compare Runs
- Seleccionar 2-4 runs
- Equity en mismo gráfico
- Tabla comparativa
- Breakdown por régimen
```

### 3.2 AuronAI Actual

```python
# ❌ NO TIENES:
- UI web
- Visualización interactiva
- Comparación de runs

# ✅ TIENES:
- Scripts de backtesting
- Resultados en JSON
- Gráficos estáticos (matplotlib)
```

**Evaluación**: 10% implementado
- Solo tienes scripts CLI
- Gráficos estáticos guardados en results/

**Recomendación**: Streamlit MVP (más rápido)
```python
# app.py
import streamlit as st
from auronai.backtesting import BacktestEngine

st.title("AuronAI Strategy Lab")

# Pantalla 1: Run Backtest
strategy = st.selectbox("Strategy", ["Long Momentum", "Short Momentum", "Neutral"])
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")
symbols = st.multiselect("Universe", ["AAPL", "MSFT", ...])

if st.button("Run Backtest"):
    # Ejecutar backtest
    results = run_backtest(strategy, start_date, end_date, symbols)
    
    # Pantalla 2: Results
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Return", f"{results['return']:.2f}%")
    col2.metric("Sharpe", f"{results['sharpe']:.2f}")
    col3.metric("Max DD", f"{results['max_dd']:.2f}%")
    col4.metric("Win Rate", f"{results['win_rate']:.2f}%")
    
    # Equity curve
    st.line_chart(results['equity_curve'])
    
    # Trades table
    st.dataframe(results['trades'])
```

---

## 4. MATRIZ DE DECISIÓN

### 4.1 ¿Qué Reutilizar de AuronAI?

| Componente | Reutilizar | Adaptar | Reescribir |
|------------|-----------|---------|------------|
| MarketDataProvider | ✅ | Agregar Parquet | - |
| TechnicalIndicators | ✅ | Agregar RS20, ADX | - |
| BacktestEngine | ✅ | Extraer a plugins | - |
| SwingStrategies | ✅ | Convertir a plugins | - |
| RiskManager | ✅ | - | - |
| UI/Visualización | - | - | ✅ Crear nuevo |
| Run Management | - | - | ✅ Crear nuevo |

### 4.2 ¿Qué Construir Nuevo?

1. **Data Layer** (2-3 días)
   - Parquet persistence
   - DuckDB integration
   - Data versioning

2. **Feature Store** (1-2 días)
   - Precomputación de features
   - RS20 calculation
   - ADX integration

3. **Strategy Plugins** (2-3 días)
   - BaseStrategy interface
   - Refactor existing strategies
   - Regime engine centralizado

4. **Run Management** (2-3 días)
   - SQLite database
   - Run metadata tracking
   - Comparison engine

5. **UI Streamlit** (3-4 días)
   - 3 pantallas básicas
   - Gráficos interactivos
   - Run comparison

**Total estimado**: 10-15 días para MVP completo

---

## 5. ROADMAP RECOMENDADO

### Fase 1: Fundación (3-4 días)
```
✅ Mantener tu código actual funcionando
🔧 Agregar:
   - Parquet persistence
   - DuckDB básico
   - Run metadata (sin UI)
```

### Fase 2: Refactor Strategies (2-3 días)
```
🔧 Crear BaseStrategy interface
🔧 Convertir SwingMultiAssetV1/V2/LongShort a plugins
🔧 Centralizar regime detection
```

### Fase 3: UI MVP (3-4 días)
```
🆕 Streamlit app básica
🆕 Run backtest screen
🆕 Results visualization
```

### Fase 4: Comparación (2-3 días)
```
🆕 Run database queries
🆕 Compare runs screen
🆕 Breakdown por régimen
```

---

## 6. DECISIÓN FINAL

### Opción A: Evolución Incremental (RECOMENDADO)
```
✅ Mantener AuronAI como base
✅ Agregar capas del spec propuesto
✅ Migración gradual sin romper nada
✅ Tiempo: 10-15 días
```

### Opción B: Reescritura Completa
```
⚠️ Empezar desde cero con spec propuesto
⚠️ Perder momentum actual
⚠️ Tiempo: 20-30 días
❌ NO RECOMENDADO
```

### Opción C: Híbrido
```
✅ Usar AuronAI para backtesting
✅ Construir UI nueva con Streamlit
✅ Agregar solo persistencia mínima
✅ Tiempo: 5-7 días
✅ OPCIÓN RÁPIDA para ver resultados
```

---

## 7. PRÓXIMOS PASOS

### Inmediato (Hoy)
1. Decidir qué opción seguir (A, B, o C)
2. Crear spec en `.kiro/specs/swing-strategy-lab/`
3. Definir prioridades

### Esta Semana
1. Implementar Parquet persistence
2. Agregar RS20 y ADX a TechnicalIndicators
3. Crear BaseStrategy interface

### Próxima Semana
1. Streamlit MVP (3 pantallas)
2. Run database
3. Primera comparación de runs

---

## 8. CONCLUSIÓN

**TU SISTEMA ACTUAL ES SÓLIDO** 🎉

- Tienes 60-70% de lo que necesitas
- El motor de backtesting es profesional
- Las estrategias funcionan

**LO QUE FALTA ES INFRAESTRUCTURA**:
- Persistencia (Parquet + DuckDB)
- Reproducibilidad (run tracking)
- UI (Streamlit)

**RECOMENDACIÓN**: Opción A (Evolución Incremental)
- Aprovecha lo que tienes
- Agrega capas del spec propuesto
- 10-15 días para MVP completo

¿Quieres que creemos el spec formal para empezar la implementación?
