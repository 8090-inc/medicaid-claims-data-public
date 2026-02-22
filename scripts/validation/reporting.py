"""Data quality report generation — JSON quality summaries."""

import json
import os
import time


def generate_quality_report(counters, month_counts, month_paid,
                            min_month, max_month, csv_path, output_path):
    """Generate and write a JSON data quality report.

    Args:
        counters: dict of validation counters.
        month_counts: dict of claim_month -> row count.
        month_paid: dict of claim_month -> total paid.
        min_month: Earliest valid claim month.
        max_month: Latest valid claim month.
        csv_path: Path to source CSV.
        output_path: Path to write JSON report.

    Returns:
        The report dict.
    """
    report = {
        'csv_path': csv_path,
        'total_rows_scanned': counters['total_rows'],
        'valid_rows': counters['valid_rows'],
        'invalid_rows': counters['invalid_rows'],
        'invalid_breakdown': {k: v for k, v in counters.items() if k.startswith('invalid_')},
        'negative_paid_rows': counters.get('negative_paid', 0),
        'zero_beneficiaries_positive_claims': counters.get('zero_beneficiaries_positive_claims', 0),
        'min_month': min_month,
        'max_month': max_month,
        'month_coverage_count': len(month_counts),
        'month_counts': month_counts,
        'month_paid': month_paid,
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    return report
