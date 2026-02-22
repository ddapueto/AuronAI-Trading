"""
Strategy plugin system for AuronAI.

This module provides the base interfaces and implementations for
trading strategies with regime-aware signal generation.
"""

from auronai.strategies.base_strategy import BaseStrategy, MarketRegime, StrategyParams
from auronai.strategies.bollinger_mean_reversion import (
    BollingerMeanReversionStrategy,
)
from auronai.strategies.golden_cross import GoldenCrossStrategy
from auronai.strategies.long_momentum import LongMomentumStrategy
from auronai.strategies.macd_histogram_reversal import (
    MACDHistogramReversalStrategy,
)
from auronai.strategies.neutral_strategy import NeutralStrategy
from auronai.strategies.pairs_trading import PairsTradingStrategy
from auronai.strategies.regime_engine import RegimeEngine
from auronai.strategies.rsi_divergence import RSIDivergenceStrategy
from auronai.strategies.sector_rotation import SectorRotationStrategy
from auronai.strategies.short_momentum import ShortMomentumStrategy
from auronai.strategies.swing_tp import SwingTPStrategy
from auronai.strategies.turtle_trading import TurtleTradingStrategy
from auronai.strategies.williams_r_strategy import WilliamsRStrategy

__all__ = [
    "BaseStrategy",
    "MarketRegime",
    "StrategyParams",
    "RegimeEngine",
    "LongMomentumStrategy",
    "ShortMomentumStrategy",
    "NeutralStrategy",
    "SwingTPStrategy",
    "TurtleTradingStrategy",
    "GoldenCrossStrategy",
    "RSIDivergenceStrategy",
    "BollingerMeanReversionStrategy",
    "PairsTradingStrategy",
    "SectorRotationStrategy",
    "MACDHistogramReversalStrategy",
    "WilliamsRStrategy",
]
