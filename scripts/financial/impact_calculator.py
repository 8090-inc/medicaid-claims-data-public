"""Financial impact estimation for flagged providers."""

import logging

logger = logging.getLogger('medicaid_fwa.financial')


def calculate_excess_payment(provider_rate, peer_median_rate, provider_claims):
    """Calculate excess payment for a single provider.

    Args:
        provider_rate: Provider's paid-per-claim rate.
        peer_median_rate: Median rate for peer group.
        provider_claims: Total claims for the provider.

    Returns:
        Estimated excess payment amount.
    """
    if provider_rate <= peer_median_rate:
        return 0.0
    return (provider_rate - peer_median_rate) * provider_claims


def estimate_total_impact(findings):
    """Aggregate financial impact across all findings.

    Args:
        findings: List of finding dicts with 'total_impact' field.

    Returns:
        dict with total_impact, finding_count, and breakdown by method.
    """
    total = sum(f.get('total_impact', 0) for f in findings)
    by_method = {}
    for f in findings:
        method = f.get('method_name', 'unknown')
        by_method[method] = by_method.get(method, 0) + f.get('total_impact', 0)

    logger.info(f'Total estimated impact: ${total:,.0f} from {len(findings)} findings')
    return {
        'total_impact': total,
        'finding_count': len(findings),
        'by_method': by_method,
    }
