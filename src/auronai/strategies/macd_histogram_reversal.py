"""
MACD Histogram Reversal strategy.

Momentum strategy that enters when the MACD histogram turns positive
with EMA trend confirmation.
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


class MACDHistogramReversalStrategy(BaseStrategy):
    """
    MACD Histogram Reversal strategy.

    Type: Momentum | Regime: BULL
    Timeframe: Swing (holding_days=10)
    Expected win rate: ~50-55%
    Max drawdown: ~10-15%

    Entry: macd_histogram > 0 AND ema_20 > ema_50 (trend confirmed)
    Ranking: By relative_strength (strongest first)

    Required columns: Close, macd_histogram, ema_20, ema_50,
                      atr, relative_strength
    """

    @property
    def name(self) -> str:
        return "MACD Histogram Reversal"

    @property
    def description(self) -> str:
        return "Momentum entry on MACD histogram reversal with trend filter"

    def generate_signals(
        self,
        features: pd.DataFrame,
        regime: MarketRegime,
        current_date: datetime,
    ) -> dict[str, float]:
        if regime != MarketRegime.BULL:
            return {}

        required = [
            "Close",
            "macd_histogram",
            "ema_20",
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
                (features["macd_histogram"] > 0)
                & (features["ema_20"] > features["ema_50"])
                & (~features["macd_histogram"].isna())
                & (~features["ema_20"].isna())
                & (~features["ema_50"].isna())
                & (~features["relative_strength"].isna())
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
