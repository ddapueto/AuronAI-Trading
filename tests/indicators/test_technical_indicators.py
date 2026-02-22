"""Unit tests for technical indicators.

These tests verify indicator calculations with known test cases and edge cases.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytest

from auronai.indicators import TechnicalIndicators


@pytest.fixture
def sample_data():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range(start='2024-01-01', periods=250, freq='D')
    
    # Generate simple trending data
    close_prices = np.linspace(100, 150, 250)
    
    data = pd.DataFrame({
        'Open': close_prices * 0.99,
        'High': close_prices * 1.02,
        'Low': close_prices * 0.98,
        'Close': close_prices,
        'Volume': np.random.randint(1000000, 5000000, 250)
    }, index=dates)
    
    return data


@pytest.fixture
def insufficient_data():
    """Create insufficient data for testing."""
    dates = pd.date_range(start='2024-01-01', periods=5, freq='D')
    
    data = pd.DataFrame({
        'Open': [100, 101, 102, 103, 104],
        'High': [102, 103, 104, 105, 106],
        'Low': [99, 100, 101, 102, 103],
        'Close': [101, 102, 103, 104, 105],
        'Volume': [1000000] * 5
    }, index=dates)
    
    return data


@pytest.fixture
def zero_volatility_data():
    """Create data with zero volatility (flat prices)."""
    dates = pd.date_range(start='2024-01-01', periods=250, freq='D')
    
    data = pd.DataFrame({
        'Open': [100] * 250,
        'High': [100] * 250,
        'Low': [100] * 250,
        'Close': [100] * 250,
        'Volume': [1000000] * 250
    }, index=dates)
    
    return data


class TestRSI:
    """Test RSI calculation."""
    
    def test_rsi_calculation(self, sample_data):
        """Test RSI with sample data."""
        calculator = TechnicalIndicators()
        
        rsi = calculator.calculate_rsi(sample_data)
        
        assert rsi is not None
        assert len(rsi) == len(sample_data)
        
        # RSI should be between 0 and 100
        rsi_valid = rsi.dropna()
        assert (rsi_valid >= 0).all()
        assert (rsi_valid <= 100).all()
        
        # For uptrending data, RSI should be > 50
        assert rsi.iloc[-1] > 50
    
    def test_rsi_insufficient_data(self, insufficient_data):
        """Test RSI with insufficient data."""
        calculator = TechnicalIndicators()
        
        rsi = calculator.calculate_rsi(insufficient_data, period=14)
        
        # Should return None for insufficient data
        assert rsi is None
    
    def test_rsi_custom_period(self, sample_data):
        """Test RSI with custom period."""
        calculator = TechnicalIndicators()
        
        rsi_14 = calculator.calculate_rsi(sample_data, period=14)
        rsi_7 = calculator.calculate_rsi(sample_data, period=7)
        
        assert rsi_14 is not None
        assert rsi_7 is not None
        
        # Shorter period should have more data points
        assert len(rsi_7.dropna()) >= len(rsi_14.dropna())
    
    def test_rsi_zero_volatility(self, zero_volatility_data):
        """Test RSI with zero volatility."""
        calculator = TechnicalIndicators()
        
        rsi = calculator.calculate_rsi(zero_volatility_data)
        
        # RSI should be 50 for flat prices (no gains or losses)
        if rsi is not None:
            rsi_valid = rsi.dropna()
            if len(rsi_valid) > 0:
                # Allow some tolerance for numerical precision
                assert np.allclose(rsi_valid, 50, atol=1)


class TestMACD:
    """Test MACD calculation."""
    
    def test_macd_calculation(self, sample_data):
        """Test MACD with sample data."""
        calculator = TechnicalIndicators()
        
        macd = calculator.calculate_macd(sample_data)
        
        assert macd is not None
        assert 'macd' in macd
        assert 'signal' in macd
        assert 'histogram' in macd
        
        # Histogram should equal MACD - Signal
        valid_idx = (macd['macd'].notna() & 
                    macd['signal'].notna() & 
                    macd['histogram'].notna())
        
        if valid_idx.any():
            calculated_hist = macd['macd'][valid_idx] - macd['signal'][valid_idx]
            assert np.allclose(macd['histogram'][valid_idx], calculated_hist, rtol=1e-5)
    
    def test_macd_insufficient_data(self, insufficient_data):
        """Test MACD with insufficient data."""
        calculator = TechnicalIndicators()
        
        macd = calculator.calculate_macd(insufficient_data)
        
        # Should return None for insufficient data
        assert macd is None
    
    def test_macd_custom_parameters(self, sample_data):
        """Test MACD with custom parameters."""
        calculator = TechnicalIndicators()
        
        macd = calculator.calculate_macd(sample_data, fast=8, slow=17, signal=9)
        
        assert macd is not None
        assert 'macd' in macd
        assert 'signal' in macd
        assert 'histogram' in macd


class TestBollingerBands:
    """Test Bollinger Bands calculation."""
    
    def test_bollinger_bands_calculation(self, sample_data):
        """Test Bollinger Bands with sample data."""
        calculator = TechnicalIndicators()
        
        bb = calculator.calculate_bollinger_bands(sample_data)
        
        assert bb is not None
        assert 'upper' in bb
        assert 'middle' in bb
        assert 'lower' in bb
        
        # Check ordering: lower < middle < upper
        valid_idx = bb['middle'].notna()
        
        if valid_idx.any():
            assert (bb['lower'][valid_idx] <= bb['middle'][valid_idx]).all()
            assert (bb['middle'][valid_idx] <= bb['upper'][valid_idx]).all()
    
    def test_bollinger_bands_insufficient_data(self, insufficient_data):
        """Test Bollinger Bands with insufficient data."""
        calculator = TechnicalIndicators()
        
        bb = calculator.calculate_bollinger_bands(insufficient_data, period=20)
        
        # Should return None for insufficient data
        assert bb is None
    
    def test_bollinger_bands_custom_parameters(self, sample_data):
        """Test Bollinger Bands with custom parameters."""
        calculator = TechnicalIndicators()
        
        bb_2std = calculator.calculate_bollinger_bands(sample_data, period=20, std=2.0)
        bb_3std = calculator.calculate_bollinger_bands(sample_data, period=20, std=3.0)
        
        assert bb_2std is not None
        assert bb_3std is not None
        
        # 3 std bands should be wider than or equal to 2 std bands
        assert bb_3std['upper'].iloc[-1] >= bb_2std['upper'].iloc[-1]
        assert bb_3std['lower'].iloc[-1] <= bb_2std['lower'].iloc[-1]
        
        # Middle band should be the same
        assert np.allclose(bb_3std['middle'].iloc[-1], bb_2std['middle'].iloc[-1])


class TestEMA:
    """Test EMA calculation."""
    
    def test_ema_calculation(self, sample_data):
        """Test EMA with sample data."""
        calculator = TechnicalIndicators()
        
        ema_20 = calculator.calculate_ema(sample_data, period=20)
        
        assert ema_20 is not None
        assert len(ema_20) == len(sample_data)
        
        # EMA should follow price trend
        # For uptrending data, EMA should be increasing
        ema_valid = ema_20.dropna()
        if len(ema_valid) > 10:
            assert ema_valid.iloc[-1] > ema_valid.iloc[0]
    
    def test_ema_insufficient_data(self, insufficient_data):
        """Test EMA with insufficient data."""
        calculator = TechnicalIndicators()
        
        ema = calculator.calculate_ema(insufficient_data, period=20)
        
        # Should return None for insufficient data
        assert ema is None
    
    def test_ema_multiple_periods(self, sample_data):
        """Test EMA with multiple periods."""
        calculator = TechnicalIndicators()
        
        ema_20 = calculator.calculate_ema(sample_data, period=20)
        ema_50 = calculator.calculate_ema(sample_data, period=50)
        ema_200 = calculator.calculate_ema(sample_data, period=200)
        
        assert ema_20 is not None
        assert ema_50 is not None
        # EMA 200 might be None if not enough data
        
        # Shorter period EMA should react faster to price changes
        if ema_50 is not None:
            # For uptrending data, shorter EMA should be above longer EMA
            assert ema_20.iloc[-1] > ema_50.iloc[-1]


class TestStochastic:
    """Test Stochastic Oscillator calculation."""
    
    def test_stochastic_calculation(self, sample_data):
        """Test Stochastic with sample data."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        stoch = calculator.calculate_stochastic(sample_data)
        
        assert stoch is not None
        assert 'k' in stoch
        assert 'd' in stoch
        
        # Values should be between 0 and 100
        k_valid = stoch['k'].dropna()
        d_valid = stoch['d'].dropna()
        
        if len(k_valid) > 0:
            assert (k_valid >= 0).all()
            assert (k_valid <= 100).all()
        
        if len(d_valid) > 0:
            assert (d_valid >= 0).all()
            assert (d_valid <= 100).all()
    
    def test_stochastic_insufficient_data(self, insufficient_data):
        """Test Stochastic with insufficient data."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        stoch = calculator.calculate_stochastic(insufficient_data)
        
        # Should return None for insufficient data
        assert stoch is None


class TestATR:
    """Test ATR calculation."""
    
    def test_atr_calculation(self, sample_data):
        """Test ATR with sample data."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        atr = calculator.calculate_atr(sample_data)
        
        assert atr is not None
        
        # ATR should be positive
        atr_valid = atr.dropna()
        assert (atr_valid >= 0).all()
    
    def test_atr_insufficient_data(self, insufficient_data):
        """Test ATR with insufficient data."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        atr = calculator.calculate_atr(insufficient_data, period=14)
        
        # Should return None for insufficient data
        assert atr is None
    
    def test_atr_zero_volatility(self, zero_volatility_data):
        """Test ATR with zero volatility."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        atr = calculator.calculate_atr(zero_volatility_data)
        
        # ATR should be 0 or very close to 0 for flat prices
        if atr is not None:
            atr_valid = atr.dropna()
            if len(atr_valid) > 0:
                assert np.allclose(atr_valid, 0, atol=0.01)


