# Swing Strategy Lab - Technical Architecture

## Overview

The Swing Strategy Lab is a quantitative strategy development platform built on top of AuronAI. It provides a complete workflow for backtesting, analyzing, and comparing trading strategies.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit UI Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Run Backtest │  │ View Results │  │ Compare Runs │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                  Application Layer                           │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │ BacktestRunner   │────────▶│  RunManager      │          │
│  │ (Orchestrator)   │         │  (SQLite)        │          │
│  └──────────────────┘         └──────────────────┘          │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                   Strategy Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Long         │  │ Short        │  │ Neutral      │      │
│  │ Momentum     │  │ Momentum     │  │ Strategy     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                   ┌────────┴────────┐                        │
│                   │ RegimeEngine    │                        │
│                   │ (BULL/BEAR/     │                        │
│                   │  NEUTRAL)       │                        │
│                   └─────────────────┘                        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ ParquetCache │  │ FeatureStore │  │ DuckDB       │      │
│  │ (OHLCV)      │  │ (Indicators) │  │ (Queries)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                   ┌────────┴────────┐                        │
│                   │ MarketData      │                        │
│                   │ Provider        │                        │
│                   │ (Yahoo Finance) │                        │
│                   └─────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. UI Layer (Streamlit)

**Location**: `src/auronai/ui/`

**Components**:
- `app.py`: Main entry point, navigation, routing
- `pages/run_backtest.py`: Backtest configuration and execution
- `pages/view_results.py`: Results visualization with Plotly
- `pages/compare_runs.py`: Multi-run comparison

**Key Features**:
- Interactive parameter configuration
- Real-time progress indicators
- Responsive charts (Plotly)
- Session state management
- CSV export functionality

**Technologies**:
- Streamlit 1.28+
- Plotly 5.17+
- Pandas 2.0+

### 2. Application Layer

**Location**: `src/auronai/backtesting/`

#### BacktestRunner

**Responsibilities**:
1. Orchestrate backtest execution
2. Load/fetch market data
3. Compute technical indicators
4. Detect market regime
5. Execute strategy signals
6. Track trades and equity
7. Calculate metrics
8. Save results to database

**Key Methods**:
- `run(config, strategy)`: Main execution loop
- `_load_data()`: Data retrieval with caching
- `_compute_features()`: Indicator calculation
- `_execute_rebalance()`: Trade execution (simplified)
- `_calculate_metrics()`: Performance metrics

**Performance**:
- 1-year backtest: ~5-10 seconds
- Cache hit: <100ms
- Supports 5-50 symbols

#### RunManager

**Responsibilities**:
1. Persist backtest runs to SQLite
2. Store metrics, trades, equity curves
3. Retrieve runs by ID
4. Compare multiple runs
5. Manage run lifecycle

**Database Schema**:

```sql
-- Runs table
CREATE TABLE backtest_runs (
    run_id TEXT PRIMARY KEY,
    strategy_id TEXT,
    strategy_params TEXT,
    symbols TEXT,
    benchmark TEXT,
    start_date TEXT,
    end_date TEXT,
    initial_capital REAL,
    data_version TEXT,
    code_version TEXT,
    created_at TEXT
);

-- Metrics table
CREATE TABLE backtest_metrics (
    run_id TEXT,
    metric_name TEXT,
    metric_value REAL,
    FOREIGN KEY (run_id) REFERENCES backtest_runs(run_id)
);

-- Trades table
CREATE TABLE backtest_trades (
    run_id TEXT,
    symbol TEXT,
    entry_date TEXT,
    exit_date TEXT,
    entry_price REAL,
    exit_price REAL,
    shares REAL,
    direction TEXT,
    pnl_dollar REAL,
    pnl_percent REAL,
    reason TEXT,
    FOREIGN KEY (run_id) REFERENCES backtest_runs(run_id)
);

-- Equity curve table
CREATE TABLE backtest_equity_curve (
    run_id TEXT,
    date TEXT,
    equity REAL,
    FOREIGN KEY (run_id) REFERENCES backtest_runs(run_id)
);
```

#### MetricsCalculator

**Responsibilities**:
- Calculate return metrics (Total Return, CAGR)
- Calculate risk metrics (Sharpe, Max Drawdown, Calmar, Volatility)
- Calculate trade statistics (Win Rate, Profit Factor, Expectancy)
- Calculate exposure and regime breakdown

**Formulas**:

```python
# CAGR
cagr = (final_equity / initial_capital) ** (1 / years) - 1

# Sharpe Ratio (annualized, risk-free rate = 0)
sharpe = (returns.mean() / returns.std()) * sqrt(252)

# Max Drawdown
drawdown = (equity - equity.cummax()) / equity.cummax()
max_drawdown = drawdown.min()

# Calmar Ratio
calmar = cagr / abs(max_drawdown)

# Profit Factor
profit_factor = sum(wins) / abs(sum(losses))
```

