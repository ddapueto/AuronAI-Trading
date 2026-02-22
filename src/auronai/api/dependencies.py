"""Shared FastAPI dependencies — singletons for broker, agent, risk manager."""

from functools import lru_cache

from auronai.agents.trading_agent import TradingAgent
from auronai.brokers.paper_broker import PaperBroker
from auronai.core.models import TradingConfig
from auronai.data.symbol_universe import SYMBOL_UNIVERSE
from auronai.risk.risk_manager import RiskManager

_broker: PaperBroker | None = None
_agent: TradingAgent | None = None


async def get_broker() -> PaperBroker:
    """Return the singleton PaperBroker (connected)."""
    global _broker
    if _broker is None:
        config = TradingConfig.from_env()
        _broker = PaperBroker(initial_cash=config.portfolio_value)
        await _broker.connect()
    return _broker


def get_agent() -> TradingAgent:
    """Return the singleton TradingAgent in analysis mode."""
    global _agent
    if _agent is None:
        _agent = TradingAgent(mode="analysis")
    return _agent


@lru_cache
def get_config() -> TradingConfig:
    """Return TradingConfig from environment."""
    return TradingConfig.from_env()


def get_risk_manager(portfolio_value: float | None = None) -> RiskManager:
    """Build a RiskManager for the given (or default) portfolio value."""
    config = get_config()
    value = portfolio_value or config.portfolio_value
    return RiskManager(
        portfolio_value=value,
        max_risk_per_trade=config.max_risk_per_trade,
        max_position_size=config.max_position_size,
        max_portfolio_exposure=config.max_portfolio_exposure,
    )


def get_universe() -> dict[str, list[str]]:
    """Return the symbol universe dictionary."""
    return SYMBOL_UNIVERSE