class TestOBV:
    """Test OBV calculation."""
    
    def test_obv_calculation(self, sample_data):
        """Test OBV with sample data."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        obv = calculator.calculate_obv(sample_data)
        
        assert obv is not None
        assert len(obv) == len(sample_data)
    
    def test_obv_insufficient_data(self, insufficient_data):
        """Test OBV with insufficient data."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        # OBV only needs 2 data points
        obv = calculator.calculate_obv(insufficient_data)
        
        assert obv is not None


class TestADX:
    """Test ADX calculation."""

    def test_adx_calculation(self, sample_data):
        """Test ADX with sample data."""
        calculator = TechnicalIndicators(advanced_mode=True)

        adx = calculator.calculate_adx(sample_data)

        assert adx is not None

        # ADX should be between 0 and 100
        adx_valid = adx.dropna()
        if len(adx_valid) > 0:
            assert (adx_valid >= 0).all()
            assert (adx_valid <= 100).all()

    def test_adx_insufficient_data(self, insufficient_data):
        """Test ADX with insufficient data."""
        calculator = TechnicalIndicators(advanced_mode=True)

        adx = calculator.calculate_adx(insufficient_data)

        assert adx is None


class TestVWAP:
    """Test VWAP calculation."""

    def test_vwap_calculation(self, sample_data):
        """Test VWAP with sample data."""
        calculator = TechnicalIndicators(advanced_mode=True)

        vwap = calculator.calculate_vwap(sample_data)

        assert vwap is not None
        assert len(vwap) == len(sample_data)

        # VWAP should be within the price range
        vwap_valid = vwap.dropna()
        if len(vwap_valid) > 0:
            assert vwap_valid.iloc[-1] > 0

    def test_vwap_insufficient_data(self):
        """Test VWAP with insufficient data."""
        calculator = TechnicalIndicators(advanced_mode=True)

        dates = pd.date_range(start='2024-01-01', periods=1, freq='D')
        data = pd.DataFrame({
            'Open': [100],
            'High': [102],
            'Low': [99],
            'Close': [101],
            'Volume': [1000000],
        }, index=dates)

        vwap = calculator.calculate_vwap(data)

        assert vwap is None


