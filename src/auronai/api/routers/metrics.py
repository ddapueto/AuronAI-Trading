"""Portfolio metrics endpoint."""

import logging

from fastapi import APIRouter, Depends

from auronai.api.dependencies import get_broker
from auronai.api.schemas import PortfolioMetricsResponse
from auronai.brokers.models import OrderStatus
from auronai.brokers.paper_broker import PaperBroker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/", response_model=PortfolioMetricsResponse)
async def get_metrics(broker: PaperBroker = Depends(get_broker)):
    """Get portfolio metrics: equity, cash, P&L, exposure, trade stats."""
    account = await broker.get_account()
    positions = await broker.get_positions()

    unrealized_pnl = sum(p.unrealized_pnl for p in positions)
    total_market_value = sum(abs(p.market_value) for p in positions)
    exposure = total_market_value / account.equity if account.equity > 0 else 0.0
    max_position_pct = (
        max(abs(p.market_value) / account.equity for p in positions)
        if positions and account.equity > 0
        else 0.0
    )

    filled_orders = [o for o in broker._orders.values() if o.status == OrderStatus.FILLED]
    total_trades = len(filled_orders)

    # TODO: PaperBroker doesn't track realized P&L per trade yet,
    # so win_rate and profit_factor cannot be computed accurately.
    win_rate = None
    profit_factor = None

    return PortfolioMetricsResponse(
        equity=account.equity,
        cash=account.cash,
        unrealized_pnl=round(unrealized_pnl, 2),
        exposure=round(exposure, 4),
        max_position_pct=round(max_position_pct, 4),
        total_trades=total_trades,
        win_rate=win_rate,
        profit_factor=profit_factor,
    )
