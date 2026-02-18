# Candlestick Data and Real-Time Analysis

## Understanding Candlestick Data (OHLCV)

### What is OHLCV?

Each candlestick (vela japonesa) represents price action during a specific time period:

```
Candlestick Components:
- Open (O):   First price when period starts
- High (H):   Highest price during period
- Low (L):    Lowest price during period
- Close (C):  Last price when period closes
- Volume (V): Total shares/contracts traded
```

### Timeframes

The system supports multiple timeframes:

```python
# Daily (1d) - Most common for swing trading
# Each candle = 1 full trading day
# Open: 9:30 AM ET, Close: 4:00 PM ET

# Intraday examples:
# 1m  = 1 minute candles
# 5m  = 5 minute candles
# 15m = 15 minute candles
# 1h  = 1 hour candles
```

## How Technical Indicators Use Candlestick Data

### Example: RSI Calculation

```python
# RSI needs CLOSE prices from multiple candles
closes = [150.0, 151.5, 149.0, 152.0, 153.5, ...]  # Last 14+ days

# Calculate price changes
gains = [1.5, 0, 3.0, 1.5, ...]  # Positive changes
losses = [0, 2.5, 0, 0, ...]     # Negative changes

# Average gains/losses over 14 periods
avg_gain = sum(gains) / 14
avg_loss = sum(losses) / 14

# RSI formula
rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))
```

### Example: MACD Calculation

```python
# MACD needs CLOSE prices for EMAs
closes = [150.0, 151.5, 149.0, ...]

# Calculate EMAs
ema_12 = calculate_ema(closes, period=12)  # Fast line
ema_26 = calculate_ema(closes, period=26)  # Slow line

# MACD line
macd = ema_12 - ema_26

# Signal line (EMA of MACD)
signal = calculate_ema(macd_values, period=9)
```

### Example: ATR (Uses High, Low, Close)

```python
# ATR needs H, L, C from multiple candles
for each candle:
    true_range = max(
        high - low,                    # Current range
        abs(high - previous_close),    # Gap up
        abs(low - previous_close)      # Gap down
    )

atr = average(true_ranges, period=14)
```

## The "Current Day" Problem

### Scenario: Daily Timeframe (1d)

```
Monday 9:30 AM - Market opens
├─ 10:00 AM: Price = $150 (candle forming)
├─ 12:00 PM: Price = $152 (candle still forming)
├─ 2:00 PM:  Price = $148 (candle still forming)
└─ 4:00 PM:  Price = $151 (candle CLOSES)

Current candle:
- Open: $150 (fixed at 9:30 AM)
- High: $152 (highest so far)
- Low: $148 (lowest so far)
- Close: $151 (final at 4:00 PM)
- Volume: accumulating all day
```

### The Challenge

**During trading hours (9:30 AM - 4:00 PM):**
- Current candle is INCOMPLETE
- Close price keeps changing
- High/Low keep updating
- Indicators calculated with incomplete data are UNRELIABLE

**After market close (4:00 PM):**
- Candle is COMPLETE
- All values are FINAL
- Indicators are RELIABLE

## AuronAI's Approach

### Strategy 1: End-of-Day Analysis (Recommended for Daily)

```python
# Run analysis AFTER market close (4:00 PM ET)
# Use only COMPLETED candles

# Example: Analyzing on Monday 5:00 PM
data = yf.download("AAPL", period="3mo", interval="1d")

# Last row = Monday's COMPLETED candle
# All previous rows = Historical COMPLETED candles
# All indicators calculated with FINAL data ✅
```

**Advantages:**
- All data is final and reliable
- No false signals from incomplete candles
- Suitable for swing trading (hold days/weeks)
- Less stressful, no need to watch intraday

**Disadvantages:**
- Can't react to intraday moves
- Miss intraday opportunities

### Strategy 2: Intraday Analysis (For Day Trading)

```python
# Use shorter timeframes (5m, 15m, 1h)
# Each candle completes faster

# Example: 15-minute candles
data = yf.download("AAPL", period="1d", interval="15m")

# 9:30-9:45 AM: First candle COMPLETES at 9:45
# 9:45-10:00 AM: Second candle COMPLETES at 10:00
# ... and so on

# At 10:00 AM, you have:
# - 2 COMPLETED 15m candles
# - 1 INCOMPLETE current candle (10:00-10:15)
```

**Advantages:**
- React faster to market moves
- More trading opportunities
- Can enter/exit same day

**Disadvantages:**
- More noise and false signals
- Requires constant monitoring
- Higher stress and transaction costs

### Strategy 3: Hybrid Approach (Recommended)

```python
# Use daily timeframe for DIRECTION
# Use intraday for ENTRY/EXIT timing

# Step 1: Daily analysis (after market close)
daily_data = yf.download("AAPL", period="3mo", interval="1d")
daily_rsi = calculate_rsi(daily_data['Close'])
daily_trend = "bullish" if daily_rsi < 40 else "bearish"

# Step 2: Intraday analysis (during market hours)
if daily_trend == "bullish":
    # Look for entry on 15m timeframe
    intraday_data = yf.download("AAPL", period="1d", interval="15m")
    
    # Wait for pullback on 15m chart
    # Enter when 15m RSI < 30
    # But only if daily trend is bullish
```

## Handling the Current Incomplete Candle

