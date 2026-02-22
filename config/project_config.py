"""Centralized project configuration — paths, constants, and runtime settings.

All scripts should import paths and settings from here instead of
recalculating PROJECT_ROOT or hardcoding directory names.
"""

import os

# ── Core paths ──────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
CONFIG_DIR = os.path.join(PROJECT_ROOT, 'config')
UTILS_DIR = os.path.join(PROJECT_ROOT, 'utils')
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
TESTS_DIR = os.path.join(PROJECT_ROOT, 'tests')

# ── Data paths ──────────────────────────────────────────────────────────
CSV_PATH = os.path.join(PROJECT_ROOT, 'medicaid-provider-spending.csv')
DB_PATH = os.path.join(PROJECT_ROOT, 'medicaid.duckdb')
PARQUET_PATH = os.path.join(PROJECT_ROOT, 'claims.parquet')

# ── Reference data ──────────────────────────────────────────────────────
REFERENCE_DIR = os.path.join(PROJECT_ROOT, 'reference_data')
NPPES_DIR = os.path.join(REFERENCE_DIR, 'nppes')
HCPCS_DIR = os.path.join(REFERENCE_DIR, 'hcpcs')
LEIE_DIR = os.path.join(REFERENCE_DIR, 'leie')
DQ_ATLAS_DIR = os.path.join(REFERENCE_DIR, 'dq_atlas')
POSITIVE_CONTROLS_DIR = os.path.join(REFERENCE_DIR, 'positive_controls')

# ── Output directories ──────────────────────────────────────────────────
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
ANALYSIS_DIR = os.path.join(OUTPUT_DIR, 'analysis')
CHARTS_DIR = os.path.join(OUTPUT_DIR, 'charts')
HYPOTHESES_DIR = os.path.join(OUTPUT_DIR, 'hypotheses')
FINDINGS_DIR = os.path.join(OUTPUT_DIR, 'findings')
QA_DIR = os.path.join(OUTPUT_DIR, 'qa')
CARDS_DIR = os.path.join(OUTPUT_DIR, 'cards')

# ── Key output files ────────────────────────────────────────────────────
CMS_REPORT_PATH = os.path.join(OUTPUT_DIR, 'cms_administrator_report.md')
EXECUTIVE_BRIEF_PATH = os.path.join(ANALYSIS_DIR, 'executive_brief.md')
FRAUD_PATTERNS_PATH = os.path.join(ANALYSIS_DIR, 'fraud_patterns.md')
ACTION_PLAN_PATH = os.path.join(ANALYSIS_DIR, 'action_plan_memo.md')
INDEX_PATH = os.path.join(ANALYSIS_DIR, 'INDEX.md')
CALIBRATION_PATH = os.path.join(ANALYSIS_DIR, 'method_calibration.csv')
PRUNED_METHODS_PATH = os.path.join(ANALYSIS_DIR, 'pruned_methods.csv')

# ── DuckDB settings ─────────────────────────────────────────────────────
DB_WRITE_THREADS = 16
DB_WRITE_MEMORY_LIMIT = '96GB'

# ── Pipeline settings ───────────────────────────────────────────────────
CHECKPOINT_PATH = os.path.join(PROJECT_ROOT, 'pipeline_checkpoints.json')
MAX_HYPOTHESIS_WORKERS = 10

# ── Chart settings ──────────────────────────────────────────────────────
CHART_DPI = 150
CHART_FORMAT = 'png'

# ── All output directories that should be created at startup ────────────
OUTPUT_SUBDIRS = [
    ANALYSIS_DIR,
    CHARTS_DIR,
    HYPOTHESES_DIR,
    FINDINGS_DIR,
    QA_DIR,
    CARDS_DIR,
    LOGS_DIR,
]
