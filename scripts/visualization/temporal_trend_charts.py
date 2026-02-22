"""Temporal trend visualizations for billing patterns."""

import logging
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from config.project_config import CHART_DIR

logger = logging.getLogger('medicaid_fwa.visualization')


def chart_monthly_spending_trend(con, output_dir=None):
    """Generate monthly spending trend line chart.

    Args:
        con: DuckDB connection (read-only).
        output_dir: Output directory for chart PNG.

    Returns:
        Path to generated chart.
    """
    from utils.chart_utils import setup_hhs_style, create_line_chart

    output_dir = output_dir or CHART_DIR
    os.makedirs(output_dir, exist_ok=True)

    rows = con.execute("""
        SELECT claim_month, SUM(paid) AS total_paid
        FROM claims GROUP BY claim_month ORDER BY claim_month
    """).fetchall()

    months = [r[0] for r in rows]
    paid = [r[1] for r in rows]

    path = os.path.join(output_dir, 'monthly_spending_trend.png')
    create_line_chart(
        months, paid,
        'Monthly Medicaid Provider Spending',
        'January 2018 \u2013 December 2024 | Fee-for-Service and Managed Care',
        path,
    )
    logger.info(f'Generated monthly spending trend: {path}')
    return path


def chart_provider_monthly_trend(con, npi, output_dir=None):
    """Generate monthly spending chart for a single provider.

    Args:
        con: DuckDB connection (read-only).
        npi: Provider NPI.
        output_dir: Output directory for chart PNG.

    Returns:
        Path to generated chart.
    """
    from utils.chart_utils import setup_hhs_style, HHS_AMBER, HHS_DARK

    output_dir = output_dir or CHART_DIR
    os.makedirs(output_dir, exist_ok=True)
    setup_hhs_style()

    rows = con.execute("""
        SELECT claim_month, total_paid
        FROM provider_monthly
        WHERE billing_npi = ?
        ORDER BY claim_month
    """, [npi]).fetchall()

    if not rows:
        return None

    months = [r[0] for r in rows]
    paid = [r[1] for r in rows]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(range(len(months)), paid, color=HHS_AMBER, linewidth=2, marker='o', markersize=3)
    ax.fill_between(range(len(months)), paid, alpha=0.15, color=HHS_AMBER)

    # X-axis labels (every 6th month)
    tick_indices = range(0, len(months), max(1, len(months) // 12))
    ax.set_xticks(list(tick_indices))
    ax.set_xticklabels([months[i] for i in tick_indices], rotation=45, ha='right', fontsize=8)

    ax.set_ylabel('Total Paid ($)')
    ax.set_title(f'Monthly Billing Trend — NPI {npi}')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))

    path = os.path.join(output_dir, f'provider_{npi}_trend.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info(f'Generated provider trend chart: {path}')
    return path


def chart_detection_method_counts(findings_by_method, output_dir=None):
    """Chart the number of findings per detection method.

    Args:
        findings_by_method: dict mapping method_name -> list of findings.
        output_dir: Output directory for chart PNG.

    Returns:
        Path to generated chart.
    """
    from utils.chart_utils import setup_hhs_style, HHS_AMBER, HHS_DARK

    output_dir = output_dir or CHART_DIR
    os.makedirs(output_dir, exist_ok=True)
    setup_hhs_style()

    methods = sorted(findings_by_method.keys(), key=lambda m: len(findings_by_method[m]))
    counts = [len(findings_by_method[m]) for m in methods]

    if not methods:
        return None

    fig, ax = plt.subplots(figsize=(10, max(6, len(methods) * 0.35)))
    bars = ax.barh(range(len(methods)), counts, color=HHS_AMBER, edgecolor=HHS_DARK)
    ax.set_yticks(range(len(methods)))
    ax.set_yticklabels([m[:40] for m in methods], fontsize=8)
    ax.set_xlabel('Number of Findings')
    ax.set_title('Findings by Detection Method')

    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height() / 2,
                f'{count:,}', va='center', fontsize=8)

    path = os.path.join(output_dir, 'detection_method_counts.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info(f'Generated detection method counts chart: {path}')
    return path
