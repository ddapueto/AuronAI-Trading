"""Shared models for broker abstraction layer."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    """Order direction."""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderStatus(str, Enum):
    """Order lifecycle status."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForce(str, Enum):
    """Order time-in-force policy."""

    DAY = "day"  # Valid for the trading day
    GTC = "gtc"  # Good til cancelled
    IOC = "ioc"  # Immediate or cancel
    FOK = "fok"  # Fill or kill


class AssetType(str, Enum):
    """Type of tradeable asset."""

    STOCK = "stock"
    ETF = "etf"
    CFD = "cfd"
    CRYPTO = "crypto"
    FOREX = "forex"


@dataclass
class AccountInfo:
    """Broker account information."""

    account_id: str
    broker: str
    currency: str
    balance: float
    equity: float
    buying_power: float
    cash: float
    portfolio_value: float
    day_trades_remaining: int | None = None  # None if PDT doesn't apply (CFDs)
    leverage: float = 1.0
    is_paper: bool = True


@dataclass
class Quote:
    """Real-time quote for a symbol."""

    symbol: str
    bid: float
    ask: float
    last: float
    volume: int
    timestamp: datetime
    high: float = 0.0
    low: float = 0.0
    open: float = 0.0
    prev_close: float = 0.0

    @property
    def mid(self) -> float:
        """Mid price between bid and ask."""
        return (self.bid + self.ask) / 2

    @property
    def spread(self) -> float:
        """Bid-ask spread."""
        return self.ask - self.bid


@dataclass
class Position:
    """Open position in broker account."""

    symbol: str
    quantity: float  # float for fractional shares
    side: OrderSide
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    asset_type: AssetType = AssetType.STOCK

    @property
    def is_long(self) -> bool:
        return self.side == OrderSide.BUY

    @property
    def is_short(self) -> bool:
        return self.side == OrderSide.SELL


@dataclass
class Order:
    """Order representation."""

    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    status: OrderStatus = OrderStatus.PENDING
    limit_price: float | None = None
    stop_price: float | None = None
    time_in_force: TimeInForce = TimeInForce.DAY
    filled_quantity: float = 0.0
    filled_avg_price: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    broker_order_id: str | None = None

    @property
    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED

    @property
    def is_active(self) -> bool:
        return self.status in (
            OrderStatus.PENDING,
            OrderStatus.SUBMITTED,
            OrderStatus.PARTIAL,
        )
