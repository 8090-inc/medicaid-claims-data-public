#!/usr/bin/env python3
"""Milestone 3: Exploratory data analysis and profiling.

Produces a JSON data profile and baseline charts establishing normal patterns.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.db_utils import get_connection, format_dollars
from utils.chart_utils import (
    setup_hhs_style, create_horizontal_bar_chart, create_line_chart,
    HHS_AMBER, HHS_DARK, HHS_MUTED, HHS_GRID, add_hhs_border, add_hhs_branding,
    get_title_font, get_mono_font, dollar_formatter
)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
CHART_DIR = os.path.join(OUTPUT_DIR, 'charts')


def main():
    t0 = time.time()
    os.makedirs(CHART_DIR, exist_ok=True)
    con = get_connection(read_only=True)

    profile = {}

    # --- Global Statistics ---
    print("Computing global statistics ...")
    stats = con.execute("""
        SELECT
            COUNT(*)                            AS total_rows,
            COUNT(DISTINCT billing_npi)         AS unique_billing_npis,
            COUNT(DISTINCT servicing_npi)       AS unique_servicing_npis,
            COUNT(DISTINCT hcpcs_code)          AS unique_hcpcs_codes,
            COUNT(DISTINCT claim_month)         AS unique_months,
            SUM(paid)                           AS total_paid,
            SUM(claims)                         AS total_claims,
            SUM(beneficiaries)                  AS total_beneficiaries,
            AVG(paid)                           AS avg_paid,
            STDDEV(paid)                        AS std_paid,
            SUM(CASE WHEN paid < 0 THEN 1 ELSE 0 END) AS negative_paid_rows,
            SUM(CASE WHEN servicing_npi IS NULL OR servicing_npi = '' THEN 1 ELSE 0 END) AS null_servicing_rows
        FROM claims
    """).fetchone()

    median_paid = con.execute("SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY paid) FROM claims").fetchone()[0]

    profile['total_rows'] = stats[0]
    profile['unique_billing_npis'] = stats[1]
    profile['unique_servicing_npis'] = stats[2]
    profile['unique_hcpcs_codes'] = stats[3]
    profile['unique_months'] = stats[4]
    profile['total_paid'] = stats[5]
    profile['total_claims'] = stats[6]
    profile['total_beneficiaries'] = stats[7]
    profile['avg_paid'] = stats[8]
    profile['median_paid'] = median_paid
    profile['std_paid'] = stats[9]
    profile['negative_paid_rows'] = stats[10]
    profile['null_servicing_rows'] = stats[11]

    print(f"  Total rows: {stats[0]:,}")
    print(f"  Total paid: {format_dollars(stats[5])}")
    print(f"  Unique billing NPIs: {stats[1]:,}")

    # --- Top 100 providers ---
    print("Fetching top 100 providers by spending ...")
    top_providers = con.execute("""
        SELECT
            ps.billing_npi,
            COALESCE(p.name, 'NPI ' || ps.billing_npi) AS name,
            COALESCE(p.state, '') AS state,
            COALESCE(p.specialty, '') AS specialty,
            ps.total_paid,
            ps.total_claims,
            ps.total_beneficiaries,
            ps.num_codes,
            ps.num_months
        FROM provider_summary ps
        LEFT JOIN providers p ON ps.billing_npi = p.npi
        ORDER BY ps.total_paid DESC
        LIMIT 100
    """).fetchall()
    profile['top_100_providers'] = [
        {'npi': r[0], 'name': r[1], 'state': r[2], 'specialty': r[3],
         'total_paid': r[4], 'total_claims': r[5], 'total_beneficiaries': r[6],
         'num_codes': r[7], 'num_months': r[8]}
        for r in top_providers
    ]

    # --- Top 100 HCPCS codes ---
    print("Fetching top 100 HCPCS codes by spending ...")
    top_codes = con.execute("""
        SELECT
            hs.hcpcs_code,
            COALESCE(hc.short_desc, 'Code ' || hs.hcpcs_code) AS description,
            COALESCE(hc.category, 'Other') AS category,
            hs.total_paid,
            hs.total_claims,
            hs.num_providers
        FROM hcpcs_summary hs
        LEFT JOIN hcpcs_codes hc ON hs.hcpcs_code = hc.hcpcs_code
        ORDER BY hs.total_paid DESC
        LIMIT 100
    """).fetchall()
    profile['top_100_hcpcs'] = [
        {'code': r[0], 'description': r[1], 'category': r[2],
         'total_paid': r[3], 'total_claims': r[4], 'num_providers': r[5]}
        for r in top_codes
    ]

    # --- Monthly spending ---
    print("Computing monthly spending ...")
    monthly = con.execute("""
        SELECT claim_month, SUM(paid) AS total_paid, SUM(claims) AS total_claims
        FROM claims
        GROUP BY claim_month
        ORDER BY claim_month
    """).fetchall()
    profile['monthly_spending'] = [
        {'month': r[0], 'total_paid': r[1], 'total_claims': r[2]}
        for r in monthly
    ]

    # --- Spending concentration (Pareto) ---
    print("Computing spending concentration ...")
    pareto = con.execute("""
        WITH ranked AS (
            SELECT
                billing_npi,
                total_paid,
                SUM(total_paid) OVER (ORDER BY total_paid DESC) AS cumulative_paid,
                ROW_NUMBER() OVER (ORDER BY total_paid DESC) AS rank_num,
                COUNT(*) OVER () AS total_providers,
                SUM(total_paid) OVER () AS grand_total
            FROM provider_summary
        )
        SELECT
            MIN(CASE WHEN cumulative_paid >= grand_total * 0.5 THEN rank_num END) * 100.0 / MAX(total_providers) AS pct_50,
            MIN(CASE WHEN cumulative_paid >= grand_total * 0.8 THEN rank_num END) * 100.0 / MAX(total_providers) AS pct_80,
            MIN(CASE WHEN cumulative_paid >= grand_total * 0.9 THEN rank_num END) * 100.0 / MAX(total_providers) AS pct_90,
            MIN(CASE WHEN cumulative_paid >= grand_total * 0.99 THEN rank_num END) * 100.0 / MAX(total_providers) AS pct_99
        FROM ranked
    """).fetchone()
    profile['spending_concentration'] = {
        'pct_providers_for_50pct_spend': round(pareto[0], 2) if pareto[0] else None,
        'pct_providers_for_80pct_spend': round(pareto[1], 2) if pareto[1] else None,
        'pct_providers_for_90pct_spend': round(pareto[2], 2) if pareto[2] else None,
        'pct_providers_for_99pct_spend': round(pareto[3], 2) if pareto[3] else None,
    }
    print(f"  Concentration: {profile['spending_concentration']}")

    # --- Write data profile ---
    profile_path = os.path.join(OUTPUT_DIR, 'data_profile.json')
    with open(profile_path, 'w') as f:
        json.dump(profile, f, indent=2, default=str)
    print(f"\nData profile written to {profile_path}")

    # === Chart Generation ===

    # Chart 1: Monthly Spending Trend
    print("\nGenerating charts ...")
    months = [r[0] for r in monthly]
    paid_vals = [r[1] for r in monthly]

    # Convert months to FY labels for display
    def month_to_fy(m):
        year, mo = int(m[:4]), int(m[5:7])
        if mo >= 10:
            return f"FY{year + 1}"
        return f"FY{year}"

    create_line_chart(
        x=months,
        y=paid_vals,
        title='Monthly Medicaid Provider Spending',
        subtitle='January 2018 \u2013 December 2024 | Total Fee-for-Service and Managed Care',
        output_path=os.path.join(CHART_DIR, 'monthly_spending_trend.png'),
    )

    # Chart 2: Top 20 Procedures by Spending
    top20_codes = top_codes[:20]
    code_labels = [f"{r[0]} - {r[1][:40]}" for r in top20_codes]
    code_vals = [r[3] for r in top20_codes]
    create_horizontal_bar_chart(
        data=code_vals,
        labels=code_labels,
        title='Top 20 Procedures by Total Spending',
        subtitle='HCPCS Code | Total Medicaid Paid 2018\u20132024',
        output_path=os.path.join(CHART_DIR, 'top20_procedures.png'),
        figsize=(12, 10),
    )

    # Chart 3: Top 20 Providers by Spending
    top20_prov = top_providers[:20]
    prov_labels = [f"{r[1][:35]} ({r[2]})" for r in top20_prov]
    prov_vals = [r[4] for r in top20_prov]
    create_horizontal_bar_chart(
        data=prov_vals,
        labels=prov_labels,
        title='Top 20 Providers by Total Spending',
        subtitle='Billing Provider | Total Medicaid Paid 2018\u20132024',
        output_path=os.path.join(CHART_DIR, 'top20_providers.png'),
        figsize=(12, 10),
    )

    # Chart 4: Lorenz Curve (Provider Spending Concentration)
    print("  Computing Lorenz curve ...")
    lorenz_data = con.execute("""
        SELECT total_paid FROM provider_summary ORDER BY total_paid ASC
    """).fetchall()
    values = np.array([r[0] for r in lorenz_data])
    cum_values = np.cumsum(values) / np.sum(values)
    cum_providers = np.arange(1, len(values) + 1) / len(values)

    # Subsample for plotting
    step = max(1, len(values) // 1000)
    cx = cum_providers[::step]
    cy = cum_values[::step]

    setup_hhs_style()
    mono = get_mono_font()
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot(cx, cy, color=HHS_AMBER, linewidth=2, label='Actual Distribution')
    ax.plot([0, 1], [0, 1], color=HHS_MUTED, linewidth=1, linestyle='--', label='Perfect Equality')
    ax.set_xlabel('Cumulative Share of Providers', fontsize=11, color=HHS_MUTED)
    ax.set_ylabel('Cumulative Share of Spending', fontsize=11, color=HHS_MUTED)
    ax.set_title('Provider Spending Concentration', fontsize=14, fontweight=600, color=HHS_DARK, loc='left', pad=20)
    fig.text(0.125, 0.92, 'Lorenz Curve | Medicaid Provider Spending 2018\u20132024', fontsize=11, fontfamily=mono, color=HHS_MUTED)
    ax.legend(fontsize=10, frameon=False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    add_hhs_border(fig)
    add_hhs_branding(fig)
    plt.tight_layout()
    lorenz_path = os.path.join(CHART_DIR, 'lorenz_curve.png')
    fig.savefig(lorenz_path, facecolor=fig.get_facecolor(), edgecolor=fig.get_edgecolor())
    plt.close(fig)
    print(f"  Chart saved: {lorenz_path}")

    con.close()
    print(f"\nMilestone 3 complete. Time: {time.time() - t0:.1f}s")


if __name__ == '__main__':
    main()
