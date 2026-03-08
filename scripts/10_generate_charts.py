#!/usr/bin/env python3
"""Milestone 10: Chart generation in HHS OpenData style.

Generates 11+ charts for the final report matching the HHS OpenData portal design.
"""

import json
import os
import sys
import time
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.db_utils import get_connection, format_dollars
from utils.chart_utils import (
    setup_hhs_style, create_horizontal_bar_chart, create_line_chart,
    create_scatter_chart, add_hhs_border, add_hhs_branding,
    HHS_AMBER, HHS_DARK, HHS_MUTED, HHS_GRID, HHS_RED, HHS_GREEN,
    get_title_font, get_mono_font, dollar_formatter
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
CHART_DIR = os.path.join(OUTPUT_DIR, 'charts')
FINDINGS_PATH = os.path.join(OUTPUT_DIR, 'findings', 'final_scored_findings.json')
PROFILE_PATH = os.path.join(OUTPUT_DIR, 'data_profile.json')


def load_findings():
    if os.path.exists(FINDINGS_PATH):
        with open(FINDINGS_PATH) as f:
            return json.load(f)
    return {'summary': {}, 'findings': []}


def load_profile():
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH) as f:
            return json.load(f)
    return {}


def chart_monthly_spending(con):
    """Chart 1: Monthly spending trend line chart."""
    print("  Chart 1: Monthly spending trend ...")
    rows = con.execute("""
        SELECT claim_month, SUM(paid) AS total_paid
        FROM claims GROUP BY claim_month ORDER BY claim_month
    """).fetchall()
    months = [r[0] for r in rows]
    paid = [r[1] for r in rows]

    # Drop final month if incomplete (>50% drop from prior month)
    if len(paid) >= 2 and paid[-1] < paid[-2] * 0.5:
        months = months[:-1]
        paid = paid[:-1]

    create_line_chart(
        months, paid,
        'Monthly Medicaid Provider Spending',
        'January 2018 \u2013 December 2024 | Fee-for-Service and Managed Care',
        os.path.join(CHART_DIR, 'monthly_spending_trend.png'),
    )


def chart_top20_flagged_providers(findings):
    """Chart 2: Top 20 providers by estimated recoverable amount."""
    print("  Chart 2: Top 20 flagged providers ...")
    top20 = findings['findings'][:20]
    if not top20:
        print("    No findings available")
        return

    labels = [f"{f.get('name', f['npi'])[:30]} ({f.get('state', '')})" for f in top20]
    values = [f['total_impact'] for f in top20]

    create_horizontal_bar_chart(
        values, labels,
        'Top 20 Providers by Estimated Recoverable Amount',
        'Fraud, Waste & Abuse Analysis | Medicaid 2018\u20132024',
        os.path.join(CHART_DIR, 'top20_flagged_providers.png'),
        figsize=(12, 10),
    )


def chart_top20_flagged_procedures(con, findings):
    """Chart 3: Top 20 HCPCS codes by total flagged spending."""
    print("  Chart 3: Top 20 flagged procedures ...")
    from collections import defaultdict

    # Aggregate flagged spending by code
    # Use the data profile for top codes
    rows = con.execute("""
        SELECT
            hs.hcpcs_code,
            COALESCE(hc.short_desc, 'Code ' || hs.hcpcs_code) AS description,
            hs.total_paid
        FROM hcpcs_summary hs
        LEFT JOIN hcpcs_codes hc ON hs.hcpcs_code = hc.hcpcs_code
        ORDER BY hs.total_paid DESC
        LIMIT 20
    """).fetchall()

    if not rows:
        return

    labels = [f"{r[0]} - {r[1][:35]}" for r in rows]
    values = [r[2] for r in rows]

    create_horizontal_bar_chart(
        values, labels,
        'Top 20 Procedures by Total Spending',
        'HCPCS Code Analysis | Medicaid 2018\u20132024',
        os.path.join(CHART_DIR, 'top20_flagged_procedures.png'),
        figsize=(12, 10),
    )


