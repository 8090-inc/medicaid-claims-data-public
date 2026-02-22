#!/usr/bin/env python3
"""Master orchestrator: runs all milestones in sequence.

Usage:
    python3 scripts/run_all.py                    # Run full pipeline
    python3 scripts/run_all.py --start-from 5     # Resume from milestone 5
    python3 scripts/run_all.py --skip 13 131      # Skip milestones 13 and 13b
    python3 scripts/run_all.py --resume            # Resume from last checkpoint
"""

import argparse
import os
import sys
import subprocess
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)

# Ensure project root is on path for config imports
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.project_config import CSV_PATH, CHECKPOINT_PATH, OUTPUT_DIR
from config.logging_config import setup_logging, get_logger
from scripts.orchestration.milestone_manager import (
    MILESTONES,
    CheckpointManager,
    get_milestone_sequence,
)
from scripts.orchestration.execution_logger import ExecutionLogger
from scripts.orchestration.audit_logger import AuditLogger
from scripts.orchestration.data_manager import verify_inputs, verify_outputs

logger = get_logger('run_all')


def run_milestone(script_name, description):
    """Run a single milestone script, returning True on success."""
    script_path = os.path.join(SCRIPTS_DIR, script_name)

    start = time.time()
    result = subprocess.run(
        [sys.executable, script_path],
        cwd=PROJECT_ROOT,
        capture_output=False,
    )
    elapsed = time.time() - start

    return result.returncode == 0, elapsed


def parse_args():
    parser = argparse.ArgumentParser(description='Medicaid FWA Analytics Pipeline')
    parser.add_argument('--start-from', dest='start_from', default=None,
                        help='Start from a specific milestone (script name or number)')
    parser.add_argument('--skip', nargs='*', default=[],
                        help='Skip specific milestones (script names or numbers)')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from the last checkpoint')
    parser.add_argument('--reset', action='store_true',
                        help='Clear checkpoints and start fresh')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')
    return parser.parse_args()


def main():
    args = parse_args()

    # Initialize logging
    import logging
    level = getattr(logging, args.log_level)
    setup_logging(level=level)

    # Initialize checkpoint manager
    checkpoint = CheckpointManager()
    if args.reset:
        checkpoint.reset()
        print('  Checkpoints cleared.')

    t0 = time.time()

    print('=' * 70)
    print('  MEDICAID PROVIDER SPENDING: FRAUD, WASTE & ABUSE ANALYSIS')
    print('  Full Pipeline Execution')
    print('=' * 70)

    # Check for CSV
    if not os.path.exists(CSV_PATH):
        print(f'\nERROR: CSV file not found at {CSV_PATH}')
        print('Please ensure medicaid-provider-spending.csv is in the project root.')
        sys.exit(1)

    csv_size = os.path.getsize(CSV_PATH) / (1024 ** 3)
    print(f'\nCSV file found: {CSV_PATH}')
    print(f'CSV size: {csv_size:.2f} GB')

    # Determine starting point
    start_from = args.start_from
    if args.resume:
        resume_point = checkpoint.get_resume_point()
        if resume_point:
            start_from = resume_point
            print(f'\n  Resuming from: {resume_point}')
        else:
            print('\n  No checkpoint found — starting from beginning.')

    skip = set(args.skip)

    # Get filtered milestone sequence
    sequence = get_milestone_sequence(start_from=start_from, skip=skip)
    if not sequence:
        print('\n  No milestones to execute.')
        sys.exit(0)

    # Initialize execution tracking
    exec_logger = ExecutionLogger(len(sequence))
    audit = AuditLogger()
    audit.log_pipeline_start({
        'start_from': start_from,
        'skip': list(skip),
        'total_milestones': len(sequence),
    })
    checkpoint.mark_pipeline_start()

    # Execute milestones
    for i, (script_name, description, milestone_num) in enumerate(sequence):
        # Pre-flight input check
        inputs_ok, missing = verify_inputs(script_name)
        if not inputs_ok:
            logger.warning(f'Missing inputs for {script_name}: {missing}')

        exec_logger.log_milestone_start(description, script_name, i)
        audit.log_milestone_start(description, milestone_num)

        success, elapsed = run_milestone(script_name, description)

        exec_logger.log_milestone_end(description, success, elapsed)
        audit.log_milestone_end(description, success, elapsed)

        if success:
            checkpoint.mark_completed(script_name, elapsed)
            # Post-flight output check
            verify_outputs(script_name)
        else:
            print(f'\nPipeline stopped at: {description}')
            print('Fix the error and re-run with: python3 scripts/run_all.py --resume')
            break

    # Summary
    exec_logger.log_pipeline_summary()
    audit.log_pipeline_end(
        [(d, s) for d, s, _ in exec_logger.get_results()],
        time.time() - t0,
    )

    # Check final output
    report_path = os.path.join(OUTPUT_DIR, 'cms_administrator_report.md')
    if os.path.exists(report_path):
        size = os.path.getsize(report_path)
        print(f'\n  Final report: {report_path} ({size:,} bytes)')
        print(f'\n  Pipeline complete. Report is ready for review.')
    else:
        print(f'\n  Report not yet generated.')

    print(f'{"="*70}')


if __name__ == '__main__':
    main()
