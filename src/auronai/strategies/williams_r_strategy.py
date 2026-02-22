"""
Williams %R strategy — oversold mean reversion.

Mean reversion strategy that buys when Williams %R indicates oversold
conditions with an uptrend filter.
"""

from datetime import datetime
from typing import Any

import pandas as pd

from auronai.strategies.base_strategy import (
    BaseStrategy,
    MarketRegime,
)
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


class WilliamsRStrategy(BaseStrategy):
    """
    Williams %R strategy — oversold mean reversion.

    Type: Mean reversion | Regime: BULL or NEUTRAL
    Timeframe: Swing (holding_days=10)
    Expected win rate: ~55-60%
    Max drawdown: ~10-12%

    Entry: williams_r < -80 (oversold) AND Close > ema_50 (uptrend)
    Exit signal: williams_r > -20 (overbought)

    Required columns: Close, williams_r, ema_50, atr, relative_strength
    """

    @property
    def name(self) -> str:
        return "Williams %R"

    @property
    def description(self) -> str:
        return "Oversold mean reversion using Williams %R with trend filter"

    def generate_signals(
        self,
        features: pd.DataFrame,
        regime: MarketRegime,
        current_date: datetime,
    ) -> dict[str, float]:
        if regime not in (MarketRegime.BULL, MarketRegime.NEUTRAL):
            return {}

        required = [
            "Close",
            "williams_r",
            "ema_50",
            "atr",
            "relative_strength",
        ]
        if any(col not in features.columns for col in required):
            return {}

        try:
            if features.empty:
                return {}

            candidates = features[
                (features["williams_r"] < -80)
                & (features["Close"] > features["ema_50"])
                & (~features["williams_r"].isna())
                & (~features["ema_50"].isna())
                & (~features["relative_strength"].isna())
            ].copy()

            if candidates.empty:
                return {}

            # Most oversold first (lowest williams_r)
            candidates = candidates.sort_values("williams_r", ascending=True)

            selected = candidates.head(self.params.top_k)
            weight = 1.0 / len(selected)
            return dict.fromkeys(selected.index, weight)

        except (KeyError, TypeError, AttributeError):
            return {}

    def risk_model(
        self,
        target_weights: dict[str, float],
        features: pd.DataFrame,
        current_portfolio: dict[str, float],
    ) -> dict[str, float]:
        if not target_weights:
            return {}

        total_weight = sum(abs(w) for w in target_weights.values())

        if total_weight > self.params.risk_budget:
            scale = self.params.risk_budget / total_weight
            adjusted = {s: w * scale for s, w in target_weights.items()}
        else:
            adjusted = target_weights.copy()

        max_pos = self.params.risk_budget / max(self.params.top_k, 1)
        for symbol in adjusted:
            if abs(adjusted[symbol]) > max_pos:
                adjusted[symbol] = max_pos

        return adjusted

    def get_params(self) -> dict[str, Any]:
        return {
            "top_k": self.params.top_k,
            "holding_days": self.params.holding_days,
            "tp_multiplier": self.params.tp_multiplier,
            "risk_budget": self.params.risk_budget,
            "defensive_risk_budget": self.params.defensive_risk_budget,
        }
