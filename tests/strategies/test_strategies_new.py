"""
Tests for the 8 new trading strategies (Issue #21).

Each strategy has 4 tests:
- Instantiation: name, description, params
- Signals in correct regime
- No signals in wrong regime
- Risk model respects budget
"""

from datetime import datetime

import pandas as pd
import pytest

from auronai.strategies import (
    MarketRegime,
    StrategyParams,
    TurtleTradingStrategy,
    GoldenCrossStrategy,
    RSIDivergenceStrategy,
    BollingerMeanReversionStrategy,
    PairsTradingStrategy,
    SectorRotationStrategy,
    MACDHistogramReversalStrategy,
    WilliamsRStrategy,
)

DATE = datetime(2024, 6, 15)


@pytest.fixture
def sample_features():
    """Superset feature DataFrame covering all strategy requirements."""
    return pd.DataFrame(
        {
            "Close": [150.0, 200.0, 120.0, 180.0, 160.0],
            "High": [155.0, 205.0, 125.0, 185.0, 165.0],
            "Low": [145.0, 195.0, 115.0, 175.0, 155.0],
            "Volume": [1e6, 2e6, 5e5, 1.5e6, 8e5],
            "ema_20": [148.0, 198.0, 118.0, 178.0, 158.0],
            "ema_50": [140.0, 190.0, 110.0, 170.0, 150.0],
            "ema_200": [130.0, 180.0, 100.0, 160.0, 140.0],
            "rsi": [55.0, 60.0, 25.0, 28.0, 45.0],
            "atr": [3.0, 4.0, 2.5, 3.5, 3.0],
            "relative_strength": [0.08, 0.05, 0.10, 0.02, 0.06],
            "macd_histogram": [0.5, 0.3, 0.8, -0.2, 0.1],
            # Turtle-specific
            "high_20": [148.0, 198.0, 118.0, 178.0, 158.0],
            "low_10": [142.0, 192.0, 112.0, 172.0, 152.0],
            # Bollinger-specific
            "bb_lower": [155.0, 205.0, 125.0, 185.0, 165.0],
            "bb_middle": [160.0, 210.0, 130.0, 190.0, 170.0],
            "bb_upper": [165.0, 215.0, 135.0, 195.0, 175.0],
            # Williams-specific
            "williams_r": [-85.0, -50.0, -90.0, -92.0, -30.0],
        },
        index=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
    )


# ─── Turtle Trading ─────────────────────────────────────────────


class TestTurtleTrading:
    def test_instantiation(self):
        params = StrategyParams(top_k=3, holding_days=20)
        s = TurtleTradingStrategy(params)
        assert s.name == "Turtle Trading"
        assert "breakout" in s.description.lower()
        assert s.params.top_k == 3
        assert s.params.holding_days == 20

    def test_generates_signals_in_bull(self, sample_features):
        params = StrategyParams(top_k=2)
        s = TurtleTradingStrategy(params)
        signals = s.generate_signals(sample_features, MarketRegime.BULL, DATE)
        assert len(signals) > 0
        assert all(w > 0 for w in signals.values())

    def test_no_signals_in_bear(self, sample_features):
        params = StrategyParams(top_k=2)
        s = TurtleTradingStrategy(params)
        signals = s.generate_signals(sample_features, MarketRegime.BEAR, DATE)
        assert len(signals) == 0

    def test_risk_model_respects_budget(self, sample_features):
        params = StrategyParams(risk_budget=0.10, top_k=2)
        s = TurtleTradingStrategy(params)
        weights = {"AAPL": 0.5, "MSFT": 0.5}
        adjusted = s.risk_model(weights, sample_features, {})
        total = sum(abs(w) for w in adjusted.values())
        assert total <= params.risk_budget + 0.01


# ─── Golden Cross ────────────────────────────────────────────────


class TestGoldenCross:
    def test_instantiation(self):
        params = StrategyParams()
        s = GoldenCrossStrategy(params)
        assert s.name == "Golden Cross"
        assert "ema" in s.description.lower() or "crossover" in s.description.lower()
        assert s.params.top_k == 3

    def test_generates_signals_in_bull(self, sample_features):
        params = StrategyParams(top_k=2)
        s = GoldenCrossStrategy(params)
        signals = s.generate_signals(sample_features, MarketRegime.BULL, DATE)
        # Features have ema_50 > ema_200 and rsi > 50 for some symbols
        assert len(signals) > 0
        assert all(w > 0 for w in signals.values())

    def test_no_signals_in_bear(self, sample_features):
        params = StrategyParams(top_k=2)
        s = GoldenCrossStrategy(params)
        signals = s.generate_signals(sample_features, MarketRegime.BEAR, DATE)
        assert len(signals) == 0

    def test_risk_model_respects_budget(self, sample_features):
        params = StrategyParams(risk_budget=0.10, top_k=2)
        s = GoldenCrossStrategy(params)
        weights = {"AAPL": 0.5, "MSFT": 0.5}
        adjusted = s.risk_model(weights, sample_features, {})
        total = sum(abs(w) for w in adjusted.values())
        assert total <= params.risk_budget + 0.01


