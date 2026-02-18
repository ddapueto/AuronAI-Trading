#!/usr/bin/env python3
"""
Generate Phase 1 Evaluation Report.

This script analyzes validation results and generates a comprehensive
report with a clear recommendation: CONTINUE/PIVOT/STOP.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from auronai.analysis.evaluation_report import EvaluationReportGenerator
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Generate Phase 1 evaluation report."""
    
    logger.info("=" * 80)
    logger.info("PHASE 1 EVALUATION REPORT GENERATOR")
    logger.info("=" * 80)
    
    # Initialize report generator
    generator = EvaluationReportGenerator()
    
    # Generate report
    try:
        report = generator.generate_report()
        
        # Display key results
        logger.info("\n" + "=" * 80)
        logger.info("REPORT GENERATED SUCCESSFULLY")
        logger.info("=" * 80)
        
        exec_summary = report['executive_summary']
        recommendation = report['recommendation']
        
        logger.info(f"\n📊 VERDICT: {exec_summary['verdict']}")
        logger.info(f"🎯 Confidence: {exec_summary['confidence']:.0%}")
        logger.info(f"💰 Expected Returns: {exec_summary['expected_returns']}")
        logger.info(f"⏱️ Estimated Effort: {exec_summary['estimated_effort']}")
        
        logger.info("\n🔍 KEY FINDINGS:")
        for finding in exec_summary['key_findings']:
            logger.info(f"  {finding}")
        
        logger.info(f"\n💡 RECOMMENDATION: {recommendation['decision']}")
        logger.info(f"\n📝 Reasoning:")
        logger.info(f"  {recommendation['reasoning']}")
        
        logger.info(f"\n📋 NEXT STEPS:")
        for i, step in enumerate(recommendation['next_steps'], 1):
            logger.info(f"  {i}. {step}")
        
        logger.info("\n" + "=" * 80)
        logger.info("📄 Full report saved to: results/phase1_evaluation_report.json")
        logger.info("📄 Summary saved to: results/phase1_recommendation.md")
        logger.info("=" * 80)
        
        # Return exit code based on recommendation
        if recommendation['decision'] == 'CONTINUE':
            return 0
        elif recommendation['decision'] == 'PIVOT':
            return 1
        else:  # STOP
            return 2
        
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return 3


if __name__ == '__main__':
    sys.exit(main())