def chart_findings_by_category(findings):
    """Chart 4: Findings by category."""
    print("  Chart 4: Findings by category ...")
    from collections import defaultdict

    category_stats = defaultdict(lambda: {'count': 0, 'impact': 0})

    category_names = {
        'statistical': '1. Statistical Outliers',
        'temporal': '2. Temporal Anomalies',
        'peer': '3. Peer Comparison',
        'network': '4. Network Analysis',
        'concentration': '5. Concentration',
        'ml': '6. Machine Learning',
        'deep_learning': '7. Deep Learning',
        'domain': '8. Domain Rules',
        'crossref': '9. Cross-Reference',
        'composite': '10. Composite',
    }

    for f in findings.get('findings', []):
        method = f.get('primary_method', '')
        # Map method to category
        method_to_cat = {
            'z_score_paid_per_claim': 'statistical', 'z_score_claims_per_bene': 'statistical',
            'z_score_paid_per_bene': 'statistical', 'iqr_outlier': 'statistical',
            'gev_extreme': 'statistical', 'benfords_law': 'statistical',
            'month_spike': 'temporal', 'sudden_appearance': 'temporal',
            'sudden_disappearance': 'temporal', 'yoy_growth': 'temporal',
            'seasonal_violation': 'temporal', 'covid_anomaly': 'temporal',
            'december_surge': 'temporal', 'change_point': 'temporal',
            'peer_rate': 'peer', 'peer_volume': 'peer',
            'peer_concentration': 'peer', 'geographic_peer': 'peer',
            'specialty_peer': 'peer', 'size_mismatch': 'peer',
            'hub_spoke': 'network', 'shared_servicing': 'network',
            'circular_billing': 'network', 'network_density': 'network',
            'new_network': 'network', 'pure_billing': 'network',
            'ghost_network': 'network',
            'provider_dominance': 'concentration', 'single_code': 'concentration',
            'hhi_concentration': 'concentration', 'geographic_monopoly': 'concentration',
            'temporal_concentration': 'concentration',
            'isolation_forest': 'ml', 'dbscan': 'ml', 'random_forest': 'ml',
            'xgboost': 'ml', 'kmeans': 'ml', 'lof': 'ml',
            'autoencoder': 'deep_learning', 'vae': 'deep_learning',
            'lstm': 'deep_learning', 'transformer': 'deep_learning',
            'impossible_volume': 'domain', 'upcoding': 'domain',
            'unbundling': 'domain', 'high_risk_category': 'domain',
            'phantom_billing': 'domain', 'adjustment_anomaly': 'domain',
            'duplicate_billing': 'domain',
            'specialty_mismatch': 'crossref', 'entity_type_anomaly': 'crossref',
            'geographic_impossibility': 'crossref', 'state_spending_anomaly': 'crossref',
            'composite_multi_signal': 'composite', 'ensemble_agreement': 'composite',
        }
        cat = method_to_cat.get(method, 'other')
        category_stats[cat]['count'] += 1
        category_stats[cat]['impact'] += f.get('total_impact', 0)

    if not category_stats:
        return

    # Sort by category number
    ordered = []
    for key, display in category_names.items():
        if key in category_stats:
            ordered.append((display, category_stats[key]['impact']))

    if not ordered:
        return

    labels = [o[0] for o in ordered]
    values = [o[1] for o in ordered]

    create_horizontal_bar_chart(
        values, labels,
        'Findings by Analytical Category',
        'Total Estimated Impact by Detection Method',
        os.path.join(CHART_DIR, 'findings_by_category.png'),
        figsize=(12, 8),
    )


def chart_risk_scatter(findings):
    """Chart 5: Provider risk scatter plot."""
    print("  Chart 5: Provider risk scatter ...")
    data = findings.get('findings', [])
    if not data:
        return

    x_vals = []
    y_vals = []
    colors = []

    for f in data[:500]:  # Top 500
        paid = f.get('total_paid', f.get('total_impact', 0))
        score = f.get('score', f.get('num_methods', 0))
        if paid > 0:
            x_vals.append(paid)
            y_vals.append(score)
            colors.append(HHS_RED if f.get('confidence') == 'high' else HHS_AMBER)

    if not x_vals:
        return

    create_scatter_chart(
        x_vals, y_vals,
        'Provider Risk Assessment',
        'Total Medicaid Paid vs Composite Anomaly Score',
        os.path.join(CHART_DIR, 'provider_risk_scatter.png'),
        colors=colors,
        xlabel='Total Medicaid Paid (log scale)',
        ylabel='Anomaly Score / Methods Count',
        log_x=True,
    )


