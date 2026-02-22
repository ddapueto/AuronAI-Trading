"""Symbol analysis endpoints — single and batch analysis via TradingAgent."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from auronai.agents.trading_agent import TradingAgent
from auronai.api.dependencies import get_agent
from auronai.api.schemas import (
    AnalysisResponse,
    BatchAnalysisRequest,
    SignalResponse,
    TradePlanResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def _to_analysis_response(result: dict) -> AnalysisResponse:
    """Convert TradingAgent result dict to AnalysisResponse."""
    signal = None
    if result.get("signal"):
        s = result["signal"]
        signal = SignalResponse(
            action=s.get("action", "HOLD"),
            confidence=s.get("confidence", 0),
            strategy=s.get("strategy"),
            bullish_signals=s.get("bullish_signals", []),
            bearish_signals=s.get("bearish_signals", []),
        )

    trade_plan = None
    if result.get("trade_plan"):
        tp = result["trade_plan"]
        trade_plan = TradePlanResponse(**tp)

    return AnalysisResponse(
        symbol=result["symbol"],
        timestamp=result["timestamp"],
        current_price=result.get("current_price"),
        indicators=result.get("indicators"),
        signal=signal,
        ai_analysis=result.get("ai_analysis"),
        trade_plan=trade_plan,
        mode=result.get("mode", "analysis"),
        error=result.get("error"),
    )


@router.get("/{symbol}", response_model=AnalysisResponse)
async def analyze_symbol(
    symbol: str,
    agent: TradingAgent = Depends(get_agent),
):
    """Run full analysis for a single symbol."""
    try:
        result = agent.analyze_symbol(symbol.upper())
        return _to_analysis_response(result)
    except Exception as exc:
        logger.error("Analysis failed for %s: %s", symbol, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/batch", response_model=list[AnalysisResponse])
async def analyze_batch(
    body: BatchAnalysisRequest,
    agent: TradingAgent = Depends(get_agent),
):
    """Run analysis for multiple symbols."""
    if not body.symbols:
        raise HTTPException(status_code=422, detail="symbols list is empty")
    if len(body.symbols) > 20:
        raise HTTPException(
            status_code=422,
            detail="Maximum 20 symbols per batch request",
        )
    results: list[AnalysisResponse] = []
    for sym in body.symbols:
        try:
            result = agent.analyze_symbol(sym.upper())
            results.append(_to_analysis_response(result))
        except Exception as exc:
            logger.error("Batch analysis failed for %s: %s", sym, exc)
            results.append(
                AnalysisResponse(
                    symbol=sym.upper(),
                    timestamp=result.get("timestamp") if "result" in dir() else None,
                    error=str(exc),
                )
            )
    return results
