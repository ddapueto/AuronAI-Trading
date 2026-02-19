"""
Stress testing against historical crisis scenarios.

Tests strategy resilience during extreme market events by analyzing
performance metrics during known crisis periods.
"""

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf

from auronai.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CrisisScenario:
    """Definition of a historical crisis period.

    Attributes:
        name: Human-readable name.
        start: Crisis start date.
        end: Crisis end date.
        description: Brief description of the event.
        benchmark_drawdown: Approximate peak-to-trough drawdown of the market.
    """

    name: str
    start: datetime
    end: datetime
    description: str
    benchmark_drawdown: float  # e.g. -0.34 for -34%


# Pre-defined crisis scenarios
CRISIS_SCENARIOS: list[CrisisScenario] = [
    CrisisScenario(
        name="COVID Crash",
        start=datetime(2020, 2, 19),
        end=datetime(2020, 3, 23),
        description="Pandemic selloff: S&P 500 fell 34% in 23 trading days",
        benchmark_drawdown=-0.34,
    ),
    CrisisScenario(
        name="Bear Market 2022",
        start=datetime(2022, 1, 3),
        end=datetime(2022, 10, 12),
        description="Inflation/rate hikes bear market: S&P 500 fell ~25%",
        benchmark_drawdown=-0.25,
    ),
    CrisisScenario(
        name="Flash Crash 2010",
        start=datetime(2010, 5, 6),
        end=datetime(2010, 5, 10),
        description="Intraday crash of ~9%, recovery within minutes",
        benchmark_drawdown=-0.09,
    ),
    CrisisScenario(
        name="Financial Crisis 2008",
        start=datetime(2008, 9, 15),
        end=datetime(2009, 3, 9),
        description="Lehman collapse, S&P 500 fell ~57% from peak",
        benchmark_drawdown=-0.57,
    ),
    CrisisScenario(
        name="COVID Recovery Correction",
        start=datetime(2020, 9, 2),
        end=datetime(2020, 9, 23),
        description="Tech-led correction after rapid recovery, ~10% drop",
        benchmark_drawdown=-0.10,
    ),
]


@dataclass
class ScenarioResult:
    """Result of stress testing a strategy against one crisis scenario.

    Attributes:
        scenario: The crisis scenario tested.
        strategy_return: Strategy return during the period.
        benchmark_return: Benchmark return during the period.
        max_drawdown: Maximum drawdown during the period.
        recovery_days: Trading days from trough to recovery (None if no recovery).
        volatility: Annualized volatility during the period.
        win_rate: Win rate of trades during the period.
        num_trades: Number of trades during the period.
        outperformance: Strategy return minus benchmark return.
    """

    scenario: CrisisScenario
    strategy_return: float
    benchmark_return: float
    max_drawdown: float
    recovery_days: int | None
    volatility: float
    win_rate: float
    num_trades: int
    outperformance: float


