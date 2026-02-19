"""
Backtesting engine and orchestration for AuronAI.

This module provides backtesting capabilities including run management,
trade execution simulation, and performance metrics calculation.
"""

from auronai.backtesting.run_manager import RunManager, BacktestRun
from auronai.backtesting.backtest_config import (
    BacktestConfig,
    BacktestResult,
    Trade
)
from auronai.backtesting.backtest_runner import BacktestRunner
from auronai.backtesting.monte_carlo import MonteCarloResult, MonteCarloSimulator

__all__ = [
    'RunManager',
    'BacktestRun',
    'BacktestConfig',
    'BacktestResult',
    'Trade',
    'BacktestRunner',
    'MonteCarloSimulator',
    'MonteCarloResult',
]