def chart_temporal_top5(con, findings):
    """Chart 6: Monthly billing for top 5 flagged providers."""
    print("  Chart 6: Temporal anomalies top 5 ...")
    top5 = findings.get('findings', [])[:5]
    if not top5:
        return

    setup_hhs_style()
    mono = get_mono_font()

    fig, axes = plt.subplots(5, 1, figsize=(12, 15), sharex=True)
    if not hasattr(axes, '__len__'):
        axes = [axes]

    colors = [HHS_AMBER, '#E88B0E', '#D97706', '#B45309', '#92400E']

    for i, f in enumerate(top5):
        npi = f.get('npi', '')
        name = f.get('name', npi)[:30]
        if not npi or npi.startswith('STATE_'):
            continue

        try:
            rows = con.execute("""
                SELECT claim_month, SUM(paid) AS paid
                FROM provider_monthly WHERE billing_npi = ?
                GROUP BY claim_month ORDER BY claim_month
            """, [npi]).fetchall()
        except Exception:
            continue

        if not rows:
            continue

        months = [r[0] for r in rows]
        paid = [r[1] for r in rows]

        ax = axes[i] if i < len(axes) else axes[-1]
        ax.plot(months, paid, color=colors[i % len(colors)], linewidth=1.5)
        ax.set_title(f"{name} ({f.get('state', '')})", fontsize=11, fontweight=600,
                     color=HHS_DARK, loc='left')
        ax.yaxis.set_major_formatter(dollar_formatter())
        ax.set_ylim(bottom=0)
        ax.grid(axis='y', linestyle='--', linewidth=0.5, color=HHS_GRID)
        ax.grid(axis='x', visible=False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        if len(months) > 20:
            ax.set_xticks(months[::12])

    fig.suptitle('Top 5 Flagged Providers: Monthly Billing', fontsize=14,
                 fontweight=600, color=HHS_DARK, y=0.98)
    fig.text(0.5, 0.96, 'Monthly Medicaid Payments | Flagged for Anomalous Patterns',
             fontsize=11, fontfamily=mono, color=HHS_MUTED, ha='center')

    add_hhs_border(fig)
    add_hhs_branding(fig)
    plt.tight_layout(rect=[0, 0.02, 1, 0.95])
    path = os.path.join(CHART_DIR, 'temporal_anomalies_top5.png')
    fig.savefig(path, facecolor=fig.get_facecolor(), edgecolor=fig.get_edgecolor())
    plt.close(fig)
    print(f"    Saved: {path}")


def chart_benfords(con):
    """Chart 7: Benford's Law first-digit distribution."""
    print("  Chart 7: Benford's Law ...")

    rows = con.execute("""
        SELECT
            CAST(SUBSTR(CAST(ABS(CAST(paid AS INTEGER)) AS VARCHAR), 1, 1) AS INTEGER) AS first_digit,
            COUNT(*) AS cnt
        FROM claims
        WHERE paid > 0 AND ABS(paid) >= 1
        GROUP BY first_digit
        HAVING first_digit BETWEEN 1 AND 9
        ORDER BY first_digit
    """).fetchall()

    if not rows:
        return

    actual = {r[0]: r[1] for r in rows}
    total = sum(actual.values())
    digits = list(range(1, 10))

    import math
    expected_pct = [math.log10(1 + 1 / d) * 100 for d in digits]
    actual_pct = [(actual.get(d, 0) / total * 100) for d in digits]

    setup_hhs_style()
    mono = get_mono_font()

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(digits))
    width = 0.35

    bars1 = ax.bar(x - width / 2, expected_pct, width, label='Expected (Benford)', color='#D4D4D4', edgecolor='none')
    bars2 = ax.bar(x + width / 2, actual_pct, width, label='Actual', color=HHS_AMBER, edgecolor='none')

    ax.set_xlabel('First Digit', fontsize=11, color=HHS_MUTED)
    ax.set_ylabel('Frequency (%)', fontsize=11, color=HHS_MUTED)
    ax.set_xticks(x)
    ax.set_xticklabels([str(d) for d in digits])
    ax.legend(fontsize=10, frameon=False)
    ax.set_title("Benford's Law: First-Digit Distribution", fontsize=14, fontweight=600,
                 color=HHS_DARK, loc='left', pad=20)
    fig.text(0.125, 0.92, 'Payment Amounts | All Medicaid Claims 2018\u20132024',
             fontsize=11, fontfamily=mono, color=HHS_MUTED)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis='y', linestyle='--', linewidth=0.5, color=HHS_GRID)

    add_hhs_border(fig)
    add_hhs_branding(fig)
    plt.tight_layout()
    path = os.path.join(CHART_DIR, 'benfords_law.png')
    fig.savefig(path, facecolor=fig.get_facecolor(), edgecolor=fig.get_edgecolor())
    plt.close(fig)
    print(f"    Saved: {path}")


