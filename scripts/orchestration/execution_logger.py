"""Execution logging and progress tracking for pipeline milestones.

Provides structured progress output, execution time tracking,
and pipeline summary reporting.
"""

import logging
import time

logger = logging.getLogger('medicaid_fwa.orchestration')


class ExecutionLogger:
    """Tracks and reports milestone execution progress."""

    def __init__(self, total_milestones):
        self._total = total_milestones
        self._completed = 0
        self._results = []
        self._start_time = time.time()

    def log_milestone_start(self, description, script_name, index):
        """Log the start of a milestone execution."""
        self._completed = index
        progress = f'[{index + 1}/{self._total}]'
        print(f'\n{"="*70}')
        print(f'  {progress} {description}')
        print(f'  Running: python3 scripts/{script_name}')
        print(f'{"="*70}\n')
        logger.info(f'{progress} Starting: {description}')

    def log_milestone_end(self, description, success, elapsed):
        """Log the completion of a milestone."""
        status = 'COMPLETED' if success else 'FAILED'
        print(f'\n  {status}: {description} ({elapsed:.1f}s)')
        self._results.append((description, success, elapsed))
        if success:
            logger.info(f'{status}: {description} ({elapsed:.1f}s)')
        else:
            logger.error(f'{status}: {description} ({elapsed:.1f}s)')

    def log_pipeline_summary(self):
        """Print and log the final pipeline summary."""
        total_time = time.time() - self._start_time
        passed = sum(1 for _, ok, _ in self._results if ok)
        failed = sum(1 for _, ok, _ in self._results if not ok)

        print(f'\n{"="*70}')
        print('  PIPELINE SUMMARY')
        print(f'{"="*70}')
        for desc, success, elapsed in self._results:
            status = 'PASS' if success else 'FAIL'
            print(f'  [{status}] {desc} ({elapsed:.1f}s)')

        print(f'\n  Passed: {passed}  Failed: {failed}  Total: {len(self._results)}')
        print(f'  Total time: {total_time:.0f}s ({total_time / 60:.1f} min)')
        print(f'{"="*70}')

        logger.info(f'Pipeline complete: {passed} passed, {failed} failed, {total_time:.0f}s total')

    def get_results(self):
        """Return list of (description, success, elapsed) tuples."""
        return list(self._results)
