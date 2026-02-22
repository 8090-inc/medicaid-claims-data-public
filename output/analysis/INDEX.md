# Medicaid Claims Fraud Detection — Master Index

**Dataset:** HHS Provider Spending, January 2018 through December 2024
**Scope:** $1.09 trillion across 227M billing records, 617,503 providers, 84 months

![Monthly Medicaid Provider Spending, Jan 2018 – Dec 2024](../charts/monthly_spending_trend.png)

![Fraud Pattern Heat Map](../charts/fraud_heatmap_aligned.png)

---

## Executive Reports

| Document | Description |
|----------|-------------|
| [executive_brief.md](executive_brief.md) | One-page summary: top 500 leads, quality-weighted exposure, dominant signal families. |
| [action_plan_memo.md](action_plan_memo.md) | CEO action plan: 30-day priorities, policy actions, risk concentration, deliverables. |

---

## Fraud Pattern Analysis

| Document | Description |
|----------|-------------|
| [fraud_patterns.md](fraud_patterns.md) | Comprehensive 10-pattern analysis with provider examples, methodology, and cross-cutting observations. Technical audience. |
| [fraud_patterns_summary.md](fraud_patterns_summary.md) | Plain-language version of the 10 patterns for non-technical readers. |

---

## Sector Deep Dives

| Document | Description |
|----------|-------------|
| [ltc_nursing_home_trends.md](ltc_nursing_home_trends.md) | Long-term care and nursing home trends: facility-to-home shift, T1019 dominance, nursing home contraction, assisted living growth, spending extrapolations through 2028. |

---

## Methodology and Calibration

| Document | Description |
|----------|-------------|
| [calibration_report.md](calibration_report.md) | Holdout + placebo calibration: most stable/unstable methods, LEIE overlap rates. |
| [hypothesis_validation_summary.md](hypothesis_validation_summary.md) | 1,087 hypotheses tested: 481 supported, 606 unsupported. Totals by method. |
| [longitudinal_multivariate_report.md](longitudinal_multivariate_report.md) | Time-range overview: top states, specialties, HCPCS codes by total paid. |
| [pruned_methods.csv](pruned_methods.csv) | Four methods removed for instability. |
| [method_calibration.csv](method_calibration.csv) | Per-method holdout rates and z-delta scores. |
| [positive_control_overlaps.csv](positive_control_overlaps.csv) | LEIE overlap rates per detection method. |

---

## Data Tables

| File | Description |
|------|-------------|
| [monthly_totals.csv](monthly_totals.csv) | Monthly spending totals (Jan 2018 – Dec 2024). |
| [state_monthly_totals.csv](state_monthly_totals.csv) | Spending by state and month. |
| [specialty_monthly_totals.csv](specialty_monthly_totals.csv) | Spending by provider specialty and month. |
| [code_monthly_totals_top200.csv](code_monthly_totals_top200.csv) | Top 200 HCPCS codes by month. |

---

## Visualizations

All charts are in `output/charts/`. 14 PNG files total.

### Overview Charts

| Chart | Description |
|-------|-------------|
| [monthly_spending_trend.png](../charts/monthly_spending_trend.png) | Total Medicaid spending by month, Jan 2018 – Dec 2024. |
| [top20_procedures.png](../charts/top20_procedures.png) | Top 20 HCPCS procedure codes by total paid. |
| [lorenz_curve.png](../charts/lorenz_curve.png) | Spending concentration (Lorenz curve). |
| [hhs_examples_full_page.png](../charts/hhs_examples_full_page.png) | HHS dataset page reference. |

### Card Views (Summary)

| Chart | Description |
|-------|-------------|
| [card1_monthly_spending.png](../charts/card1_monthly_spending.png) | Monthly spending trend (card format). |
| [card2_top_procedures.png](../charts/card2_top_procedures.png) | Top procedures (card format). |

### Fraud Detection Charts

| Chart | Description |
|-------|-------------|
| [top20_flagged_procedures.png](../charts/top20_flagged_procedures.png) | Top 20 flagged procedure codes. |
| [findings_by_category.png](../charts/findings_by_category.png) | Finding distribution by analytical category. |
| [provider_risk_scatter.png](../charts/provider_risk_scatter.png) | Provider risk scatter plot (methods vs. exposure). |
| [state_heatmap.png](../charts/state_heatmap.png) | Risk exposure by state (heat map). |
| [benfords_law.png](../charts/benfords_law.png) | Benford's law analysis of billing amounts. |
| [network_graph_top3.png](../charts/network_graph_top3.png) | Network graph of top 3 billing networks. |

### Fraud Heatmaps

| Chart | Description |
|-------|-------------|
| [fraud_heatmap_final.png](../charts/fraud_heatmap_final.png) | Fraud pattern intensity matrix (final version). |
| [fraud_heatmap_aligned.png](../charts/fraud_heatmap_aligned.png) | Fraud heatmap with aligned spending/risk columns. |
| [fraud_heatmap_merged.png](../charts/fraud_heatmap_merged.png) | Merged spending + risk heatmap. |
| [fraud_heatmap_v1.png](../charts/fraud_heatmap_v1.png) | Fraud heatmap (initial version). |

### Interactive

| File | Description |
|------|-------------|
| [fraud_heatmap.html](fraud_heatmap.html) | Interactive HTML fraud pattern heatmap with merged spending + risk columns. |

---

## Key Numbers at a Glance

| Metric | Value |
|--------|-------|
| Total Medicaid spending (2018–2024) | $1,093,562,833,513 |
| Total billing records analyzed | 227,083,361 |
| Individual claim transactions | 18,825,564,012 |
| Providers analyzed | 617,503 |
| Provider-level standardized exposure | $354,986,926,844 |
| Systemic rate/code exposure | $116,147,010,551 |
| Quality-weighted provider exposure | $325,267,268,838 |
| High-confidence findings | 10,913 |
| Medium-confidence findings | 19,379 |
| Low-confidence findings | 560,889 |
| Detection methods (after pruning) | ~60 active methods |
| Methods pruned for instability | 4 |
| Largest single HCPCS code: T1019 | $122,739,547,514 (11.2% of total) |
| LTC sector total (2018–2024) | $191.2B (17.5% of total) |
| LTC annual growth rate (CAGR 2018–2023) | 17.9% |

---

## Pattern Summary (Quick Reference)

| # | Pattern | Provider Exposure | Providers | Key Insight |
|---|---------|-------------------|-----------|-------------|
| 1 | Home Health & Personal Care | $55.1B | 20,041 | T1019 = 11.2% of all Medicaid; NY agencies dominate |
| 2 | Middleman Billing | $36.5B | 1,915 | GuardianTrac: 15 methods, $1.24B exposure |
| 3 | Government Agency Outliers | $53.5B | 20,583 | 11 of top 20 are public entities — policy, not fraud |
| 4 | Providers That Cannot Exist | $0.9B + $116.1B systemic | 407 | 3 unregistered IDs billed in 24-30 states |
| 5 | Billing Every Day | $9.6B | 20 | Weak standalone signal; strong corroborator |
| 6 | Sudden Starts & Stops | $91.8B | 2,433 | Largest by dollar; Dec 2024 data caveat applies |
| 7 | Billing Networks | $11.3B | 846 | Mains'l Florida: 81x rate markup |
| 8 | State Rate Differences | $77.5B systemic | 20 combos | NY T1019: 2.1x national median |
| 9 | Upcoding & Impossible Volumes | $3.4B | 36 | Major hospital systems need chart review, not fraud referral |
| 10 | Shared Beneficiary Counts | $2.4B | 19 | CARE Inc (NY): 240,183 matching benes |

