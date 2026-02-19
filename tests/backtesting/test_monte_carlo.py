"""Tests for Monte Carlo simulation."""

import numpy as np
import pandas as pd
import pytest

from auronai.backtesting.monte_carlo import MonteCarloSimulator


@pytest.fixture
def simulator() -> MonteCarloSimulator:
    return MonteCarloSimulator(n_simulations=500, seed=42)


@pytest.fixture
def sample_returns() -> list[float]:
    """Realistic trade returns: ~60% win rate, avg win > avg loss."""
    rng = np.random.default_rng(123)
    n_trades = 100
    wins = rng.uniform(0.01, 0.08, size=int(n_trades * 0.6))
    losses = rng.uniform(-0.05, -0.005, size=int(n_trades * 0.4))
    returns = np.concatenate([wins, losses])
    rng.shuffle(returns)
    return returns.tolist()


@pytest.fixture
def sample_trades(sample_returns: list[float]) -> list[dict]:
    """Trade dicts compatible with BacktestResult format."""
    return [
        {"pnl_percent": r * 100, "pnl_dollar": r * 1000, "symbol": "AAPL"}
        for r in sample_returns
    ]


class TestMonteCarloSimulatorRun:
    def test_basic_run(
        self, simulator: MonteCarloSimulator, sample_returns: list[float]
    ) -> None:
        result = simulator.run(sample_returns, initial_capital=10_000.0)
        assert result.n_simulations == 500
        assert result.initial_capital == 10_000.0

    def test_metric_distributions_exist(
        self, simulator: MonteCarloSimulator, sample_returns: list[float]
    ) -> None:
        result = simulator.run(sample_returns)
        expected_metrics = [
            "total_return",
            "annualized_return",
            "max_drawdown",
            "sharpe_ratio",
            "volatility",
            "final_equity",
        ]
        for metric in expected_metrics:
            assert metric in result.metric_distributions
            assert len(result.metric_distributions[metric]) == 500

    def test_percentiles_structure(
        self, simulator: MonteCarloSimulator, sample_returns: list[float]
    ) -> None:
        result = simulator.run(sample_returns)
        for metric in result.percentiles:
            pcts = result.percentiles[metric]
            assert set(pcts.keys()) == {"P05", "P25", "P50", "P75", "P95"}
            # Percentiles should be ordered
            assert pcts["P05"] <= pcts["P25"] <= pcts["P50"]
            assert pcts["P50"] <= pcts["P75"] <= pcts["P95"]

    def test_probability_of_ruin_range(
        self, simulator: MonteCarloSimulator, sample_returns: list[float]
    ) -> None:
        result = simulator.run(sample_returns, ruin_threshold=0.5)
        assert 0.0 <= result.probability_of_ruin <= 1.0

    def test_max_drawdown_is_negative(
        self, simulator: MonteCarloSimulator, sample_returns: list[float]
    ) -> None:
        result = simulator.run(sample_returns)
        median_dd = result.percentiles["max_drawdown"]["P50"]
        assert median_dd <= 0.0

    def test_equity_curves_shape(
        self, simulator: MonteCarloSimulator, sample_returns: list[float]
    ) -> None:
        result = simulator.run(sample_returns)
        assert isinstance(result.equity_curves, pd.DataFrame)
        # 100 sample curves (or less if n_simulations < 100)
        assert result.equity_curves.shape[1] <= 100
        # n_trades + 1 rows (initial capital row)
        assert result.equity_curves.shape[0] == len(sample_returns) + 1

    def test_custom_n_trades_per_sim(
        self, simulator: MonteCarloSimulator, sample_returns: list[float]
    ) -> None:
        result = simulator.run(sample_returns, n_trades_per_sim=50)
        # Equity curves should have 50 + 1 rows
        assert result.equity_curves.shape[0] == 51

    def test_reproducibility_with_seed(self, sample_returns: list[float]) -> None:
        sim1 = MonteCarloSimulator(n_simulations=100, seed=42)
        sim2 = MonteCarloSimulator(n_simulations=100, seed=42)
        r1 = sim1.run(sample_returns)
        r2 = sim2.run(sample_returns)
        np.testing.assert_array_equal(
            r1.metric_distributions["total_return"],
            r2.metric_distributions["total_return"],
        )

    def test_different_seeds_differ(self, sample_returns: list[float]) -> None:
        sim1 = MonteCarloSimulator(n_simulations=100, seed=1)
        sim2 = MonteCarloSimulator(n_simulations=100, seed=2)
        r1 = sim1.run(sample_returns)
        r2 = sim2.run(sample_returns)
        assert not np.array_equal(
            r1.metric_distributions["total_return"],
            r2.metric_distributions["total_return"],
        )


