# SwingTPStrategy Implementation

## Overview

SwingTPStrategy is a faithful replication of the original `SwingNoSLStrategy` logic, integrated into the AuronAI backtesting framework.

## Key Features

### 1. Market Regime Detection
- **EMA200**: Close > EMA200 (bullish)
- **Slope**: EMA200 slope over 20 days > 0 (uptrend)
- **ADX**: >= 15 (strong trend)

### 2. Risk Management
- **Base Risk Budget**: 20% in normal market
- **Defensive Risk Budget**: 5% in defensive market
- **Drawdown Kill Switch**:
  - 5% DD: Reduce risk to max 10%
  - 8% DD: Reduce risk to max 5%
  - 10% DD: PAUSE trading for 10 days

### 3. Selection Criteria
- Top K symbols by relative strength (20-day lookback vs benchmark)
- NO EMA/RSI filters (original uses only relative strength)

### 4. Exit Rules
- **Take Profit**: 5% gain (configurable via `tp_multiplier`)
- **Time Exit**: After `holding_days` (default: 10 days)
- **NO Stop Loss**: By design, to avoid daily data imprecision

## Implementation Details

### ADX Integration

ADX (Average Directional Index) was added to the system:

1. **TechnicalIndicators.calculate_adx()**: New method to calculate ADX using pandas-ta
2. **FeatureStore.compute_and_save()**: Now computes and caches ADX for all symbols
3. **SwingTPStrategy._calculate_market_regime_advanced()**: Uses ADX from features

### Differences from LongMomentumStrategy

| Aspect | Long Momentum | Swing TP (Original) |
|--------|---------------|---------------------|
| **Filters** | EMA20>EMA50, RSI<70, RS | Only RS |
| **Regime** | RegimeEngine (EMA200+slope) | EMA200+slope+ADX |
| **Risk Budget** | Fixed 20%/5% | Dynamic with DD kill switch |
| **Exits** | Only rebalancing | TP + Time Exit explicit |
| **Tracking** | Simplified | Detailed (entry/exit/reason) |

## Usage

### In UI

Select "Swing TP (No SL)" from the strategy dropdown in the Run Backtest page.

### Programmatically

```python
from auronai.strategies import SwingTPStrategy, StrategyParams
from auronai.backtesting import BacktestRunner, BacktestConfig

# Create strategy
params = StrategyParams(
    top_k=3,
    holding_days=10,
    tp_multiplier=1.05,  # 5% TP
    risk_budget=0.20
)
strategy = SwingTPStrategy(params)

# Run backtest
config = BacktestConfig(
    strategy_id="swing_tp",
    symbols=['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA'],
    benchmark='SPY',
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    initial_capital=100000.0
)

runner = BacktestRunner()
result = runner.run(config, strategy)
```

## Testing

Run the test script:

```bash
uv run python scripts/test_swing_tp_strategy.py
```

## Notes

- Feature cache was cleared after ADX implementation to ensure all features are recalculated
- The strategy respects the `holding_days` parameter and only rebalances when needed
- Position tracking includes entry/exit dates and reasons for analysis
