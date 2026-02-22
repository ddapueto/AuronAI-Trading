"""
Pairs Trading strategy — simplified spread trading.

Market-neutral strategy that goes long the weakest symbol
(mean reversion up) and short the strongest (mean reversion down).
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


class PairsTradingStrategy(BaseStrategy):
    """
    Pairs Trading strategy — simplified spread trading.

    Type: Market neutral | Regime: ANY
    Timeframe: Swing (holding_days=10)
    Expected win rate: ~50-55%
    Max drawdown: ~8-12%

    Logic: Long the weakest symbol by relative_strength (mean reversion up),
           short the strongest (mean reversion down).

    Required columns: Close, relative_strength, ema_20
    """

    @property
    def name(self) -> str:
        return "Pairs Trading"

    @property
    def description(self) -> str:
        return "Market-neutral spread trading on relative strength extremes"

    def generate_signals(
        self,
        features: pd.DataFrame,
        regime: MarketRegime,
        current_date: datetime,
    ) -> dict[str, float]:
        # Works in any regime (market neutral)
        required = ["Close", "relative_strength", "ema_20"]
        if any(col not in features.columns for col in required):
            return {}

        try:
            if features.empty or len(features) < 2:
                return {}

            valid = features[
                (~features["relative_strength"].isna()) & (~features["ema_20"].isna())
            ].copy()

            if len(valid) < 2:
                return {}

            sorted_df = valid.sort_values("relative_strength", ascending=True)

            # Long the weakest (bottom), short the strongest (top)
            n_pairs = min(self.params.top_k, len(sorted_df) // 2)
            if n_pairs < 1:
                return {}

            long_symbols = sorted_df.head(n_pairs)
            short_symbols = sorted_df.tail(n_pairs)

            weight = 1.0 / (2 * n_pairs)

            signals: dict[str, float] = {}
            for symbol in long_symbols.index:
                signals[symbol] = weight
            for symbol in short_symbols.index:
                signals[symbol] = -weight

            return signals

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
                adjusted[symbol] = max_pos if adjusted[symbol] > 0 else -max_pos

        return adjusted

    def get_params(self) -> dict[str, Any]:
        return {
            "top_k": self.params.top_k,
            "holding_days": self.params.holding_days,
            "tp_multiplier": self.params.tp_multiplier,
            "risk_budget": self.params.risk_budget,
            "defensive_risk_budget": self.params.defensive_risk_budget,
        }
