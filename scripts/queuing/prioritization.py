"""Investigation queue prioritization logic."""

import csv
import logging
import os

from config.project_config import ANALYSIS_DIR

logger = logging.getLogger('medicaid_fwa.queuing')


def generate_priority_queue(scored_findings, output_dir=None, top_n=500):
    """Generate the prioritized investigation queue CSV.

    Args:
        scored_findings: List of findings with priority_score.
        output_dir: Output directory.
        top_n: Number of top findings to include.

    Returns:
        Path to the generated CSV.
    """
    output_dir = output_dir or ANALYSIS_DIR
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, 'priority_queue.csv')

    sorted_findings = sorted(
        scored_findings,
        key=lambda x: x.get('priority_score', 0),
        reverse=True,
    )[:top_n]

    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['rank', 'npi', 'priority_score', 'total_impact',
                         'confidence', 'method_name', 'hypothesis_id'])
        for rank, finding in enumerate(sorted_findings, 1):
            npis = finding.get('flagged_providers', [])
            npi = npis[0] if npis else ''
            writer.writerow([
                rank, npi,
                round(finding.get('priority_score', 0), 2),
                round(finding.get('total_impact', 0), 2),
                round(finding.get('confidence', 0), 4),
                finding.get('method_name', ''),
                finding.get('hypothesis_id', ''),
            ])

    logger.info(f'Priority queue written: {path} ({len(sorted_findings)} entries)')
    return path
