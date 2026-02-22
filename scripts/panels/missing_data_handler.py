"""Missing data handling for longitudinal panels — gap detection, interpolation."""

import logging

logger = logging.getLogger('medicaid_fwa.panels')


def detect_provider_gaps(con, min_gap_months=2):
    """Detect providers with gaps in their billing history.

    Args:
        con: DuckDB connection (read-only).
        min_gap_months: Minimum gap size to flag (default 2).

    Returns:
        list of dicts with provider NPI, gap start, gap end.
    """
    logger.info(f'Detecting provider billing gaps (min {min_gap_months} months) ...')
    rows = con.execute(f"""
        WITH months AS (
            SELECT DISTINCT billing_npi, claim_month
            FROM provider_monthly
        ),
        gaps AS (
            SELECT
                billing_npi, claim_month,
                LEAD(claim_month) OVER (PARTITION BY billing_npi ORDER BY claim_month) AS next_month,
                DATEDIFF('month',
                    CAST(claim_month || '-01' AS DATE),
                    CAST(LEAD(claim_month) OVER (PARTITION BY billing_npi ORDER BY claim_month) || '-01' AS DATE)
                ) AS gap_months
            FROM months
        )
        SELECT billing_npi, claim_month, next_month, gap_months
        FROM gaps
        WHERE gap_months >= {min_gap_months}
        ORDER BY gap_months DESC
        LIMIT 1000
    """).fetchall()

    gaps = [
        {'billing_npi': r[0], 'last_active': r[1], 'next_active': r[2], 'gap_months': r[3]}
        for r in rows
    ]
    logger.info(f'  Found {len(gaps)} billing gaps')
    return gaps
