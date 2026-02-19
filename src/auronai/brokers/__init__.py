"""Broker abstraction layer for AuronAI Trading."""

from auronai.brokers.base_broker import BaseBroker
from auronai.brokers.models import (
    AccountInfo,
    AssetType,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    Quote,
    TimeInForce,
)
from auronai.brokers.paper_broker import PaperBroker

__all__ = [
    "AlpacaBroker",
    "AssetType",
    "BaseBroker",
    "LibertexBroker",
    "PaperBroker",
    "AccountInfo",
    "Order",
    "OrderSide",
    "OrderStatus",
    "OrderType",
    "Position",
    "Quote",
    "TimeInForce",
]


def AlpacaBroker(**kwargs: object) -> "BaseBroker":  # type: ignore[return]
    """Lazy-loaded Alpaca broker (requires alpaca-py)."""
    from auronai.brokers.alpaca_broker import AlpacaBroker as _AlpacaBroker

    return _AlpacaBroker(**kwargs)


def LibertexBroker(**kwargs: object) -> "BaseBroker":  # type: ignore[return]
    """Lazy-loaded Libertex broker (requires MetaTrader5, Windows only)."""
    from auronai.brokers.libertex_broker import LibertexBroker as _LibertexBroker

    return _LibertexBroker(**kwargs)
