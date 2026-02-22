"""Entity deduplication and resolution for provider records."""

import logging

logger = logging.getLogger('medicaid_fwa.relationships')


def find_duplicate_providers(con, method='name_state'):
    """Identify potentially duplicated provider entities.

    Args:
        con: DuckDB connection (read-only).
        method: Resolution strategy ('name_state' or 'address').

    Returns:
        list of dicts with 'group_key', 'npis', 'names'.
    """
    if method == 'name_state':
        rows = con.execute("""
            SELECT
                UPPER(TRIM(p.provider_name)) || '|' || COALESCE(p.state, '') AS group_key,
                LIST(p.npi) AS npis,
                COUNT(*) AS cnt
            FROM providers p
            WHERE p.provider_name IS NOT NULL
            GROUP BY group_key
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
        """).fetchall()
    else:
        rows = con.execute("""
            SELECT
                COALESCE(p.state, '') || '|' || COALESCE(p.zip, '') AS group_key,
                LIST(p.npi) AS npis,
                COUNT(*) AS cnt
            FROM providers p
            WHERE p.state IS NOT NULL AND p.zip IS NOT NULL
            GROUP BY group_key
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
        """).fetchall()

    duplicates = []
    for key, npis, cnt in rows:
        duplicates.append({
            'group_key': key,
            'npis': npis if isinstance(npis, list) else [npis],
            'count': cnt,
        })

    logger.info(f'Found {len(duplicates)} potential duplicate provider groups '
                f'(method={method})')
    return duplicates


def merge_provider_findings(findings, npi_mapping):
    """Consolidate findings for providers that resolved to the same entity.

    Args:
        findings: List of finding dicts.
        npi_mapping: dict mapping alias_npi -> canonical_npi.

    Returns:
        Modified findings list with NPIs resolved to canonical form.
    """
    if not npi_mapping:
        return findings

    merged_count = 0
    for f in findings:
        original_providers = f.get('flagged_providers', [])
        resolved = []
        for npi in original_providers:
            canonical = npi_mapping.get(npi, npi)
            if canonical not in resolved:
                resolved.append(canonical)
            if canonical != npi:
                merged_count += 1
        f['flagged_providers'] = resolved

    logger.info(f'Resolved {merged_count} NPI references to canonical form')
    return findings
