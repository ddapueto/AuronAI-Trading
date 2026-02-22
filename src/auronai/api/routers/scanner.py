"""Signal scanner — scan multiple symbols and rank by confidence."""

import logging

from fastapi import APIRouter, Depends

from auronai.agents.trading_agent import TradingAgent
from auronai.api.dependencies import get_agent, get_universe
from auronai.api.schemas import ScannerRequest, ScannerResponse, ScannerResultItem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scanner", tags=["scanner"])


@router.post("/run", response_model=ScannerResponse)
async def run_scanner(
    body: ScannerRequest,
    agent: TradingAgent = Depends(get_agent),
    universe: dict = Depends(get_universe),
):
    """Scan symbols and rank by signal confidence."""
    symbols = body.symbols
    if not symbols:
        symbols = [s for cat in universe.values() for s in cat]

    items: list[ScannerResultItem] = []
    for sym in symbols:
        try:
            result = agent.analyze_symbol(sym.upper())
            signal = result.get("signal", {})
            indicators = result.get("indicators", {})

            rsi_val = None
            if "rsi" in indicators and isinstance(indicators["rsi"], dict):
                rsi_val = indicators["rsi"].get("value")

            macd_trend = None
            if "macd" in indicators and isinstance(indicators["macd"], dict):
                macd_trend = indicators["macd"].get("trend")

            change_pct = None
            price = result.get("current_price")
            if price and indicators:
                prev = indicators.get("prev_close")
                if prev and prev > 0:
                    change_pct = ((price - prev) / prev) * 100

            items.append(
                ScannerResultItem(
                    symbol=sym.upper(),
                    price=price,
                    action=signal.get("action", "HOLD"),
                    confidence=signal.get("confidence", 0),
                    rsi=rsi_val,
                    macd_trend=macd_trend,
                    change_pct=change_pct,
                )
            )
        except Exception as exc:
            logger.error("Scanner failed for %s: %s", sym, exc)
            items.append(
                ScannerResultItem(
                    symbol=sym.upper(),
                    action="HOLD",
                    confidence=0,
                )
            )

    # Sort by confidence descending
    items.sort(key=lambda x: x.confidence, reverse=True)

    buy = sum(1 for i in items if i.action == "BUY")
    sell = sum(1 for i in items if i.action == "SELL")
    hold = sum(1 for i in items if i.action == "HOLD")
    avg_conf = sum(i.confidence for i in items) / len(items) if items else 0

    return ScannerResponse(
        total=len(items),
        buy_signals=buy,
        sell_signals=sell,
        hold_signals=hold,
        avg_confidence=round(avg_conf, 2),
        results=items,
    )
