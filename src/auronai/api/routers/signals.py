"""Aggregated signals — scan universe and return BUY/SELL signals only."""

import logging

from fastapi import APIRouter, Depends, Query

from auronai.agents.trading_agent import TradingAgent
from auronai.api.dependencies import get_agent, get_universe
from auronai.api.schemas import AggregatedSignalItem, AggregatedSignalsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("/", response_model=AggregatedSignalsResponse)
async def get_signals(
    limit: int = Query(default=20, ge=1, le=100),
    agent: TradingAgent = Depends(get_agent),
    universe: dict = Depends(get_universe),
):
    """Scan universe and return top BUY/SELL signals ranked by confidence."""
    symbols = [s for cat in universe.values() for s in cat]

    items: list[AggregatedSignalItem] = []
    for sym in symbols:
        try:
            result = agent.analyze_symbol(sym.upper())
            signal = result.get("signal", {})
            action = signal.get("action", "HOLD")
            if action == "HOLD":
                continue
            items.append(
                AggregatedSignalItem(
                    symbol=sym.upper(),
                    action=action,
                    confidence=signal.get("confidence", 0),
                    strategy=signal.get("strategy"),
                    price=result.get("current_price"),
                )
            )
        except Exception as exc:
            logger.error("Signal scan failed for %s: %s", sym, exc)

    items.sort(key=lambda x: x.confidence, reverse=True)
    items = items[:limit]

    return AggregatedSignalsResponse(
        total=len(items),
        buy_signals=sum(1 for i in items if i.action == "BUY"),
        sell_signals=sum(1 for i in items if i.action == "SELL"),
        results=items,
    )
