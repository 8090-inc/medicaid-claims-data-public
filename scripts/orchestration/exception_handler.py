"""Centralized exception handling for pipeline operations.

Provides try-except wrappers for common operations (file I/O, database queries,
hypothesis execution) with proper logging and error classification.
"""

import logging
import traceback
from functools import wraps

from scripts.orchestration.error_classifier import (
    ErrorSeverity,
    classify_error,
    format_error_context,
)

logger = logging.getLogger('medicaid_fwa.exception_handler')


def handle_milestone(milestone_name):
    """Decorator for milestone functions — catches and classifies errors.

    Args:
        milestone_name: Human-readable milestone identifier.

    Returns:
        Decorator that wraps the milestone function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                severity = classify_error(e, context=milestone_name)
                ctx = format_error_context(e, milestone=milestone_name, script=func.__module__)
                if severity == ErrorSeverity.CRITICAL:
                    logger.critical(f'{milestone_name}: {e}', extra={'context': ctx})
                elif severity == ErrorSeverity.WARNING:
                    logger.warning(f'{milestone_name}: {e}', extra={'context': ctx})
                else:
                    logger.error(f'{milestone_name}: {e}', extra={'context': ctx})
                logger.debug(traceback.format_exc())
                raise
        return wrapper
    return decorator


def safe_file_operation(operation, path, default=None, milestone=None):
    """Execute a file operation safely with error handling.

    Args:
        operation: Callable that performs the file operation.
        path: File path being operated on.
        default: Value to return on failure.
        milestone: Optional milestone name for error context.

    Returns:
        Result of operation, or default on failure.
    """
    try:
        return operation(path)
    except Exception as e:
        severity = classify_error(e)
        ctx = format_error_context(e, milestone=milestone, script=path)
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f'File operation failed: {path} — {e}', extra={'context': ctx})
            raise
        logger.warning(f'File operation failed: {path} — {e}', extra={'context': ctx})
        return default


def safe_query(con, sql, params=None, milestone=None):
    """Execute a DuckDB query safely with error handling.

    Args:
        con: DuckDB connection.
        sql: SQL query string.
        params: Optional query parameters.
        milestone: Optional milestone name for error context.

    Returns:
        Query results list, or empty list on non-critical error.
    """
    try:
        if params:
            return con.execute(sql, params).fetchall()
        return con.execute(sql).fetchall()
    except Exception as e:
        severity = classify_error(e)
        ctx = format_error_context(e, milestone=milestone)
        ctx['sql_preview'] = sql[:200]
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f'Query failed: {e}', extra={'context': ctx})
            raise
        logger.warning(f'Query failed: {e}', extra={'context': ctx})
        return []


def safe_hypothesis_execution(func, hypothesis, con, milestone=None):
    """Execute a single hypothesis test safely.

    Per-hypothesis failures are logged but don't halt the pipeline.

    Args:
        func: Callable that tests the hypothesis.
        hypothesis: Hypothesis dict.
        con: DuckDB connection.
        milestone: Optional milestone name.

    Returns:
        List of findings, or empty list on failure.
    """
    h_id = hypothesis.get('id', 'unknown')
    try:
        return func(hypothesis, con)
    except Exception as e:
        ctx = format_error_context(e, milestone=milestone)
        ctx['hypothesis_id'] = h_id
        logger.warning(f'Hypothesis {h_id} failed: {e}', extra={'context': ctx})
        return []
