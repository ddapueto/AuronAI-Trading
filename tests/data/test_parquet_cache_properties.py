"""
Property-based tests for ParquetCache.

Tests universal properties that should hold for all valid inputs.
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from auronai.data.parquet_cache import ParquetCache


# Strategies for generating test data

@st.composite
def ohlcv_dataframe(draw, min_rows=10, max_rows=100):
    """Generate valid OHLCV DataFrame."""
    num_rows = draw(st.integers(min_value=min_rows, max_value=max_rows))
    
    # Generate dates
    start_date = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2023, 12, 31)
    ))
    dates = pd.date_range(start=start_date, periods=num_rows, freq='D')
    
    # Generate OHLC data with valid relationships
    base_price = draw(st.floats(min_value=10.0, max_value=1000.0))
    
    data = []
    for _ in range(num_rows):
        # Generate Low first
        low = draw(st.floats(
            min_value=base_price * 0.95,
            max_value=base_price * 1.05
        ))
        
        # High must be >= Low
        high = draw(st.floats(
            min_value=low,
            max_value=low * 1.1
        ))
        
        # Open and Close must be between Low and High
        open_price = draw(st.floats(min_value=low, max_value=high))
        close_price = draw(st.floats(min_value=low, max_value=high))
        
        # Volume must be non-negative
        volume = draw(st.integers(min_value=0, max_value=1000000000))
        
        data.append({
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close_price,
            'Volume': volume
        })
        
        # Update base price for next iteration
        base_price = close_price
    
    df = pd.DataFrame(data, index=dates)
    return df


@st.composite
def symbol_strategy(draw):
    """Generate valid stock symbols."""
    # Generate 1-5 uppercase letters
    length = draw(st.integers(min_value=1, max_value=5))
    letters = draw(st.lists(
        st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
        min_size=length,
        max_size=length
    ))
    return ''.join(letters)


# Property Tests

class TestParquetCacheProperties:
    """Property-based tests for ParquetCache."""
    
    @given(
        symbol=symbol_strategy(),
        data=ohlcv_dataframe()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_1_data_persistence_round_trip(self, symbol, data):
        """
        Property 1: Data Persistence Round Trip
        
        For any OHLCV dataset, saving to Parquet and then loading
        should produce an equivalent dataset.
        
        **Feature: swing-strategy-lab, Property 1: Data round trip**
        **Validates: Requirements FR-1, FR-2**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ParquetCache(cache_dir=tmpdir)
            
            # Save data
            data_version = cache.save_data(symbol, data)
            
            # Load data back
            start_date = data.index.min()
            end_date = data.index.max()
            loaded_data = cache.get_data(symbol, start_date, end_date)
            
            # Assert data is not None
            assert loaded_data is not None, "Loaded data should not be None"
            
            # Assert same shape
            assert loaded_data.shape == data.shape, \
                f"Shape mismatch: {loaded_data.shape} != {data.shape}"
            
            # Assert same columns
            assert set(loaded_data.columns) == set(data.columns), \
                "Columns mismatch"
            
            # Assert same index (dates) - compare values only
            assert (loaded_data.index == data.index).all(), \
                "Index dates mismatch"
            
            # Assert same values (with tolerance for floating point)
            # Reset index to avoid frequency comparison issues
            loaded_reset = loaded_data.reset_index()
            data_reset = data.reset_index()
            
            pd.testing.assert_frame_equal(
                loaded_reset[sorted(data.columns)],
                data_reset[sorted(data.columns)],
                check_dtype=False,
                rtol=1e-5
            )
            
            # Verify dates match
            assert (loaded_reset['index'] == data_reset['index']).all()
            
            # Assert data version is consistent
            assert cache.get_data_version(symbol) == data_version
    
    @given(
        symbol=symbol_strategy(),
        data=ohlcv_dataframe()
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.data_too_large]
    )
    def test_property_data_version_determinism(self, symbol, data):
        """
        Property: Data version should be deterministic.
        
        Saving the same data twice should produce the same data_version.
        
        **Feature: swing-strategy-lab, Property: Data version determinism**
        **Validates: Requirements FR-4**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ParquetCache(cache_dir=tmpdir)
            
            # Save data first time
            version1 = cache.save_data(symbol, data)
            
            # Clear and save again
            cache.clear_cache(symbol)
            version2 = cache.save_data(symbol, data)
            
            # Versions should be identical
            assert version1 == version2, \
                "Data version should be deterministic for same data"
    
    @given(
        symbol=symbol_strategy(),
        data=ohlcv_dataframe(min_rows=50)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_partial_date_range_retrieval(self, symbol, data):
        """
        Property: Partial date range retrieval.
        
        Loading a subset of the date range should return only that subset.
        
        **Feature: swing-strategy-lab, Property: Partial retrieval**
        **Validates: Requirements FR-2**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ParquetCache(cache_dir=tmpdir)
            
            # Save full data
            cache.save_data(symbol, data)
            
            # Load middle 50% of date range
            all_dates = data.index
            start_idx = len(all_dates) // 4
            end_idx = 3 * len(all_dates) // 4
            
            start_date = all_dates[start_idx]
            end_date = all_dates[end_idx]
            
            loaded_data = cache.get_data(symbol, start_date, end_date)
            
            assert loaded_data is not None
            
            # All loaded dates should be within requested range
            assert (loaded_data.index >= start_date).all()
            assert (loaded_data.index <= end_date).all()
            
            # Should have approximately the right number of rows
            # (allowing for some tolerance due to date filtering)
            expected_rows = end_idx - start_idx + 1
            assert abs(len(loaded_data) - expected_rows) <= 5
    
    @given(
        symbol=symbol_strategy(),
        data=ohlcv_dataframe()
    )
    @settings(max_examples=50, deadline=None)
    def test_property_cache_metadata_consistency(self, symbol, data):
        """
        Property: Cache metadata consistency.
        
        Metadata should accurately reflect cached data.
        
        **Feature: swing-strategy-lab, Property: Metadata consistency**
        **Validates: Requirements FR-4**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ParquetCache(cache_dir=tmpdir)
            
            # Save data
            cache.save_data(symbol, data)
            
            # Get metadata
            info = cache.get_cache_info(symbol)
            
            assert info is not None
            assert 'data_version' in info
            assert 'last_updated' in info
            assert 'start_date' in info
            assert 'end_date' in info
            assert 'num_records' in info
            
            # Verify metadata accuracy
            assert info['num_records'] == len(data)
            
            # Verify symbol is in cached list
            assert symbol in cache.get_cached_symbols()
    
    @given(
        symbol=symbol_strategy(),
        data=ohlcv_dataframe()
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.data_too_large]
    )
    def test_property_clear_cache_removes_data(self, symbol, data):
        """
        Property: Clear cache removes data.
        
        After clearing cache, data should not be retrievable.
        
        **Feature: swing-strategy-lab, Property: Cache clearing**
        **Validates: Requirements FR-2**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ParquetCache(cache_dir=tmpdir)
            
            # Save data
            cache.save_data(symbol, data)
            
            # Verify data exists
            start_date = data.index.min()
            end_date = data.index.max()
            assert cache.get_data(symbol, start_date, end_date) is not None
            
            # Clear cache
            cache.clear_cache(symbol)
            
            # Data should no longer be retrievable
            assert cache.get_data(symbol, start_date, end_date) is None
            assert cache.get_data_version(symbol) is None
            assert symbol not in cache.get_cached_symbols()


