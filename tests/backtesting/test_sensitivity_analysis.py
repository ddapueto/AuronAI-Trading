"""Tests for parameter sensitivity analysis."""

import pandas as pd
import pytest

from auronai.backtesting.sensitivity_analysis import (
    SensitivityAnalyzer,
)


def _stable_eval(params: dict) -> dict[str, float]:
    """Eval function that is insensitive to parameter changes (robust)."""
    return {
        "sharpe_ratio": 1.5,
        "max_drawdown": -0.08,
        "win_rate": 0.60,
    }


def _fragile_eval(params: dict) -> dict[str, float]:
    """Eval function where sharpe degrades heavily with any parameter change."""
    lookback = params.get("lookback", 90)
    # Sharpe peaks at exactly 90, degrades sharply otherwise
    distance = abs(lookback - 90) / 90
    sharpe = max(0.0, 1.5 - distance * 5.0)
    return {
        "sharpe_ratio": sharpe,
        "max_drawdown": -0.08 - distance * 0.2,
        "win_rate": 0.60 - distance * 0.3,
    }


def _linear_eval(params: dict) -> dict[str, float]:
    """Eval function where sharpe scales linearly with lookback."""
    lookback = params.get("lookback", 90)
    top_n = params.get("top_n", 5)
    sharpe = lookback / 100 + top_n / 10
    return {
        "sharpe_ratio": sharpe,
        "max_drawdown": -0.10,
        "win_rate": 0.55,
    }


@pytest.fixture
def base_params() -> dict:
    return {"lookback": 90, "top_n": 5}


class TestSensitivityAnalyzerRun:
    def test_basic_run(self, base_params: dict) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_stable_eval, base_params=base_params
        )
        report = analyzer.run("Test Strategy")
        assert report.strategy_name == "Test Strategy"
        assert len(report.parameter_results) == 2  # lookback, top_n

    def test_base_metrics_captured(self, base_params: dict) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_stable_eval, base_params=base_params
        )
        report = analyzer.run()
        assert report.base_metrics["sharpe_ratio"] == 1.5
        assert report.base_metrics["max_drawdown"] == -0.08

    def test_stable_strategy_not_fragile(self, base_params: dict) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_stable_eval, base_params=base_params
        )
        report = analyzer.run()
        assert len(report.fragile_params) == 0
        for r in report.parameter_results:
            assert r.is_fragile is False

    def test_fragile_strategy_detected(self) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_fragile_eval,
            base_params={"lookback": 90},
        )
        report = analyzer.run()
        assert "lookback" in report.fragile_params
        assert report.parameter_results[0].is_fragile is True

    def test_degradation_values(self) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_fragile_eval,
            base_params={"lookback": 90},
        )
        report = analyzer.run()
        r = report.parameter_results[0]
        assert r.degradation_20pct > 0
        assert r.degradation_50pct >= r.degradation_20pct

    def test_robustness_score_range(self, base_params: dict) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_stable_eval, base_params=base_params
        )
        report = analyzer.run()
        assert 0 <= report.robustness_score <= 100

    def test_stable_has_high_score(self, base_params: dict) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_stable_eval, base_params=base_params
        )
        report = analyzer.run()
        assert report.robustness_score > 90

    def test_fragile_has_low_score(self) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_fragile_eval,
            base_params={"lookback": 90},
        )
        report = analyzer.run()
        assert report.robustness_score < 50

    def test_skips_non_numeric_params(self) -> None:
        params = {"lookback": 90, "strategy_name": "momentum"}
        analyzer = SensitivityAnalyzer(
            eval_fn=_stable_eval, base_params=params
        )
        report = analyzer.run()
        # Only lookback should be analyzed (string params skipped)
        assert len(report.parameter_results) == 1
        assert report.parameter_results[0].param_name == "lookback"


