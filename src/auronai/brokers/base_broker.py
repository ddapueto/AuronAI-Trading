"""Abstract base class for broker implementations."""

from abc import ABC, abstractmethod
from collections.abc import Callable

import pandas as pd

from auronai.brokers.models import (
    AccountInfo,
    Order,
    OrderSide,
    OrderType,
    Position,
    Quote,
    TimeInForce,
)


class BaseBroker(ABC):
    """
    Abstract broker interface.

    All broker implementations (Alpaca, Libertex/MT5, Paper) must implement
    this interface. This allows strategies and the execution engine to be
    broker-agnostic.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Broker identifier (e.g., 'alpaca', 'libertex', 'paper')."""
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Whether the broker connection is active."""
        ...

    @property
    @abstractmethod
    def supports_fractional(self) -> bool:
        """Whether the broker supports fractional shares."""
        ...

    @property
    @abstractmethod
    def supports_short_selling(self) -> bool:
        """Whether the broker supports short selling."""
        ...

    @property
    def supports_paper_trading(self) -> bool:
        """Whether the broker has a paper/demo mode."""
        return True

    # --- Connection ---

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the broker."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the broker."""
        ...

    # --- Account ---

    @abstractmethod
    async def get_account(self) -> AccountInfo:
        """Get current account information."""
        ...

    # --- Market Data ---

    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote:
        """Get real-time quote for a symbol."""
        ...

    @abstractmethod
    async def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: str | None = None,
        end: str | None = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        Get historical OHLCV bars.

        Args:
            symbol: Ticker symbol.
            timeframe: Bar timeframe ('1m', '5m', '15m', '1h', '1d').
            start: Start datetime string (ISO format).
            end: End datetime string (ISO format).
            limit: Maximum number of bars.

        Returns:
            DataFrame with columns: open, high, low, close, volume, timestamp.
        """
        ...

    @abstractmethod
    async def subscribe_quotes(
        self, symbols: list[str], callback: Callable[[Quote], None]
    ) -> None:
        """
        Subscribe to real-time quote updates.

        Args:
            symbols: List of symbols to subscribe to.
            callback: Function called with each new Quote.
        """
        ...

    @abstractmethod
    async def unsubscribe_quotes(self, symbols: list[str]) -> None:
        """Unsubscribe from real-time quote updates."""
        ...

    # --- Orders ---

    @abstractmethod
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
        """
        Place a new order.

        Args:
            symbol: Ticker symbol.
            side: BUY or SELL.
            quantity: Number of shares (fractional allowed if broker supports).
            order_type: MARKET, LIMIT, STOP, STOP_LIMIT.
            limit_price: Required for LIMIT and STOP_LIMIT orders.
            stop_price: Required for STOP and STOP_LIMIT orders.
            time_in_force: DAY, GTC, IOC, FOK.

        Returns:
            Order with status and broker order ID.
        """
        ...

    @abstractmethod
    async def cancel_order(self, order_id: str) -> Order:
        """Cancel an open order by ID."""
        ...

    @abstractmethod
    async def get_order(self, order_id: str) -> Order:
        """Get order details by ID."""
        ...

    @abstractmethod
    async def get_open_orders(self) -> list[Order]:
        """Get all open/pending orders."""
        ...

    # --- Positions ---

    @abstractmethod
    async def get_positions(self) -> list[Position]:
        """Get all open positions."""
        ...

    @abstractmethod
    async def get_position(self, symbol: str) -> Position | None:
        """Get position for a specific symbol, or None if no position."""
        ...

    @abstractmethod
    async def close_position(self, symbol: str) -> Order:
        """Close entire position for a symbol."""
        ...

    @abstractmethod
    async def close_all_positions(self) -> list[Order]:
        """Close all open positions. Returns list of closing orders."""
        ...

    # --- Convenience methods ---

    async def buy(
        self,
        symbol: str,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: float | None = None,
    ) -> Order:
        """Place a buy order (convenience wrapper)."""
        return await self.place_order(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
        )

    async def sell(
        self,
        symbol: str,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: float | None = None,
    ) -> Order:
        """Place a sell order (convenience wrapper)."""
        return await self.place_order(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
        )
