"""Confidence score adjustment based on data quality weights."""

import logging

logger = logging.getLogger('medicaid_fwa.quality')


def adjust_confidence_by_quality(findings, quality_scores):
    """Adjust finding confidence scores based on state data quality.

    Reduces confidence for findings in states with lower data quality.

    Args:
        findings: List of finding dicts.
        quality_scores: dict mapping npi -> quality_weight.

    Returns:
        Modified findings list with adjusted confidence.
    """
    if not quality_scores:
        return findings

    adjusted_count = 0
    for f in findings:
        for npi in f.get('flagged_providers', []):
            quality_weight = quality_scores.get(npi, 1.0)
            if quality_weight < 1.0:
                f['confidence'] = f.get('confidence', 0.5) * quality_weight
                f['quality_adjusted'] = True
                adjusted_count += 1
                break

    logger.info(f'Adjusted confidence for {adjusted_count} findings based on data quality')
    return findings
