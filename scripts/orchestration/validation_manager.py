"""Pre/post-condition validation for milestone execution.

Validates file existence, JSON structure, CSV columns, and markdown content.
"""

import csv
import json
import logging
import os

logger = logging.getLogger('medicaid_fwa.validation')


def validate_file_exists(path, label='file'):
    """Check that a file exists and is non-empty.

    Args:
        path: File path to check.
        label: Human-readable label for error messages.

    Returns:
        tuple of (ok: bool, message: str)
    """
    if not os.path.exists(path):
        return False, f'{label} not found: {path}'
    if os.path.getsize(path) == 0:
        return False, f'{label} is empty: {path}'
    return True, f'{label} OK: {path}'


def validate_json_file(path, required_keys=None):
    """Validate a JSON file can be parsed and optionally contains required keys.

    Args:
        path: Path to JSON file.
        required_keys: Optional list of keys that must be present in each object.

    Returns:
        tuple of (ok: bool, message: str, data_or_none)
    """
    ok, msg = validate_file_exists(path, 'JSON file')
    if not ok:
        return False, msg, None
    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f'Invalid JSON in {path}: {e}', None

    if required_keys and isinstance(data, list) and len(data) > 0:
        sample = data[0]
        missing = [k for k in required_keys if k not in sample]
        if missing:
            return False, f'JSON missing required keys {missing} in {path}', data

    return True, f'JSON valid: {path}', data


def validate_csv_file(path, expected_columns=None):
    """Validate a CSV file structure.

    Args:
        path: Path to CSV file.
        expected_columns: Optional list of column names to check.

    Returns:
        tuple of (ok: bool, message: str)
    """
    ok, msg = validate_file_exists(path, 'CSV file')
    if not ok:
        return False, msg
    try:
        with open(path) as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None:
                return False, f'CSV has no header: {path}'
            if expected_columns:
                missing = [c for c in expected_columns if c not in header]
                if missing:
                    return False, f'CSV missing columns {missing} in {path}'
    except Exception as e:
        return False, f'CSV read error in {path}: {e}'
    return True, f'CSV valid: {path}'


def validate_markdown_file(path, min_length=10):
    """Validate a markdown report is non-trivial.

    Args:
        path: Path to markdown file.
        min_length: Minimum character count.

    Returns:
        tuple of (ok: bool, message: str)
    """
    ok, msg = validate_file_exists(path, 'Markdown file')
    if not ok:
        return False, msg
    size = os.path.getsize(path)
    if size < min_length:
        return False, f'Markdown too short ({size} bytes): {path}'
    return True, f'Markdown valid ({size} bytes): {path}'


def validate_database_tables(con, expected_tables):
    """Verify that required DuckDB tables exist.

    Args:
        con: DuckDB connection.
        expected_tables: List of table names.

    Returns:
        tuple of (ok: bool, missing: list)
    """
    existing = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    missing = [t for t in expected_tables if t not in existing]
    return len(missing) == 0, missing
