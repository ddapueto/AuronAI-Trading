"""
RSI Divergence strategy — mean reversion on RSI/MACD divergences.

Identifies situations where RSI is extreme but MACD histogram
signals momentum is reversing, creating a divergence entry opportunity.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from auronai.strategies.base_strategy import (
    BaseStrategy,
    MarketRegime,
    StrategyParams,
)
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OpenPosition:
    """Track an open position with entry details."""

    symbol: str
    entry_date: datetime
    entry_price: float
    shares: float
    direction: str  # "long" or "short"


class RSIDivergenceStrategy(BaseStrategy):
    """
    RSI Divergence strategy — mean reversion on RSI/MACD divergences.

    Type: Mean reversion | Regime: BULL or NEUTRAL
    Timeframe: Swing (holding_days=10)
    Expected win rate: ~55-60%
    Max drawdown: ~10-15%

    Bullish signal: rsi < 35 AND macd_histogram > 0
    Bearish signal: rsi > 65 AND macd_histogram < 0
    Exit: RSI normalizes (40-60 range) OR time exit

    Required columns: Close, rsi, macd_histogram, atr, relative_strength
    """

    def __init__(self, params: StrategyParams) -> None:
        super().__init__(params)
        self.open_positions: dict[str, OpenPosition] = {}

    @property
    def name(self) -> str:
        return "RSI Divergence"

    @property
    def description(self) -> str:
        return "Mean reversion on RSI/MACD histogram divergences"

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
            "rsi",
            "macd_histogram",
            "atr",
            "relative_strength",
        ]
        if any(col not in features.columns for col in required):
            return {}

        available_slots = self.params.top_k - len(self.open_positions)
        if available_slots <= 0:
            return {}

        try:
            if features.empty:
                return {}

            open_symbols = set(self.open_positions.keys())

            # Bullish divergence: oversold RSI + improving momentum
            bullish = features[
                (features["rsi"] < 35)
                & (features["macd_histogram"] > 0)
                & (~features["rsi"].isna())
                & (~features["macd_histogram"].isna())
                & (~features.index.isin(open_symbols))
            ].copy()

            if bullish.empty:
                return {}

            # Sort by most oversold (lowest RSI first = best opportunity)
            bullish = bullish.sort_values("rsi", ascending=True)

            selected = bullish.head(available_slots)
            weight = 1.0 / len(selected)
            return dict.fromkeys(selected.index, weight)

        except (KeyError, TypeError, AttributeError):
            return {}

    def _check_exits_with_data(
        self,
        features: pd.DataFrame,
        current_date: datetime,
    ) -> dict[str, dict[str, Any]]:
        """Check exit conditions for open positions."""
        exit_info: dict[str, dict[str, Any]] = {}

        for symbol, position in list(self.open_positions.items()):
            if symbol not in features.index:
                continue

            row = features.loc[symbol]
            close_val = float(row["Close"])

            # Exit: RSI normalized (40-60 range)
            if "rsi" in row and not pd.isna(row["rsi"]):
                rsi_val = float(row["rsi"])
                if 40 <= rsi_val <= 60:
                    exit_info[symbol] = {
                        "exit_price": close_val,
                        "reason": "RSINormalized",
                    }
                    del self.open_positions[symbol]
                    continue

            # Time exit
            days_held = (current_date - position.entry_date).days
            if days_held >= self.params.holding_days:
                exit_info[symbol] = {
                    "exit_price": close_val,
                    "reason": "TimeExit",
                }
                del self.open_positions[symbol]

        return exit_info

    def risk_model(
        self,
        target_weights: dict[str, float],
        features: pd.DataFrame,
        current_portfolio: dict[str, float],
    ) -> dict[str, float]:
        if not target_weights:
            return self._get_position_weights()

        for symbol in target_weights:
            if symbol in self.open_positions:
                continue
            if symbol not in features.index:
                continue

            row = features.loc[symbol]
            if "Close" not in row:
                continue

            entry_price = float(row["Close"])

            self.open_positions[symbol] = OpenPosition(
                symbol=symbol,
                entry_date=datetime.now(),
                entry_price=entry_price,
                shares=0.0,
                direction="long",
            )

        return self._get_position_weights()

    def _get_position_weights(self) -> dict[str, float]:
        if not self.open_positions:
            return {}
        weight = self.params.risk_budget / len(self.open_positions)
        max_position = self.params.risk_budget / self.params.top_k
        weight = min(weight, max_position)
        return dict.fromkeys(self.open_positions, weight)

    def set_entry_date(self, date: datetime) -> None:
        for position in self.open_positions.values():
            position.entry_date = date

    def get_params(self) -> dict[str, Any]:
        return {
            "top_k": self.params.top_k,
            "holding_days": self.params.holding_days,
            "tp_multiplier": self.params.tp_multiplier,
            "risk_budget": self.params.risk_budget,
            "defensive_risk_budget": self.params.defensive_risk_budget,
        }