class TestIchimoku:
    """Test Ichimoku Cloud calculation."""

    def test_ichimoku_calculation(self, sample_data):
        """Test Ichimoku with sample data."""
        calculator = TechnicalIndicators(advanced_mode=True)

        ichimoku = calculator.calculate_ichimoku(sample_data)

        assert ichimoku is not None
        assert 'tenkan' in ichimoku
        assert 'kijun' in ichimoku
        assert 'senkou_a' in ichimoku
        assert 'senkou_b' in ichimoku
        assert 'chikou' in ichimoku

    def test_ichimoku_insufficient_data(self, insufficient_data):
        """Test Ichimoku with insufficient data."""
        calculator = TechnicalIndicators(advanced_mode=True)

        ichimoku = calculator.calculate_ichimoku(insufficient_data)

        assert ichimoku is None


class TestSupertrend:
    """Test Supertrend calculation."""

    def test_supertrend_calculation(self, sample_data):
        """Test Supertrend with sample data."""
        calculator = TechnicalIndicators(advanced_mode=True)

        st = calculator.calculate_supertrend(sample_data)

        assert st is not None
        assert 'supertrend' in st
        assert 'direction' in st

    def test_supertrend_direction_values(self, sample_data):
        """Test Supertrend direction is +1 or -1."""
        calculator = TechnicalIndicators(advanced_mode=True)

        st = calculator.calculate_supertrend(sample_data)

        assert st is not None
        dir_valid = st['direction'].dropna()
        if len(dir_valid) > 0:
            assert set(dir_valid.unique()).issubset({1, -1})

    def test_supertrend_insufficient_data(self, insufficient_data):
        """Test Supertrend with insufficient data."""
        calculator = TechnicalIndicators(advanced_mode=True)

        st = calculator.calculate_supertrend(insufficient_data)

        assert st is None


