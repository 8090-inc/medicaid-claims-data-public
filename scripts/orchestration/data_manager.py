"""Inter-milestone data handoff verification.

Validates that expected input files exist before a milestone runs
and expected output files are generated after completion.
"""

import json
import os
import logging

from config.project_config import (
    DB_PATH, CSV_PATH, FINDINGS_DIR, HYPOTHESES_DIR,
    ANALYSIS_DIR, CHARTS_DIR, OUTPUT_DIR, QA_DIR,
)

logger = logging.getLogger('medicaid_fwa.data_manager')

# Expected inputs for each milestone script (files that must exist before running)
MILESTONE_INPUTS = {
    '00_data_quality.py': [CSV_PATH],
    '01_setup_and_ingest.py': [CSV_PATH],
    '02_enrich_references.py': [DB_PATH],
    '03_eda.py': [DB_PATH],
    '04_generate_hypotheses.py': [DB_PATH],
    '05_run_hypotheses_1_to_5.py': [DB_PATH, os.path.join(HYPOTHESES_DIR, 'batch_00.json')],
    '06_run_ml_hypotheses.py': [DB_PATH],
    '07_run_domain_rules.py': [DB_PATH],
    '08_run_crossref_composite.py': [DB_PATH],
    '09_financial_impact.py': [DB_PATH],
    '10_generate_charts.py': [DB_PATH],
    '11_generate_report.py': [DB_PATH],
}

# Expected outputs for each milestone script (files that should exist after running)
MILESTONE_OUTPUTS = {
    '00_data_quality.py': [os.path.join(QA_DIR, 'data_quality_report.json')],
    '01_setup_and_ingest.py': [DB_PATH],
    '04_generate_hypotheses.py': [os.path.join(HYPOTHESES_DIR, 'batch_00.json')],
    '10_generate_charts.py': [CHARTS_DIR],
    '11_generate_report.py': [os.path.join(OUTPUT_DIR, 'cms_administrator_report.md')],
}


def verify_inputs(script_name):
    """Check that all required inputs exist before milestone execution.

    Args:
        script_name: The milestone script filename.

    Returns:
        tuple of (all_ok: bool, missing: list of missing file paths)
    """
    required = MILESTONE_INPUTS.get(script_name, [])
    missing = [p for p in required if not os.path.exists(p)]
    if missing:
        logger.warning(f'{script_name}: Missing inputs: {missing}')
    return len(missing) == 0, missing


def verify_outputs(script_name):
    """Check that expected outputs were generated after milestone execution.

    Args:
        script_name: The milestone script filename.

    Returns:
        tuple of (all_ok: bool, missing: list of missing file paths)
    """
    expected = MILESTONE_OUTPUTS.get(script_name, [])
    missing = [p for p in expected if not os.path.exists(p)]
    if missing:
        logger.warning(f'{script_name}: Missing outputs: {missing}')
    return len(missing) == 0, missing


def get_output_file_sizes(directory):
    """Get sizes of all files in a directory for audit logging.

    Args:
        directory: Path to scan.

    Returns:
        dict mapping filename -> size in bytes.
    """
    sizes = {}
    if os.path.isdir(directory):
        for fname in os.listdir(directory):
            fpath = os.path.join(directory, fname)
            if os.path.isfile(fpath):
                sizes[fname] = os.path.getsize(fpath)
    return sizes