### 3. Strategy Layer

**Location**: `src/auronai/strategies/`

#### BaseStrategy (Abstract)

**Interface**:
```python
class BaseStrategy(ABC):
    @abstractmethod
    def generate_signals(
        self,
        features: pd.DataFrame,
        regime: MarketRegime,
        current_date: datetime
    ) -> Dict[str, float]:
        """Generate trading signals (symbol -> score)."""
        pass
    
    @abstractmethod
    def risk_model(
        self,
        signals: Dict[str, float],
        features: pd.DataFrame,
        current_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """Convert signals to position weights."""
        pass
```

#### LongMomentumStrategy

**Logic**:
1. Only trade in BULL regime
2. Rank symbols by relative strength
3. Apply filters: EMA20 > EMA50, RSI < 70
4. Select top K symbols
5. Equal weight allocation (risk_budget / K)
6. Cap individual positions at max_position_size

**Parameters**:
- `top_k`: Number of positions (default: 3)
- `holding_days`: Rebalance frequency (default: 10)
- `risk_budget`: Total exposure (default: 0.2 = 20%)
- `max_position_size`: Per-symbol limit (default: 0.2 = 20%)

#### ShortMomentumStrategy

**Logic**:
1. Only trade in BEAR regime
2. Rank symbols by relative strength (inverse)
3. Apply filters: EMA20 < EMA50, RSI > 30
4. Select bottom K symbols
5. Equal weight short allocation
6. Cap individual positions

#### NeutralStrategy

**Logic**:
1. Only trade in NEUTRAL regime
2. Select low volatility symbols (low ATR)
3. Prefer positive relative strength
4. Defensive allocation (5% total exposure)
5. Longer holding periods

#### RegimeEngine

**Detection Logic**:
```python
def detect_regime(benchmark_features, current_idx):
    # Calculate EMA200
    ema200 = benchmark_features['ema_200'].iloc[current_idx]
    
    # Calculate slope over lookback period
    if current_idx >= slope_lookback:
        recent_ema = ema200.iloc[-slope_lookback:]
        slope = (recent_ema.iloc[-1] - recent_ema.iloc[0]) / slope_lookback
        
        # Classify regime
        if slope > 0.001:  # Positive slope
            return MarketRegime.BULL
        elif slope < -0.001:  # Negative slope
            return MarketRegime.BEAR
        else:  # Flat
            return MarketRegime.NEUTRAL
```

**Parameters**:
- `ema_period`: EMA length (default: 200)
- `slope_lookback`: Days for slope calculation (default: 20)

### 4. Data Layer

**Location**: `src/auronai/data/`

#### ParquetCache

**Purpose**: Persistent storage of OHLCV data

**Features**:
- Year-based partitioning: `{symbol}/{year}.parquet`
- SHA256 versioning for reproducibility
- Date range filtering
- Automatic validation (OHLC relationships)

**Storage Structure**:
```
data/cache/ohlcv/
├── AAPL/
│   ├── 2022.parquet
│   ├── 2023.parquet
│   └── 2024.parquet
├── MSFT/
│   └── ...
└── metadata.json
```

#### FeatureStore

**Purpose**: Cache computed technical indicators

**Features**:
- Computes 18+ indicators using TechnicalIndicators
- Calculates relative strength vs benchmark
- Invalidation support
- Deterministic computation

**Indicators Cached**:
- Moving Averages: SMA20, SMA50, EMA20, EMA50, EMA200
- Momentum: RSI, MACD, Stochastic
- Volatility: ATR, Bollinger Bands
- Volume: OBV
- Relative Strength vs benchmark

**Storage Structure**:
```
data/cache/features/
├── AAPL_features.parquet
├── MSFT_features.parquet
└── ...
```

#### DuckDBQueryEngine

**Purpose**: SQL queries over Parquet files

**Features**:
- Zero-copy queries
- Aggregations and rolling calculations
- Connection pooling
- <100ms query performance

**Example Queries**:
```sql
-- Get OHLCV for date range
SELECT * FROM read_parquet('data/cache/ohlcv/AAPL/*.parquet')
WHERE date BETWEEN '2023-01-01' AND '2023-12-31';

-- Calculate rolling metrics
SELECT 
    date,
    symbol,
    AVG(close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as sma20
FROM read_parquet('data/cache/ohlcv/*/*.parquet');
```

## Data Flow

### Backtest Execution Flow