class TestKeltnerChannels:
    """Test Keltner Channels calculation."""

    def test_keltner_channels_calculation(self, sample_data):
        """Test Keltner Channels with sample data."""
        calculator = TechnicalIndicators(advanced_mode=True)

        kc = calculator.calculate_keltner_channels(sample_data)

        assert kc is not None
        assert 'upper' in kc
        assert 'middle' in kc
        assert 'lower' in kc

    def test_keltner_channels_ordering(self, sample_data):
        """Test that lower <= middle <= upper."""
        calculator = TechnicalIndicators(advanced_mode=True)

        kc = calculator.calculate_keltner_channels(sample_data)

        assert kc is not None
        valid_idx = kc['middle'].notna() & kc['upper'].notna() & kc['lower'].notna()
        if valid_idx.any():
            assert (kc['lower'][valid_idx] <= kc['middle'][valid_idx]).all()
            assert (kc['middle'][valid_idx] <= kc['upper'][valid_idx]).all()

    def test_keltner_channels_insufficient_data(self, insufficient_data):
        """Test Keltner Channels with insufficient data."""
        calculator = TechnicalIndicators(advanced_mode=True)

        kc = calculator.calculate_keltner_channels(insufficient_data)

        assert kc is None


class TestFibonacciRetracements:
    """Test Fibonacci Retracement levels calculation."""

    def test_fibonacci_calculation(self, sample_data):
        """Test Fibonacci with sample data."""
        calculator = TechnicalIndicators(advanced_mode=True)

        fib = calculator.calculate_fibonacci_retracements(sample_data)

        assert fib is not None
        assert '0.0' in fib
        assert '0.236' in fib
        assert '0.382' in fib
        assert '0.5' in fib
        assert '0.618' in fib
        assert '0.786' in fib
        assert '1.0' in fib

    def test_fibonacci_level_ordering(self, sample_data):
        """Test that Fibonacci levels are properly ordered (descending)."""
        calculator = TechnicalIndicators(advanced_mode=True)

        fib = calculator.calculate_fibonacci_retracements(sample_data)

        assert fib is not None
        # 0.0 is swing high, 1.0 is swing low
        assert fib['0.0'] >= fib['0.236']
        assert fib['0.236'] >= fib['0.382']
        assert fib['0.382'] >= fib['0.5']
        assert fib['0.5'] >= fib['0.618']
        assert fib['0.618'] >= fib['0.786']
        assert fib['0.786'] >= fib['1.0']

    def test_fibonacci_swing_values(self, sample_data):
        """Test that 0.0 is swing high and 1.0 is swing low."""
        calculator = TechnicalIndicators(advanced_mode=True)

        fib = calculator.calculate_fibonacci_retracements(
            sample_data, period=120
        )

        assert fib is not None
        recent = sample_data.iloc[-120:]
        expected_high = float(recent['High'].max())
        expected_low = float(recent['Low'].min())

        assert np.isclose(fib['0.0'], expected_high)
        assert np.isclose(fib['1.0'], expected_low)

    def test_fibonacci_insufficient_data(self, insufficient_data):
        """Test Fibonacci with insufficient data."""
        calculator = TechnicalIndicators(advanced_mode=True)

        fib = calculator.calculate_fibonacci_retracements(
            insufficient_data, period=120
        )

        assert fib is None


class TestCMF:
    """Test Chaikin Money Flow calculation."""

    def test_cmf_calculation(self, sample_data):
        """Test CMF with sample data."""
        calculator = TechnicalIndicators(advanced_mode=True)

        cmf = calculator.calculate_cmf(sample_data)

        assert cmf is not None

    def test_cmf_bounds(self, sample_data):
        """Test that CMF values are between -1 and 1."""
        calculator = TechnicalIndicators(advanced_mode=True)

        cmf = calculator.calculate_cmf(sample_data)

        assert cmf is not None
        cmf_valid = cmf.dropna()
        if len(cmf_valid) > 0:
            assert (cmf_valid >= -1).all()
            assert (cmf_valid <= 1).all()

    def test_cmf_insufficient_data(self, insufficient_data):
        """Test CMF with insufficient data."""
        calculator = TechnicalIndicators(advanced_mode=True)

        cmf = calculator.calculate_cmf(insufficient_data)

        assert cmf is None


