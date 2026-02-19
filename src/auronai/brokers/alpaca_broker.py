"""Alpaca Markets broker implementation."""

import logging
import os
from collections.abc import Callable
from datetime import datetime

import pandas as pd

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

_ORDER_SIDE_MAP = {"buy": OrderSide.BUY, "sell": OrderSide.SELL}

_ORDER_STATUS_MAP = {
    "new": OrderStatus.SUBMITTED,
    "accepted": OrderStatus.SUBMITTED,
    "pending_new": OrderStatus.PENDING,
    "partially_filled": OrderStatus.PARTIAL,
    "filled": OrderStatus.FILLED,
    "canceled": OrderStatus.CANCELLED,
    "expired": OrderStatus.EXPIRED,
    "rejected": OrderStatus.REJECTED,
    "pending_cancel": OrderStatus.SUBMITTED,
    "pending_replace": OrderStatus.SUBMITTED,
}

_ORDER_TYPE_MAP = {
    "market": OrderType.MARKET,
    "limit": OrderType.LIMIT,
    "stop": OrderType.STOP,
    "stop_limit": OrderType.STOP_LIMIT,
    "trailing_stop": OrderType.TRAILING_STOP,
}

_TIF_MAP = {
    "day": TimeInForce.DAY,
    "gtc": TimeInForce.GTC,
    "ioc": TimeInForce.IOC,
    "fok": TimeInForce.FOK,
}

_TIMEFRAME_MAP = {
    "1m": "1Min",
    "5m": "5Min",
    "15m": "15Min",
    "1h": "1Hour",
    "1d": "1Day",
}


