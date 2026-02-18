"""
Defensive strategy for neutral/choppy markets.

This strategy focuses on low volatility stocks with reduced exposure
during NEUTRAL market regimes.
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


class NeutralStrategy(BaseStrategy):
    """
    Defensive strategy for NEUTRAL regime.
    
    Approach:
    - Reduce exposure to defensive_risk_budget (default 5% vs 20% in bull)
    - Focus on low volatility stocks (low ATR)
    - Positive but modest momentum (positive relative strength)
    
    Selection Criteria:
    - Low ATR (below median volatility)
    - Positive relative strength
    - Stable price action
    
    **Validates: Requirements FR-7**
    """
    
    @property
    def name(self) -> str:
        """Strategy name for display."""
        return "Neutral/Defensive"
    
    @property
    def description(self) -> str:
        """Strategy description for UI."""
        return "Defensive strategy for choppy markets"
    
    def generate_signals(
        self,
        features: pd.DataFrame,
        regime: MarketRegime,
        current_date: datetime
    ) -> Dict[str, float]:
        """
        Select low volatility symbols with positive momentum.
        
        Args:
            features: DataFrame with OHLCV + indicators for all symbols
            regime: Current market regime
            current_date: Current simulation date
        
        Returns:
            Dictionary mapping symbol -> target weight
            Empty dict if not in NEUTRAL regime
        """
        # Only trade in neutral regime
        if regime != MarketRegime.NEUTRAL:
            logger.debug(f"Skipping signals - regime is {regime.value}, need NEUTRAL")
            return {}
        
        # Filter: Low volatility and positive RS
        try:
            # Calculate median ATR for volatility threshold
            median_atr = features['atr'].median()
            
            candidates = features[
                (features['atr'] < median_atr) &
                (features['relative_strength'] > 0) &
                (~features['atr'].isna()) &
                (~features['relative_strength'].isna())
            ].copy()
            
            if len(candidates) == 0:
                logger.debug("No candidates passed filters")
                return {}
            
            # Sort by relative strength (prefer stable positive momentum)
            candidates = candidates.sort_values('relative_strength', ascending=False)
            
            # Select top K
            selected = candidates.head(self.params.top_k)
            
            # Equal weight distribution
            weight = 1.0 / len(selected) if len(selected) > 0 else 0.0
            
            signals = {symbol: weight for symbol in selected.index}
            
            logger.info(
                f"Generated {len(signals)} defensive signals: "
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
        
        Uses defensive_risk_budget (default 5%) instead of regular risk_budget.
        
        Constraints:
        - Maximum total exposure = defensive_risk_budget (default 5%)
        - Maximum position size = defensive_risk_budget / top_k
        
        Args:
            target_weights: Raw weights from generate_signals()
            features: Current market features
            current_portfolio: Current positions
        
        Returns:
            Adjusted weights after risk constraints
        """
        if not target_weights:
            return {}
        
        # Use defensive risk budget for neutral regime
        risk_budget = self.params.defensive_risk_budget
        
        # Calculate total target exposure
        total_weight = sum(abs(w) for w in target_weights.values())
        
        # Scale down if exceeds defensive risk budget
        if total_weight > risk_budget:
            scale_factor = risk_budget / total_weight
            adjusted = {
                symbol: weight * scale_factor
                for symbol, weight in target_weights.items()
            }
            logger.info(
                f"Scaled weights by {scale_factor:.2f} to respect "
                f"defensive_risk_budget={risk_budget}"
            )
        else:
            adjusted = target_weights.copy()
        
        # Ensure no single position exceeds max
        max_position = risk_budget / self.params.top_k
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
