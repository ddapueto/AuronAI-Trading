"""
Unit tests for Dual Momentum Strategy.
"""

import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from auronai.strategies.dual_momentum import (
    DualMomentumStrategy,
    DualMomentumParams
)
from auronai.strategies.base_strategy import MarketRegime


class TestDualMomentumParams:
    """Test suite for DualMomentumParams."""
    
    def test_default_params(self):
        """Test default parameter values."""
        params = DualMomentumParams()
        
        assert params.lookback_period == 252
        assert params.top_n == 5
        assert params.rebalance_frequency == 'monthly'
    
    def test_custom_params(self):
        """Test custom parameter values."""
        params = DualMomentumParams(
            lookback_period=180,
            top_n=3,
            rebalance_frequency='weekly'
        )
        
        assert params.lookback_period == 180
        assert params.top_n == 3
        assert params.rebalance_frequency == 'weekly'
    
    def test_invalid_lookback_period_raises_error(self):
        """Test that invalid lookback_period raises ValueError."""
        with pytest.raises(ValueError, match="lookback_period must be >= 1"):
            DualMomentumParams(lookback_period=0)
    
    def test_invalid_top_n_raises_error(self):
        """Test that invalid top_n raises ValueError."""
        with pytest.raises(ValueError, match="top_n must be >= 1"):
            DualMomentumParams(top_n=0)
    
    def test_invalid_rebalance_frequency_raises_error(self):
        """Test that invalid rebalance_frequency raises ValueError."""
        with pytest.raises(ValueError, match="rebalance_frequency must be"):
            DualMomentumParams(rebalance_frequency='daily')