@dataclass
class StressTestReport:
    """Aggregated stress test report across all crisis scenarios.

    Attributes:
        strategy_name: Name of the strategy tested.
        benchmark_symbol: Benchmark symbol used.
        results: List of per-scenario results.
        resilience_score: Overall resilience score (0-100).
    """

    strategy_name: str
    benchmark_symbol: str
    results: list[ScenarioResult] = field(default_factory=list)
    resilience_score: float = 0.0

    def summary(self) -> str:
        """Human-readable summary of stress test results."""
        lines = [
            f"Stress Test Report: {self.strategy_name}",
            f"Benchmark: {self.benchmark_symbol}",
            f"Resilience Score: {self.resilience_score:.0f}/100",
            "",
            f"{'Scenario':<25} {'Strategy':>10} {'Benchmark':>10} "
            f"{'MaxDD':>8} {'Recovery':>10} {'Outperf':>10}",
            "-" * 78,
        ]
        for r in self.results:
            recovery_str = f"{r.recovery_days}d" if r.recovery_days is not None else "N/R"
            lines.append(
                f"{r.scenario.name:<25} {r.strategy_return:>9.2%} "
                f"{r.benchmark_return:>9.2%} {r.max_drawdown:>7.2%} "
                f"{recovery_str:>10} {r.outperformance:>9.2%}"
            )
        return "\n".join(lines)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to DataFrame."""
        rows = []
        for r in self.results:
            rows.append({
                "scenario": r.scenario.name,
                "strategy_return": r.strategy_return,
                "benchmark_return": r.benchmark_return,
                "max_drawdown": r.max_drawdown,
                "recovery_days": r.recovery_days,
                "volatility": r.volatility,
                "win_rate": r.win_rate,
                "num_trades": r.num_trades,
                "outperformance": r.outperformance,
            })
        return pd.DataFrame(rows)


class StressTester:
    """
    Tests strategy resilience against historical crisis scenarios.

    Analyzes equity curves and trades from backtests to measure how a
    strategy performed during known market stress periods.

    Example::

        tester = StressTester(benchmark="SPY")
        report = tester.run(
            equity_curve=backtest_result.equity_curve,
            trades=backtest_result.trades,
            strategy_name="Dual Momentum",
        )
        print(report.summary())
    """

    def __init__(
        self,
        benchmark: str = "SPY",
        scenarios: list[CrisisScenario] | None = None,
    ) -> None:
        self._benchmark = benchmark
        self._scenarios = scenarios or CRISIS_SCENARIOS
        self._benchmark_cache: dict[str, pd.DataFrame] = {}

    def run(
        self,
        equity_curve: pd.DataFrame,
        trades: list[dict],
        strategy_name: str = "Strategy",
    ) -> StressTestReport:
        """
        Run stress tests against all crisis scenarios.

        Args:
            equity_curve: DataFrame with 'date' and 'equity' columns.
            trades: List of trade dicts with entry_date, exit_date, pnl_percent.
            strategy_name: Name for the report.

        Returns:
            StressTestReport with per-scenario results and resilience score.
        """
        equity_curve = equity_curve.copy()
        equity_curve["date"] = pd.to_datetime(equity_curve["date"])

        report = StressTestReport(
            strategy_name=strategy_name,
            benchmark_symbol=self._benchmark,
        )

        for scenario in self._scenarios:
            result = self._test_scenario(equity_curve, trades, scenario)
            if result is not None:
                report.results.append(result)

        if report.results:
            report.resilience_score = self._calculate_resilience_score(
                report.results
            )

        logger.info(
            "Stress test complete: %s — %d scenarios, score: %.0f/100",
            strategy_name,
            len(report.results),
            report.resilience_score,
        )
        return report

    def run_from_returns(
        self,
        daily_returns: pd.Series,
        initial_capital: float = 10_000.0,
        strategy_name: str = "Strategy",
    ) -> StressTestReport:
        """
        Run stress tests from a daily returns series.

        Args:
            daily_returns: Series with DatetimeIndex and daily returns.
            initial_capital: Starting capital.
            strategy_name: Name for the report.

        Returns:
            StressTestReport.
        """
        equity = initial_capital * (1 + daily_returns).cumprod()
        equity_curve = pd.DataFrame({
            "date": equity.index,
            "equity": equity.values,
        })
        return self.run(equity_curve, [], strategy_name)

    def _test_scenario(
        self,
        equity_curve: pd.DataFrame,
        trades: list[dict],
        scenario: CrisisScenario,
    ) -> ScenarioResult | None:
        """Test one crisis scenario."""
        # Filter equity curve to scenario period
        mask = (equity_curve["date"] >= scenario.start) & (
            equity_curve["date"] <= scenario.end
        )
        crisis_equity = equity_curve[mask]

        if len(crisis_equity) < 2:
            logger.warning(
                "Skipping %s: insufficient data in equity curve", scenario.name
            )
            return None

        equity_values = crisis_equity["equity"].values

        # Strategy metrics during crisis
        strategy_return = (equity_values[-1] / equity_values[0]) - 1.0
        max_drawdown = self._calc_max_drawdown(equity_values)
        volatility = self._calc_volatility(equity_values)
        recovery_days = self._calc_recovery_days(equity_curve, scenario)

        # Trades during crisis
        crisis_trades = self._filter_trades(trades, scenario)
        win_rate = self._calc_win_rate(crisis_trades)

        # Benchmark return
        benchmark_return = self._get_benchmark_return(scenario)

        return ScenarioResult(
            scenario=scenario,
            strategy_return=strategy_return,
            benchmark_return=benchmark_return,
            max_drawdown=max_drawdown,
            recovery_days=recovery_days,
            volatility=volatility,
            win_rate=win_rate,
            num_trades=len(crisis_trades),
            outperformance=strategy_return - benchmark_return,
        )

    def _get_benchmark_return(self, scenario: CrisisScenario) -> float:
        """Get benchmark return for a crisis period."""
        cache_key = f"{self._benchmark}_{scenario.start}_{scenario.end}"
        if cache_key not in self._benchmark_cache:
            try:
                ticker = yf.Ticker(self._benchmark)
                hist = ticker.history(start=scenario.start, end=scenario.end)
                if len(hist) >= 2:
                    self._benchmark_cache[cache_key] = hist
                else:
                    return scenario.benchmark_drawdown
            except Exception:  # noqa: BLE001
                logger.warning(
                    "Could not fetch benchmark data for %s, using scenario default",
                    scenario.name,
                )
                return scenario.benchmark_drawdown

        hist = self._benchmark_cache[cache_key]
        return (hist["Close"].iloc[-1] / hist["Close"].iloc[0]) - 1.0

    @staticmethod
    def _calc_max_drawdown(equity: np.ndarray) -> float:
        """Calculate max drawdown from equity array."""
        running_max = np.maximum.accumulate(equity)
        drawdowns = (equity - running_max) / running_max
        return float(drawdowns.min()) if len(drawdowns) > 0 else 0.0

    @staticmethod
    def _calc_volatility(equity: np.ndarray) -> float:
        """Calculate annualized volatility from equity array."""
        if len(equity) < 2:
            return 0.0
        returns = np.diff(equity) / equity[:-1]
        return float(np.std(returns) * np.sqrt(252))

    @staticmethod
    def _calc_recovery_days(
        equity_curve: pd.DataFrame,
        scenario: CrisisScenario,
    ) -> int | None:
        """Calculate days from crisis trough to pre-crisis equity level."""
        pre_crisis = equity_curve[equity_curve["date"] < scenario.start]
        if len(pre_crisis) == 0:
            return None

        pre_crisis_level = pre_crisis["equity"].iloc[-1]
        post_trough = equity_curve[equity_curve["date"] > scenario.end]

        if len(post_trough) == 0:
            return None

        recovered = post_trough[post_trough["equity"] >= pre_crisis_level]
        if len(recovered) == 0:
            return None

        recovery_date = recovered["date"].iloc[0]
        trough_date = scenario.end
        return int((recovery_date - pd.Timestamp(trough_date)).days)

    @staticmethod
    def _filter_trades(
        trades: list[dict], scenario: CrisisScenario
    ) -> list[dict]:
        """Filter trades that overlap with the crisis period."""
        result = []
        for t in trades:
            entry = t.get("entry_date")
            exit_date = t.get("exit_date")
            if entry is None:
                continue
            entry_dt = pd.Timestamp(entry)
            if entry_dt >= scenario.start and entry_dt <= scenario.end:
                result.append(t)
            elif exit_date is not None:
                exit_dt = pd.Timestamp(exit_date)
                if exit_dt >= scenario.start and exit_dt <= scenario.end:
                    result.append(t)
        return result

    @staticmethod
    def _calc_win_rate(trades: list[dict]) -> float:
        """Calculate win rate from trade dicts."""
        closed = [
            t for t in trades if t.get("pnl_dollar") is not None
        ]
        if not closed:
            return 0.0
        wins = sum(1 for t in closed if t["pnl_dollar"] > 0)
        return wins / len(closed)

    @staticmethod
    def _calculate_resilience_score(results: list[ScenarioResult]) -> float:
        """
        Calculate overall resilience score (0-100).

        Scoring criteria:
        - Outperformance vs benchmark (40 pts max)
        - Max drawdown containment (30 pts max)
        - Recovery speed (20 pts max)
        - Win rate maintenance (10 pts max)
        """
        if not results:
            return 0.0

        scores: list[float] = []
        for r in results:
            score = 0.0

            # Outperformance (40 pts): +20 for beating benchmark, scaled
            if r.outperformance >= 0:
                score += min(40.0, 20.0 + r.outperformance * 200)
            else:
                score += max(0.0, 20.0 + r.outperformance * 100)

            # Max drawdown (30 pts): better if less drawdown
            # 0% dd = 30pts, -50% dd = 0pts
            dd_score = max(0.0, 30.0 * (1.0 + r.max_drawdown / 0.5))
            score += min(30.0, dd_score)

            # Recovery (20 pts): faster = better
            if r.recovery_days is not None:
                if r.recovery_days <= 30:
                    score += 20.0
                elif r.recovery_days <= 90:
                    score += 15.0
                elif r.recovery_days <= 180:
                    score += 10.0
                else:
                    score += 5.0
            # No recovery = 0 pts

            # Win rate (10 pts)
            score += r.win_rate * 10.0

            scores.append(min(100.0, score))

        return float(np.mean(scores))
