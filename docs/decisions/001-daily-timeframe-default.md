# ADR-001: Use Daily Timeframe as Default with End-of-Day Analysis

## Estado
Aceptado

## Contexto

AuronAI needs to decide on the default timeframe for market analysis and when to run that analysis. The key considerations are:

1. **Data Reliability**: Incomplete candles (current day during market hours) produce unreliable indicator values that change throughout the day
2. **User Experience**: Different trading styles (scalping, day trading, swing trading) require different timeframes
3. **Complexity**: Real-time intraday analysis requires handling incomplete candles and constant monitoring
4. **Target Audience**: System should be accessible to beginners while being powerful for professionals

### The Problem

When analyzing during market hours with daily timeframe:
- Current candle is incomplete (Open is fixed, but High/Low/Close keep changing)
- Technical indicators calculated with incomplete data are unreliable
- Signals can change dramatically as the day progresses
- Creates confusion and potential for bad trading decisions

Example:
```
10:00 AM: RSI = 65 (based on incomplete candle) → "Hold"
2:00 PM:  RSI = 72 (candle updated) → "Sell"
4:00 PM:  RSI = 68 (final value) → "Hold"
```

## Decisión

**Default Configuration:**
- Timeframe: Daily (1d)
- Analysis timing: After market close (4:00 PM ET)
- Incomplete candle handling: Exclude current day if market is open
- Trading style: Swing trading (hold days to weeks)

**Rationale:**
1. Daily timeframe provides most reliable signals (completed candles)
2. End-of-day analysis eliminates confusion from changing intraday values
3. Suitable for 80% of users (swing traders and position traders)
4. Less stressful - no need to watch market all day
5. Better for beginners to learn without noise

**Configuration Flexibility:**
System will support other timeframes via configuration:
```python
TIMEFRAME=1d          # Default
TIMEFRAME=15m         # For day traders
TIMEFRAME=1h          # For active traders
TIMEFRAME=1wk         # For position traders
```

## Consecuencias

### Positivas

1. **Reliability**: All analysis based on completed, final data
2. **Simplicity**: Users don't need to understand incomplete candle issues
3. **Accessibility**: Beginners can use system without confusion
4. **Lower Stress**: No need to monitor market constantly
5. **Better Decisions**: Time to think and plan trades overnight
6. **Lower Costs**: Fewer trades = lower transaction costs
7. **Proven Strategy**: Swing trading is a proven, sustainable approach

### Negativas

1. **Missed Opportunities**: Can't react to intraday moves
2. **Slower Execution**: Trades executed next day, not immediately
3. **Gap Risk**: Price can gap overnight (open different from previous close)
4. **Not for Day Traders**: Active day traders need intraday timeframes
5. **Delayed Signals**: May miss fast-moving opportunities

### Mitigations

1. **Support Multiple Timeframes**: Allow users to configure for their style
2. **Hybrid Mode**: Use daily for direction, intraday for entry/exit timing
3. **Pre-Market Analysis**: Run analysis before market open (9:00 AM)
4. **Alert System**: Notify when conditions change significantly
5. **Documentation**: Clear guide on when to use each timeframe

## Alternativas Consideradas

### Alternative A: Intraday (15m) as Default

**Pros:**
- Faster reaction to market moves
- More trading opportunities
- Can enter/exit same day

**Cons:**
- Much higher noise and false signals
- Requires constant monitoring
- Overwhelming for beginners
- Higher transaction costs
- More stressful

**Why Rejected:** Too complex for default. Better as advanced option.

### Alternative B: Real-Time with Incomplete Candle

**Pros:**
- Most up-to-date information
- Can see signals as they develop

**Cons:**
- Signals change constantly during day
- Very confusing for users
- Leads to impulsive decisions
- Technically complex to implement correctly

**Why Rejected:** Creates more problems than it solves. Unreliable signals lead to bad trades.

### Alternative C: Weekly (1wk) as Default

**Pros:**
- Very stable signals
- Minimal noise
- Suitable for long-term investors

**Cons:**
- Too slow for most traders
- Misses medium-term opportunities
- Less engaging for users

**Why Rejected:** Too conservative. Daily provides good balance.

## Implementation Details

### Market Hours Detection

```python
import datetime
import pytz

def is_market_open() -> bool:
    """Check if US stock market is currently open."""
    et = pytz.timezone('US/Eastern')
    now = datetime.datetime.now(et)
    
    # Market hours: 9:30 AM - 4:00 PM ET, Monday-Friday
    if now.weekday() >= 5:  # Weekend
        return False
    
    market_open = now.replace(hour=9, minute=30, second=0)
    market_close = now.replace(hour=16, minute=0, second=0)
    
    return market_open <= now <= market_close
```

### Incomplete Candle Handling

```python
def get_analysis_data(symbol: str, period: str = "3mo") -> pd.DataFrame:
    """Get market data, excluding incomplete candle if market is open."""
    data = yf.download(symbol, period=period, interval="1d")
    
    if is_market_open():
        # Remove last row (incomplete current day)
        data = data[:-1]
        logger.info("Market open - using data up to yesterday's close")
    else:
        logger.info("Market closed - using all available data")
    
    return data
```

### User Notification

```python
def analyze(symbol: str) -> dict:
    """Run analysis with appropriate warnings."""
    if is_market_open():
        print("⚠️ Market is currently open")
        print("💡 Analysis based on yesterday's close")
        print("🕐 For today's final signals, run after 4:00 PM ET")
    
    data = get_analysis_data(symbol)
    indicators = calculate_indicators(data)
    recommendation = generate_recommendation(indicators)
    
    return recommendation
```

## Configuration

### .env Settings

```bash
# Timeframe for analysis
TIMEFRAME=1d  # Options: 1m, 5m, 15m, 1h, 1d, 1wk

# Trading style
TRADING_STYLE=swing  # Options: scalping, day, swing, position

# Use incomplete candle? (only for intraday)
USE_INCOMPLETE_CANDLE=false

# Preferred analysis time (24h format)
ANALYSIS_TIME=17:00  # 5:00 PM ET (after market close)
```

## Future Enhancements

1. **Scheduled Analysis**: Automatically run at configured time
2. **Multi-Timeframe Analysis**: Show daily + weekly + monthly in one view
3. **Hybrid Mode**: Daily for direction, 15m for entry timing
4. **Alert System**: Notify when daily signals change
5. **Backtesting**: Test strategies on different timeframes

## References

- [Candlestick Data Flow Documentation](../technical/candlestick-data-flow.md)
- [Technical Indicators Reference](../../.kiro/steering/technical-indicators-reference.md)
- Yahoo Finance API: https://github.com/ranaroussi/yfinance

## Revisión

- **Fecha**: 2025-02-10
- **Autor**: AuronAI Team
- **Revisores**: N/A
- **Próxima revisión**: Después de 3 meses de uso en producción
