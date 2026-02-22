"""Accuracy and performance metrics for detection method validation."""

import logging

logger = logging.getLogger('medicaid_fwa.validation')


def compute_detection_rates(findings, positive_control_npis):
    """Compute detection rates against known positive controls.

    Args:
        findings: List of finding dicts.
        positive_control_npis: dict mapping source_name -> set of known-bad NPIs.

    Returns:
        dict mapping source_name -> metrics dict with 'detected', 'total', 'rate'.
    """
    flagged_npis = set()
    for f in findings:
        flagged_npis.update(f.get('flagged_providers', []))

    rates = {}
    for source, known_npis in positive_control_npis.items():
        detected = flagged_npis & known_npis
        total = len(known_npis)
        rates[source] = {
            'detected': len(detected),
            'total': total,
            'rate': len(detected) / total if total > 0 else 0,
            'detected_npis': list(detected)[:100],
        }
        logger.info(f'{source}: detected {len(detected)}/{total} '
                    f'({rates[source]["rate"]:.1%})')

    return rates


def compute_method_stability(findings_by_method):
    """Compute stability metrics across detection methods.

    Args:
        findings_by_method: dict mapping method_name -> list of findings.

    Returns:
        dict mapping method_name -> stability metrics.
    """
    metrics = {}
    for method, findings in findings_by_method.items():
        npis = set()
        impacts = []
        confidences = []
        for f in findings:
            npis.update(f.get('flagged_providers', []))
            impacts.append(f.get('total_impact', 0))
            confidences.append(f.get('confidence', 0))

        metrics[method] = {
            'finding_count': len(findings),
            'unique_providers': len(npis),
            'avg_impact': sum(impacts) / len(impacts) if impacts else 0,
            'avg_confidence': sum(confidences) / len(confidences) if confidences else 0,
            'total_impact': sum(impacts),
        }

    logger.info(f'Computed stability metrics for {len(metrics)} methods')
    return metrics


def compute_overlap_matrix(findings_by_method):
    """Compute pairwise overlap between detection methods.

    Args:
        findings_by_method: dict mapping method_name -> list of findings.

    Returns:
        dict of (method_a, method_b) -> overlap_count.
    """
    method_npis = {}
    for method, findings in findings_by_method.items():
        npis = set()
        for f in findings:
            npis.update(f.get('flagged_providers', []))
        method_npis[method] = npis

    overlaps = {}
    methods = sorted(method_npis.keys())
    for i, m1 in enumerate(methods):
        for m2 in methods[i + 1:]:
            overlap = method_npis[m1] & method_npis[m2]
            overlaps[(m1, m2)] = len(overlap)

    return overlaps
