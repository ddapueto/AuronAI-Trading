"""Property-based tests for market data provider.

**Validates: Requirements 2.8**
"""

from hypothesis import given, strategies as st, settings
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch

from auronai.data.market_data_provider import MarketDataProvider


# Property 4: Data Caching Consistency
@given(
    symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu',))),
    period=st.sampled_from(['1d', '5d', '1mo', '3mo']),
    interval=st.sampled_from(['1d', '1h']),
    cache_ttl=st.integers(min_value=1, max_value=300)
)
@settings(max_examples=20, deadline=None)  # Reduced examples for faster testing
def test_property_data_caching_consistency(symbol, period, interval, cache_ttl):
    """
    **Property 4: Data Caching Consistency**
    
    For any symbol and timeframe, retrieving data twice within the cache TTL
    should return identical results without making additional API calls.
    
    **Validates: Requirements 2.8**
    """
    provider = MarketDataProvider(cache_ttl_seconds=cache_ttl)
    
    # Create mock data
    mock_data = pd.DataFrame({
        'Open': [100.0, 101.0, 102.0],
        'High': [101.0, 102.0, 103.0],
        'Low': [99.0, 100.0, 101.0],
        'Close': [100.5, 101.5, 102.5],
        'Volume': [1000000, 1100000, 1200000]
    })
    
    # Mock yfinance to return our test data
    with patch('yfinance.Ticker') as mock_ticker:
        mock_instance = Mock()
        mock_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_instance
        
        # First call - should hit the API
        data1 = provider.get_historical_data(symbol, period, interval)
        call_count_after_first = mock_instance.history.call_count
        
        # Second call - should hit cache
        data2 = provider.get_historical_data(symbol, period, interval)
        call_count_after_second = mock_instance.history.call_count
        
        # Verify caching behavior
        assert call_count_after_second == call_count_after_first, \
            "Second call should not make additional API calls (should use cache)"
        
        # Verify data consistency
        assert data1 is not None, "First call should return data"
        assert data2 is not None, "Second call should return data"
        
        # Data should be identical
        pd.testing.assert_frame_equal(
            data1.reset_index(drop=True),
            data2.reset_index(drop=True),
            check_dtype=False
        )


@given(
    symbols=st.lists(
        st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=('Lu',))),
        min_size=1,
        max_size=3,
        unique=True
    )
)
@settings(max_examples=10, deadline=None)
def test_property_cache_isolation_per_symbol(symbols):
    """
    **Property: Cache Isolation Per Symbol**
    
    For any set of symbols, cached data for one symbol should not affect
    cached data for another symbol.
    
    **Validates: Requirements 2.8**
    """
    provider = MarketDataProvider(cache_ttl_seconds=60)
    
    # Create different mock data for each symbol
    mock_data_map = {}
    for i, symbol in enumerate(symbols):
        mock_data_map[symbol] = pd.DataFrame({
            'Open': [100.0 + i, 101.0 + i],
            'High': [101.0 + i, 102.0 + i],
            'Low': [99.0 + i, 100.0 + i],
            'Close': [100.5 + i, 101.5 + i],
            'Volume': [1000000 + i * 100000, 1100000 + i * 100000]
        })
    
    with patch('yfinance.Ticker') as mock_ticker:
        def get_mock_ticker(symbol):
            mock_instance = Mock()
            mock_instance.history.return_value = mock_data_map.get(symbol, pd.DataFrame())
            return mock_instance
        
        mock_ticker.side_effect = get_mock_ticker
        
        # Fetch data for all symbols
        results = {}
        for symbol in symbols:
            data = provider.get_historical_data(symbol, '1mo', '1d')
            if data is not None:
                results[symbol] = data
        
        # Verify each symbol has unique data
        if len(results) > 1:
            symbols_list = list(results.keys())
            for i in range(len(symbols_list)):
                for j in range(i + 1, len(symbols_list)):
                    sym1, sym2 = symbols_list[i], symbols_list[j]
                    # Data should be different for different symbols
                    assert not results[sym1]['Close'].equals(results[sym2]['Close']), \
                        f"Data for {sym1} and {sym2} should be different"


def test_property_cache_expiration():
    """
    **Property: Cache Expiration**
    
    For any cached data, after the TTL expires, the next request should
    fetch fresh data from the API.
    
    **Validates: Requirements 2.8**
    """
    provider = MarketDataProvider(cache_ttl_seconds=1)  # 1 second TTL
    
    mock_data1 = pd.DataFrame({
        'Open': [100.0],
        'High': [101.0],
        'Low': [99.0],
        'Close': [100.5],
        'Volume': [1000000]
    })
    
    mock_data2 = pd.DataFrame({
        'Open': [200.0],
        'High': [201.0],
        'Low': [199.0],
        'Close': [200.5],
        'Volume': [2000000]
    })
    
    with patch('yfinance.Ticker') as mock_ticker:
        mock_instance = Mock()
        # First call returns data1, second call returns data2
        mock_instance.history.side_effect = [mock_data1, mock_data2]
        mock_ticker.return_value = mock_instance
        
        # First call
        data1 = provider.get_historical_data('TEST', '1mo', '1d')
        
        # Wait for cache to expire
        import time
        time.sleep(1.1)
        
        # Second call after expiration
        data2 = provider.get_historical_data('TEST', '1mo', '1d')
        
        # Should have made 2 API calls
        assert mock_instance.history.call_count == 2, \
            "Should make new API call after cache expiration"
        
        # Data should be different
        assert data1 is not None and data2 is not None
        assert not data1['Close'].equals(data2['Close']), \
            "Data should be different after cache expiration"
