#!/usr/bin/env python3
"""Project foundation setup — creates directories, validates config, checks dependencies.

Usage: python3 setup_project_foundation.py
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from config.project_config import OUTPUT_SUBDIRS, LOGS_DIR
from utils.directory_manager import ensure_output_directories
from utils.validation import run_all_validations


def main():
    print('=' * 70)
    print('  MEDICAID FWA ANALYTICS — PROJECT FOUNDATION SETUP')
    print('=' * 70)

    # 1. Create directories
    print('\n  Creating output directories ...')
    created = ensure_output_directories()
    if created:
        for d in created:
            print(f'    Created: {d}')
    else:
        print('    All directories already exist.')

    # 2. Run validations
    print('\n  Running validation checks ...')
    results = run_all_validations()

    # Python
    py = results['python']
    status = 'PASS' if py['ok'] else 'FAIL'
    print(f'    [{status}] Python version: {py["info"]}')

    # Dependencies
    deps = results['dependencies']
    dep_status = 'PASS' if deps['ok'] else 'FAIL'
    missing = [d[0] for d in deps['details'] if not d[1]]
    print(f'    [{dep_status}] Dependencies: {len(deps["details"]) - len(missing)}/{len(deps["details"])} installed')
    if missing:
        print(f'           Missing: {", ".join(missing)}')
        print(f'           Run: pip install -r requirements.txt')

    # Input CSV
    csv = results['input_csv']
    csv_status = 'PASS' if csv['ok'] else 'WARN'
    if csv['ok']:
        print(f'    [{csv_status}] Input CSV: {csv["size_gb"]:.2f} GB')
    else:
        print(f'    [{csv_status}] Input CSV: not found (needed for pipeline execution)')

    # Database
    db = results['database']
    db_status = 'PASS' if db['ok'] else 'WARN'
    if db['ok']:
        print(f'    [{db_status}] Database: {db["size_gb"]:.2f} GB')
    else:
        print(f'    [{db_status}] Database: not found (will be created by pipeline)')

    # Directories
    dirs = results['directories']
    dir_status = 'PASS' if dirs['ok'] else 'FAIL'
    print(f'    [{dir_status}] Output directories: {"all OK" if dirs["ok"] else "issues found"}')

    # Config file
    config_path = os.path.join(PROJECT_ROOT, 'config.yml')
    if os.path.exists(config_path):
        print(f'    [PASS] Configuration: config.yml present')
    else:
        print(f'    [WARN] Configuration: config.yml not found')

    # Summary
    print(f'\n{"=" * 70}')
    if results['all_ok']:
        print('  Foundation setup complete. Ready for pipeline execution.')
    else:
        print('  Foundation setup complete with warnings. See above for details.')
    print(f'{"=" * 70}')


if __name__ == '__main__':
    main()
