"""Directory management — creation, validation, and cleanup.

Ensures all required output directories exist before pipeline execution.
"""

import os

from config.project_config import OUTPUT_SUBDIRS, PROJECT_ROOT


def ensure_output_directories():
    """Create all required output directories if they don't exist.

    Returns:
        list of directories that were newly created.
    """
    created = []
    for directory in OUTPUT_SUBDIRS:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            created.append(directory)
    return created


def validate_directory_structure():
    """Verify that all required directories exist and are writable.

    Returns:
        dict with 'valid' (bool) and 'missing' (list of missing paths).
    """
    missing = []
    for directory in OUTPUT_SUBDIRS:
        if not os.path.isdir(directory):
            missing.append(directory)
        elif not os.access(directory, os.W_OK):
            missing.append(f'{directory} (not writable)')
    return {
        'valid': len(missing) == 0,
        'missing': missing,
    }


def ensure_directory(path):
    """Create a single directory if it doesn't exist.

    Args:
        path: Directory path to create.
    """
    os.makedirs(path, exist_ok=True)


def get_relative_path(absolute_path):
    """Convert an absolute path to a project-relative path.

    Args:
        absolute_path: Full filesystem path.

    Returns:
        Path relative to PROJECT_ROOT, or the original path if not under PROJECT_ROOT.
    """
    try:
        return os.path.relpath(absolute_path, PROJECT_ROOT)
    except ValueError:
        return absolute_path
