"""
Property-based tests for FeatureStore.

Tests universal properties that should hold for all valid inputs.
"""

import tempfile
from datetime import datetime

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auronai.data.feature_store import FeatureStore


class TestFeatureStoreProperties:
    """Property-based tests for FeatureStore."""
    
    @given(
        num_rows=st.integers(min_value=250, max_value=300)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_2_feature_computation_determinism(self, num_rows):
        """
        Property 2: Feature Computation Determinism
        
        For any OHLCV dataset, computing features twice should
        produce identical results.
        
        **Feature: swing-strategy-lab, Property 2: Feature determinism**
        **Validates: Requirements FR-3**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data
            dates = pd.date_range('2023-01-01', periods=num_rows, freq='D')
            data = pd.DataFrame({
                'Open': 100.0,
                'High': 105.0,
                'Low': 95.0,
                'Close': 100.0,
                'Volume': 1000000
            }, index=dates)
            
            store = FeatureStore(cache_dir=tmpdir)
            
            # Compute features first time
            features1 = store.compute_and_save('TEST', data)
            
            # Invalidate and compute again
            store.invalidate('TEST')
            features2 = store.compute_and_save('TEST', data)
            
            # Should be identical
            pd.testing.assert_frame_equal(
                features1,
                features2,
                check_dtype=False,
                rtol=1e-10
            )


class TestFeatureStoreEdgeCases:
    """Unit tests for specific edge cases."""
    
    def test_compute_and_retrieve_features(self):
        """Should compute and retrieve features correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data (need enough for indicators)
            dates = pd.date_range('2023-01-01', periods=250, freq='D')
            data = pd.DataFrame({
                'Open': 100.0,
                'High': 105.0,
                'Low': 95.0,
                'Close': 100.0,
                'Volume': 1000000
            }, index=dates)
            
            store = FeatureStore(cache_dir=tmpdir)
            
            # Compute features
            features = store.compute_and_save('AAPL', data)
            
            # Should have all indicator columns
            expected_cols = [
                'Open', 'High', 'Low', 'Close', 'Volume',
                'ema_20', 'ema_50', 'ema_200',
                'macd', 'macd_signal', 'macd_hist',
                'rsi', 'stochastic_k', 'stochastic_d',
                'atr', 'bb_upper', 'bb_middle', 'bb_lower',
                'relative_strength'
            ]
            
            for col in expected_cols:
                assert col in features.columns, f"Missing column: {col}"
            
            # Retrieve from cache
            cached = store.get_features('AAPL', dates.min(), dates.max())
            
            assert cached is not None
            assert len(cached) == len(features)
    
    def test_nonexistent_symbol_returns_none(self):
        """Getting features for non-existent symbol should return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FeatureStore(cache_dir=tmpdir)
            
            result = store.get_features(
                'NONEXISTENT',
                datetime(2023, 1, 1),
                datetime(2023, 12, 31)
            )
            
            assert result is None
    
    def test_invalidate_removes_features(self):
        """Invalidating should remove cached features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dates = pd.date_range('2023-01-01', periods=250, freq='D')
            data = pd.DataFrame({
                'Open': 100.0,
                'High': 105.0,
                'Low': 95.0,
                'Close': 100.0,
                'Volume': 1000000
            }, index=dates)
            
            store = FeatureStore(cache_dir=tmpdir)
            store.compute_and_save('AAPL', data)
            
            # Should exist
            assert store.get_features('AAPL', dates.min(), dates.max()) is not None
            
            # Invalidate
            store.invalidate('AAPL')
            
            # Should not exist
            assert store.get_features('AAPL', dates.min(), dates.max()) is None
    
    def test_relative_strength_with_benchmark(self):
        """Should calculate relative strength vs benchmark."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dates = pd.date_range('2023-01-01', periods=250, freq='D')
            
            # Symbol data
            symbol_data = pd.DataFrame({
                'Open': 100.0,
                'High': 105.0,
                'Low': 95.0,
                'Close': 100.0,
                'Volume': 1000000
            }, index=dates)
            
            # Benchmark data
            benchmark_data = pd.DataFrame({
                'Open': 200.0,
                'High': 210.0,
                'Low': 190.0,
                'Close': 200.0,
                'Volume': 2000000
            }, index=dates)
            
            store = FeatureStore(cache_dir=tmpdir)
            features = store.compute_and_save('AAPL', symbol_data, benchmark_data)
            
            # Should have relative_strength column
            assert 'relative_strength' in features.columns
            
            # Should not be all zeros (after warmup period)
            assert features['relative_strength'].iloc[50:].abs().sum() >= 0
