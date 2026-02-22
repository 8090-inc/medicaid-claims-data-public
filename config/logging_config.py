"""Structured logging configuration for the Medicaid FWA Analytics Pipeline.

Provides console + rotating file logging with ISO 8601 timestamps,
JSON-structured context, and milestone-level progress tracking.
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime, timezone

from config.project_config import LOGS_DIR

# ── Log file paths ──────────────────────────────────────────────────────
PIPELINE_LOG = os.path.join(LOGS_DIR, 'pipeline.log')
AUDIT_LOG = os.path.join(LOGS_DIR, 'audit_trail.log')

# ── Rotation settings ───────────────────────────────────────────────────
MAX_LOG_BYTES = 50 * 1024 * 1024  # 50 MB
BACKUP_COUNT = 5


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON lines for machine parsing."""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if hasattr(record, 'milestone'):
            log_entry['milestone'] = record.milestone
        if hasattr(record, 'context') and record.context:
            log_entry['context'] = record.context
        if record.exc_info and record.exc_info[0] is not None:
            log_entry['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


class ConsoleFormatter(logging.Formatter):
    """Human-readable console formatter matching existing print() style."""

    LEVEL_PREFIXES = {
        'DEBUG': '    ',
        'INFO': '  ',
        'WARNING': '  WARNING: ',
        'ERROR': '  ERROR: ',
        'CRITICAL': '  CRITICAL: ',
    }

    def format(self, record):
        prefix = self.LEVEL_PREFIXES.get(record.levelname, '  ')
        milestone_tag = ''
        if hasattr(record, 'milestone') and record.milestone:
            milestone_tag = f'[{record.milestone}] '
        return f'{prefix}{milestone_tag}{record.getMessage()}'


def setup_logging(level=logging.INFO, console=True, file_logging=True):
    """Initialize the pipeline logging system.

    Args:
        level: Minimum log level (default INFO).
        console: Enable console output (default True).
        file_logging: Enable rotating file output (default True).

    Returns:
        The root logger configured for the pipeline.
    """
    os.makedirs(LOGS_DIR, exist_ok=True)

    root_logger = logging.getLogger('medicaid_fwa')
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(ConsoleFormatter())
        root_logger.addHandler(console_handler)

    if file_logging:
        file_handler = logging.handlers.RotatingFileHandler(
            PIPELINE_LOG,
            maxBytes=MAX_LOG_BYTES,
            backupCount=BACKUP_COUNT,
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name, milestone=None):
    """Get a named child logger, optionally tagged with a milestone.

    Args:
        name: Logger name (e.g., module or script name).
        milestone: Optional milestone identifier for tagging log entries.

    Returns:
        A logging.Logger instance under the 'medicaid_fwa' namespace.
    """
    logger = logging.getLogger(f'medicaid_fwa.{name}')
    if milestone:
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.milestone = milestone
            record.context = None
            return record

        logging.setLogRecordFactory(record_factory)
    return logger


def log_with_context(logger, level, message, **context):
    """Log a message with structured context data.

    Args:
        logger: Logger instance.
        level: Log level (e.g., logging.INFO).
        message: Log message string.
        **context: Key-value pairs to include as structured context.
    """
    record = logger.makeRecord(
        logger.name, level, '', 0, message, (), None,
    )
    record.context = context if context else None
    record.milestone = getattr(record, 'milestone', None)
    logger.handle(record)