class TestMonteCarloFromTrades:
    def test_run_from_trades(
        self, simulator: MonteCarloSimulator, sample_trades: list[dict]
    ) -> None:
        result = simulator.run_from_trades(sample_trades, initial_capital=10_000.0)
        assert result.n_simulations == 500
        assert "total_return" in result.percentiles

    def test_filters_none_pnl(self, simulator: MonteCarloSimulator) -> None:
        trades = [
            {"pnl_percent": 5.0, "symbol": "AAPL"},
            {"pnl_percent": None, "symbol": "MSFT"},  # Open trade
            {"pnl_percent": -2.0, "symbol": "GOOGL"},
        ]
        result = simulator.run_from_trades(trades)
        assert result.n_simulations == 500

    def test_too_few_trades_raises(self, simulator: MonteCarloSimulator) -> None:
        trades = [{"pnl_percent": 5.0, "symbol": "AAPL"}]
        with pytest.raises(ValueError, match="at least 2"):
            simulator.run_from_trades(trades)


class TestMonteCarloFromEquityCurve:
    def test_run_from_equity_curve(self, simulator: MonteCarloSimulator) -> None:
        equity = pd.DataFrame(
            {"equity": np.linspace(10_000, 12_000, 252)}
        )
        result = simulator.run_from_equity_curve(equity, initial_capital=10_000.0)
        assert result.n_simulations == 500
        assert "total_return" in result.percentiles

    def test_too_short_curve_raises(self, simulator: MonteCarloSimulator) -> None:
        equity = pd.DataFrame({"equity": [10_000.0]})
        with pytest.raises(ValueError, match="at least 2"):
            simulator.run_from_equity_curve(equity)


class TestMonteCarloEdgeCases:
    def test_too_few_returns_raises(self, simulator: MonteCarloSimulator) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            simulator.run([0.05])

    def test_all_winning_trades(self, simulator: MonteCarloSimulator) -> None:
        returns = [0.02, 0.03, 0.01, 0.04, 0.02] * 20
        result = simulator.run(returns, ruin_threshold=0.5)
        assert result.probability_of_ruin == 0.0
        assert result.percentiles["total_return"]["P05"] > 0

    def test_all_losing_trades(self, simulator: MonteCarloSimulator) -> None:
        returns = [-0.02, -0.03, -0.01, -0.04, -0.02] * 20
        result = simulator.run(returns, ruin_threshold=0.5)
        assert result.probability_of_ruin > 0
        assert result.percentiles["total_return"]["P95"] < 0

    def test_high_ruin_threshold(
        self, simulator: MonteCarloSimulator, sample_returns: list[float]
    ) -> None:
        result = simulator.run(sample_returns, ruin_threshold=0.99)
        # Losing 99% is very unlikely with normal returns
        assert result.probability_of_ruin < 0.1

    def test_large_simulation(self, sample_returns: list[float]) -> None:
        sim = MonteCarloSimulator(n_simulations=2000, seed=42)
        result = sim.run(sample_returns)
        assert result.n_simulations == 2000
        assert len(result.metric_distributions["total_return"]) == 2000


class TestMonteCarloResult:
    def test_summary_string(
        self, simulator: MonteCarloSimulator, sample_returns: list[float]
    ) -> None:
        result = simulator.run(sample_returns)
        summary = result.summary()
        assert "Monte Carlo Simulation" in summary
        assert "500 scenarios" in summary
        assert "Probability of Ruin" in summary

    def test_get_metric_df(
        self, simulator: MonteCarloSimulator, sample_returns: list[float]
    ) -> None:
        result = simulator.run(sample_returns)
        df = result.get_metric_df()
        assert isinstance(df, pd.DataFrame)
        assert "P05" in df.columns
        assert "P95" in df.columns
        assert "total_return" in df.index
        assert "max_drawdown" in df.index
        assert "sharpe_ratio" in df.index
