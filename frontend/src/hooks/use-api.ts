"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  PositionSizeRequest,
  StopLossRequest,
  TakeProfitRequest,
  MonteCarloRequest,
} from "@/lib/api";

// ── Market ──────────────────────────────────────────────────────────────

export function useQuote(symbol: string) {
  return useQuery({
    queryKey: ["quote", symbol],
    queryFn: () => api.getQuote(symbol),
    enabled: !!symbol,
    refetchInterval: 30_000,
  });
}

export function useBars(symbol: string, timeframe = "1d", limit = 200) {
  return useQuery({
    queryKey: ["bars", symbol, timeframe, limit],
    queryFn: () => api.getBars(symbol, timeframe, limit),
    enabled: !!symbol,
  });
}

export function useUniverse() {
  return useQuery({
    queryKey: ["universe"],
    queryFn: api.getUniverse,
    staleTime: 5 * 60_000,
  });
}

// ── Analysis ────────────────────────────────────────────────────────────

export function useAnalysis(symbol: string) {
  return useQuery({
    queryKey: ["analysis", symbol],
    queryFn: () => api.analyzeSymbol(symbol),
    enabled: !!symbol,
    staleTime: 60_000,
  });
}

// ── Scanner ─────────────────────────────────────────────────────────────

export function useScanner() {
  return useMutation({
    mutationFn: (params: { symbols?: string[]; strategy?: string }) =>
      api.runScanner(params.symbols, params.strategy),
  });
}

// ── Trading ─────────────────────────────────────────────────────────────

export function useAccount() {
  return useQuery({
    queryKey: ["account"],
    queryFn: api.getAccount,
    refetchInterval: 15_000,
  });
}

export function usePositions() {
  return useQuery({
    queryKey: ["positions"],
    queryFn: api.getPositions,
    refetchInterval: 15_000,
  });
}

export function useOrders() {
  return useQuery({
    queryKey: ["orders"],
    queryFn: api.getOrders,
    refetchInterval: 15_000,
  });
}

export function useBuy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { symbol: string; quantity: number }) =>
      api.buy(data.symbol, data.quantity),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["account"] });
      qc.invalidateQueries({ queryKey: ["positions"] });
    },
  });
}

export function useSell() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { symbol: string; quantity: number }) =>
      api.sell(data.symbol, data.quantity),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["account"] });
      qc.invalidateQueries({ queryKey: ["positions"] });
    },
  });
}

export function useClosePosition() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => api.closePosition(symbol),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["account"] });
      qc.invalidateQueries({ queryKey: ["positions"] });
    },
  });
}

// ── Risk ────────────────────────────────────────────────────────────────

export function usePositionSize() {
  return useMutation({
    mutationFn: (data: PositionSizeRequest) => api.calcPositionSize(data),
  });
}

export function useStopLoss() {
  return useMutation({
    mutationFn: (data: StopLossRequest) => api.calcStopLoss(data),
  });
}

export function useTakeProfit() {
  return useMutation({
    mutationFn: (data: TakeProfitRequest) => api.calcTakeProfit(data),
  });
}

// ── Backtest ────────────────────────────────────────────────────────────

export function useBacktestRuns() {
  return useQuery({
    queryKey: ["backtest-runs"],
    queryFn: api.listRuns,
  });
}

export function useBacktestRun(runId: string) {
  return useQuery({
    queryKey: ["backtest-run", runId],
    queryFn: () => api.getRun(runId),
    enabled: !!runId,
  });
}

export function useMonteCarlo() {
  return useMutation({
    mutationFn: (data: MonteCarloRequest) => api.runMonteCarlo(data),
  });
}

export function useStressTest() {
  return useMutation({
    mutationFn: (runId: string) => api.runStressTest(runId),
  });
}

// ── Signals ────────────────────────────────────────────────────────────

export function useSignals(limit = 20) {
  return useQuery({
    queryKey: ["signals", limit],
    queryFn: () => api.getSignals(limit),
    refetchInterval: 60_000,
  });
}

// ── Metrics ────────────────────────────────────────────────────────────

export function useMetrics() {
  return useQuery({
    queryKey: ["metrics"],
    queryFn: api.getMetrics,
    refetchInterval: 30_000,
  });
}

// ── Kill Switch ────────────────────────────────────────────────────────

export function useKillSwitch() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.killSwitch(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["account"] });
      qc.invalidateQueries({ queryKey: ["positions"] });
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["metrics"] });
    },
  });
}

// ── Trade History ──────────────────────────────────────────────────────

export function useTradeHistory() {
  return useQuery({
    queryKey: ["trade-history"],
    queryFn: () => api.getTradeHistory(),
    refetchInterval: 30_000,
  });
}

// ── Health ──────────────────────────────────────────────────────────────

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 30_000,
    retry: false,
  });
}
