"""Unit tests for market data provider.

**Validates: Requirements 2.1, 2.6, 11.1**
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import time

from auronai.data.market_data_provider import MarketDataProvider


class TestMarketDataProviderBasic:
    """Test basic market data provider functionality."""
    
    def test_initialization(self):
        """Test provider initialization with custom parameters."""
        provider = MarketDataProvider(
            cache_ttl_seconds=120,
            max_retries=5,
            retry_delays=[0.5, 1.0, 2.0]
        )
        
        assert provider.cache_ttl_seconds == 120
        assert provider.max_retries == 5
        assert provider.retry_delays == [0.5, 1.0, 2.0]
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        provider = MarketDataProvider()
        
        key1 = provider._get_cache_key('AAPL', '1mo', '1d')
        key2 = provider._get_cache_key('AAPL', '1mo', '1d')
        key3 = provider._get_cache_key('MSFT', '1mo', '1d')
        
        assert key1 == key2, "Same parameters should generate same key"
        assert key1 != key3, "Different symbols should generate different keys"


class TestDataRetrieval:
    """Test data retrieval functionality."""
    
    @patch('yfinance.Ticker')
    def test_successful_data_retrieval(self, mock_ticker):
        """Test successful data retrieval from yfinance.
        
        **Validates: Requirements 2.1**
        """
        # Create mock data
        mock_data = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0],
            'High': [101.0, 102.0, 103.0],
            'Low': [99.0, 100.0, 101.0],
            'Close': [100.5, 101.5, 102.5],
            'Volume': [1000000, 1100000, 1200000]
        })
        
        mock_instance = Mock()
        mock_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_instance
        
        provider = MarketDataProvider()
        data = provider.get_historical_data('AAPL', '1mo', '1d')
        
        assert data is not None
        assert len(data) == 3
        assert list(data.columns) == ['Open', 'High', 'Low', 'Close', 'Volume']
    
    @patch('yfinance.Ticker')
    def test_get_current_data(self, mock_ticker):
        """Test getting current market data.
        
        **Validates: Requirements 2.1**
        """
        # Create mock data
        mock_hist = pd.DataFrame({
            'Open': [100.0],
            'High': [101.0],
            'Low': [99.0],
            'Close': [100.5],
            'Volume': [1000000]
        }, index=[pd.Timestamp('2024-01-01 10:00:00')])
        
        mock_instance = Mock()
        mock_instance.history.return_value = mock_hist
        mock_instance.info = {'symbol': 'AAPL'}
        mock_ticker.return_value = mock_instance
        
        provider = MarketDataProvider()
        current = provider.get_current_data('AAPL')
        
        assert current is not None
        assert current['symbol'] == 'AAPL'
        assert current['price'] == 100.5
        assert current['volume'] == 1000000
    
    @patch('yfinance.Ticker')
    def test_get_multiple_symbols(self, mock_ticker):
        """Test retrieving data for multiple symbols.
        
        **Validates: Requirements 2.3**
        """
        mock_data = pd.DataFrame({
            'Open': [100.0],
            'High': [101.0],
            'Low': [99.0],
            'Close': [100.5],
            'Volume': [1000000]
        })
        
        mock_instance = Mock()
        mock_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_instance
        
        provider = MarketDataProvider()
        results = provider.get_multiple_symbols(['AAPL', 'MSFT', 'GOOGL'])
        
        assert len(results) == 3
        assert 'AAPL' in results
        assert 'MSFT' in results
        assert 'GOOGL' in results


class TestDataValidation:
    """Test data validation functionality."""
    
    def test_validate_valid_data(self):
        """Test validation of valid market data.
        
        **Validates: Requirements 2.5**
        """
        provider = MarketDataProvider()
        
        valid_data = pd.DataFrame({
            'Open': [100.0, 101.0],
            'High': [101.0, 102.0],
            'Low': [99.0, 100.0],
            'Close': [100.5, 101.5],
            'Volume': [1000000, 1100000]
        })
        
        assert provider._validate_data(valid_data, 'TEST') is True
    
    def test_validate_empty_data(self):
        """Test validation rejects empty data.
        
        **Validates: Requirements 2.5**
        """
        provider = MarketDataProvider()
        
        empty_data = pd.DataFrame()
        assert provider._validate_data(empty_data, 'TEST') is False
    
    def test_validate_missing_columns(self):
        """Test validation rejects data with missing columns.
        
        **Validates: Requirements 2.5**
        """
        provider = MarketDataProvider()
        
        incomplete_data = pd.DataFrame({
            'Open': [100.0],
            'Close': [100.5]
            # Missing High, Low, Volume
        })
        
        assert provider._validate_data(incomplete_data, 'TEST') is False
    
    def test_validate_data_with_some_nans(self):
        """Test validation allows some NaN values.
        
        **Validates: Requirements 2.5**
        """
        provider = MarketDataProvider()
        
        data_with_nans = pd.DataFrame({
            'Open': [100.0, 101.0, None],
            'High': [101.0, 102.0, 103.0],
            'Low': [99.0, 100.0, 101.0],
            'Close': [100.5, 101.5, 102.5],
            'Volume': [1000000, 1100000, 1200000]
        })
        
        # Should pass with only 1/3 NaN in one column
        assert provider._validate_data(data_with_nans, 'TEST') is True


class TestRetryLogic:
    """Test retry logic with exponential backoff."""
    
    @patch('yfinance.Ticker')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_retry_on_failure(self, mock_sleep, mock_ticker):
        """Test retry logic on network failures.
        
        **Validates: Requirements 11.1**
        """
        # First 2 calls fail, 3rd succeeds
        mock_instance = Mock()
        mock_instance.history.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            pd.DataFrame({
                'Open': [100.0],
                'High': [101.0],
                'Low': [99.0],
                'Close': [100.5],
                'Volume': [1000000]
            })
        ]
        mock_ticker.return_value = mock_instance
        
        provider = MarketDataProvider(max_retries=3, retry_delays=[0.1, 0.2, 0.4])
        data = provider._fetch_with_retry('AAPL', '1mo', '1d')
        
        assert data is not None
        assert mock_instance.history.call_count == 3
        assert mock_sleep.call_count == 2  # Slept twice before final success
    
    @patch('yfinance.Ticker')
    @patch('time.sleep')
    def test_exhausted_retries(self, mock_sleep, mock_ticker):
        """Test behavior when all retries are exhausted.
        
        **Validates: Requirements 11.1**
        """
        # All calls fail
        mock_instance = Mock()
        mock_instance.history.side_effect = Exception("Network error")
        mock_ticker.return_value = mock_instance
        
        provider = MarketDataProvider(max_retries=3)
        data = provider._fetch_with_retry('AAPL', '1mo', '1d')
        
        assert data is None
        assert mock_instance.history.call_count == 3
    
    @patch('yfinance.Ticker')
    @patch('time.sleep')
    def test_exponential_backoff_delays(self, mock_sleep, mock_ticker):
        """Test that retry delays follow exponential backoff pattern.
        
        **Validates: Requirements 11.1**
        """
        mock_instance = Mock()
        mock_instance.history.side_effect = Exception("Network error")
        mock_ticker.return_value = mock_instance
        
        provider = MarketDataProvider(max_retries=3, retry_delays=[1.0, 2.0, 4.0])
        provider._fetch_with_retry('AAPL', '1mo', '1d')
        
        # Check sleep was called with correct delays
        assert mock_sleep.call_count == 2  # 2 retries = 2 sleeps
        mock_sleep.assert_any_call(1.0)
        mock_sleep.assert_any_call(2.0)


class TestCaching:
    """Test caching functionality."""
    
    @patch('yfinance.Ticker')
    def test_cache_hit(self, mock_ticker):
        """Test that cached data is returned on second call.
        
        **Validates: Requirements 2.8**
        """
        mock_data = pd.DataFrame({
            'Open': [100.0],
            'High': [101.0],
            'Low': [99.0],
            'Close': [100.5],
            'Volume': [1000000]
        })
        
        mock_instance = Mock()
        mock_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_instance
        
        provider = MarketDataProvider(cache_ttl_seconds=60)
        
        # First call
        data1 = provider.get_historical_data('AAPL', '1mo', '1d')
        call_count_1 = mock_instance.history.call_count
        
        # Second call (should hit cache)
        data2 = provider.get_historical_data('AAPL', '1mo', '1d')
        call_count_2 = mock_instance.history.call_count
        
        assert call_count_2 == call_count_1, "Should not make additional API call"
        pd.testing.assert_frame_equal(data1.reset_index(drop=True), data2.reset_index(drop=True))
    
    @patch('yfinance.Ticker')
    def test_cache_miss_different_params(self, mock_ticker):
        """Test that different parameters result in cache miss.
        
        **Validates: Requirements 2.8**
        """
        mock_data = pd.DataFrame({
            'Open': [100.0],
            'High': [101.0],
            'Low': [99.0],
            'Close': [100.5],
            'Volume': [1000000]
        })
        
        mock_instance = Mock()
        mock_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_instance
        
        provider = MarketDataProvider()
        
        # Different symbols
        provider.get_historical_data('AAPL', '1mo', '1d')
        provider.get_historical_data('MSFT', '1mo', '1d')
        
        # Should make 2 API calls
        assert mock_instance.history.call_count == 2
    
    def test_clear_cache(self):
        """Test cache clearing functionality."""
        provider = MarketDataProvider()
        
        # Add some data to cache manually
        mock_data = pd.DataFrame({'Close': [100.0]})
        provider._save_to_cache('TEST:1mo:1d', mock_data)
        
        assert len(provider._cache) > 0
        
        provider.clear_cache()
        
        assert len(provider._cache) == 0
    
    def test_cache_stats(self):
        """Test cache statistics."""
        provider = MarketDataProvider()
        
        stats = provider.get_cache_stats()
        
        assert 'total_entries' in stats
        assert 'active_entries' in stats
        assert 'expired_entries' in stats


class TestSymbolValidation:
    """Test symbol validation functionality."""
    
    @patch('yfinance.Ticker')
    def test_validate_valid_symbol(self, mock_ticker):
        """Test validation of valid symbol.
        
        **Validates: Requirements 2.6**
        """
        mock_instance = Mock()
        mock_instance.info = {'symbol': 'AAPL'}
        mock_instance.history.return_value = pd.DataFrame({
            'Close': [100.0, 101.0]
        })
        mock_ticker.return_value = mock_instance
        
        provider = MarketDataProvider()
        assert provider.validate_symbol('AAPL') is True
    
    @patch('yfinance.Ticker')
    def test_validate_invalid_symbol(self, mock_ticker):
        """Test validation rejects invalid symbol.
        
        **Validates: Requirements 2.6**
        """
        mock_instance = Mock()
        mock_instance.info = {}  # Empty info
        mock_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_instance
        
        provider = MarketDataProvider()
        assert provider.validate_symbol('INVALID') is False
    
    @patch('yfinance.Ticker')
    def test_validate_symbol_with_no_data(self, mock_ticker):
        """Test validation rejects symbol with no recent data.
        
        **Validates: Requirements 2.6**
        """
        mock_instance = Mock()
        mock_instance.info = {'symbol': 'TEST'}
        mock_instance.history.return_value = pd.DataFrame()  # No data
        mock_ticker.return_value = mock_instance
        
        provider = MarketDataProvider()
        assert provider.validate_symbol('TEST') is False
