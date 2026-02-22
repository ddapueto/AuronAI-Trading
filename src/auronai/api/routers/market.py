"""Market data endpoints — quotes, bars, symbol universe."""

from fastapi import APIRouter, Depends, HTTPException, Query

from auronai.api.dependencies import get_broker, get_universe
from auronai.api.schemas import (
    BarData,
    BarsResponse,
    QuoteResponse,
    SymbolMetadataItem,
    UniverseDetailedResponse,
    UniverseResponse,
)
from auronai.brokers.paper_broker import PaperBroker
from auronai.data.symbol_universe import SYMBOL_METADATA, SYMBOL_UNIVERSE

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/quote/{symbol}", response_model=QuoteResponse)
async def get_quote(
    symbol: str,
    broker: PaperBroker = Depends(get_broker),
):
    """Get real-time quote for a symbol."""
    try:
        q = await broker.get_quote(symbol.upper())
        return QuoteResponse(
            symbol=q.symbol,
            bid=q.bid,
            ask=q.ask,
            last=q.last,
            volume=q.volume,
            timestamp=q.timestamp,
            high=q.high,
            low=q.low,
            open=q.open,
            prev_close=q.prev_close,
            mid=q.mid,
            spread=q.spread,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/bars/{symbol}", response_model=BarsResponse)
async def get_bars(
    symbol: str,
    timeframe: str = Query("1d", pattern="^(1m|5m|15m|1h|1d|1wk)$"),
    period: str = Query("3mo"),
    limit: int = Query(200, ge=1, le=2000),
    broker: PaperBroker = Depends(get_broker),
):
    """Get OHLCV bar data for a symbol."""
    try:
        df = await broker.get_bars(
            symbol.upper(),
            timeframe=timeframe,
            limit=limit,
        )
        bars = [
            BarData(
                timestamp=str(idx),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row.get("volume", 0)),
            )
            for idx, row in df.iterrows()
        ]
        return BarsResponse(
            symbol=symbol.upper(),
            timeframe=timeframe,
            bars=bars,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/universe", response_model=UniverseResponse)
async def get_symbol_universe(
    universe: dict = Depends(get_universe),
):
    """Get the symbol universe by category."""
    total = sum(len(v) for v in universe.values())
    return UniverseResponse(categories=universe, total=total)


@router.get(
    "/universe/detailed",
    response_model=UniverseDetailedResponse,
)
async def get_symbol_universe_detailed():
    """Get the symbol universe with enriched metadata per symbol."""
    total = sum(len(v) for v in SYMBOL_UNIVERSE.values())
    metadata = {
        sym: SymbolMetadataItem(
            symbol=info.symbol,
            asset_type=info.asset_type.value,
            sector=info.sector,
            beta_estimate=info.beta_estimate,
            min_volume=info.min_volume,
            is_pdt_safe=info.is_pdt_safe,
            cfd_available=info.cfd_available,
            leverage_warning=info.leverage_warning,
        )
        for sym, info in SYMBOL_METADATA.items()
    }
    return UniverseDetailedResponse(
        categories=SYMBOL_UNIVERSE,
        total=total,
        metadata=metadata,
    )
