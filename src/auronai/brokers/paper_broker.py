"""Paper broker — local trading simulator using yfinance for market data."""

import logging
import uuid
from collections.abc import Callable
from datetime import datetime

import pandas as pd
import yfinance as yf

from auronai.brokers.base_broker import BaseBroker
from auronai.brokers.models import (
    AccountInfo,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    Quote,
    TimeInForce,
)

logger = logging.getLogger(__name__)

_YF_TIMEFRAME_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
    "1d": "1d",
    "1wk": "1wk",
}

_YF_PERIOD_FOR_TIMEFRAME = {
    "1m": "7d",
    "5m": "60d",
    "15m": "60d",
    "1h": "730d",
    "1d": "max",
    "1wk": "max",
}


class PaperBroker(BaseBroker):
    """
    Local paper trading simulator.

    Simulates order fills at market price using yfinance data.
    No external broker connection required.

    Example::

        broker = PaperBroker(initial_cash=10_000.0)
        await broker.connect()
        order = await broker.buy("AAPL", 5)
        positions = await broker.get_positions()
        await broker.disconnect()
    """

    def __init__(
        self,
        initial_cash: float = 10_000.0,
        commission: float = 0.0,
        slippage: float = 0.001,
    ) -> None:
        self._initial_cash = initial_cash
        self._cash = initial_cash
        self._commission = commission
        self._slippage = slippage
        self._connected = False
        self._positions: dict[str, Position] = {}
        self._orders: dict[str, Order] = {}
        self._open_orders: dict[str, Order] = {}

    # --- Properties ---

    @property
    def name(self) -> str:
        return "paper"

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def supports_fractional(self) -> bool:
        return True

    @property
    def supports_short_selling(self) -> bool:
        return False

    # --- Connection ---

    async def connect(self) -> None:
        self._connected = True
        logger.info("PaperBroker connected (cash=%.2f)", self._cash)

    async def disconnect(self) -> None:
        self._connected = False
        logger.info("PaperBroker disconnected")

    # --- Account ---

    async def get_account(self) -> AccountInfo:
        equity = self._cash + sum(
            p.market_value for p in self._positions.values()
        )
        return AccountInfo(
            account_id="paper-local",
            broker=self.name,
            currency="USD",
            balance=self._cash,
            equity=equity,
            buying_power=self._cash,
            cash=self._cash,
            portfolio_value=equity,
            day_trades_remaining=None,
            leverage=1.0,
            is_paper=True,
        )

    # --- Market Data ---

    async def get_quote(self, symbol: str) -> Quote:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        last = float(info.last_price)
        prev = float(info.previous_close)
        spread = last * self._slippage
        return Quote(
            symbol=symbol,
            bid=last - spread / 2,
            ask=last + spread / 2,
            last=last,
            volume=int(info.last_volume),
            timestamp=datetime.now(),
            prev_close=prev,
        )

    async def get_bars(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: str | None = None,
        end: str | None = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        yf_interval = _YF_TIMEFRAME_MAP.get(timeframe, "1d")
        kwargs: dict[str, object] = {"interval": yf_interval}
        if start and end:
            kwargs["start"] = start
            kwargs["end"] = end
        else:
            period = _YF_PERIOD_FOR_TIMEFRAME.get(yf_interval, "3mo")
            kwargs["period"] = period

        ticker = yf.Ticker(symbol)
        df = ticker.history(**kwargs)  # type: ignore[arg-type]

        if df.empty:
            return pd.DataFrame(
                columns=["open", "high", "low", "close", "volume"]
            )

        df.columns = [c.lower() for c in df.columns]
        cols = ["open", "high", "low", "close", "volume"]
        df = df[[c for c in cols if c in df.columns]]
        return df.tail(limit)

    async def subscribe_quotes(
        self, symbols: list[str], callback: Callable[[Quote], None]
    ) -> None:
        logger.warning("PaperBroker does not support real-time streaming")

    async def unsubscribe_quotes(self, symbols: list[str]) -> None:
        pass

    # --- Orders ---

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: float | None = None,
        stop_price: float | None = None,
        time_in_force: TimeInForce = TimeInForce.DAY,
    ) -> Order:
        order_id = str(uuid.uuid4())[:8]
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            limit_price=limit_price,
            stop_price=stop_price,
            time_in_force=time_in_force,
        )
        self._orders[order_id] = order

        if order_type == OrderType.MARKET:
            order = await self._fill_order(order)
        else:
            order.status = OrderStatus.SUBMITTED
            self._open_orders[order_id] = order
            logger.info("Order %s submitted (pending fill)", order_id)

        return order

    async def cancel_order(self, order_id: str) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise ValueError(f"Order {order_id} not found")
        if not order.is_active:
            raise ValueError(f"Order {order_id} is not active ({order.status})")
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now()
        self._open_orders.pop(order_id, None)
        return order

    async def get_order(self, order_id: str) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise ValueError(f"Order {order_id} not found")
        return order

    async def get_open_orders(self) -> list[Order]:
        return list(self._open_orders.values())

    # --- Positions ---

    async def get_positions(self) -> list[Position]:
        return list(self._positions.values())

    async def get_position(self, symbol: str) -> Position | None:
        return self._positions.get(symbol)

    async def close_position(self, symbol: str) -> Order:
        pos = self._positions.get(symbol)
        if pos is None:
            raise ValueError(f"No position for {symbol}")
        close_side = OrderSide.SELL if pos.is_long else OrderSide.BUY
        return await self.place_order(
            symbol=symbol,
            side=close_side,
            quantity=abs(pos.quantity),
        )

    async def close_all_positions(self) -> list[Order]:
        orders: list[Order] = []
        for symbol in list(self._positions.keys()):
            order = await self.close_position(symbol)
            orders.append(order)
        return orders

    # --- Internal ---

    async def _fill_order(self, order: Order) -> Order:
        """Simulate immediate fill at market price with slippage."""
        quote = await self.get_quote(order.symbol)
        if order.side == OrderSide.BUY:
            fill_price = quote.ask
        else:
            fill_price = quote.bid

        cost = fill_price * order.quantity + self._commission

        if order.side == OrderSide.BUY:
            if cost > self._cash:
                order.status = OrderStatus.REJECTED
                logger.warning(
                    "Order %s rejected: insufficient cash (%.2f needed, %.2f available)",
                    order.order_id,
                    cost,
                    self._cash,
                )
                return order
            self._cash -= cost
            self._update_position_on_buy(order.symbol, order.quantity, fill_price)
        else:
            pos = self._positions.get(order.symbol)
            if pos is None or pos.quantity < order.quantity:
                order.status = OrderStatus.REJECTED
                logger.warning("Order %s rejected: insufficient position", order.order_id)
                return order
            proceeds = fill_price * order.quantity - self._commission
            self._cash += proceeds
            self._update_position_on_sell(order.symbol, order.quantity, fill_price)

        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.filled_avg_price = fill_price
        order.updated_at = datetime.now()
        self._open_orders.pop(order.order_id, None)
        logger.info(
            "Order %s filled: %s %s %.4f @ %.2f",
            order.order_id,
            order.side.value,
            order.symbol,
            order.quantity,
            fill_price,
        )
        return order

    def _update_position_on_buy(
        self, symbol: str, qty: float, price: float
    ) -> None:
        existing = self._positions.get(symbol)
        if existing is not None:
            total_qty = existing.quantity + qty
            avg_price = (
                (existing.entry_price * existing.quantity + price * qty) / total_qty
            )
            existing.quantity = total_qty
            existing.entry_price = avg_price
            existing.current_price = price
            existing.market_value = total_qty * price
            existing.unrealized_pnl = (price - avg_price) * total_qty
            existing.unrealized_pnl_pct = (
                (price - avg_price) / avg_price if avg_price else 0.0
            )
        else:
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=qty,
                side=OrderSide.BUY,
                entry_price=price,
                current_price=price,
                market_value=qty * price,
                unrealized_pnl=0.0,
                unrealized_pnl_pct=0.0,
            )

    def _update_position_on_sell(
        self, symbol: str, qty: float, price: float
    ) -> None:
        pos = self._positions[symbol]
        remaining = pos.quantity - qty
        if remaining <= 1e-9:
            del self._positions[symbol]
        else:
            pos.quantity = remaining
            pos.current_price = price
            pos.market_value = remaining * price
            pos.unrealized_pnl = (price - pos.entry_price) * remaining
            pos.unrealized_pnl_pct = (
                (price - pos.entry_price) / pos.entry_price
                if pos.entry_price
                else 0.0
            )
