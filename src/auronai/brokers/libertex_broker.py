"""Libertex broker via MetaTrader 5 terminal.

NOTE: MetaTrader5 only works on Windows (or Wine/VM on Mac/Linux).
Install with: pip install MetaTrader5
"""

import logging
import os
from collections.abc import Callable
from datetime import datetime

import pandas as pd

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

logger = logging.getLogger(__name__)

_MT5_TIMEFRAME_MAP = {
    "1m": "TIMEFRAME_M1",
    "5m": "TIMEFRAME_M5",
    "15m": "TIMEFRAME_M15",
    "1h": "TIMEFRAME_H1",
    "1d": "TIMEFRAME_D1",
}


class LibertexBroker(BaseBroker):
    """
    Libertex broker via MetaTrader 5.

    Supports CFDs with no PDT rule and leverage up to 1:999.
    Requires MetaTrader5 Python package (Windows only).

    Example::

        broker = LibertexBroker(
            login=12345678,
            password="...",
            server="Libertex-Demo",
        )
        await broker.connect()
    """

    def __init__(
        self,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
        mt5_path: str | None = None,
    ) -> None:
        self._login = login or int(os.getenv("MT5_LOGIN", "0"))
        self._password = password or os.getenv("MT5_PASSWORD", "")
        self._server = server or os.getenv("MT5_SERVER", "Libertex-Demo")
        self._mt5_path = mt5_path or os.getenv("MT5_PATH")
        self._connected = False
        self._mt5: object | None = None

    @property
    def name(self) -> str:
        return "libertex"

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def supports_fractional(self) -> bool:
        return True  # CFDs support 0.01 lot

    @property
    def supports_short_selling(self) -> bool:
        return True  # CFDs allow short selling

    def _get_mt5(self) -> object:
        """Lazy import MetaTrader5."""
        if self._mt5 is None:
            try:
                import MetaTrader5 as mt5  # type: ignore[import-untyped]

                self._mt5 = mt5
            except ImportError:
                raise ImportError(
                    "MetaTrader5 package required. Install with: pip install MetaTrader5. "
                    "NOTE: Only works on Windows (or Wine/VM)."
                ) from None
        return self._mt5

    async def connect(self) -> None:
        mt5 = self._get_mt5()

        init_kwargs: dict[str, object] = {}
        if self._mt5_path:
            init_kwargs["path"] = self._mt5_path

        if not mt5.initialize(**init_kwargs):  # type: ignore[union-attr]
            error = mt5.last_error()  # type: ignore[union-attr]
            raise ConnectionError(f"MT5 initialize failed: {error}")

        if self._login:
            authorized = mt5.login(  # type: ignore[union-attr]
                login=self._login,
                password=self._password,
                server=self._server,
            )
            if not authorized:
                mt5.shutdown()  # type: ignore[union-attr]
                raise ConnectionError(
                    f"MT5 login failed for account {self._login} on {self._server}"
                )

        self._connected = True
        logger.info("LibertexBroker connected (server=%s)", self._server)

    async def disconnect(self) -> None:
        if self._mt5 is not None:
            self._mt5.shutdown()  # type: ignore[union-attr]
        self._connected = False
        logger.info("LibertexBroker disconnected")

    def _ensure_connected(self) -> None:
        if not self._connected:
            raise RuntimeError("LibertexBroker is not connected. Call connect() first.")

    async def get_account(self) -> AccountInfo:
        self._ensure_connected()
        mt5 = self._get_mt5()
        info = mt5.account_info()  # type: ignore[union-attr]
        if info is None:
            raise RuntimeError("Failed to get MT5 account info")
        return AccountInfo(
            account_id=str(info.login),
            broker=self.name,
            currency=info.currency,
            balance=float(info.balance),
            equity=float(info.equity),
            buying_power=float(info.margin_free),
            cash=float(info.balance),
            portfolio_value=float(info.equity),
            day_trades_remaining=None,  # No PDT for CFDs
            leverage=float(info.leverage),
            is_paper=info.trade_mode != 0,  # 0 = real, 1 = demo
        )

    async def get_quote(self, symbol: str) -> Quote:
        self._ensure_connected()
        mt5 = self._get_mt5()
        tick = mt5.symbol_info_tick(symbol)  # type: ignore[union-attr]
        if tick is None:
            raise ValueError(f"No tick data for {symbol}")
        return Quote(
            symbol=symbol,
            bid=float(tick.bid),
            ask=float(tick.ask),
            last=float(tick.last),
            volume=int(tick.volume),
            timestamp=datetime.fromtimestamp(tick.time),
        )

    async def get_bars(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: str | None = None,
        end: str | None = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        self._ensure_connected()
        mt5 = self._get_mt5()

        tf_name = _MT5_TIMEFRAME_MAP.get(timeframe, "TIMEFRAME_D1")
        mt5_tf = getattr(mt5, tf_name)

        rates = mt5.copy_rates_from_pos(  # type: ignore[union-attr]
            symbol, mt5_tf, 0, limit
        )
        if rates is None or len(rates) == 0:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df = df.set_index("time")
        return df[["open", "high", "low", "close", "tick_volume"]].rename(
            columns={"tick_volume": "volume"}
        )

    async def subscribe_quotes(
        self, symbols: list[str], callback: Callable[[Quote], None]
    ) -> None:
        logger.info(
            "LibertexBroker: quote subscription requested for %s (polling mode)", symbols
        )

    async def unsubscribe_quotes(self, symbols: list[str]) -> None:
        pass

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
        self._ensure_connected()
        mt5 = self._get_mt5()

        tick = mt5.symbol_info_tick(symbol)  # type: ignore[union-attr]
        if tick is None:
            raise ValueError(f"Cannot get price for {symbol}")

        price = tick.ask if side == OrderSide.BUY else tick.bid

        if order_type == OrderType.MARKET:
            mt5_type = mt5.ORDER_TYPE_BUY if side == OrderSide.BUY else mt5.ORDER_TYPE_SELL  # type: ignore[union-attr]
        elif order_type == OrderType.LIMIT:
            mt5_type = (  # type: ignore[union-attr]
                mt5.ORDER_TYPE_BUY_LIMIT
                if side == OrderSide.BUY
                else mt5.ORDER_TYPE_SELL_LIMIT
            )
            price = limit_price or price
        elif order_type == OrderType.STOP:
            mt5_type = (  # type: ignore[union-attr]
                mt5.ORDER_TYPE_BUY_STOP
                if side == OrderSide.BUY
                else mt5.ORDER_TYPE_SELL_STOP
            )
            price = stop_price or price
        else:
            raise ValueError(f"Unsupported order type for MT5: {order_type}")

        request = {
            "action": mt5.TRADE_ACTION_DEAL if order_type == OrderType.MARKET else mt5.TRADE_ACTION_PENDING,  # type: ignore[union-attr]
            "symbol": symbol,
            "volume": quantity,
            "type": mt5_type,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "auronai",
            "type_time": mt5.ORDER_TIME_GTC,  # type: ignore[union-attr]
            "type_filling": mt5.ORDER_FILLING_IOC,  # type: ignore[union-attr]
        }

        result = mt5.order_send(request)  # type: ignore[union-attr]
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:  # type: ignore[union-attr]
            error_msg = result.comment if result else "Unknown error"
            logger.error("MT5 order failed: %s", error_msg)
            return Order(
                order_id=str(result.order) if result else "0",
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                status=OrderStatus.REJECTED,
            )

        return Order(
            order_id=str(result.order),
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            status=OrderStatus.FILLED if order_type == OrderType.MARKET else OrderStatus.SUBMITTED,
            filled_quantity=float(result.volume),
            filled_avg_price=float(result.price),
            broker_order_id=str(result.deal),
        )

    async def cancel_order(self, order_id: str) -> Order:
        self._ensure_connected()
        mt5 = self._get_mt5()
        request = {
            "action": mt5.TRADE_ACTION_REMOVE,  # type: ignore[union-attr]
            "order": int(order_id),
        }
        mt5.order_send(request)  # type: ignore[union-attr]
        return await self.get_order(order_id)

    async def get_order(self, order_id: str) -> Order:
        self._ensure_connected()
        mt5 = self._get_mt5()
        orders = mt5.orders_get(ticket=int(order_id))  # type: ignore[union-attr]
        if orders and len(orders) > 0:
            o = orders[0]
            side = OrderSide.BUY if o.type in (0, 2, 4) else OrderSide.SELL
            return Order(
                order_id=str(o.ticket),
                symbol=o.symbol,
                side=side,
                order_type=OrderType.MARKET,
                quantity=float(o.volume_current),
                status=OrderStatus.SUBMITTED,
                broker_order_id=str(o.ticket),
            )

        # Check in history
        deals = mt5.history_orders_get(ticket=int(order_id))  # type: ignore[union-attr]
        if deals and len(deals) > 0:
            d = deals[0]
            side = OrderSide.BUY if d.type in (0, 2, 4) else OrderSide.SELL
            return Order(
                order_id=str(d.ticket),
                symbol=d.symbol,
                side=side,
                order_type=OrderType.MARKET,
                quantity=float(d.volume_initial),
                status=OrderStatus.FILLED,
                filled_quantity=float(d.volume_initial),
                broker_order_id=str(d.ticket),
            )

        raise ValueError(f"Order {order_id} not found")

    async def get_open_orders(self) -> list[Order]:
        self._ensure_connected()
        mt5 = self._get_mt5()
        orders = mt5.orders_get()  # type: ignore[union-attr]
        if orders is None:
            return []
        result = []
        for o in orders:
            side = OrderSide.BUY if o.type in (0, 2, 4) else OrderSide.SELL
            result.append(
                Order(
                    order_id=str(o.ticket),
                    symbol=o.symbol,
                    side=side,
                    order_type=OrderType.LIMIT,
                    quantity=float(o.volume_current),
                    status=OrderStatus.SUBMITTED,
                    broker_order_id=str(o.ticket),
                )
            )
        return result

    async def get_positions(self) -> list[Position]:
        self._ensure_connected()
        mt5 = self._get_mt5()
        positions = mt5.positions_get()  # type: ignore[union-attr]
        if positions is None:
            return []
        return [self._map_mt5_position(p) for p in positions]

    async def get_position(self, symbol: str) -> Position | None:
        self._ensure_connected()
        mt5 = self._get_mt5()
        positions = mt5.positions_get(symbol=symbol)  # type: ignore[union-attr]
        if positions is None or len(positions) == 0:
            return None
        return self._map_mt5_position(positions[0])

    async def close_position(self, symbol: str) -> Order:
        pos = await self.get_position(symbol)
        if pos is None:
            raise ValueError(f"No position for {symbol}")
        close_side = OrderSide.SELL if pos.is_long else OrderSide.BUY
        return await self.place_order(
            symbol=symbol,
            side=close_side,
            quantity=pos.quantity,
        )

    async def close_all_positions(self) -> list[Order]:
        positions = await self.get_positions()
        orders: list[Order] = []
        for pos in positions:
            order = await self.close_position(pos.symbol)
            orders.append(order)
        return orders

    @staticmethod
    def _map_mt5_position(p: object) -> Position:
        """Map MT5 position to our Position model."""
        side = OrderSide.BUY if p.type == 0 else OrderSide.SELL  # type: ignore[attr-defined]
        qty = float(p.volume)  # type: ignore[attr-defined]
        entry = float(p.price_open)  # type: ignore[attr-defined]
        current = float(p.price_current)  # type: ignore[attr-defined]
        pnl = float(p.profit)  # type: ignore[attr-defined]
        return Position(
            symbol=str(p.symbol),  # type: ignore[attr-defined]
            quantity=qty,
            side=side,
            entry_price=entry,
            current_price=current,
            market_value=qty * current,
            unrealized_pnl=pnl,
            unrealized_pnl_pct=(current - entry) / entry if entry else 0.0,
            asset_type=AssetType.CFD,
        )
