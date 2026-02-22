"""OIG LEIE exclusion list cross-referencing."""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger('medicaid_fwa.validation')


def check_leie_exclusions(con, leie_npi_set):
    """Cross-reference billing providers against the LEIE exclusion list.

    Args:
        con: DuckDB connection (read-only).
        leie_npi_set: Set of excluded NPI strings from leie_utils.build_leie_npi_set().

    Returns:
        list of finding dicts for providers found on the exclusion list.
    """
    if not leie_npi_set:
        logger.warning('Empty LEIE NPI set — skipping exclusion check')
        return []

    # Get all billing NPIs with their total payments
    rows = con.execute("""
        SELECT billing_npi, total_paid, total_claims
        FROM provider_summary
        ORDER BY total_paid DESC
    """).fetchall()

    findings = []
    for npi, paid, claims in rows:
        if npi in leie_npi_set:
            findings.append({
                'hypothesis_id': 'LEIE_EXCLUSION',
                'flagged_providers': [npi],
                'total_impact': paid,
                'confidence': 0.95,
                'method_name': 'oig_leie_cross_reference',
                'evidence': (
                    f'Provider {npi} found on OIG LEIE exclusion list. '
                    f'Total Medicaid payments: ${paid:,.2f} across {claims:,} claims.'
                ),
            })

    logger.info(f'LEIE check: {len(findings)} excluded providers found billing Medicaid')
    return findings


def check_leie_name_matches(con, leie_name_index):
    """Fuzzy match providers against LEIE by last name + state.

    Args:
        con: DuckDB connection (read-only).
        leie_name_index: dict from leie_utils.build_leie_name_address_index().

    Returns:
        list of potential match dicts for manual review.
    """
    if not leie_name_index:
        return []

    rows = con.execute("""
        SELECT npi, provider_name, state
        FROM providers
        WHERE provider_name IS NOT NULL AND state IS NOT NULL
    """).fetchall()

    matches = []
    for npi, name, state in rows:
        last_name = name.strip().upper().split(',')[0].split(' ')[0] if name else ''
        key = (last_name, state.upper() if state else '')
        if key in leie_name_index:
            for leie_record in leie_name_index[key]:
                matches.append({
                    'npi': npi,
                    'provider_name': name,
                    'state': state,
                    'leie_lastname': leie_record.get('lastname', ''),
                    'leie_firstname': leie_record.get('firstname', ''),
                    'leie_npi': leie_record.get('npi', ''),
                    'leie_excltype': leie_record.get('excltype', ''),
                    'match_type': 'name_state',
                })

    logger.info(f'LEIE name matching: {len(matches)} potential matches for review')
    return matches
