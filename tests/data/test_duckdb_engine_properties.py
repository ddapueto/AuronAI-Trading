"""
Property-based tests for DuckDBQueryEngine.

Tests universal properties that should hold for all valid inputs.
"""

import tempfile
import time
from datetime import datetime

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auronai.data.parquet_cache import ParquetCache
from auronai.data.duckdb_engine import DuckDBQueryEngine


# Property Tests

class TestDuckDBQueryEngineProperties:
    """Property-based tests for DuckDBQueryEngine."""
    
    @given(
        num_rows=st.integers(min_value=30, max_value=50)
    )
    @settings(max_examples=20, deadline=None)
    def test_property_11_cache_hit_performance(self, num_rows):
        """
        Property 11: Cache Hit Performance
        
        For any cached data request, retrieval time should be < 100ms.
        
        **Feature: swing-strategy-lab, Property 11: Cache performance**
        **Validates: Requirements NFR Performance**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create simple test data
            dates = pd.date_range('2023-01-01', periods=num_rows, freq='D')
            data = pd.DataFrame({
                'Open': 100.0,
                'High': 105.0,
                'Low': 95.0,
                'Close': 100.0,
                'Volume': 1000000
            }, index=dates)
            
            cache = ParquetCache(cache_dir=tmpdir)
            cache.save_data('TEST', data)
            
            engine = DuckDBQueryEngine(cache_dir=tmpdir)
            
            # Warm up
            engine.query_ohlcv(
                symbols=['TEST'],
                start_date=dates.min(),
                end_date=dates.max()
            )
            
            # Measure second query
            start_time = time.time()
            result = engine.query_ohlcv(
                symbols=['TEST'],
                start_date=dates.min(),
                end_date=dates.max()
            )
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Should be fast (< 100ms)
            assert elapsed_ms < 100, \
                f"Query took {elapsed_ms:.2f}ms, expected < 100ms"
            
            assert not result.empty
            engine.close()


# Unit tests for edge cases

class TestDuckDBQueryEngineEdgeCases:
    """Unit tests for specific edge cases."""
    
    def test_empty_symbols_list_returns_empty_dataframe(self):
        """Empty symbols list should return empty DataFrame."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DuckDBQueryEngine(cache_dir=tmpdir)
            result = engine.query_ohlcv(
                symbols=[],
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31)
            )
            assert result.empty
            engine.close()
    
    def test_query_and_stats_work(self):
        """Basic query and stats should work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create simple test data
            dates = pd.date_range('2023-01-01', periods=10, freq='D')
            data = pd.DataFrame({
                'Open': 100.0,
                'High': 105.0,
                'Low': 95.0,
                'Close': 100.0,
                'Volume': 1000000
            }, index=dates)
            
            cache = ParquetCache(cache_dir=tmpdir)
            cache.save_data('AAPL', data)
            
            engine = DuckDBQueryEngine(cache_dir=tmpdir)
            
            # Test query
            result = engine.query_ohlcv(
                symbols=['AAPL'],
                start_date=dates.min(),
                end_date=dates.max()
            )
            assert len(result) == 10
            
            # Test stats
            stats = engine.get_symbol_stats(
                symbol='AAPL',
                start_date=dates.min(),
                end_date=dates.max()
            )
            assert stats is not None
            assert stats['num_records'] == 10
            
            engine.close()
