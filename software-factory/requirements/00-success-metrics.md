---
title: "Success Metrics"
type: "overview"
id: "14fadb61-b5f7-4e6e-b2e7-fca47e551874"
---

## Primary Success Metrics

### Detection Coverage and Completeness

**Total Records Analyzed** - The system shall process 100% of billing records in each CMS data export, with no sampling or exclusions. Current baseline: 227,083,361 records representing $1.09 trillion in payments.

**Provider Coverage** - The system shall analyze every billing provider NPI in the dataset, enriching with NPPES registry data where available. Current baseline: 617,503 unique billing providers.

**Hypothesis Execution Rate** - The system shall successfully execute all active hypotheses in the taxonomy, excluding only those flagged as unstable through validation testing. Current baseline: 1,087 hypotheses across 10 categories, with 4 methods pruned for instability.

### Investigation Prioritization Quality

**Multi-Signal Concentration** - At least 80% of the top 500 prioritized providers shall trigger 3 or more independent detection methods, indicating convergent evidence. Current baseline: 90% (450 of top 500).

**Financial Impact Ranking** - The top 100 prioritized providers shall account for at least 40% of the quality-weighted total exposure, demonstrating effective concentration of high-impact leads. Current baseline: 49.8% ($46.7B of $93.8B top-500 pool).

**High-Confidence Finding Rate** - At least 10,000 findings shall meet high-confidence criteria (3+ categories, known fraud pattern, or z-score > 5). Current baseline: 10,913 high-confidence findings.

### Validation and Calibration Metrics

**Holdout Persistence Rate** - At least 60% of providers flagged in the training period (2018-2022) shall remain flagged in the holdout period (2023-2024), demonstrating temporal stability. Current baseline: 65.44% baseline holdout rate.

**Method Stability Threshold** - Detection methods with holdout z-delta below -1.0 shall be flagged for review or pruning. Methods with z-delta above +1.0 are considered highly stable.

**LEIE Cross-Reference Overlap** - The system shall cross-check all findings against the OIG exclusion list (currently 8,302 NPIs) and report overlap rates per detection method.

**Positive Control Validation** (when dataset is available) - Detection methods shall flag at least 70% of known fraud cases in the positive control dataset, demonstrating sensitivity to confirmed bad actors.

### Financial Impact and Exposure Quantification

**Total Provider-Level Exposure** - The system shall quantify total standardized provider-level exposure (excess above peer median, capped at total paid). Current baseline: $354,986,926,844 across all provider-level patterns.

**Systemic vs. Provider Separation** - The system shall separate systemic exposure (state/code aggregates requiring policy intervention) from provider-level exposure (investigation targets). Current baseline: $116,147,010,551 systemic exposure reported separately.

**Deduplication Accuracy** - When a provider appears in multiple fraud patterns, the system shall apply a deduplication method to avoid double-counting exposure. The deduplicated total shall be clearly documented in all executive reports.

### Operational Performance

**Pipeline Execution Time** - The complete 24-milestone pipeline shall execute in under 4 hours on standard hardware (16+ GB RAM, SSD storage).

**Output Completeness** - Every pipeline run shall produce: CMS Administrator Report, executive brief, action plan memo, top 50/100/200/500 investigation queues, fraud pattern summaries, hypothesis validation reports, and at least 40 visualization charts.

**Data Quality Reporting** - The system shall assess and report data quality issues including: negative paid amounts, zero paid amounts, null claim months, missing provider names, and non-standard NPI formats.

### User Adoption and Utilization Metrics

**Investigation Queue Utilization** - At least 80% of high-confidence findings in the top 100 list shall be reviewed by investigators within one quarter of report delivery.

**Recovery Conversion Rate** (when feedback is available) - At least 40% of investigated high-confidence findings shall result in recoveries, enforcement actions, or provider enrollment terminations.

**Policy Action Conversion** - At least 3 systemic findings per report shall result in policy recommendations (rate changes, authorization rules, program design reforms) within one year.

### Reporting and Communication Metrics

**Executive Brief Readability** - The one-page executive brief shall summarize key findings in language accessible to non-technical stakeholders, requiring no specialized statistical knowledge.

**Evidence Package Completeness** - For each top 100 provider, the system shall provide: provider name and NPI, state, total paid, quality-weighted exposure, number of flagging methods, list of flagging method names, peer comparison baselines, and time series visualization (when applicable).

**Chart Clarity and Coverage** - The system shall generate at least 40 visualizations covering: spending trends, fraud heatmaps, Benford's Law analysis, Lorenz curves, network graphs, state comparisons, temporal anomalies, and top provider/procedure rankings.

## Secondary Metrics

**False Positive Reduction** - Year-over-year reduction in the number of flagged providers that, upon investigation, are determined to be legitimate billing practices or policy issues rather than fraud.

**Method Correlation Analysis** - Documentation of which detection methods frequently co-occur, enabling identification of method families and redundant signals.

**State Quality Weighting Impact** - Quantification of how state-level quality weights adjust exposure estimates, demonstrating the system's ability to account for data quality variations.

**Coverage of Fraud Pattern Taxonomy** - All 10 fraud pattern categories shall have at least 10 flagged providers, ensuring comprehensive pattern detection across the taxonomy.

## Success Thresholds

**Minimum Viable Performance** - The system must process 100% of records, execute 95%+ of active hypotheses, generate all required reports, and produce a prioritized top 500 list with at least 70% multi-signal concentration.

**Target Performance** - The system should achieve 90%+ multi-signal concentration in the top 500, 65%+ holdout persistence, and produce actionable leads that convert to investigations at 40%+ rate.

**Exceptional Performance** - The system should identify novel fraud patterns not previously documented, achieve 95%+ holdout persistence for top-tier methods, and support policy reforms that measurably reduce systemic waste.
