"""Composite risk scoring — combines multiple detection method scores."""

import logging
from collections import defaultdict

logger = logging.getLogger('medicaid_fwa.scoring')


def compute_composite_scores(findings, method_weights=None):
    """Compute composite risk scores by aggregating across detection methods.

    Args:
        findings: List of finding dicts from all detection methods.
        method_weights: Optional dict mapping method_name -> weight (default all 1.0).

    Returns:
        dict mapping provider_npi -> composite_score.
    """
    logger.info(f'Computing composite scores from {len(findings)} findings ...')
    method_weights = method_weights or {}

    provider_scores = defaultdict(list)
    for f in findings:
        weight = method_weights.get(f.get('method_name', ''), 1.0)
        confidence = f.get('confidence', 0.5) * weight
        for npi in f.get('flagged_providers', []):
            provider_scores[npi].append({
                'method': f.get('method_name', ''),
                'confidence': confidence,
                'impact': f.get('total_impact', 0),
            })

    composites = {}
    for npi, scores in provider_scores.items():
        avg_confidence = sum(s['confidence'] for s in scores) / len(scores)
        total_impact = sum(s['impact'] for s in scores)
        method_count = len(set(s['method'] for s in scores))

        composite = min(
            avg_confidence * (1 + 0.1 * (method_count - 1)),
            1.0,
        )
        composites[npi] = {
            'score': round(composite, 4),
            'total_impact': total_impact,
            'method_count': method_count,
            'finding_count': len(scores),
        }

    logger.info(f'  Scored {len(composites)} providers')
    return composites
