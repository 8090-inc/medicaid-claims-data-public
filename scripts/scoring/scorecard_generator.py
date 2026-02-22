"""Provider scorecard generation — per-provider validation score summaries."""

import csv
import json
import logging
import os

from config.project_config import ANALYSIS_DIR

logger = logging.getLogger('medicaid_fwa.scoring')


def generate_provider_scorecards(composites, output_dir=None):
    """Generate per-provider scorecard CSV.

    Args:
        composites: dict from compute_composite_scores (npi -> score dict).
        output_dir: Output directory (default: output/analysis/).

    Returns:
        Path to the generated CSV file.
    """
    output_dir = output_dir or ANALYSIS_DIR
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, 'provider_validation_scores.csv')

    sorted_providers = sorted(
        composites.items(),
        key=lambda x: x[1]['score'],
        reverse=True,
    )

    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['npi', 'composite_score', 'total_impact',
                         'method_count', 'finding_count', 'tier'])
        for npi, scores in sorted_providers:
            tier = 'high' if scores['score'] >= 0.8 else 'medium' if scores['score'] >= 0.5 else 'low'
            writer.writerow([
                npi, round(scores['score'], 4), round(scores['total_impact'], 2),
                scores['method_count'], scores['finding_count'], tier,
            ])

    logger.info(f'  Wrote {len(sorted_providers)} provider scorecards to {path}')
    return path
