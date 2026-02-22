"""Immutable append-only audit trail for pipeline execution.

Logs all data transformations, configuration changes, and significant events
to support reproducibility and compliance reporting (7-year retention for
federal healthcare programs).
"""

import json
import logging
import os
from datetime import datetime, timezone

from config.project_config import LOGS_DIR

logger = logging.getLogger('medicaid_fwa.audit')


class AuditLogger:
    """Append-only audit trail logger."""

    def __init__(self, log_dir=None):
        self._log_dir = log_dir or LOGS_DIR
        os.makedirs(self._log_dir, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        self._log_path = os.path.join(self._log_dir, f'audit_trail_{timestamp}.log')
        self._events = []

    @property
    def log_path(self):
        return self._log_path

    def log_event(self, event_type, details, milestone=None):
        """Log an audit event.

        Args:
            event_type: Category of event (e.g., 'ingestion', 'transformation', 'output').
            details: dict of event-specific details.
            milestone: Optional milestone identifier.
        """
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': event_type,
            'milestone': milestone,
            'details': details,
        }
        self._events.append(entry)
        with open(self._log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        logger.info(f'Audit: {event_type} — {details.get("summary", "")}')

    def log_pipeline_start(self, config_snapshot):
        """Log pipeline execution start with configuration snapshot."""
        self.log_event('pipeline_start', {
            'summary': 'Pipeline execution started',
            'config': config_snapshot,
        })

    def log_pipeline_end(self, results, total_time):
        """Log pipeline completion with summary results."""
        self.log_event('pipeline_end', {
            'summary': f'Pipeline completed in {total_time:.1f}s',
            'milestone_results': results,
            'total_time_seconds': total_time,
        })

    def log_milestone_start(self, milestone_name, milestone_number):
        """Log milestone execution start."""
        self.log_event('milestone_start', {
            'summary': f'Starting {milestone_name}',
            'milestone_number': milestone_number,
        }, milestone=milestone_name)

    def log_milestone_end(self, milestone_name, success, elapsed, row_count=None, output_files=None):
        """Log milestone completion."""
        self.log_event('milestone_end', {
            'summary': f'{"PASS" if success else "FAIL"}: {milestone_name} ({elapsed:.1f}s)',
            'success': success,
            'elapsed_seconds': elapsed,
            'row_count': row_count,
            'output_files': output_files or [],
        }, milestone=milestone_name)

    def log_data_transformation(self, milestone, operation, input_rows, output_rows, details=None):
        """Log a data transformation with row counts."""
        self.log_event('data_transformation', {
            'summary': f'{operation}: {input_rows} → {output_rows} rows',
            'operation': operation,
            'input_rows': input_rows,
            'output_rows': output_rows,
            'details': details,
        }, milestone=milestone)

    def log_finding(self, milestone, finding_count, total_impact):
        """Log findings generation summary."""
        self.log_event('findings', {
            'summary': f'{finding_count} findings, impact: {total_impact}',
            'finding_count': finding_count,
            'total_impact': total_impact,
        }, milestone=milestone)

    def get_events(self):
        """Return all events logged in this session."""
        return list(self._events)
