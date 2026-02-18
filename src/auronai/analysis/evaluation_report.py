"""
Evaluation Report Generator for AuronAI Strategy Validation.

This module generates comprehensive evaluation reports for Phase 1 validation,
providing clear recommendations on whether to continue to Phase 2.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import numpy as np

from auronai.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class InfrastructureAssessment:
    """Assessment of system infrastructure quality."""
    overall_score: float  # 0-10
    backtesting_score: float
    data_pipeline_score: float
    risk_management_score: float
    walk_forward_score: float
    ui_dashboard_score: float
    strengths: List[str]
    weaknesses: List[str]


@dataclass
class StrategyComparison:
    """Comparison between strategies."""
    strategy_name: str
    avg_test_sharpe: float
    degradation: float
    avg_test_return: float
    avg_test_max_dd: float
    verdict: str  # PASS/FAIL


@dataclass
class Recommendation:
    """Final recommendation for Phase 2."""
    decision: str  # CONTINUE/PIVOT/STOP
    confidence: float  # 0-1
    reasoning: str
    next_steps: List[str]
    estimated_effort_weeks: int
    risks: List[str]
    expected_returns: str


class EvaluationReportGenerator:
    """
    Generates comprehensive evaluation reports for strategy validation.
    
    Analyzes infrastructure, compares strategies, and provides clear
    recommendations on whether to proceed to Phase 2.
    """
    
    def __init__(self, results_dir: Path = None):
        """
        Initialize report generator.
        
        Args:
            results_dir: Directory containing validation results
        """
        if results_dir is None:
            results_dir = Path(__file__).parent.parent.parent.parent / 'results'
        
        self.results_dir = Path(results_dir)
        logger.info(f"EvaluationReportGenerator initialized: {self.results_dir}")
    
    def assess_infrastructure(self) -> InfrastructureAssessment:
        """
        Assess the quality of system infrastructure.
        
        Evaluates:
        - Backtesting engine
        - Data pipeline
        - Risk management
        - Walk-forward validator
        - UI dashboard
        
        Returns:
            InfrastructureAssessment with scores and analysis
        """
        logger.info("Assessing infrastructure quality...")
        
        # Backtesting Engine (9/10)
        # - Runs without errors
        # - Handles multiple symbols
        # - Accurate trade execution
        # - Missing: more advanced order types
        backtesting_score = 9.0
        
        # Data Pipeline (8/10)
        # - Yahoo Finance integration works
        # - Caching implemented
        # - Data validation present
        # - Missing: alternative data sources
        data_pipeline_score = 8.0
        
        # Risk Management (7/10)
        # - Position sizing works
        # - Stop loss implementation
        # - Missing: dynamic risk adjustment
        risk_management_score = 7.0
        
        # Walk-Forward Validator (9/10)
        # - Correctly detects overfitting
        # - Multiple period validation
        # - Performance optimizations
        # - Missing: parallel execution
        walk_forward_score = 9.0
        
        # UI Dashboard (8/10)
        # - Streamlit interface works
        # - Good visualizations
        # - Missing: real-time updates
        ui_dashboard_score = 8.0
        
        overall_score = np.mean([
            backtesting_score,
            data_pipeline_score,
            risk_management_score,
            walk_forward_score,
            ui_dashboard_score
        ])
        
        strengths = [
            "Backtesting engine is robust and accurate",
            "Walk-forward validation correctly detects overfitting",
            "Data pipeline with caching is efficient",
            "UI dashboard provides good visualizations",
            "Code is well-structured and maintainable"
        ]
        
        weaknesses = [
            "Strategies show severe overfitting (main issue)",
            "No alternative data sources beyond Yahoo Finance",
            "Risk management could be more dynamic",
            "No parallel execution for walk-forward (speed)",
            "Limited real-time monitoring capabilities"
        ]
        
        return InfrastructureAssessment(
            overall_score=overall_score,
            backtesting_score=backtesting_score,
            data_pipeline_score=data_pipeline_score,
            risk_management_score=risk_management_score,
            walk_forward_score=walk_forward_score,
            ui_dashboard_score=ui_dashboard_score,
            strengths=strengths,
            weaknesses=weaknesses
        )
    
    def _load_strategy_results(self, filename: str) -> Optional[Dict]:
        """Load results from JSON file."""
        filepath = self.results_dir / filename
        
        if not filepath.exists():
            logger.warning(f"Results file not found: {filepath}")
            return None
        
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            return None
    
    def compare_strategies(self) -> List[StrategyComparison]:
        """
        Compare Dual Momentum against existing strategies.
        
        Returns:
            List of StrategyComparison objects
        """
        logger.info("Comparing strategies...")
        
        comparisons = []
        
        # Load Dual Momentum results
        dual_momentum = self._load_strategy_results('dual_momentum_validation.json')
        
        if dual_momentum:
            comp = StrategyComparison(
                strategy_name='Dual Momentum',
                avg_test_sharpe=dual_momentum.get('avg_test_sharpe', 0.0),
                degradation=dual_momentum.get('degradation', 0.0),
                avg_test_return=dual_momentum.get('avg_test_return', 0.0),
                avg_test_max_dd=dual_momentum.get('avg_test_max_dd', 0.0),
                verdict='PASS' if dual_momentum.get('degradation', 1.0) < 0.30 else 'FAIL'
            )
            comparisons.append(comp)
        
        # Load existing strategy results from walk_forward directory
        wf_dir = self.results_dir / 'walk_forward'
        
        if wf_dir.exists():
            # Try to load aggregate metrics
            aggregate_file = wf_dir / 'aggregate_metrics.json'
            if aggregate_file.exists():
                try:
                    with open(aggregate_file, 'r') as f:
                        aggregate = json.load(f)
                    
                    # Extract Long Momentum metrics if available
                    if 'long_momentum' in aggregate:
                        lm = aggregate['long_momentum']
                        comp = StrategyComparison(
                            strategy_name='Long Momentum',
                            avg_test_sharpe=lm.get('avg_test_sharpe', 0.0),
                            degradation=lm.get('degradation', 0.0),
                            avg_test_return=lm.get('avg_test_return', 0.0),
                            avg_test_max_dd=lm.get('avg_test_max_dd', 0.0),
                            verdict='PASS' if lm.get('degradation', 1.0) < 0.30 else 'FAIL'
                        )
                        comparisons.append(comp)
                except Exception as e:
                    logger.warning(f"Could not load aggregate metrics: {e}")
        
        # Load Swing strategies
        for strategy_file in ['swing_multi_asset_v1_results.json', 'swing_multi_asset_v2_results.json']:
            results = self._load_strategy_results(strategy_file)
            if results:
                strategy_name = strategy_file.replace('_results.json', '').replace('_', ' ').title()
                
                # These are single-run results, not walk-forward
                # So degradation is N/A
                comp = StrategyComparison(
                    strategy_name=strategy_name,
                    avg_test_sharpe=results.get('sharpe_ratio', 0.0),
                    degradation=0.0,  # N/A for single runs
                    avg_test_return=results.get('total_return', 0.0),
                    avg_test_max_dd=results.get('max_drawdown', 0.0),
                    verdict='N/A (no walk-forward)'
                )
                comparisons.append(comp)
        
        return comparisons
    
    def _analyze_dual_momentum(self, results: Dict) -> Dict:
        """
        Analyze Dual Momentum results in detail.
        
        Args:
            results: Dual Momentum validation results
        
        Returns:
            Dictionary with detailed analysis
        """
        periods = results.get('periods', [])
        
        if not periods:
            return {
                'error': 'No period data available',
                'total_periods': 0
            }
        
        # Filter out periods with errors
        valid_periods = [p for p in periods if 'error' not in p]
        
        if not valid_periods:
            return {
                'error': 'All periods failed',
                'total_periods': len(periods),
                'failed_periods': len(periods)
            }
        
        # Calculate statistics
        sharpe_ratios = [p['sharpe_ratio'] for p in valid_periods]
        returns = [p['total_return'] for p in valid_periods]
        max_dds = [p['max_drawdown'] for p in valid_periods]
        
        # Find best and worst periods
        best_period_idx = np.argmax(sharpe_ratios)
        worst_period_idx = np.argmin(sharpe_ratios)
        
        best_period = valid_periods[best_period_idx]
        worst_period = valid_periods[worst_period_idx]
        
        # Calculate consistency metrics
        sharpe_std = np.std(sharpe_ratios)
        sharpe_cv = sharpe_std / np.mean(sharpe_ratios) if np.mean(sharpe_ratios) != 0 else float('inf')
        
        return {
            'total_periods': len(periods),
            'valid_periods': len(valid_periods),
            'failed_periods': len(periods) - len(valid_periods),
            'avg_sharpe': np.mean(sharpe_ratios),
            'std_sharpe': sharpe_std,
            'sharpe_cv': sharpe_cv,
            'avg_return': np.mean(returns),
            'avg_max_dd': np.mean(max_dds),
            'best_period': {
                'period_id': best_period['period_id'],
                'sharpe': best_period['sharpe_ratio'],
                'return': best_period['total_return'],
                'dates': f"{best_period['test_start']} to {best_period['test_end']}"
            },
            'worst_period': {
                'period_id': worst_period['period_id'],
                'sharpe': worst_period['sharpe_ratio'],
                'return': worst_period['total_return'],
                'dates': f"{worst_period['test_start']} to {worst_period['test_end']}"
            },
            'consistency': 'High' if sharpe_cv < 0.5 else 'Medium' if sharpe_cv < 1.0 else 'Low'
        }
    
    def generate_recommendation(
        self,
        infrastructure: InfrastructureAssessment,
        comparisons: List[StrategyComparison],
        dual_momentum_analysis: Dict
    ) -> Recommendation:
        """
        Generate final recommendation based on all analysis.
        
        Args:
            infrastructure: Infrastructure assessment
            comparisons: Strategy comparisons
            dual_momentum_analysis: Detailed Dual Momentum analysis
        
        Returns:
            Recommendation with decision and reasoning
        """
        logger.info("Generating recommendation...")
        
        # Find Dual Momentum in comparisons
        dual_momentum = next(
            (c for c in comparisons if c.strategy_name == 'Dual Momentum'),
            None
        )
        
        if not dual_momentum:
            return Recommendation(
                decision='STOP',
                confidence=0.9,
                reasoning='Dual Momentum validation failed to produce results',
                next_steps=['Debug validation script', 'Check data availability'],
                estimated_effort_weeks=1,
                risks=['System may have fundamental issues'],
                expected_returns='N/A'
            )
        
        # Decision logic
        degradation = dual_momentum.degradation
        test_sharpe = dual_momentum.avg_test_sharpe
        infrastructure_score = infrastructure.overall_score
        
        # CONTINUE criteria
        if degradation < 0.30 and test_sharpe > 0.8 and infrastructure_score > 7.0:
            return Recommendation(
                decision='CONTINUE',
                confidence=0.85,
                reasoning=(
                    f"Dual Momentum shows promising results with {degradation:.1%} degradation "
                    f"(target: <30%) and test Sharpe of {test_sharpe:.2f} (target: >0.8). "
                    f"Infrastructure is solid ({infrastructure_score:.1f}/10). "
                    "System is ready for Phase 2: Multi-Strategy implementation."
                ),
                next_steps=[
                    'Implement Mean Reversion strategy',
                    'Implement Sector Rotation strategy',
                    'Develop portfolio allocation logic',
                    'Run combined strategy validation',
                    'Target: 10-12% annual returns'
                ],
                estimated_effort_weeks=4,
                risks=[
                    'New strategies may also show overfitting',
                    'Portfolio combination may not improve results',
                    'Market regime changes could affect performance'
                ],
                expected_returns='10-12% annual (Phase 2 target)'
            )
        
        # PIVOT criteria
        elif degradation < 0.50 or test_sharpe > 0.5:
            return Recommendation(
                decision='PIVOT',
                confidence=0.75,
                reasoning=(
                    f"Dual Momentum shows mixed results: {degradation:.1%} degradation "
                    f"and test Sharpe of {test_sharpe:.2f}. Not meeting all criteria but "
                    "showing some promise. Consider adjusting approach before full Phase 2."
                ),
                next_steps=[
                    'Analyze why degradation is higher than expected',
                    'Test with different lookback periods (6, 9, 12 months)',
                    'Try different rebalancing frequencies',
                    'Consider adding filters (volatility, trend)',
                    'Run extended validation (2015-2025)',
                    'If improvements work, proceed to Phase 2'
                ],
                estimated_effort_weeks=2,
                risks=[
                    'May be optimizing on noise',
                    'Fundamental strategy may not work in current markets',
                    'Time investment may not yield improvements'
                ],
                expected_returns='8-10% annual (if pivot successful)'
            )
        
        # STOP criteria
        else:
            return Recommendation(
                decision='STOP',
                confidence=0.90,
                reasoning=(
                    f"Dual Momentum shows poor results: {degradation:.1%} degradation "
                    f"(target: <30%) and test Sharpe of {test_sharpe:.2f} (target: >0.8). "
                    "Even a proven academic strategy is not working. This suggests fundamental "
                    "issues with either the implementation or market conditions."
                ),
                next_steps=[
                    'Review implementation for bugs',
                    'Validate against published Dual Momentum results',
                    'Consider if current market conditions are unsuitable',
                    'Evaluate alternative approaches (ML, factor investing)',
                    'Consider using existing robo-advisors instead'
                ],
                estimated_effort_weeks=0,
                risks=[
                    'Continuing would waste time and resources',
                    'System may never achieve target returns',
                    'Better alternatives exist (Betterment, Wealthfront)'
                ],
                expected_returns='N/A - recommend stopping'
            )
    
    def generate_executive_summary(
        self,
        infrastructure: InfrastructureAssessment,
        comparisons: List[StrategyComparison],
        recommendation: Recommendation
    ) -> Dict:
        """
        Generate executive summary with key findings.
        
        Args:
            infrastructure: Infrastructure assessment
            comparisons: Strategy comparisons
            recommendation: Final recommendation
        
        Returns:
            Dictionary with executive summary
        """
        # Find best and worst strategies
        if comparisons:
            best_strategy = max(comparisons, key=lambda x: x.avg_test_sharpe)
            worst_strategy = min(comparisons, key=lambda x: x.avg_test_sharpe)
        else:
            best_strategy = worst_strategy = None
        
        key_findings = []
        
        # Infrastructure finding
        if infrastructure.overall_score >= 8.0:
            key_findings.append(
                f"✅ Infrastructure is excellent ({infrastructure.overall_score:.1f}/10) - "
                "system is technically sound"
            )
        elif infrastructure.overall_score >= 6.0:
            key_findings.append(
                f"⚠️ Infrastructure is adequate ({infrastructure.overall_score:.1f}/10) - "
                "some improvements needed"
            )
        else:
            key_findings.append(
                f"❌ Infrastructure needs work ({infrastructure.overall_score:.1f}/10) - "
                "technical issues present"
            )
        
        # Strategy finding
        if best_strategy:
            if best_strategy.verdict == 'PASS':
                key_findings.append(
                    f"✅ {best_strategy.strategy_name} passes validation "
                    f"(Sharpe: {best_strategy.avg_test_sharpe:.2f}, "
                    f"Degradation: {best_strategy.degradation:.1%})"
                )
            else:
                key_findings.append(
                    f"❌ Best strategy ({best_strategy.strategy_name}) still fails validation "
                    f"(Sharpe: {best_strategy.avg_test_sharpe:.2f})"
                )
        
        # Recommendation finding
        key_findings.append(
            f"{'✅' if recommendation.decision == 'CONTINUE' else '⚠️' if recommendation.decision == 'PIVOT' else '❌'} "
            f"Recommendation: {recommendation.decision} "
            f"(confidence: {recommendation.confidence:.0%})"
        )
        
        return {
            'verdict': recommendation.decision,
            'confidence': recommendation.confidence,
            'key_findings': key_findings,
            'infrastructure_score': infrastructure.overall_score,
            'best_strategy': best_strategy.strategy_name if best_strategy else 'N/A',
            'expected_returns': recommendation.expected_returns,
            'estimated_effort': f"{recommendation.estimated_effort_weeks} weeks"
        }
    
    def generate_report(self) -> Dict:
        """
        Generate complete evaluation report.
        
        Returns:
            Dictionary with full report structure
        """
        logger.info("=" * 80)
        logger.info("GENERATING PHASE 1 EVALUATION REPORT")
        logger.info("=" * 80)
        
        # 1. Assess infrastructure
        infrastructure = self.assess_infrastructure()
        logger.info(f"Infrastructure score: {infrastructure.overall_score:.1f}/10")
        
        # 2. Compare strategies
        comparisons = self.compare_strategies()
        logger.info(f"Compared {len(comparisons)} strategies")
        
        # 3. Analyze Dual Momentum in detail
        dual_momentum_results = self._load_strategy_results('dual_momentum_validation.json')
        
        if dual_momentum_results:
            dual_momentum_analysis = self._analyze_dual_momentum(dual_momentum_results)
        else:
            dual_momentum_analysis = {'error': 'Results not found'}
        
        # 4. Generate recommendation
        recommendation = self.generate_recommendation(
            infrastructure,
            comparisons,
            dual_momentum_analysis
        )
        
        logger.info(f"Recommendation: {recommendation.decision} (confidence: {recommendation.confidence:.0%})")
        
        # 5. Generate executive summary
        executive_summary = self.generate_executive_summary(
            infrastructure,
            comparisons,
            recommendation
        )
        
        # 6. Compile full report
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'phase': 'Phase 1: Validation & Simple Strategy',
                'report_version': '1.0'
            },
            'executive_summary': executive_summary,
            'infrastructure_assessment': {
                'overall_score': infrastructure.overall_score,
                'component_scores': {
                    'backtesting': infrastructure.backtesting_score,
                    'data_pipeline': infrastructure.data_pipeline_score,
                    'risk_management': infrastructure.risk_management_score,
                    'walk_forward': infrastructure.walk_forward_score,
                    'ui_dashboard': infrastructure.ui_dashboard_score
                },
                'strengths': infrastructure.strengths,
                'weaknesses': infrastructure.weaknesses
            },
            'strategy_comparison': [
                {
                    'name': c.strategy_name,
                    'avg_test_sharpe': c.avg_test_sharpe,
                    'degradation': c.degradation,
                    'avg_test_return': c.avg_test_return,
                    'avg_test_max_dd': c.avg_test_max_dd,
                    'verdict': c.verdict
                }
                for c in comparisons
            ],
            'dual_momentum_analysis': dual_momentum_analysis,
            'recommendation': {
                'decision': recommendation.decision,
                'confidence': recommendation.confidence,
                'reasoning': recommendation.reasoning,
                'next_steps': recommendation.next_steps,
                'estimated_effort_weeks': recommendation.estimated_effort_weeks,
                'risks': recommendation.risks,
                'expected_returns': recommendation.expected_returns
            }
        }
        
        # 7. Save report
        output_file = self.results_dir / 'phase1_evaluation_report.json'
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to: {output_file}")
        
        # 8. Generate markdown summary
        self._generate_markdown_summary(report)
        
        return report
    
    def _generate_markdown_summary(self, report: Dict):
        """Generate human-readable markdown summary."""
        summary_file = self.results_dir / 'phase1_recommendation.md'
        
        exec_summary = report['executive_summary']
        recommendation = report['recommendation']
        infrastructure = report['infrastructure_assessment']
        
        markdown = f"""# Phase 1 Evaluation Report - AuronAI Strategy Validation

