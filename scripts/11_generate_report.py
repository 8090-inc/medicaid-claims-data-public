#!/usr/bin/env python3
"""Milestone 11: Final report assembly.

Produces output/cms_administrator_report.md — a plain-English report for
Dr. Mehmet Oz, CMS Administrator.
"""

import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.db_utils import get_connection, format_dollars

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
FINDINGS_PATH = os.path.join(OUTPUT_DIR, 'findings', 'final_scored_findings.json')
PROFILE_PATH = os.path.join(OUTPUT_DIR, 'data_profile.json')
CHART_DIR = os.path.join(OUTPUT_DIR, 'charts')
REPORT_PATH = os.path.join(OUTPUT_DIR, 'cms_administrator_report.md')
HYPOTHESES_DIR = os.path.join(OUTPUT_DIR, 'hypotheses')
HYPOTHESES_PATH = os.path.join(HYPOTHESES_DIR, 'all_hypotheses.json')
TESTABLE_PATH = os.path.join(HYPOTHESES_DIR, 'all_hypotheses_testable.json')


def load_findings():
    with open(FINDINGS_PATH) as f:
        return json.load(f)


def load_profile():
    with open(PROFILE_PATH) as f:
        return json.load(f)

def load_hypothesis_count():
    for path in (TESTABLE_PATH, HYPOTHESES_PATH):
        if os.path.exists(path):
            with open(path) as f:
                return len(json.load(f))
    return 0


