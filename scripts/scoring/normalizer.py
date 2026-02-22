"""Score normalization — min-max, z-score, percentile rank normalization."""

import logging
import numpy as np

logger = logging.getLogger('medicaid_fwa.scoring')


def min_max_normalize(scores):
    """Normalize scores to [0, 1] range using min-max scaling.

    Args:
        scores: list or array of numeric scores.

    Returns:
        numpy array of normalized scores.
    """
    arr = np.array(scores, dtype=float)
    min_val = arr.min()
    max_val = arr.max()
    if max_val == min_val:
        return np.zeros_like(arr)
    return (arr - min_val) / (max_val - min_val)


def percentile_rank_normalize(scores):
    """Normalize scores to percentile ranks [0, 1].

    Args:
        scores: list or array of numeric scores.

    Returns:
        numpy array of percentile ranks.
    """
    from scipy.stats import rankdata
    arr = np.array(scores, dtype=float)
    ranks = rankdata(arr, method='average')
    return (ranks - 1) / (len(ranks) - 1) if len(ranks) > 1 else np.array([0.5])


def assign_confidence_tier(score):
    """Assign a confidence tier label based on score.

    Args:
        score: Normalized score [0, 1].

    Returns:
        'high', 'medium', or 'low'.
    """
    if score >= 0.8:
        return 'high'
    elif score >= 0.5:
        return 'medium'
    return 'low'
