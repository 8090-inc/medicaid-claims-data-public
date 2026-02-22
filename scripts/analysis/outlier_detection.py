"""Statistical outlier detection — extracted from StatisticalAnalyzer."""

import logging
import math

import numpy as np

logger = logging.getLogger('medicaid_fwa.analysis')


def detect_zscore_outliers(con, metric='paid_per_claim', z_threshold=3.0, min_claims=10):
    """Detect providers with z-scores exceeding threshold for a given metric.

    Args:
        con: DuckDB connection (read-only).
        metric: Column to analyze.
        z_threshold: Z-score cutoff.
        min_claims: Minimum claims for inclusion.

    Returns:
        list of outlier dicts with npi, code, z_score, value, mean, std.
    """
    rows = con.execute(f"""
        WITH code_stats AS (
            SELECT
                hcpcs_code,
                AVG(avg_paid_per_claim) AS mean_val,
                STDDEV(avg_paid_per_claim) AS std_val,
                COUNT(*) AS n_providers
            FROM provider_hcpcs
            GROUP BY hcpcs_code
            HAVING COUNT(*) >= 20 AND STDDEV(avg_paid_per_claim) > 0
        )
        SELECT
            ph.billing_npi, ph.hcpcs_code,
            ph.avg_paid_per_claim, cs.mean_val, cs.std_val,
            (ph.avg_paid_per_claim - cs.mean_val) / cs.std_val AS z_score,
            ph.total_claims
        FROM provider_hcpcs ph
        INNER JOIN code_stats cs ON ph.hcpcs_code = cs.hcpcs_code
        WHERE ph.total_claims >= {min_claims}
            AND (ph.avg_paid_per_claim - cs.mean_val) / cs.std_val > {z_threshold}
        ORDER BY z_score DESC
    """).fetchall()

    outliers = []
    for npi, code, value, mean, std, z, claims in rows:
        outliers.append({
            'npi': npi,
            'hcpcs_code': code,
            'value': value,
            'mean': mean,
            'std': std,
            'z_score': z,
            'claims': claims,
        })

    logger.info(f'Z-score detection: {len(outliers)} outliers (z>{z_threshold})')
    return outliers


def detect_iqr_outliers(con, multiplier=3.0, min_claims=10):
    """Detect outliers using interquartile range method.

    Args:
        con: DuckDB connection (read-only).
        multiplier: IQR multiplier for outlier threshold.
        min_claims: Minimum claims for inclusion.

    Returns:
        list of outlier dicts.
    """
    rows = con.execute(f"""
        WITH code_iqr AS (
            SELECT
                hcpcs_code,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY avg_paid_per_claim) AS q1,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY avg_paid_per_claim) AS q3,
                COUNT(*) AS n_providers
            FROM provider_hcpcs
            GROUP BY hcpcs_code
            HAVING COUNT(*) >= 20
        )
        SELECT
            ph.billing_npi, ph.hcpcs_code,
            ph.avg_paid_per_claim,
            ci.q1, ci.q3,
            ci.q3 - ci.q1 AS iqr,
            ph.total_claims
        FROM provider_hcpcs ph
        INNER JOIN code_iqr ci ON ph.hcpcs_code = ci.hcpcs_code
        WHERE ph.total_claims >= {min_claims}
            AND ci.q3 - ci.q1 > 0
            AND ph.avg_paid_per_claim > ci.q3 + {multiplier} * (ci.q3 - ci.q1)
        ORDER BY (ph.avg_paid_per_claim - ci.q3) / (ci.q3 - ci.q1) DESC
    """).fetchall()

    outliers = []
    for npi, code, value, q1, q3, iqr, claims in rows:
        outliers.append({
            'npi': npi,
            'hcpcs_code': code,
            'value': value,
            'q1': q1,
            'q3': q3,
            'iqr': iqr,
            'distance_from_fence': (value - (q3 + multiplier * iqr)),
            'claims': claims,
        })

    logger.info(f'IQR detection: {len(outliers)} outliers (>{multiplier}x IQR)')
    return outliers