class AlpacaBroker(BaseBroker):
    """
    Alpaca Markets broker.

    Connects to Alpaca REST API via alpaca-py. Supports paper and live trading.
    PDT rule applies for accounts under $25K.

    Example::

        broker = AlpacaBroker(
            api_key="PK...",
            secret_key="...",
            paper=True,
        )
        await broker.connect()
        account = await broker.get_account()
    """

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        paper: bool = True,
    ) -> None:
        self._api_key = api_key or os.getenv("ALPACA_API_KEY", "")
        self._secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY", "")
        self._paper = paper
        self._connected = False
        self._trading_client: object | None = None
        self._data_client: object | None = None

    @property
    def name(self) -> str:
        return "alpaca"

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def supports_fractional(self) -> bool:
        return True

    @property
    def supports_short_selling(self) -> bool:
        return True

    async def connect(self) -> None:
        from alpaca.data.live import StockDataStream  # noqa: F401
        from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest  # noqa: F401
        from alpaca.trading.client import TradingClient

        if not self._api_key or not self._secret_key:
            raise ValueError(
                "Alpaca API keys required. Set ALPACA_API_KEY and ALPACA_SECRET_KEY."
            )

        self._trading_client = TradingClient(
            api_key=self._api_key,
            secret_key=self._secret_key,
            paper=self._paper,
        )
        self._connected = True
        logger.info("AlpacaBroker connected (paper=%s)", self._paper)

    async def disconnect(self) -> None:
        self._trading_client = None
        self._data_client = None
        self._connected = False
        logger.info("AlpacaBroker disconnected")

    def _ensure_connected(self) -> None:
        if not self._connected or self._trading_client is None:
            raise RuntimeError("AlpacaBroker is not connected. Call connect() first.")

    async def get_account(self) -> AccountInfo:
        self._ensure_connected()
        acct = self._trading_client.get_account()  # type: ignore[union-attr]
        return AccountInfo(
            account_id=str(acct.id),
            broker=self.name,
            currency=str(acct.currency),
            balance=float(acct.cash),
            equity=float(acct.equity),
            buying_power=float(acct.buying_power),
            cash=float(acct.cash),
            portfolio_value=float(acct.portfolio_value),
            day_trades_remaining=(
                max(0, 3 - int(acct.daytrade_count))
                if hasattr(acct, "daytrade_count") and acct.daytrade_count is not None
                else None
            ),
            leverage=float(acct.multiplier) if acct.multiplier else 1.0,
            is_paper=self._paper,
        )

    async def get_quote(self, symbol: str) -> Quote:
        self._ensure_connected()
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockLatestQuoteRequest

        client = StockHistoricalDataClient(
            api_key=self._api_key, secret_key=self._secret_key
        )
        req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        quotes = client.get_stock_latest_quote(req)
        q = quotes[symbol]
        return Quote(
            symbol=symbol,
            bid=float(q.bid_price),
            ask=float(q.ask_price),
            last=float(q.ask_price),  # Alpaca doesn't provide last in quote
            volume=int(q.bid_size + q.ask_size),
            timestamp=q.timestamp if isinstance(q.timestamp, datetime) else datetime.now(),
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
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

        client = StockHistoricalDataClient(
            api_key=self._api_key, secret_key=self._secret_key
        )

        tf_map = {
            "1m": TimeFrame(1, TimeFrameUnit.Minute),
            "5m": TimeFrame(5, TimeFrameUnit.Minute),
            "15m": TimeFrame(15, TimeFrameUnit.Minute),
            "1h": TimeFrame(1, TimeFrameUnit.Hour),
            "1d": TimeFrame(1, TimeFrameUnit.Day),
        }
        tf = tf_map.get(timeframe, TimeFrame(1, TimeFrameUnit.Day))

        params: dict[str, object] = {
            "symbol_or_symbols": symbol,
            "timeframe": tf,
            "limit": limit,
        }
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        req = StockBarsRequest(**params)  # type: ignore[arg-type]
        bars = client.get_stock_bars(req)
        df = bars.df

        if df.empty:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        df.columns = [c.lower() for c in df.columns]
        if isinstance(df.index, pd.MultiIndex):
            df = df.droplevel("symbol")
        cols = ["open", "high", "low", "close", "volume"]
        return df[[c for c in cols if c in df.columns]]

    async def subscribe_quotes(
        self, symbols: list[str], callback: Callable[[Quote], None]
    ) -> None:
        self._ensure_connected()
        logger.info("Alpaca quote subscription requested for %s (not started)", symbols)

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
        from alpaca.trading.enums import (
            OrderSide as AlpacaSide,
        )
        from alpaca.trading.enums import (
            TimeInForce as AlpacaTIF,
        )
        from alpaca.trading.requests import (
            LimitOrderRequest,
            MarketOrderRequest,
            StopLimitOrderRequest,
            StopOrderRequest,
        )

        alpaca_side = AlpacaSide.BUY if side == OrderSide.BUY else AlpacaSide.SELL
        tif_map = {
            TimeInForce.DAY: AlpacaTIF.DAY,
            TimeInForce.GTC: AlpacaTIF.GTC,
            TimeInForce.IOC: AlpacaTIF.IOC,
            TimeInForce.FOK: AlpacaTIF.FOK,
        }
        alpaca_tif = tif_map.get(time_in_force, AlpacaTIF.DAY)

        if order_type == OrderType.MARKET:
            req = MarketOrderRequest(
                symbol=symbol, qty=quantity, side=alpaca_side, time_in_force=alpaca_tif
            )
        elif order_type == OrderType.LIMIT:
            req = LimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=alpaca_side,
                time_in_force=alpaca_tif,
                limit_price=limit_price,
            )
        elif order_type == OrderType.STOP:
            req = StopOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=alpaca_side,
                time_in_force=alpaca_tif,
                stop_price=stop_price,
            )
        elif order_type == OrderType.STOP_LIMIT:
            req = StopLimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=alpaca_side,
                time_in_force=alpaca_tif,
                limit_price=limit_price,
                stop_price=stop_price,
            )
        else:
            raise ValueError(f"Unsupported order type: {order_type}")

        result = self._trading_client.submit_order(req)  # type: ignore[union-attr]
        return self._map_alpaca_order(result)

    async def cancel_order(self, order_id: str) -> Order:
        self._ensure_connected()
        self._trading_client.cancel_order_by_id(order_id)  # type: ignore[union-attr]
        return await self.get_order(order_id)

    async def get_order(self, order_id: str) -> Order:
        self._ensure_connected()
        result = self._trading_client.get_order_by_id(order_id)  # type: ignore[union-attr]
        return self._map_alpaca_order(result)

    async def get_open_orders(self) -> list[Order]:
        self._ensure_connected()
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        req = GetOrdersRequest(status=QueryOrderStatus.OPEN)
        results = self._trading_client.get_orders(req)  # type: ignore[union-attr]
        return [self._map_alpaca_order(o) for o in results]

    async def get_positions(self) -> list[Position]:
        self._ensure_connected()
        results = self._trading_client.get_all_positions()  # type: ignore[union-attr]
        return [self._map_alpaca_position(p) for p in results]

    async def get_position(self, symbol: str) -> Position | None:
        self._ensure_connected()
        try:
            result = self._trading_client.get_open_position(symbol)  # type: ignore[union-attr]
            return self._map_alpaca_position(result)
        except Exception:  # noqa: BLE001
            return None

    async def close_position(self, symbol: str) -> Order:
        self._ensure_connected()
        result = self._trading_client.close_position(symbol)  # type: ignore[union-attr]
        return self._map_alpaca_order(result)

    async def close_all_positions(self) -> list[Order]:
        self._ensure_connected()
        results = self._trading_client.close_all_positions()  # type: ignore[union-attr]
        return [self._map_alpaca_order(o) for o in results]

    @staticmethod
    def _map_alpaca_order(o: object) -> Order:
        """Map alpaca-py order object to our Order model."""
        status = _ORDER_STATUS_MAP.get(str(o.status), OrderStatus.PENDING)  # type: ignore[attr-defined]
        side = _ORDER_SIDE_MAP.get(str(o.side), OrderSide.BUY)  # type: ignore[attr-defined]
        otype = _ORDER_TYPE_MAP.get(str(o.type), OrderType.MARKET)  # type: ignore[attr-defined]
        tif = _TIF_MAP.get(str(o.time_in_force), TimeInForce.DAY)  # type: ignore[attr-defined]
        return Order(
            order_id=str(o.id),  # type: ignore[attr-defined]
            symbol=str(o.symbol),  # type: ignore[attr-defined]
            side=side,
            order_type=otype,
            quantity=float(o.qty or 0),  # type: ignore[attr-defined]
            status=status,
            limit_price=float(o.limit_price) if o.limit_price else None,  # type: ignore[attr-defined]
            stop_price=float(o.stop_price) if o.stop_price else None,  # type: ignore[attr-defined]
            time_in_force=tif,
            filled_quantity=float(o.filled_qty or 0),  # type: ignore[attr-defined]
            filled_avg_price=float(o.filled_avg_price or 0),  # type: ignore[attr-defined]
            created_at=o.created_at if isinstance(o.created_at, datetime) else datetime.now(),  # type: ignore[attr-defined]
            updated_at=o.updated_at if isinstance(o.updated_at, datetime) else datetime.now(),  # type: ignore[attr-defined]
            broker_order_id=str(o.id),  # type: ignore[attr-defined]
        )

    @staticmethod
    def _map_alpaca_position(p: object) -> Position:
        """Map alpaca-py position object to our Position model."""
        qty = float(p.qty)  # type: ignore[attr-defined]
        side = OrderSide.BUY if qty > 0 else OrderSide.SELL
        return Position(
            symbol=str(p.symbol),  # type: ignore[attr-defined]
            quantity=abs(qty),
            side=side,
            entry_price=float(p.avg_entry_price),  # type: ignore[attr-defined]
            current_price=float(p.current_price),  # type: ignore[attr-defined]
            market_value=float(p.market_value),  # type: ignore[attr-defined]
            unrealized_pnl=float(p.unrealized_pl),  # type: ignore[attr-defined]
            unrealized_pnl_pct=float(p.unrealized_plpc),  # type: ignore[attr-defined]
        )