# ─── RSI Divergence ──────────────────────────────────────────────


class TestRSIDivergence:
    def test_instantiation(self):
        params = StrategyParams()
        s = RSIDivergenceStrategy(params)
        assert s.name == "RSI Divergence"
        assert "divergence" in s.description.lower()

    def test_generates_signals_in_bull(self, sample_features):
        params = StrategyParams(top_k=3)
        s = RSIDivergenceStrategy(params)
        # GOOGL rsi=25 < 35, macd_histogram=0.8 > 0
        # TSLA  rsi=28 < 35, macd_histogram=-0.2 (no — negative)
        signals = s.generate_signals(sample_features, MarketRegime.BULL, DATE)
        assert len(signals) > 0
        assert "GOOGL" in signals

    def test_no_signals_in_bear(self, sample_features):
        params = StrategyParams(top_k=2)
        s = RSIDivergenceStrategy(params)
        signals = s.generate_signals(sample_features, MarketRegime.BEAR, DATE)
        assert len(signals) == 0

    def test_risk_model_respects_budget(self, sample_features):
        params = StrategyParams(risk_budget=0.10, top_k=2)
        s = RSIDivergenceStrategy(params)
        weights = {"GOOGL": 0.5, "TSLA": 0.5}
        adjusted = s.risk_model(weights, sample_features, {})
        total = sum(abs(w) for w in adjusted.values())
        assert total <= params.risk_budget + 0.01


# ─── Bollinger Mean Reversion ────────────────────────────────────


class TestBollingerMeanReversion:
    def test_instantiation(self):
        params = StrategyParams()
        s = BollingerMeanReversionStrategy(params)
        assert s.name == "Bollinger Mean Reversion"
        assert "bollinger" in s.description.lower()

    def test_generates_signals_in_correct_regime(self, sample_features):
        # Adjust data: Close <= bb_lower, rsi < 30, Close > ema_200
        features = sample_features.copy()
        features.loc["GOOGL", "Close"] = 124.0  # <= bb_lower=125
        features.loc["GOOGL", "rsi"] = 22.0
        features.loc["GOOGL", "ema_200"] = 100.0
        features.loc["TSLA", "Close"] = 184.0  # <= bb_lower=185
        features.loc["TSLA", "rsi"] = 28.0
        features.loc["TSLA", "ema_200"] = 160.0

        params = StrategyParams(top_k=3)
        s = BollingerMeanReversionStrategy(params)
        signals = s.generate_signals(features, MarketRegime.BULL, DATE)
        assert len(signals) > 0

    def test_no_signals_in_bear(self, sample_features):
        params = StrategyParams(top_k=2)
        s = BollingerMeanReversionStrategy(params)
        signals = s.generate_signals(
            sample_features, MarketRegime.BEAR, DATE
        )
        assert len(signals) == 0

    def test_risk_model_respects_budget(self, sample_features):
        params = StrategyParams(risk_budget=0.10, top_k=2)
        s = BollingerMeanReversionStrategy(params)
        weights = {"GOOGL": 0.5, "TSLA": 0.5}
        adjusted = s.risk_model(weights, sample_features, {})
        total = sum(abs(w) for w in adjusted.values())
        assert total <= params.risk_budget + 0.01


# ─── Pairs Trading ───────────────────────────────────────────────


class TestPairsTrading:
    def test_instantiation(self):
        params = StrategyParams()
        s = PairsTradingStrategy(params)
        assert s.name == "Pairs Trading"
        assert "neutral" in s.description.lower()

    def test_generates_signals_in_any_regime(self, sample_features):
        params = StrategyParams(top_k=2)
        s = PairsTradingStrategy(params)
        for regime in MarketRegime:
            signals = s.generate_signals(sample_features, regime, DATE)
            assert len(signals) > 0
            # Should have both long and short
            has_long = any(w > 0 for w in signals.values())
            has_short = any(w < 0 for w in signals.values())
            assert has_long and has_short

    def test_signals_are_balanced(self, sample_features):
        """Long and short exposure should be roughly balanced."""
        params = StrategyParams(top_k=2)
        s = PairsTradingStrategy(params)
        signals = s.generate_signals(
            sample_features, MarketRegime.NEUTRAL, DATE
        )
        long_sum = sum(w for w in signals.values() if w > 0)
        short_sum = sum(abs(w) for w in signals.values() if w < 0)
        assert abs(long_sum - short_sum) < 0.01

    def test_risk_model_respects_budget(self, sample_features):
        params = StrategyParams(risk_budget=0.10, top_k=2)
        s = PairsTradingStrategy(params)
        weights = {"AAPL": 0.3, "MSFT": -0.3, "GOOGL": 0.3, "TSLA": -0.3}
        adjusted = s.risk_model(weights, sample_features, {})
        total = sum(abs(w) for w in adjusted.values())
        assert total <= params.risk_budget + 0.01


