"""Unit tests for AIAnalyzer."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.auronai.analysis.ai_analyzer import AIAnalyzer


class TestAIAnalyzerInitialization:
    """Test AIAnalyzer initialization."""
    
    def test_init_without_api_key(self):
        """Test initialization without API key."""
        analyzer = AIAnalyzer()
        
        assert analyzer.api_key is None
        assert analyzer.client is None
        assert analyzer.cache_ttl == 300
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        # Mock the anthropic module import
        with patch.dict("sys.modules", {"anthropic": Mock()}):
            with patch("anthropic.Anthropic") as mock_anthropic:
                analyzer = AIAnalyzer(api_key="test-key")
                
                assert analyzer.api_key == "test-key"
                mock_anthropic.assert_called_once_with(api_key="test-key")
    
    def test_init_with_missing_anthropic_package(self):
        """Test initialization when anthropic package is not installed."""
        # Simulate missing anthropic package
        with patch.dict("sys.modules", {"anthropic": None}):
            analyzer = AIAnalyzer(api_key="test-key")
            
            assert analyzer.client is None


class TestFallbackAnalysis:
    """Test rule-based fallback analysis."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer without API key."""
        return AIAnalyzer()
    
    def test_fallback_strong_bullish(self, analyzer):
        """Test fallback with strong bullish signals."""
        indicators = {
            "rsi": 25.0,  # Oversold
            "macd": 0.5,
            "macd_signal": 0.3,  # Bullish
            "ema_20": 150.0,
            "ema_50": 145.0,
            "ema_200": 140.0,  # Strong uptrend
            "stochastic_k": 15.0,  # Oversold
        }
        
        result = analyzer.fallback_analysis("AAPL", indicators, 150.0, None)
        
        assert result["action"] == "BUY"
        assert result["confidence"] >= 7.0
        assert len(result["bullish_signals"]) > 0
        assert "reasoning" in result
    
    def test_fallback_strong_bearish(self, analyzer):
        """Test fallback with strong bearish signals."""
        indicators = {
            "rsi": 75.0,  # Overbought
            "macd": 0.3,
            "macd_signal": 0.5,  # Bearish
            "ema_20": 140.0,
            "ema_50": 145.0,
            "ema_200": 150.0,  # Strong downtrend
            "stochastic_k": 85.0,  # Overbought
        }
        
        result = analyzer.fallback_analysis("AAPL", indicators, 140.0, None)
        
        assert result["action"] == "SELL"
        assert result["confidence"] >= 7.0
        assert len(result["bearish_signals"]) > 0
    
    def test_fallback_mixed_signals(self, analyzer):
        """Test fallback with mixed signals."""
        indicators = {
            "rsi": 50.0,  # Neutral
            "macd": 0.5,
            "macd_signal": 0.3,  # Bullish
            "ema_20": 145.0,
            "ema_50": 150.0,  # Bearish
        }
        
        result = analyzer.fallback_analysis("AAPL", indicators, 145.0, None)
        
        assert result["action"] == "HOLD"
        assert result["confidence"] == 5.0
    
    def test_fallback_rsi_oversold(self, analyzer):
        """Test RSI oversold detection."""
        indicators = {"rsi": 25.0}
        
        result = analyzer.fallback_analysis("AAPL", indicators, 100.0, None)
        
        assert any("RSI oversold" in s for s in result["bullish_signals"])
    
    def test_fallback_rsi_overbought(self, analyzer):
        """Test RSI overbought detection."""
        indicators = {"rsi": 75.0}
        
        result = analyzer.fallback_analysis("AAPL", indicators, 100.0, None)
        
        assert any("RSI overbought" in s for s in result["bearish_signals"])
    
    def test_fallback_macd_bullish(self, analyzer):
        """Test MACD bullish signal."""
        indicators = {
            "macd": 0.5,
            "macd_signal": 0.3,
        }
        
        result = analyzer.fallback_analysis("AAPL", indicators, 100.0, None)
        
        assert any("MACD above signal" in s for s in result["bullish_signals"])
    
    def test_fallback_ema_uptrend(self, analyzer):
        """Test EMA uptrend detection."""
        indicators = {
            "ema_20": 150.0,
            "ema_50": 145.0,
            "ema_200": 140.0,
        }
        
        result = analyzer.fallback_analysis("AAPL", indicators, 150.0, None)
        
        assert any("uptrend" in s.lower() for s in result["bullish_signals"])
    
    def test_fallback_bollinger_oversold(self, analyzer):
        """Test Bollinger Bands oversold."""
        indicators = {
            "bb_lower": 105.0,
            "bb_upper": 115.0,
        }
        
        result = analyzer.fallback_analysis("AAPL", indicators, 100.0, None)
        
        assert any("Bollinger" in s for s in result["bullish_signals"])
    
    def test_fallback_empty_indicators(self, analyzer):
        """Test fallback with no indicators."""
        indicators = {}
        
        result = analyzer.fallback_analysis("AAPL", indicators, 100.0, None)
        
        assert result["action"] == "HOLD"
        assert result["confidence"] == 5.0


