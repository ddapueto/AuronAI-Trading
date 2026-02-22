"""Risk management endpoints — position sizing, stop loss, take profit."""

from fastapi import APIRouter, HTTPException

from auronai.api.schemas import (
    PositionSizeRequest,
    PositionSizeResponse,
    StopLossRequest,
    StopLossResponse,
    TakeProfitRequest,
    TakeProfitResponse,
    ValidateTradeRequest,
    ValidateTradeResponse,
)
from auronai.risk.risk_manager import RiskManager

router = APIRouter(prefix="/api/risk", tags=["risk"])


def _build_rm(portfolio_value: float) -> RiskManager:
    return RiskManager(portfolio_value=portfolio_value)


@router.post("/position-size", response_model=PositionSizeResponse)
async def calc_position_size(body: PositionSizeRequest):
    """Calculate optimal position size via Kelly Criterion."""
    rm = _build_rm(body.portfolio_value)

    shares = rm.calculate_position_size(
        entry_price=body.entry_price,
        stop_loss=body.stop_loss,
        win_probability=body.win_probability,
        rr_ratio=body.rr_ratio,
    )

    # Reproduce kelly fraction for response
    kelly = (body.win_probability * body.rr_ratio - (1 - body.win_probability)) / body.rr_ratio
    kelly = max(kelly, 0.0)

    risk_per_share = abs(body.entry_price - body.stop_loss)
    risk_amount = shares * risk_per_share
    risk_pct = risk_amount / body.portfolio_value if body.portfolio_value else 0

    return PositionSizeResponse(
        shares=shares,
        position_value=round(shares * body.entry_price, 2),
        risk_amount=round(risk_amount, 2),
        risk_pct=round(risk_pct, 4),
        kelly_fraction=round(kelly, 4),
    )


@router.post("/stop-loss", response_model=StopLossResponse)
async def calc_stop_loss(body: StopLossRequest):
    """Calculate ATR-based stop loss."""
    rm = _build_rm(10_000)  # portfolio value not needed for SL calc

    sl = rm.calculate_stop_loss(
        entry_price=body.entry_price,
        atr=body.atr,
        direction=body.direction,
    )
    if sl is None:
        raise HTTPException(status_code=422, detail="Invalid inputs for stop loss")

    distance = abs(body.entry_price - sl)
    distance_pct = distance / body.entry_price

    return StopLossResponse(
        stop_loss=sl,
        distance=round(distance, 2),
        distance_pct=round(distance_pct, 4),
    )


@router.post("/take-profit", response_model=TakeProfitResponse)
async def calc_take_profit(body: TakeProfitRequest):
    """Calculate take profit level from R/R ratio."""
    rm = _build_rm(10_000)

    tp = rm.calculate_take_profit(
        entry_price=body.entry_price,
        stop_loss=body.stop_loss,
        rr_ratio=body.rr_ratio,
    )
    if tp is None:
        raise HTTPException(status_code=422, detail="Invalid inputs for take profit")

    distance = abs(tp - body.entry_price)
    distance_pct = distance / body.entry_price

    return TakeProfitResponse(
        take_profit=tp,
        distance=round(distance, 2),
        distance_pct=round(distance_pct, 4),
        rr_ratio=body.rr_ratio,
    )


@router.post("/validate", response_model=ValidateTradeResponse)
async def validate_trade(body: ValidateTradeRequest):
    """Validate if a trade meets risk criteria."""
    rm = _build_rm(body.portfolio_value)

    is_valid, message = rm.validate_trade(
        position_size=body.position_size,
        entry_price=body.entry_price,
        current_exposure=body.current_exposure,
    )

    return ValidateTradeResponse(is_valid=is_valid, message=message)
