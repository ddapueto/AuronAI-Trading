"""
AuronAI - Sistema de Trading Algorítmico Profesional

Un sistema completo de trading que integra análisis técnico, risk management,
AI-powered analysis, y backtesting.
"""

from auronai.agents.trading_agent import TradingAgent
from auronai.core.models import TradingConfig

__version__ = "0.1.0"
__author__ = "AuronAI Team"

# Exportar clases principales para fácil importación
__all__ = [
    "__version__",
    "__author__",
    "TradingAgent",
    "TradingConfig",
]
