"""Hypothesis feasibility assessment — data availability classification."""

import json
import logging
import os

from config.project_config import HYPOTHESES_DIR

logger = logging.getLogger('medicaid_fwa.hypotheses')


FEASIBILITY_LEVELS = {
    'fully_feasible': 'All required data fields are available',
    'partially_feasible': 'Core data available but some fields missing',
    'not_feasible': 'Required data not available in current dataset',
}


def assess_feasibility(hypothesis, available_columns):
    """Determine feasibility of a single hypothesis.

    Args:
        hypothesis: Hypothesis dict with 'method' and 'parameters'.
        available_columns: Set of available column names.

    Returns:
        Feasibility level string.
    """
    method = hypothesis.get('method', '')

    # Methods that work with the core dataset
    core_methods = [
        'z_score', 'iqr', 'gev', 'benford', 'percentile',
        'peer_comparison', 'temporal', 'network', 'concentration',
    ]
    if any(m in method for m in core_methods):
        return 'fully_feasible'

    # Methods that need additional data (units, geographic, etc.)
    if 'volume' in method or 'impossible' in method:
        return 'partially_feasible'

    return 'fully_feasible'


def build_feasibility_matrix(hypotheses, available_columns=None):
    """Build feasibility assessment for all hypotheses.

    Args:
        hypotheses: List of hypothesis dicts.
        available_columns: Set of available data columns.

    Returns:
        dict mapping hypothesis_id -> feasibility_level.
    """
    available_columns = available_columns or set()
    matrix = {}
    for h in hypotheses:
        matrix[h['id']] = assess_feasibility(h, available_columns)

    counts = {}
    for level in matrix.values():
        counts[level] = counts.get(level, 0) + 1
    logger.info(f'Feasibility matrix: {counts}')

    return matrix


def save_feasibility_matrix(matrix, output_dir=None):
    """Save the feasibility matrix to JSON.

    Args:
        matrix: dict from build_feasibility_matrix.
        output_dir: Output directory (default: output/hypotheses/).
    """
    output_dir = output_dir or HYPOTHESES_DIR
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, 'feasibility_matrix.json')
    with open(path, 'w') as f:
        json.dump(matrix, f, indent=2)
    logger.info(f'Feasibility matrix saved to {path}')
