"""Base class for milestone execution with input validation and error handling.

Provides a standard structure for milestone scripts: validate inputs,
execute, validate outputs, log timing.
"""

import logging
import os
import time

from config.project_config import PROJECT_ROOT

logger = logging.getLogger('medicaid_fwa.milestone')


class MilestoneBase:
    """Base class for wrapping milestone execution with standard scaffolding.

    Subclasses implement `run()` with their actual logic.
    """

    name = 'unnamed'
    milestone_number = -1
    description = ''
    required_inputs = []   # list of file paths that must exist
    expected_outputs = []  # list of file paths that should be created

    def __init__(self):
        self._start_time = None
        self._elapsed = None

    def validate_inputs(self):
        """Check that all required input files exist.

        Returns:
            tuple of (ok: bool, missing: list)
        """
        missing = [p for p in self.required_inputs if not os.path.exists(p)]
        if missing:
            logger.error(f'[{self.name}] Missing required inputs: {missing}')
        return len(missing) == 0, missing

    def validate_outputs(self):
        """Check that all expected output files were created.

        Returns:
            tuple of (ok: bool, missing: list)
        """
        missing = [p for p in self.expected_outputs if not os.path.exists(p)]
        if missing:
            logger.warning(f'[{self.name}] Missing expected outputs: {missing}')
        return len(missing) == 0, missing

    def run(self):
        """Execute the milestone logic. Override in subclasses."""
        raise NotImplementedError

    def execute(self):
        """Full milestone execution with validation, timing, and error handling.

        Returns:
            bool indicating success.
        """
        logger.info(f'[{self.name}] Starting: {self.description}')
        self._start_time = time.time()

        # Pre-check
        ok, missing = self.validate_inputs()
        if not ok:
            logger.error(f'[{self.name}] Cannot proceed — missing inputs')
            return False

        # Execute
        try:
            self.run()
        except Exception as e:
            self._elapsed = time.time() - self._start_time
            logger.error(f'[{self.name}] Failed after {self._elapsed:.1f}s: {e}')
            raise

        self._elapsed = time.time() - self._start_time

        # Post-check
        ok, missing = self.validate_outputs()
        if not ok:
            logger.warning(f'[{self.name}] Completed with missing outputs')

        logger.info(f'[{self.name}] Completed in {self._elapsed:.1f}s')
        return True

    @property
    def elapsed(self):
        return self._elapsed
