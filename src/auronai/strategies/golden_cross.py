"""
Golden Cross strategy — EMA 50/200 crossover.

Classic trend-following strategy that enters when EMA50 crosses above EMA200
(Golden Cross) and exits on the Death Cross.
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
    sl_price: float  # Stop loss: ATR × 2 below entry


class GoldenCrossStrategy(BaseStrategy):
    """
    Golden Cross strategy — EMA 50/200 crossover.

    Type: Trend following | Regime: BULL
    Timeframe: Position trading (holding_days=20)
    Expected win rate: ~45-50%
    Max drawdown: ~12-18%

    Entry: ema_50 > ema_200 AND rsi > 50 (Golden Cross state)
    Exit: ema_50 < ema_200 (Death Cross) OR time exit
    Stop Loss: ATR × 2 below entry price

    Required columns: Close, ema_50, ema_200, rsi, atr
    """

    def __init__(self, params: StrategyParams) -> None:
        super().__init__(params)
        self.open_positions: dict[str, OpenPosition] = {}

    @property
    def name(self) -> str:
        return "Golden Cross"

    @property
    def description(self) -> str:
        return "EMA 50/200 crossover trend-following strategy"

    def generate_signals(
        self,
        features: pd.DataFrame,
        regime: MarketRegime,
        current_date: datetime,
    ) -> dict[str, float]:
        if regime != MarketRegime.BULL:
            return {}

        required = ["Close", "ema_50", "ema_200", "rsi", "atr"]
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
                (features["ema_50"] > features["ema_200"])
                & (features["rsi"] > 50)
                & (~features["ema_50"].isna())
                & (~features["ema_200"].isna())
                & (~features["rsi"].isna())
                & (~features.index.isin(open_symbols))
            ].copy()

            if candidates.empty:
                return {}

            # Rank by how far ema_50 is above ema_200 (trend strength)
            candidates["trend_strength"] = (
                candidates["ema_50"] - candidates["ema_200"]
            ) / candidates["ema_200"]
            candidates = candidates.sort_values("trend_strength", ascending=False)

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

            # Exit: Death Cross (ema_50 < ema_200)
            if "ema_50" in row and "ema_200" in row:
                ema50 = float(row["ema_50"])
                ema200 = float(row["ema_200"])
                if not pd.isna(ema50) and not pd.isna(ema200) and ema50 < ema200:
                    exit_info[symbol] = {
                        "exit_price": close_val,
                        "reason": "DeathCross",
                    }
                    del self.open_positions[symbol]
                    continue

            # Stop loss: ATR × 2 below entry
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
            sl_price = entry_price - (atr_val * 2)

            self.open_positions[symbol] = OpenPosition(
                symbol=symbol,
                entry_date=datetime.now(),
                entry_price=entry_price,
                shares=0.0,
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
