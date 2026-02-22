"""Finding deduplication — merges overlapping findings by NPI+HCPCS."""

import logging
from collections import defaultdict

logger = logging.getLogger('medicaid_fwa.financial')


def deduplicate_findings(findings):
    """Remove duplicate findings for the same provider+code combination.

    Keeps the finding with the highest confidence for each NPI+HCPCS pair.

    Args:
        findings: List of finding dicts.

    Returns:
        Deduplicated list of findings.
    """
    logger.info(f'Deduplicating {len(findings)} findings ...')

    # Group by (npi, method) to avoid double-counting
    npi_findings = defaultdict(list)
    for f in findings:
        for npi in f.get('flagged_providers', []):
            key = (npi, f.get('method_name', ''))
            npi_findings[key].append(f)

    deduped = []
    seen_keys = set()
    for key, grouped in npi_findings.items():
        best = max(grouped, key=lambda x: x.get('confidence', 0))
        finding_key = (key[0], best.get('hypothesis_id', ''))
        if finding_key not in seen_keys:
            deduped.append(best)
            seen_keys.add(finding_key)

    logger.info(f'  Deduplicated to {len(deduped)} findings')
    return deduped
