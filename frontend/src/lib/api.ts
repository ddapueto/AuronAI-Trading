const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetcher<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

// ── Market ──────────────────────────────────────────────────────────────

export const api = {
  // Market
  getQuote: (symbol: string) =>
    fetcher<Quote>(`/api/market/quote/${symbol}`),
  getBars: (symbol: string, timeframe = "1d", limit = 200) =>
    fetcher<BarsResponse>(`/api/market/bars/${symbol}?timeframe=${timeframe}&limit=${limit}`),
  getUniverse: () =>
    fetcher<UniverseResponse>("/api/market/universe"),

  // Analysis
  analyzeSymbol: (symbol: string) =>
    fetcher<AnalysisResponse>(`/api/analysis/${symbol}`),
  analyzeBatch: (symbols: string[]) =>
    fetcher<AnalysisResponse[]>("/api/analysis/batch", {
      method: "POST",
      body: JSON.stringify({ symbols }),
    }),

  // Scanner
  runScanner: (symbols?: string[], strategy = "combo") =>
    fetcher<ScannerResponse>("/api/scanner/run", {
      method: "POST",
      body: JSON.stringify({ symbols, strategy }),
    }),

  // Trading
  getAccount: () =>
    fetcher<AccountResponse>("/api/trading/account"),
  getPositions: () =>
    fetcher<PositionResponse[]>("/api/trading/positions"),
  buy: (symbol: string, quantity: number) =>
    fetcher<OrderResponse>("/api/trading/buy", {
      method: "POST",
      body: JSON.stringify({ symbol, quantity }),
    }),
  sell: (symbol: string, quantity: number) =>
    fetcher<OrderResponse>("/api/trading/sell", {
      method: "POST",
      body: JSON.stringify({ symbol, quantity }),
    }),
  closePosition: (symbol: string) =>
    fetcher<OrderResponse>(`/api/trading/close/${symbol}`, { method: "POST" }),
  closeAll: () =>
    fetcher<OrderResponse[]>("/api/trading/close-all", { method: "POST" }),
  getOrders: () =>
    fetcher<OrderResponse[]>("/api/trading/orders"),

  // Risk
  calcPositionSize: (data: PositionSizeRequest) =>
    fetcher<PositionSizeResponse>("/api/risk/position-size", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  calcStopLoss: (data: StopLossRequest) =>
    fetcher<StopLossResponse>("/api/risk/stop-loss", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  calcTakeProfit: (data: TakeProfitRequest) =>
    fetcher<TakeProfitResponse>("/api/risk/take-profit", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Backtest
  listRuns: () =>
    fetcher<BacktestRunSummary[]>("/api/backtest/runs"),
  getRun: (runId: string) =>
    fetcher<BacktestRunDetail>(`/api/backtest/runs/${runId}`),
  getRunTrades: (runId: string) =>
    fetcher<Record<string, unknown>[]>(`/api/backtest/runs/${runId}/trades`),
  getRunEquity: (runId: string) =>
    fetcher<Record<string, unknown>[]>(`/api/backtest/runs/${runId}/equity`),
  runMonteCarlo: (data: MonteCarloRequest) =>
    fetcher<MonteCarloResponse>("/api/backtest/monte-carlo", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  runStressTest: (runId: string) =>
    fetcher<StressTestResponse>("/api/backtest/stress-test", {
      method: "POST",
      body: JSON.stringify({ run_id: runId }),
    }),

  // Signals
  getSignals: (limit = 20) =>
    fetcher<AggregatedSignalsResponse>(`/api/signals/?limit=${limit}`),

  // Metrics
  getMetrics: () =>
    fetcher<PortfolioMetricsResponse>("/api/metrics/"),

  // Kill Switch
  killSwitch: () =>
    fetcher<KillSwitchResponse>("/api/trading/kill-switch", { method: "POST" }),

  // Trade History
  getTradeHistory: (limit = 50) =>
    fetcher<OrderResponse[]>(`/api/trading/trade-history?limit=${limit}`),

  // Health
  health: () => fetcher<{ status: string }>("/api/health"),
};

// ── Types ───────────────────────────────────────────────────────────────

export interface Quote {
  symbol: string;
  bid: number;
  ask: number;
  last: number;
  volume: number;
  timestamp: string;
  high: number;
  low: number;
  open: number;
  prev_close: number;
  mid: number;
  spread: number;
}

export interface BarData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface BarsResponse {
  symbol: string;
  timeframe: string;
  bars: BarData[];
}

export interface UniverseResponse {
  categories: Record<string, string[]>;
  total: number;
}

export interface Signal {
  action: "BUY" | "SELL" | "HOLD";
  confidence: number;
  strategy?: string;
  bullish_signals: string[];
  bearish_signals: string[];
}

export interface TradePlan {
  symbol: string;
  action: string;
  position_size: number;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  risk_amount: number;
  reward_amount: number;
  rr_ratio: number;
  validation?: string;
}

export interface AnalysisResponse {
  symbol: string;
  timestamp: string;
  current_price?: number;
  indicators?: Record<string, unknown>;
  signal?: Signal;
  ai_analysis?: Record<string, unknown>;
  trade_plan?: TradePlan;
  mode: string;
  error?: string;
}

export interface ScannerResultItem {
  symbol: string;
  price?: number;
  action: string;
  confidence: number;
  rsi?: number;
  macd_trend?: string;
  change_pct?: number;
}

export interface ScannerResponse {
  total: number;
  buy_signals: number;
  sell_signals: number;
  hold_signals: number;
  avg_confidence: number;
  results: ScannerResultItem[];
}

export interface AccountResponse {
  account_id: string;
  broker: string;
  currency: string;
  balance: number;
  equity: number;
  buying_power: number;
  cash: number;
  portfolio_value: number;
  day_trades_remaining?: number;
  leverage: number;
  is_paper: boolean;
}

export interface PositionResponse {
  symbol: string;
  quantity: number;
  side: string;
  entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

export interface OrderResponse {
  order_id: string;
  symbol: string;
  side: string;
  order_type: string;
  quantity: number;
  status: string;
  limit_price?: number;
  stop_price?: number;
  filled_quantity: number;
  filled_avg_price: number;
  created_at: string;
  updated_at: string;
}

export interface PositionSizeRequest {
  entry_price: number;
  stop_loss: number;
  win_probability?: number;
  rr_ratio?: number;
  portfolio_value?: number;
}

export interface PositionSizeResponse {
  shares: number;
  position_value: number;
  risk_amount: number;
  risk_pct: number;
  kelly_fraction: number;
}

export interface StopLossRequest {
  entry_price: number;
  atr: number;
  direction?: string;
}

export interface StopLossResponse {
  stop_loss: number;
  distance: number;
  distance_pct: number;
}

export interface TakeProfitRequest {
  entry_price: number;
  stop_loss: number;
  rr_ratio?: number;
}

export interface TakeProfitResponse {
  take_profit: number;
  distance: number;
  distance_pct: number;
  rr_ratio: number;
}

export interface BacktestRunSummary {
  run_id: string;
  strategy_id: string;
  symbols: string[];
  start_date: string;
  end_date: string;
  initial_capital: number;
  created_at: string;
  metrics: Record<string, number>;
}

export interface BacktestRunDetail extends BacktestRunSummary {
  strategy_params: Record<string, unknown>;
  benchmark: string;
  data_version: string;
  code_version: string;
}

export interface MonteCarloRequest {
  run_id?: string;
  trade_returns?: number[];
  initial_capital?: number;
  n_simulations?: number;
  ruin_threshold?: number;
}

export interface MonteCarloResponse {
  n_simulations: number;
  initial_capital: number;
  probability_of_ruin: number;
  ruin_threshold: number;
  percentiles: Record<string, Record<string, number>>;
  summary: string;
}

export interface StressTestResponse {
  strategy_name: string;
  resilience_score: number;
  results: {
    scenario_name: string;
    start_date: string;
    end_date: string;
    benchmark_decline: number;
    strategy_return: number;
    benchmark_return: number;
    max_drawdown: number;
    recovery_days?: number;
    outperformance: number;
  }[];
  summary: string;
}

export interface AggregatedSignalItem {
  symbol: string;
  action: string;
  confidence: number;
  strategy?: string;
  price?: number;
}

export interface AggregatedSignalsResponse {
  total: number;
  buy_signals: number;
  sell_signals: number;
  results: AggregatedSignalItem[];
}

export interface PortfolioMetricsResponse {
  equity: number;
  cash: number;
  unrealized_pnl: number;
  exposure: number;
  max_position_pct: number;
  total_trades: number;
  win_rate?: number;
  profit_factor?: number;
}

export interface KillSwitchResponse {
  cancelled_orders: number;
  closed_positions: number;
  details: string[];
}