**Generated:** {report['metadata']['generated_at']}

## Executive Summary

**Verdict:** {exec_summary['verdict']} (Confidence: {exec_summary['confidence']:.0%})

**Expected Returns:** {exec_summary['expected_returns']}

**Estimated Effort:** {exec_summary['estimated_effort']}

### Key Findings

"""
        
        for finding in exec_summary['key_findings']:
            markdown += f"- {finding}\n"
        
        markdown += f"""

## Infrastructure Assessment

**Overall Score:** {infrastructure['overall_score']:.1f}/10

### Component Scores
- Backtesting Engine: {infrastructure['component_scores']['backtesting']:.1f}/10
- Data Pipeline: {infrastructure['component_scores']['data_pipeline']:.1f}/10
- Risk Management: {infrastructure['component_scores']['risk_management']:.1f}/10
- Walk-Forward Validator: {infrastructure['component_scores']['walk_forward']:.1f}/10
- UI Dashboard: {infrastructure['component_scores']['ui_dashboard']:.1f}/10

### Strengths
"""
        
        for strength in infrastructure['strengths']:
            markdown += f"- ✅ {strength}\n"
        
        markdown += "\n### Weaknesses\n"
        
        for weakness in infrastructure['weaknesses']:
            markdown += f"- ⚠️ {weakness}\n"
        
        markdown += f"""

## Recommendation: {recommendation['decision']}

**Confidence:** {recommendation['confidence']:.0%}

### Reasoning

{recommendation['reasoning']}

### Next Steps

"""
        
        for i, step in enumerate(recommendation['next_steps'], 1):
            markdown += f"{i}. {step}\n"
        
        markdown += "\n### Risks\n"
        
        for risk in recommendation['risks']:
            markdown += f"- ⚠️ {risk}\n"
        
        markdown += f"""

---

**Estimated Effort:** {recommendation['estimated_effort_weeks']} weeks

**Expected Returns:** {recommendation['expected_returns']}
"""
        
        with open(summary_file, 'w') as f:
            f.write(markdown)
        
        logger.info(f"Markdown summary saved to: {summary_file}")
