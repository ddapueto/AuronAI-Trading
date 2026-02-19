"""
Parameter sensitivity analysis for strategy robustness validation.

Varies strategy parameters around their optimal values to detect overfitting.
If performance degrades significantly with small parameter changes, the
strategy is likely fragile/overfit.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from auronai.utils.logger import get_logger

logger = get_logger(__name__)

# Type alias for a function that takes params dict and returns metrics dict
EvalFunction = Callable[[dict], dict[str, float]]


@dataclass
class ParameterSensitivity:
    """Sensitivity result for a single parameter.

    Attributes:
        param_name: Name of the parameter.
        base_value: Optimal/baseline value.
        variations: List of tested values.
        metrics: DataFrame with columns for each metric, indexed by param value.
        degradation_20pct: Max metric degradation at ±20% variation.
        degradation_50pct: Max metric degradation at ±50% variation.
        is_fragile: True if degradation_20pct > 30%.
    """

    param_name: str
    base_value: float
    variations: list[float] = field(default_factory=list)
    metrics: pd.DataFrame = field(default_factory=pd.DataFrame)
    degradation_20pct: float = 0.0
    degradation_50pct: float = 0.0
    is_fragile: bool = False


@dataclass
class HeatmapResult:
    """Sensitivity heatmap for two parameters simultaneously.

    Attributes:
        param_x: First parameter name.
        param_y: Second parameter name.
        values_x: Values tested for param_x.
        values_y: Values tested for param_y.
        metric_name: Metric shown in heatmap.
        grid: 2D array of metric values (shape: len(values_y) x len(values_x)).
    """

    param_x: str
    param_y: str
    values_x: list[float]
    values_y: list[float]
    metric_name: str
    grid: np.ndarray = field(default_factory=lambda: np.array([]))

    def to_dataframe(self) -> pd.DataFrame:
        """Convert heatmap to DataFrame with param_y as index, param_x as columns."""
        return pd.DataFrame(
            self.grid,
            index=[f"{self.param_y}={v}" for v in self.values_y],
            columns=[f"{self.param_x}={v}" for v in self.values_x],
        )


@dataclass
class SensitivityReport:
    """Aggregated sensitivity analysis report.

    Attributes:
        strategy_name: Name of the strategy analyzed.
        base_params: Baseline parameter values.
        base_metrics: Metrics at baseline parameters.
        parameter_results: Per-parameter sensitivity results.
        heatmaps: Two-parameter heatmap results.
        fragile_params: List of fragile parameter names.
        robustness_score: Overall robustness score (0-100).
    """

    strategy_name: str
    base_params: dict
    base_metrics: dict[str, float] = field(default_factory=dict)
    parameter_results: list[ParameterSensitivity] = field(default_factory=list)
    heatmaps: list[HeatmapResult] = field(default_factory=list)
    fragile_params: list[str] = field(default_factory=list)
    robustness_score: float = 0.0

    def summary(self) -> str:
        """Human-readable summary."""
        lines = [
            f"Sensitivity Analysis: {self.strategy_name}",
            f"Robustness Score: {self.robustness_score:.0f}/100",
            f"Fragile Parameters: {', '.join(self.fragile_params) or 'None'}",
            "",
            f"{'Parameter':<20} {'Base':>8} {'Deg ±20%':>10} {'Deg ±50%':>10} "
            f"{'Status':>10}",
            "-" * 62,
        ]
        for r in self.parameter_results:
            status = "FRAGILE" if r.is_fragile else "OK"
            lines.append(
                f"{r.param_name:<20} {r.base_value:>8.3g} "
                f"{r.degradation_20pct:>9.1%} {r.degradation_50pct:>9.1%} "
                f"{status:>10}"
            )
        return "\n".join(lines)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert parameter results to DataFrame."""
        rows = []
        for r in self.parameter_results:
            rows.append({
                "parameter": r.param_name,
                "base_value": r.base_value,
                "degradation_20pct": r.degradation_20pct,
                "degradation_50pct": r.degradation_50pct,
                "is_fragile": r.is_fragile,
            })
        return pd.DataFrame(rows)


