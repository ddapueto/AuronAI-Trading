"""Signal generation module for trading strategies."""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Generate trading signals from technical indicators.
    
    Supports multiple strategies: RSI, MACD, EMA Cross, and Combo.
    Calculates confidence scores based on indicator alignment.
    """
    
    def __init__(self):
        """Initialize signal generator."""
        # Weights for confidence calculation
        self.indicator_weights = {
            "rsi": 0.20,
            "macd": 0.25,
            "ema": 0.25,
            "bollinger": 0.15,
            "stochastic": 0.15,
        }
        
    def generate_signal(
        self, indicators: Dict[str, Any], strategy: str = "combo"
    ) -> Dict[str, Any]:
        """
        Generate trading signal based on strategy.
        
        Args:
            indicators: Dictionary of calculated technical indicators
            strategy: Strategy to use ("rsi", "macd", "ema", "combo")
            
        Returns:
            Dictionary with:
                - action: "BUY", "SELL", or "HOLD"
                - confidence: Score from 0-10
                - strategy: Strategy used
                - bullish_signals: List of bullish factors
                - bearish_signals: List of bearish factors
        """
        strategy = strategy.lower()
        
        if strategy == "rsi":
            action = self._rsi_strategy(indicators)
        elif strategy == "macd":
            action = self._macd_strategy(indicators)
        elif strategy == "ema":
            action = self._ema_strategy(indicators)
        elif strategy == "combo":
            action = self._combo_strategy(indicators)
        else:
            logger.warning(f"Unknown strategy {strategy}, using combo")
            action = self._combo_strategy(indicators)
            
        # Identify signals
        bullish_signals = self.identify_bullish_signals(indicators)
        bearish_signals = self.identify_bearish_signals(indicators)
        
        # Calculate confidence
        confidence = self.calculate_confidence(indicators)
        
        return {
            "action": action,
            "confidence": confidence,
            "strategy": strategy,
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals,
        }
        
    def _rsi_strategy(self, indicators: Dict[str, Any]) -> str:
        """RSI oversold/overbought strategy."""
        rsi = indicators.get("rsi")
        
        if rsi is None:
            return "HOLD"
            
        if rsi < 30:
            return "BUY"  # Oversold
        elif rsi > 70:
            return "SELL"  # Overbought
        else:
            return "HOLD"
            
    def _macd_strategy(self, indicators: Dict[str, Any]) -> str:
        """MACD crossover strategy."""
        macd = indicators.get("macd")
        macd_signal = indicators.get("macd_signal")
        macd_prev = indicators.get("macd_prev")
        signal_prev = indicators.get("macd_signal_prev")
        
        if None in [macd, macd_signal, macd_prev, signal_prev]:
            return "HOLD"
            
        # Check for crossover
        if macd_prev <= signal_prev and macd > macd_signal:
            return "BUY"  # Bullish crossover
        elif macd_prev >= signal_prev and macd < macd_signal:
            return "SELL"  # Bearish crossover
        elif macd > macd_signal:
            return "BUY"  # MACD above signal
        elif macd < macd_signal:
            return "SELL"  # MACD below signal
        else:
            return "HOLD"
            
    def _ema_strategy(self, indicators: Dict[str, Any]) -> str:
        """EMA trend following strategy."""
        ema_20 = indicators.get("ema_20")
        ema_50 = indicators.get("ema_50")
        ema_200 = indicators.get("ema_200")
        
        if None in [ema_20, ema_50]:
            return "HOLD"
            
        # Strong uptrend: EMA20 > EMA50 > EMA200
        if ema_200 is not None:
            if ema_20 > ema_50 > ema_200:
                return "BUY"
            elif ema_20 < ema_50 < ema_200:
                return "SELL"
                
        # Simple trend: EMA20 > EMA50
        if ema_20 > ema_50:
            return "BUY"
        elif ema_20 < ema_50:
            return "SELL"
        else:
            return "HOLD"
            
    def _combo_strategy(self, indicators: Dict[str, Any]) -> str:
        """
        Combo strategy requiring 3+ aligned signals.
        
        Counts bullish and bearish signals from different indicators
        and requires majority alignment.
        """
        bullish_count = 0
        bearish_count = 0
        
        # RSI signals
        rsi = indicators.get("rsi")
        if rsi is not None:
            if rsi < 30:
                bullish_count += 1
            elif rsi > 70:
                bearish_count += 1
            elif rsi < 40:
                bullish_count += 0.5  # Weak bullish
            elif rsi > 60:
                bearish_count += 0.5  # Weak bearish
                
        # MACD signals
        macd = indicators.get("macd")
        macd_signal = indicators.get("macd_signal")
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                bullish_count += 1
            else:
                bearish_count += 1
                
        # EMA signals
        ema_20 = indicators.get("ema_20")
        ema_50 = indicators.get("ema_50")
        if ema_20 is not None and ema_50 is not None:
            if ema_20 > ema_50:
                bullish_count += 1
            else:
                bearish_count += 1
                
        # Bollinger Bands signals
        close = indicators.get("close")
        bb_lower = indicators.get("bb_lower")
        bb_upper = indicators.get("bb_upper")
        if None not in [close, bb_lower, bb_upper]:
            if close < bb_lower:
                bullish_count += 1  # Oversold
            elif close > bb_upper:
                bearish_count += 1  # Overbought
                
        # Stochastic signals
        stoch_k = indicators.get("stochastic_k")
        if stoch_k is not None:
            if stoch_k < 20:
                bullish_count += 1
            elif stoch_k > 80:
                bearish_count += 1
                
        # Require 3+ aligned signals
        if bullish_count >= 3:
            return "BUY"
        elif bearish_count >= 3:
            return "SELL"
        else:
            return "HOLD"
            
    def calculate_confidence(self, indicators: Dict[str, Any]) -> float:
        """
        Calculate confidence score (0-10) based on indicator alignment.
        
        Uses weighted sum of aligned indicators:
        - RSI: 20%
        - MACD: 25%
        - EMA: 25%
        - Bollinger: 15%
        - Stochastic: 15%
        
        Args:
            indicators: Dictionary of calculated indicators
            
        Returns:
            Confidence score from 0 to 10
        """
        bullish_score = 0.0
        bearish_score = 0.0
        total_weight = 0.0
        
        # RSI contribution (20%)
        rsi = indicators.get("rsi")
        if rsi is not None:
            weight = self.indicator_weights["rsi"]
            total_weight += weight
            
            if rsi < 30:
                bullish_score += weight * 1.0  # Strong oversold
            elif rsi < 40:
                bullish_score += weight * 0.5  # Weak oversold
            elif rsi > 70:
                bearish_score += weight * 1.0  # Strong overbought
            elif rsi > 60:
                bearish_score += weight * 0.5  # Weak overbought
                
        # MACD contribution (25%)
        macd = indicators.get("macd")
        macd_signal = indicators.get("macd_signal")
        if macd is not None and macd_signal is not None:
            weight = self.indicator_weights["macd"]
            total_weight += weight
            
            diff = macd - macd_signal
            if diff > 0:
                # Normalize to 0-1 range (assume max diff of 5)
                strength = min(abs(diff) / 5.0, 1.0)
                bullish_score += weight * strength
            else:
                strength = min(abs(diff) / 5.0, 1.0)
                bearish_score += weight * strength
                
        # EMA contribution (25%)
        ema_20 = indicators.get("ema_20")
        ema_50 = indicators.get("ema_50")
        ema_200 = indicators.get("ema_200")
        
        if ema_20 is not None and ema_50 is not None:
            weight = self.indicator_weights["ema"]
            total_weight += weight
            
            # Calculate trend strength
            if ema_200 is not None:
                if ema_20 > ema_50 > ema_200:
                    bullish_score += weight * 1.0  # Strong uptrend
                elif ema_20 < ema_50 < ema_200:
                    bearish_score += weight * 1.0  # Strong downtrend
                elif ema_20 > ema_50:
                    bullish_score += weight * 0.5  # Weak uptrend
                elif ema_20 < ema_50:
                    bearish_score += weight * 0.5  # Weak downtrend
            else:
                if ema_20 > ema_50:
                    bullish_score += weight * 0.7
                elif ema_20 < ema_50:
                    bearish_score += weight * 0.7
                    
        # Bollinger Bands contribution (15%)
        close = indicators.get("close")
        bb_lower = indicators.get("bb_lower")
        bb_upper = indicators.get("bb_upper")
        bb_middle = indicators.get("bb_middle")
        
        if None not in [close, bb_lower, bb_upper, bb_middle]:
            weight = self.indicator_weights["bollinger"]
            total_weight += weight
            
            band_width = bb_upper - bb_lower
            if band_width > 0:
                # Position within bands (0 = lower, 1 = upper)
                position = (close - bb_lower) / band_width
                
                if position < 0.2:
                    bullish_score += weight * 1.0  # Near lower band
                elif position < 0.4:
                    bullish_score += weight * 0.5
                elif position > 0.8:
                    bearish_score += weight * 1.0  # Near upper band
                elif position > 0.6:
                    bearish_score += weight * 0.5
                    
        # Stochastic contribution (15%)
        stoch_k = indicators.get("stochastic_k")
        if stoch_k is not None:
            weight = self.indicator_weights["stochastic"]
            total_weight += weight
            
            if stoch_k < 20:
                bullish_score += weight * 1.0  # Oversold
            elif stoch_k < 30:
                bullish_score += weight * 0.5
            elif stoch_k > 80:
                bearish_score += weight * 1.0  # Overbought
            elif stoch_k > 70:
                bearish_score += weight * 0.5
                
        # Calculate final confidence (0-10 scale)
        if total_weight == 0:
            return 0.0
            
        # Net score: positive = bullish, negative = bearish
        net_score = (bullish_score - bearish_score) / total_weight
        
        # Convert to 0-10 confidence (higher = more confident)
        confidence = abs(net_score) * 10.0
        
        return round(min(confidence, 10.0), 1)
        
    def identify_bullish_signals(self, indicators: Dict[str, Any]) -> List[str]:
        """
        Identify all bullish factors from indicators.
        
        Args:
            indicators: Dictionary of calculated indicators
            
        Returns:
            List of bullish signal descriptions
        """
        signals = []
        
        # RSI signals
        rsi = indicators.get("rsi")
        if rsi is not None:
            if rsi < 30:
                signals.append(f"RSI oversold at {rsi:.1f}")
            elif rsi < 40:
                signals.append(f"RSI approaching oversold at {rsi:.1f}")
                
        # MACD signals
        macd = indicators.get("macd")
        macd_signal = indicators.get("macd_signal")
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                signals.append("MACD above signal line (bullish)")
                
        # EMA signals
        ema_20 = indicators.get("ema_20")
        ema_50 = indicators.get("ema_50")
        ema_200 = indicators.get("ema_200")
        
        if ema_20 is not None and ema_50 is not None:
            if ema_200 is not None and ema_20 > ema_50 > ema_200:
                signals.append("Strong uptrend (EMA20 > EMA50 > EMA200)")
            elif ema_20 > ema_50:
                signals.append("Uptrend (EMA20 > EMA50)")
                
        # Bollinger Bands signals
        close = indicators.get("close")
        bb_lower = indicators.get("bb_lower")
        if close is not None and bb_lower is not None:
            if close < bb_lower:
                signals.append("Price below lower Bollinger Band (oversold)")
                
        # Stochastic signals
        stoch_k = indicators.get("stochastic_k")
        if stoch_k is not None:
            if stoch_k < 20:
                signals.append(f"Stochastic oversold at {stoch_k:.1f}")
                
        # Volume signals
        obv = indicators.get("obv")
        obv_prev = indicators.get("obv_prev")
        if obv is not None and obv_prev is not None:
            if obv > obv_prev:
                signals.append("On-Balance Volume increasing")
                
        return signals
        
    def identify_bearish_signals(self, indicators: Dict[str, Any]) -> List[str]:
        """
        Identify all bearish factors from indicators.
        
        Args:
            indicators: Dictionary of calculated indicators
            
        Returns:
            List of bearish signal descriptions
        """
        signals = []
        
        # RSI signals
        rsi = indicators.get("rsi")
        if rsi is not None:
            if rsi > 70:
                signals.append(f"RSI overbought at {rsi:.1f}")
            elif rsi > 60:
                signals.append(f"RSI approaching overbought at {rsi:.1f}")
                
        # MACD signals
        macd = indicators.get("macd")
        macd_signal = indicators.get("macd_signal")
        if macd is not None and macd_signal is not None:
            if macd < macd_signal:
                signals.append("MACD below signal line (bearish)")
                
        # EMA signals
        ema_20 = indicators.get("ema_20")
        ema_50 = indicators.get("ema_50")
        ema_200 = indicators.get("ema_200")
        
        if ema_20 is not None and ema_50 is not None:
            if ema_200 is not None and ema_20 < ema_50 < ema_200:
                signals.append("Strong downtrend (EMA20 < EMA50 < EMA200)")
            elif ema_20 < ema_50:
                signals.append("Downtrend (EMA20 < EMA50)")
                
        # Bollinger Bands signals
        close = indicators.get("close")
        bb_upper = indicators.get("bb_upper")
        if close is not None and bb_upper is not None:
            if close > bb_upper:
                signals.append("Price above upper Bollinger Band (overbought)")
                
        # Stochastic signals
        stoch_k = indicators.get("stochastic_k")
        if stoch_k is not None:
            if stoch_k > 80:
                signals.append(f"Stochastic overbought at {stoch_k:.1f}")
                
        # Volume signals
        obv = indicators.get("obv")
        obv_prev = indicators.get("obv_prev")
        if obv is not None and obv_prev is not None:
            if obv < obv_prev:
                signals.append("On-Balance Volume decreasing")
                
        return signals
