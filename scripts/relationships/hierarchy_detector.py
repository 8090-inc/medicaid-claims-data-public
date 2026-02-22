"""Organizational hierarchy detection from billing patterns."""

import logging

logger = logging.getLogger('medicaid_fwa.relationships')


def detect_billing_hierarchies(con):
    """Detect organizational hierarchies via fan-out patterns.

    Identifies billing NPIs that distribute claims across many servicing NPIs,
    suggesting organizational (group practice) structure.

    Args:
        con: DuckDB connection (read-only).

    Returns:
        list of dicts with 'billing_npi', 'servicing_count', 'total_paid', 'type'.
    """
    rows = con.execute("""
        SELECT
            billing_npi,
            COUNT(DISTINCT servicing_npi) AS servicing_count,
            SUM(total_paid) AS total_paid
        FROM billing_servicing_network
        WHERE billing_npi != servicing_npi
        GROUP BY billing_npi
        HAVING COUNT(DISTINCT servicing_npi) >= 5
        ORDER BY servicing_count DESC
    """).fetchall()

    hierarchies = []
    for billing, svc_count, paid in rows:
        hier_type = 'large_group' if svc_count >= 20 else 'small_group'
        hierarchies.append({
            'billing_npi': billing,
            'servicing_count': svc_count,
            'total_paid': paid,
            'type': hier_type,
        })

    logger.info(f'Detected {len(hierarchies)} billing hierarchies '
                f'({sum(1 for h in hierarchies if h["type"] == "large_group")} large groups)')
    return hierarchies


def detect_servicing_hubs(con, min_billing_partners=5):
    """Detect servicing NPIs that receive referrals from many billing NPIs.

    Args:
        con: DuckDB connection (read-only).
        min_billing_partners: Minimum billing partners to qualify.

    Returns:
        list of dicts with 'servicing_npi', 'billing_count', 'total_paid'.
    """
    rows = con.execute(f"""
        SELECT
            servicing_npi,
            COUNT(DISTINCT billing_npi) AS billing_count,
            SUM(total_paid) AS total_paid
        FROM billing_servicing_network
        WHERE billing_npi != servicing_npi
        GROUP BY servicing_npi
        HAVING COUNT(DISTINCT billing_npi) >= {min_billing_partners}
        ORDER BY billing_count DESC
    """).fetchall()

    hubs = [{'servicing_npi': s, 'billing_count': b, 'total_paid': p} for s, b, p in rows]
    logger.info(f'Detected {len(hubs)} servicing hubs (min {min_billing_partners} billing partners)')
    return hubs
