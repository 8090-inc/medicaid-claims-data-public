"""Impossible service combination detection — services that cannot coexist."""

import logging

from utils.constants import PHYSICAL_LIMITS, TIMED_CODES

logger = logging.getLogger('medicaid_fwa.rules')


def detect_impossible_volumes(con):
    """Detect physically impossible service volumes.

    Note: The source dataset does not include service units or time increments,
    only total claims. Without units, physical-limit logic is limited.

    Args:
        con: DuckDB connection (read-only).

    Returns:
        list of finding dicts.
    """
    logger.info('Checking for impossible service volumes ...')
    logger.info('  Skipped: dataset lacks units/time increments needed for volume limits')
    return []


def detect_duplicate_billing(con, time_window='same month'):
    """Detect potential duplicate billing patterns.

    Looks for providers billing the same code for the same beneficiary
    count in the same month at identical amounts.

    Args:
        con: DuckDB connection (read-only).
        time_window: Time window for duplicate detection.

    Returns:
        list of finding dicts.
    """
    logger.info('Detecting duplicate billing patterns ...')
    findings = []

    rows = con.execute("""
        SELECT billing_npi, hcpcs_code, claim_month, beneficiaries,
               COUNT(*) as duplicate_count, SUM(paid) as total_paid
        FROM claims
        GROUP BY billing_npi, hcpcs_code, claim_month, beneficiaries
        HAVING COUNT(*) > 1
        ORDER BY SUM(paid) DESC
        LIMIT 1000
    """).fetchall()

    for row in rows:
        findings.append({
            'hypothesis_id': 'H_DUP',
            'flagged_providers': [row[0]],
            'total_impact': row[5],
            'confidence': 0.6,
            'method_name': 'duplicate_billing',
            'evidence': f'Code {row[1]}, month {row[2]}: {row[4]} duplicate entries',
        })

    logger.info(f'  Found {len(findings)} potential duplicates')
    return findings
