"""
Bollinger Bands Mean Reversion strategy.

Buys when price touches the lower Bollinger Band with RSI confirmation
and targets the middle band (mean reversion).
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
    tp_price: float  # Take profit at bb_middle
    sl_price: float  # Stop loss below bb_lower


class BollingerMeanReversionStrategy(BaseStrategy):
    """
    Bollinger Bands Mean Reversion strategy.

    Type: Mean reversion | Regime: BULL or NEUTRAL
    Timeframe: Swing (holding_days=10)
    Expected win rate: ~60-65%
    Max drawdown: ~8-12%

    Entry: Close <= bb_lower AND rsi < 30 AND Close > ema_200
    TP: bb_middle (mean reversion target)
    SL: ATR below bb_lower

    Required columns: Close, High, bb_lower, bb_upper, bb_middle,
                      rsi, ema_200, atr
    """

    def __init__(self, params: StrategyParams) -> None:
        super().__init__(params)
        self.open_positions: dict[str, OpenPosition] = {}

    @property
    def name(self) -> str:
        return "Bollinger Mean Reversion"

    @property
    def description(self) -> str:
        return "Mean reversion strategy using Bollinger Bands"

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
            "High",
            "bb_lower",
            "bb_upper",
            "bb_middle",
            "rsi",
            "ema_200",
            "atr",
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
            candidates = features[
                (features["Close"] <= features["bb_lower"])
                & (features["rsi"] < 30)
                & (features["Close"] > features["ema_200"])
                & (~features["bb_lower"].isna())
                & (~features["rsi"].isna())
                & (~features["ema_200"].isna())
                & (~features.index.isin(open_symbols))
            ].copy()

            if candidates.empty:
                return {}

            # Rank by how oversold: lower RSI = better opportunity
            candidates = candidates.sort_values("rsi", ascending=True)

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
            high_val = float(row["High"])
            close_val = float(row["Close"])

            # Take profit: High >= bb_middle
            if "bb_middle" in row and not pd.isna(row["bb_middle"]):
                if high_val >= float(row["bb_middle"]):
                    exit_info[symbol] = {
                        "exit_price": float(row["bb_middle"]),
                        "reason": "TP",
                    }
                    del self.open_positions[symbol]
                    continue

            # Stop loss
            if close_val <= position.sl_price:
                exit_info[symbol] = {
                    "exit_price": close_val,
                    "reason": "StopLoss",
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
            atr_val = (
                float(row["atr"])
                if "atr" in row and not pd.isna(row["atr"])
                else entry_price * 0.02
            )
            bb_lower = (
                float(row["bb_lower"])
                if "bb_lower" in row and not pd.isna(row["bb_lower"])
                else entry_price
            )
            bb_middle = (
                float(row["bb_middle"])
                if "bb_middle" in row and not pd.isna(row["bb_middle"])
                else entry_price * 1.02
            )
            sl_price = bb_lower - atr_val

            self.open_positions[symbol] = OpenPosition(
                symbol=symbol,
                entry_date=datetime.now(),
                entry_price=entry_price,
                shares=0.0,
                tp_price=bb_middle,
                sl_price=sl_price,
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
