"""Shared fixtures for API tests."""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Ensure no API keys are required during tests
os.environ.pop("AURONAI_API_KEYS", None)

from auronai.api import dependencies as deps
from auronai.api.main import app
from auronai.brokers.models import (
    AccountInfo,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
)


def _make_account(cash: float = 10_000.0) -> AccountInfo:
    equity = cash
    return AccountInfo(
        account_id="paper-test",
        broker="paper",
        currency="USD",
        balance=cash,
        equity=equity,
        buying_power=cash,
        cash=cash,
        portfolio_value=equity,
        day_trades_remaining=None,
        leverage=1.0,
        is_paper=True,
    )


def _make_position(
    symbol: str = "AAPL",
    qty: float = 10,
    entry: float = 150.0,
    current: float = 155.0,
) -> Position:
    mv = qty * current
    pnl = (current - entry) * qty
    return Position(
        symbol=symbol,
        quantity=qty,
        side=OrderSide.BUY,
        entry_price=entry,
        current_price=current,
        market_value=mv,
        unrealized_pnl=pnl,
        unrealized_pnl_pct=(current - entry) / entry,
    )


def _make_order(
    symbol: str = "AAPL",
    side: OrderSide = OrderSide.BUY,
    qty: float = 10,
    status: OrderStatus = OrderStatus.FILLED,
    price: float = 150.0,
) -> Order:
    return Order(
        order_id="test-001",
        symbol=symbol,
        side=side,
        order_type=OrderType.MARKET,
        quantity=qty,
        status=status,
        filled_quantity=qty if status == OrderStatus.FILLED else 0,
        filled_avg_price=price if status == OrderStatus.FILLED else 0,
    )


@pytest.fixture()
def mock_broker():
    """Create a mock PaperBroker with sensible defaults."""
    broker = AsyncMock()
    broker.name = "paper"
    broker.is_connected = True
    broker.get_account = AsyncMock(return_value=_make_account())
    broker.get_positions = AsyncMock(return_value=[])
    broker.get_open_orders = AsyncMock(return_value=[])
    broker.close_position = AsyncMock(return_value=_make_order())
    broker.close_all_positions = AsyncMock(return_value=[])
    broker.cancel_order = AsyncMock(return_value=_make_order(status=OrderStatus.CANCELLED))
    broker._orders = {}
    broker.disconnect = AsyncMock()
    return broker


@pytest.fixture()
def mock_agent():
    """Create a mock TradingAgent."""
    agent = MagicMock()
    agent.analyze_symbol.return_value = {
        "current_price": 150.0,
        "signal": {
            "action": "BUY",
            "confidence": 0.75,
            "strategy": "dual_momentum",
        },
        "indicators": {},
    }
    return agent


@pytest_asyncio.fixture()
async def client(mock_broker, mock_agent):
    """AsyncClient with mocked dependencies."""
    # Reset cached API keys so tests run without auth
    from auronai.api import middleware

    middleware._VALID_KEYS = None

    async def _get_broker():
        return mock_broker

    def _get_agent():
        return mock_agent

    app.dependency_overrides[deps.get_broker] = _get_broker
    app.dependency_overrides[deps.get_agent] = _get_agent

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    middleware._VALID_KEYS = None
