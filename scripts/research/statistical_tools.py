"""Statistical tools for research analysis — regression, clustering, time series."""

import logging

import numpy as np

logger = logging.getLogger('medicaid_fwa.research')


def compute_regression(x, y):
    """Simple linear regression using numpy.

    Args:
        x: array-like of independent variable values.
        y: array-like of dependent variable values.

    Returns:
        dict with 'slope', 'intercept', 'r_squared', 'n'.
    """
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    n = len(x)
    if n < 3:
        return {'slope': 0, 'intercept': 0, 'r_squared': 0, 'n': n}

    coeffs = np.polyfit(x, y, 1)
    slope, intercept = coeffs[0], coeffs[1]

    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    return {'slope': float(slope), 'intercept': float(intercept),
            'r_squared': float(r_squared), 'n': n}


def compute_descriptive_stats(values):
    """Compute descriptive statistics for a numeric array.

    Args:
        values: array-like of numeric values.

    Returns:
        dict with mean, median, std, min, max, p25, p75, p95, n.
    """
    arr = np.array(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    n = len(arr)
    if n == 0:
        return {'mean': 0, 'median': 0, 'std': 0, 'min': 0, 'max': 0,
                'p25': 0, 'p75': 0, 'p95': 0, 'n': 0}

    return {
        'mean': float(np.mean(arr)),
        'median': float(np.median(arr)),
        'std': float(np.std(arr)),
        'min': float(np.min(arr)),
        'max': float(np.max(arr)),
        'p25': float(np.percentile(arr, 25)),
        'p75': float(np.percentile(arr, 75)),
        'p95': float(np.percentile(arr, 95)),
        'n': n,
    }


def compute_z_scores(values):
    """Compute z-scores for each value relative to the array.

    Args:
        values: array-like of numeric values.

    Returns:
        numpy array of z-scores.
    """
    arr = np.array(values, dtype=float)
    mean = np.mean(arr)
    std = np.std(arr)
    if std == 0:
        return np.zeros_like(arr)
    return (arr - mean) / std


def detect_changepoints_cusum(values, threshold=5.0):
    """Detect changepoints using CUSUM (Cumulative Sum) method.

    Args:
        values: array-like of time-ordered values.
        threshold: CUSUM threshold for detecting a change.

    Returns:
        list of indices where changepoints were detected.
    """
    arr = np.array(values, dtype=float)
    n = len(arr)
    if n < 5:
        return []

    mean = np.mean(arr)
    cusum_pos = np.zeros(n)
    cusum_neg = np.zeros(n)
    changepoints = []

    for i in range(1, n):
        cusum_pos[i] = max(0, cusum_pos[i - 1] + (arr[i] - mean))
        cusum_neg[i] = min(0, cusum_neg[i - 1] + (arr[i] - mean))

        if cusum_pos[i] > threshold * np.std(arr):
            changepoints.append(i)
            cusum_pos[i] = 0
        elif cusum_neg[i] < -threshold * np.std(arr):
            changepoints.append(i)
            cusum_neg[i] = 0

    return changepoints


def compute_gini_coefficient(values):
    """Compute Gini coefficient for measuring concentration.

    Args:
        values: array-like of non-negative values.

    Returns:
        float Gini coefficient (0 = perfect equality, 1 = perfect inequality).
    """
    arr = np.array(values, dtype=float)
    arr = arr[arr >= 0]
    if len(arr) == 0 or np.sum(arr) == 0:
        return 0.0

    arr = np.sort(arr)
    n = len(arr)
    index = np.arange(1, n + 1)
    return float((2 * np.sum(index * arr) - (n + 1) * np.sum(arr)) / (n * np.sum(arr)))
