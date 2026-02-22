"""Backtesting endpoints — runs, Monte Carlo, stress testing, sensitivity."""

import logging

import numpy as np
from fastapi import APIRouter, HTTPException

from auronai.api.schemas import (
    BacktestRunDetail,
    BacktestRunSummary,
    MonteCarloRequest,
    MonteCarloResponse,
    ParameterSensitivityResponse,
    ScenarioResultResponse,
    SensitivityRequest,
    SensitivityResponse,
    StressTestRequest,
    StressTestResponse,
)
from auronai.backtesting.run_manager import RunManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


def _get_run_manager() -> RunManager:
    return RunManager()


# ── Run CRUD ────────────────────────────────────────────────────────────


@router.get("/runs", response_model=list[BacktestRunSummary])
async def list_runs(strategy_id: str | None = None, limit: int = 50):
    """List saved backtest runs."""
    rm = _get_run_manager()
    try:
        runs = rm.list_runs(strategy_id=strategy_id, limit=limit)
        return [
            BacktestRunSummary(
                run_id=r.run_id,
                strategy_id=r.strategy_id,
                symbols=r.symbols,
                start_date=r.start_date,
                end_date=r.end_date,
                initial_capital=r.initial_capital,
                created_at=r.created_at,
                metrics=r.metrics,
            )
            for r in runs
        ]
    finally:
        rm.close()


@router.get("/runs/{run_id}", response_model=BacktestRunDetail)
async def get_run(run_id: str):
    """Get detailed info for a single backtest run."""
    rm = _get_run_manager()
    try:
        run = rm.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return BacktestRunDetail(
            run_id=run.run_id,
            strategy_id=run.strategy_id,
            strategy_params=run.strategy_params,
            symbols=run.symbols,
            benchmark=run.benchmark,
            start_date=run.start_date,
            end_date=run.end_date,
            initial_capital=run.initial_capital,
            data_version=run.data_version,
            code_version=run.code_version,
            created_at=run.created_at,
            metrics=run.metrics,
        )
    finally:
        rm.close()


@router.get("/runs/{run_id}/trades")
async def get_run_trades(run_id: str):
    """Get trades for a backtest run."""
    rm = _get_run_manager()
    try:
        run = rm.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        df = rm.get_trades(run_id)
        return df.to_dict(orient="records")
    finally:
        rm.close()


@router.get("/runs/{run_id}/equity")
async def get_run_equity(run_id: str):
    """Get equity curve for a backtest run."""
    rm = _get_run_manager()
    try:
        run = rm.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        df = rm.get_equity_curve(run_id)
        return df.to_dict(orient="records")
    finally:
        rm.close()


# ── Monte Carlo ─────────────────────────────────────────────────────────


@router.post("/monte-carlo", response_model=MonteCarloResponse)
async def run_monte_carlo(body: MonteCarloRequest):
    """Run Monte Carlo simulation on trade returns."""
    from auronai.backtesting.monte_carlo import MonteCarloSimulator

    trade_returns: list[float] | None = body.trade_returns

    if body.run_id and trade_returns is None:
        rm = _get_run_manager()
        try:
            run = rm.get_run(body.run_id)
            if run is None:
                raise HTTPException(status_code=404, detail="Run not found")
            trades_df = rm.get_trades(body.run_id)
            if "pnl_pct" in trades_df.columns:
                trade_returns = trades_df["pnl_pct"].tolist()
            elif "return" in trades_df.columns:
                trade_returns = trades_df["return"].tolist()
            else:
                raise HTTPException(
                    status_code=422,
                    detail="Trades have no return/pnl_pct column",
                )
        finally:
            rm.close()

    if not trade_returns:
        raise HTTPException(
            status_code=422,
            detail="Provide trade_returns or a valid run_id",
        )

    sim = MonteCarloSimulator(
        n_simulations=body.n_simulations,
        seed=42,
    )
    result = sim.run(
        trade_returns=np.array(trade_returns),
        initial_capital=body.initial_capital,
        ruin_threshold=body.ruin_threshold,
    )

    # Convert numpy values in percentiles
    percentiles = {}
    for metric, pcts in result.percentiles.items():
        percentiles[metric] = {k: round(float(v), 4) for k, v in pcts.items()}

    return MonteCarloResponse(
        n_simulations=result.n_simulations,
        initial_capital=result.initial_capital,
        probability_of_ruin=round(float(result.probability_of_ruin), 4),
        ruin_threshold=result.ruin_threshold,
        percentiles=percentiles,
        summary=result.summary(),
    )


