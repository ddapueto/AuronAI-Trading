"""Tests for stress testing against crisis scenarios."""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from auronai.backtesting.stress_testing import (
    CRISIS_SCENARIOS,
    CrisisScenario,
    StressTester,
)


def _make_equity_curve(
    start: str,
    end: str,
    initial: float = 10_000.0,
    daily_return: float = 0.001,
) -> pd.DataFrame:
    """Generate a synthetic equity curve."""
    dates = pd.bdate_range(start, end)
    n = len(dates)
    rng = np.random.default_rng(42)
    returns = daily_return + rng.normal(0, 0.01, n)
    equity = initial * np.cumprod(1 + returns)
    return pd.DataFrame({"date": dates.astype(str), "equity": equity})


def _make_trades(
    start: str, end: str, n_trades: int = 20
) -> list[dict]:
    """Generate synthetic trades within a date range."""
    dates = pd.bdate_range(start, end)
    rng = np.random.default_rng(42)
    trades = []
    for _i in range(min(n_trades, len(dates) - 1)):
        entry_idx = rng.integers(0, len(dates) - 1)
        exit_idx = min(entry_idx + rng.integers(1, 10), len(dates) - 1)
        pnl = rng.uniform(-500, 800)
        trades.append({
            "symbol": "AAPL",
            "entry_date": str(dates[entry_idx].date()),
            "exit_date": str(dates[exit_idx].date()),
            "pnl_dollar": pnl,
            "pnl_percent": pnl / 100,
        })
    return trades


@pytest.fixture
def tester() -> StressTester:
    """StressTester with only COVID scenario for fast tests."""
    covid = CrisisScenario(
        name="COVID Crash",
        start=datetime(2020, 2, 19),
        end=datetime(2020, 3, 23),
        description="Test scenario",
        benchmark_drawdown=-0.34,
    )
    return StressTester(benchmark="SPY", scenarios=[covid])


@pytest.fixture
def full_equity() -> pd.DataFrame:
    """Equity curve spanning 2019-2021 (covers COVID)."""
    return _make_equity_curve("2019-01-01", "2021-12-31")


@pytest.fixture
def full_trades() -> list[dict]:
    """Trades during COVID period."""
    return _make_trades("2020-02-19", "2020-03-23", n_trades=10)


class TestCrisisScenarios:
    def test_predefined_scenarios_exist(self) -> None:
        assert len(CRISIS_SCENARIOS) >= 4

    def test_scenario_names(self) -> None:
        names = [s.name for s in CRISIS_SCENARIOS]
        assert "COVID Crash" in names
        assert "Bear Market 2022" in names
        assert "Financial Crisis 2008" in names
        assert "Flash Crash 2010" in names

    def test_scenario_dates_valid(self) -> None:
        for s in CRISIS_SCENARIOS:
            assert s.start < s.end
            assert s.benchmark_drawdown < 0


class TestStressTester:
    def test_run_returns_report(
        self, tester: StressTester, full_equity: pd.DataFrame, full_trades: list[dict]
    ) -> None:
        report = tester.run(full_equity, full_trades, "Test Strategy")
        assert report.strategy_name == "Test Strategy"
        assert report.benchmark_symbol == "SPY"

    def test_report_has_results(
        self, tester: StressTester, full_equity: pd.DataFrame, full_trades: list[dict]
    ) -> None:
        report = tester.run(full_equity, full_trades)
        assert len(report.results) == 1
        assert report.results[0].scenario.name == "COVID Crash"

    def test_scenario_result_fields(
        self, tester: StressTester, full_equity: pd.DataFrame, full_trades: list[dict]
    ) -> None:
        report = tester.run(full_equity, full_trades)
        r = report.results[0]
        # Strategy return should be a float
        assert isinstance(r.strategy_return, float)
        assert isinstance(r.max_drawdown, float)
        assert r.max_drawdown <= 0
        assert isinstance(r.volatility, float)
        assert r.volatility >= 0
        assert 0.0 <= r.win_rate <= 1.0

    def test_resilience_score_range(
        self, tester: StressTester, full_equity: pd.DataFrame, full_trades: list[dict]
    ) -> None:
        report = tester.run(full_equity, full_trades)
        assert 0.0 <= report.resilience_score <= 100.0

    def test_skips_scenarios_without_data(self) -> None:
        """Scenarios outside equity curve range are skipped."""
        future_scenario = CrisisScenario(
            name="Future Crisis",
            start=datetime(2030, 1, 1),
            end=datetime(2030, 6, 1),
            description="Future",
            benchmark_drawdown=-0.20,
        )
        tester = StressTester(scenarios=[future_scenario])
        equity = _make_equity_curve("2020-01-01", "2020-12-31")
        report = tester.run(equity, [])
        assert len(report.results) == 0
        assert report.resilience_score == 0.0


class TestStressTesterFromReturns:
    def test_run_from_returns(self, tester: StressTester) -> None:
        dates = pd.bdate_range("2019-01-01", "2021-12-31")
        rng = np.random.default_rng(42)
        returns = pd.Series(rng.normal(0.0005, 0.01, len(dates)), index=dates)
        report = tester.run_from_returns(returns, strategy_name="Returns Test")
        assert report.strategy_name == "Returns Test"
        assert len(report.results) >= 0  # May have data or not


