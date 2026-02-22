"""
Turtle Trading strategy — Donchian channel breakout.

Classic trend-following strategy based on the original Turtle Traders system.
Enters on 20-day high breakouts and exits on 10-day low breaks.
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
    stop_price: float  # Trailing stop at 10-day low


class TurtleTradingStrategy(BaseStrategy):
    """
    Turtle Trading strategy — Donchian channel breakout.

    Type: Trend following | Regime: BULL
    Timeframe: Swing/position (holding_days=20)
    Expected win rate: ~40% (wins are large, losses are small)
    Max drawdown: ~15-20%

    Entry: Close > 20-day high (Donchian breakout)
    Exit: Close < 10-day low OR time exit
    Position sizing: risk_budget / top_k, ATR-based sizing

    Required columns: Close, High, Low, atr, high_20, low_10
    """

    def __init__(self, params: StrategyParams) -> None:
        super().__init__(params)
        self.open_positions: dict[str, OpenPosition] = {}

    @property
    def name(self) -> str:
        return "Turtle Trading"

    @property
    def description(self) -> str:
        return "Donchian channel breakout trend-following strategy"

    def generate_signals(
        self,
        features: pd.DataFrame,
        regime: MarketRegime,
        current_date: datetime,
    ) -> dict[str, float]:
        if regime != MarketRegime.BULL:
            return {}

        required = ["Close", "High", "Low", "atr", "high_20", "low_10"]
        if any(col not in features.columns for col in required):
            return {}

        available_slots = self.params.top_k - len(self.open_positions)
        if available_slots <= 0:
            return {}

        try:
            if features.empty:
                return {}

            open_symbols = set(self.open_positions.keys())
            candidates = features[
                (features["Close"] > features["high_20"])
                & (~features["atr"].isna())
                & (~features.index.isin(open_symbols))
            ].copy()

            if candidates.empty:
                return {}

            # Rank by breakout strength: (Close - high_20) / atr
            candidates["breakout_strength"] = (
                candidates["Close"] - candidates["high_20"]
            ) / candidates["atr"]
            candidates = candidates.sort_values("breakout_strength", ascending=False)

            selected = candidates.head(available_slots)
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

            # Exit: Close < 10-day low
            if "low_10" in row and not pd.isna(row["low_10"]):
                if close_val < float(row["low_10"]):
                    exit_info[symbol] = {
                        "exit_price": close_val,
                        "reason": "ChannelExit",
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
            stop_price = (
                float(row["low_10"])
                if "low_10" in row and not pd.isna(row["low_10"])
                else entry_price * 0.95
            )

            self.open_positions[symbol] = OpenPosition(
                symbol=symbol,
                entry_date=datetime.now(),
                entry_price=entry_price,
                shares=0.0,
                stop_price=stop_price,
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
