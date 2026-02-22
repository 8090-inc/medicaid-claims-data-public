"""Billing spike detection in provider time series."""

import logging

logger = logging.getLogger('medicaid_fwa.analysis')


def detect_monthly_spikes(con, ratio_threshold=3.0, min_monthly_paid=10000, limit=5000):
    """Detect month-over-month billing spikes.

    Args:
        con: DuckDB connection (read-only).
        ratio_threshold: Current/previous month ratio to flag.
        min_monthly_paid: Minimum monthly paid amount.
        limit: Maximum providers to analyze.

    Returns:
        list of spike dicts with npi, month, current_paid, previous_paid, ratio.
    """
    rows = con.execute(f"""
        WITH monthly_lag AS (
            SELECT
                billing_npi,
                claim_month,
                total_paid,
                LAG(total_paid) OVER (PARTITION BY billing_npi ORDER BY claim_month) AS prev_paid
            FROM provider_monthly
        )
        SELECT billing_npi, claim_month, total_paid, prev_paid,
               total_paid / prev_paid AS ratio
        FROM monthly_lag
        WHERE prev_paid > 0 AND total_paid > {min_monthly_paid}
            AND total_paid / prev_paid > {ratio_threshold}
        ORDER BY total_paid / prev_paid DESC
        LIMIT {limit}
    """).fetchall()

    spikes = []
    for npi, month, current, previous, ratio in rows:
        spikes.append({
            'npi': npi,
            'month': month,
            'current_paid': current,
            'previous_paid': previous,
            'ratio': round(ratio, 2),
        })

    logger.info(f'Spike detection: {len(spikes)} monthly spikes (>{ratio_threshold}x)')
    return spikes


def detect_year_over_year_growth(con, growth_threshold=2.0, min_annual_paid=50000):
    """Detect providers with abnormal year-over-year billing growth.

    Args:
        con: DuckDB connection (read-only).
        growth_threshold: YoY growth ratio to flag.
        min_annual_paid: Minimum annual paid amount.

    Returns:
        list of dicts with npi, year, current_annual, previous_annual, growth_ratio.
    """
    rows = con.execute(f"""
        WITH annual AS (
            SELECT
                billing_npi,
                EXTRACT(YEAR FROM claim_month::DATE) AS yr,
                SUM(total_paid) AS annual_paid
            FROM provider_monthly
            GROUP BY billing_npi, yr
        ),
        annual_lag AS (
            SELECT
                billing_npi, yr, annual_paid,
                LAG(annual_paid) OVER (PARTITION BY billing_npi ORDER BY yr) AS prev_annual
            FROM annual
        )
        SELECT billing_npi, yr, annual_paid, prev_annual,
               annual_paid / prev_annual AS growth
        FROM annual_lag
        WHERE prev_annual > 0 AND annual_paid > {min_annual_paid}
            AND annual_paid / prev_annual > {growth_threshold}
        ORDER BY growth DESC
    """).fetchall()

    growth_anomalies = []
    for npi, year, current, previous, growth in rows:
        growth_anomalies.append({
            'npi': npi,
            'year': int(year),
            'current_annual': current,
            'previous_annual': previous,
            'growth_ratio': round(growth, 2),
        })

    logger.info(f'YoY growth: {len(growth_anomalies)} anomalies (>{growth_threshold}x)')
    return growth_anomalies
