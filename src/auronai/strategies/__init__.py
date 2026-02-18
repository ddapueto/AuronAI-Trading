"""
Strategy plugin system for AuronAI.

This module provides the base interfaces and implementations for
trading strategies with regime-aware signal generation.
"""

from auronai.strategies.base_strategy import (
    BaseStrategy,
    MarketRegime,
    StrategyParams
)
from auronai.strategies.regime_engine import RegimeEngine
from auronai.strategies.long_momentum import LongMomentumStrategy
from auronai.strategies.short_momentum import ShortMomentumStrategy
from auronai.strategies.neutral_strategy import NeutralStrategy
from auronai.strategies.swing_tp import SwingTPStrategy

__all__ = [
    'BaseStrategy',
    'MarketRegime',
    'StrategyParams',
    'RegimeEngine',
    'LongMomentumStrategy',
    'ShortMomentumStrategy',
    'NeutralStrategy',
    'SwingTPStrategy'
]