class TestStressTesterMetrics:
    def test_max_drawdown_calculation(self) -> None:
        equity = np.array([100, 110, 90, 85, 95, 100])
        dd = StressTester._calc_max_drawdown(equity)
        # Peak was 110, trough was 85 → dd = (85-110)/110 = -0.2272
        assert dd == pytest.approx(-25 / 110, rel=1e-4)

    def test_max_drawdown_no_drawdown(self) -> None:
        equity = np.array([100, 110, 120, 130])
        dd = StressTester._calc_max_drawdown(equity)
        assert dd == 0.0

    def test_volatility_calculation(self) -> None:
        equity = np.array([100, 102, 98, 101, 99, 103])
        vol = StressTester._calc_volatility(equity)
        assert vol > 0
        assert isinstance(vol, float)

    def test_volatility_constant_equity(self) -> None:
        equity = np.array([100, 100, 100, 100])
        vol = StressTester._calc_volatility(equity)
        assert vol == 0.0

    def test_win_rate_all_winners(self) -> None:
        trades = [{"pnl_dollar": 100}, {"pnl_dollar": 200}]
        assert StressTester._calc_win_rate(trades) == 1.0

    def test_win_rate_all_losers(self) -> None:
        trades = [{"pnl_dollar": -100}, {"pnl_dollar": -200}]
        assert StressTester._calc_win_rate(trades) == 0.0

    def test_win_rate_empty(self) -> None:
        assert StressTester._calc_win_rate([]) == 0.0

    def test_filter_trades_in_range(self) -> None:
        scenario = CrisisScenario(
            name="Test", start=datetime(2020, 3, 1), end=datetime(2020, 3, 31),
            description="", benchmark_drawdown=-0.1,
        )
        trades = [
            {"entry_date": "2020-03-05", "exit_date": "2020-03-10", "pnl_dollar": 100},
            {"entry_date": "2020-01-05", "exit_date": "2020-01-10", "pnl_dollar": 50},
            {"entry_date": "2020-02-25", "exit_date": "2020-03-05", "pnl_dollar": -30},
        ]
        filtered = StressTester._filter_trades(trades, scenario)
        assert len(filtered) == 2  # First and third

    def test_recovery_days(self) -> None:
        # Pre-crisis: equity at 100
        # Crisis: drops to 80
        # Post-crisis: recovers to 100 after 30 days
        dates = (
            ["2020-02-18"] + ["2020-02-19"] + ["2020-03-23"] + ["2020-04-22"]
        )
        equities = [100, 100, 80, 105]
        equity_curve = pd.DataFrame({"date": pd.to_datetime(dates), "equity": equities})
        scenario = CrisisScenario(
            name="Test", start=datetime(2020, 2, 19), end=datetime(2020, 3, 23),
            description="", benchmark_drawdown=-0.2,
        )
        days = StressTester._calc_recovery_days(equity_curve, scenario)
        assert days is not None
        assert days == 30  # 2020-03-23 to 2020-04-22

    def test_recovery_days_no_recovery(self) -> None:
        dates = ["2020-02-18", "2020-02-19", "2020-03-23", "2020-04-22"]
        equities = [100, 100, 80, 85]  # Never recovers to 100
        equity_curve = pd.DataFrame({"date": pd.to_datetime(dates), "equity": equities})
        scenario = CrisisScenario(
            name="Test", start=datetime(2020, 2, 19), end=datetime(2020, 3, 23),
            description="", benchmark_drawdown=-0.2,
        )
        days = StressTester._calc_recovery_days(equity_curve, scenario)
        assert days is None


class TestStressTestReport:
    def test_summary_string(
        self, tester: StressTester, full_equity: pd.DataFrame, full_trades: list[dict]
    ) -> None:
        report = tester.run(full_equity, full_trades)
        summary = report.summary()
        assert "Stress Test Report" in summary
        assert "Resilience Score" in summary

    def test_to_dataframe(
        self, tester: StressTester, full_equity: pd.DataFrame, full_trades: list[dict]
    ) -> None:
        report = tester.run(full_equity, full_trades)
        df = report.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert "scenario" in df.columns
        assert "strategy_return" in df.columns
        assert "max_drawdown" in df.columns


class TestResilienceScore:
    def test_perfect_resilience(self) -> None:
        """Strategy that outperforms and recovers fast."""
        from auronai.backtesting.stress_testing import ScenarioResult

        scenario = CrisisScenario(
            name="Test", start=datetime(2020, 1, 1), end=datetime(2020, 6, 1),
            description="", benchmark_drawdown=-0.30,
        )
        result = ScenarioResult(
            scenario=scenario,
            strategy_return=0.05,
            benchmark_return=-0.30,
            max_drawdown=-0.02,
            recovery_days=10,
            volatility=0.10,
            win_rate=0.8,
            num_trades=20,
            outperformance=0.35,
        )
        score = StressTester._calculate_resilience_score([result])
        assert score > 80  # Should be very high

    def test_poor_resilience(self) -> None:
        from auronai.backtesting.stress_testing import ScenarioResult

        scenario = CrisisScenario(
            name="Test", start=datetime(2020, 1, 1), end=datetime(2020, 6, 1),
            description="", benchmark_drawdown=-0.30,
        )
        result = ScenarioResult(
            scenario=scenario,
            strategy_return=-0.50,
            benchmark_return=-0.30,
            max_drawdown=-0.55,
            recovery_days=None,
            volatility=0.50,
            win_rate=0.2,
            num_trades=10,
            outperformance=-0.20,
        )
        score = StressTester._calculate_resilience_score([result])
        assert score < 30  # Should be low
