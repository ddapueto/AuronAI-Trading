"""AI-powered market analysis using Claude API."""

from typing import Dict, Any, Optional, List
import logging
import time
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """
    AI-powered market analyzer using Claude API.
    
    Provides comprehensive market analysis with fallback to rule-based
    analysis when API is unavailable.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AI analyzer.
        
        Args:
            api_key: Anthropic API key (optional)
        """
        self.api_key = api_key
        self.client = None
        self._cache: Dict[str, tuple] = {}  # symbol -> (result, timestamp)
        self.cache_ttl = 300  # 5 minutes
        
        # Initialize Anthropic client if API key provided
        if self.api_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
                logger.info("Claude API client initialized successfully")
            except ImportError:
                logger.warning("anthropic package not installed, using fallback analysis")
                self.client = None
            except Exception as e:
                logger.error(f"Failed to initialize Claude API client: {e}")
                self.client = None
        else:
            logger.info("No API key provided, using fallback analysis")
    
    def analyze_market(
        self,
        symbol: str,
        indicators: Dict[str, Any],
        current_price: float,
        price_change_pct: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze market conditions and provide trading recommendation.
        
        Args:
            symbol: Stock symbol
            indicators: Dictionary of calculated technical indicators
            current_price: Current stock price
            price_change_pct: Price change percentage (optional)
            
        Returns:
            Dictionary with:
                - action: "BUY", "SELL", or "HOLD"
                - confidence: Score from 1-10
                - bullish_signals: List of bullish factors
                - bearish_signals: List of bearish factors
                - reasoning: Explanation of recommendation
                - source: "claude_api" or "rule_based"
        """
        # Check cache first
        cache_key = f"{symbol}_{current_price}"
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Using cached analysis for {symbol}")
                return result
        
        # Try Claude API first if available
        if self.client:
            try:
                result = self._analyze_with_claude(
                    symbol, indicators, current_price, price_change_pct
                )
                result["source"] = "claude_api"
                
                # Cache the result
                self._cache[cache_key] = (result, time.time())
                return result
                
            except Exception as e:
                logger.warning(f"Claude API failed: {e}, falling back to rule-based")
        
        # Fallback to rule-based analysis
        result = self.fallback_analysis(symbol, indicators, current_price, price_change_pct)
        result["source"] = "rule_based"
        
        # Cache the result
        self._cache[cache_key] = (result, time.time())
        return result
    
    def _analyze_with_claude(
        self,
        symbol: str,
        indicators: Dict[str, Any],
        current_price: float,
        price_change_pct: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze market using Claude API.
        
        Args:
            symbol: Stock symbol
            indicators: Technical indicators
            current_price: Current price
            price_change_pct: Price change percentage
            
        Returns:
            Analysis result dictionary
        """
        # Build structured prompt
        prompt = self._build_prompt(symbol, indicators, current_price, price_change_pct)
        
        # Call Claude API with retry
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Extract text from response
                response_text = response.content[0].text
                
                # Parse the response
                return self.parse_recommendation(response_text, indicators)
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Claude API attempt {attempt + 1} failed: {e}, retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    raise
    
    def _build_prompt(
        self,
        symbol: str,
        indicators: Dict[str, Any],
        current_price: float,
        price_change_pct: Optional[float] = None
    ) -> str:
        """
        Build structured prompt for Claude API.
        
        Args:
            symbol: Stock symbol
            indicators: Technical indicators
            current_price: Current price
            price_change_pct: Price change percentage
            
        Returns:
            Formatted prompt string
        """
        # Format indicators for prompt
        indicator_text = []
        
        if indicators.get("rsi") is not None:
            indicator_text.append(f"- RSI: {indicators['rsi']:.2f}")
        
        if indicators.get("macd") is not None and indicators.get("macd_signal") is not None:
            indicator_text.append(
                f"- MACD: {indicators['macd']:.4f}, Signal: {indicators['macd_signal']:.4f}"
            )
        
        if indicators.get("ema_20") is not None:
            indicator_text.append(f"- EMA20: ${indicators['ema_20']:.2f}")
        if indicators.get("ema_50") is not None:
            indicator_text.append(f"- EMA50: ${indicators['ema_50']:.2f}")
        if indicators.get("ema_200") is not None:
            indicator_text.append(f"- EMA200: ${indicators['ema_200']:.2f}")
        
        if indicators.get("bb_upper") is not None:
            indicator_text.append(
                f"- Bollinger Bands: Upper ${indicators['bb_upper']:.2f}, "
                f"Middle ${indicators['bb_middle']:.2f}, Lower ${indicators['bb_lower']:.2f}"
            )
        
        if indicators.get("stochastic_k") is not None:
            indicator_text.append(f"- Stochastic %K: {indicators['stochastic_k']:.2f}")
        
        if indicators.get("atr") is not None:
            indicator_text.append(f"- ATR: ${indicators['atr']:.2f}")
        
        indicators_str = "\n".join(indicator_text)
        
        price_change_str = ""
        if price_change_pct is not None:
            price_change_str = f"\n- Price Change: {price_change_pct:+.2f}%"
        
        prompt = f"""You are a professional trading analyst. Analyze the following market data for {symbol} and provide a trading recommendation.

Current Market Data:
- Symbol: {symbol}
- Current Price: ${current_price:.2f}{price_change_str}

Technical Indicators:
{indicators_str}

Please provide your analysis in the following JSON format:
{{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": <1-10>,
    "bullish_signals": [<list of bullish factors>],
    "bearish_signals": [<list of bearish factors>],
    "reasoning": "<brief explanation of your recommendation>"
}}

Guidelines:
- BUY: Strong bullish signals, good entry opportunity
- SELL: Strong bearish signals, exit or short opportunity  
- HOLD: Mixed signals or insufficient conviction
- Confidence 1-3: Low, 4-7: Moderate, 8-10: High
- Consider indicator alignment and market context
- Be concise but specific in your reasoning

Respond ONLY with the JSON object, no additional text."""

        return prompt
    
    def parse_recommendation(
        self,
        response: str,
        indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse Claude API response into structured format.
        
        Args:
            response: Raw response text from Claude
            indicators: Original indicators (for fallback)
            
        Returns:
            Structured analysis result
        """
        try:
            # Try to extract JSON from response
            # Handle cases where Claude adds text before/after JSON
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[start_idx:end_idx]
            result = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["action", "confidence", "bullish_signals", "bearish_signals"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate action
            if result["action"] not in ["BUY", "SELL", "HOLD"]:
                logger.warning(f"Invalid action: {result['action']}, defaulting to HOLD")
                result["action"] = "HOLD"
            
            # Validate confidence
            try:
                confidence = float(result["confidence"])
                result["confidence"] = max(1.0, min(10.0, confidence))
            except (ValueError, TypeError):
                logger.warning(f"Invalid confidence: {result['confidence']}, defaulting to 5")
                result["confidence"] = 5.0
            
            # Ensure lists
            if not isinstance(result["bullish_signals"], list):
                result["bullish_signals"] = []
            if not isinstance(result["bearish_signals"], list):
                result["bearish_signals"] = []
            
            # Add reasoning if missing
            if "reasoning" not in result:
                result["reasoning"] = "Analysis based on technical indicators"
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse Claude response: {e}")
            logger.debug(f"Response was: {response}")
            
            # Return fallback result
            return self.fallback_analysis("", indicators, 0.0, None)
    
    def fallback_analysis(
        self,
        symbol: str,
        indicators: Dict[str, Any],
        current_price: float,
        price_change_pct: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Rule-based analysis when Claude API is unavailable.
        
        Args:
            symbol: Stock symbol
            indicators: Technical indicators
            current_price: Current price
            price_change_pct: Price change percentage
            
        Returns:
            Analysis result dictionary
        """
        bullish_signals = []
        bearish_signals = []
        bullish_score = 0
        bearish_score = 0
        
        # RSI analysis
        rsi = indicators.get("rsi")
        if rsi is not None:
            if rsi < 30:
                bullish_signals.append(f"RSI oversold at {rsi:.1f}")
                bullish_score += 2
            elif rsi < 40:
                bullish_signals.append(f"RSI approaching oversold at {rsi:.1f}")
                bullish_score += 1
            elif rsi > 70:
                bearish_signals.append(f"RSI overbought at {rsi:.1f}")
                bearish_score += 2
            elif rsi > 60:
                bearish_signals.append(f"RSI approaching overbought at {rsi:.1f}")
                bearish_score += 1
        
        # MACD analysis
        macd = indicators.get("macd")
        macd_signal = indicators.get("macd_signal")
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                bullish_signals.append("MACD above signal line")
                bullish_score += 2
            else:
                bearish_signals.append("MACD below signal line")
                bearish_score += 2
        
        # EMA trend analysis
        ema_20 = indicators.get("ema_20")
        ema_50 = indicators.get("ema_50")
        ema_200 = indicators.get("ema_200")
        
        if ema_20 is not None and ema_50 is not None:
            if ema_200 is not None:
                if ema_20 > ema_50 > ema_200:
                    bullish_signals.append("Strong uptrend (EMA20 > EMA50 > EMA200)")
                    bullish_score += 3
                elif ema_20 < ema_50 < ema_200:
                    bearish_signals.append("Strong downtrend (EMA20 < EMA50 < EMA200)")
                    bearish_score += 3
            else:
                if ema_20 > ema_50:
                    bullish_signals.append("Uptrend (EMA20 > EMA50)")
                    bullish_score += 2
                elif ema_20 < ema_50:
                    bearish_signals.append("Downtrend (EMA20 < EMA50)")
                    bearish_score += 2
        
        # Bollinger Bands analysis
        close = current_price
        bb_lower = indicators.get("bb_lower")
        bb_upper = indicators.get("bb_upper")
        
        if bb_lower is not None and bb_upper is not None:
            if close < bb_lower:
                bullish_signals.append("Price below lower Bollinger Band")
                bullish_score += 2
            elif close > bb_upper:
                bearish_signals.append("Price above upper Bollinger Band")
                bearish_score += 2
        
        # Stochastic analysis
        stoch_k = indicators.get("stochastic_k")
        if stoch_k is not None:
            if stoch_k < 20:
                bullish_signals.append(f"Stochastic oversold at {stoch_k:.1f}")
                bullish_score += 2
            elif stoch_k > 80:
                bearish_signals.append(f"Stochastic overbought at {stoch_k:.1f}")
                bearish_score += 2
        
        # Determine action and confidence
        if bullish_score >= 5 and bullish_score > bearish_score:
            action = "BUY"
            confidence = min(10, 5 + bullish_score - bearish_score)
            reasoning = f"Strong bullish signals detected ({bullish_score} bullish vs {bearish_score} bearish)"
        elif bearish_score >= 5 and bearish_score > bullish_score:
            action = "SELL"
            confidence = min(10, 5 + bearish_score - bullish_score)
            reasoning = f"Strong bearish signals detected ({bearish_score} bearish vs {bullish_score} bullish)"
        else:
            action = "HOLD"
            confidence = 5
            reasoning = f"Mixed signals ({bullish_score} bullish, {bearish_score} bearish)"
        
        return {
            "action": action,
            "confidence": float(confidence),
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals,
            "reasoning": reasoning,
        }
    
    def clear_cache(self):
        """Clear the analysis cache."""
        self._cache.clear()
        logger.debug("Analysis cache cleared")
