"""End-to-end tests for Sprint 1 & 2 pipeline integration.

Validates that PaperBroker → Monte Carlo / Stress Testing / Sensitivity
components work together with compatible data formats.
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from auronai.backtesting.monte_carlo import MonteCarloSimulator
from auronai.backtesting.sensitivity_analysis import SensitivityAnalyzer
from auronai.backtesting.stress_testing import (
    CrisisScenario,
    StressTester,
)
from auronai.brokers.models import OrderStatus, Quote
from auronai.brokers.paper_broker import PaperBroker

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXED_PRICES: dict[str, float] = {
    "AAPL": 150.0,
    "MSFT": 300.0,
    "GOOGL": 2800.0,
    "TSLA": 200.0,
    "AMZN": 3300.0,
}


def _make_quote(symbol: str, price: float) -> Quote:
    """Build a deterministic Quote with no spread."""
    return Quote(
        symbol=symbol,
        bid=price,
        ask=price,
        last=price,
        volume=1_000_000,
        timestamp=datetime.now(),
    )


def _mock_get_quote(symbol: str) -> Quote:
    price = FIXED_PRICES.get(symbol, 100.0)
    return _make_quote(symbol, price)


async def _execute_trades(
    broker: PaperBroker,
    symbols: list[str],
    buy_price_map: dict[str, float],
    sell_price_map: dict[str, float],
) -> list[dict]:
    """Buy then sell each symbol, returning trade dicts with PnL."""
    trades: list[dict] = []
    for symbol in symbols:
        buy_p = buy_price_map[symbol]
        with patch.object(
            broker, "get_quote", new=AsyncMock(
                return_value=_make_quote(symbol, buy_p),
            ),
        ):
            buy_order = await broker.buy(symbol, 1.0)
        assert buy_order.status == OrderStatus.FILLED

        sell_p = sell_price_map[symbol]
        with patch.object(
            broker, "get_quote", new=AsyncMock(
                return_value=_make_quote(symbol, sell_p),
            ),
        ):
            sell_order = await broker.sell(symbol, 1.0)
        assert sell_order.status == OrderStatus.FILLED

        pnl_dollar = sell_p - buy_p
        pnl_pct = (pnl_dollar / buy_p) * 100
        trades.append({
            "symbol": symbol,
            "entry_date": buy_order.created_at.strftime("%Y-%m-%d"),
            "exit_date": sell_order.updated_at.strftime("%Y-%m-%d"),
            "pnl_dollar": pnl_dollar,
            "pnl_percent": pnl_pct,
        })
    return trades


# ---------------------------------------------------------------------------
# TestBrokerToAnalysisPipeline
# ---------------------------------------------------------------------------


class TestBrokerToAnalysisPipeline:
    """Validates that PaperBroker output feeds correctly into analysis modules."""

    @pytest.mark.asyncio
    async def test_full_pipeline_broker_to_monte_carlo(
        self, paper_broker: PaperBroker,
    ) -> None:
        """PaperBroker trades → Monte Carlo run_from_trades."""
        await paper_broker.connect()
        buy_prices = {
            "AAPL": 150.0, "MSFT": 300.0, "GOOGL": 2800.0,
            "TSLA": 200.0, "AMZN": 3300.0,
        }
        sell_prices = {
            "AAPL": 158.0, "MSFT": 290.0, "GOOGL": 2900.0,
            "TSLA": 180.0, "AMZN": 3400.0,
        }
        trades = await _execute_trades(
            paper_broker, list(buy_prices), buy_prices, sell_prices,
        )
        await paper_broker.disconnect()

        assert len(trades) >= 5

        sim = MonteCarloSimulator(n_simulations=100, seed=42)
        result = sim.run_from_trades(trades, initial_capital=10_000.0)

        assert result.n_simulations == 100
        assert "total_return" in result.percentiles
        assert isinstance(result.equity_curves, pd.DataFrame)
        assert result.equity_curves.shape[1] <= 100

    @pytest.mark.asyncio
    async def test_full_pipeline_broker_to_stress_test(
        self, synthetic_equity_curve: pd.DataFrame,
    ) -> None:
        """Equity curve with dates 2019-2021 → StressTester with COVID."""
        covid = CrisisScenario(
            name="COVID Crash",
            start=datetime(2020, 2, 19),
            end=datetime(2020, 3, 23),
            description="COVID-19 market crash",
            benchmark_drawdown=-0.34,
        )
        tester = StressTester(benchmark="SPY", scenarios=[covid])
        trades: list[dict] = []
        report = tester.run(
            synthetic_equity_curve, trades, "E2E Stress Strategy",
        )

        assert report.strategy_name == "E2E Stress Strategy"
        assert len(report.results) == 1

        scenario_result = report.results[0]
        assert scenario_result.scenario.name == "COVID Crash"
        assert isinstance(scenario_result.strategy_return, float)
        assert isinstance(scenario_result.max_drawdown, float)
        assert 0.0 <= report.resilience_score <= 100.0

    def test_full_pipeline_equity_curve_to_monte_carlo(
        self, synthetic_equity_curve: pd.DataFrame,
    ) -> None:
        """Equity curve → Monte Carlo run_from_equity_curve."""
        sim = MonteCarloSimulator(n_simulations=100, seed=42)
        result = sim.run_from_equity_curve(
            synthetic_equity_curve.rename(columns={"date": "idx"}).assign(
                equity=synthetic_equity_curve["equity"],
            )[["equity"]],
            initial_capital=10_000.0,
        )

        assert result.n_simulations == 100
        assert "total_return" in result.metric_distributions
        assert "max_drawdown" in result.metric_distributions
        assert result.percentiles["total_return"]["P05"] <= (
            result.percentiles["total_return"]["P95"]
        )

    def test_full_pipeline_sensitivity_with_eval_fn(self) -> None:
        """SensitivityAnalyzer with eval_fn that uses simulated trades."""

        def eval_fn(params: dict) -> dict[str, float]:
            lookback = params.get("lookback", 14)
            threshold = params.get("threshold", 30)
            # Simulate: sharpe degrades slightly with param changes
            base_sharpe = 1.5
            sharpe = base_sharpe - abs(lookback - 14) * 0.01
            sharpe -= abs(threshold - 30) * 0.005
            return {
                "sharpe_ratio": max(0.0, sharpe),
                "max_drawdown": -0.08,
                "win_rate": 0.60,
            }

        analyzer = SensitivityAnalyzer(
            eval_fn=eval_fn,
            base_params={"lookback": 14, "threshold": 30},
            target_metric="sharpe_ratio",
        )
        report = analyzer.run("E2E Sensitivity Strategy")

        assert report.strategy_name == "E2E Sensitivity Strategy"
        assert 0 <= report.robustness_score <= 100
        assert len(report.parameter_results) == 2
        assert report.base_metrics["sharpe_ratio"] == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# TestCrossComponentDataFlow
# ---------------------------------------------------------------------------


class TestCrossComponentDataFlow:
    """Verifies data format compatibility between components."""

    def test_trade_format_compatibility(
        self, synthetic_trades: list[dict],
    ) -> None:
        """Trade dicts from fixtures are compatible with Monte Carlo."""
        sim = MonteCarloSimulator(n_simulations=50, seed=42)
        result = sim.run_from_trades(synthetic_trades, initial_capital=10_000.0)

        assert result.n_simulations == 50
        assert "total_return" in result.percentiles
        assert result.probability_of_ruin >= 0.0

    def test_equity_curve_format_compatibility(
        self, synthetic_equity_curve: pd.DataFrame,
    ) -> None:
        """Equity curve format works for both Monte Carlo and Stress Tester."""
        # Monte Carlo accepts DataFrame with 'equity' column
        sim = MonteCarloSimulator(n_simulations=50, seed=42)
        mc_result = sim.run_from_equity_curve(
            synthetic_equity_curve[["equity"]],
        )
        assert mc_result.n_simulations == 50

        # Stress tester accepts DataFrame with 'date' + 'equity'
        covid = CrisisScenario(
            name="COVID Crash",
            start=datetime(2020, 2, 19),
            end=datetime(2020, 3, 23),
            description="Test",
            benchmark_drawdown=-0.34,
        )
        tester = StressTester(benchmark="SPY", scenarios=[covid])
        st_report = tester.run(synthetic_equity_curve, [])
        assert len(st_report.results) == 1

    def test_all_reports_generate_summary(
        self,
        synthetic_trades: list[dict],
        synthetic_equity_curve: pd.DataFrame,
    ) -> None:
        """All analysis reports produce non-empty summary strings."""
        # Monte Carlo
        sim = MonteCarloSimulator(n_simulations=50, seed=42)
        mc_result = sim.run_from_trades(synthetic_trades)
        mc_summary = mc_result.summary()
        assert isinstance(mc_summary, str)
        assert len(mc_summary) > 0
        assert "Monte Carlo" in mc_summary

        # Stress Test
        covid = CrisisScenario(
            name="COVID Crash",
            start=datetime(2020, 2, 19),
            end=datetime(2020, 3, 23),
            description="Test",
            benchmark_drawdown=-0.34,
        )
        tester = StressTester(benchmark="SPY", scenarios=[covid])
        st_report = tester.run(synthetic_equity_curve, synthetic_trades)
        st_summary = st_report.summary()
        assert isinstance(st_summary, str)
        assert len(st_summary) > 0
        assert "Stress Test" in st_summary

        # Sensitivity
        analyzer = SensitivityAnalyzer(
            eval_fn=lambda p: {"sharpe_ratio": 1.5},
            base_params={"lookback": 14},
        )
        sens_report = analyzer.run()
        sens_summary = sens_report.summary()
        assert isinstance(sens_summary, str)
        assert len(sens_summary) > 0
        assert "Sensitivity" in sens_summary

    def test_all_reports_generate_dataframe(
        self,
        synthetic_trades: list[dict],
        synthetic_equity_curve: pd.DataFrame,
    ) -> None:
        """All analysis reports produce valid DataFrames."""
        # Monte Carlo → get_metric_df
        sim = MonteCarloSimulator(n_simulations=50, seed=42)
        mc_result = sim.run_from_trades(synthetic_trades)
        mc_df = mc_result.get_metric_df()
        assert isinstance(mc_df, pd.DataFrame)
        assert len(mc_df) > 0
        assert "P05" in mc_df.columns

        # Stress Test → to_dataframe
        covid = CrisisScenario(
            name="COVID Crash",
            start=datetime(2020, 2, 19),
            end=datetime(2020, 3, 23),
            description="Test",
            benchmark_drawdown=-0.34,
        )
        tester = StressTester(benchmark="SPY", scenarios=[covid])
        st_report = tester.run(synthetic_equity_curve, synthetic_trades)
        st_df = st_report.to_dataframe()
        assert isinstance(st_df, pd.DataFrame)
        assert len(st_df) > 0
        assert "scenario" in st_df.columns

        # Sensitivity → to_dataframe
        analyzer = SensitivityAnalyzer(
            eval_fn=lambda p: {"sharpe_ratio": 1.5},
            base_params={"lookback": 14},
        )
        sens_report = analyzer.run()
        sens_df = sens_report.to_dataframe()
        assert isinstance(sens_df, pd.DataFrame)
        assert len(sens_df) > 0
        assert "parameter" in sens_df.columns


# ---------------------------------------------------------------------------
# TestEndToEndWithSyntheticBacktest
# ---------------------------------------------------------------------------


class TestEndToEndWithSyntheticBacktest:
    """Full cycle: broker trades → analysis pipeline."""

    @pytest.mark.asyncio
    async def test_complete_backtest_analysis_cycle(self) -> None:
        """Execute 10 trades via PaperBroker, then run all 3 analyses."""
        broker = PaperBroker(
            initial_cash=100_000.0, commission=0.0, slippage=0.0,
        )
        await broker.connect()

        # Step 1: Execute 10 buy/sell cycles with deterministic prices
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"] * 2
        buy_prices = [
            150.0, 300.0, 130.0, 200.0, 170.0,
            152.0, 305.0, 128.0, 210.0, 175.0,
        ]
        sell_prices = [
            158.0, 290.0, 140.0, 180.0, 185.0,
            148.0, 315.0, 135.0, 220.0, 165.0,
        ]

        trades: list[dict] = []
        equity_values: list[float] = [100_000.0]

        for i, symbol in enumerate(symbols):
            bp = buy_prices[i]
            sp = sell_prices[i]

            with patch.object(
                broker, "get_quote", new=AsyncMock(
                    return_value=_make_quote(symbol, bp),
                ),
            ):
                buy = await broker.buy(symbol, 10.0)
            assert buy.status == OrderStatus.FILLED

            with patch.object(
                broker, "get_quote", new=AsyncMock(
                    return_value=_make_quote(symbol, sp),
                ),
            ):
                sell = await broker.sell(symbol, 10.0)
            assert sell.status == OrderStatus.FILLED

            pnl_dollar = (sp - bp) * 10.0
            pnl_pct = ((sp - bp) / bp) * 100
            trades.append({
                "symbol": symbol,
                "entry_date": buy.created_at.strftime("%Y-%m-%d"),
                "exit_date": sell.updated_at.strftime("%Y-%m-%d"),
                "pnl_dollar": pnl_dollar,
                "pnl_percent": pnl_pct,
            })
            account = await broker.get_account()
            equity_values.append(account.equity)

        await broker.disconnect()
        assert len(trades) == 10

        # Step 2: Build equity curve from broker equity snapshots
        dates = pd.bdate_range("2020-01-02", periods=len(equity_values))
        equity_curve = pd.DataFrame({
            "date": dates.astype(str),
            "equity": equity_values,
        })

        # Step 3: Monte Carlo on trades
        sim = MonteCarloSimulator(n_simulations=100, seed=42)
        mc_result = sim.run_from_trades(trades, initial_capital=100_000.0)
        assert "total_return" in mc_result.percentiles
        assert mc_result.percentiles["total_return"]["P05"] <= (
            mc_result.percentiles["total_return"]["P95"]
        )

        # Step 4: Stress test on equity curve
        # Use a custom scenario matching our short equity curve
        test_scenario = CrisisScenario(
            name="Test Drawdown",
            start=datetime(2020, 1, 2),
            end=datetime(2020, 1, 10),
            description="Synthetic test period",
            benchmark_drawdown=-0.10,
        )
        tester = StressTester(
            benchmark="SPY", scenarios=[test_scenario],
        )
        st_report = tester.run(equity_curve, trades, "E2E Strategy")
        assert 0.0 <= st_report.resilience_score <= 100.0

        # Step 5: Sensitivity analysis with parametrized eval_fn
        def eval_fn(params: dict) -> dict[str, float]:
            lookback = params.get("lookback", 14)
            # Simulate: sharpe varies slightly with lookback
            sharpe = 1.2 + (lookback - 14) * 0.01
            return {
                "sharpe_ratio": max(0.0, sharpe),
                "max_drawdown": -0.10,
                "win_rate": 0.55,
            }

        analyzer = SensitivityAnalyzer(
            eval_fn=eval_fn,
            base_params={"lookback": 14},
            target_metric="sharpe_ratio",
        )
        sens_report = analyzer.run("E2E Strategy")
        assert 0 <= sens_report.robustness_score <= 100

        # Step 6: Verify all scores are in range [0, 100]
        assert 0 <= st_report.resilience_score <= 100
        assert 0 <= sens_report.robustness_score <= 100
        assert 0.0 <= mc_result.probability_of_ruin <= 1.0