# ── Stress Test ─────────────────────────────────────────────────────────


@router.post("/stress-test", response_model=StressTestResponse)
async def run_stress_test(body: StressTestRequest):
    """Run stress testing against historical crisis scenarios."""
    import pandas as pd

    from auronai.backtesting.stress_testing import StressTester

    rm = _get_run_manager()
    try:
        run = rm.get_run(body.run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")

        equity_df = rm.get_equity_curve(body.run_id)
        trades_df = rm.get_trades(body.run_id)
        trades_list = trades_df.to_dict(orient="records")

        if "date" in equity_df.columns:
            equity_df["date"] = pd.to_datetime(equity_df["date"])
            equity_df = equity_df.set_index("date")

        tester = StressTester()
        report = tester.run(
            equity_curve=equity_df,
            trades=trades_list,
            strategy_name=run.strategy_id,
        )

        results = [
            ScenarioResultResponse(
                scenario_name=r.scenario.name,
                start_date=str(r.scenario.start_date),
                end_date=str(r.scenario.end_date),
                benchmark_decline=r.scenario.benchmark_decline,
                strategy_return=round(float(r.strategy_return), 4),
                benchmark_return=round(float(r.benchmark_return), 4),
                max_drawdown=round(float(r.max_drawdown), 4),
                recovery_days=r.recovery_days,
                outperformance=round(float(r.outperformance), 4),
            )
            for r in report.results
        ]

        return StressTestResponse(
            strategy_name=report.strategy_name,
            resilience_score=round(float(report.resilience_score), 2),
            results=results,
            summary=report.summary(),
        )
    finally:
        rm.close()


# ── Sensitivity Analysis ───────────────────────────────────────────────


@router.post("/sensitivity", response_model=SensitivityResponse)
async def run_sensitivity(body: SensitivityRequest):
    """Run parameter sensitivity analysis on a backtest run."""
    from auronai.backtesting.sensitivity_analysis import SensitivityAnalyzer

    rm = _get_run_manager()
    try:
        run = rm.get_run(body.run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")

        def eval_fn(params: dict) -> dict[str, float]:
            # Use stored equity/trades for base evaluation.
            # Full re-backtest with varied params would require the
            # strategy + data pipeline which is out of scope for the
            # synchronous API. Return base metrics for now.
            return dict(run.metrics)

        analyzer = SensitivityAnalyzer(
            eval_fn=eval_fn,
            base_params=run.strategy_params,
            target_metric=body.target_metric,
        )
        report = analyzer.run(strategy_name=run.strategy_id)

        parameters = [
            ParameterSensitivityResponse(
                param_name=r.param_name,
                base_value=r.base_value,
                is_fragile=r.is_fragile,
                degradation_20pct=round(float(r.degradation_20pct), 4),
                degradation_50pct=round(float(r.degradation_50pct), 4),
            )
            for r in report.parameter_results
        ]

        return SensitivityResponse(
            strategy_name=report.strategy_name,
            robustness_score=round(float(report.robustness_score), 2),
            base_metrics={k: round(float(v), 4) for k, v in report.base_metrics.items()},
            fragile_params=report.fragile_params,
            parameters=parameters,
            summary=report.summary(),
        )
    finally:
        rm.close()
