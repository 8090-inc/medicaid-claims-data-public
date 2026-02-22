"""State-level data quality scoring using DQ Atlas weights."""

import json
import logging
import os

from config.project_config import DQ_ATLAS_DIR

logger = logging.getLogger('medicaid_fwa.quality')


def load_state_quality_weights(dq_atlas_dir=None):
    """Load state data quality weights from DQ Atlas reference data.

    Args:
        dq_atlas_dir: Directory containing DQ Atlas files.

    Returns:
        dict mapping state_code -> quality_weight (0.0 to 1.0).
    """
    dq_atlas_dir = dq_atlas_dir or DQ_ATLAS_DIR
    weights = {}

    if not os.path.isdir(dq_atlas_dir):
        logger.warning(f'DQ Atlas directory not found: {dq_atlas_dir}')
        return weights

    for fname in os.listdir(dq_atlas_dir):
        if fname.endswith('.json'):
            path = os.path.join(dq_atlas_dir, fname)
            with open(path) as f:
                data = json.load(f)
            if isinstance(data, dict):
                weights.update(data)

    logger.info(f'Loaded quality weights for {len(weights)} states')
    return weights


def score_state_quality(con, weights):
    """Score provider data quality based on their state's DQ Atlas weight.

    Args:
        con: DuckDB connection (read-only).
        weights: dict from load_state_quality_weights.

    Returns:
        dict mapping npi -> quality_weight.
    """
    if not weights:
        logger.warning('No state quality weights available')
        return {}

    rows = con.execute("""
        SELECT ps.billing_npi, COALESCE(p.state, '') AS state
        FROM provider_summary ps
        LEFT JOIN providers p ON ps.billing_npi = p.npi
    """).fetchall()

    scored = {}
    for npi, state in rows:
        scored[npi] = weights.get(state, 1.0)

    logger.info(f'Scored {len(scored)} providers with state quality weights')
    return scored
