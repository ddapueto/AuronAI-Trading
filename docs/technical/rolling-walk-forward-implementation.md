# Rolling Walk-Forward Optimization - Technical Implementation

## Overview

Rolling walk-forward optimization is a robust validation technique that simulates real-world trading by:
1. Re-optimizing parameters periodically (weekly/monthly) using only past data
2. Testing with optimized parameters for the following period
3. Repeating this process throughout the entire backtest period

This prevents look-ahead bias and provides realistic out-of-sample performance estimates.

## Architecture

### Core Components

#### 1. RollingWalkForwardOptimizer

Main class that orchestrates the optimization process.

**Location**: `src/auronai/backtesting/rolling_walk_forward.py`

**Key Parameters**:
- `train_window_days`: Historical data window for optimization (default: 180 days / 6 months)
- `test_window_days`: Forward testing period (default: 21 days / 3 weeks)
- `reoptimize_frequency`: How often to re-optimize ('weekly' or 'monthly')
- `initial_capital`: Starting capital for each backtest
- `commission_rate`: Commission per trade (0.0 = free broker)
- `slippage_rate`: Slippage as decimal (0.0005 = 0.05%)

#### 2. OptimizationPeriod

Dataclass representing a single optimization period.

**Attributes**:
- `period_id`: Sequential identifier
- `train_start`, `train_end`: Training period dates
- `test_start`, `test_end`: Testing period dates
- `best_params`: Optimized parameters for this period
- `train_sharpe`: In-sample Sharpe ratio
- `test_sharpe`: Out-of-sample Sharpe ratio
- `test_return`: Out-of-sample return
- `test_max_dd`: Out-of-sample max drawdown

#### 3. RollingWalkForwardResult

Aggregated results from all optimization periods.

**Key Metrics**:
- `avg_train_sharpe`: Average in-sample performance
- `avg_test_sharpe`: Average out-of-sample performance
- `std_test_sharpe`: Standard deviation of out-of-sample performance
- `degradation`: (train - test) / train - measures overfitting
- `param_frequency`: How often each parameter value was chosen

## Algorithm Flow

### 1. Period Generation

```python
def _generate_periods(start_date, end_date):
    """
    Generate optimization periods.
    
    Example with weekly re-optimization:
    
    Period 1:
      Train: Oct 1 - Dec 31 (90 days)
      Test:  Jan 1 - Jan 7  (7 days)
    
    Period 2:
      Train: Oct 8 - Jan 7  (90 days, rolling window)
      Test:  Jan 8 - Jan 14 (7 days)
    
    Period 3:
      Train: Oct 15 - Jan 14 (90 days, rolling window)
      Test:  Jan 15 - Jan 21 (7 days)
    
    And so on...
    """
```

**Key Points**:
- Training window is ROLLING (not anchored)
- Each period uses only data available at that point in time
- No look-ahead bias

### 2. Parameter Optimization

For each period:

```python
def _optimize_params(symbols, train_start, train_end, param_grid):
    """
    Test all parameter combinations on training data.
    
    Example param_grid:
    {
        'top_k': [2, 3, 4, 5],
        'holding_days': [7, 10, 14],
        'tp_multiplier': [1.03, 1.05, 1.07]
    }
    
    Total combinations: 4 * 3 * 3 = 36 backtests per period
    """
    best_sharpe = -999
    best_params = None
    
    for params in all_combinations:
        # Run backtest on training data
        result = backtest(params, train_start, train_end)
        
        if result.sharpe > best_sharpe:
            best_sharpe = result.sharpe
            best_params = params
    
    return best_params, best_sharpe
```

### 3. Out-of-Sample Testing

```python
def _test_params(symbols, test_start, test_end, params):
    """
    Test optimized parameters on unseen data.
    
    This simulates real trading:
    - Parameters were optimized using only past data
    - Testing on future data (from perspective of optimization)
    - No parameter adjustments during test period
    """
    result = backtest(params, test_start, test_end)
    
    return {
        'sharpe_ratio': result.sharpe,
        'total_return': result.return,
        'max_drawdown': result.max_dd
    }
```

### 4. Results Aggregation

```python
def _calculate_results(periods):
    """
    Aggregate metrics across all periods.
    
    Key metrics:
    - avg_train_sharpe: Average in-sample performance
    - avg_test_sharpe: Average out-of-sample performance
    - degradation: (train - test) / train
    
    Degradation interpretation:
    - < 20%: Excellent robustness
    - 20-30%: Good robustness
    - > 30%: Possible overfitting
    """
```

## Usage

### Quick Test (2 months)

```bash
python scripts/test_rolling_walk_forward.py
```

**Configuration**:
- Symbols: AAPL, MSFT, GOOGL (3 symbols)
- Period: Jan 2024 - Feb 2024 (2 months)
- Train window: 90 days
- Test window: 7 days
- Re-optimize: Weekly
- Expected time: ~1 minute

### Full Optimization (2020-2025)

```bash
python scripts/run_rolling_walk_forward.py
```

