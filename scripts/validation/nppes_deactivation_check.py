"""NPPES deactivation cross-referencing for provider validation."""

import logging

logger = logging.getLogger('medicaid_fwa.validation')


def check_nppes_deactivations(con):
    """Find providers billing after their NPPES deactivation date.

    Args:
        con: DuckDB connection (read-only).

    Returns:
        list of finding dicts for providers billing after deactivation.
    """
    # Check if providers table has deactivation_date column
    try:
        cols = con.execute("SELECT column_name FROM information_schema.columns "
                           "WHERE table_name = 'providers'").fetchall()
        col_names = {c[0] for c in cols}
    except Exception:
        col_names = set()

    if 'deactivation_date' not in col_names:
        logger.info('No deactivation_date column in providers table — skipping check')
        return []

    rows = con.execute("""
        SELECT
            p.npi,
            p.deactivation_date,
            ps.total_paid,
            ps.total_claims,
            MAX(c.claim_month) AS last_claim_month
        FROM providers p
        INNER JOIN provider_summary ps ON p.npi = ps.billing_npi
        INNER JOIN claims c ON c.billing_npi = p.npi
        WHERE p.deactivation_date IS NOT NULL
            AND p.deactivation_date != ''
        GROUP BY p.npi, p.deactivation_date, ps.total_paid, ps.total_claims
        HAVING MAX(c.claim_month) > p.deactivation_date
        ORDER BY ps.total_paid DESC
    """).fetchall()

    findings = []
    for npi, deact_date, paid, claims, last_claim in rows:
        findings.append({
            'hypothesis_id': 'NPPES_DEACTIVATION',
            'flagged_providers': [npi],
            'total_impact': paid,
            'confidence': 0.85,
            'method_name': 'nppes_deactivation_check',
            'evidence': (
                f'Provider {npi} deactivated on {deact_date} but has claims through '
                f'{last_claim}. Total payments: ${paid:,.2f}.'
            ),
        })

    logger.info(f'NPPES deactivation check: {len(findings)} providers billing after deactivation')
    return findings


def check_nppes_missing_providers(con):
    """Identify billing providers not found in NPPES registry.

    Args:
        con: DuckDB connection (read-only).

    Returns:
        list of dicts with unregistered provider details.
    """
    try:
        rows = con.execute("""
            SELECT ps.billing_npi, ps.total_paid, ps.total_claims
            FROM provider_summary ps
            LEFT JOIN providers p ON ps.billing_npi = p.npi
            WHERE p.npi IS NULL
            ORDER BY ps.total_paid DESC
        """).fetchall()
    except Exception:
        logger.warning('Could not check for missing NPPES providers')
        return []

    missing = []
    for npi, paid, claims in rows:
        missing.append({
            'npi': npi,
            'total_paid': paid,
            'total_claims': claims,
        })

    logger.info(f'NPPES check: {len(missing)} billing providers not in NPPES registry')
    return missing
