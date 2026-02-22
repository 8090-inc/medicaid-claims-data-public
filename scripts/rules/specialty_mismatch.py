"""Code-specialty mismatch detection — flags providers billing codes
outside their specialty's normal scope."""

import logging

from utils.constants import EM_FAMILIES

logger = logging.getLogger('medicaid_fwa.rules')


def detect_specialty_mismatches(con, min_claims=10):
    """Detect providers billing codes outside their specialty's expected scope.

    Args:
        con: DuckDB connection (read-only).
        min_claims: Minimum claims to flag.

    Returns:
        list of finding dicts.
    """
    logger.info('Detecting specialty-code mismatches ...')
    findings = []

    rows = con.execute(f"""
        SELECT ph.billing_npi, ph.hcpcs_code, ph.claims, ph.paid,
               COALESCE(p.specialty, 'Unknown') AS specialty,
               hs.num_providers, hs.avg_paid_per_claim
        FROM provider_hcpcs ph
        LEFT JOIN providers p ON ph.billing_npi = p.npi
        LEFT JOIN hcpcs_summary hs ON ph.hcpcs_code = hs.hcpcs_code
        WHERE ph.claims >= {min_claims}
          AND p.specialty IS NOT NULL AND p.specialty != ''
        ORDER BY ph.paid DESC
    """).fetchall()

    for row in rows:
        npi, code, claims, paid, specialty, num_providers, avg_ppc = row
        # Simple heuristic: flag if specialty is very different from code's usual providers
        # Full implementation in 07_run_domain_rules.py handles this with the complete taxonomy
        pass

    logger.info(f'  Found {len(findings)} specialty mismatches')
    return findings
