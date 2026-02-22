"""Provider segmentation for investigation queues."""

import logging

logger = logging.getLogger('medicaid_fwa.queuing')


def segment_by_risk_tier(composites):
    """Segment providers into risk tiers.

    Args:
        composites: dict from composite_scorer (npi -> score dict).

    Returns:
        dict with 'high', 'medium', 'low' lists of NPIs.
    """
    tiers = {'high': [], 'medium': [], 'low': []}
    for npi, scores in composites.items():
        score = scores.get('score', 0)
        if score >= 0.8:
            tiers['high'].append(npi)
        elif score >= 0.5:
            tiers['medium'].append(npi)
        else:
            tiers['low'].append(npi)

    logger.info(f'Risk tiers: high={len(tiers["high"])}, '
                f'medium={len(tiers["medium"])}, low={len(tiers["low"])}')
    return tiers


def segment_by_specialty(composites, con):
    """Segment risk-scored providers by specialty.

    Args:
        composites: dict from composite_scorer.
        con: DuckDB connection (read-only).

    Returns:
        dict mapping specialty -> list of (npi, score) tuples.
    """
    logger.info('Segmenting by specialty ...')
    npis = list(composites.keys())
    if not npis:
        return {}

    # Fetch specialties
    npi_list = "','".join(npis[:10000])
    rows = con.execute(f"""
        SELECT npi, COALESCE(specialty, 'Unknown')
        FROM providers
        WHERE npi IN ('{npi_list}')
    """).fetchall()
    npi_specialty = {r[0]: r[1] for r in rows}

    by_specialty = {}
    for npi, scores in composites.items():
        specialty = npi_specialty.get(npi, 'Unknown')
        if specialty not in by_specialty:
            by_specialty[specialty] = []
        by_specialty[specialty].append((npi, scores['score']))

    for specialty in by_specialty:
        by_specialty[specialty].sort(key=lambda x: x[1], reverse=True)

    logger.info(f'  {len(by_specialty)} specialties represented')
    return by_specialty
