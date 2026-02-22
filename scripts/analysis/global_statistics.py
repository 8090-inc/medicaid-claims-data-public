"""Global statistics computation — totals, averages, medians."""

import logging

logger = logging.getLogger('medicaid_fwa.analysis')


def compute_global_stats(con):
    """Compute global aggregate statistics from the claims table.

    Args:
        con: DuckDB connection (read-only).

    Returns:
        dict with total_rows, unique_billing_npis, total_paid, etc.
    """
    logger.info('Computing global statistics ...')
    stats = con.execute("""
        SELECT
            COUNT(*)                            AS total_rows,
            COUNT(DISTINCT billing_npi)         AS unique_billing_npis,
            COUNT(DISTINCT servicing_npi)       AS unique_servicing_npis,
            COUNT(DISTINCT hcpcs_code)          AS unique_hcpcs_codes,
            COUNT(DISTINCT claim_month)         AS unique_months,
            SUM(paid)                           AS total_paid,
            SUM(claims)                         AS total_claims,
            SUM(beneficiaries)                  AS total_beneficiaries,
            AVG(paid)                           AS avg_paid,
            STDDEV(paid)                        AS std_paid,
            SUM(CASE WHEN paid < 0 THEN 1 ELSE 0 END) AS negative_paid_rows,
            SUM(CASE WHEN servicing_npi IS NULL OR servicing_npi = '' THEN 1 ELSE 0 END) AS null_servicing_rows
        FROM claims
    """).fetchone()

    median_paid = con.execute(
        "SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY paid) FROM claims"
    ).fetchone()[0]

    profile = {
        'total_rows': stats[0],
        'unique_billing_npis': stats[1],
        'unique_servicing_npis': stats[2],
        'unique_hcpcs_codes': stats[3],
        'unique_months': stats[4],
        'total_paid': stats[5],
        'total_claims': stats[6],
        'total_beneficiaries': stats[7],
        'avg_paid': stats[8],
        'median_paid': median_paid,
        'std_paid': stats[9],
        'negative_paid_rows': stats[10],
        'null_servicing_rows': stats[11],
    }
    logger.info(f'  Total rows: {stats[0]:,}, Total paid: ${stats[5]:,.0f}')
    return profile
