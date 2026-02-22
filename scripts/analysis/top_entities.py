"""Top providers and HCPCS codes by spending."""

import logging

logger = logging.getLogger('medicaid_fwa.analysis')


def get_top_providers(con, limit=100):
    """Fetch top providers by total spending.

    Args:
        con: DuckDB connection (read-only).
        limit: Number of providers to return.

    Returns:
        list of dicts with provider details.
    """
    logger.info(f'Fetching top {limit} providers by spending ...')
    rows = con.execute(f"""
        SELECT
            ps.billing_npi,
            COALESCE(p.name, 'NPI ' || ps.billing_npi) AS name,
            COALESCE(p.state, '') AS state,
            COALESCE(p.specialty, '') AS specialty,
            ps.total_paid, ps.total_claims, ps.total_beneficiaries,
            ps.num_codes, ps.num_months
        FROM provider_summary ps
        LEFT JOIN providers p ON ps.billing_npi = p.npi
        ORDER BY ps.total_paid DESC
        LIMIT {limit}
    """).fetchall()

    return [
        {'npi': r[0], 'name': r[1], 'state': r[2], 'specialty': r[3],
         'total_paid': r[4], 'total_claims': r[5], 'total_beneficiaries': r[6],
         'num_codes': r[7], 'num_months': r[8]}
        for r in rows
    ]


def get_top_hcpcs(con, limit=100):
    """Fetch top HCPCS codes by total spending.

    Args:
        con: DuckDB connection (read-only).
        limit: Number of codes to return.

    Returns:
        list of dicts with code details.
    """
    logger.info(f'Fetching top {limit} HCPCS codes by spending ...')
    rows = con.execute(f"""
        SELECT
            hcpcs_code, num_providers, total_claims, total_paid,
            avg_paid_per_claim, median_paid_per_claim, p95_paid_per_claim
        FROM hcpcs_summary
        ORDER BY total_paid DESC
        LIMIT {limit}
    """).fetchall()

    return [
        {'code': r[0], 'num_providers': r[1], 'total_claims': r[2],
         'total_paid': r[3], 'avg_paid_per_claim': r[4],
         'median_paid_per_claim': r[5], 'p95_paid_per_claim': r[6]}
        for r in rows
    ]
