"""Provider ranking and risk score visualizations."""

import logging
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from config.project_config import CHART_DIR

logger = logging.getLogger('medicaid_fwa.visualization')


def chart_top_flagged_providers(findings, top_n=20, output_dir=None):
    """Generate horizontal bar chart of top flagged providers by impact.

    Args:
        findings: List of finding dicts with 'npi', 'total_impact'.
        top_n: Number of providers to show.
        output_dir: Output directory for chart PNG.

    Returns:
        Path to generated chart.
    """
    from utils.chart_utils import (
        setup_hhs_style, create_horizontal_bar_chart, HHS_AMBER
    )

    output_dir = output_dir or CHART_DIR
    os.makedirs(output_dir, exist_ok=True)

    top = sorted(findings, key=lambda f: f.get('total_impact', 0), reverse=True)[:top_n]
    if not top:
        logger.warning('No findings for provider ranking chart')
        return None

    labels = [f"{f.get('name', f.get('npi', 'Unknown'))[:30]}" for f in top]
    values = [f['total_impact'] for f in top]

    path = os.path.join(output_dir, 'top_flagged_providers.png')
    create_horizontal_bar_chart(
        values, labels,
        f'Top {top_n} Providers by Estimated Recoverable Amount',
        'Fraud, Waste & Abuse Analysis | Medicaid 2018\u20132024',
        path,
    )
    logger.info(f'Generated provider ranking chart: {path}')
    return path


def chart_risk_score_distribution(composites, output_dir=None):
    """Generate histogram of composite risk scores.

    Args:
        composites: dict mapping npi -> score dict with 'score'.
        output_dir: Output directory for chart PNG.

    Returns:
        Path to generated chart.
    """
    from utils.chart_utils import setup_hhs_style, HHS_AMBER, HHS_DARK

    output_dir = output_dir or CHART_DIR
    os.makedirs(output_dir, exist_ok=True)
    setup_hhs_style()

    scores = [s.get('score', 0) for s in composites.values()]
    if not scores:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(scores, bins=50, color=HHS_AMBER, edgecolor=HHS_DARK, alpha=0.85)
    ax.set_xlabel('Composite Risk Score')
    ax.set_ylabel('Number of Providers')
    ax.set_title('Distribution of Provider Risk Scores')

    path = os.path.join(output_dir, 'risk_score_distribution.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info(f'Generated risk score distribution chart: {path}')
    return path


def chart_risk_tier_breakdown(tiers, output_dir=None):
    """Generate bar chart showing provider counts per risk tier.

    Args:
        tiers: dict with 'high', 'medium', 'low' lists from segmentation.
        output_dir: Output directory for chart PNG.

    Returns:
        Path to generated chart.
    """
    from utils.chart_utils import setup_hhs_style, HHS_RED, HHS_AMBER, HHS_GREEN, HHS_DARK

    output_dir = output_dir or CHART_DIR
    os.makedirs(output_dir, exist_ok=True)
    setup_hhs_style()

    labels = ['High Risk', 'Medium Risk', 'Low Risk']
    counts = [len(tiers.get('high', [])), len(tiers.get('medium', [])),
              len(tiers.get('low', []))]
    colors = [HHS_RED, HHS_AMBER, HHS_GREEN]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, counts, color=colors, edgecolor=HHS_DARK, width=0.6)
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10,
                f'{count:,}', ha='center', va='bottom', fontweight='bold')

    ax.set_ylabel('Number of Providers')
    ax.set_title('Provider Risk Tier Distribution')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))

    path = os.path.join(output_dir, 'risk_tier_breakdown.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info(f'Generated risk tier breakdown chart: {path}')
    return path
