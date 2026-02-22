"""Paper trading endpoints — account, positions, orders, kill switch."""

from fastapi import APIRouter, Depends, HTTPException, Query

from auronai.api.dependencies import get_broker
from auronai.api.schemas import (
    AccountResponse,
    KillSwitchResponse,
    OrderResponse,
    PositionResponse,
    TradeRequest,
)
from auronai.brokers.models import OrderSide, OrderStatus, OrderType
from auronai.brokers.paper_broker import PaperBroker

router = APIRouter(prefix="/api/trading", tags=["trading"])


def _order_to_response(o) -> OrderResponse:
    return OrderResponse(
        order_id=o.order_id,
        symbol=o.symbol,
        side=o.side.value,
        order_type=o.order_type.value,
        quantity=o.quantity,
        status=o.status.value,
        limit_price=o.limit_price,
        stop_price=o.stop_price,
        filled_quantity=o.filled_quantity,
        filled_avg_price=o.filled_avg_price,
        created_at=o.created_at,
        updated_at=o.updated_at,
    )


def _position_to_response(p) -> PositionResponse:
    return PositionResponse(
        symbol=p.symbol,
        quantity=p.quantity,
        side=p.side.value,
        entry_price=p.entry_price,
        current_price=p.current_price,
        market_value=p.market_value,
        unrealized_pnl=p.unrealized_pnl,
        unrealized_pnl_pct=p.unrealized_pnl_pct,
    )


@router.get("/account", response_model=AccountResponse)
async def get_account(broker: PaperBroker = Depends(get_broker)):
    """Get paper trading account info."""
    acc = await broker.get_account()
    return AccountResponse(
        account_id=acc.account_id,
        broker=acc.broker,
        currency=acc.currency,
        balance=acc.balance,
        equity=acc.equity,
        buying_power=acc.buying_power,
        cash=acc.cash,
        portfolio_value=acc.portfolio_value,
        day_trades_remaining=acc.day_trades_remaining,
        leverage=acc.leverage,
        is_paper=acc.is_paper,
    )


@router.get("/positions", response_model=list[PositionResponse])
async def get_positions(broker: PaperBroker = Depends(get_broker)):
    """List all open positions."""
    positions = await broker.get_positions()
    return [_position_to_response(p) for p in positions]


@router.post("/buy", response_model=OrderResponse)
async def buy(body: TradeRequest, broker: PaperBroker = Depends(get_broker)):
    """Place a buy order."""
    try:
        ot = OrderType(body.order_type) if body.order_type else OrderType.MARKET
        order = await broker.place_order(
            symbol=body.symbol.upper(),
            side=OrderSide.BUY,
            quantity=body.quantity,
            order_type=ot,
            limit_price=body.limit_price,
        )
        return _order_to_response(order)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sell", response_model=OrderResponse)
async def sell(body: TradeRequest, broker: PaperBroker = Depends(get_broker)):
    """Place a sell order."""
    try:
        ot = OrderType(body.order_type) if body.order_type else OrderType.MARKET
        order = await broker.place_order(
            symbol=body.symbol.upper(),
            side=OrderSide.SELL,
            quantity=body.quantity,
            order_type=ot,
            limit_price=body.limit_price,
        )
        return _order_to_response(order)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/close/{symbol}", response_model=OrderResponse)
async def close_position(
    symbol: str,
    broker: PaperBroker = Depends(get_broker),
):
    """Close an open position."""
    try:
        order = await broker.close_position(symbol.upper())
        return _order_to_response(order)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/close-all", response_model=list[OrderResponse])
async def close_all_positions(broker: PaperBroker = Depends(get_broker)):
    """Close all open positions."""
    orders = await broker.close_all_positions()
    return [_order_to_response(o) for o in orders]


@router.get("/orders", response_model=list[OrderResponse])
async def get_orders(broker: PaperBroker = Depends(get_broker)):
    """List open orders."""
    orders = await broker.get_open_orders()
    return [_order_to_response(o) for o in orders]


@router.post("/kill-switch", response_model=KillSwitchResponse)
async def kill_switch(broker: PaperBroker = Depends(get_broker)):
    """Emergency: cancel all open orders and close all positions."""
    details: list[str] = []

    # Cancel open orders
    open_orders = await broker.get_open_orders()
    cancelled = 0
    for order in open_orders:
        try:
            await broker.cancel_order(order.order_id)
            details.append(f"Cancelled order {order.order_id} ({order.symbol})")
            cancelled += 1
        except Exception as exc:
            details.append(f"Failed to cancel {order.order_id}: {exc}")

    # Close all positions
    positions = await broker.get_positions()
    closed = 0
    for pos in positions:
        try:
            await broker.close_position(pos.symbol)
            details.append(f"Closed {pos.symbol}: {pos.quantity} shares")
            closed += 1
        except Exception as exc:
            details.append(f"Failed to close {pos.symbol}: {exc}")

    return KillSwitchResponse(
        cancelled_orders=cancelled,
        closed_positions=closed,
        details=details,
    )


@router.get("/trade-history", response_model=list[OrderResponse])
async def get_trade_history(
    limit: int = Query(default=50, ge=1, le=500),
    broker: PaperBroker = Depends(get_broker),
):
    """List filled orders sorted by date descending."""
    filled = [o for o in broker._orders.values() if o.status == OrderStatus.FILLED]
    filled.sort(key=lambda o: o.updated_at, reverse=True)
    return [_order_to_response(o) for o in filled[:limit]]
