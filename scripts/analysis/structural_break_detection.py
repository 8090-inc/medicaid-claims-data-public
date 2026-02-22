"""Structural break detection in provider billing time series."""

import logging

import numpy as np

logger = logging.getLogger('medicaid_fwa.analysis')


def detect_cusum_breaks(con, min_months=12, threshold=5.0, limit=5000):
    """Detect structural breaks in provider monthly billing using CUSUM.

    Args:
        con: DuckDB connection (read-only).
        min_months: Minimum months of billing history.
        threshold: CUSUM threshold multiplier.
        limit: Maximum providers to analyze.

    Returns:
        list of dicts with npi, break_month, direction, magnitude.
    """
    providers = con.execute(f"""
        SELECT billing_npi, COUNT(DISTINCT claim_month) AS n_months
        FROM provider_monthly
        GROUP BY billing_npi
        HAVING COUNT(DISTINCT claim_month) >= {min_months}
        ORDER BY SUM(total_paid) DESC
        LIMIT {limit}
    """).fetchall()

    breaks = []
    for npi, n_months in providers:
        rows = con.execute("""
            SELECT claim_month, total_paid
            FROM provider_monthly
            WHERE billing_npi = ?
            ORDER BY claim_month
        """, [npi]).fetchall()

        values = np.array([r[1] for r in rows], dtype=float)
        months = [r[0] for r in rows]

        if len(values) < min_months:
            continue

        mean = np.mean(values)
        std = np.std(values)
        if std == 0:
            continue

        cusum_pos = 0
        cusum_neg = 0
        for i in range(1, len(values)):
            cusum_pos = max(0, cusum_pos + (values[i] - mean))
            cusum_neg = min(0, cusum_neg + (values[i] - mean))

            if cusum_pos > threshold * std:
                breaks.append({
                    'npi': npi,
                    'break_month': months[i],
                    'direction': 'increase',
                    'magnitude': float(cusum_pos / std),
                })
                cusum_pos = 0
            elif cusum_neg < -threshold * std:
                breaks.append({
                    'npi': npi,
                    'break_month': months[i],
                    'direction': 'decrease',
                    'magnitude': float(abs(cusum_neg) / std),
                })
                cusum_neg = 0

    logger.info(f'CUSUM analysis: {len(breaks)} structural breaks across '
                f'{len(providers)} providers')
    return breaks