class TestSensitivityAnalyzerHeatmap:
    def test_heatmap_basic(self, base_params: dict) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_linear_eval, base_params=base_params
        )
        heatmap = analyzer.run_heatmap(
            param_x="lookback",
            param_y="top_n",
            values_x=[60, 90, 120],
            values_y=[3, 5, 7],
        )
        assert heatmap.param_x == "lookback"
        assert heatmap.param_y == "top_n"
        assert heatmap.grid.shape == (3, 3)

    def test_heatmap_values_correct(self, base_params: dict) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_linear_eval, base_params=base_params
        )
        heatmap = analyzer.run_heatmap(
            param_x="lookback",
            param_y="top_n",
            values_x=[100],
            values_y=[10],
            metric="sharpe_ratio",
        )
        # sharpe = 100/100 + 10/10 = 2.0
        assert heatmap.grid[0, 0] == pytest.approx(2.0)

    def test_heatmap_to_dataframe(self, base_params: dict) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_linear_eval, base_params=base_params
        )
        heatmap = analyzer.run_heatmap(
            param_x="lookback",
            param_y="top_n",
            values_x=[60, 90],
            values_y=[3, 5],
        )
        df = heatmap.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (2, 2)


class TestSensitivityReport:
    def test_summary_string(self, base_params: dict) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_stable_eval, base_params=base_params
        )
        report = analyzer.run()
        summary = report.summary()
        assert "Sensitivity Analysis" in summary
        assert "Robustness Score" in summary
        assert "lookback" in summary

    def test_to_dataframe(self, base_params: dict) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_stable_eval, base_params=base_params
        )
        report = analyzer.run()
        df = report.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert "parameter" in df.columns
        assert "is_fragile" in df.columns
        assert len(df) == 2

    def test_fragile_params_list(self) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_fragile_eval,
            base_params={"lookback": 90},
        )
        report = analyzer.run()
        assert isinstance(report.fragile_params, list)
        assert "lookback" in report.fragile_params


class TestParameterVariations:
    def test_variations_include_base(self, base_params: dict) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_stable_eval, base_params=base_params
        )
        report = analyzer.run()
        for r in report.parameter_results:
            assert r.base_value in r.variations

    def test_metrics_df_has_rows(self, base_params: dict) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_stable_eval, base_params=base_params
        )
        report = analyzer.run()
        for r in report.parameter_results:
            # At least baseline + some variations
            assert len(r.metrics) >= 2

    def test_custom_variations(self) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_stable_eval,
            base_params={"lookback": 100},
            variation_pcts=[-0.10, 0.10],
        )
        report = analyzer.run()
        r = report.parameter_results[0]
        # Base + 2 variations
        assert len(r.metrics) == 3

    def test_int_params_stay_int(self) -> None:
        call_log: list[dict] = []

        def logging_eval(params: dict) -> dict[str, float]:
            call_log.append(dict(params))
            return {"sharpe_ratio": 1.0}

        analyzer = SensitivityAnalyzer(
            eval_fn=logging_eval,
            base_params={"lookback": 100},
            variation_pcts=[0.20],
        )
        analyzer.run()
        # Check that varied lookback is int (120)
        varied_calls = [c for c in call_log if c["lookback"] != 100]
        for c in varied_calls:
            assert isinstance(c["lookback"], int)


class TestEdgeCases:
    def test_empty_params(self) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_stable_eval, base_params={}
        )
        report = analyzer.run()
        assert len(report.parameter_results) == 0
        assert report.robustness_score == 100.0

    def test_single_param(self) -> None:
        analyzer = SensitivityAnalyzer(
            eval_fn=_stable_eval, base_params={"lookback": 90}
        )
        report = analyzer.run()
        assert len(report.parameter_results) == 1

    def test_zero_base_value(self) -> None:
        """Parameter with base value 0 should not crash."""
        def eval_fn(params: dict) -> dict[str, float]:
            return {"sharpe_ratio": 1.0}

        analyzer = SensitivityAnalyzer(
            eval_fn=eval_fn, base_params={"offset": 0}
        )
        report = analyzer.run()
        assert len(report.parameter_results) == 1
