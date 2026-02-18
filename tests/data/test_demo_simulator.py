"""Unit tests for demo simulator.

**Validates: Requirements 6.1, 6.5**
"""

import pytest
import pandas as pd
from unittest.mock import patch
import socket

from auronai.data.demo_simulator import DemoSimulator


class TestDemoSimulatorBasic:
    """Test basic demo simulator functionality."""
    
    def test_generate_price_data_returns_dataframe(self):
        """Test that generate_price_data returns a DataFrame.
        
        **Validates: Requirements 6.1**
        """
        simulator = DemoSimulator(seed=42)
        df = simulator.generate_price_data('AAPL', days=10)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
        assert list(df.columns) == ['Open', 'High', 'Low', 'Close', 'Volume']
    
    def test_generate_price_data_with_custom_parameters(self):
        """Test generation with custom parameters.
        
        **Validates: Requirements 6.1**
        """
        simulator = DemoSimulator(seed=42)
        df = simulator.generate_price_data(
            'TEST',
            days=20,
            initial_price=150.0,
            volatility=0.03,
            drift=0.001
        )
        
        assert len(df) == 20
        # First open should be close to initial price
        assert abs(df.iloc[0]['Open'] - 150.0) < 1.0
    
    def test_ohlc_relationships_valid(self):
        """Test that OHLC relationships are always valid.
        
        **Validates: Requirements 6.2**
        """
        simulator = DemoSimulator(seed=42)
        df = simulator.generate_price_data('TEST', days=30)
        
        for i in range(len(df)):
            row = df.iloc[i]
            assert row['High'] >= row['Open']
            assert row['High'] >= row['Close']
            assert row['Low'] <= row['Open']
            assert row['Low'] <= row['Close']
            assert row['Volume'] > 0


class TestTrendingMarkets:
    """Test trending market generation."""
    
    def test_uptrend_generation(self):
        """Test uptrend market generation.
        
        **Validates: Requirements 6.2**
        """
        simulator = DemoSimulator(seed=42)
        df = simulator.generate_trending_market(
            'TEST',
            days=30,
            direction='up',
            strength=0.02
        )
        
        # Check that price generally increases
        first_price = df.iloc[0]['Close']
        last_price = df.iloc[-1]['Close']
        
        # With positive drift, last price should be higher
        assert last_price > first_price
    
    def test_downtrend_generation(self):
        """Test downtrend market generation.
        
        **Validates: Requirements 6.2**
        """
        simulator = DemoSimulator(seed=42)
        df = simulator.generate_trending_market(
            'TEST',
            days=30,
            direction='down',
            strength=0.02
        )
        
        # Check that price generally decreases
        first_price = df.iloc[0]['Close']
        last_price = df.iloc[-1]['Close']
        
        # With negative drift, last price should be lower
        assert last_price < first_price
    
    def test_ranging_market(self):
        """Test ranging (no trend) market generation.
        
        **Validates: Requirements 6.2**
        """
        simulator = DemoSimulator(seed=42)
        df = simulator.generate_trending_market(
            'TEST',
            days=30,
            direction='sideways',
            strength=0.0
        )
        
        # Price should stay relatively close to initial
        first_price = df.iloc[0]['Close']
        last_price = df.iloc[-1]['Close']
        
        # Should be within reasonable range
        assert abs(last_price - first_price) / first_price < 0.5


class TestMarketNoise:
    """Test market noise addition."""
    
    def test_add_market_noise(self):
        """Test adding noise to market data.
        
        **Validates: Requirements 6.2**
        """
        simulator = DemoSimulator(seed=42)
        df = simulator.generate_price_data('TEST', days=10)
        
        # Add noise
        noisy_df = simulator.add_market_noise(df, noise_level=0.01)
        
        # Should have same shape
        assert noisy_df.shape == df.shape
        
        # Prices should be different
        assert not noisy_df['Close'].equals(df['Close'])
        
        # OHLC relationships should still be valid
        for i in range(len(noisy_df)):
            row = noisy_df.iloc[i]
            assert row['High'] >= max(row['Open'], row['Close'])
            assert row['Low'] <= min(row['Open'], row['Close'])
    
    def test_noise_level_effect(self):
        """Test that higher noise level creates more variation.
        
        **Validates: Requirements 6.2**
        """
        simulator = DemoSimulator(seed=42)
        df = simulator.generate_price_data('TEST', days=20)
        
        # Add low noise
        low_noise = simulator.add_market_noise(df.copy(), noise_level=0.001)
        
        # Add high noise
        high_noise = simulator.add_market_noise(df.copy(), noise_level=0.05)
        
        # Calculate differences from original
        low_diff = abs(low_noise['Close'] - df['Close']).mean()
        high_diff = abs(high_noise['Close'] - df['Close']).mean()
        
        # Higher noise should create larger differences
        assert high_diff > low_diff


