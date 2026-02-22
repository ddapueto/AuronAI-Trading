"""
Sector Rotation strategy — momentum-based sector/symbol selection.

Selects top symbols by relative strength with trend confirmation
(ema_50 > ema_200) for monthly rebalance.
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


class SectorRotationStrategy(BaseStrategy):
    """
    Sector Rotation strategy — momentum-based selection.

    Type: Momentum | Regime: BULL or NEUTRAL
    Timeframe: Position (holding_days=21 for monthly rebalance)
    Expected win rate: ~50-55%
    Max drawdown: ~15-20%

    Logic: Select top K symbols by relative_strength where
           ema_50 > ema_200 (confirmed uptrend). Monthly rebalance.

    Required columns: Close, relative_strength, ema_50, ema_200
    """

    @property
    def name(self) -> str:
        return "Sector Rotation"

    @property
    def description(self) -> str:
        return "Momentum-based sector rotation with trend confirmation"

    def generate_signals(
        self,
        features: pd.DataFrame,
        regime: MarketRegime,
        current_date: datetime,
    ) -> dict[str, float]:
        if regime not in (MarketRegime.BULL, MarketRegime.NEUTRAL):
            return {}

        required = ["Close", "relative_strength", "ema_50", "ema_200"]
        if any(col not in features.columns for col in required):
            return {}

        try:
            if features.empty:
                return {}

            candidates = features[
                (features["ema_50"] > features["ema_200"])
                & (~features["relative_strength"].isna())
                & (~features["ema_50"].isna())
                & (~features["ema_200"].isna())
            ].copy()

            if candidates.empty:
                return {}

            candidates = candidates.sort_values("relative_strength", ascending=False)

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
