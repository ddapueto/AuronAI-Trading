"""Tests for PaperBroker — local trading simulator."""

import pytest

from auronai.brokers.models import (
    OrderSide,
    OrderStatus,
    OrderType,
)
from auronai.brokers.paper_broker import PaperBroker


@pytest.fixture
def broker() -> PaperBroker:
    return PaperBroker(initial_cash=10_000.0, commission=0.0, slippage=0.0)


class TestPaperBrokerProperties:
    def test_name(self, broker: PaperBroker) -> None:
        assert broker.name == "paper"

    def test_not_connected_initially(self, broker: PaperBroker) -> None:
        assert broker.is_connected is False

    def test_supports_fractional(self, broker: PaperBroker) -> None:
        assert broker.supports_fractional is True

    def test_no_short_selling(self, broker: PaperBroker) -> None:
        assert broker.supports_short_selling is False

    def test_supports_paper_trading(self, broker: PaperBroker) -> None:
        assert broker.supports_paper_trading is True


class TestPaperBrokerConnection:
    @pytest.mark.asyncio
    async def test_connect(self, broker: PaperBroker) -> None:
        await broker.connect()
        assert broker.is_connected is True

    @pytest.mark.asyncio
    async def test_disconnect(self, broker: PaperBroker) -> None:
        await broker.connect()
        await broker.disconnect()
        assert broker.is_connected is False


class TestPaperBrokerAccount:
    @pytest.mark.asyncio
    async def test_initial_account(self, broker: PaperBroker) -> None:
        await broker.connect()
        account = await broker.get_account()
        assert account.balance == 10_000.0
        assert account.equity == 10_000.0
        assert account.buying_power == 10_000.0
        assert account.is_paper is True
        assert account.broker == "paper"
        assert account.day_trades_remaining is None
        assert account.leverage == 1.0


class TestPaperBrokerOrders:
    @pytest.mark.asyncio
    async def test_buy_market_order(self, broker: PaperBroker) -> None:
        await broker.connect()
        # Manually set a known price via _positions bypass
        order = await broker.place_order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=1.0,
            order_type=OrderType.MARKET,
        )
        assert order.status == OrderStatus.FILLED
        assert order.filled_quantity == 1.0
        assert order.filled_avg_price > 0
        assert order.side == OrderSide.BUY

    @pytest.mark.asyncio
    async def test_buy_creates_position(self, broker: PaperBroker) -> None:
        await broker.connect()
        await broker.place_order("AAPL", OrderSide.BUY, 2.0)
        positions = await broker.get_positions()
        assert len(positions) == 1
        assert positions[0].symbol == "AAPL"
        assert positions[0].quantity == 2.0

    @pytest.mark.asyncio
    async def test_sell_removes_position(self, broker: PaperBroker) -> None:
        await broker.connect()
        await broker.place_order("AAPL", OrderSide.BUY, 2.0)
        await broker.place_order("AAPL", OrderSide.SELL, 2.0)
        positions = await broker.get_positions()
        assert len(positions) == 0

    @pytest.mark.asyncio
    async def test_partial_sell(self, broker: PaperBroker) -> None:
        await broker.connect()
        await broker.place_order("AAPL", OrderSide.BUY, 5.0)
        await broker.place_order("AAPL", OrderSide.SELL, 2.0)
        pos = await broker.get_position("AAPL")
        assert pos is not None
        assert pos.quantity == 3.0

    @pytest.mark.asyncio
    async def test_insufficient_cash_rejected(self) -> None:
        broker = PaperBroker(initial_cash=1.0, slippage=0.0)
        await broker.connect()
        order = await broker.place_order("AAPL", OrderSide.BUY, 100.0)
        assert order.status == OrderStatus.REJECTED

    @pytest.mark.asyncio
    async def test_sell_without_position_rejected(self, broker: PaperBroker) -> None:
        await broker.connect()
        order = await broker.place_order("AAPL", OrderSide.SELL, 1.0)
        assert order.status == OrderStatus.REJECTED

    @pytest.mark.asyncio
    async def test_limit_order_stays_pending(self, broker: PaperBroker) -> None:
        await broker.connect()
        order = await broker.place_order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=1.0,
            order_type=OrderType.LIMIT,
            limit_price=100.0,
        )
        assert order.status == OrderStatus.SUBMITTED
        open_orders = await broker.get_open_orders()
        assert len(open_orders) == 1

    @pytest.mark.asyncio
    async def test_cancel_order(self, broker: PaperBroker) -> None:
        await broker.connect()
        order = await broker.place_order(
            "AAPL", OrderSide.BUY, 1.0, OrderType.LIMIT, limit_price=100.0
        )
        cancelled = await broker.cancel_order(order.order_id)
        assert cancelled.status == OrderStatus.CANCELLED
        open_orders = await broker.get_open_orders()
        assert len(open_orders) == 0

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_raises(self, broker: PaperBroker) -> None:
        await broker.connect()
        with pytest.raises(ValueError, match="not found"):
            await broker.cancel_order("fake-id")

    @pytest.mark.asyncio
    async def test_get_order(self, broker: PaperBroker) -> None:
        await broker.connect()
        order = await broker.place_order("AAPL", OrderSide.BUY, 1.0)
        fetched = await broker.get_order(order.order_id)
        assert fetched.order_id == order.order_id
        assert fetched.status == OrderStatus.FILLED

    @pytest.mark.asyncio
    async def test_get_order_nonexistent_raises(self, broker: PaperBroker) -> None:
        await broker.connect()
        with pytest.raises(ValueError, match="not found"):
            await broker.get_order("fake-id")


