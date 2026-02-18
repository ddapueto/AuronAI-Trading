"""
Short-only momentum strategy for bear markets.

This strategy selects weakest stocks based on relative strength
and only trades during BEAR market regimes.
"""

from datetime import datetime
from typing import Dict, Any

import pandas as pd

from auronai.strategies.base_strategy import (
    BaseStrategy,
    MarketRegime,
    StrategyParams
)
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


class ShortMomentumStrategy(BaseStrategy):
    """
    Short-only momentum strategy for BEAR regime.
    
    Selection Criteria:
    - Bottom K symbols by relative strength (weakest)
    - Negative EMA trend (EMA20 < EMA50)
    - RSI not oversold (> 30)
    
    Exit Rules:
    - Take profit: -5% (price drops 5%)
    - Time exit: 10 days (configurable via holding_days)
    - Trend reversal: EMA20 crosses above EMA50
    
    **Validates: Requirements FR-7**
    """
    
    @property
    def name(self) -> str:
        """Strategy name for display."""
        return "Short Momentum"
    
    @property
    def description(self) -> str:
        """Strategy description for UI."""
        return "Short-only momentum strategy for bear markets"
    
    def generate_signals(
        self,
        features: pd.DataFrame,
        regime: MarketRegime,
        current_date: datetime
    ) -> Dict[str, float]:
        """
        Select bottom K symbols by relative strength.
        
        Args:
            features: DataFrame with OHLCV + indicators for all symbols
            regime: Current market regime
            current_date: Current simulation date
        
        Returns:
            Dictionary mapping symbol -> target weight (negative for shorts)
            Empty dict if not in BEAR regime
        """
        # Only trade in bear regime
        if regime != MarketRegime.BEAR:
            logger.debug(f"Skipping signals - regime is {regime.value}, need BEAR")
            return {}
        
        # Filter: EMA20 < EMA50 and RSI > 30
        try:
            candidates = features[
                (features['ema_20'] < features['ema_50']) &
                (features['rsi'] > 30) &
                (~features['ema_20'].isna()) &
                (~features['ema_50'].isna()) &
                (~features['rsi'].isna()) &
                (~features['relative_strength'].isna())
            ].copy()
            
            if len(candidates) == 0:
                logger.debug("No candidates passed filters")
                return {}
            
            # Sort by relative strength (ascending = weakest first)
            candidates = candidates.sort_values('relative_strength', ascending=True)
            
            # Select bottom K (weakest)
            selected = candidates.head(self.params.top_k)
            
            # Equal weight distribution (negative for shorts)
            weight = -1.0 / len(selected) if len(selected) > 0 else 0.0
            
            signals = {symbol: weight for symbol in selected.index}
            
            logger.info(
                f"Generated {len(signals)} short signals: "
                f"{list(signals.keys())}"
            )
            
            return signals
            
        except KeyError as e:
            logger.error(f"Missing required column in features: {e}")
            return {}
    
    def risk_model(
        self,
        target_weights: Dict[str, float],
        features: pd.DataFrame,
        current_portfolio: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Apply risk constraints to target weights.
        
        Constraints:
        - Maximum total exposure = risk_budget (default 20%)
        - Maximum position size = risk_budget / top_k
        
        Args:
            target_weights: Raw weights from generate_signals()
            features: Current market features
            current_portfolio: Current positions
        
        Returns:
            Adjusted weights after risk constraints
        """
        if not target_weights:
            return {}
        
        # Calculate total target exposure (absolute value for shorts)
        total_weight = sum(abs(w) for w in target_weights.values())
        
        # Scale down if exceeds risk budget
        if total_weight > self.params.risk_budget:
            scale_factor = self.params.risk_budget / total_weight
            adjusted = {
                symbol: weight * scale_factor
                for symbol, weight in target_weights.items()
            }
            logger.info(
                f"Scaled weights by {scale_factor:.2f} to respect "
                f"risk_budget={self.params.risk_budget}"
            )
        else:
            adjusted = target_weights.copy()
        
        # Ensure no single position exceeds max
        max_position = self.params.risk_budget / self.params.top_k
        for symbol in adjusted:
            if abs(adjusted[symbol]) > max_position:
                logger.warning(
                    f"Capping {symbol} position from {adjusted[symbol]:.2%} "
                    f"to {max_position:.2%}"
                )
                adjusted[symbol] = max_position if adjusted[symbol] > 0 else -max_position
        
        return adjusted
    
    def get_params(self) -> Dict[str, Any]:
        """Return strategy parameters as dictionary."""
        return {
            'top_k': self.params.top_k,
            'holding_days': self.params.holding_days,
            'tp_multiplier': self.params.tp_multiplier,
            'risk_budget': self.params.risk_budget,
            'defensive_risk_budget': self.params.defensive_risk_budget
        }
