"""Tests for AlpacaBroker with mocked alpaca-py SDK."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from auronai.brokers.alpaca_broker import AlpacaBroker
from auronai.brokers.models import OrderSide, OrderStatus


@pytest.fixture
def broker() -> AlpacaBroker:
    return AlpacaBroker(api_key="test-key", secret_key="test-secret", paper=True)


def _mock_alpaca_account() -> SimpleNamespace:
    return SimpleNamespace(
        id="test-account-id",
        currency="USD",
        cash="50000.00",
        equity="52000.00",
        buying_power="100000.00",
        portfolio_value="52000.00",
        daytrade_count="1",
        multiplier="2",
    )


def _mock_alpaca_order(**overrides: object) -> SimpleNamespace:
    defaults = {
        "id": "order-123",
        "symbol": "AAPL",
        "side": "buy",
        "type": "market",
        "qty": "10",
        "status": "filled",
        "limit_price": None,
        "stop_price": None,
        "time_in_force": "day",
        "filled_qty": "10",
        "filled_avg_price": "150.50",
        "created_at": datetime(2026, 1, 1),
        "updated_at": datetime(2026, 1, 1),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _mock_alpaca_position() -> SimpleNamespace:
    return SimpleNamespace(
        symbol="AAPL",
        qty="10",
        avg_entry_price="150.00",
        current_price="155.00",
        market_value="1550.00",
        unrealized_pl="50.00",
        unrealized_plpc="0.0333",
    )


class TestAlpacaBrokerProperties:
    def test_name(self, broker: AlpacaBroker) -> None:
        assert broker.name == "alpaca"

    def test_supports_fractional(self, broker: AlpacaBroker) -> None:
        assert broker.supports_fractional is True

    def test_supports_short_selling(self, broker: AlpacaBroker) -> None:
        assert broker.supports_short_selling is True

    def test_not_connected_initially(self, broker: AlpacaBroker) -> None:
        assert broker.is_connected is False


class TestAlpacaBrokerConnection:
    @pytest.mark.asyncio
    async def test_connect(self, broker: AlpacaBroker) -> None:
        mock_trading_client = MagicMock()
        with patch("alpaca.trading.client.TradingClient", return_value=mock_trading_client):
            await broker.connect()
            assert broker.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_without_keys_raises(self) -> None:
        broker = AlpacaBroker(api_key="", secret_key="", paper=True)
        with pytest.raises(ValueError, match="API keys required"):
            await broker.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self, broker: AlpacaBroker) -> None:
        broker._connected = True
        broker._trading_client = MagicMock()
        await broker.disconnect()
        assert broker.is_connected is False
        assert broker._trading_client is None


class TestAlpacaBrokerAccount:
    @pytest.mark.asyncio
    async def test_get_account(self, broker: AlpacaBroker) -> None:
        broker._connected = True
        broker._trading_client = MagicMock()
        broker._trading_client.get_account.return_value = _mock_alpaca_account()

        account = await broker.get_account()
        assert account.broker == "alpaca"
        assert account.equity == 52000.0
        assert account.balance == 50000.0
        assert account.day_trades_remaining == 2  # 3 - 1
        assert account.leverage == 2.0
        assert account.is_paper is True

    @pytest.mark.asyncio
    async def test_get_account_not_connected_raises(self, broker: AlpacaBroker) -> None:
        with pytest.raises(RuntimeError, match="not connected"):
            await broker.get_account()


class TestAlpacaBrokerOrders:
    @pytest.mark.asyncio
    async def test_place_market_order(self, broker: AlpacaBroker) -> None:
        broker._connected = True
        broker._trading_client = MagicMock()
        broker._trading_client.submit_order.return_value = _mock_alpaca_order()

        with patch.dict("sys.modules", {
            "alpaca.trading.requests": MagicMock(),
            "alpaca.trading.enums": MagicMock(),
        }):
            order = await broker.place_order("AAPL", OrderSide.BUY, 10.0)
            assert order.symbol == "AAPL"
            assert order.status == OrderStatus.FILLED
            assert order.filled_quantity == 10.0

    @pytest.mark.asyncio
    async def test_get_order(self, broker: AlpacaBroker) -> None:
        broker._connected = True
        broker._trading_client = MagicMock()
        broker._trading_client.get_order_by_id.return_value = _mock_alpaca_order()

        order = await broker.get_order("order-123")
        assert order.order_id == "order-123"

    @pytest.mark.asyncio
    async def test_cancel_order(self, broker: AlpacaBroker) -> None:
        broker._connected = True
        broker._trading_client = MagicMock()
        broker._trading_client.get_order_by_id.return_value = _mock_alpaca_order(
            status="canceled"
        )

        order = await broker.cancel_order("order-123")
        assert order.status == OrderStatus.CANCELLED


class TestAlpacaBrokerPositions:
    @pytest.mark.asyncio
    async def test_get_positions(self, broker: AlpacaBroker) -> None:
        broker._connected = True
        broker._trading_client = MagicMock()
        broker._trading_client.get_all_positions.return_value = [_mock_alpaca_position()]

        positions = await broker.get_positions()
        assert len(positions) == 1
        assert positions[0].symbol == "AAPL"
        assert positions[0].quantity == 10.0
        assert positions[0].entry_price == 150.0

    @pytest.mark.asyncio
    async def test_get_position_none(self, broker: AlpacaBroker) -> None:
        broker._connected = True
        broker._trading_client = MagicMock()
        broker._trading_client.get_open_position.side_effect = Exception("Not found")

        pos = await broker.get_position("FAKE")
        assert pos is None