class SensitivityAnalyzer:
    """
    Analyzes strategy parameter sensitivity to detect overfitting.

    Takes a scoring function that evaluates a parameter set and returns
    performance metrics. Varies each parameter independently and in pairs
    to measure impact on key metrics.

    Example::

        def evaluate(params: dict) -> dict[str, float]:
            # Run backtest with params, return metrics
            return {"sharpe_ratio": 1.5, "max_drawdown": -0.08, "win_rate": 0.6}

        analyzer = SensitivityAnalyzer(
            eval_fn=evaluate,
            base_params={"lookback": 90, "top_n": 5},
            target_metric="sharpe_ratio",
        )
        report = analyzer.run()
        print(report.summary())
    """

    def __init__(
        self,
        eval_fn: EvalFunction,
        base_params: dict,
        target_metric: str = "sharpe_ratio",
        variation_pcts: list[float] | None = None,
        fragility_threshold: float = 0.30,
    ) -> None:
        """
        Args:
            eval_fn: Function that takes params dict → metrics dict.
            base_params: Baseline (optimal) parameter values.
            target_metric: Primary metric for degradation analysis.
            variation_pcts: Percentage variations to test.
                Defaults to [-50%, -20%, -10%, +10%, +20%, +50%].
            fragility_threshold: Degradation threshold for fragility flag.
        """
        self._eval_fn = eval_fn
        self._base_params = dict(base_params)
        self._target_metric = target_metric
        self._variation_pcts = variation_pcts or [-0.50, -0.20, -0.10, 0.10, 0.20, 0.50]
        self._fragility_threshold = fragility_threshold

    def run(self, strategy_name: str = "Strategy") -> SensitivityReport:
        """
        Run full sensitivity analysis.

        Args:
            strategy_name: Name for the report.

        Returns:
            SensitivityReport with per-parameter results and robustness score.
        """
        logger.info("Running sensitivity analysis for %s", strategy_name)

        # Evaluate baseline
        base_metrics = self._eval_fn(self._base_params)

        report = SensitivityReport(
            strategy_name=strategy_name,
            base_params=dict(self._base_params),
            base_metrics=base_metrics,
        )

        # Analyze each parameter independently
        numeric_params = {
            k: v for k, v in self._base_params.items()
            if isinstance(v, (int, float))
        }

        for param_name, base_value in numeric_params.items():
            result = self._analyze_parameter(
                param_name, base_value, base_metrics
            )
            report.parameter_results.append(result)
            if result.is_fragile:
                report.fragile_params.append(param_name)

        # Calculate robustness score
        report.robustness_score = self._calculate_robustness_score(
            report.parameter_results
        )

        logger.info(
            "Sensitivity analysis complete. Score: %.0f/100, Fragile: %s",
            report.robustness_score,
            report.fragile_params or "None",
        )
        return report

    def run_heatmap(
        self,
        param_x: str,
        param_y: str,
        values_x: list[float],
        values_y: list[float],
        metric: str | None = None,
    ) -> HeatmapResult:
        """
        Generate a 2D heatmap varying two parameters simultaneously.

        Args:
            param_x: First parameter name.
            param_y: Second parameter name.
            values_x: Values to test for param_x.
            values_y: Values to test for param_y.
            metric: Metric to map. Defaults to target_metric.

        Returns:
            HeatmapResult with 2D grid of metric values.
        """
        metric = metric or self._target_metric
        grid = np.zeros((len(values_y), len(values_x)))

        total = len(values_x) * len(values_y)
        logger.info(
            "Running heatmap: %s x %s (%d evaluations)", param_x, param_y, total
        )

        for i, vy in enumerate(values_y):
            for j, vx in enumerate(values_x):
                params = dict(self._base_params)
                params[param_x] = type(self._base_params[param_x])(vx)
                params[param_y] = type(self._base_params[param_y])(vy)
                metrics = self._eval_fn(params)
                grid[i, j] = metrics.get(metric, 0.0)

        return HeatmapResult(
            param_x=param_x,
            param_y=param_y,
            values_x=values_x,
            values_y=values_y,
            metric_name=metric,
            grid=grid,
        )

    def _analyze_parameter(
        self,
        param_name: str,
        base_value: float,
        base_metrics: dict[str, float],
    ) -> ParameterSensitivity:
        """Analyze sensitivity of a single parameter."""
        base_target = base_metrics.get(self._target_metric, 0.0)
        variations: list[float] = []
        metric_rows: list[dict] = []

        # Add baseline
        variations.append(base_value)
        row = {"param_value": base_value, "variation_pct": 0.0}
        row.update(base_metrics)
        metric_rows.append(row)

        # Test each variation
        for pct in self._variation_pcts:
            varied_value = base_value * (1 + pct)
            # Preserve type (int params stay int)
            if isinstance(self._base_params[param_name], int):
                varied_value = round(varied_value)
                if varied_value == base_value:
                    continue

            params = dict(self._base_params)
            params[param_name] = type(self._base_params[param_name])(varied_value)

            metrics = self._eval_fn(params)
            variations.append(varied_value)
            row = {"param_value": varied_value, "variation_pct": pct}
            row.update(metrics)
            metric_rows.append(row)

        metrics_df = pd.DataFrame(metric_rows)

        # Calculate degradation
        degradation_20 = self._calc_degradation(metrics_df, base_target, 0.20)
        degradation_50 = self._calc_degradation(metrics_df, base_target, 0.50)

        return ParameterSensitivity(
            param_name=param_name,
            base_value=base_value,
            variations=sorted(set(variations)),
            metrics=metrics_df,
            degradation_20pct=degradation_20,
            degradation_50pct=degradation_50,
            is_fragile=degradation_20 > self._fragility_threshold,
        )

    def _calc_degradation(
        self,
        metrics_df: pd.DataFrame,
        base_value: float,
        max_pct: float,
    ) -> float:
        """Calculate worst degradation within ±max_pct variation."""
        if base_value == 0:
            return 0.0

        within_range = metrics_df[
            metrics_df["variation_pct"].abs() <= max_pct + 1e-9
        ]
        if within_range.empty:
            return 0.0

        target_col = self._target_metric
        if target_col not in within_range.columns:
            return 0.0

        values = within_range[target_col].values
        worst = values.min() if base_value > 0 else values.max()
        degradation = abs((worst - base_value) / base_value)
        return float(degradation)

    @staticmethod
    def _calculate_robustness_score(
        results: list[ParameterSensitivity],
    ) -> float:
        """
        Calculate overall robustness score (0-100).

        100 = no degradation at all variations
        0 = all parameters are fragile with >50% degradation
        """
        if not results:
            return 100.0

        scores: list[float] = []
        for r in results:
            # Score per parameter: lower degradation = higher score
            param_score = max(0.0, 100.0 * (1.0 - r.degradation_20pct))
            scores.append(param_score)

        return float(np.mean(scores))
