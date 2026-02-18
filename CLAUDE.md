# AuronAI Trading - Claude Code Instructions

## Proyecto
Sistema de trading algorítmico para cuenta de $3,000 USD con contribuciones mensuales de $200.
Brokers: Alpaca Markets (acciones reales) + Libertex/MT5 (CFDs, sin PDT).
Enfoque: swing trading (70%) + intraday selectivo (30%).

## Estructura del Código

```
src/auronai/
├── indicators/       # Indicadores técnicos (RSI, MACD, BB, EMA, etc.)
├── strategies/       # Estrategias de trading (Dual Momentum, Swing TP, etc.)
│   └── intraday/     # Estrategias intraday (ORB, VWAP, Gap&Go)
├── backtesting/      # Motor de backtesting, walk-forward, Monte Carlo
├── risk/             # Risk management (Kelly Criterion, position sizing)
├── data/             # Symbol universe, market data providers, cache
├── brokers/          # Abstracción multi-broker (Alpaca, Libertex/MT5, Paper)
├── pipeline/         # Real-time signal pipeline
├── execution/        # Order execution, position management
├── ml/               # Machine Learning
│   ├── models/       # XGBoost clasificadores
│   └── sentiment/    # FinBERT sentiment analysis
├── portfolio/        # Portfolio management
├── cli/              # CLI con Typer
└── ui/               # Streamlit UI
frontend/             # Future React/Next.js dashboard
tests/                # Tests unitarios e integración
scripts/              # Scripts de backtesting y análisis
```

## Stack Técnico
- Python 3.12+, FastAPI, Streamlit
- pandas, numpy, pandas-ta, scikit-learn
- yfinance (data histórica), alpaca-py (broker), MetaTrader5 (Libertex)
- DuckDB (local), PostgreSQL + QuestDB (production)
- Redis (cache/pubsub), Docker Compose

## Convenciones

### Código
- Línea máxima: 100 chars
- Formatter/linter: `ruff`
- Type checking: `mypy` (strict)
- Tests: `pytest` con coverage >= 80%
- Imports: ordenados por isort (via ruff)

### Trading-Specific
- Siempre incluir gestión de riesgo en estrategias
- Position sizing basado en % del portfolio (1-2% risk max)
- Nunca hardcodear valores de capital — usar config
- **Look-ahead bias: PROHIBIDO** en backtesting (no usar datos futuros)
- Survival bias: considerar delisted stocks en backtests

### Estrategias
- Heredar de `BaseStrategy` en `strategies/base_strategy.py`
- Implementar: `generate_signals()`, `risk_model()`, `get_params()`
- Cada estrategia debe tener tests con datos sintéticos
- Documentar: timeframe, win rate esperado, max drawdown

### Brokers
- Usar `BaseBroker` ABC para toda interacción con brokers
- Lazy imports para dependencias de broker específico
- Nunca hardcodear API keys — usar `.env`
- Diferenciar entre acciones reales (Alpaca) y CFDs (Libertex)

### Git
- Branch por feature/issue
- Commits descriptivos en inglés
- PR con summary + test plan

## Comandos Útiles
```bash
# Tests
pytest tests/
pytest tests/ -k "test_strategy" --no-header

# Linting
ruff check src/
ruff format src/

# Type checking
mypy src/auronai/

# Backtest
python scripts/run_backtest.py --strategy dual_momentum

# Streamlit UI
streamlit run src/auronai/ui/app.py
```

## Reglas Importantes
- Comunicar en español con el usuario
- No dar financial advice — siempre disclaimer de análisis técnico
- Ser honesto con win rates y expectativas de retorno
- PDT rule aplica solo en Alpaca (< $25K): máx 3 day trades en 5 días rolling
- PDT NO aplica en Libertex CFDs — day trading ilimitado
- Precaución con leverage en CFDs — puede amplificar pérdidas
- Priorizar: correctness > performance > elegancia
