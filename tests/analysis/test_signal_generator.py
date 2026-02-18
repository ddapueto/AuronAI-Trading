"""Unit tests for SignalGenerator."""

import pytest
from src.auronai.analysis.signal_generator import SignalGenerator


class TestSignalGenerator:
    """Test suite for SignalGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create a SignalGenerator instance."""
        return SignalGenerator()
    
    # RSI Strategy Tests
    
    def test_rsi_strategy_oversold(self, generator):
        """Test RSI strategy with oversold condition."""
        indicators = {"rsi": 25.0}
        result = generator.generate_signal(indicators, strategy="rsi")
        
        assert result["action"] == "BUY"
        assert result["strategy"] == "rsi"
        assert "confidence" in result
        assert "bullish_signals" in result
        assert "bearish_signals" in result
    
    def test_rsi_strategy_overbought(self, generator):
        """Test RSI strategy with overbought condition."""
        indicators = {"rsi": 75.0}
        result = generator.generate_signal(indicators, strategy="rsi")
        
        assert result["action"] == "SELL"
        assert result["strategy"] == "rsi"
    
    def test_rsi_strategy_neutral(self, generator):
        """Test RSI strategy with neutral condition."""
        indicators = {"rsi": 50.0}
        result = generator.generate_signal(indicators, strategy="rsi")
        
        assert result["action"] == "HOLD"
    
    def test_rsi_strategy_missing_data(self, generator):
        """Test RSI strategy with missing RSI data."""
        indicators = {}
        result = generator.generate_signal(indicators, strategy="rsi")
        
        assert result["action"] == "HOLD"
    
    # MACD Strategy Tests
    
    def test_macd_strategy_bullish_crossover(self, generator):
        """Test MACD strategy with bullish crossover."""
        indicators = {
            "macd": 0.5,
            "macd_signal": 0.3,
            "macd_prev": 0.2,
            "macd_signal_prev": 0.25,
        }
        result = generator.generate_signal(indicators, strategy="macd")
        
        assert result["action"] == "BUY"
        assert result["strategy"] == "macd"
    
    def test_macd_strategy_bearish_crossover(self, generator):
        """Test MACD strategy with bearish crossover."""
        indicators = {
            "macd": 0.2,
            "macd_signal": 0.3,
            "macd_prev": 0.35,
            "macd_signal_prev": 0.3,
        }
        result = generator.generate_signal(indicators, strategy="macd")
        
        assert result["action"] == "SELL"
        assert result["strategy"] == "macd"
    
    def test_macd_strategy_above_signal(self, generator):
        """Test MACD strategy when MACD is above signal."""
        indicators = {
            "macd": 0.5,
            "macd_signal": 0.3,
            "macd_prev": 0.4,
            "macd_signal_prev": 0.2,
        }
        result = generator.generate_signal(indicators, strategy="macd")
        
        assert result["action"] == "BUY"
    
    def test_macd_strategy_missing_data(self, generator):
        """Test MACD strategy with missing data."""
        indicators = {"macd": 0.5}
        result = generator.generate_signal(indicators, strategy="macd")
        
        assert result["action"] == "HOLD"
    
    # EMA Strategy Tests
    
    def test_ema_strategy_strong_uptrend(self, generator):
        """Test EMA strategy with strong uptrend."""
        indicators = {
            "ema_20": 150.0,
            "ema_50": 145.0,
            "ema_200": 140.0,
        }
        result = generator.generate_signal(indicators, strategy="ema")
        
        assert result["action"] == "BUY"
        assert result["strategy"] == "ema"
    
    def test_ema_strategy_strong_downtrend(self, generator):
        """Test EMA strategy with strong downtrend."""
        indicators = {
            "ema_20": 140.0,
            "ema_50": 145.0,
            "ema_200": 150.0,
        }
        result = generator.generate_signal(indicators, strategy="ema")
        
        assert result["action"] == "SELL"
    
    def test_ema_strategy_simple_uptrend(self, generator):
        """Test EMA strategy with simple uptrend (no EMA200)."""
        indicators = {
            "ema_20": 150.0,
            "ema_50": 145.0,
        }
        result = generator.generate_signal(indicators, strategy="ema")
        
        assert result["action"] == "BUY"
    
    def test_ema_strategy_missing_data(self, generator):
        """Test EMA strategy with missing data."""
        indicators = {}
        result = generator.generate_signal(indicators, strategy="ema")
        
        assert result["action"] == "HOLD"
    
    # Combo Strategy Tests
    
    def test_combo_strategy_strong_bullish(self, generator):
        """Test combo strategy with strong bullish signals."""
        indicators = {
            "rsi": 25.0,  # Oversold
            "macd": 0.5,
            "macd_signal": 0.3,  # MACD above signal
            "ema_20": 150.0,
            "ema_50": 145.0,  # Uptrend
            "close": 140.0,
            "bb_lower": 145.0,  # Below lower band
            "bb_upper": 155.0,
            "stochastic_k": 15.0,  # Oversold
        }
        result = generator.generate_signal(indicators, strategy="combo")
        
        assert result["action"] == "BUY"
        assert result["strategy"] == "combo"
    
    def test_combo_strategy_strong_bearish(self, generator):
        """Test combo strategy with strong bearish signals."""
        indicators = {
            "rsi": 75.0,  # Overbought
            "macd": 0.3,
            "macd_signal": 0.5,  # MACD below signal
            "ema_20": 145.0,
            "ema_50": 150.0,  # Downtrend
            "close": 160.0,
            "bb_lower": 145.0,
            "bb_upper": 155.0,  # Above upper band
            "stochastic_k": 85.0,  # Overbought
        }
        result = generator.generate_signal(indicators, strategy="combo")
        
        assert result["action"] == "SELL"
    
    def test_combo_strategy_mixed_signals(self, generator):
        """Test combo strategy with mixed signals."""
        indicators = {
            "rsi": 50.0,  # Neutral
            "macd": 0.5,
            "macd_signal": 0.3,  # Bullish
            "ema_20": 145.0,
            "ema_50": 150.0,  # Bearish
        }
        result = generator.generate_signal(indicators, strategy="combo")
        
        assert result["action"] == "HOLD"
    
    def test_combo_strategy_insufficient_signals(self, generator):
        """Test combo strategy with insufficient aligned signals."""
        indicators = {
            "rsi": 25.0,  # Bullish
            "macd": 0.3,
            "macd_signal": 0.5,  # Bearish
        }
        result = generator.generate_signal(indicators, strategy="combo")
        
        assert result["action"] == "HOLD"
    
    # Unknown Strategy Test
    
    def test_unknown_strategy_defaults_to_combo(self, generator):
        """Test that unknown strategy defaults to combo."""
        indicators = {
            "rsi": 25.0,
            "macd": 0.5,
            "macd_signal": 0.3,
            "ema_20": 150.0,
            "ema_50": 145.0,
        }
        result = generator.generate_signal(indicators, strategy="unknown")
        
        # Should use combo strategy
        assert result["strategy"] == "unknown"
        assert result["action"] in ["BUY", "SELL", "HOLD"]
    
    # Confidence Calculation Tests
    
    def test_confidence_all_bullish(self, generator):
        """Test confidence calculation with all bullish indicators."""
        indicators = {
            "rsi": 25.0,  # Strong oversold
            "macd": 1.0,
            "macd_signal": 0.0,  # Strong bullish
            "ema_20": 150.0,
            "ema_50": 145.0,
            "ema_200": 140.0,  # Strong uptrend
            "close": 140.0,
            "bb_lower": 145.0,
            "bb_upper": 155.0,
            "bb_middle": 150.0,  # Near lower band
            "stochastic_k": 15.0,  # Strong oversold
        }
        confidence = generator.calculate_confidence(indicators)
        
        assert confidence > 7.0  # High confidence
        assert confidence <= 10.0
    
    def test_confidence_all_bearish(self, generator):
        """Test confidence calculation with all bearish indicators."""
        indicators = {
            "rsi": 75.0,  # Strong overbought
            "macd": 0.0,
            "macd_signal": 1.0,  # Strong bearish
            "ema_20": 140.0,
            "ema_50": 145.0,
            "ema_200": 150.0,  # Strong downtrend
            "close": 160.0,
            "bb_lower": 145.0,
            "bb_upper": 155.0,
            "bb_middle": 150.0,  # Near upper band
            "stochastic_k": 85.0,  # Strong overbought
        }
        confidence = generator.calculate_confidence(indicators)
        
        assert confidence > 7.0  # High confidence
        assert confidence <= 10.0
    
    def test_confidence_mixed_signals(self, generator):
        """Test confidence calculation with mixed signals."""
        indicators = {
            "rsi": 50.0,  # Neutral
            "macd": 0.5,
            "macd_signal": 0.3,  # Weak bullish
            "ema_20": 145.0,
            "ema_50": 150.0,  # Bearish
        }
        confidence = generator.calculate_confidence(indicators)
        
        assert confidence < 7.0  # Low confidence
        assert confidence >= 0.0
    
    def test_confidence_no_indicators(self, generator):
        """Test confidence calculation with no indicators."""
        indicators = {}
        confidence = generator.calculate_confidence(indicators)
        
        assert confidence == 0.0
    
    def test_confidence_range(self, generator):
        """Test that confidence is always in valid range."""
        indicators = {
            "rsi": 25.0,
            "macd": 10.0,  # Extreme value
            "macd_signal": 0.0,
            "ema_20": 200.0,
            "ema_50": 100.0,
        }
        confidence = generator.calculate_confidence(indicators)
        
        assert 0.0 <= confidence <= 10.0
    
    # Bullish Signals Identification Tests
    
    def test_identify_bullish_signals_rsi(self, generator):
        """Test identification of RSI bullish signals."""
        indicators = {"rsi": 25.0}
        signals = generator.identify_bullish_signals(indicators)
        
        assert len(signals) > 0
        assert any("RSI" in s for s in signals)
    
    def test_identify_bullish_signals_macd(self, generator):
        """Test identification of MACD bullish signals."""
        indicators = {
            "macd": 0.5,
            "macd_signal": 0.3,
        }
        signals = generator.identify_bullish_signals(indicators)
        
        assert len(signals) > 0
        assert any("MACD" in s for s in signals)
    
    def test_identify_bullish_signals_ema(self, generator):
        """Test identification of EMA bullish signals."""
        indicators = {
            "ema_20": 150.0,
            "ema_50": 145.0,
            "ema_200": 140.0,
        }
        signals = generator.identify_bullish_signals(indicators)
        
        assert len(signals) > 0
        assert any("uptrend" in s.lower() for s in signals)
    
    def test_identify_bullish_signals_bollinger(self, generator):
        """Test identification of Bollinger Bands bullish signals."""
        indicators = {
            "close": 140.0,
            "bb_lower": 145.0,
        }
        signals = generator.identify_bullish_signals(indicators)
        
        assert len(signals) > 0
        assert any("Bollinger" in s for s in signals)
    
    def test_identify_bullish_signals_stochastic(self, generator):
        """Test identification of Stochastic bullish signals."""
        indicators = {"stochastic_k": 15.0}
        signals = generator.identify_bullish_signals(indicators)
        
        assert len(signals) > 0
        assert any("Stochastic" in s for s in signals)
    
    def test_identify_bullish_signals_obv(self, generator):
        """Test identification of OBV bullish signals."""
        indicators = {
            "obv": 1000000,
            "obv_prev": 900000,
        }
        signals = generator.identify_bullish_signals(indicators)
        
        assert len(signals) > 0
        assert any("Volume" in s for s in signals)
    
    def test_identify_bullish_signals_none(self, generator):
        """Test identification with no bullish signals."""
        indicators = {
            "rsi": 75.0,  # Overbought
            "macd": 0.3,
            "macd_signal": 0.5,  # Bearish
        }
        signals = generator.identify_bullish_signals(indicators)
        
        assert len(signals) == 0
    
    # Bearish Signals Identification Tests
    
    def test_identify_bearish_signals_rsi(self, generator):
        """Test identification of RSI bearish signals."""
        indicators = {"rsi": 75.0}
        signals = generator.identify_bearish_signals(indicators)
        
        assert len(signals) > 0
        assert any("RSI" in s for s in signals)
    
    def test_identify_bearish_signals_macd(self, generator):
        """Test identification of MACD bearish signals."""
        indicators = {
            "macd": 0.3,
            "macd_signal": 0.5,
        }
        signals = generator.identify_bearish_signals(indicators)
        
        assert len(signals) > 0
        assert any("MACD" in s for s in signals)
    
    def test_identify_bearish_signals_ema(self, generator):
        """Test identification of EMA bearish signals."""
        indicators = {
            "ema_20": 140.0,
            "ema_50": 145.0,
            "ema_200": 150.0,
        }
        signals = generator.identify_bearish_signals(indicators)
        
        assert len(signals) > 0
        assert any("downtrend" in s.lower() for s in signals)
    
    def test_identify_bearish_signals_bollinger(self, generator):
        """Test identification of Bollinger Bands bearish signals."""
        indicators = {
            "close": 160.0,
            "bb_upper": 155.0,
        }
        signals = generator.identify_bearish_signals(indicators)
        
        assert len(signals) > 0
        assert any("Bollinger" in s for s in signals)
    
    def test_identify_bearish_signals_stochastic(self, generator):
        """Test identification of Stochastic bearish signals."""
        indicators = {"stochastic_k": 85.0}
        signals = generator.identify_bearish_signals(indicators)
        
        assert len(signals) > 0
        assert any("Stochastic" in s for s in signals)
    
    def test_identify_bearish_signals_obv(self, generator):
        """Test identification of OBV bearish signals."""
        indicators = {
            "obv": 900000,
            "obv_prev": 1000000,
        }
        signals = generator.identify_bearish_signals(indicators)
        
        assert len(signals) > 0
        assert any("Volume" in s for s in signals)
    
    def test_identify_bearish_signals_none(self, generator):
        """Test identification with no bearish signals."""
        indicators = {
            "rsi": 25.0,  # Oversold
            "macd": 0.5,
            "macd_signal": 0.3,  # Bullish
        }
        signals = generator.identify_bearish_signals(indicators)
        
        assert len(signals) == 0
    
    # Edge Cases
    
    def test_none_values_in_indicators(self, generator):
        """Test handling of None values in indicators."""
        indicators = {
            "rsi": None,
            "macd": None,
            "macd_signal": None,
        }
        result = generator.generate_signal(indicators, strategy="combo")
        
        assert result["action"] == "HOLD"
        assert result["confidence"] == 0.0
    
    def test_partial_indicator_data(self, generator):
        """Test with partial indicator data."""
        indicators = {
            "rsi": 25.0,
            "macd": 0.5,
            # Missing macd_signal
            "ema_20": 150.0,
            # Missing ema_50
        }
        result = generator.generate_signal(indicators, strategy="combo")
        
        # Should handle gracefully
        assert result["action"] in ["BUY", "SELL", "HOLD"]
        assert 0.0 <= result["confidence"] <= 10.0
    
    def test_extreme_indicator_values(self, generator):
        """Test with extreme indicator values."""
        indicators = {
            "rsi": 0.0,  # Extreme oversold
            "macd": 100.0,  # Extreme value
            "macd_signal": -100.0,
            "ema_20": 1000000.0,
            "ema_50": 1.0,
        }
        result = generator.generate_signal(indicators, strategy="combo")
        
        # Should handle without crashing
        assert result["action"] in ["BUY", "SELL", "HOLD"]
        assert 0.0 <= result["confidence"] <= 10.0
    
    def test_result_structure(self, generator):
        """Test that result has all required fields."""
        indicators = {"rsi": 50.0}
        result = generator.generate_signal(indicators, strategy="rsi")
        
        assert "action" in result
        assert "confidence" in result
        assert "strategy" in result
        assert "bullish_signals" in result
        assert "bearish_signals" in result
        assert isinstance(result["bullish_signals"], list)
        assert isinstance(result["bearish_signals"], list)
        assert result["action"] in ["BUY", "SELL", "HOLD"]
        assert 0.0 <= result["confidence"] <= 10.0
