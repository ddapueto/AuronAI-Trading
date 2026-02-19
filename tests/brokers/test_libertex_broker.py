"""Tests for LibertexBroker with mocked MetaTrader5."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from auronai.brokers.libertex_broker import LibertexBroker
from auronai.brokers.models import AssetType, OrderSide, OrderStatus


@pytest.fixture
def broker() -> LibertexBroker:
    return LibertexBroker(login=12345, password="test", server="Test-Demo")


def _mock_mt5() -> MagicMock:
    """Create a mock MT5 module with common constants."""
    mt5 = MagicMock()
    mt5.initialize.return_value = True
    mt5.login.return_value = True
    mt5.TIMEFRAME_D1 = 16408
    mt5.TIMEFRAME_H1 = 16385
    mt5.ORDER_TYPE_BUY = 0
    mt5.ORDER_TYPE_SELL = 1
    mt5.ORDER_TYPE_BUY_LIMIT = 2
    mt5.ORDER_TYPE_SELL_LIMIT = 3
    mt5.ORDER_TYPE_BUY_STOP = 4
    mt5.ORDER_TYPE_SELL_STOP = 5
    mt5.TRADE_ACTION_DEAL = 1
    mt5.TRADE_ACTION_PENDING = 5
    mt5.TRADE_ACTION_REMOVE = 8
    mt5.ORDER_TIME_GTC = 1
    mt5.ORDER_FILLING_IOC = 2
    mt5.TRADE_RETCODE_DONE = 10009
    return mt5


def _mock_account_info() -> SimpleNamespace:
    return SimpleNamespace(
        login=12345,
        currency="USD",
        balance=50000.0,
        equity=51000.0,
        margin_free=45000.0,
        leverage=100,
        trade_mode=1,  # demo
    )


def _mock_tick() -> SimpleNamespace:
    return SimpleNamespace(
        bid=150.0,
        ask=150.10,
        last=150.05,
        volume=1000,
        time=1700000000,
    )


def _mock_position() -> SimpleNamespace:
    return SimpleNamespace(
        symbol="EURUSD",
        volume=0.1,
        type=0,  # buy
        price_open=1.0850,
        price_current=1.0900,
        profit=50.0,
    )


class TestLibertexBrokerProperties:
    def test_name(self, broker: LibertexBroker) -> None:
        assert broker.name == "libertex"

    def test_supports_fractional(self, broker: LibertexBroker) -> None:
        assert broker.supports_fractional is True

    def test_supports_short_selling(self, broker: LibertexBroker) -> None:
        assert broker.supports_short_selling is True

    def test_not_connected_initially(self, broker: LibertexBroker) -> None:
        assert broker.is_connected is False


class TestLibertexBrokerConnection:
    @pytest.mark.asyncio
    async def test_connect(self, broker: LibertexBroker) -> None:
        mt5 = _mock_mt5()
        with patch.dict("sys.modules", {"MetaTrader5": mt5}):
            broker._mt5 = None
            broker._mt5 = mt5
            await broker.connect()
            assert broker.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_init_fails(self, broker: LibertexBroker) -> None:
        mt5 = _mock_mt5()
        mt5.initialize.return_value = False
        mt5.last_error.return_value = ("error", -1)
        broker._mt5 = mt5
        with pytest.raises(ConnectionError, match="initialize failed"):
            await broker.connect()

    @pytest.mark.asyncio
    async def test_connect_login_fails(self, broker: LibertexBroker) -> None:
        mt5 = _mock_mt5()
        mt5.login.return_value = False
        broker._mt5 = mt5
        with pytest.raises(ConnectionError, match="login failed"):
            await broker.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self, broker: LibertexBroker) -> None:
        mt5 = _mock_mt5()
        broker._mt5 = mt5
        broker._connected = True
        await broker.disconnect()
        assert broker.is_connected is False
        mt5.shutdown.assert_called_once()


class TestLibertexBrokerAccount:
    @pytest.mark.asyncio
    async def test_get_account(self, broker: LibertexBroker) -> None:
        mt5 = _mock_mt5()
        mt5.account_info.return_value = _mock_account_info()
        broker._mt5 = mt5
        broker._connected = True

        account = await broker.get_account()
        assert account.broker == "libertex"
        assert account.balance == 50000.0
        assert account.equity == 51000.0
        assert account.leverage == 100.0
        assert account.day_trades_remaining is None  # No PDT for CFDs
        assert account.is_paper is True  # demo mode

    @pytest.mark.asyncio
    async def test_get_account_not_connected(self, broker: LibertexBroker) -> None:
        with pytest.raises(RuntimeError, match="not connected"):
            await broker.get_account()


class TestLibertexBrokerQuote:
    @pytest.mark.asyncio
    async def test_get_quote(self, broker: LibertexBroker) -> None:
        mt5 = _mock_mt5()
        mt5.symbol_info_tick.return_value = _mock_tick()
        broker._mt5 = mt5
        broker._connected = True

        quote = await broker.get_quote("EURUSD")
        assert quote.symbol == "EURUSD"
        assert quote.bid == 150.0
        assert quote.ask == 150.10
        assert quote.volume == 1000

    @pytest.mark.asyncio
    async def test_get_quote_no_data(self, broker: LibertexBroker) -> None:
        mt5 = _mock_mt5()
        mt5.symbol_info_tick.return_value = None
        broker._mt5 = mt5
        broker._connected = True

        with pytest.raises(ValueError, match="No tick data"):
            await broker.get_quote("INVALID")


class TestLibertexBrokerOrders:
    @pytest.mark.asyncio
    async def test_place_market_order(self, broker: LibertexBroker) -> None:
        mt5 = _mock_mt5()
        mt5.symbol_info_tick.return_value = _mock_tick()
        mt5.order_send.return_value = SimpleNamespace(
            retcode=10009,
            order=100001,
            volume=0.1,
            price=150.10,
            deal=200001,
            comment="done",
        )
        broker._mt5 = mt5
        broker._connected = True

        order = await broker.place_order("EURUSD", OrderSide.BUY, 0.1)
        assert order.status == OrderStatus.FILLED
        assert order.filled_quantity == 0.1
        assert order.broker_order_id == "200001"

    @pytest.mark.asyncio
    async def test_place_order_rejected(self, broker: LibertexBroker) -> None:
        mt5 = _mock_mt5()
        mt5.symbol_info_tick.return_value = _mock_tick()
        mt5.order_send.return_value = SimpleNamespace(
            retcode=10006,
            order=0,
            volume=0,
            price=0,
            deal=0,
            comment="Rejected",
        )
        broker._mt5 = mt5
        broker._connected = True

        order = await broker.place_order("EURUSD", OrderSide.BUY, 0.1)
        assert order.status == OrderStatus.REJECTED


class TestLibertexBrokerPositions:
    @pytest.mark.asyncio
    async def test_get_positions(self, broker: LibertexBroker) -> None:
        mt5 = _mock_mt5()
        mt5.positions_get.return_value = [_mock_position()]
        broker._mt5 = mt5
        broker._connected = True

        positions = await broker.get_positions()
        assert len(positions) == 1
        assert positions[0].symbol == "EURUSD"
        assert positions[0].quantity == 0.1
        assert positions[0].side == OrderSide.BUY
        assert positions[0].asset_type == AssetType.CFD

    @pytest.mark.asyncio
    async def test_get_position_none(self, broker: LibertexBroker) -> None:
        mt5 = _mock_mt5()
        mt5.positions_get.return_value = None
        broker._mt5 = mt5
        broker._connected = True

        pos = await broker.get_position("FAKE")
        assert pos is None

    @pytest.mark.asyncio
    async def test_no_positions(self, broker: LibertexBroker) -> None:
        mt5 = _mock_mt5()
        mt5.positions_get.return_value = None
        broker._mt5 = mt5
        broker._connected = True

        positions = await broker.get_positions()
        assert positions == []