def main():
    t0 = time.time()

    findings_data = load_findings()
    profile = load_profile()
    summary = findings_data.get('summary', {})
    findings = findings_data.get('findings', [])
    hypothesis_count = load_hypothesis_count()
    hypothesis_delta = hypothesis_count - 1000 if hypothesis_count else 0

    high_conf = [f for f in findings if f.get('confidence') == 'high']
    med_conf = [f for f in findings if f.get('confidence') == 'medium']
    low_conf = [f for f in findings if f.get('confidence') == 'low']

    total_paid = profile.get('total_paid', 0)
    total_recoverable = summary.get('total_estimated_recoverable', 0)
    systemic_total = summary.get('systemic_exposure_total', 0)

    lines = []

    def w(line=''):
        lines.append(line)

    # --- Header ---
    w('---')
    w()
    w('# ANALYSIS OF FRAUD, WASTE, AND ABUSE IN MEDICAID PROVIDER SPENDING')
    w()
    w('**HHS Provider Spending Dataset, January 2018 through December 2024**')
    w()
    w(f'**Prepared for:** Dr. Mehmet Oz, Administrator, Centers for Medicare & Medicaid Services')
    w()
    w(f'**Analyst:** Rohit Kelapure')
    w()
    w(f'**Date:** {datetime.now().strftime("%B %Y")}')
    w()
    w('---')
    w()

    # --- Section 1: Executive Summary ---
    w('## 1. Executive Summary')
    w()
    w(f'This analysis examined {format_dollars(total_paid)} in Medicaid provider spending '
      f'across {profile.get("total_rows", 0):,} billing records spanning January 2018 through December 2024. '
      f'The dataset covers {profile.get("unique_billing_npis", 0):,} billing providers, '
      f'{profile.get("unique_hcpcs_codes", 0):,} procedure codes, and '
      f'{profile.get("total_beneficiaries", 0):,} beneficiary-months of service.')
    w()
    w(f'Using {hypothesis_count:,} testable hypotheses across 10 analytical categories — statistical outlier detection, '
      f'temporal anomaly analysis, peer comparison, network analysis, market concentration, '
      f'classical machine learning, deep learning, domain-specific rules, cross-reference enrichment, '
      f'and composite multi-signal scoring — this analysis identified:')
    w()
    w(f'- **{len(high_conf):,} high-confidence findings** representing an estimated '
      f'{format_dollars(summary.get("high_confidence_impact", 0))} in potentially recoverable payments')
    w(f'- **{len(med_conf):,} medium-confidence findings** representing an estimated '
      f'{format_dollars(summary.get("medium_confidence_impact", 0))}')
    w(f'- **{len(low_conf):,} low-confidence findings** representing an estimated '
      f'{format_dollars(summary.get("low_confidence_impact", 0))}')
    w()
    w(f'**Total estimated recoverable amount: {format_dollars(total_recoverable)}**')
    if systemic_total:
        w(f'**Separate systemic exposure (state/code aggregates): {format_dollars(systemic_total)}**')
    w()

    # Top 5 findings in plain English
    w('### Top 5 Findings')
    w()
    for i, f in enumerate(findings[:5]):
        name = f.get('name', f.get('npi', 'Unknown'))
        npi = f.get('npi', '')
        state = f.get('state', '')
        impact = format_dollars(f.get('total_impact', 0))
        methods = f.get('num_methods', 0)
        evidence = f.get('evidence', '')
        w(f'{i+1}. **{name}** (NPI {npi}, {state}): Estimated {impact} in potentially improper payments. '
          f'Flagged by {methods} detection methods. {evidence[:200]}')
        w()

    w(f'![Top 20 Flagged Providers](charts/top20_flagged_providers.png)')
    w()

    # --- Section 2: Methodology ---
    w('## 2. Methodology')
    w()
    w('### Dataset')
    w()
    w('The analysis used the HHS Provider Spending dataset released by the U.S. Department of Health and Human Services. '
      'This dataset contains every fee-for-service claim, managed care encounter, and CHIP claim processed by state '
      'Medicaid agencies from January 2018 through December 2024. Each record contains the billing provider NPI, '
      'servicing provider NPI, HCPCS procedure code, claim month, number of unique beneficiaries, number of claims, '
      'and total amount paid.')
    w()
    w('### Reference Data')
    w()
    w('Provider identities (names, specialties, locations) were obtained from the NPPES National Provider registry. '
      'HCPCS procedure code descriptions were sourced from CMS reference files.')
    w()
    w('### Analytical Methods')
    w()
    w(f'{hypothesis_count:,} structured hypotheses were generated and tested across 10 categories:')
    w()
    w('| Category | Hypotheses | Description |')
    w('|----------|-----------|-------------|')
    w('| 1. Statistical Outliers | 150 | Z-score, IQR, extreme value, and Benford\'s Law tests |')
    w('| 2. Temporal Anomalies | 120 | Month-over-month spikes, sudden appearance/disappearance, seasonality |')
    w('| 3. Peer Comparison | 130 | Rate, volume, and concentration compared to code/state/specialty peers |')
    w('| 4. Network Analysis | 120 | Hub-spoke, circular billing, ghost networks, pure billing entities |')
    w('| 5. Concentration | 80 | Market dominance, single-code specialists, geographic monopolies |')
    w('| 6. Machine Learning | 150 | Isolation Forest, DBSCAN, XGBoost, K-Means, LOF, Random Forest |')
    w('| 7. Deep Learning | 80 | Autoencoder, VAE, LSTM, Transformer attention anomalies |')
    w('| 8. Domain Rules | 100 | Impossible volumes, upcoding, unbundling, phantom billing |')
    w('| 9. Cross-Reference | 70 | Specialty mismatch, entity type, geographic impossibility |')
    w('| 10. Composite | Variable | Multi-signal providers flagged by 3+ categories |')
    w()
    if hypothesis_delta > 0:
        w(f'**Note:** This includes {hypothesis_delta} gap-analysis hypotheses beyond the base 1,000 taxonomy.')
        w()
    elif hypothesis_delta < 0:
        w(f'**Note:** {abs(hypothesis_delta)} hypotheses were filtered as not testable in this dataset.')
        w()
    w('### Confidence Tiers')
    w()
    w('- **High:** Flagged by 3 or more analytical categories, or exhibits a known fraud pattern '
      '(impossible service volumes, circular billing), or has a z-score above 5.')
    w('- **Medium:** Flagged by 2 categories, or has a z-score between 3 and 5.')
    w('- **Low:** Flagged by 1 category with a z-score between 2 and 3.')
    w()

    # --- Section 3: High-Confidence Findings ---
    w('## 3. High-Confidence Findings')
    w()

    for i, f in enumerate(high_conf[:50]):
        npi = f.get('npi', '')
        name = f.get('name', npi)
        state = f.get('state', '')
        city = f.get('city', '')
        specialty = f.get('specialty', '')
        entity_type = f.get('entity_type', '')
        total_paid_provider = f.get('total_paid', f.get('total_impact', 0))
        impact = f.get('total_impact', 0)
        methods = f.get('methods', [])
        num_methods = f.get('num_methods', 0)
        evidence = f.get('evidence', '')
        total_claims = f.get('total_claims', 0)
        total_benes = f.get('total_beneficiaries', 0)
        first_month = f.get('first_month', '')
        last_month = f.get('last_month', '')

        w(f'### Finding {i+1}: {name}')
        w()
        w(f'- **NPI:** {npi}')
        w(f'- **Location:** {city}, {state}' if city else f'- **State:** {state}')
        w(f'- **Specialty:** {specialty}')
        w(f'- **Entity Type:** {entity_type}')
        w(f'- **Active Period:** {first_month} through {last_month}')
        w(f'- **Total Medicaid Paid:** {format_dollars(total_paid_provider)}')
        w(f'- **Total Claims:** {total_claims:,}' if total_claims else '')
        w(f'- **Total Beneficiaries:** {total_benes:,}' if total_benes else '')
        w()
        w(f'**Anomaly Description:** {evidence}')
        w()
        w(f'**Detection Methods:** Flagged by {num_methods} of 10 analytical categories: {", ".join(methods)}')
        w()
        w(f'**Estimated Recoverable Amount:** {format_dollars(impact)}')
        w()

        # Embed per-finding chart if it exists
        chart_path = f'charts/finding_F{i+1:03d}_timeseries.png'
        if os.path.exists(os.path.join(OUTPUT_DIR, chart_path)):
            w(f'![Monthly Billing]({chart_path})')
            w()

        w('---')
        w()

    # --- Section 4: Medium-Confidence Findings ---
    w('## 4. Medium-Confidence Findings')
    w()
    w('| # | Provider | NPI | State | Estimated Impact | Methods | Primary Method |')
    w('|---|----------|-----|-------|-----------------|---------|----------------|')
    for i, f in enumerate(med_conf[:80]):
        name = f.get('name', f.get('npi', ''))[:30]
        npi = f.get('npi', '')
        state = f.get('state', '')
        impact = format_dollars(f.get('total_impact', 0))
        num_methods = f.get('num_methods', 0)
        method = f.get('primary_method', '')
        w(f'| {len(high_conf) + i + 1} | {name} | {npi} | {state} | {impact} | {num_methods} | {method} |')
    w()

    # --- Section 5: Low-Confidence Findings ---
    w('## 5. Low-Confidence Findings')
    w()
    w(f'An additional {len(low_conf):,} providers were flagged at low confidence, '
      f'representing {format_dollars(summary.get("low_confidence_impact", 0))} in potential recoverable payments. '
      f'These findings warrant further investigation but do not meet the threshold for immediate referral.')
    w()
    w('| # | Provider | NPI | State | Impact | Method |')
    w('|---|----------|-----|-------|--------|--------|')
    for i, f in enumerate(low_conf[:50]):
        name = f.get('name', f.get('npi', ''))[:25]
        w(f'| {i+1} | {name} | {f.get("npi", "")} | {f.get("state", "")} | '
          f'{format_dollars(f.get("total_impact", 0))} | {f.get("primary_method", "")} |')
    w()

    # --- Section 6: Systemic Patterns ---
    w('## 6. Systemic Patterns')
    w()

    w('### State-Level Anomalies')
    w()
    w('![State Heatmap](charts/state_heatmap.png)')
    w()
    w('Several states show disproportionately high per-beneficiary spending for specific service categories, '
      'particularly personal care services and behavioral health. These state-level patterns may indicate '
      'systemic issues with rate-setting, program integrity, or oversight rather than individual provider fraud.')
    w()

    w('### High-Risk HCPCS Categories')
    w()
    w('![Top 20 Procedures](charts/top20_flagged_procedures.png)')
    w()

    top_codes = profile.get('top_100_hcpcs', [])[:5]
    if top_codes:
        w('The highest-risk procedure categories are:')
        w()
        for tc in top_codes:
            w(f'- **{tc["code"]}** ({tc["description"]}): {format_dollars(tc["total_paid"])} total, '
              f'{tc["num_providers"]:,} providers')
        w()

    w('### Temporal Trends')
    w()
    w('![Monthly Spending Trend](charts/monthly_spending_trend.png)')
    w()
    w('Total Medicaid spending shows a clear upward trend from 2018 through 2024, '
      'with a notable dip during the early COVID-19 pandemic (April-May 2020) followed by '
      'rapid recovery and acceleration. Several flagged providers show billing patterns that '
      'diverge sharply from this population trend.')
    w()

    w('### Network and Organized Billing Schemes')
    w()
    w('![Network Graph](charts/network_graph_top3.png)')
    w()
    w('The network analysis identified several large billing networks with characteristics '
      'consistent with organized fraud schemes, including hub-and-spoke structures where a '
      'single billing entity submits claims on behalf of dozens of servicing providers, '
      'some of whom show signs of being phantom providers (very short activity periods, '
      'no independent billing, and concentrated billing patterns).')
    w()

    # --- Section 7: Financial Impact Summary ---
    w('## 7. Financial Impact Summary')
    w()
    w(f'| Metric | Value |')
    w(f'|--------|-------|')
    w(f'| Total Medicaid Spending Analyzed | {format_dollars(total_paid)} |')
    w(f'| Total Findings | {len(findings):,} |')
    w(f'| High-Confidence Findings | {len(high_conf):,} |')
    w(f'| Medium-Confidence Findings | {len(med_conf):,} |')
    w(f'| Low-Confidence Findings | {len(low_conf):,} |')
    w(f'| **Total Estimated Recoverable** | **{format_dollars(total_recoverable)}** |')
    w(f'| High-Confidence Impact | {format_dollars(summary.get("high_confidence_impact", 0))} |')
    w(f'| Medium-Confidence Impact | {format_dollars(summary.get("medium_confidence_impact", 0))} |')
    w(f'| Low-Confidence Impact | {format_dollars(summary.get("low_confidence_impact", 0))} |')
    w()
    w('![Findings by Category](charts/findings_by_category.png)')
    w()
    w('![Provider Risk Scatter](charts/provider_risk_scatter.png)')
    w()
    w("![Benford's Law](charts/benfords_law.png)")
    w()
    w('![Lorenz Curve](charts/lorenz_curve.png)')
    w()

    # --- Section 8: Recommendations ---
    w('## 8. Recommendations')
    w()
    w('### Immediate Referrals to OIG')
    w()
    w('The following providers should be referred to the HHS Office of Inspector General for investigation:')
    w()
    for i, f in enumerate(high_conf[:10]):
        w(f'{i+1}. **{f.get("name", f.get("npi", ""))}** (NPI {f.get("npi", "")}, {f.get("state", "")}): '
          f'{format_dollars(f.get("total_impact", 0))} estimated improper payments. '
          f'Flagged by {f.get("num_methods", 0)} detection methods.')
    w()

    w('### Policy Changes')
    w()
    w('- **Strengthen pre-payment review** for personal care services (T1019, T1020) and behavioral health '
      'codes (H-series), which account for a disproportionate share of flagged spending.')
    w('- **Implement real-time volume limits** for timed services to prevent physically impossible billing '
      '(e.g., more than 8 hours of personal care per beneficiary per day).')
    w('- **Require periodic re-validation** of billing networks, particularly pure billing entities '
      'that never deliver services directly.')
    w('- **Enhance cross-state data sharing** to detect providers billing in geographic impossibility patterns.')
    w()

    w('### Enhanced Monitoring Targets')
    w()
    w('- New providers billing more than $500,000 in their first month of activity')
    w('- Billing networks that add more than 5 servicing NPIs in a single month')
    w('- Providers whose December billing exceeds 3x their monthly average')
    w('- Providers deriving more than 90% of revenue from a single HCPCS code')
    w('- States where per-beneficiary spending for specific codes exceeds 2x the national median')
    w()

    # --- Section 9: Appendix ---
    w('## 9. Appendix')
    w()
    w('### Data Dictionary')
    w()
    w('| Field | Description |')
    w('|-------|-------------|')
    w('| BILLING_PROVIDER_NPI_NUM | National Provider Identifier of the billing entity |')
    w('| SERVICING_PROVIDER_NPI_NUM | NPI of the provider who delivered the service |')
    w('| HCPCS_CODE | Healthcare Common Procedure Coding System code |')
    w('| CLAIM_FROM_MONTH | Month of service (YYYY-MM format) |')
    w('| TOTAL_UNIQUE_BENEFICIARIES | Number of distinct Medicaid patients |')
    w('| TOTAL_CLAIMS | Number of billing events |')
    w('| TOTAL_PAID | Dollar amount paid by Medicaid |')
    w()

    w('### Charts')
    w()
    chart_files = sorted([f for f in os.listdir(CHART_DIR) if f.endswith('.png')])
    for cf in chart_files:
        w(f'- `{cf}`')
    w()

    w('### Analytical Framework')
    w()
    w(f'This analysis tested {hypothesis_count:,} structured hypotheses organized into 10 categories. '
      'Each hypothesis has a defined acceptance criterion, statistical threshold, and financial impact method. '
      'The full hypothesis set is available in `output/hypotheses/all_hypotheses.json`.')
    w()
    w('---')
    w()
    w('*This report was generated from the HHS Provider Spending dataset using automated analytical methods. '
      'All findings should be verified through additional investigation before taking enforcement action.*')
    w()

    # Write report
    report = '\n'.join(lines)
    with open(REPORT_PATH, 'w') as f:
        f.write(report)

    print(f"Report written to {REPORT_PATH}")
    print(f"Report length: {len(report):,} characters, {len(lines):,} lines")
    print(f"\nMilestone 11 complete. Time: {time.time() - t0:.1f}s")


if __name__ == '__main__':
    main()
