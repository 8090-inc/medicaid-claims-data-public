#!/usr/bin/env python3
"""Master orchestrator: runs all milestones in sequence.

Usage: python3 scripts/run_all.py
"""

import os
import sys
import subprocess
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)

MILESTONES = [
    ('00_data_quality.py', 'Milestone 0: CSV Data Quality Scan'),
    ('01_setup_and_ingest.py', 'Milestone 1: Data Ingestion'),
    ('02_enrich_references.py', 'Milestone 2: Reference Data Enrichment'),
    ('03_eda.py', 'Milestone 3: Exploratory Data Analysis'),
    ('04_generate_hypotheses.py', 'Milestone 4: Hypothesis Generation'),
    ('12_feasibility_matrix.py', 'Milestone 12: Hypothesis Feasibility Matrix'),
    ('05_run_hypotheses_1_to_5.py', 'Milestone 5: Parallel Hypothesis Testing (Cat 1-5)'),
    ('06_run_ml_hypotheses.py', 'Milestone 6: ML/DL Anomaly Detection'),
    ('07_run_domain_rules.py', 'Milestone 7: Domain-Specific Rules'),
    ('08_run_crossref_composite.py', 'Milestone 8: Cross-Reference & Composite'),
    ('15_build_dq_atlas_weights.py', 'Milestone 15: Build DQ Atlas State Weights'),
    ('09_financial_impact.py', 'Milestone 9: Financial Impact & Deduplication'),
    ('16_generate_current_pack.py', 'Milestone 16: Current Risk Queue Pack'),
    ('10_generate_charts.py', 'Milestone 10: Chart Generation'),
    ('11_generate_report.py', 'Milestone 11: Report Assembly'),
    ('13_panel_build.py', 'Milestone 13: Longitudinal Panel Build'),
    ('13_longitudinal_multivariate_analysis.py', 'Milestone 13b: Longitudinal Multivariate Analysis'),
    ('14_validation_calibration.py', 'Milestone 14: Validation & Calibration'),
    ('12_validate_hypotheses.py', 'Milestone 12b: Hypothesis Validation Summary'),
    ('18_generate_hypothesis_cards.py', 'Milestone 18: Hypothesis Cards'),
    ('17_generate_cards.py', 'Milestone 17: Executive Dashboard Cards'),
    ('19_generate_executive_brief.py', 'Milestone 19: Executive Brief'),
    ('20_generate_merged_cards.py', 'Milestone 20: Merged Aggregate + Hypothesis Cards'),
    ('21_generate_fraud_patterns.py', 'Milestone 21: Fraud Pattern Summary'),
    ('22_generate_action_plan.py', 'Milestone 22: Action Plan Memo + Priority Queue'),
    ('23_generate_provider_validation_scores.py', 'Milestone 23: Provider Validation Scores'),
]


def run_milestone(script_name, description):
    """Run a single milestone script, returning True on success."""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    print(f'\n{"="*70}')
    print(f'  {description}')
    print(f'  Running: python3 {script_path}')
    print(f'{"="*70}\n')

    start = time.time()
    result = subprocess.run(
        [sys.executable, script_path],
        cwd=PROJECT_ROOT,
        capture_output=False,
    )
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f'\n  FAILED: {description} (exit code {result.returncode}, {elapsed:.1f}s)')
        return False
    else:
        print(f'\n  COMPLETED: {description} ({elapsed:.1f}s)')
        return True


def main():
    t0 = time.time()

    print('='*70)
    print('  MEDICAID PROVIDER SPENDING: FRAUD, WASTE & ABUSE ANALYSIS')
    print('  Full Pipeline Execution')
    print('='*70)

    # Check for CSV
    csv_path = os.path.join(PROJECT_ROOT, 'medicaid-provider-spending.csv')
    if not os.path.exists(csv_path):
        print(f'\nERROR: CSV file not found at {csv_path}')
        print('Please ensure medicaid-provider-spending.csv is in the project root.')
        sys.exit(1)

    print(f'\nCSV file found: {csv_path}')
    csv_size = os.path.getsize(csv_path) / (1024**3)
    print(f'CSV size: {csv_size:.2f} GB')

    results = []
    for script_name, description in MILESTONES:
        success = run_milestone(script_name, description)
        results.append((description, success))
        if not success:
            print(f'\nPipeline stopped at: {description}')
            print('Fix the error and re-run from this milestone.')
            break

    # Summary
    print(f'\n{"="*70}')
    print('  PIPELINE SUMMARY')
    print(f'{"="*70}')
    for desc, success in results:
        status = 'PASS' if success else 'FAIL'
        print(f'  [{status}] {desc}')
    print(f'\n  Total time: {time.time() - t0:.0f}s ({(time.time() - t0) / 60:.1f} min)')

    # Check final output
    report_path = os.path.join(PROJECT_ROOT, 'output', 'cms_administrator_report.md')
    if os.path.exists(report_path):
        size = os.path.getsize(report_path)
        print(f'\n  Final report: {report_path} ({size:,} bytes)')
        print(f'\n  Pipeline complete. Report is ready for review.')
    else:
        print(f'\n  Report not yet generated.')

    print(f'{"="*70}')


if __name__ == '__main__':
    main()
