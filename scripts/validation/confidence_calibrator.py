"""Confidence score calibration using positive controls."""

import logging

logger = logging.getLogger('medicaid_fwa.validation')


def calibrate_confidence_scores(findings, positive_control_npis):
    """Adjust confidence scores based on validation against known positives.

    Providers confirmed by positive controls get a confidence boost;
    methods with low detection rates get confidence penalties.

    Args:
        findings: List of finding dicts.
        positive_control_npis: Set of known-bad NPI strings.

    Returns:
        Modified findings list with calibrated confidence scores.
    """
    if not positive_control_npis:
        return findings

    confirmed = set()
    for f in findings:
        for npi in f.get('flagged_providers', []):
            if npi in positive_control_npis:
                confirmed.add(npi)

    calibrated_count = 0
    for f in findings:
        providers = f.get('flagged_providers', [])
        if any(p in confirmed for p in providers):
            # Boost confidence for findings corroborated by positive controls
            original = f.get('confidence', 0.5)
            f['confidence'] = min(1.0, original * 1.2)
            f['calibration_note'] = 'boosted_by_positive_control'
            calibrated_count += 1

    logger.info(f'Calibrated {calibrated_count} findings using '
                f'{len(confirmed)} confirmed positive controls')
    return findings


def compute_calibration_curve(findings, positive_control_npis, n_bins=10):
    """Compute calibration curve comparing predicted confidence to actual detection.

    Args:
        findings: List of finding dicts.
        positive_control_npis: Set of known-bad NPI strings.
        n_bins: Number of confidence bins.

    Returns:
        list of dicts with 'bin_start', 'bin_end', 'mean_confidence',
        'actual_positive_rate', 'count'.
    """
    if not positive_control_npis or not findings:
        return []

    # Bin findings by confidence
    bin_width = 1.0 / n_bins
    bins = [{'confidences': [], 'positives': 0, 'count': 0} for _ in range(n_bins)]

    for f in findings:
        conf = f.get('confidence', 0.5)
        bin_idx = min(int(conf / bin_width), n_bins - 1)
        bins[bin_idx]['confidences'].append(conf)
        bins[bin_idx]['count'] += 1
        providers = f.get('flagged_providers', [])
        if any(p in positive_control_npis for p in providers):
            bins[bin_idx]['positives'] += 1

    curve = []
    for i, b in enumerate(bins):
        if b['count'] > 0:
            curve.append({
                'bin_start': round(i * bin_width, 2),
                'bin_end': round((i + 1) * bin_width, 2),
                'mean_confidence': sum(b['confidences']) / len(b['confidences']),
                'actual_positive_rate': b['positives'] / b['count'],
                'count': b['count'],
            })

    logger.info(f'Calibration curve: {len(curve)} non-empty bins')
    return curve
