"""Timing, memory tracking, and progress logging for milestones."""

import logging
import os
import time

logger = logging.getLogger('medicaid_fwa.performance')


class PerformanceTracker:
    """Tracks execution time and memory usage for a milestone."""

    def __init__(self, milestone_name):
        self._name = milestone_name
        self._start_time = None
        self._checkpoints = []

    def start(self):
        """Mark the start of execution."""
        self._start_time = time.time()
        logger.debug(f'[{self._name}] Timer started')

    def checkpoint(self, label, row_count=None):
        """Record an intermediate checkpoint.

        Args:
            label: Description of what was just completed.
            row_count: Optional row count at this point.
        """
        elapsed = time.time() - self._start_time if self._start_time else 0
        entry = {
            'label': label,
            'elapsed': round(elapsed, 2),
            'row_count': row_count,
            'memory_mb': _get_memory_usage_mb(),
        }
        self._checkpoints.append(entry)
        msg = f'[{self._name}] {label}: {elapsed:.1f}s'
        if row_count is not None:
            msg += f' ({row_count:,} rows)'
        logger.info(msg)
        print(f'  {msg}')

    def finish(self):
        """Mark the end of execution and return summary.

        Returns:
            dict with execution summary.
        """
        total = time.time() - self._start_time if self._start_time else 0
        summary = {
            'milestone': self._name,
            'total_seconds': round(total, 2),
            'checkpoints': self._checkpoints,
            'peak_memory_mb': max(
                (c['memory_mb'] for c in self._checkpoints if c['memory_mb'] is not None),
                default=None,
            ),
        }
        logger.info(f'[{self._name}] Finished: {total:.1f}s total')
        return summary


class ProgressReporter:
    """Reports progress for long-running operations within a milestone."""

    def __init__(self, total, label='items', report_every=1000):
        self._total = total
        self._label = label
        self._report_every = report_every
        self._processed = 0
        self._start = time.time()

    def update(self, count=1):
        """Record processing of count items and optionally log progress."""
        self._processed += count
        if self._processed % self._report_every == 0 or self._processed == self._total:
            elapsed = time.time() - self._start
            pct = (self._processed / self._total * 100) if self._total > 0 else 0
            rate = self._processed / elapsed if elapsed > 0 else 0
            print(f'    Progress: {self._processed:,}/{self._total:,} {self._label} '
                  f'({pct:.0f}%, {rate:.0f}/s)')

    @property
    def processed(self):
        return self._processed


def _get_memory_usage_mb():
    """Get current process memory usage in MB (macOS/Linux)."""
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return round(usage.ru_maxrss / (1024 * 1024), 1)  # macOS reports in bytes
    except Exception:
        return None