### Option A: Ignore Current Candle (Conservative)

```python
# Use only completed candles
data = yf.download("AAPL", period="1mo", interval="1d")

# Remove last row (current incomplete day)
completed_data = data[:-1]

# Calculate indicators on completed data only
rsi = calculate_rsi(completed_data['Close'])
```

**Use when:**
- Swing trading (daily timeframe)
- Running analysis after market close
- Want most reliable signals

### Option B: Use Current Candle (Aggressive)

```python
# Include current incomplete candle
data = yf.download("AAPL", period="1mo", interval="1d")

# Calculate indicators including current candle
rsi = calculate_rsi(data['Close'])

# BUT: Mark as "preliminary" or "live"
print(f"RSI: {rsi:.2f} (LIVE - subject to change)")
```

**Use when:**
- Day trading (intraday timeframes)
- Need real-time updates
- Understand signals may change

### Option C: Wait for Candle Close (Best Practice)

```python
import datetime

# Check if market is open
now = datetime.datetime.now()
market_close = now.replace(hour=16, minute=0)  # 4:00 PM ET

if now < market_close:
    print("⚠️ Market still open. Current candle incomplete.")
    print("💡 Recommendation: Wait until 4:00 PM for final signals.")
    
    # Option: Show preliminary analysis with warning
    show_preliminary_analysis()
else:
    print("✅ Market closed. All data is final.")
    show_final_analysis()
```

## Practical Example: Daily Workflow

### Morning Routine (Before Market Open - 9:00 AM)

```python
# Analyze yesterday's COMPLETED data
data = yf.download("AAPL", period="3mo", interval="1d")

# All candles are complete (market closed yesterday)
rsi = calculate_rsi(data['Close'])
macd = calculate_macd(data['Close'])

# Generate trading plan for today
if rsi < 30 and macd_bullish:
    print("📈 Plan: Look to BUY if price dips to $150")
    print("🎯 Target: $155")
    print("🛑 Stop: $147")
```

### During Market Hours (9:30 AM - 4:00 PM)

```python
# Option 1: Don't check (recommended for swing traders)
# Trust your morning analysis

# Option 2: Monitor with caution (for active traders)
current_price = get_current_price("AAPL")

if current_price <= 150:
    print("💰 Entry price reached!")
    print("⚠️ Verify with 15m chart before entering")
```

### After Market Close (5:00 PM)

```python
# Update analysis with TODAY's completed candle
data = yf.download("AAPL", period="3mo", interval="1d")

# Now includes today's FINAL candle
rsi = calculate_rsi(data['Close'])

# Evaluate if trade plan still valid for tomorrow
if rsi < 30:
    print("✅ Plan still valid for tomorrow")
else:
    print("❌ Conditions changed, revise plan")
```

## Implementation in AuronAI

### Configuration in .env

```bash
# Timeframe for analysis
TIMEFRAME=1d  # Options: 1m, 5m, 15m, 1h, 1d, 1wk

# Trading style
TRADING_STYLE=swing  # Options: scalping, day, swing, position

# Use incomplete candle?
USE_INCOMPLETE_CANDLE=false  # true for intraday, false for daily
```

### Code Implementation

```python
class TradingAgent:
    def analyze(self, symbol: str, timeframe: str = "1d"):
        # Get data
        data = yf.download(symbol, period="3mo", interval=timeframe)
        
        # Handle incomplete candle based on timeframe
        if timeframe == "1d" and not self.config.use_incomplete_candle:
            # For daily, check if market is closed
            if self.is_market_open():
                print("⚠️ Market open. Using yesterday's close.")
                data = data[:-1]  # Remove incomplete candle
        
        # Calculate indicators on complete data
        indicators = self.calculate_indicators(data)
        
        # Generate recommendation
        recommendation = self.generate_recommendation(indicators)
        
        return recommendation
```

## Best Practices

### For Swing Trading (Days to Weeks)

1. ✅ Use daily (1d) timeframe
2. ✅ Run analysis after market close (4:00 PM ET)
3. ✅ Ignore current incomplete candle
4. ✅ Make decisions based on completed data
5. ✅ Execute trades next morning

### For Day Trading (Intraday)

1. ✅ Use 5m, 15m, or 1h timeframes
2. ✅ Wait for candle to complete before acting
3. ✅ Use daily timeframe for overall direction
4. ✅ Enter on intraday timeframe
5. ⚠️ Be aware of higher noise and false signals

### For Position Trading (Weeks to Months)

1. ✅ Use daily (1d) or weekly (1wk) timeframe
2. ✅ Run analysis weekly
3. ✅ Focus on long-term trends
4. ✅ Ignore short-term volatility

## Summary

**Key Takeaways:**

1. **Indicators need multiple completed candles** to calculate accurately
2. **Current incomplete candle** changes throughout the day
3. **Daily timeframe**: Best to analyze after market close (4:00 PM)
4. **Intraday timeframes**: Each candle completes faster, but more noise
5. **Hybrid approach**: Use daily for direction, intraday for timing
6. **AuronAI default**: Daily timeframe, analysis after market close

**Recommendation for AuronAI:**

Start with daily timeframe and end-of-day analysis. This gives you:
- Most reliable signals
- Less stress
- Time to think and plan
- Suitable for beginners and professionals

Once comfortable, you can explore intraday timeframes for more active trading.
