"""Priority ranking for investigation queue."""

import logging

logger = logging.getLogger('medicaid_fwa.financial')


def rank_by_priority(findings):
    """Rank findings by priority score (impact * confidence).

    Args:
        findings: List of finding dicts.

    Returns:
        Sorted list of findings with 'priority_score' added.
    """
    logger.info(f'Ranking {len(findings)} findings by priority ...')
    for f in findings:
        f['priority_score'] = f.get('total_impact', 0) * f.get('confidence', 0.5)

    ranked = sorted(findings, key=lambda x: x['priority_score'], reverse=True)
    logger.info(f'  Top priority impact: ${ranked[0]["priority_score"]:,.0f}' if ranked else '  No findings')
    return ranked