class TestResponseParsing:
    """Test Claude API response parsing."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer."""
        return AIAnalyzer()
    
    def test_parse_valid_json(self, analyzer):
        """Test parsing valid JSON response."""
        response = """{
            "action": "BUY",
            "confidence": 8,
            "bullish_signals": ["RSI oversold", "MACD bullish"],
            "bearish_signals": [],
            "reasoning": "Strong bullish momentum"
        }"""
        
        result = analyzer.parse_recommendation(response, {})
        
        assert result["action"] == "BUY"
        assert result["confidence"] == 8.0
        assert len(result["bullish_signals"]) == 2
        assert "reasoning" in result
    
    def test_parse_json_with_extra_text(self, analyzer):
        """Test parsing JSON with surrounding text."""
        response = """Here's my analysis:
        {
            "action": "SELL",
            "confidence": 7,
            "bullish_signals": [],
            "bearish_signals": ["RSI overbought"],
            "reasoning": "Overbought conditions"
        }
        Hope this helps!"""
        
        result = analyzer.parse_recommendation(response, {})
        
        assert result["action"] == "SELL"
        assert result["confidence"] == 7.0
    
    def test_parse_invalid_action(self, analyzer):
        """Test parsing with invalid action."""
        response = """{
            "action": "INVALID",
            "confidence": 5,
            "bullish_signals": [],
            "bearish_signals": []
        }"""
        
        result = analyzer.parse_recommendation(response, {})
        
        assert result["action"] == "HOLD"  # Should default to HOLD
    
    def test_parse_invalid_confidence(self, analyzer):
        """Test parsing with invalid confidence."""
        response = """{
            "action": "BUY",
            "confidence": "high",
            "bullish_signals": [],
            "bearish_signals": []
        }"""
        
        result = analyzer.parse_recommendation(response, {})
        
        assert result["confidence"] == 5.0  # Should default to 5
    
    def test_parse_confidence_out_of_range(self, analyzer):
        """Test parsing with confidence out of range."""
        response = """{
            "action": "BUY",
            "confidence": 15,
            "bullish_signals": [],
            "bearish_signals": []
        }"""
        
        result = analyzer.parse_recommendation(response, {})
        
        assert result["confidence"] == 10.0  # Should cap at 10
    
    def test_parse_missing_fields(self, analyzer):
        """Test parsing with missing required fields."""
        response = """{
            "action": "BUY"
        }"""
        
        indicators = {"rsi": 50.0}
        result = analyzer.parse_recommendation(response, indicators)
        
        # Should fall back to rule-based
        assert "action" in result
        assert "confidence" in result
    
    def test_parse_malformed_json(self, analyzer):
        """Test parsing malformed JSON."""
        response = "This is not JSON at all"
        
        indicators = {"rsi": 50.0}
        result = analyzer.parse_recommendation(response, indicators)
        
        # Should fall back to rule-based
        assert "action" in result
        assert result["action"] in ["BUY", "SELL", "HOLD"]
    
    def test_parse_non_list_signals(self, analyzer):
        """Test parsing when signals are not lists."""
        response = """{
            "action": "BUY",
            "confidence": 7,
            "bullish_signals": "RSI oversold",
            "bearish_signals": null
        }"""
        
        result = analyzer.parse_recommendation(response, {})
        
        assert isinstance(result["bullish_signals"], list)
        assert isinstance(result["bearish_signals"], list)