**Configuration**:
- Symbols: AAPL, MSFT, GOOGL, NVDA, TSLA (5 symbols)
- Period: 2020-2025 (6 years)
- Train window: 180 days (6 months)
- Test window: 7 days (1 week)
- Re-optimize: Weekly
- Expected time: ~1-2 hours

## Interpreting Results

### Degradation Analysis

```python
degradation = (avg_train_sharpe - avg_test_sharpe) / avg_train_sharpe

if degradation < 0.20:
    # Excellent: Strategy is very robust
    # Parameters generalize well to unseen data
    
elif degradation < 0.30:
    # Good: Strategy is robust
    # Some performance loss but acceptable
    
else:
    # Warning: High degradation
    # Possible overfitting to training data
    # Consider simplifying strategy or using fewer parameters
```

### Parameter Stability

```python
param_frequency = {
    'top_k=3': 45,  # Chosen 45 times out of 52 weeks
    'top_k=2': 7,   # Chosen 7 times
    ...
}

# High frequency (> 50%) = stable parameter
# Low frequency (< 20%) = unstable parameter
```

**Interpretation**:
- Stable parameters: Consistently chosen across different market conditions
- Unstable parameters: Vary significantly, may indicate overfitting

### Out-of-Sample Consistency

```python
std_test_sharpe = 0.5  # Standard deviation of test Sharpe ratios

if std_test_sharpe < 0.5:
    # Consistent performance across periods
    
elif std_test_sharpe < 1.0:
    # Moderate variability
    
else:
    # High variability
    # Strategy may be sensitive to market conditions
```

## Comparison with Simple Backtest

### Simple Backtest (Current Implementation)

```
Train: 2020-2023 (optimize parameters once)
Test:  2024-2025 (test with fixed parameters)

Problem: Parameters optimized on 2020-2023 may not work in 2024-2025
```

### Rolling Walk-Forward

```
Period 1: Train 2020-H1, Test 2020-H2
Period 2: Train 2020-H2, Test 2021-H1
Period 3: Train 2021-H1, Test 2021-H2
...
Period N: Train 2024-H2, Test 2025-H1

Advantage: Parameters re-optimized regularly, simulating real trading
```

## Performance Considerations

### Computational Cost

```python
# Simple backtest
backtests = num_param_combinations
# Example: 36 combinations = 36 backtests

# Rolling walk-forward
backtests = num_periods * num_param_combinations
# Example: 52 weeks * 36 combinations = 1,872 backtests
```

**Optimization Tips**:
1. Use smaller parameter grids for initial testing
2. Cache market data to avoid repeated downloads
3. Run overnight for full 6-year optimization
4. Consider parallel processing for production use

### Memory Usage

- Each backtest stores equity curve and trades
- Memory usage: ~10 MB per backtest
- Full optimization: ~20 GB total (cleared after each period)

## Implementation Details

### Data Handling

```python
# Training data
train_start = test_start - timedelta(days=train_window_days)
train_end = test_start - timedelta(days=1)

# Ensure no overlap between train and test
assert train_end < test_start

# Ensure no look-ahead bias
assert all_data_before(train_end) < test_start
```

### Strategy Integration

The optimizer works with any strategy that implements:
- `StrategyParams` dataclass
- `generate_signals()` method
- `risk_model()` method

Currently supported:
- `LongMomentumStrategy`
- `ShortMomentumStrategy`
- `NeutralStrategy`

### Error Handling

```python
try:
    result = backtest(params, train_start, train_end)
except Exception as e:
    logger.warning(f"Error testing params {params}: {e}")
    continue  # Skip this combination

# Fallback to default params if all fail
if best_params is None:
    best_params = StrategyParams()  # Use defaults
```

## Future Enhancements

### 1. Parallel Processing

```python
from multiprocessing import Pool

def optimize_period(period):
    # Run optimization for single period
    pass

with Pool(processes=4) as pool:
    results = pool.map(optimize_period, periods)
```

### 2. Adaptive Parameter Grids

```python
# Start with coarse grid
coarse_grid = {'top_k': [2, 4, 6]}

# Refine around best values
if best_top_k == 4:
    fine_grid = {'top_k': [3, 4, 5]}
```

### 3. Monte Carlo Simulation

```python
# Add randomness to test robustness
for _ in range(1000):
    shuffled_periods = random.sample(periods, len(periods))
    result = aggregate_metrics(shuffled_periods)
    distribution.append(result)
```

### 4. Walk-Forward Efficiency Ratio

```python
wfe = avg_test_sharpe / avg_train_sharpe

if wfe > 0.5:
    # Good: Out-of-sample is > 50% of in-sample
    pass
```

## References

- Pardo, R. (2008). "The Evaluation and Optimization of Trading Strategies" (Chapter on Walk-Forward Analysis)
- Aronson, D. (2006). "Evidence-Based Technical Analysis" (Chapter on Overfitting)

## Related Documentation

- [Walk-Forward Optimization Explained](../user/walk-forward-optimization-explicado.md) - User guide
- [Anchored vs Rolling Walk-Forward](../user/walk-forward-anchored-vs-rolling.md) - Comparison
- [Current Backtest Implementation](../user/como-funciona-tu-backtest-actual.md) - Simple backtest
