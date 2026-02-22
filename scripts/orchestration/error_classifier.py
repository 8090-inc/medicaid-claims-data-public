"""Error classification for the pipeline.

Classifies errors into severity levels:
- CRITICAL: Halt entire pipeline (DB connection failure, missing input, memory exhaustion)
- ERROR: Fail current milestone, continue pipeline if configured
- WARNING: Log and proceed (non-fatal data issues, degraded results)
"""

import logging
from enum import Enum

logger = logging.getLogger('medicaid_fwa.error_classifier')


class ErrorSeverity(Enum):
    CRITICAL = 'CRITICAL'
    ERROR = 'ERROR'
    WARNING = 'WARNING'


# Exception types that warrant CRITICAL classification
CRITICAL_EXCEPTIONS = (
    OSError,           # disk full, permission denied
    MemoryError,       # memory exhaustion
    SystemError,       # interpreter-level failure
    KeyboardInterrupt, # user abort
)

# Substrings in error messages that indicate CRITICAL severity
CRITICAL_PATTERNS = [
    'database is locked',
    'disk full',
    'out of memory',
    'connection refused',
    'missing input',
    'csv file not found',
    'duckdb',
    'could not open',
    'permission denied',
]

# Substrings that indicate WARNING (non-fatal)
WARNING_PATTERNS = [
    'no data found',
    'empty result',
    'skipping',
    'fallback',
    'not available',
    'deprecated',
]


def classify_error(exception, context=''):
    """Classify an exception into a severity level.

    Args:
        exception: The exception instance.
        context: Optional string describing where the error occurred.

    Returns:
        ErrorSeverity enum value.
    """
    if isinstance(exception, CRITICAL_EXCEPTIONS):
        return ErrorSeverity.CRITICAL

    msg = str(exception).lower()

    for pattern in CRITICAL_PATTERNS:
        if pattern in msg:
            return ErrorSeverity.CRITICAL

    for pattern in WARNING_PATTERNS:
        if pattern in msg:
            return ErrorSeverity.WARNING

    return ErrorSeverity.ERROR


def should_halt_pipeline(severity):
    """Determine if the pipeline should halt for a given severity.

    Args:
        severity: ErrorSeverity enum value.

    Returns:
        True if pipeline should stop.
    """
    return severity == ErrorSeverity.CRITICAL


def format_error_context(exception, milestone=None, script=None, row_count=None):
    """Create a structured error context dict for logging.

    Args:
        exception: The exception instance.
        milestone: Optional milestone name/number.
        script: Optional script filename.
        row_count: Optional row count at time of error.

    Returns:
        dict with error context fields.
    """
    ctx = {
        'error_type': type(exception).__name__,
        'error_message': str(exception),
        'severity': classify_error(exception).value,
    }
    if milestone:
        ctx['milestone'] = milestone
    if script:
        ctx['script'] = script
    if row_count is not None:
        ctx['row_count'] = row_count
    return ctx