class TestAdvancedIndicators:
    """Test advanced indicators (Williams %R, CCI, ROC)."""
    
    def test_williams_r_calculation(self, sample_data):
        """Test Williams %R with sample data."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        willr = calculator.calculate_williams_r(sample_data)
        
        assert willr is not None
        
        # Williams %R should be between -100 and 0
        willr_valid = willr.dropna()
        if len(willr_valid) > 0:
            assert (willr_valid >= -100).all()
            assert (willr_valid <= 0).all()
    
    def test_cci_calculation(self, sample_data):
        """Test CCI with sample data."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        cci = calculator.calculate_cci(sample_data)
        
        assert cci is not None
    
    def test_roc_calculation(self, sample_data):
        """Test ROC with sample data."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        roc = calculator.calculate_roc(sample_data)
        
        assert roc is not None
        
        # For uptrending data, ROC should be mostly positive
        roc_valid = roc.dropna()
        if len(roc_valid) > 10:
            assert roc_valid.mean() > 0


class TestCalculateAllIndicators:
    """Test calculate_all_indicators method."""
    
    def test_basic_mode(self, sample_data):
        """Test calculate_all_indicators in basic mode."""
        calculator = TechnicalIndicators(advanced_mode=False)
        
        result = calculator.calculate_all_indicators(sample_data)
        
        # Should have basic indicators
        assert 'rsi' in result
        assert 'macd' in result
        assert 'bollinger_bands' in result
        assert 'ema_20' in result
        assert 'ema_50' in result
        
        # OBV is always calculated (basic indicator)
        assert 'obv' in result

        # Should NOT have advanced-only indicators
        assert 'stochastic' not in result
        assert 'atr' not in result
        assert 'vwap' not in result
        assert 'ichimoku' not in result
        assert 'supertrend' not in result
        assert 'keltner_channels' not in result
        assert 'fibonacci' not in result
        assert 'cmf' not in result
    
    def test_advanced_mode(self, sample_data):
        """Test calculate_all_indicators in advanced mode."""
        calculator = TechnicalIndicators(advanced_mode=True)

        result = calculator.calculate_all_indicators(sample_data)

        # Should have all indicators
        assert 'rsi' in result
        assert 'macd' in result
        assert 'bollinger_bands' in result
        assert 'ema_20' in result
        assert 'ema_50' in result
        assert 'stochastic' in result
        assert 'atr' in result
        assert 'obv' in result
        assert 'williams_r' in result
        assert 'cci' in result
        assert 'roc' in result
        # New indicators
        assert 'adx' in result
        assert 'vwap' in result
        assert 'ichimoku' in result
        assert 'supertrend' in result
        assert 'keltner_channels' in result
        assert 'fibonacci' in result
        assert 'cmf' in result
    
    def test_indicator_structure(self, sample_data):
        """Test that indicators have correct structure."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        result = calculator.calculate_all_indicators(sample_data)
        
        # RSI should have value, previous, trend
        assert 'value' in result['rsi']
        assert 'previous' in result['rsi']
        assert 'trend' in result['rsi']
        assert result['rsi']['trend'] in ['up', 'down']
        
        # MACD should have value, signal, histogram, trend
        assert 'value' in result['macd']
        assert 'signal' in result['macd']
        assert 'histogram' in result['macd']
        assert 'trend' in result['macd']
        assert result['macd']['trend'] in ['bullish', 'bearish']
        
        # Bollinger Bands should have upper, middle, lower, position
        assert 'upper' in result['bollinger_bands']
        assert 'middle' in result['bollinger_bands']
        assert 'lower' in result['bollinger_bands']
        assert 'position' in result['bollinger_bands']
        assert result['bollinger_bands']['position'] in [
            'above_upper', 'below_lower', 'upper_half', 'lower_half'
        ]
    
    def test_insufficient_data_handling(self, insufficient_data):
        """Test that insufficient data is handled gracefully."""
        calculator = TechnicalIndicators(advanced_mode=True)
        
        result = calculator.calculate_all_indicators(insufficient_data)
        
        # Should return empty dict or dict with None values
        # Most indicators should not be present due to insufficient data
        assert isinstance(result, dict)
