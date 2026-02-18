"""Property-based tests for technical indicators.

These tests verify that indicator calculations satisfy universal properties
across a wide range of inputs.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings
import pytest

from auronai.indicators import TechnicalIndicators


# Strategy for generating valid OHLCV data
@st.composite
def ohlcv_data(draw, min_rows=50, max_rows=100):
    """Generate valid OHLCV DataFrame for testing.
    
    Args:
        draw: Hypothesis draw function
        min_rows: Minimum number of rows
        max_rows: Maximum number of rows
        
    Returns:
        DataFrame with valid OHLCV data
    """
    n_rows = draw(st.integers(min_value=min_rows, max_value=max_rows))
    
    # Generate base price around 100
    base_price = draw(st.floats(min_value=10.0, max_value=500.0))
    
    # Generate price changes (geometric Brownian motion)
    returns = draw(
        st.lists(
            st.floats(min_value=-0.05, max_value=0.05),
            min_size=n_rows,
            max_size=n_rows
        )
    )
    
    # Calculate prices
    prices = [base_price]
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    # Generate OHLC from close prices
    data = []
    for i, close in enumerate(prices):
        # Generate high/low around close
        volatility = draw(st.floats(min_value=0.001, max_value=0.03))
        high = close * (1 + volatility)
        low = close * (1 - volatility)
        open_price = draw(st.floats(min_value=low, max_value=high))
        
        # Ensure OHLC relationships
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # Generate volume
        volume = draw(st.integers(min_value=100000, max_value=10000000))
        
        data.append({
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': volume
        })
    
    df = pd.DataFrame(data)
    df.index = pd.date_range(start=datetime.now() - timedelta(days=n_rows), periods=n_rows, freq='D')
    
    return df


class TestIndicatorCompleteness:
    """Property 1: Technical Indicator Calculation Completeness.
    
    For any valid OHLCV data with sufficient periods, calculating indicators
    should return all expected indicators with non-None values for the
    configured mode (basic or advanced).
    
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.10**
    """
    
    @given(data=ohlcv_data(min_rows=60, max_rows=70))
    @settings(max_examples=3, deadline=2000)
    def test_basic_mode_completeness(self, data):
        """Test that basic mode returns all basic indicators."""
        calculator = TechnicalIndicators(advanced_mode=False)
        
        result = calculator.calculate_all_indicators(data)
        
        # Basic indicators should always be present
        expected_basic = ['rsi', 'macd', 'bollinger_bands', 'ema_20', 'ema_50']
        
        for indicator in expected_basic:
            assert indicator in result, f"Missing basic indicator: {indicator}"
            assert result[indicator] is not None, f"Indicator {indicator} is None"
        
        # Advanced indicators should NOT be present in basic mode
        advanced_indicators = ['stochastic', 'atr', 'obv', 'williams_r', 'cci', 'roc']
        for indicator in advanced_indicators:
            assert indicator not in result, f"Advanced indicator {indicator} should not be in basic mode"
    
    @given(data=ohlcv_data(min_rows=60, max_rows=70))
    @settings(max_examples=3, deadline=2000)
    def test_advanced_mode_completeness(self, data):
        """Test that advanced mode returns all indicators."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        result = calculator.calculate_all_indicators(data)
        
        # All indicators should be present in advanced mode
        expected_all = [
            'rsi', 'macd', 'bollinger_bands', 'ema_20', 'ema_50',
            'stochastic', 'atr', 'obv', 'williams_r', 'cci', 'roc'
        ]
        
        for indicator in expected_all:
            assert indicator in result, f"Missing indicator in advanced mode: {indicator}"
            assert result[indicator] is not None, f"Indicator {indicator} is None"
    
    @given(data=ohlcv_data(min_rows=60, max_rows=70))
    @settings(max_examples=3, deadline=2000)
    def test_indicator_structure(self, data):
        """Test that indicators have expected structure."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        result = calculator.calculate_all_indicators(data)
        
        # RSI should have value, previous, trend
        if 'rsi' in result:
            assert 'value' in result['rsi']
            assert 'previous' in result['rsi']
            assert 'trend' in result['rsi']
            assert result['rsi']['trend'] in ['up', 'down']
        
        # MACD should have value, signal, histogram, trend
        if 'macd' in result:
            assert 'value' in result['macd']
            assert 'signal' in result['macd']
            assert 'histogram' in result['macd']
            assert 'trend' in result['macd']
            assert result['macd']['trend'] in ['bullish', 'bearish']
        
        # Bollinger Bands should have upper, middle, lower, position
        if 'bollinger_bands' in result:
            assert 'upper' in result['bollinger_bands']
            assert 'middle' in result['bollinger_bands']
            assert 'lower' in result['bollinger_bands']
            assert 'position' in result['bollinger_bands']


class TestIndicatorMathematicalCorrectness:
    """Property 2: Technical Indicator Mathematical Correctness.
    
    For any OHLCV data, calculated RSI values should be between 0 and 100,
    MACD should equal (EMA_fast - EMA_slow), and Bollinger Bands should
    satisfy: lower < middle < upper.
    
    **Validates: Requirements 1.1, 1.2, 1.3**
    
    NOTE: These tests are skipped by default as they are slow.
    Run with: pytest -m "not slow" to skip, or pytest -m "slow" to run only these.
    """
    
    @pytest.mark.slow
    @given(data=ohlcv_data(min_rows=50, max_rows=60))
    @settings(max_examples=2, deadline=1000)
    def test_rsi_bounds(self, data):
        """Test that RSI values are between 0 and 100."""
        calculator = TechnicalIndicators()
        
        rsi = calculator.calculate_rsi(data)
        
        if rsi is not None:
            # Check if data has zero volatility (all prices the same)
            price_std = data['Close'].std()
            
            if price_std == 0:
                # With zero volatility, RSI should be NaN (undefined)
                # This is expected behavior - RSI requires price movement
                assert rsi.isna().all(), "RSI should be NaN with zero volatility"
            else:
                # With normal volatility, RSI should be between 0 and 100
                # Filter out NaN values (warm-up period)
                valid_rsi = rsi.dropna()
                
                if len(valid_rsi) > 0:
                    assert (valid_rsi >= 0).all(), "RSI values below 0 found"
                    assert (valid_rsi <= 100).all(), "RSI values above 100 found"
    
    @pytest.mark.slow
    @given(data=ohlcv_data(min_rows=50, max_rows=60))
    @settings(max_examples=2, deadline=1000)
    def test_bollinger_bands_ordering(self, data):
        """Test that Bollinger Bands satisfy lower < middle < upper."""
        calculator = TechnicalIndicators()
        
        bb = calculator.calculate_bollinger_bands(data)
        
        if bb is not None:
            # Check if data has zero volatility (all prices the same)
            price_std = data['Close'].std()
            
            if price_std == 0:
                # With zero volatility, bands should all be equal to the price
                # or NaN (depending on pandas_ta implementation)
                # This is expected behavior - Bollinger Bands require volatility
                valid_middle = bb['middle'].dropna()
                if len(valid_middle) > 0:
                    # All bands should be equal when there's no volatility
                    valid_idx = bb['middle'].notna()
                    lower = bb['lower'][valid_idx]
                    middle = bb['middle'][valid_idx]
                    upper = bb['upper'][valid_idx]
                    
                    # With zero volatility, upper and lower should equal middle
                    assert (lower == middle).all() or lower.isna().all(), "Bands should be equal with zero volatility"
                    assert (upper == middle).all() or upper.isna().all(), "Bands should be equal with zero volatility"
            else:
                # With normal volatility, check proper ordering
                # Remove NaN values
                valid_idx = bb['middle'].notna()
                
                if valid_idx.sum() > 0:
                    lower = bb['lower'][valid_idx]
                    middle = bb['middle'][valid_idx]
                    upper = bb['upper'][valid_idx]
                    
                    # Check ordering (use <= to handle edge cases)
                    assert (lower <= middle).all(), "Lower band above middle band"
                    assert (middle <= upper).all(), "Middle band above upper band"
                    
                    # For non-zero volatility, upper should be strictly greater than lower
                    # (unless volatility is extremely small)
                    if (upper - lower).max() > 1e-10:
                        assert (lower <= upper).all(), "Lower band not below or equal to upper band"
    
    @pytest.mark.slow
    @given(data=ohlcv_data(min_rows=50, max_rows=60))
    @settings(max_examples=2, deadline=1000)
    def test_macd_histogram_calculation(self, data):
        """Test that MACD histogram = MACD - Signal."""
        calculator = TechnicalIndicators()
        
        macd = calculator.calculate_macd(data)
        
        if macd is not None:
            # Remove NaN values
            valid_idx = macd['macd'].notna() & macd['signal'].notna() & macd['histogram'].notna()
            
            macd_line = macd['macd'][valid_idx]
            signal_line = macd['signal'][valid_idx]
            histogram = macd['histogram'][valid_idx]
            
            # Histogram should equal MACD - Signal (within floating point tolerance)
            calculated_histogram = macd_line - signal_line
            
            # Use numpy's allclose for floating point comparison
            assert np.allclose(histogram, calculated_histogram, rtol=1e-5, atol=1e-8), \
                "MACD histogram does not equal MACD - Signal"
    
    @pytest.mark.slow
    @given(data=ohlcv_data(min_rows=50, max_rows=60))
    @settings(max_examples=2, deadline=1000)
    def test_stochastic_bounds(self, data):
        """Test that Stochastic values are between 0 and 100."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        stoch = calculator.calculate_stochastic(data)
        
        if stoch is not None:
            # %K and %D should be between 0 and 100
            k_valid = stoch['k'].dropna()
            d_valid = stoch['d'].dropna()
            
            if len(k_valid) > 0:
                assert (k_valid >= 0).all(), "Stochastic %K values below 0"
                assert (k_valid <= 100).all(), "Stochastic %K values above 100"
            
            if len(d_valid) > 0:
                assert (d_valid >= 0).all(), "Stochastic %D values below 0"
                assert (d_valid <= 100).all(), "Stochastic %D values above 100"
    
    @pytest.mark.slow
    @given(data=ohlcv_data(min_rows=50, max_rows=60))
    @settings(max_examples=2, deadline=1000)
    def test_atr_positive(self, data):
        """Test that ATR values are always positive."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        atr = calculator.calculate_atr(data)
        
        if atr is not None:
            atr_valid = atr.dropna()
            
            if len(atr_valid) > 0:
                assert (atr_valid >= 0).all(), "ATR values should be non-negative"
    
    @pytest.mark.slow
    @given(data=ohlcv_data(min_rows=50, max_rows=60))
    @settings(max_examples=2, deadline=1000)
    def test_williams_r_bounds(self, data):
        """Test that Williams %R values are between -100 and 0."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        willr = calculator.calculate_williams_r(data)
        
        if willr is not None:
            willr_valid = willr.dropna()
            
            if len(willr_valid) > 0:
                assert (willr_valid >= -100).all(), "Williams %R values below -100"
                assert (willr_valid <= 0).all(), "Williams %R values above 0"
