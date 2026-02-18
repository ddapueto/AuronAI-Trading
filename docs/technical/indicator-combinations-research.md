# Indicator Combinations Research - Best Practices

**Research Date:** February 2026  
**Sources:** Tradeciety, QuantifiedStrategies, Multiple Trading Resources

## Executive Summary

This document compiles research on the best technical indicator combinations for trading strategies, focusing on avoiding correlation and maximizing signal quality.

## Key Principle: Avoid Indicator Redundancy

**The Problem:** Using multiple indicators from the same category creates "indicator redundancy" - they all show the same information, leading to:
- Overconfidence in signals
- Missing other important market clues
- False sense of confirmation

**The Solution:** Combine indicators from DIFFERENT categories that complement each other.

---

## Indicator Categories

### 1. TREND Indicators
**Purpose:** Identify direction and strength of trends

- Moving Averages (SMA, EMA)
- MACD (Moving Average Convergence Divergence)
- ADX (Average Directional Index)
- Parabolic SAR
- Ichimoku Cloud
- Bollinger Bands (when used for trend)

### 2. MOMENTUM Indicators
**Purpose:** Measure speed and strength of price movements

- RSI (Relative Strength Index)
- Stochastic Oscillator
- CCI (Commodity Channel Index)
- Williams %R
- ROC (Rate of Change)
- Momentum Indicator

### 3. VOLATILITY Indicators
**Purpose:** Measure price fluctuations and market uncertainty

- Bollinger Bands (when used for volatility)
- ATR (Average True Range)
- Standard Deviation
- Keltner Channels
- Envelopes

### 4. VOLUME Indicators
**Purpose:** Confirm price movements with volume analysis

- OBV (On-Balance Volume)
- VWAP (Volume Weighted Average Price)
- Money Flow Index (MFI)
- Volume Profile
- Accumulation/Distribution

---

## Proven Combination Strategies

### Strategy 1: Triple Screen Trading System (Alexander Elder)

**Concept:** Use 3 different timeframes with complementary indicators

**Screen 1 - Market Tide (Long-term trend)**
- Timeframe: Weekly or 4H
- Indicator: MACD or EMA
- Purpose: Identify overall trend direction
- Rule: Only trade in direction of this trend

**Screen 2 - Market Wave (Medium-term oscillations)**
- Timeframe: Daily or 1H
- Indicator: Stochastic or RSI
- Purpose: Find pullbacks within the trend
- Rule: Wait for oscillator to show opposite signal (oversold in uptrend)

**Screen 3 - Market Entry (Short-term timing)**
- Timeframe: 4H or 15min
- Indicator: Price action + trailing stop
- Purpose: Precise entry timing
- Rule: Enter when price breaks in trend direction

**Why it works:** Each screen filters different aspects - trend, momentum, timing

---

### Strategy 2: Complementary Indicator Combo

**Best Practice Combination:**

1. **TREND:** ADX or Moving Average
   - Identifies if market is trending or ranging
   - ADX > 25 = trending, < 20 = ranging

2. **MOMENTUM:** RSI
   - Shows overbought/oversold conditions
   - Works best in ranging markets
   - RSI < 30 = oversold, > 70 = overbought

3. **VOLATILITY:** Bollinger Bands
   - Shows price extremes
   - Narrow bands = low volatility (breakout coming)
   - Wide bands = high volatility (reversal possible)

4. **VOLUME:** OBV (optional)
   - Confirms price movements
   - Rising OBV + rising price = strong uptrend
   - Falling OBV + rising price = weak uptrend (divergence)

**Trading Rules:**
- In TREND (ADX > 25): Use trend-following signals, ignore RSI extremes
- In RANGE (ADX < 20): Use RSI + Bollinger Bands for reversals
- Always check volume for confirmation

---

### Strategy 3: Uncorrelated Indicator System

**Problem with Current COMBO Strategy:**
- RSI, MACD, Stochastic are ALL momentum indicators
- They're highly correlated (move together)
- This creates false confirmation

**Better Approach:**

**BUY Signal requires:**
1. **TREND:** EMA20 > EMA50 (uptrend confirmed)
2. **MOMENTUM:** RSI < 40 (pullback in uptrend)
3. **VOLATILITY:** Price near lower Bollinger Band (oversold)
4. **VOLUME:** OBV rising (accumulation)