class TestAnalyzeMarket:
    """Test main analyze_market method."""
    
    def test_analyze_without_api_key(self):
        """Test analysis without API key uses fallback."""
        analyzer = AIAnalyzer()
        
        indicators = {
            "rsi": 25.0,
            "macd": 0.5,
            "macd_signal": 0.3,
        }
        
        result = analyzer.analyze_market("AAPL", indicators, 150.0)
        
        assert result["source"] == "rule_based"
        assert result["action"] in ["BUY", "SELL", "HOLD"]
    
    def test_analyze_with_cache(self):
        """Test that cache is used for repeated requests."""
        analyzer = AIAnalyzer()
        
        indicators = {"rsi": 50.0}
        
        # First call
        result1 = analyzer.analyze_market("AAPL", indicators, 150.0)
        
        # Second call (should use cache)
        result2 = analyzer.analyze_market("AAPL", indicators, 150.0)
        
        assert result1 == result2
    
    def test_clear_cache(self):
        """Test cache clearing."""
        analyzer = AIAnalyzer()
        
        indicators = {"rsi": 50.0}
        analyzer.analyze_market("AAPL", indicators, 150.0)
        
        assert len(analyzer._cache) > 0
        
        analyzer.clear_cache()
        
        assert len(analyzer._cache) == 0
    
    def test_analyze_with_api_success(self):
        """Test successful API call."""
        # Mock the anthropic module
        with patch.dict("sys.modules", {"anthropic": Mock()}):
            with patch("anthropic.Anthropic") as mock_anthropic:
                # Mock the API response
                mock_client = Mock()
                mock_response = Mock()
                mock_response.content = [Mock(text="""{
            "action": "BUY",
            "confidence": 8,
            "bullish_signals": ["Strong momentum"],
            "bearish_signals": [],
            "reasoning": "Bullish setup"
        }""")]
                mock_client.messages.create.return_value = mock_response
                mock_anthropic.return_value = mock_client
                
                analyzer = AIAnalyzer(api_key="test-key")
                indicators = {"rsi": 30.0}
                
                result = analyzer.analyze_market("AAPL", indicators, 150.0)
                
                assert result["source"] == "claude_api"
                assert result["action"] == "BUY"
                assert result["confidence"] == 8.0
    
    def test_analyze_with_api_failure_fallback(self):
        """Test fallback when API fails."""
        # Mock the anthropic module
        with patch.dict("sys.modules", {"anthropic": Mock()}):
            with patch("anthropic.Anthropic") as mock_anthropic:
                # Mock API to raise exception
                mock_client = Mock()
                mock_client.messages.create.side_effect = Exception("API Error")
                mock_anthropic.return_value = mock_client
                
                analyzer = AIAnalyzer(api_key="test-key")
                indicators = {"rsi": 25.0, "macd": 0.5, "macd_signal": 0.3}
                
                result = analyzer.analyze_market("AAPL", indicators, 150.0)
                
                # Should fall back to rule-based
                assert result["source"] == "rule_based"
                assert result["action"] in ["BUY", "SELL", "HOLD"]


class TestPromptBuilding:
    """Test prompt construction."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer."""
        return AIAnalyzer()
    
    def test_build_prompt_basic(self, analyzer):
        """Test basic prompt building."""
        indicators = {
            "rsi": 50.0,
            "macd": 0.5,
            "macd_signal": 0.3,
        }
        
        prompt = analyzer._build_prompt("AAPL", indicators, 150.0, None)
        
        assert "AAPL" in prompt
        assert "150.00" in prompt
        assert "RSI" in prompt
        assert "MACD" in prompt
        assert "JSON" in prompt
    
    def test_build_prompt_with_price_change(self, analyzer):
        """Test prompt with price change."""
        indicators = {"rsi": 50.0}
        
        prompt = analyzer._build_prompt("AAPL", indicators, 150.0, 2.5)
        
        assert "+2.50%" in prompt
    
    def test_build_prompt_with_all_indicators(self, analyzer):
        """Test prompt with all indicators."""
        indicators = {
            "rsi": 50.0,
            "macd": 0.5,
            "macd_signal": 0.3,
            "ema_20": 150.0,
            "ema_50": 145.0,
            "ema_200": 140.0,
            "bb_upper": 155.0,
            "bb_middle": 150.0,
            "bb_lower": 145.0,
            "stochastic_k": 50.0,
            "atr": 2.5,
        }
        
        prompt = analyzer._build_prompt("AAPL", indicators, 150.0, None)
        
        assert "RSI" in prompt
        assert "MACD" in prompt
        assert "EMA20" in prompt
        assert "EMA50" in prompt
        assert "EMA200" in prompt
        assert "Bollinger" in prompt
        assert "Stochastic" in prompt
        assert "ATR" in prompt


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_analyze_with_none_indicators(self):
        """Test analysis with None indicator values."""
        analyzer = AIAnalyzer()
        
        indicators = {
            "rsi": None,
            "macd": None,
            "macd_signal": None,
        }
        
        result = analyzer.analyze_market("AAPL", indicators, 150.0)
        
        assert result["action"] == "HOLD"
    
    def test_analyze_with_empty_indicators(self):
        """Test analysis with empty indicators dict."""
        analyzer = AIAnalyzer()
        
        result = analyzer.analyze_market("AAPL", {}, 150.0)
        
        assert result["action"] == "HOLD"
        assert result["confidence"] == 5.0
    
    def test_fallback_with_extreme_values(self):
        """Test fallback with extreme indicator values."""
        analyzer = AIAnalyzer()
        
        indicators = {
            "rsi": 0.0,
            "macd": 1000.0,
            "macd_signal": -1000.0,
        }
        
        result = analyzer.fallback_analysis("AAPL", indicators, 150.0, None)
        
        # Should handle without crashing
        assert result["action"] in ["BUY", "SELL", "HOLD"]
        assert 1.0 <= result["confidence"] <= 10.0
