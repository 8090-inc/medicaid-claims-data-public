"""Executive report package assembly for leadership review."""

import json
import logging
import os
import shutil

from config.project_config import ANALYSIS_DIR, CHART_DIR, OUTPUT_DIR

logger = logging.getLogger('medicaid_fwa.export')


def assemble_executive_package(output_dir=None):
    """Assemble executive-level report package with key deliverables.

    Collects the executive brief, top charts, summary statistics,
    and action plan into a single directory for distribution.

    Args:
        output_dir: Destination directory. Defaults to output/packages/executive/.

    Returns:
        Path to assembled package directory.
    """
    output_dir = output_dir or os.path.join(OUTPUT_DIR, 'packages', 'executive')
    os.makedirs(output_dir, exist_ok=True)

    # Core documents
    documents = [
        ('executive_brief.md', ANALYSIS_DIR),
        ('action_plan_memo.md', ANALYSIS_DIR),
        ('cms_administrator_report.md', ANALYSIS_DIR),
        ('fraud_patterns.md', ANALYSIS_DIR),
    ]

    copied = []
    for fname, src_dir in documents:
        src = os.path.join(src_dir, fname)
        if os.path.exists(src):
            dst = os.path.join(output_dir, fname)
            shutil.copy2(src, dst)
            copied.append(fname)

    # Key charts
    chart_files = [
        'monthly_spending_trend.png',
        'top_flagged_providers.png',
        'risk_tier_breakdown.png',
        'risk_score_distribution.png',
        'detection_method_counts.png',
    ]

    charts_dir = os.path.join(output_dir, 'charts')
    os.makedirs(charts_dir, exist_ok=True)
    for fname in chart_files:
        src = os.path.join(CHART_DIR, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(charts_dir, fname))
            copied.append(f'charts/{fname}')

    # Summary data
    summary_files = [
        'priority_queue.csv',
        'provider_scorecards.csv',
    ]
    for fname in summary_files:
        src = os.path.join(ANALYSIS_DIR, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(output_dir, fname))
            copied.append(fname)

    # Write manifest
    manifest = {
        'package_type': 'executive',
        'files': copied,
        'file_count': len(copied),
    }
    manifest_path = os.path.join(output_dir, 'manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f'Executive package: {len(copied)} files assembled in {output_dir}')
    return output_dir