```
1. User configures backtest in UI
   ↓
2. BacktestRunner.run() called
   ↓
3. Load data (ParquetCache or fetch from Yahoo)
   ↓
4. Compute features (FeatureStore)
   ↓
5. For each trading day:
   a. Detect regime (RegimeEngine)
   b. Generate signals (Strategy)
   c. Apply risk model (Strategy)
   d. Execute trades (simplified rebalance)
   e. Update equity
   ↓
6. Calculate metrics (MetricsCalculator)
   ↓
7. Save to database (RunManager)
   ↓
8. Display results in UI
```

### Caching Strategy

**Level 1: OHLCV Data (Parquet)**
- Cache hit: <10ms
- Cache miss: Fetch from Yahoo (~2-5s per symbol)
- Invalidation: Manual or on data corruption

**Level 2: Features (Parquet)**
- Cache hit: <50ms
- Cache miss: Compute from OHLCV (~100-500ms per symbol)
- Invalidation: When OHLCV changes

**Level 3: Runs (SQLite)**
- Retrieval: <100ms
- Storage: ~50-200ms per run
- No invalidation (immutable)

## Performance Characteristics

### Benchmarks

**1-Year Backtest (10 symbols)**:
- Cold start (no cache): ~30-60 seconds
- Warm start (cached): ~5-10 seconds
- UI response: <100ms

**Memory Usage**:
- Base: ~100MB
- Per symbol: ~5-10MB
- Peak (50 symbols): ~500MB-1GB

**Disk Usage**:
- OHLCV cache: ~1-2MB per symbol-year
- Features cache: ~2-5MB per symbol
- Runs database: ~100KB per run

### Scalability Limits

**Tested**:
- Symbols: Up to 50
- Date range: Up to 5 years
- Runs: Up to 1000

**Theoretical**:
- Symbols: 100+ (with optimization)
- Date range: 10+ years
- Runs: Unlimited (SQLite scales well)

## Extension Points

### Adding New Strategies

1. Inherit from `BaseStrategy`
2. Implement `generate_signals()` and `risk_model()`
3. Register in UI dropdown
4. Add tests

Example:
```python
class MyCustomStrategy(BaseStrategy):
    def generate_signals(self, features, regime, date):
        # Your logic here
        return signals
    
    def risk_model(self, signals, features, current_weights):
        # Your risk logic here
        return target_weights
```

### Adding New Indicators

1. Add to `TechnicalIndicators` class
2. Update `FeatureStore.compute_and_save()`
3. Use in strategy `generate_signals()`

### Adding New Metrics

1. Add calculation to `MetricsCalculator`
2. Update database schema if needed
3. Display in UI

## Testing Strategy

### Unit Tests
- Individual components (ParquetCache, FeatureStore, etc.)
- Strategy logic with known inputs
- Metrics calculations

### Property Tests
- Data persistence round-trip
- Feature computation determinism
- Metrics calculation correctness

### Integration Tests
- End-to-end backtest execution
- Multi-strategy comparison
- Database persistence

### Performance Tests
- Backtest execution time
- Cache hit performance
- UI responsiveness

## Dependencies

### Core
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical computing
- `pyarrow>=12.0.0` - Parquet support

### Data
- `yfinance>=0.2.28` - Market data
- `duckdb>=0.9.0` - SQL queries

### UI
- `streamlit>=1.28.0` - Web framework
- `plotly>=5.17.0` - Interactive charts

### Storage
- `sqlite3` (built-in) - Run persistence

## Configuration

### Environment Variables
```bash
# Data directories
AURONAI_CACHE_DIR=data/cache
AURONAI_DB_PATH=data/runs.db

# API settings
YAHOO_FINANCE_TIMEOUT=30
YAHOO_FINANCE_MAX_RETRIES=3

# Performance
AURONAI_MAX_WORKERS=4
AURONAI_CACHE_TTL=3600
```

### Config File (Future)
```yaml
# config.yaml
data:
  cache_dir: data/cache
  db_path: data/runs.db

strategies:
  long_momentum:
    default_top_k: 3
    default_holding_days: 10
  
performance:
  max_workers: 4
  cache_ttl: 3600
```

## Security Considerations

1. **No sensitive data**: All data is public market data
2. **Local storage**: No cloud dependencies
3. **No authentication**: Single-user desktop app
4. **Input validation**: All user inputs validated
5. **SQL injection**: Parameterized queries only

## Future Enhancements

### Short Term
- [ ] Git versioning for reproducibility
- [ ] Data versioning validation
- [ ] Configuration file support
- [ ] CLI interface

### Medium Term
- [ ] Real-time data integration
- [ ] Parameter optimization (grid search)
- [ ] Walk-forward analysis
- [ ] Monte Carlo simulation

### Long Term
- [ ] Multi-user support
- [ ] Cloud deployment
- [ ] Real trading integration
- [ ] Machine learning strategies

## References

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Documentation](https://plotly.com/python/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [Parquet Format](https://parquet.apache.org/)
