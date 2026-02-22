"""Pydantic models for API request/response serialization."""

from datetime import datetime

from pydantic import BaseModel, Field

# ── Market ──────────────────────────────────────────────────────────────


class QuoteResponse(BaseModel):
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
    mid: float = 0.0
    spread: float = 0.0


class BarData(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class BarsResponse(BaseModel):
    symbol: str
    timeframe: str
    bars: list[BarData]


class UniverseResponse(BaseModel):
    categories: dict[str, list[str]]
    total: int


# ── Account / Trading ───────────────────────────────────────────────────


class AccountResponse(BaseModel):
    account_id: str
    broker: str
    currency: str
    balance: float
    equity: float
    buying_power: float
    cash: float
    portfolio_value: float
    day_trades_remaining: int | None = None
    leverage: float = 1.0
    is_paper: bool = True


class PositionResponse(BaseModel):
    symbol: str
    quantity: float
    side: str
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class OrderResponse(BaseModel):
    order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    status: str
    limit_price: float | None = None
    stop_price: float | None = None
    filled_quantity: float = 0.0
    filled_avg_price: float = 0.0
    created_at: datetime
    updated_at: datetime


class TradeRequest(BaseModel):
    symbol: str
    quantity: float = Field(gt=0)
    order_type: str = "market"
    limit_price: float | None = None


# ── Analysis ────────────────────────────────────────────────────────────


class TradePlanResponse(BaseModel):
    symbol: str
    action: str
    position_size: int
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_amount: float
    reward_amount: float
    rr_ratio: float
    validation: str | None = None


class SignalResponse(BaseModel):
    action: str
    confidence: float
    strategy: str | None = None
    bullish_signals: list[str] = []
    bearish_signals: list[str] = []


class AnalysisResponse(BaseModel):
    symbol: str
    timestamp: datetime
    current_price: float | None = None
    indicators: dict | None = None
    signal: SignalResponse | None = None
    ai_analysis: dict | None = None
    trade_plan: TradePlanResponse | None = None
    mode: str = "analysis"
    error: str | None = None


class BatchAnalysisRequest(BaseModel):
    symbols: list[str]


# ── Scanner ─────────────────────────────────────────────────────────────


class ScannerRequest(BaseModel):
    symbols: list[str] | None = None
    strategy: str = "combo"


class ScannerResultItem(BaseModel):
    symbol: str
    price: float | None = None
    action: str
    confidence: float
    rsi: float | None = None
    macd_trend: str | None = None
    change_pct: float | None = None


class ScannerResponse(BaseModel):
    total: int
    buy_signals: int
    sell_signals: int
    hold_signals: int
    avg_confidence: float
    results: list[ScannerResultItem]


# ── Risk ────────────────────────────────────────────────────────────────


class PositionSizeRequest(BaseModel):
    entry_price: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    win_probability: float = Field(ge=0, le=1, default=0.5)
    rr_ratio: float = Field(gt=0, default=2.0)
    portfolio_value: float = Field(gt=0, default=10000.0)


class PositionSizeResponse(BaseModel):
    shares: int
    position_value: float
    risk_amount: float
    risk_pct: float
    kelly_fraction: float


class StopLossRequest(BaseModel):
    entry_price: float = Field(gt=0)
    atr: float = Field(gt=0)
    direction: str = "long"


class StopLossResponse(BaseModel):
    stop_loss: float
    distance: float
    distance_pct: float


class TakeProfitRequest(BaseModel):
    entry_price: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    rr_ratio: float = Field(ge=1.5, default=2.0)


class TakeProfitResponse(BaseModel):
    take_profit: float
    distance: float
    distance_pct: float
    rr_ratio: float


class ValidateTradeRequest(BaseModel):
    position_size: int = Field(gt=0)
    entry_price: float = Field(gt=0)
    current_exposure: float = Field(ge=0, le=1, default=0.0)
    portfolio_value: float = Field(gt=0, default=10000.0)


class ValidateTradeResponse(BaseModel):
    is_valid: bool
    message: str


# ── Backtest ────────────────────────────────────────────────────────────


class BacktestRunSummary(BaseModel):
    run_id: str
    strategy_id: str
    symbols: list[str]
    start_date: datetime
    end_date: datetime
    initial_capital: float
    created_at: datetime
    metrics: dict[str, float]


class BacktestRunDetail(BacktestRunSummary):
    strategy_params: dict
    benchmark: str
    data_version: str
    code_version: str


class MonteCarloRequest(BaseModel):
    run_id: str | None = None
    trade_returns: list[float] | None = None
    initial_capital: float = 10000.0
    n_simulations: int = Field(default=1000, ge=100, le=10000)
    ruin_threshold: float = Field(default=0.5, gt=0, lt=1)


class MonteCarloResponse(BaseModel):
    n_simulations: int
    initial_capital: float
    probability_of_ruin: float
    ruin_threshold: float
    percentiles: dict[str, dict[str, float]]
    summary: str


class StressTestRequest(BaseModel):
    run_id: str


class ScenarioResultResponse(BaseModel):
    scenario_name: str
    start_date: str
    end_date: str
    benchmark_decline: float
    strategy_return: float
    benchmark_return: float
    max_drawdown: float
    recovery_days: int | None
    outperformance: float


class StressTestResponse(BaseModel):
    strategy_name: str
    resilience_score: float
    results: list[ScenarioResultResponse]
    summary: str


class SensitivityRequest(BaseModel):
    run_id: str
    target_metric: str = "sharpe_ratio"


class ParameterSensitivityResponse(BaseModel):
    param_name: str
    base_value: float
    is_fragile: bool
    degradation_20pct: float
    degradation_50pct: float


class SensitivityResponse(BaseModel):
    strategy_name: str
    robustness_score: float
    base_metrics: dict[str, float]
    fragile_params: list[str]
    parameters: list[ParameterSensitivityResponse]
    summary: str


# ── Signals ────────────────────────────────────────────────────────────


class AggregatedSignalItem(BaseModel):
    symbol: str
    action: str
    confidence: float
    strategy: str | None = None
    price: float | None = None


class AggregatedSignalsResponse(BaseModel):
    total: int
    buy_signals: int
    sell_signals: int
    results: list[AggregatedSignalItem]


# ── Portfolio Metrics ──────────────────────────────────────────────────


class PortfolioMetricsResponse(BaseModel):
    equity: float
    cash: float
    unrealized_pnl: float
    exposure: float
    max_position_pct: float
    total_trades: int
    win_rate: float | None = None
    profit_factor: float | None = None


# ── Kill Switch ────────────────────────────────────────────────────────


class KillSwitchResponse(BaseModel):
    cancelled_orders: int
    closed_positions: int
    details: list[str]