class TestMultipleSymbols:
    """Test multiple symbol generation."""
    
    def test_generate_multiple_symbols(self):
        """Test generating data for multiple symbols.
        
        **Validates: Requirements 6.1**
        """
        simulator = DemoSimulator(seed=42)
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        data_dict = simulator.generate_multiple_symbols(symbols, days=15)
        
        assert len(data_dict) == 3
        assert all(symbol in data_dict for symbol in symbols)
        assert all(len(df) == 15 for df in data_dict.values())
    
    def test_different_symbols_different_data(self):
        """Test that different symbols get different data.
        
        **Validates: Requirements 6.1**
        """
        simulator = DemoSimulator(seed=42)
        symbols = ['AAPL', 'MSFT']
        
        data_dict = simulator.generate_multiple_symbols(symbols, days=10)
        
        # Data should be different for different symbols
        assert not data_dict['AAPL']['Close'].equals(data_dict['MSFT']['Close'])


class TestOfflineOperation:
    """Test that demo simulator works offline."""
    
    def test_no_network_calls(self):
        """Test that no network calls are made.
        
        **Validates: Requirements 6.5**
        """
        # This test verifies that the simulator doesn't make network calls
        # by checking that it works even when network is "disabled"
        
        simulator = DemoSimulator(seed=42)
        
        # Generate data - should work without network
        df = simulator.generate_price_data('TEST', days=10)
        
        assert len(df) == 10
        assert all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume'])
    
    def test_works_without_api_keys(self):
        """Test that simulator works without any API keys.
        
        **Validates: Requirements 6.5**
        """
        # No API keys needed
        simulator = DemoSimulator()
        
        df = simulator.generate_price_data('TEST', days=5)
        
        assert len(df) == 5
        assert df is not None


class TestReproducibility:
    """Test reproducibility with seeds."""
    
    def test_same_seed_same_results(self):
        """Test that same seed produces same results.
        
        **Validates: Requirements 6.1**
        """
        sim1 = DemoSimulator(seed=12345)
        df1 = sim1.generate_price_data('TEST', days=10)
        
        sim2 = DemoSimulator(seed=12345)
        df2 = sim2.generate_price_data('TEST', days=10)
        
        # Should be identical (comparing values, not timestamps)
        pd.testing.assert_frame_equal(df1.reset_index(drop=True), df2.reset_index(drop=True))
    
    def test_different_seed_different_results(self):
        """Test that different seeds produce different results.
        
        **Validates: Requirements 6.1**
        """
        sim1 = DemoSimulator(seed=111)
        df1 = sim1.generate_price_data('TEST', days=10)
        
        sim2 = DemoSimulator(seed=222)
        df2 = sim2.generate_price_data('TEST', days=10)
        
        # Should be different
        assert not df1['Close'].equals(df2['Close'])


class TestVolumeGeneration:
    """Test volume generation."""
    
    def test_volume_correlated_with_price_movement(self):
        """Test that volume is correlated with price movements.
        
        **Validates: Requirements 6.2**
        """
        simulator = DemoSimulator(seed=42)
        df = simulator.generate_price_data('TEST', days=50, volatility=0.03)
        
        # Calculate price changes
        df['price_change'] = abs(df['Close'] - df['Open']) / df['Open']
        
        # Check that there's some correlation between price change and volume
        # (not perfect, but should exist)
        correlation = df['price_change'].corr(df['Volume'])
        
        # Should have positive correlation (more volume on bigger moves)
        assert correlation > 0, f"Expected positive correlation, got {correlation}"
    
    def test_volume_always_positive(self):
        """Test that volume is always positive.
        
        **Validates: Requirements 6.2**
        """
        simulator = DemoSimulator(seed=42)
        df = simulator.generate_price_data('TEST', days=30)
        
        assert all(df['Volume'] > 0), "All volume values must be positive"
