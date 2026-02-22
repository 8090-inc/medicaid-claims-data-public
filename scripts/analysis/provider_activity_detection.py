"""Provider activity pattern detection — sudden start/stop analysis."""

import logging

logger = logging.getLogger('medicaid_fwa.analysis')


def detect_sudden_starts(con, min_first_month_paid=50000, max_prior_months=0):
    """Detect providers with sudden high-volume billing starts.

    Args:
        con: DuckDB connection (read-only).
        min_first_month_paid: Minimum paid in first billing month.
        max_prior_months: Maximum months before start (0 = new providers).

    Returns:
        list of dicts with npi, first_month, first_month_paid, total_paid.
    """
    rows = con.execute(f"""
        WITH first_months AS (
            SELECT
                billing_npi,
                MIN(claim_month) AS first_month,
                COUNT(DISTINCT claim_month) AS n_months
            FROM provider_monthly
            GROUP BY billing_npi
        ),
        first_month_paid AS (
            SELECT
                pm.billing_npi,
                fm.first_month,
                pm.total_paid AS first_month_paid,
                ps.total_paid AS total_paid,
                fm.n_months
            FROM first_months fm
            INNER JOIN provider_monthly pm
                ON fm.billing_npi = pm.billing_npi AND fm.first_month = pm.claim_month
            INNER JOIN provider_summary ps ON fm.billing_npi = ps.billing_npi
        )
        SELECT billing_npi, first_month, first_month_paid, total_paid
        FROM first_month_paid
        WHERE first_month_paid > {min_first_month_paid}
        ORDER BY first_month_paid DESC
    """).fetchall()

    starts = []
    for npi, month, first_paid, total in rows:
        starts.append({
            'npi': npi,
            'first_month': month,
            'first_month_paid': first_paid,
            'total_paid': total,
        })

    logger.info(f'Sudden starts: {len(starts)} providers (>=${min_first_month_paid:,.0f} first month)')
    return starts


def detect_sudden_stops(con, min_last_month_paid=50000, recent_months=6):
    """Detect providers who abruptly stopped billing.

    Args:
        con: DuckDB connection (read-only).
        min_last_month_paid: Minimum paid in last billing month.
        recent_months: How many months ago constitutes "recent".

    Returns:
        list of dicts with npi, last_month, last_month_paid, total_paid.
    """
    rows = con.execute(f"""
        WITH last_months AS (
            SELECT
                billing_npi,
                MAX(claim_month) AS last_month,
                COUNT(DISTINCT claim_month) AS n_months
            FROM provider_monthly
            GROUP BY billing_npi
            HAVING COUNT(DISTINCT claim_month) >= 6
        ),
        last_month_paid AS (
            SELECT
                lm.billing_npi,
                lm.last_month,
                pm.total_paid AS last_month_paid,
                ps.total_paid AS total_paid,
                lm.n_months
            FROM last_months lm
            INNER JOIN provider_monthly pm
                ON lm.billing_npi = pm.billing_npi AND lm.last_month = pm.claim_month
            INNER JOIN provider_summary ps ON lm.billing_npi = ps.billing_npi
        )
        SELECT billing_npi, last_month, last_month_paid, total_paid
        FROM last_month_paid
        WHERE last_month_paid > {min_last_month_paid}
            AND last_month < (SELECT MAX(claim_month) FROM provider_monthly)
        ORDER BY last_month_paid DESC
    """).fetchall()

    stops = []
    for npi, month, last_paid, total in rows:
        stops.append({
            'npi': npi,
            'last_month': month,
            'last_month_paid': last_paid,
            'total_paid': total,
        })

    logger.info(f'Sudden stops: {len(stops)} providers (>=${min_last_month_paid:,.0f} last month)')
    return stops
