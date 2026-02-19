"""
Monte Carlo simulation for strategy robustness validation.

Generates bootstrap scenarios from historical trade returns to estimate
the distribution of key performance metrics (Sharpe, Max Drawdown, CAGR)
and calculate probability of ruin.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from auronai.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MonteCarloResult:
    """Results from a Monte Carlo simulation run.

    Attributes:
        n_simulations: Number of simulations run.
        initial_capital: Starting capital for each simulation.
        metric_distributions: Dict of metric name -> array of values across sims.
        percentiles: Dict of metric name -> dict of percentile values.
        probability_of_ruin: Probability of losing more than ruin_threshold.
        ruin_threshold: Fraction of capital loss that defines ruin.
        equity_curves: Sample of simulated equity curves (DataFrame).
    """

    n_simulations: int
    initial_capital: float
    metric_distributions: dict[str, np.ndarray] = field(default_factory=dict)
    percentiles: dict[str, dict[str, float]] = field(default_factory=dict)
    probability_of_ruin: float = 0.0
    ruin_threshold: float = 0.5
    equity_curves: pd.DataFrame = field(default_factory=pd.DataFrame)

    def summary(self) -> str:
        """Human-readable summary of Monte Carlo results."""
        lines = [
            f"Monte Carlo Simulation ({self.n_simulations} scenarios)",
            f"Initial Capital: ${self.initial_capital:,.0f}",
            f"Probability of Ruin (>{self.ruin_threshold:.0%} loss): "
            f"{self.probability_of_ruin:.2%}",
            "",
        ]
        for metric, pcts in self.percentiles.items():
            lines.append(f"  {metric}:")
            for label, val in pcts.items():
                if "return" in metric or "drawdown" in metric:
                    lines.append(f"    {label}: {val:.2%}")
                else:
                    lines.append(f"    {label}: {val:.4f}")
        return "\n".join(lines)

    def get_metric_df(self) -> pd.DataFrame:
        """Return percentiles as a DataFrame for easy comparison."""
        rows = []
        for metric, pcts in self.percentiles.items():
            row = {"metric": metric, **pcts}
            rows.append(row)
        return pd.DataFrame(rows).set_index("metric")


class MonteCarloSimulator:
    """
    Bootstrap Monte Carlo simulator for trading strategy validation.

    Takes historical trade returns and generates N simulated equity paths
    by resampling trades with replacement. Calculates distribution of
    performance metrics across all paths.

    Example::

        simulator = MonteCarloSimulator(n_simulations=1000, seed=42)
        result = simulator.run(
            trade_returns=[-0.02, 0.05, 0.03, -0.01, 0.04, ...],
            initial_capital=10_000.0,
        )
        print(result.summary())
    """

    def __init__(
        self,
        n_simulations: int = 1000,
        seed: int | None = 42,
    ) -> None:
        self._n_simulations = n_simulations
        self._rng = np.random.default_rng(seed)

    def run(
        self,
        trade_returns: list[float] | np.ndarray,
        initial_capital: float = 10_000.0,
        n_trades_per_sim: int | None = None,
        ruin_threshold: float = 0.5,
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation with bootstrap resampling of trades.

        Args:
            trade_returns: Array of per-trade percentage returns (e.g. 0.05 = +5%).
            initial_capital: Starting capital for each simulation.
            n_trades_per_sim: Number of trades per simulation path.
                Defaults to len(trade_returns).
            ruin_threshold: Fraction of capital loss that defines ruin
                (0.5 = losing 50% of capital).

        Returns:
            MonteCarloResult with distributions and percentiles.
        """
        returns = np.asarray(trade_returns, dtype=np.float64)
        if len(returns) < 2:
            raise ValueError("Need at least 2 trade returns for simulation")

        n_trades = n_trades_per_sim or len(returns)
        logger.info(
            "Running Monte Carlo: %d simulations, %d trades each",
            self._n_simulations,
            n_trades,
        )

        # Bootstrap: resample trade returns with replacement
        # Shape: (n_simulations, n_trades)
        sampled = self._rng.choice(returns, size=(self._n_simulations, n_trades))

        # Build equity curves: cumulative product of (1 + return)
        growth_factors = 1.0 + sampled
        cum_equity = initial_capital * np.cumprod(growth_factors, axis=1)

        # Prepend initial capital column
        initial_col = np.full((self._n_simulations, 1), initial_capital)
        equity_paths = np.hstack([initial_col, cum_equity])

        # Calculate metrics for each simulation
        metrics = self._calculate_path_metrics(equity_paths, initial_capital)

        # Percentiles
        pct_labels = ["P05", "P25", "P50", "P75", "P95"]
        pct_values = [5, 25, 50, 75, 95]
        percentiles: dict[str, dict[str, float]] = {}
        for name, values in metrics.items():
            percentiles[name] = {
                label: float(np.percentile(values, p))
                for label, p in zip(pct_labels, pct_values, strict=True)
            }

        # Probability of ruin
        final_equity = equity_paths[:, -1]
        ruin_count = np.sum(final_equity < initial_capital * (1 - ruin_threshold))
        prob_ruin = float(ruin_count / self._n_simulations)

        # Sample equity curves for visualization (max 100)
        n_sample = min(100, self._n_simulations)
        sample_idx = self._rng.choice(
            self._n_simulations, size=n_sample, replace=False
        )
        sample_curves = pd.DataFrame(
            equity_paths[sample_idx].T,
            columns=[f"sim_{i}" for i in range(n_sample)],
        )

        result = MonteCarloResult(
            n_simulations=self._n_simulations,
            initial_capital=initial_capital,
            metric_distributions=metrics,
            percentiles=percentiles,
            probability_of_ruin=prob_ruin,
            ruin_threshold=ruin_threshold,
            equity_curves=sample_curves,
        )

        logger.info(
            "Monte Carlo complete. Median return: %.2f%%, P(ruin): %.2f%%",
            percentiles["total_return"]["P50"] * 100,
            prob_ruin * 100,
        )
        return result

    def run_from_trades(
        self,
        trades: list[dict],
        initial_capital: float = 10_000.0,
        ruin_threshold: float = 0.5,
    ) -> MonteCarloResult:
        """
        Run Monte Carlo from a list of trade dicts (BacktestResult.trades format).

        Args:
            trades: List of trade dicts with 'pnl_percent' key.
            initial_capital: Starting capital.
            ruin_threshold: Fraction loss for ruin.

        Returns:
            MonteCarloResult.
        """
        returns = [
            t["pnl_percent"] / 100.0
            for t in trades
            if t.get("pnl_percent") is not None
        ]
        if len(returns) < 2:
            raise ValueError(
                "Need at least 2 closed trades with pnl_percent for simulation"
            )
        return self.run(
            trade_returns=returns,
            initial_capital=initial_capital,
            ruin_threshold=ruin_threshold,
        )

    def run_from_equity_curve(
        self,
        equity_curve: pd.DataFrame,
        initial_capital: float = 10_000.0,
        ruin_threshold: float = 0.5,
    ) -> MonteCarloResult:
        """
        Run Monte Carlo by bootstrapping daily returns from an equity curve.

        Args:
            equity_curve: DataFrame with 'equity' column.
            initial_capital: Starting capital.
            ruin_threshold: Fraction loss for ruin.

        Returns:
            MonteCarloResult.
        """
        equity = equity_curve["equity"].values
        daily_returns = np.diff(equity) / equity[:-1]
        daily_returns = daily_returns[np.isfinite(daily_returns)]
        if len(daily_returns) < 2:
            raise ValueError("Need at least 2 daily returns for simulation")
        return self.run(
            trade_returns=daily_returns.tolist(),
            initial_capital=initial_capital,
            ruin_threshold=ruin_threshold,
        )

    @staticmethod
    def _calculate_path_metrics(
        equity_paths: np.ndarray,
        initial_capital: float,
    ) -> dict[str, np.ndarray]:
        """Calculate performance metrics for all simulated equity paths.

        Args:
            equity_paths: Shape (n_simulations, n_steps+1) equity values.
            initial_capital: Starting capital.

        Returns:
            Dict of metric name -> array of values (one per simulation).
        """
        n_sims = equity_paths.shape[0]
        n_steps = equity_paths.shape[1] - 1  # exclude initial capital

        # Total return
        final_equity = equity_paths[:, -1]
        total_return = (final_equity / initial_capital) - 1.0

        # Annualized return (assuming ~252 trading days)
        years = n_steps / 252.0
        if years > 0:
            annualized_return = (final_equity / initial_capital) ** (1.0 / years) - 1.0
        else:
            annualized_return = total_return

        # Max drawdown per path
        max_drawdowns = np.zeros(n_sims)
        for i in range(n_sims):
            path = equity_paths[i]
            running_max = np.maximum.accumulate(path)
            drawdowns = (path - running_max) / running_max
            max_drawdowns[i] = drawdowns.min()

        # Sharpe ratio per path (annualized)
        # daily returns from equity paths
        daily_returns = np.diff(equity_paths, axis=1) / equity_paths[:, :-1]
        mean_daily = daily_returns.mean(axis=1)
        std_daily = daily_returns.std(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            sharpe_ratios = np.where(
                std_daily > 0,
                (mean_daily / std_daily) * np.sqrt(252),
                0.0,
            )

        # Volatility (annualized)
        volatility = std_daily * np.sqrt(252)

        return {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "max_drawdown": max_drawdowns,
            "sharpe_ratio": sharpe_ratios,
            "volatility": volatility,
            "final_equity": final_equity,
        }