**SELL Signal requires:**
1. **TREND:** EMA20 < EMA50 (downtrend confirmed)
2. **MOMENTUM:** RSI > 60 (rally in downtrend)
3. **VOLATILITY:** Price near upper Bollinger Band (overbought)
4. **VOLUME:** OBV falling (distribution)

**Why this is better:**
- Each indicator measures a DIFFERENT aspect
- Less correlation = more reliable signals
- Filters out false signals better

---

## Correlation Analysis

### Highly Correlated (AVOID using together):
- RSI + Stochastic + CCI (all momentum)
- MACD + EMA crossover (both trend-following)
- Bollinger Bands + Keltner Channels (both volatility)

### Low Correlation (GOOD to combine):
- RSI (momentum) + ADX (trend strength)
- MACD (trend) + Bollinger Bands (volatility)
- EMA (trend) + OBV (volume)
- Stochastic (momentum) + ATR (volatility)

---

## Recommended Combinations by Trading Style

### Day Trading (High Frequency)
1. VWAP (volume/price)
2. RSI (momentum)
3. ATR (volatility for stops)

### Swing Trading (Multi-day holds)
1. EMA 20/50 (trend)
2. RSI (momentum)
3. Bollinger Bands (volatility)
4. OBV (volume confirmation)

### Position Trading (Long-term)
1. EMA 50/200 (long-term trend)
2. MACD (trend changes)
3. ADX (trend strength)
4. Weekly volume analysis

---

## Implementation Recommendations for AuronAI

### Current COMBO Strategy Issues:
```python
# Current (TOO CORRELATED):
- RSI (momentum)
- MACD (momentum/trend)
- Stochastic (momentum)  # REDUNDANT with RSI
- Bollinger Bands (volatility)
- EMA (trend)
```

### Improved COMBO Strategy:
```python
# Better (UNCORRELATED):
- ADX (trend STRENGTH) - replaces simple EMA comparison
- RSI (momentum) - keep
- Bollinger Bands (volatility) - keep
- OBV (volume) - add for confirmation
- Remove: Stochastic (redundant with RSI)
- Remove: MACD (redundant with ADX + RSI)
```

### Scoring System:
```python
# Weight by category (avoid overweighting correlated signals)
TREND: 40% weight
  - ADX > 25 and rising = +0.4
  - ADX < 20 = 0 (ranging market)

MOMENTUM: 30% weight
  - RSI < 30 = +0.3 (oversold)
  - RSI 30-45 = +0.15 (weak bullish)
  - RSI > 70 = -0.3 (overbought)

VOLATILITY: 20% weight
  - Price < BB lower = +0.2 (oversold)
  - Price > BB upper = -0.2 (overbought)
  - BB squeeze (narrow) = +0.1 (breakout coming)

VOLUME: 10% weight
  - OBV rising = +0.1
  - OBV falling = -0.1

TOTAL SCORE > 0.5 = BUY
TOTAL SCORE < -0.5 = SELL
```

---

## Key Takeaways

1. **Never use 2+ indicators from the same category** - they're correlated
2. **Combine indicators that measure DIFFERENT things** - trend, momentum, volatility, volume
3. **Use ADX to determine market state** - trending vs ranging
4. **In trends:** Follow trend indicators, ignore oscillators
5. **In ranges:** Use oscillators (RSI) + Bollinger Bands
6. **Always confirm with volume** - OBV or VWAP
7. **Less is more:** 3-4 uncorrelated indicators > 10 correlated ones

---

## References

1. Tradeciety - "How To Combine The Best Indicators And Avoid Wrong Signals"
   - https://tradeciety.com/how-to-choose-the-best-indicators-for-your-trading

2. Alexander Elder - "Triple Screen Trading System"
   - Multiple timeframe analysis with complementary indicators

3. QuantifiedStrategies - "Alexander Elder Triple Screen Strategy"
   - Backtest results and implementation details

4. Multiple trading resources on indicator correlation and redundancy

---

## Next Steps for AuronAI

1. **Implement ADX** to replace simple EMA crossover
2. **Add OBV** for volume confirmation
3. **Remove Stochastic** from COMBO (redundant with RSI)
4. **Adjust scoring** to weight by category, not by individual indicators
5. **Backtest** new uncorrelated combo vs current combo
6. **Compare results** - expect fewer trades but higher win rate

Content was rephrased for compliance with licensing restrictions.