# ─── Sector Rotation ────────────────────────────────────────────


class TestSectorRotation:
    def test_instantiation(self):
        params = StrategyParams()
        s = SectorRotationStrategy(params)
        assert s.name == "Sector Rotation"
        assert "rotation" in s.description.lower()

    def test_generates_signals_in_bull(self, sample_features):
        params = StrategyParams(top_k=2)
        s = SectorRotationStrategy(params)
        signals = s.generate_signals(sample_features, MarketRegime.BULL, DATE)
        assert len(signals) > 0
        assert all(w > 0 for w in signals.values())

    def test_no_signals_in_bear(self, sample_features):
        params = StrategyParams(top_k=2)
        s = SectorRotationStrategy(params)
        signals = s.generate_signals(sample_features, MarketRegime.BEAR, DATE)
        assert len(signals) == 0

    def test_risk_model_respects_budget(self, sample_features):
        params = StrategyParams(risk_budget=0.10, top_k=2)
        s = SectorRotationStrategy(params)
        weights = {"AAPL": 0.5, "MSFT": 0.5}
        adjusted = s.risk_model(weights, sample_features, {})
        total = sum(abs(w) for w in adjusted.values())
        assert total <= params.risk_budget + 0.01


# ─── MACD Histogram Reversal ────────────────────────────────────


class TestMACDHistogramReversal:
    def test_instantiation(self):
        params = StrategyParams()
        s = MACDHistogramReversalStrategy(params)
        assert s.name == "MACD Histogram Reversal"
        assert "macd" in s.description.lower()

    def test_generates_signals_in_bull(self, sample_features):
        params = StrategyParams(top_k=3)
        s = MACDHistogramReversalStrategy(params)
        signals = s.generate_signals(sample_features, MarketRegime.BULL, DATE)
        # AAPL, MSFT, GOOGL, NVDA all have macd_histogram > 0, ema_20 > ema_50
        assert len(signals) > 0
        assert all(w > 0 for w in signals.values())

    def test_no_signals_in_bear(self, sample_features):
        params = StrategyParams(top_k=2)
        s = MACDHistogramReversalStrategy(params)
        signals = s.generate_signals(sample_features, MarketRegime.BEAR, DATE)
        assert len(signals) == 0

    def test_risk_model_respects_budget(self, sample_features):
        params = StrategyParams(risk_budget=0.10, top_k=2)
        s = MACDHistogramReversalStrategy(params)
        weights = {"AAPL": 0.5, "MSFT": 0.5}
        adjusted = s.risk_model(weights, sample_features, {})
        total = sum(abs(w) for w in adjusted.values())
        assert total <= params.risk_budget + 0.01


# ─── Williams %R ─────────────────────────────────────────────────


class TestWilliamsR:
    def test_instantiation(self):
        params = StrategyParams()
        s = WilliamsRStrategy(params)
        assert s.name == "Williams %R"
        assert "williams" in s.description.lower()

    def test_generates_signals_in_bull(self, sample_features):
        params = StrategyParams(top_k=3)
        s = WilliamsRStrategy(params)
        signals = s.generate_signals(sample_features, MarketRegime.BULL, DATE)
        # AAPL williams_r=-85 < -80 AND Close=150 > ema_50=140 → signal
        # GOOGL williams_r=-90 < -80 AND Close=120 > ema_50=110 → signal
        # TSLA williams_r=-92 < -80 AND Close=180 > ema_50=170 → signal
        assert len(signals) > 0
        assert all(w > 0 for w in signals.values())

    def test_no_signals_in_bear(self, sample_features):
        params = StrategyParams(top_k=2)
        s = WilliamsRStrategy(params)
        signals = s.generate_signals(sample_features, MarketRegime.BEAR, DATE)
        assert len(signals) == 0

    def test_risk_model_respects_budget(self, sample_features):
        params = StrategyParams(risk_budget=0.10, top_k=2)
        s = WilliamsRStrategy(params)
        weights = {"AAPL": 0.5, "GOOGL": 0.5}
        adjusted = s.risk_model(weights, sample_features, {})
        total = sum(abs(w) for w in adjusted.values())
        assert total <= params.risk_budget + 0.01
