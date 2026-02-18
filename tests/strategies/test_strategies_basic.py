"""
Basic tests for strategy implementations.

Tests that strategies can be instantiated and generate signals correctly.
"""

from datetime import datetime

import pandas as pd
import pytest

from auronai.strategies import (
    MarketRegime,
    StrategyParams,
    LongMomentumStrategy,
    ShortMomentumStrategy,
    NeutralStrategy,
    RegimeEngine
)


class TestStrategyInstantiation:
    """Test that strategies can be instantiated."""
    
    def test_long_momentum_strategy_instantiation(self):
        """Should create LongMomentumStrategy instance."""
        params = StrategyParams()
        strategy = LongMomentumStrategy(params)
        
        assert strategy.name == "Long Momentum"
        assert "bull" in strategy.description.lower()
        assert strategy.params.top_k == 3
    
    def test_short_momentum_strategy_instantiation(self):
        """Should create ShortMomentumStrategy instance."""
        params = StrategyParams()
        strategy = ShortMomentumStrategy(params)
        
        assert strategy.name == "Short Momentum"
        assert "bear" in strategy.description.lower()
        assert strategy.params.top_k == 3
    
    def test_neutral_strategy_instantiation(self):
        """Should create NeutralStrategy instance."""
        params = StrategyParams()
        strategy = NeutralStrategy(params)
        
        assert strategy.name == "Neutral/Defensive"
        assert "defensive" in strategy.description.lower()
        assert strategy.params.defensive_risk_budget == 0.05


class TestStrategySignalGeneration:
    """Test signal generation for different regimes."""
    
    @pytest.fixture
    def sample_features(self):
        """Create sample feature data."""
        dates = pd.date_range('2023-01-01', periods=5, freq='D')
        data = pd.DataFrame({
            'ema_20': [100.0, 101.0, 102.0, 103.0, 104.0],
            'ema_50': [95.0, 96.0, 97.0, 98.0, 99.0],
            'rsi': [60.0, 65.0, 55.0, 50.0, 45.0],
            'atr': [2.0, 2.5, 1.5, 1.8, 2.2],
            'relative_strength': [0.05, 0.03, 0.08, 0.02, 0.06]
        }, index=['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'])
        return data
    
    def test_long_momentum_generates_signals_in_bull_regime(self, sample_features):
        """Should generate signals in BULL regime."""
        params = StrategyParams(top_k=2)
        strategy = LongMomentumStrategy(params)
        
        signals = strategy.generate_signals(
            sample_features,
            MarketRegime.BULL,
            datetime(2023, 1, 1)
        )
        
        assert len(signals) == 2
        assert all(w > 0 for w in signals.values())
        assert abs(sum(signals.values()) - 1.0) < 0.01
    
    def test_long_momentum_no_signals_in_bear_regime(self, sample_features):
        """Should not generate signals in BEAR regime."""
        params = StrategyParams()
        strategy = LongMomentumStrategy(params)
        
        signals = strategy.generate_signals(
            sample_features,
            MarketRegime.BEAR,
            datetime(2023, 1, 1)
        )
        
        assert len(signals) == 0
    
    def test_short_momentum_generates_signals_in_bear_regime(self, sample_features):
        """Should generate short signals in BEAR regime."""
        # Modify features for bearish conditions
        sample_features['ema_20'] = [90.0, 89.0, 88.0, 87.0, 86.0]
        sample_features['ema_50'] = [95.0, 96.0, 97.0, 98.0, 99.0]
        sample_features['rsi'] = [40.0, 35.0, 45.0, 50.0, 55.0]
        
        params = StrategyParams(top_k=2)
        strategy = ShortMomentumStrategy(params)
        
        signals = strategy.generate_signals(
            sample_features,
            MarketRegime.BEAR,
            datetime(2023, 1, 1)
        )
        
        assert len(signals) == 2
        assert all(w < 0 for w in signals.values())
        assert abs(sum(signals.values()) + 1.0) < 0.01
    
    def test_neutral_strategy_generates_signals_in_neutral_regime(self, sample_features):
        """Should generate defensive signals in NEUTRAL regime."""
        params = StrategyParams(top_k=2)
        strategy = NeutralStrategy(params)
        
        signals = strategy.generate_signals(
            sample_features,
            MarketRegime.NEUTRAL,
            datetime(2023, 1, 1)
        )
        
        assert len(signals) == 2
        assert all(w > 0 for w in signals.values())


class TestRiskModel:
    """Test risk management constraints."""
    
    def test_long_momentum_respects_risk_budget(self):
        """Should scale weights to respect risk budget."""
        params = StrategyParams(risk_budget=0.10, top_k=2)
        strategy = LongMomentumStrategy(params)
        
        # Target weights that exceed risk budget
        target_weights = {'AAPL': 0.60, 'MSFT': 0.60}
        
        features = pd.DataFrame()
        current_portfolio = {}
        
        adjusted = strategy.risk_model(target_weights, features, current_portfolio)
        
        total_weight = sum(abs(w) for w in adjusted.values())
        assert total_weight <= params.risk_budget + 0.01
    
    def test_neutral_strategy_uses_defensive_risk_budget(self):
        """Should use defensive risk budget for neutral regime."""
        params = StrategyParams(defensive_risk_budget=0.05, top_k=2)
        strategy = NeutralStrategy(params)
        
        # Target weights
        target_weights = {'AAPL': 0.50, 'MSFT': 0.50}
        
        features = pd.DataFrame()
        current_portfolio = {}
        
        adjusted = strategy.risk_model(target_weights, features, current_portfolio)
        
        total_weight = sum(abs(w) for w in adjusted.values())
        assert total_weight <= params.defensive_risk_budget + 0.01


class TestRegimeEngine:
    """Test regime detection."""
    
    def test_regime_engine_instantiation(self):
        """Should create RegimeEngine instance."""
        engine = RegimeEngine(benchmark='QQQ')
        
        assert engine.benchmark == 'QQQ'
        assert engine.ema_period == 200
        assert engine.slope_lookback == 20
    
    def test_detect_bull_regime(self):
        """Should detect BULL regime."""
        engine = RegimeEngine(ema_period=10, slope_lookback=5)
        
        # Create data with bullish conditions
        dates = pd.date_range('2023-01-01', periods=30, freq='D')
        data = pd.DataFrame({
            'Close': range(100, 130),
            'ema_200': range(90, 120)
        }, index=dates)
        
        regime = engine.detect_regime(data, 25)
        
        assert regime == MarketRegime.BULL
    
    def test_detect_bear_regime(self):
        """Should detect BEAR regime."""
        engine = RegimeEngine(ema_period=10, slope_lookback=5)
        
        # Create data with bearish conditions
        dates = pd.date_range('2023-01-01', periods=30, freq='D')
        data = pd.DataFrame({
            'Close': range(130, 100, -1),
            'ema_200': range(140, 110, -1)
        }, index=dates)
        
        regime = engine.detect_regime(data, 25)
        
        assert regime == MarketRegime.BEAR
    
    def test_insufficient_data_returns_neutral(self):
        """Should return NEUTRAL when insufficient data."""
        engine = RegimeEngine(ema_period=200)
        
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        data = pd.DataFrame({
            'Close': range(100, 150),
            'ema_200': range(90, 140)
        }, index=dates)
        
        regime = engine.detect_regime(data, 10)
        
        assert regime == MarketRegime.NEUTRAL