class TestDualMomentumStrategy:
    """Test suite for DualMomentumStrategy."""
    
    @pytest.fixture
    def strategy(self):
        """Create strategy instance with default params."""
        return DualMomentumStrategy()
    
    @pytest.fixture
    def custom_strategy(self):
        """Create strategy instance with custom params."""
        params = DualMomentumParams(
            lookback_period=100,
            top_n=3,
            rebalance_frequency='monthly'
        )
        return DualMomentumStrategy(params)
    
    def test_init_with_default_params(self, strategy):
        """Test initialization with default parameters."""
        assert strategy.params.lookback_period == 252
        assert strategy.params.top_n == 5
        assert strategy.last_rebalance is None
        assert strategy.current_positions == []
    
    def test_init_with_custom_params(self, custom_strategy):
        """Test initialization with custom parameters."""
        assert custom_strategy.params.lookback_period == 100
        assert custom_strategy.params.top_n == 3
    
    def test_name_property(self, strategy):
        """Test strategy name."""
        assert strategy.name == "Dual Momentum"
    
    def test_description_property(self, strategy):
        """Test strategy description."""
        assert "Dual Momentum" in strategy.description
        assert "Antonacci" in strategy.description
    
    def test_get_params(self, strategy):
        """Test get_params returns correct dictionary."""
        params = strategy.get_params()
        
        assert params['lookback_period'] == 252
        assert params['top_n'] == 5
        assert params['rebalance_frequency'] == 'monthly'
        assert 'risk_budget' in params
    
    def test_should_rebalance_first_time(self, strategy):
        """Test that first rebalance returns True."""
        current_date = datetime(2024, 1, 15)
        assert strategy._should_rebalance(current_date) is True
    
    def test_should_rebalance_monthly_same_month(self, strategy):
        """Test that rebalancing doesn't occur in same month."""
        strategy.last_rebalance = datetime(2024, 1, 1)
        current_date = datetime(2024, 1, 15)
        
        assert strategy._should_rebalance(current_date) is False
    
    def test_should_rebalance_monthly_different_month(self, strategy):
        """Test that rebalancing occurs when month changes."""
        strategy.last_rebalance = datetime(2024, 1, 15)
        current_date = datetime(2024, 2, 1)
        
        assert strategy._should_rebalance(current_date) is True
    
    def test_should_rebalance_weekly(self):
        """Test weekly rebalancing logic."""
        params = DualMomentumParams(rebalance_frequency='weekly')
        strategy = DualMomentumStrategy(params)
        
        strategy.last_rebalance = datetime(2024, 1, 1)
        
        # Same week - no rebalance
        current_date = datetime(2024, 1, 3)
        assert strategy._should_rebalance(current_date) is False
        
        # Next week - rebalance
        current_date = datetime(2024, 1, 10)
        assert strategy._should_rebalance(current_date) is True
    
    def test_calculate_momentum_with_known_data(self, custom_strategy):
        """Test momentum calculation with known data."""
        # Create test data with known momentum
        dates = pd.date_range('2024-01-01', periods=150, freq='D')
        
        # Symbol A: 20% gain over 100 days
        data_a = pd.DataFrame({
            'symbol': 'A',
            'close': np.linspace(100, 120, 150)
        }, index=dates)
        
        # Symbol B: 10% loss over 100 days
        data_b = pd.DataFrame({
            'symbol': 'B',
            'close': np.linspace(100, 90, 150)
        }, index=dates)
        
        features = pd.concat([data_a, data_b])
        current_date = dates[-1]
        
        momentum = custom_strategy._calculate_momentum(features, current_date)
        
        # Check momentum values
        assert 'A' in momentum
        assert 'B' in momentum
        assert momentum['A'] > 0  # Positive momentum
        assert momentum['B'] < 0  # Negative momentum
        assert momentum['A'] > momentum['B']  # A has higher momentum
    
    def test_calculate_momentum_handles_insufficient_data(self, custom_strategy):
        """Test that insufficient data is handled gracefully."""
        # Create data with fewer rows than lookback period
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        
        features = pd.DataFrame({
            'symbol': 'A',
            'close': [100.0] * 50
        }, index=dates)
        
        current_date = dates[-1]
        
        momentum = custom_strategy._calculate_momentum(features, current_date)
        
        # Should return empty dict (not enough data)
        assert len(momentum) == 0
    
    def test_calculate_momentum_handles_missing_dates(self, custom_strategy):
        """Test that missing dates are handled with nearest date."""
        dates = pd.date_range('2024-01-01', periods=150, freq='D')
        
        features = pd.DataFrame({
            'symbol': 'A',
            'close': np.linspace(100, 120, 150)
        }, index=dates)
        
        # Use a date not in the index
        current_date = datetime(2024, 5, 29, 12, 0, 0)  # With time component
        
        momentum = custom_strategy._calculate_momentum(features, current_date)
        
        # Should still calculate momentum using nearest date
        assert 'A' in momentum
        assert momentum['A'] > 0
    
    def test_calculate_momentum_handles_invalid_prices(self, custom_strategy):
        """Test that invalid prices (NaN, 0) are handled."""
        dates = pd.date_range('2024-01-01', periods=150, freq='D')
        
        # Create data with NaN and zero values
        close_prices = np.linspace(100, 120, 150)
        close_prices[0] = np.nan  # NaN at start
        close_prices[50] = 0  # Zero in middle
        
        features = pd.DataFrame({
            'symbol': 'A',
            'close': close_prices
        }, index=dates)
        
        current_date = dates[-1]
        
        momentum = custom_strategy._calculate_momentum(features, current_date)
        
        # Should handle gracefully (may return empty or skip)
        # The important thing is it doesn't crash
        assert isinstance(momentum, dict)
    
    def test_generate_signals_no_rebalance_needed(self, strategy):
        """Test that no signals are generated when rebalancing not needed."""
        # Set last rebalance to current month
        strategy.last_rebalance = datetime(2024, 1, 1)
        
        dates = pd.date_range('2024-01-01', periods=300, freq='D')
        features = pd.DataFrame({
            'symbol': 'A',
            'close': [100.0] * 300
        }, index=dates)
        
        current_date = datetime(2024, 1, 15)  # Same month
        
        signals = strategy.generate_signals(
            features,
            MarketRegime.BULL,
            current_date
        )
        
        assert signals == {}
    
    def test_generate_signals_with_positive_momentum(self, custom_strategy):
        """Test signal generation with positive momentum assets."""
        dates = pd.date_range('2024-01-01', periods=150, freq='D')
        
        # Create 5 symbols with different momentum
        symbols_data = []
        for i, symbol in enumerate(['A', 'B', 'C', 'D', 'E']):
            momentum_pct = 0.1 + (i * 0.05)  # 10%, 15%, 20%, 25%, 30%
            close_prices = np.linspace(100, 100 * (1 + momentum_pct), 150)
            
            df = pd.DataFrame({
                'symbol': symbol,
                'close': close_prices
            }, index=dates)
            symbols_data.append(df)
        
        features = pd.concat(symbols_data)
        current_date = dates[-1]
        
        signals = custom_strategy.generate_signals(
            features,
            MarketRegime.BULL,
            current_date
        )
        
        # Should select top 3 (custom_strategy has top_n=3)
        assert len(signals) == 3
        
        # Should be equal weighted
        for weight in signals.values():
            assert abs(weight - 1/3) < 0.01
        
        # Should select highest momentum symbols (E, D, C)
        assert 'E' in signals
        assert 'D' in signals
        assert 'C' in signals
    
    def test_generate_signals_with_negative_momentum(self, strategy):
        """Test that no signals are generated when all momentum is negative."""
        dates = pd.date_range('2024-01-01', periods=300, freq='D')
        
        # Create symbols with negative momentum
        symbols_data = []
        for symbol in ['A', 'B', 'C']:
            close_prices = np.linspace(100, 80, 300)  # -20% momentum
            
            df = pd.DataFrame({
                'symbol': symbol,
                'close': close_prices
            }, index=dates)
            symbols_data.append(df)
        
        features = pd.concat(symbols_data)
        current_date = dates[-1]
        
        signals = strategy.generate_signals(
            features,
            MarketRegime.BULL,
            current_date
        )
        
        # Should return empty (no positive momentum)
        assert signals == {}
        assert strategy.current_positions == []
    
    def test_generate_signals_with_mixed_momentum(self, strategy):
        """Test signal generation with mixed positive/negative momentum."""
        dates = pd.date_range('2024-01-01', periods=300, freq='D')
        
        # Create symbols with mixed momentum
        symbols_data = []
        momentums = [0.20, 0.10, -0.05, -0.10, 0.15]  # 3 positive, 2 negative
        
        for i, symbol in enumerate(['A', 'B', 'C', 'D', 'E']):
            close_prices = np.linspace(100, 100 * (1 + momentums[i]), 300)
            
            df = pd.DataFrame({
                'symbol': symbol,
                'close': close_prices
            }, index=dates)
            symbols_data.append(df)
        
        features = pd.concat(symbols_data)
        current_date = dates[-1]
        
        signals = strategy.generate_signals(
            features,
            MarketRegime.BULL,
            current_date
        )
        
        # Should only select positive momentum symbols (A, B, E)
        assert len(signals) == 3
        assert 'A' in signals
        assert 'B' in signals
        assert 'E' in signals
        assert 'C' not in signals  # Negative momentum
        assert 'D' not in signals  # Negative momentum
    
    def test_generate_signals_updates_state(self, strategy):
        """Test that generate_signals updates internal state."""
        dates = pd.date_range('2024-01-01', periods=300, freq='D')
        
        features = pd.DataFrame({
            'symbol': 'A',
            'close': np.linspace(100, 120, 300)
        }, index=dates)
        
        current_date = dates[-1]
        
        signals = strategy.generate_signals(
            features,
            MarketRegime.BULL,
            current_date
        )
        
        # State should be updated
        assert strategy.last_rebalance == current_date
        assert strategy.current_positions == ['A']
    
    def test_risk_model_no_adjustment_needed(self, strategy):
        """Test risk model when no adjustment is needed."""
        target_weights = {'A': 0.10, 'B': 0.10}  # Total 20%
        features = pd.DataFrame()
        current_portfolio = {}
        
        adjusted = strategy.risk_model(target_weights, features, current_portfolio)
        
        # Should return unchanged (within risk budget)
        assert adjusted == target_weights
    
    def test_risk_model_scales_down_when_exceeds_budget(self):
        """Test risk model scales down when exceeding risk budget."""
        params = DualMomentumParams(risk_budget=0.50)  # 50% max
        strategy = DualMomentumStrategy(params)
        
        # Target weights exceed risk budget
        target_weights = {'A': 0.30, 'B': 0.30, 'C': 0.30}  # Total 90%
        features = pd.DataFrame()
        current_portfolio = {}
        
        adjusted = strategy.risk_model(target_weights, features, current_portfolio)
        
        # Should scale down to 50%
        total_adjusted = sum(adjusted.values())
        assert abs(total_adjusted - 0.50) < 0.01
        
        # Proportions should be maintained
        for symbol in adjusted:
            assert abs(adjusted[symbol] - 0.50/3) < 0.01
    
    def test_risk_model_with_empty_weights(self, strategy):
        """Test risk model with empty target weights."""
        target_weights = {}
        features = pd.DataFrame()
        current_portfolio = {}
        
        adjusted = strategy.risk_model(target_weights, features, current_portfolio)
        
        assert adjusted == {}
