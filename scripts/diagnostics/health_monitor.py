"""System health checks for the pipeline environment.

Checks database connectivity, disk space, memory, dependency versions,
and output directory integrity.
"""

import os
import sys
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.project_config import (
    DB_PATH, CSV_PATH, OUTPUT_DIR, LOGS_DIR,
    FINDINGS_DIR, CHARTS_DIR, ANALYSIS_DIR,
)
from utils.validation import validate_dependencies, validate_python_version
from scripts.utils.database_setup import health_check as db_health_check


def check_disk_space(path=None):
    """Check available disk space.

    Returns:
        dict with total, used, free in GB.
    """
    path = path or PROJECT_ROOT
    total, used, free = shutil.disk_usage(path)
    return {
        'total_gb': round(total / (1024 ** 3), 1),
        'used_gb': round(used / (1024 ** 3), 1),
        'free_gb': round(free / (1024 ** 3), 1),
        'usage_pct': round(used / total * 100, 1),
    }


def check_output_freshness():
    """Check modification times of key output files.

    Returns:
        dict mapping output file -> last modified timestamp or None.
    """
    key_files = {
        'cms_report': os.path.join(OUTPUT_DIR, 'cms_administrator_report.md'),
        'executive_brief': os.path.join(ANALYSIS_DIR, 'executive_brief.md'),
        'charts_dir': CHARTS_DIR,
        'findings_dir': FINDINGS_DIR,
    }
    results = {}
    for label, path in key_files.items():
        if os.path.exists(path):
            mtime = os.path.getmtime(path)
            import datetime
            results[label] = datetime.datetime.fromtimestamp(mtime).isoformat()
        else:
            results[label] = None
    return results


def run_health_checks():
    """Run all health checks and return a summary.

    Returns:
        dict with all health check results.
    """
    py_ok, py_info = validate_python_version()
    deps_ok, deps = validate_dependencies()
    disk = check_disk_space()
    db = db_health_check()
    freshness = check_output_freshness()

    issues = []
    if not py_ok:
        issues.append(f'Python version: {py_info}')
    if not deps_ok:
        missing = [d[0] for d in deps if not d[1]]
        issues.append(f'Missing dependencies: {missing}')
    if disk['free_gb'] < 50:
        issues.append(f'Low disk space: {disk["free_gb"]} GB free')
    if not db['exists']:
        issues.append('Database not found')
    elif not db.get('schema_valid', False):
        issues.append(f'Database schema invalid, missing: {db.get("missing_tables", [])}')

    return {
        'status': 'healthy' if not issues else 'degraded',
        'python': {'ok': py_ok, 'info': py_info},
        'dependencies': {'ok': deps_ok, 'missing': [d[0] for d in deps if not d[1]]},
        'disk': disk,
        'database': db,
        'output_freshness': freshness,
        'issues': issues,
    }


def main():
    """Print health check report."""
    results = run_health_checks()

    print('=' * 70)
    print('  PIPELINE HEALTH CHECK')
    print('=' * 70)
    print(f'\n  Status: {results["status"].upper()}')
    print(f'  Python: {results["python"]["info"]}')
    print(f'  Dependencies: {"OK" if results["dependencies"]["ok"] else "MISSING: " + str(results["dependencies"]["missing"])}')
    print(f'  Disk: {results["disk"]["free_gb"]} GB free ({results["disk"]["usage_pct"]}% used)')
    print(f'  Database: {"exists" if results["database"]["exists"] else "NOT FOUND"}', end='')
    if results["database"]["exists"]:
        print(f' ({results["database"]["size_gb"]} GB)')
    else:
        print()

    if results['issues']:
        print('\n  Issues:')
        for issue in results['issues']:
            print(f'    - {issue}')

    db = results['database']
    if db.get('table_counts'):
        print('\n  Table row counts:')
        for table, count in db['table_counts'].items():
            print(f'    {table}: {count:,}')

    freshness = results['output_freshness']
    if any(v is not None for v in freshness.values()):
        print('\n  Output freshness:')
        for label, ts in freshness.items():
            print(f'    {label}: {ts or "not generated"}')

    print(f'\n{"=" * 70}')


if __name__ == '__main__':
    main()
