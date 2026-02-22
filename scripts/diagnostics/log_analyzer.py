"""Analyze pipeline log files for patterns, errors, and performance insights."""

import json
import os
import sys
from collections import Counter
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.project_config import LOGS_DIR


def parse_json_log(log_path):
    """Parse a JSON-lines log file.

    Args:
        log_path: Path to log file.

    Returns:
        list of parsed log entry dicts.
    """
    entries = []
    if not os.path.exists(log_path):
        return entries
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def analyze_log(log_path):
    """Analyze a log file for error patterns and performance.

    Args:
        log_path: Path to log file.

    Returns:
        dict with analysis results.
    """
    entries = parse_json_log(log_path)
    if not entries:
        return {'entries': 0, 'message': 'No log entries found'}

    level_counts = Counter(e.get('level', 'UNKNOWN') for e in entries)
    error_entries = [e for e in entries if e.get('level') in ('ERROR', 'CRITICAL')]
    milestone_entries = [e for e in entries if e.get('milestone')]

    milestones = {}
    for e in milestone_entries:
        m = e['milestone']
        if m not in milestones:
            milestones[m] = {'count': 0, 'errors': 0}
        milestones[m]['count'] += 1
        if e.get('level') in ('ERROR', 'CRITICAL'):
            milestones[m]['errors'] += 1

    return {
        'entries': len(entries),
        'level_distribution': dict(level_counts),
        'error_count': len(error_entries),
        'errors': [{'level': e.get('level'), 'message': e.get('message', '')[:200]} for e in error_entries[:20]],
        'milestones': milestones,
    }


def find_latest_log():
    """Find the most recent pipeline log file.

    Returns:
        Path to log file or None.
    """
    pipeline_log = os.path.join(LOGS_DIR, 'pipeline.log')
    if os.path.exists(pipeline_log):
        return pipeline_log
    return None


def find_latest_audit_log():
    """Find the most recent audit trail log.

    Returns:
        Path to audit log or None.
    """
    if not os.path.isdir(LOGS_DIR):
        return None
    audit_logs = sorted(
        [f for f in os.listdir(LOGS_DIR) if f.startswith('audit_trail_')],
        reverse=True,
    )
    return os.path.join(LOGS_DIR, audit_logs[0]) if audit_logs else None


def main():
    """Print log analysis report."""
    print('=' * 70)
    print('  PIPELINE LOG ANALYSIS')
    print('=' * 70)

    log_path = find_latest_log()
    if log_path:
        print(f'\n  Analyzing: {log_path}')
        analysis = analyze_log(log_path)
        print(f'  Total entries: {analysis["entries"]}')
        print(f'  Level distribution: {analysis.get("level_distribution", {})}')
        if analysis.get('errors'):
            print(f'\n  Recent errors ({analysis["error_count"]}):')
            for e in analysis['errors'][:5]:
                print(f'    [{e["level"]}] {e["message"]}')
    else:
        print('\n  No pipeline log found.')

    audit_path = find_latest_audit_log()
    if audit_path:
        print(f'\n  Latest audit trail: {audit_path}')
        audit = analyze_log(audit_path)
        print(f'  Audit entries: {audit["entries"]}')
    else:
        print('\n  No audit trail found.')

    print(f'\n{"=" * 70}')


if __name__ == '__main__':
    main()