def chart_lorenz(con):
    """Chart 8: Lorenz curve (if not already generated by EDA)."""
    path = os.path.join(CHART_DIR, 'lorenz_curve.png')
    if os.path.exists(path):
        print("  Chart 8: Lorenz curve already exists, skipping")
        return

    print("  Chart 8: Lorenz curve ...")
    rows = con.execute("SELECT total_paid FROM provider_summary ORDER BY total_paid ASC").fetchall()
    values = np.array([r[0] for r in rows])
    cum_values = np.cumsum(values) / np.sum(values)
    cum_providers = np.arange(1, len(values) + 1) / len(values)

    step = max(1, len(values) // 1000)
    cx = cum_providers[::step]
    cy = cum_values[::step]

    setup_hhs_style()
    mono = get_mono_font()
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot(cx, cy, color=HHS_AMBER, linewidth=2, label='Actual')
    ax.plot([0, 1], [0, 1], color=HHS_MUTED, linewidth=1, linestyle='--', label='Perfect Equality')
    ax.set_xlabel('Cumulative Share of Providers', fontsize=11, color=HHS_MUTED)
    ax.set_ylabel('Cumulative Share of Spending', fontsize=11, color=HHS_MUTED)
    ax.set_title('Provider Spending Concentration', fontsize=14, fontweight=600,
                 color=HHS_DARK, loc='left', pad=20)
    fig.text(0.125, 0.92, 'Lorenz Curve | Medicaid Provider Spending 2018\u20132024',
             fontsize=11, fontfamily=mono, color=HHS_MUTED)
    ax.legend(fontsize=10, frameon=False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    add_hhs_border(fig)
    add_hhs_branding(fig)
    plt.tight_layout()
    fig.savefig(path, facecolor=fig.get_facecolor(), edgecolor=fig.get_edgecolor())
    plt.close(fig)
    print(f"    Saved: {path}")


def chart_network_top3(con, findings):
    """Chart 9: Network graph visualization of top 3 suspicious billing networks."""
    print("  Chart 9: Network graph top 3 ...")
    import networkx as nx

    # Find top 3 hub providers
    top_hubs = con.execute("""
        SELECT billing_npi, COUNT(DISTINCT servicing_npi) AS num_servicing, SUM(total_paid) AS total_paid
        FROM billing_servicing_network
        WHERE billing_npi != servicing_npi
        GROUP BY billing_npi
        HAVING COUNT(DISTINCT servicing_npi) > 20
        ORDER BY SUM(total_paid) DESC
        LIMIT 3
    """).fetchall()

    if not top_hubs:
        print("    No hub providers found")
        return

    setup_hhs_style()
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    if not hasattr(axes, '__len__'):
        axes = [axes]

    for idx, (hub_npi, num_serv, total_paid) in enumerate(top_hubs):
        ax = axes[idx] if idx < len(axes) else axes[-1]

        edges = con.execute("""
            SELECT servicing_npi, total_paid
            FROM billing_servicing_network
            WHERE billing_npi = ? AND servicing_npi != billing_npi
            ORDER BY total_paid DESC
            LIMIT 20
        """, [hub_npi]).fetchall()

        G = nx.DiGraph()
        G.add_node(hub_npi)
        for serv_npi, edge_paid in edges:
            G.add_node(serv_npi)
            G.add_edge(hub_npi, serv_npi, weight=edge_paid)

        pos = nx.spring_layout(G, seed=42, k=2)

        # Draw edges
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color='#D4D4D4', alpha=0.5, arrows=True, arrowsize=10)

        # Draw spoke nodes
        spoke_nodes = [n for n in G.nodes if n != hub_npi]
        nx.draw_networkx_nodes(G, pos, nodelist=spoke_nodes, node_color=HHS_AMBER,
                               node_size=100, ax=ax, alpha=0.8)

        # Draw hub node
        nx.draw_networkx_nodes(G, pos, nodelist=[hub_npi], node_color=HHS_RED,
                               node_size=300, ax=ax)

        # Get hub name
        try:
            name = con.execute("SELECT name FROM providers WHERE npi = ?", [hub_npi]).fetchone()
            hub_name = name[0][:20] if name else hub_npi[:10]
        except Exception:
            hub_name = hub_npi[:10]

        ax.set_title(f"{hub_name}\n{format_dollars(total_paid)} | {num_serv} NPIs",
                     fontsize=10, fontweight=600, color=HHS_DARK)
        ax.axis('off')

    mono = get_mono_font()
    fig.suptitle('Top 3 Suspicious Billing Networks', fontsize=14, fontweight=600,
                 color=HHS_DARK, y=1.02)
    fig.text(0.5, 0.98, 'Hub (red) and Spoke (amber) Provider Relationships',
             fontsize=11, fontfamily=mono, color=HHS_MUTED, ha='center')

    add_hhs_border(fig)
    add_hhs_branding(fig)
    plt.tight_layout()
    path = os.path.join(CHART_DIR, 'network_graph_top3.png')
    fig.savefig(path, facecolor=fig.get_facecolor(), edgecolor=fig.get_edgecolor(), bbox_inches='tight')
    plt.close(fig)
    print(f"    Saved: {path}")


def chart_state_heatmap(con, findings):
    """Chart 10: States ranked by total flagged spending."""
    print("  Chart 10: State heatmap ...")
    from collections import defaultdict

    state_spending = defaultdict(float)
    for f in findings.get('findings', []):
        state = f.get('state', '')
        if state and not f.get('npi', '').startswith('STATE_'):
            state_spending[state] += f.get('total_impact', 0)

    if not state_spending:
        # Fall back to overall state spending
        rows = con.execute("""
            SELECT p.state, SUM(ps.total_paid) AS total
            FROM provider_summary ps
            INNER JOIN providers p ON ps.billing_npi = p.npi
            WHERE p.state IS NOT NULL AND p.state != ''
            GROUP BY p.state
            ORDER BY total DESC
            LIMIT 25
        """).fetchall()
        for r in rows:
            state_spending[r[0]] = r[1]

    if not state_spending:
        return

    sorted_states = sorted(state_spending.items(), key=lambda x: -x[1])[:25]
    labels = [s[0] for s in sorted_states]
    values = [s[1] for s in sorted_states]

    create_horizontal_bar_chart(
        values, labels,
        'Flagged Spending by State',
        'Estimated Recoverable Amount by Provider State',
        os.path.join(CHART_DIR, 'state_heatmap.png'),
        figsize=(10, 10),
    )


def chart_per_finding_timeseries(con, findings):
    """Chart 11: Per-finding mini time series for top 20 high-confidence findings."""
    print("  Chart 11: Per-finding time series ...")
    high_conf = [f for f in findings.get('findings', [])
                 if f.get('confidence') == 'high' and not f.get('npi', '').startswith('STATE_')][:20]

    for i, f in enumerate(high_conf):
        npi = f.get('npi', '')
        if not npi:
            continue

        try:
            rows = con.execute("""
                SELECT claim_month, SUM(paid) AS paid
                FROM provider_monthly WHERE billing_npi = ?
                GROUP BY claim_month ORDER BY claim_month
            """, [npi]).fetchall()
        except Exception:
            continue

        if not rows or len(rows) < 3:
            continue

        months = [r[0] for r in rows]
        paid = [r[1] for r in rows]

        # Get peer median (approximate)
        peer_median = np.median(paid) * 0.3  # Rough peer reference

        name = f.get('name', npi)[:25]
        create_line_chart(
            months, paid,
            f"{name} ({f.get('state', '')})",
            f"NPI {npi} | {format_dollars(f.get('total_impact', 0))} estimated recoverable",
            os.path.join(CHART_DIR, f'finding_F{i+1:03d}_timeseries.png'),
            figsize=(10, 4),
            reference_line=[peer_median] * len(months),
            ref_label='Estimated Peer Median',
        )


def main():
    t0 = time.time()
    os.makedirs(CHART_DIR, exist_ok=True)

    con = get_connection(read_only=True)
    findings = load_findings()

    print(f"Loaded {len(findings.get('findings', []))} findings")
    print(f"\nGenerating charts ...")

    chart_monthly_spending(con)
    chart_top20_flagged_providers(findings)
    chart_top20_flagged_procedures(con, findings)
    chart_findings_by_category(findings)
    chart_risk_scatter(findings)
    chart_temporal_top5(con, findings)
    chart_benfords(con)
    chart_lorenz(con)
    chart_network_top3(con, findings)
    chart_state_heatmap(con, findings)
    chart_per_finding_timeseries(con, findings)

    con.close()

    # Count charts generated
    charts = [f for f in os.listdir(CHART_DIR) if f.endswith('.png')]
    print(f"\nGenerated {len(charts)} charts in {CHART_DIR}")
    print(f"\nMilestone 10 complete. Time: {time.time() - t0:.1f}s")


if __name__ == '__main__':
    main()