# Unit tests for edge cases

class TestParquetCacheEdgeCases:
    """Unit tests for specific edge cases."""
    
    def test_empty_dataframe_raises_error(self):
        """Empty DataFrame should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ParquetCache(cache_dir=tmpdir)
            
            empty_df = pd.DataFrame()
            
            with pytest.raises(ValueError, match="Cannot save empty DataFrame"):
                cache.save_data('AAPL', empty_df)
    
    def test_missing_columns_raises_error(self):
        """DataFrame missing required columns should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ParquetCache(cache_dir=tmpdir)
            
            # Missing 'Volume' column
            df = pd.DataFrame({
                'Open': [100.0],
                'High': [105.0],
                'Low': [99.0],
                'Close': [102.0]
            }, index=pd.date_range('2023-01-01', periods=1))
            
            with pytest.raises(ValueError, match="Missing required columns"):
                cache.save_data('AAPL', df)
    
    def test_invalid_ohlc_relationships_raises_error(self):
        """Invalid OHLC relationships should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ParquetCache(cache_dir=tmpdir)
            
            # High < Low (invalid)
            df = pd.DataFrame({
                'Open': [100.0],
                'High': [99.0],  # Invalid: High < Low
                'Low': [105.0],
                'Close': [102.0],
                'Volume': [1000000]
            }, index=pd.date_range('2023-01-01', periods=1))
            
            with pytest.raises(ValueError, match="Invalid OHLC relationships"):
                cache.save_data('AAPL', df)
    
    def test_non_datetime_index_raises_error(self):
        """DataFrame without DatetimeIndex should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ParquetCache(cache_dir=tmpdir)
            
            df = pd.DataFrame({
                'Open': [100.0],
                'High': [105.0],
                'Low': [99.0],
                'Close': [102.0],
                'Volume': [1000000]
            })  # No DatetimeIndex
            
            with pytest.raises(ValueError, match="index must be DatetimeIndex"):
                cache.save_data('AAPL', df)
    
    def test_get_data_nonexistent_symbol_returns_none(self):
        """Getting data for non-existent symbol should return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ParquetCache(cache_dir=tmpdir)
            
            result = cache.get_data(
                'NONEXISTENT',
                datetime(2023, 1, 1),
                datetime(2023, 12, 31)
            )
            
            assert result is None
    
    def test_multi_year_data_partitioning(self):
        """Data spanning multiple years should be partitioned correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ParquetCache(cache_dir=tmpdir)
            
            # Create data spanning 3 years
            dates = pd.date_range('2021-01-01', '2023-12-31', freq='D')
            df = pd.DataFrame({
                'Open': 100.0,
                'High': 105.0,
                'Low': 99.0,
                'Close': 102.0,
                'Volume': 1000000
            }, index=dates)
            
            cache.save_data('AAPL', df)
            
            # Verify files exist for each year
            symbol_dir = Path(tmpdir) / 'ohlcv' / 'AAPL'
            assert (symbol_dir / '2021.parquet').exists()
            assert (symbol_dir / '2022.parquet').exists()
            assert (symbol_dir / '2023.parquet').exists()
            
            # Verify we can load the full range
            loaded = cache.get_data('AAPL', dates.min(), dates.max())
            assert loaded is not None
            assert len(loaded) == len(df)
