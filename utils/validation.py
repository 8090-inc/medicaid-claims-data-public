"""Foundation validation utilities.

Verifies directory structure, configuration, dependencies, and system
requirements are satisfied before pipeline execution.
"""

import importlib
import os
import sys

from config.project_config import (
    CSV_PATH,
    DB_PATH,
    OUTPUT_SUBDIRS,
    PROJECT_ROOT,
)


def validate_python_version(min_version=(3, 7)):
    """Check that the Python version meets the minimum requirement."""
    current = sys.version_info[:2]
    if current < min_version:
        return False, f'Python {min_version[0]}.{min_version[1]}+ required, got {current[0]}.{current[1]}'
    return True, f'Python {current[0]}.{current[1]}'


def validate_dependencies():
    """Check that all required Python packages are importable.

    Returns:
        tuple of (all_ok: bool, results: list of (package, ok, version_or_error))
    """
    required = [
        'duckdb', 'numpy', 'scipy', 'sklearn', 'xgboost',
        'torch', 'matplotlib', 'yaml', 'joblib', 'requests', 'networkx',
    ]
    results = []
    all_ok = True
    for pkg in required:
        try:
            mod = importlib.import_module(pkg)
            version = getattr(mod, '__version__', 'installed')
            results.append((pkg, True, version))
        except ImportError:
            results.append((pkg, False, 'NOT INSTALLED'))
            all_ok = False
    return all_ok, results


def validate_input_data():
    """Check that the source CSV file exists.

    Returns:
        tuple of (exists: bool, path: str, size_gb: float or None)
    """
    if os.path.exists(CSV_PATH):
        size_gb = os.path.getsize(CSV_PATH) / (1024 ** 3)
        return True, CSV_PATH, size_gb
    return False, CSV_PATH, None


def validate_database():
    """Check that the DuckDB database file exists.

    Returns:
        tuple of (exists: bool, path: str, size_gb: float or None)
    """
    if os.path.exists(DB_PATH):
        size_gb = os.path.getsize(DB_PATH) / (1024 ** 3)
        return True, DB_PATH, size_gb
    return False, DB_PATH, None


def validate_output_directories():
    """Check that all output directories exist and are writable.

    Returns:
        tuple of (all_ok: bool, results: list of (dir_path, exists, writable))
    """
    results = []
    all_ok = True
    for directory in OUTPUT_SUBDIRS:
        exists = os.path.isdir(directory)
        writable = os.access(directory, os.W_OK) if exists else False
        results.append((directory, exists, writable))
        if not exists or not writable:
            all_ok = False
    return all_ok, results


def run_all_validations():
    """Run all foundation validation checks.

    Returns:
        dict with validation results.
    """
    py_ok, py_info = validate_python_version()
    deps_ok, deps = validate_dependencies()
    csv_ok, csv_path, csv_size = validate_input_data()
    db_ok, db_path, db_size = validate_database()
    dirs_ok, dirs = validate_output_directories()

    return {
        'python': {'ok': py_ok, 'info': py_info},
        'dependencies': {'ok': deps_ok, 'details': deps},
        'input_csv': {'ok': csv_ok, 'path': csv_path, 'size_gb': csv_size},
        'database': {'ok': db_ok, 'path': db_path, 'size_gb': db_size},
        'directories': {'ok': dirs_ok, 'details': dirs},
        'all_ok': py_ok and deps_ok and dirs_ok,
    }