class TestPaperBrokerPositions:
    @pytest.mark.asyncio
    async def test_no_positions_initially(self, broker: PaperBroker) -> None:
        await broker.connect()
        positions = await broker.get_positions()
        assert positions == []

    @pytest.mark.asyncio
    async def test_get_position_none(self, broker: PaperBroker) -> None:
        await broker.connect()
        pos = await broker.get_position("AAPL")
        assert pos is None

    @pytest.mark.asyncio
    async def test_close_position(self, broker: PaperBroker) -> None:
        await broker.connect()
        await broker.place_order("AAPL", OrderSide.BUY, 3.0)
        order = await broker.close_position("AAPL")
        assert order.status == OrderStatus.FILLED
        assert order.side == OrderSide.SELL
        positions = await broker.get_positions()
        assert len(positions) == 0

    @pytest.mark.asyncio
    async def test_close_nonexistent_raises(self, broker: PaperBroker) -> None:
        await broker.connect()
        with pytest.raises(ValueError, match="No position"):
            await broker.close_position("FAKE")

    @pytest.mark.asyncio
    async def test_close_all_positions(self, broker: PaperBroker) -> None:
        await broker.connect()
        await broker.place_order("AAPL", OrderSide.BUY, 2.0)
        await broker.place_order("MSFT", OrderSide.BUY, 3.0)
        orders = await broker.close_all_positions()
        assert len(orders) == 2
        positions = await broker.get_positions()
        assert len(positions) == 0

    @pytest.mark.asyncio
    async def test_averaging_up(self, broker: PaperBroker) -> None:
        await broker.connect()
        await broker.place_order("AAPL", OrderSide.BUY, 2.0)
        await broker.place_order("AAPL", OrderSide.BUY, 3.0)
        pos = await broker.get_position("AAPL")
        assert pos is not None
        assert pos.quantity == 5.0


class TestPaperBrokerConvenience:
    @pytest.mark.asyncio
    async def test_buy_convenience(self, broker: PaperBroker) -> None:
        await broker.connect()
        order = await broker.buy("AAPL", 1.0)
        assert order.side == OrderSide.BUY
        assert order.status == OrderStatus.FILLED

    @pytest.mark.asyncio
    async def test_sell_convenience(self, broker: PaperBroker) -> None:
        await broker.connect()
        await broker.buy("AAPL", 2.0)
        order = await broker.sell("AAPL", 1.0)
        assert order.side == OrderSide.SELL
        assert order.status == OrderStatus.FILLED


class TestPaperBrokerCashTracking:
    @pytest.mark.asyncio
    async def test_cash_decreases_on_buy(self, broker: PaperBroker) -> None:
        await broker.connect()
        await broker.buy("AAPL", 1.0)
        account = await broker.get_account()
        assert account.cash < 10_000.0

    @pytest.mark.asyncio
    async def test_cash_increases_on_sell(self, broker: PaperBroker) -> None:
        await broker.connect()
        await broker.buy("AAPL", 1.0)
        cash_after_buy = (await broker.get_account()).cash
        await broker.sell("AAPL", 1.0)
        cash_after_sell = (await broker.get_account()).cash
        assert cash_after_sell > cash_after_buy
