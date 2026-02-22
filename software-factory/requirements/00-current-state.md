---
title: "Current State"
type: "overview"
id: "684cd621-f98b-4a1d-b0f3-915c4ed91088"
---

## Data Landscape

The current system processes the CMS Medicaid Provider Utilization and Payments dataset, which contains comprehensive fee-for-service claims, managed care encounters, and CHIP claims from January 2018 through December 2024. The raw dataset is approximately 11 GB in CSV format and expands to a 30 GB DuckDB analytical database after processing.

The dataset contains 227,083,361 billing records representing 18.8 billion individual claim transactions, totaling $1,093,562,833,513 in payments. It spans 617,503 unique billing providers, 10,881 HCPCS procedure codes, and 84 months of activity across all U.S. states and territories.

## Reference Data Sources

The system integrates multiple external reference datasets to validate and enrich provider information:

**NPPES National Provider Registry** (10+ GB) provides provider identities, names, specialties, locations, and entity types. This allows the system to distinguish between individual practitioners, organizations, government agencies, and billing intermediaries.

**HCPCS Procedure Code Reference** (2026 version) maps procedure codes to service descriptions, enabling detection of specialty mismatches and impossible service combinations.

**OIG List of Excluded Individuals/Entities (LEIE)** contains 8,302 providers who are barred from receiving federal healthcare payments. Cross-referencing against this list identifies providers who continue billing after exclusion.

**CMS Data Quality Atlas** provides state-level data quality measures that weight findings based on known reporting issues and submission completeness.

**Positive Control Cases** (when available) provide known fraud examples for validation and calibration of detection methods.

## Analytical Methods Currently Deployed

The existing pipeline implements a comprehensive analytical framework organized into 24 sequential processing milestones:

**Data Quality and Ingestion** (Milestones 0-2) validates CSV structure, loads data into DuckDB, creates indexes, builds provider and HCPCS summary tables, and enriches records with NPPES and LEIE cross-references.

**Exploratory Analysis and Hypothesis Generation** (Milestones 3-4) performs statistical profiling, generates 1,087 testable hypotheses across 10 analytical categories, and establishes peer group baselines for comparison.

**Hypothesis Testing** (Milestones 5-8, 12) executes statistical outlier tests (z-scores, IQR, Benford's Law), temporal anomaly detection (month-over-month spikes, sudden appearance/disappearance), peer comparisons (rate, volume, concentration), network analysis (hub-spoke, circular billing, ghost networks), machine learning models (Isolation Forest, Random Forest, XGBoost), domain-specific business rules (impossible volumes, upcoding, unbundling), and cross-reference validation (LEIE matching, specialty mismatches).

**Longitudinal and Multivariate Analysis** (Milestones 13-14) builds panel datasets, performs structural break detection, executes COVID-adjusted temporal analysis, and validates findings against holdout data (2023-2024).

**Data Quality Weighting and Financial Impact** (Milestones 9, 15) applies state-level quality weights from the CMS Data Quality Atlas, calculates standardized financial impact (excess above peer median, capped at total paid), and deduplicates findings across methods.

**Reporting and Prioritization** (Milestones 10-11, 16-22) generates 43+ visualization charts, produces the CMS Administrator Report, creates executive briefs and action plans, builds prioritized investigation queues (top 50/100/200/500), and classifies findings into 10 fraud pattern categories.

## Output Artifacts

The system produces a comprehensive set of analytical outputs organized in the `output/` directory:

**Executive Reports** include the full CMS Administrator Report, one-page executive brief with quality-weighted exposure totals, CEO action plan with 30-day priorities, and plain-language fraud pattern summaries.

**Investigation Queues** provide CSV files with top 100 and top 500 provider-level risk leads, top 100 and top 500 systemic risk findings (state/code combinations), and detailed priority lists (top 50/100/200) with provider names, NPIs, states, exposure amounts, and flagging methods.

**Fraud Pattern Analysis** delivers comprehensive technical analysis of 10 distinct patterns, independent audit review with critical and significant findings, and sector-specific deep dives (long-term care, nursing homes, personal care services).

**Visualizations** include 43 PNG charts showing monthly spending trends, fraud pattern heatmaps, Benford's Law analysis, Lorenz curves, network graphs, state heatmaps, temporal anomaly time series, and top 20 provider/procedure rankings. Interactive HTML heatmaps are also provided.

**Data Tables and Validation** contain hypothesis batch results, feasibility matrices, holdout validation summaries, calibration reports, data quality assessments, and data profile summaries.

## Technology Stack

The system is implemented entirely in Python 3, using DuckDB as the analytical database engine for high-performance aggregation and windowing functions over large datasets. Key libraries include pandas for data manipulation, NumPy for statistical calculations, scikit-learn for machine learning models (Isolation Forest, Random Forest), XGBoost for gradient boosting, Matplotlib and Seaborn for visualization, and NetworkX for graph analysis.

The pipeline architecture uses a sequential milestone execution model orchestrated by `scripts/run_all.py`, which runs 24 individual Python scripts in a defined order. Each milestone can also be executed independently for iterative development and debugging.

## Current Limitations

While the existing system is comprehensive, several limitations exist:

**No Real-Time Processing** - The pipeline operates in batch mode on a static CSV export. It cannot detect fraud as claims are submitted, only after data is aggregated and exported.

**Manual Intervention Required** - The system generates prioritized queues and reports, but investigators must manually review findings, gather documentation, and initiate enforcement actions. No automated case management integration exists.

**December 2024 Data Incompleteness** - Recent months may have incomplete submissions from some states, creating false positives for sudden-stop detection patterns.

**Positive Control Validation Incomplete** - The system includes infrastructure for validating detection methods against known fraud cases, but the positive control dataset has not been fully populated.

**Limited Explainability for ML Models** - Machine learning models (especially deep learning methods like autoencoders and transformers) produce anomaly scores but provide limited insight into why specific providers were flagged.

**State Quality Weighting Complexity** - The CMS Data Quality Atlas provides state-level quality measures, but applying these weights consistently across all detection methods remains challenging.

**Pattern Classification Overlap** - A single provider can appear in multiple fraud pattern categories, and the current deduplication logic may not accurately reflect total recoverable amounts.
