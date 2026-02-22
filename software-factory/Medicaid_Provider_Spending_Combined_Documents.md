# Medicaid Provider Spending - Requirements Documentation

## Table of Contents

### Overview Documents
- [Business Problem](#business-problem)
- [Current State](#current-state)
- [Product Description](#product-description)
- [Personas](#personas)
- [Success Metrics](#success-metrics)
- [Technical Requirements](#technical-requirements)

### Feature Requirements
- [Data Ingestion and Preparation](#data-ingestion-and-preparation)
  - [CSV Data Quality Validation](#csv-data-quality-validation)
  - [Claims Data Ingestion](#claims-data-ingestion)
  - [Reference Data Enrichment](#reference-data-enrichment)
- [Fraud Detection Execution](#fraud-detection-execution)
  - [Statistical Hypothesis Testing](#statistical-hypothesis-testing)
  - [Machine Learning Anomaly Detection](#machine-learning-anomaly-detection)
  - [Domain-Specific Business Rules](#domain-specific-business-rules)
  - [Cross-Reference and Composite Scoring](#cross-reference-and-composite-scoring)
- [Exploratory Analysis and Hypothesis Design](#exploratory-analysis-and-hypothesis-design)
  - [Exploratory Data Analysis](#exploratory-data-analysis)
  - [Hypothesis Generation](#hypothesis-generation)
  - [Hypothesis Feasibility Matrix](#hypothesis-feasibility-matrix)
- [Longitudinal and Panel Analysis](#longitudinal-and-panel-analysis)
  - [Longitudinal Panel Construction](#longitudinal-panel-construction)
  - [Multivariate Temporal Analysis](#multivariate-temporal-analysis)
- [Validation and Calibration](#validation-and-calibration)
  - [Holdout Validation and Calibration](#holdout-validation-and-calibration)
  - [Hypothesis Validation Summary](#hypothesis-validation-summary)
  - [Provider Validation Scores](#provider-validation-scores)
- [Impact Quantification and Risk Prioritization](#impact-quantification-and-risk-prioritization)
  - [State Quality Weighting](#state-quality-weighting)
  - [Financial Impact and Deduplication](#financial-impact-and-deduplication)
  - [Risk Queue Generation](#risk-queue-generation)
  - [Fraud Pattern Classification](#fraud-pattern-classification)
- [Reporting and Visualization](#reporting-and-visualization)
  - [Chart and Visualization Generation](#chart-and-visualization-generation)
  - [CMS Administrator Report](#cms-administrator-report)
  - [Executive Dashboard Cards](#executive-dashboard-cards)
  - [Hypothesis Cards](#hypothesis-cards)
  - [Executive Brief](#executive-brief)
  - [Merged Card Aggregation](#merged-card-aggregation)
  - [Action Plan and Priority Lists](#action-plan-and-priority-lists)
- [Pipeline Orchestration and Execution](#pipeline-orchestration-and-execution)
  - [Master Pipeline Orchestration](#master-pipeline-orchestration)
  - [Individual Milestone Execution](#individual-milestone-execution)
  - [Error Handling and Logging](#error-handling-and-logging)

---

# Overview Documents

## Business Problem

## The Problem

Medicaid and Medicare programs process over $1 trillion annually in provider payments, but identifying fraud, waste, and abuse within this massive dataset is extraordinarily difficult. Traditional manual review cannot scale to examine 227 million billing records across 617,503 providers. When fraud goes undetected, taxpayer dollars are lost, legitimate providers face unfair competition, and beneficiaries may receive substandard or unnecessary care.

Current approaches to fraud detection rely heavily on reactive investigation of tips and complaints, post-payment audits triggered after patterns are already established, and manual review of sampled claims. These methods miss systematic patterns, allow fraudulent actors to operate for extended periods before detection, and cannot identify subtle statistical anomalies across the full dataset.

## Who Experiences This Problem

This problem affects multiple stakeholders in the healthcare payment ecosystem:

**CMS Administrators and Federal Auditors** need to identify improper payments and prioritize enforcement actions but lack comprehensive visibility into spending patterns across all providers and codes. They must justify investigation priorities to oversight bodies and allocate limited enforcement resources effectively.

**State Medicaid Agencies** manage provider enrollment and payment integrity programs but struggle to detect cross-state billing schemes, identify rate design issues, and distinguish between policy problems and actual fraud. They need actionable intelligence to guide both enforcement and policy reforms.

**Fraud Investigators and OIG Teams** receive too many low-quality leads and spend significant time on dead ends. They need high-confidence, multi-signal findings backed by statistical evidence and cross-referenced against exclusion lists and provider registries.

**Legitimate Healthcare Providers** compete in a marketplace where fraudulent actors can submit inflated claims or bill for services never rendered, creating unfair competitive disadvantages and eroding trust in the payment system.

**Taxpayers and Beneficiaries** ultimately bear the financial burden of fraud, waste, and abuse through higher costs, and beneficiaries may receive unnecessary services or be steered toward fraudulent providers.

## Critical Gaps

Without a comprehensive fraud detection system, stakeholders face:

* **No systematic coverage**: Manual review can only examine a small fraction of claims, leaving most suspicious activity undetected
* **Delayed detection**: Fraudulent patterns may continue for months or years before triggering investigation
* **Limited pattern recognition**: Human analysts cannot identify subtle statistical anomalies or multi-dimensional correlations across millions of records
* **Lack of prioritization**: When everything looks suspicious, investigators cannot effectively allocate scarce resources
* **Policy vs. fraud confusion**: Systemic overpayment due to rate design is often conflated with provider-level fraud, wasting enforcement resources
* **Cross-state blindness**: Providers billing in multiple states or network schemes spanning geographies evade single-state review

## Impact of the Problem

The financial and operational impact is substantial:

* **$355 billion** in suspicious provider-level spending identified through the existing analysis
* **$116 billion** in systemic rate and policy anomalies that require policy intervention rather than enforcement
* Hundreds of providers billing in patterns that are statistically impossible (billing every day, billing after deactivation, implausible volumes)
* Investigation resources wasted on low-quality leads or policy issues misidentified as fraud
* Legitimate claims processing slowed by overly broad fraud prevention controls
* Public trust in Medicaid eroded by high-profile fraud cases that could have been detected earlier

## Current State

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

## Product Description

## What the System Does

The Medicaid Claims Fraud Detection Pipeline is a comprehensive analytical platform that processes billions of healthcare claims to identify fraud, waste, and abuse patterns across the Medicaid provider network. The system ingests CMS provider spending data, enriches it with reference datasets, applies statistical and machine learning methods to detect anomalies, and generates prioritized investigation queues with supporting evidence and visualizations.

Unlike traditional fraud detection systems that rely solely on business rules or post-payment audits, this platform combines multiple analytical approaches—statistical outlier detection, temporal pattern analysis, peer comparisons, network analysis, machine learning, and domain-specific business rules—to create a comprehensive risk assessment of every provider in the dataset.

The system processes over $1 trillion in payments across 227 million billing records, covering 617,503 providers and 10,881 procedure codes, to identify an estimated $355 billion in suspicious provider-level spending across 10 distinct fraud patterns, plus $116 billion in systemic rate and policy issues requiring separate policy interventions.

## Core Value Proposition

The system delivers value by transforming massive, unstructured claims data into actionable intelligence that enables stakeholders to:

**Prioritize Limited Enforcement Resources** - Investigators receive a ranked list of high-confidence leads, with the top 500 providers accounting for substantial exposure. 90% of top-tier findings trigger 3 or more independent detection methods, providing multiple lines of evidence for investigation.

**Distinguish Fraud from Policy Problems** - The system separates provider-level fraud signals from systemic rate design and authorization issues. Eleven of the top 20 flagged entities are government agencies, indicating policy problems rather than criminal fraud. This prevents wasted enforcement effort on cases that require policy reform instead.

**Detect Patterns Invisible to Manual Review** - Statistical methods identify providers billing every single day, billing after deactivation, billing in geographic impossibility patterns, and submitting volumes that exceed physical limits. Machine learning models surface subtle multi-dimensional anomalies that no human analyst could detect across millions of records.

**Validate Findings with Cross-Referenced Evidence** - Every finding is checked against the OIG exclusion list, NPPES provider registry, and state quality measures. Multi-signal providers flagged by independent methods provide stronger evidentiary basis for investigation.

**Quantify Financial Exposure** - Each finding includes a standardized financial impact estimate (excess above peer median, capped at total billed), enabling cost-benefit analysis of investigation priorities.

**Enable Evidence-Based Policy Reform** - By identifying systemic rate anomalies and authorization gaps, the system supports policy teams in redesigning payment structures to prevent waste at the source.

## User Environments and Access Patterns

The system operates as a **batch analytical pipeline** that runs on-demand or on a scheduled basis (e.g., monthly, quarterly) when new CMS data exports become available. Primary users include:

**CMS Administrators and Federal Auditors** access executive reports and summary dashboards to understand overall fraud exposure, track trends over time, and justify budget requests for enforcement programs. They consume high-level insights like the executive brief, action plan memo, and fraud pattern summaries.

**Fraud Investigators and OIG Teams** work directly with the prioritized investigation queues (top 50/100/200/500 provider lists) and drill into individual provider details, reviewing flagging methods, financial impact, peer comparisons, and temporal patterns. They use the detailed CSV queues and per-provider time series charts.

**State Medicaid Program Integrity Teams** focus on findings specific to their state, reviewing both provider-level fraud signals and systemic rate/policy issues. They cross-reference findings with their own case management systems and provider databases.

**Data Analysts and Researchers** explore the hypothesis validation reports, calibration summaries, and methodological documentation to understand detection method performance and refine analytical approaches for future runs.

**Policy and Program Design Teams** use the systemic findings (state-level rate anomalies, code concentration patterns, authorization gaps) to inform rate-setting, prior authorization rules, and provider enrollment controls.

## Integration Points

The system is designed to integrate with external systems through standardized data exchange:

**Input Data Integration** - Consumes the CMS Medicaid Provider Utilization and Payments dataset (CSV format, updated monthly or quarterly). Can incorporate NPPES registry updates, LEIE exclusion list updates, and state-specific positive control datasets.

**Output Data Exchange** - Produces investigation queues in CSV format that can be imported into case management systems, provider enrollment platforms, or auditing workflows. Report outputs (Markdown, HTML, PNG) can be published to internal portals or distributed via email.

**Potential Future Integrations** - The system could connect to real-time claims processing systems to flag high-risk providers during adjudication, integrate with case management platforms to track investigation outcomes, or feed findings into predictive models for prospective fraud prevention.

## Deployment Model

The current system is deployed as a **standalone Python application** that runs on a workstation or server with sufficient memory and storage (30+ GB for the DuckDB database, 8 GB+ for output artifacts). The master orchestrator script `scripts/run_all.py` executes all 24 milestones sequentially, typically completing in minutes to hours depending on hardware.

Output files are written to the `output/` directory and can be copied to network shares, uploaded to cloud storage, or committed to version control for distribution to stakeholders.

## Key Differentiators

**Comprehensive Multi-Method Approach** - Rather than relying on a single detection technique, the system tests over 1,000 hypotheses across 10 analytical categories and aggregates findings using composite scoring.

**Evidence-Based Prioritization** - Findings are ranked by quality-weighted financial impact, number of flagging methods, and cross-validation against known exclusion lists.

**Transparent Methodology** - Every hypothesis has a defined acceptance criterion, statistical threshold, and financial impact formula. The full hypothesis set is documented and reproducible.

**Calibration and Validation** - The system validates findings against holdout data (2023-2024) and tracks which methods remain stable over time. Unstable methods are pruned to improve signal quality.

**Policy-Aware Classification** - Fraud patterns are explicitly categorized to distinguish enforcement targets (impossible volumes, billing after deactivation) from policy issues (government agency outliers, rate design problems).

**Scalable Architecture** - DuckDB enables efficient processing of billions of claim transactions without requiring a distributed database or cloud infrastructure.

## Personas

## Primary User Personas

### CMS Administrator / Federal Auditor

**Role and Responsibilities**: Oversees Medicaid payment integrity programs at the federal level, allocates enforcement budgets, justifies investigation priorities to congressional oversight, and tracks fraud prevention outcomes.

**Goals**: Identify the highest-impact fraud patterns, quantify total improper payment exposure, demonstrate effective use of enforcement resources, and support policy reforms to prevent systemic waste.

**Pain Points**: Too many low-quality leads that don't result in recoveries, difficulty distinguishing fraud from policy problems, lack of cross-state visibility into billing networks, and pressure to show measurable results to justify program budgets.

**How They Use the System**: Reviews executive briefs and summary dashboards monthly or quarterly when new data is available. Focuses on total exposure figures, top 10/100 provider lists, and fraud pattern categories. Uses findings to brief leadership, allocate investigator assignments, and justify policy recommendations.

**Success Criteria**: Clear prioritization of investigation targets, evidence-based exposure estimates that align with recovery potential, and identification of systemic issues requiring policy intervention.

---

### Fraud Investigator / OIG Special Agent

**Role and Responsibilities**: Conducts field investigations of suspected fraud cases, gathers evidence, interviews providers, reviews medical records, and builds cases for civil or criminal prosecution.

**Goals**: Receive high-confidence leads with multiple lines of evidence, minimize time spent on dead ends, build prosecutable cases with statistical and documentary support, and maximize recovery amounts per investigation hour.

**Pain Points**: Receives too many alerts without context, wastes time investigating legitimate billing patterns or policy issues, lacks baseline peer comparisons to establish what is "normal," and struggles to explain complex statistical methods to juries or judges.

**How They Use the System**: Works directly from prioritized investigation queues (top 50/100/200 lists), reviews individual provider profiles including flagging methods and financial impact, compares provider behavior to peer baselines, and exports evidence packages (charts, peer comparisons, temporal patterns) for case files.

**Success Criteria**: High-quality leads that convert to recoveries or enforcement actions, clear documentation of statistical anomalies, and evidentiary support that can be explained to non-technical audiences.

---

### State Medicaid Program Integrity Director

**Role and Responsibilities**: Manages provider enrollment, payment integrity, and fraud prevention programs for a state Medicaid agency. Coordinates with federal partners, implements pre-payment and post-payment review processes, and recommends policy changes to state leadership.

**Goals**: Identify in-state fraud and abuse patterns, prioritize limited audit resources, justify provider enrollment denials or terminations, detect rate design issues, and implement cost-effective controls.

**Pain Points**: Limited visibility into cross-state billing schemes, difficulty separating legitimate high-volume providers from fraudulent actors, lack of benchmarking against other states, and pressure to balance fraud prevention with timely claims payment.

**How They Use the System**: Filters investigation queues by state, reviews both provider-level and systemic findings (rate anomalies, authorization gaps), cross-references findings with state provider databases, and uses peer comparisons to justify provider audits or rate changes.

**Success Criteria**: Actionable state-specific leads, clear identification of rate and policy problems, and evidence to support provider enrollment decisions or contract terminations.

---

### Data Analyst / Methodologist

**Role and Responsibilities**: Develops and refines fraud detection methods, validates analytical approaches, evaluates detection model performance, and improves hypothesis design for future pipeline runs.

**Goals**: Understand which detection methods are most effective, identify false positive patterns, calibrate models to balance sensitivity and specificity, and improve overall signal quality.

**Pain Points**: Limited feedback on whether flagged providers were actually fraudulent, difficulty assessing model performance without ground truth labels, and trade-offs between comprehensive coverage and false positive rates.

**How They Use the System**: Reviews hypothesis validation reports, calibration summaries, and holdout performance metrics. Analyzes which methods co-occur frequently, identifies unstable or low-performing methods, and proposes refinements to the hypothesis taxonomy.

**Success Criteria**: Clear metrics on detection method stability and cross-validation, identification of methods to prune or enhance, and reproducible methodology documentation.

---

### Policy and Program Design Lead

**Role and Responsibilities**: Designs Medicaid payment rates, authorization requirements, and program integrity controls. Recommends policy changes to CMS or state legislatures based on fraud and waste analysis.

**Goals**: Identify systemic payment design flaws, quantify waste due to authorization gaps, benchmark rates across states, and design preventive controls that stop fraud before claims are paid.

**Pain Points**: Fraud findings often conflate provider-level issues with systemic rate problems, difficulty quantifying the impact of policy changes, and lack of clear separation between enforcement-appropriate findings and policy-appropriate findings.

**How They Use the System**: Focuses on systemic findings (state rate anomalies, code concentration patterns, authorization gaps), reviews the $116 billion systemic exposure separate from provider-level fraud, and uses benchmarking data to justify rate reforms or prior authorization rules.

**Success Criteria**: Clear separation of policy vs. enforcement findings, quantified exposure attributable to rate design or authorization gaps, and benchmarking data to support policy proposals.

## Success Metrics

## Primary Success Metrics

### Detection Coverage and Completeness

**Total Records Analyzed** - The system shall process 100% of billing records in each CMS data export, with no sampling or exclusions. Current baseline: 227,083,361 records representing $1.09 trillion in payments.

**Provider Coverage** - The system shall analyze every billing provider NPI in the dataset, enriching with NPPES registry data where available. Current baseline: 617,503 unique billing providers.

**Hypothesis Execution Rate** - The system shall successfully execute all active hypotheses in the taxonomy, excluding only those flagged as unstable through validation testing. Current baseline: 1,087 hypotheses across 10 categories, with 4 methods pruned for instability.

### Investigation Prioritization Quality

**Multi-Signal Concentration** - At least 80% of the top 500 prioritized providers shall trigger 3 or more independent detection methods, indicating convergent evidence. Current baseline: 90% (450 of top 500).

**Financial Impact Ranking** - The top 100 prioritized providers shall account for at least 40% of the quality-weighted total exposure, demonstrating effective concentration of high-impact leads. Current baseline: 49.8% ($46.7B of $93.8B top-500 pool).

**High-Confidence Finding Rate** - At least 10,000 findings shall meet high-confidence criteria (3+ categories, known fraud pattern, or z-score &gt; 5). Current baseline: 10,913 high-confidence findings.

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

## Technical Requirements

## Data and Infrastructure Requirements

### Input Data Specifications

**Primary Dataset: CMS Medicaid Provider Utilization and Payments** - The system shall ingest a CSV file (approximately 11 GB) containing all fee-for-service claims, managed care encounters, and CHIP claims. Required fields: BILLING_PROVIDER_NPI_NUM, SERVICING_PROVIDER_NPI_NUM, HCPCS_CODE, CLAIM_FROM_MONTH, TOTAL_UNIQUE_BENEFICIARIES, TOTAL_CLAIMS, TOTAL_PAID.

**NPPES National Provider Registry** - The system shall load and index NPPES data (10+ GB) providing provider names, specialties, locations, entity types, and deactivation dates. This reference dataset enables provider identity validation and specialty mismatch detection.

**HCPCS Procedure Code Reference** - The system shall load HCPCS code descriptions (2026 or current year version) to enable human-readable reporting and domain-specific rule application (e.g., timed services, high-risk categories).

**OIG List of Excluded Individuals/Entities (LEIE)** - The system shall load the current LEIE dataset (approximately 8,302+ NPIs) to cross-reference findings and flag providers billing after exclusion.

**CMS Data Quality Atlas** - The system shall incorporate state-level data quality measures to weight findings based on known reporting completeness and accuracy issues.

**Positive Control Dataset** (optional but recommended) - The system should support loading known fraud cases (SAM exclusions, licensure revocations, confirmed settlements) for validation and calibration of detection methods.

### Storage and Database Requirements

**DuckDB Analytical Database** - The system shall use DuckDB as the analytical database engine, creating a database file (approximately 30 GB) with optimized indexes on billing_npi, hcpcs_code, and claim_month. DuckDB enables efficient SQL-based aggregation and windowing functions over billions of rows without distributed infrastructure.

**Output Directory Structure** - The system shall organize outputs in standardized directories: `output/analysis/` (reports and queues), `output/charts/` (PNG visualizations), `output/hypotheses/` (hypothesis batches and validation), `output/findings/` (scored findings by category, regenerable), `output/qa/` (data quality reports), `output/cards/` (dashboard card components).

**File Retention and Versioning** - Large generated datasets in `output/findings/` (8+ GB, regenerable) shall be excluded from version control. Reports, charts, and queues shall be retained for historical comparison.

### Compute and Performance Requirements

**Memory** - The system shall run on hardware with at least 16 GB of RAM to support in-memory aggregations and machine learning model training.

**Storage** - The system requires at least 100 GB of available storage for input data (11 GB CSV), DuckDB database (30 GB), NPPES registry (10 GB), output findings (8 GB), and output reports/charts/queues (5 GB).

**Execution Time** - The complete 24-milestone pipeline should complete in under 4 hours on standard server hardware (16+ GB RAM, SSD storage, multi-core CPU).

**Scalability** - DuckDB's columnar storage and vectorized execution enable processing of billions of claim transactions without requiring distributed computing infrastructure.

## Technology Stack Requirements

**Programming Language** - The system is implemented in Python 3.7+ and shall use standard Python libraries for compatibility and maintainability.

**Core Libraries**:

* **pandas** - Data manipulation and CSV ingestion
* **NumPy** - Statistical calculations and array operations
* **DuckDB** - Analytical database engine
* **scikit-learn** - Machine learning models (Isolation Forest, Random Forest, DBSCAN, K-Means, Local Outlier Factor)
* **XGBoost** - Gradient boosting for anomaly scoring
* **Matplotlib and Seaborn** - Visualization and chart generation
* **NetworkX** - Graph analysis for billing network detection

**Optional Libraries**:

* **TensorFlow or PyTorch** - Deep learning models (autoencoders, VAE, LSTM, transformers) if enabled
* **Plotly** - Interactive HTML visualizations

### Pipeline Architecture Requirements

**Sequential Milestone Execution** - The system shall execute 24 milestones in a defined order via the master orchestrator script `scripts/run_all.py`. Each milestone must complete successfully before the next begins.

**Individual Milestone Execution** - Each milestone script (e.g., `03_eda.py`, `10_generate_charts.py`) shall be executable independently for iterative development, debugging, and partial re-runs.

**Error Handling and Logging** - Each milestone shall log progress to console, report errors with context, and halt pipeline execution on failure. The orchestrator shall display a summary of PASS/FAIL status for each milestone.

**Idempotency** - Milestones that generate derived tables or output files shall drop and recreate outputs, enabling re-runs without manual cleanup.

## Integration Requirements

**Input Data Integration** - The system shall accept CMS data exports in CSV format placed in the project root directory. Future enhancements may support direct connection to CMS data APIs or cloud storage (S3, Azure Blob).

**Output Data Exchange** - Investigation queues shall be exported as CSV files compatible with standard case management systems. Reports shall be generated in Markdown and HTML formats for distribution. Visualizations shall be exported as PNG files suitable for presentation decks.

**Potential Future Integrations**:

* Real-time claims processing systems for prospective fraud flagging
* Case management platforms to track investigation outcomes and recoveries
* Provider enrollment systems to automate suspension or termination workflows
* Data warehouses or business intelligence platforms for trend analysis

**API and Programmatic Access** (future consideration) - The system may expose findings via REST API or SQL views for integration with external dashboards and reporting tools.

## Security and Compliance Requirements

**Data Privacy** - The system processes aggregate provider-level data and does not contain individually identifiable beneficiary health information (PHI). However, provider NPIs and payment amounts are sensitive and shall be protected according to organizational data handling policies.

**Access Controls** - The system shall run in a controlled environment with appropriate file system permissions. Output reports containing provider identities and exposure estimates shall be shared only with authorized investigators and administrators.

**Audit Trail** - Each pipeline run shall log execution timestamps, data volume processed, and output file locations to support reproducibility and compliance reporting.

**Data Retention** - Input datasets and outputs shall be retained according to organizational records retention policies (typically 7 years for federal healthcare programs).

## Quality and Validation Requirements

**Data Quality Checks** - Milestone 0 (CSV Data Quality Scan) shall validate input data structure, detect missing required fields, identify negative or zero paid amounts, and report null values in critical fields.

**Reference Data Freshness** - The system shall document the version and effective date of all reference datasets (NPPES, HCPCS, LEIE) to ensure findings are cross-referenced against current exclusion lists and provider registries.

**Hypothesis Reproducibility** - All hypotheses shall have documented acceptance criteria, statistical thresholds, and financial impact formulas. The full hypothesis taxonomy shall be exported to `output/hypotheses/all_hypotheses.json` for transparency and reproducibility.

**Validation and Calibration** - Milestone 14 shall validate findings against holdout data (2023-2024) and report holdout persistence rates per method. Unstable methods with negative z-delta shall be flagged for pruning.

**Cross-Reference Validation** - All findings shall be checked against the LEIE exclusion list, NPPES registry, and state quality measures to provide cross-validation and evidence strength.

## Extensibility and Customization Requirements

**Hypothesis Taxonomy Extensibility** - The system shall support adding new hypotheses without modifying core pipeline code. New hypotheses can be defined in JSON configuration files or Python modules.

**Configurable Thresholds** - Statistical thresholds (z-score cutoffs, IQR multipliers, confidence tier boundaries) should be configurable via parameters or configuration files rather than hard-coded.

**Custom Fraud Pattern Definitions** - The fraud pattern classification logic (10 patterns) should be defined in a structured way that allows customization for different jurisdictions or program types (Medicare, CHIP, state-specific programs).

**Pluggable Detection Methods** - The system architecture should support adding new machine learning models, statistical tests, or domain rules as separate modules without requiring changes to the orchestrator or reporting logic.

# Feature Requirements

## Data Ingestion and Preparation

## Overview

Provide a clear and concise summary of the feature, explaining what it does and the value it delivers to the user. Describe the core problem this feature solves and how it fits into the overall product.

## Terminology

* **Key Term 1**: Brief description that ensures shared understanding across the team.
* **Key Term 2**: Definition that clarifies any ambiguity in how this concept is used.

## Requirements

### REQ-XXX-001: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-001.1:** When the user \[performs action\], the system shall \[respond with specific behavior\].
* **AC-XXX-001.2:** When \[condition exists\], the system shall \[handle appropriately\].
* **AC-XXX-001.N:** \[Continue for all acceptance criteria\]

### REQ-XXX-002: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-002.1:** When \[condition\], the system shall \[behavior\].
* **AC-XXX-002.2:** \[Continue for all acceptance criteria\]

## Feature Behavior & Rules

This section clarifies how the requirements behave in practice and how they interact. It explains cross-requirement interactions, defaults, constraints, and edge conditions without prescribing UI or user flows.

### CSV Data Quality Validation

## Overview

Before any fraud detection analysis can begin, the system must validate the incoming CMS Medicaid Provider Utilization and Payments dataset to ensure data quality and structural integrity. This feature scans the raw CSV file row-by-row to identify formatting issues, missing required fields, invalid data types, and data anomalies that would compromise downstream analysis. By catching data quality problems early, the system prevents ingestion of corrupted records and provides clear visibility into dataset completeness and coverage.

This validation step runs as Milestone 0 and is critical for establishing trust in subsequent analytical findings. The feature outputs a comprehensive data quality report and a list of invalid rows for manual review and correction.

## Terminology

* **Invalid Row**: A billing record that fails one or more validation rules, such as missing required fields, incorrect data types, or values outside acceptable ranges.
* **Data Quality Report**: A JSON summary document containing validation statistics, month coverage, total volumes, and identified anomalies.
* **Column Count**: The expected number of fields in each CSV row (7 fields: billing NPI, servicing NPI, HCPCS code, claim month, beneficiaries, claims, paid).
* **NPI (National Provider Identifier)**: A 10-digit numeric identifier assigned to healthcare providers in the United States.
* **HCPCS Code**: Healthcare Common Procedure Coding System code that identifies the medical service or procedure billed.
* **Claim Month**: The month in which services were provided, formatted as YYYY-MM.

## Requirements

### REQ-CSVDQ-001: CSV File Existence Check

**User Story:** As a data analyst, I want the system to verify that the input CSV file exists before attempting validation, so that I receive a clear error message if the file is missing.

**Acceptance Criteria:**

* **AC-CSVDQ-001.1:** When the CSV file does not exist at the expected path, the system shall exit with an error message indicating the expected file location.
* **AC-CSVDQ-001.2:** When the CSV file exists, the system shall proceed to open and scan the file.
* **AC-CSVDQ-001.3:** When the CSV file appears to be empty (no header row), the system shall exit with an error message.

### REQ-CSVDQ-002: Structural Validation

**User Story:** As a data quality engineer, I want the system to validate the structure of each CSV row, so that I can identify records with incorrect column counts or malformed data before ingestion.

**Acceptance Criteria:**

* **AC-CSVDQ-002.1:** When a row contains fewer or more than 7 columns, the system shall flag it as invalid with reason "column_count".
* **AC-CSVDQ-002.2:** When a row contains exactly 7 columns, the system shall proceed to field-level validation.
* **AC-CSVDQ-002.3:** When the total invalid row count exceeds the configured maximum (default 5,000), the system shall stop writing additional invalid rows to the output CSV but shall continue scanning.

### REQ-CSVDQ-003: Billing NPI Validation

**User Story:** As a data quality engineer, I want the system to validate billing provider NPIs, so that I can ensure all providers have properly formatted identifiers.

**Acceptance Criteria:**

* **AC-CSVDQ-003.1:** When the billing_npi field is empty, the system shall flag the row as invalid with reason "billing_npi".
* **AC-CSVDQ-003.2:** When the billing_npi field contains non-numeric characters, the system shall flag the row as invalid with reason "billing_npi".
* **AC-CSVDQ-003.3:** When the billing_npi field does not contain exactly 10 digits, the system shall flag the row as invalid with reason "billing_npi".

### REQ-CSVDQ-004: Servicing NPI Validation

**User Story:** As a data quality engineer, I want the system to validate servicing provider NPIs when present, so that I can identify malformed servicing NPIs.

**Acceptance Criteria:**

* **AC-CSVDQ-004.1:** When the servicing_npi field is empty, the system shall not flag an error (servicing NPI is optional).
* **AC-CSVDQ-004.2:** When the servicing_npi field is present and contains non-numeric characters, the system shall flag the row as invalid with reason "servicing_npi".
* **AC-CSVDQ-004.3:** When the servicing_npi field is present and does not contain exactly 10 digits, the system shall flag the row as invalid with reason "servicing_npi".

### REQ-CSVDQ-005: HCPCS Code Validation

**User Story:** As a data quality engineer, I want the system to validate that every row contains an HCPCS code, so that I can ensure all billing records have an associated procedure code.

**Acceptance Criteria:**

* **AC-CSVDQ-005.1:** When the hcpcs_code field is empty, the system shall flag the row as invalid with reason "hcpcs".
* **AC-CSVDQ-005.2:** When the hcpcs_code field is present, the system shall accept it (format validation is not performed at this stage).

### REQ-CSVDQ-006: Claim Month Validation

**User Story:** As a data quality engineer, I want the system to validate claim month formatting and values, so that I can ensure temporal data is consistent and analyzable.

**Acceptance Criteria:**

* **AC-CSVDQ-006.1:** When the claim_month field does not match the pattern YYYY-MM, the system shall flag the row as invalid with reason "claim_month".
* **AC-CSVDQ-006.2:** When the month value is less than 01 or greater than 12, the system shall flag the row as invalid with reason "claim_month".
* **AC-CSVDQ-006.3:** When the claim_month is valid, the system shall track it for coverage analysis (min month, max month, month counts).

### REQ-CSVDQ-007: Beneficiary Count Validation

**User Story:** As a data quality engineer, I want the system to validate beneficiary counts, so that I can identify records with invalid or negative patient counts.

**Acceptance Criteria:**

* **AC-CSVDQ-007.1:** When the beneficiaries field cannot be converted to an integer, the system shall flag the row as invalid with reason "beneficiaries".
* **AC-CSVDQ-007.2:** When the beneficiaries field is negative, the system shall flag the row as invalid with reason "beneficiaries".
* **AC-CSVDQ-007.3:** When the beneficiaries field is zero but the claims field is positive, the system shall increment the "zero_beneficiaries_positive_claims" counter.

### REQ-CSVDQ-008: Claims Count Validation

**User Story:** As a data quality engineer, I want the system to validate claims counts, so that I can identify records with invalid or negative claim counts.

**Acceptance Criteria:**

* **AC-CSVDQ-008.1:** When the claims field cannot be converted to an integer, the system shall flag the row as invalid with reason "claims".
* **AC-CSVDQ-008.2:** When the claims field is negative, the system shall flag the row as invalid with reason "claims".

### REQ-CSVDQ-009: Paid Amount Validation

**User Story:** As a data quality engineer, I want the system to validate paid amounts, so that I can identify records with invalid or suspicious payment values.

**Acceptance Criteria:**

* **AC-CSVDQ-009.1:** When the paid field cannot be converted to a float, the system shall flag the row as invalid with reason "paid".
* **AC-CSVDQ-009.2:** When the paid field is negative, the system shall increment the "negative_paid" counter (but shall not flag the row as invalid, as negative adjustments are legitimate).

### REQ-CSVDQ-010: Invalid Row Recording

**User Story:** As a data quality engineer, I want the system to write invalid rows to a separate CSV file, so that I can manually review and correct data quality issues.

**Acceptance Criteria:**

* **AC-CSVDQ-010.1:** When a row is flagged as invalid, the system shall write a record to `output/qa/invalid_rows.csv` containing the row number, all validation failure reasons (semicolon-delimited), and the raw row data (pipe-delimited).
* **AC-CSVDQ-010.2:** When the invalid row count exceeds the configured maximum (default 5,000), the system shall stop writing additional rows to the invalid rows CSV.
* **AC-CSVDQ-010.3:** When a row is valid, the system shall not write it to the invalid rows CSV.

### REQ-CSVDQ-011: Data Quality Report Generation

**User Story:** As a data quality engineer, I want the system to generate a comprehensive data quality report in JSON format, so that I can review validation statistics and dataset coverage.

**Acceptance Criteria:**

* **AC-CSVDQ-011.1:** When the scan completes, the system shall write a JSON report to `output/qa/data_quality_report.json`.
* **AC-CSVDQ-011.2:** The report shall include: csv_path, total_rows_scanned, valid_rows, invalid_rows, invalid_breakdown (by reason), negative_paid_rows, zero_beneficiaries_positive_claims, min_month, max_month, month_coverage_count, month_counts (dictionary), month_paid (dictionary), and generated_at timestamp.
* **AC-CSVDQ-011.3:** The invalid_breakdown field shall contain counts for each validation failure type: invalid_column_count, invalid_npi, invalid_servicing_npi, invalid_hcpcs, invalid_month, invalid_beneficiaries, invalid_claims, invalid_paid.

### REQ-CSVDQ-012: Progress Reporting

**User Story:** As a data analyst, I want the system to display progress updates during scanning, so that I can monitor execution status for large datasets.

**Acceptance Criteria:**

* **AC-CSVDQ-012.1:** When the system has scanned 5 million rows, it shall print a progress message showing rows scanned and elapsed time.
* **AC-CSVDQ-012.2:** When the system has scanned each subsequent 5 million rows, it shall print an updated progress message.
* **AC-CSVDQ-012.3:** When the scan completes, the system shall print a summary message showing the output file location and total elapsed time.

### REQ-CSVDQ-013: Configurable Scan Limits

**User Story:** As a developer, I want to limit the number of rows scanned during testing, so that I can validate the feature quickly without processing the entire dataset.

**Acceptance Criteria:**

* **AC-CSVDQ-013.1:** When the `--max-rows` argument is provided, the system shall stop scanning after processing that many rows.
* **AC-CSVDQ-013.2:** When the `--max-rows` argument is not provided, the system shall scan all rows in the CSV.
* **AC-CSVDQ-013.3:** When the `--max-errors` argument is provided, the system shall limit invalid row output to that number (default: 5,000).

## Feature Behavior & Rules

The validation logic processes the CSV in a single streaming pass, maintaining minimal memory overhead regardless of dataset size. The system distinguishes between structural errors (which prevent ingestion) and data anomalies (which are flagged for review but may be legitimate).

Negative paid amounts are counted but not flagged as invalid, as they represent legitimate claim adjustments or reversals. However, beneficiary counts of zero with positive claim counts are flagged as suspicious.

Month coverage analysis tracks the temporal span of the dataset, enabling downstream features to verify expected data completeness (e.g., 84 months for January 2018 through December 2024).

The system uses regular expressions for month format validation and explicit type conversion for numeric fields to provide clear error categorization. Multiple validation failures on a single row are recorded with all applicable failure reasons concatenated.

### Claims Data Ingestion

## Overview

After the CSV data quality validation passes, the system must load the validated claims data into a high-performance analytical database and create optimized summary tables that enable efficient fraud detection analysis. This feature ingests approximately 227 million billing records from the CMS CSV file into DuckDB, creates indexes for query performance, builds five pre-aggregated summary tables that power downstream analytical queries, and exports a compressed Parquet file for backup and external analysis.

This ingestion step runs as Milestone 1 and transforms the flat CSV structure into a relational database schema optimized for aggregation queries, temporal analysis, network detection, and peer comparisons. The feature enables all subsequent fraud detection methods by providing fast access to provider-level, code-level, and monthly aggregations.

## Terminology

* **Claims Table**: The primary fact table containing one row per billing_npi + servicing_npi + hcpcs_code + claim_month combination, representing aggregated billing activity for that combination.
* **Provider Summary**: A pre-aggregated table containing one row per provider with lifetime statistics (total codes, months active, beneficiaries, claims, paid amounts).
* **HCPCS Summary**: A pre-aggregated table containing one row per procedure code with cross-provider statistics (number of providers, median rates, percentile distributions).
* **Provider Monthly**: A time-series table containing one row per provider per month, enabling temporal anomaly detection.
* **Provider HCPCS**: A provider-code combination table showing which providers bill which codes and at what volumes and rates.
* **Billing Servicing Network**: An edge table representing relationships between billing providers and servicing providers, used for network fraud detection.

## Requirements

### REQ-CLMING-001: Database Connection and Configuration

**User Story:** As a data engineer, I want the system to establish a properly configured DuckDB connection, so that ingestion can leverage available system resources efficiently.

**Acceptance Criteria:**

* **AC-CLMING-001.1:** When the ingestion process starts, the system shall connect to the DuckDB database file at the project root.
* **AC-CLMING-001.2:** When the connection is established, the system shall configure the thread count to 16 for parallel processing.
* **AC-CLMING-001.3:** When the connection is established, the system shall set the memory limit to 96GB to handle large aggregations.

### REQ-CLMING-002: CSV File Validation

**User Story:** As a data engineer, I want the system to verify CSV file existence before attempting ingestion, so that I receive clear error messages if the file is missing.

**Acceptance Criteria:**

* **AC-CLMING-002.1:** When the CSV file does not exist at the expected path, the system shall exit with an error message.
* **AC-CLMING-002.2:** When the CSV file exists, the system shall proceed to ingest the data.

### REQ-CLMING-003: Claims Table Creation

**User Story:** As a data analyst, I want the system to load all valid CSV rows into a structured claims table, so that I can query billing data efficiently using SQL.

**Acceptance Criteria:**

* **AC-CLMING-003.1:** When creating the claims table, the system shall drop any existing claims table.
* **AC-CLMING-003.2:** When ingesting CSV data, the system shall cast billing_provider_npi_num to VARCHAR as billing_npi.
* **AC-CLMING-003.3:** When ingesting CSV data, the system shall cast servicing_provider_npi_num to VARCHAR as servicing_npi.
* **AC-CLMING-003.4:** When ingesting CSV data, the system shall cast hcpcs_code to VARCHAR.
* **AC-CLMING-003.5:** When ingesting CSV data, the system shall cast claim_from_month to VARCHAR as claim_month.
* **AC-CLMING-003.6:** When ingesting CSV data, the system shall cast total_unique_beneficiaries to INTEGER as beneficiaries.
* **AC-CLMING-003.7:** When ingesting CSV data, the system shall cast total_claims to INTEGER as claims.
* **AC-CLMING-003.8:** When ingesting CSV data, the system shall cast total_paid to DOUBLE as paid.
* **AC-CLMING-003.9:** When ingestion completes, the system shall report the total row count ingested.
* **AC-CLMING-003.10:** When ingestion completes, the system shall report the total paid amount across all claims.
* **AC-CLMING-003.11:** When ingestion completes, the system shall count and report the number of rows with negative paid amounts.
* **AC-CLMING-003.12:** When ingestion completes, the system shall count and report the number of rows with zero paid amounts.

### REQ-CLMING-004: Index Creation

**User Story:** As a database administrator, I want the system to create indexes on frequently queried columns, so that downstream analytical queries execute efficiently.

**Acceptance Criteria:**

* **AC-CLMING-004.1:** When indexes are created, the system shall create an index on claims(billing_npi).
* **AC-CLMING-004.2:** When indexes are created, the system shall create an index on claims(hcpcs_code).
* **AC-CLMING-004.3:** When indexes are created, the system shall create an index on claims(claim_month).
* **AC-CLMING-004.4:** When index creation completes, the system shall confirm all indexes were created successfully.

### REQ-CLMING-005: Provider Summary Table Creation

**User Story:** As a fraud analyst, I want the system to pre-aggregate provider-level statistics, so that I can quickly analyze provider behavior without joining back to the claims table.

**Acceptance Criteria:**

* **AC-CLMING-005.1:** When creating provider_summary, the system shall drop any existing provider_summary table.
* **AC-CLMING-005.2:** When aggregating provider data, the system shall group by billing_npi.
* **AC-CLMING-005.3:** When aggregating provider data, the system shall calculate the count of distinct hcpcs_code as num_codes.
* **AC-CLMING-005.4:** When aggregating provider data, the system shall calculate the count of distinct claim_month as num_months.
* **AC-CLMING-005.5:** When aggregating provider data, the system shall calculate the sum of beneficiaries as total_beneficiaries.
* **AC-CLMING-005.6:** When aggregating provider data, the system shall calculate the sum of claims as total_claims.
* **AC-CLMING-005.7:** When aggregating provider data, the system shall calculate the sum of paid as total_paid.
* **AC-CLMING-005.8:** When aggregating provider data, the system shall calculate avg_paid_per_claim as total_paid divided by total_claims (handling division by zero).
* **AC-CLMING-005.9:** When aggregating provider data, the system shall calculate avg_claims_per_bene as total_claims divided by total_beneficiaries (handling division by zero).
* **AC-CLMING-005.10:** When aggregating provider data, the system shall calculate first_month as the minimum claim_month.
* **AC-CLMING-005.11:** When aggregating provider data, the system shall calculate last_month as the maximum claim_month.
* **AC-CLMING-005.12:** When provider_summary creation completes, the system shall report the count of unique providers.

### REQ-CLMING-006: HCPCS Summary Table Creation

**User Story:** As a fraud analyst, I want the system to pre-aggregate code-level statistics including percentile distributions, so that I can identify outlier billing rates for each procedure code.

**Acceptance Criteria:**

* **AC-CLMING-006.1:** When creating hcpcs_summary, the system shall drop any existing hcpcs_summary table.
* **AC-CLMING-006.2:** When aggregating code data, the system shall group by hcpcs_code.
* **AC-CLMING-006.3:** When aggregating code data, the system shall calculate the count of distinct billing_npi as num_providers.
* **AC-CLMING-006.4:** When aggregating code data, the system shall calculate sum of beneficiaries, claims, and paid.
* **AC-CLMING-006.5:** When aggregating code data, the system shall calculate avg_paid_per_claim.
* **AC-CLMING-006.6:** When aggregating code data, the system shall calculate std_paid_per_claim (standard deviation).
* **AC-CLMING-006.7:** When aggregating code data, the system shall calculate median_paid_per_claim (50th percentile).
* **AC-CLMING-006.8:** When aggregating code data, the system shall calculate p95_paid_per_claim (95th percentile).
* **AC-CLMING-006.9:** When aggregating code data, the system shall filter to rows where claims &gt; 0.
* **AC-CLMING-006.10:** When hcpcs_summary creation completes, the system shall report the count of unique HCPCS codes.

### REQ-CLMING-007: Provider Monthly Table Creation

**User Story:** As a fraud analyst, I want the system to create a provider-month time series table, so that I can detect temporal anomalies and billing spikes.

**Acceptance Criteria:**

* **AC-CLMING-007.1:** When creating provider_monthly, the system shall drop any existing provider_monthly table.
* **AC-CLMING-007.2:** When aggregating monthly data, the system shall group by billing_npi and claim_month.
* **AC-CLMING-007.3:** When aggregating monthly data, the system shall calculate sum of beneficiaries, claims, and paid.
* **AC-CLMING-007.4:** When aggregating monthly data, the system shall calculate the count of distinct hcpcs_code as num_codes.
* **AC-CLMING-007.5:** When provider_monthly creation completes, the system shall report the row count.

### REQ-CLMING-008: Provider HCPCS Table Creation

**User Story:** As a fraud analyst, I want the system to create a provider-code combination table, so that I can analyze code concentration and specialty mismatches.

**Acceptance Criteria:**

* **AC-CLMING-008.1:** When creating provider_hcpcs, the system shall drop any existing provider_hcpcs table.
* **AC-CLMING-008.2:** When aggregating provider-code data, the system shall group by billing_npi and hcpcs_code.
* **AC-CLMING-008.3:** When aggregating provider-code data, the system shall calculate sum of beneficiaries, claims, and paid.
* **AC-CLMING-008.4:** When aggregating provider-code data, the system shall calculate paid_per_claim.
* **AC-CLMING-008.5:** When aggregating provider-code data, the system shall calculate claims_per_bene.
* **AC-CLMING-008.6:** When aggregating provider-code data, the system shall calculate count of distinct claim_month as months_active.
* **AC-CLMING-008.7:** When aggregating provider-code data, the system shall filter to rows where claims &gt; 0.
* **AC-CLMING-008.8:** When provider_hcpcs creation completes, the system shall report the row count.

### REQ-CLMING-009: Billing Servicing Network Table Creation

**User Story:** As a network analyst, I want the system to create an edge table representing billing-to-servicing relationships, so that I can detect circular billing and hub-spoke fraud networks.

**Acceptance Criteria:**

* **AC-CLMING-009.1:** When creating billing_servicing_network, the system shall drop any existing billing_servicing_network table.
* **AC-CLMING-009.2:** When aggregating network data, the system shall group by billing_npi and servicing_npi.
* **AC-CLMING-009.3:** When aggregating network data, the system shall calculate count of distinct hcpcs_code as shared_codes.
* **AC-CLMING-009.4:** When aggregating network data, the system shall calculate count of distinct claim_month as shared_months.
* **AC-CLMING-009.5:** When aggregating network data, the system shall calculate sum of paid as total_paid.
* **AC-CLMING-009.6:** When aggregating network data, the system shall calculate sum of claims as total_claims.
* **AC-CLMING-009.7:** When aggregating network data, the system shall filter to rows where servicing_npi is not null and not empty.
* **AC-CLMING-009.8:** When billing_servicing_network creation completes, the system shall report the edge count.

### REQ-CLMING-010: Parquet Export

**User Story:** As a data scientist, I want the system to export the claims table to Parquet format, so that I can load the data into external analytical tools.

**Acceptance Criteria:**

* **AC-CLMING-010.1:** When exporting to Parquet, the system shall write the claims table to a file named claims.parquet in the project root.
* **AC-CLMING-010.2:** When exporting to Parquet, the system shall use ZSTD compression to minimize file size.
* **AC-CLMING-010.3:** When the export completes, the system shall confirm successful Parquet creation.

### REQ-CLMING-011: Ingestion Report Generation

**User Story:** As a data engineer, I want the system to generate an ingestion summary report in JSON format, so that I can verify ingestion completeness and track data quality metrics.

**Acceptance Criteria:**

* **AC-CLMING-011.1:** When ingestion completes, the system shall write a JSON report to `output/qa/ingest_report.json`.
* **AC-CLMING-011.2:** The report shall include row_count, total_paid, negative_paid_rows, zero_paid_rows, null_claim_month_rows, and generated_at timestamp.
* **AC-CLMING-011.3:** When the report is written, the system shall confirm the output file location.

### REQ-CLMING-012: Table Verification

**User Story:** As a database administrator, I want the system to verify that all expected tables were created, so that I can confirm the ingestion process completed successfully.

**Acceptance Criteria:**

* **AC-CLMING-012.1:** When ingestion completes, the system shall query the list of all tables in the database.
* **AC-CLMING-012.2:** When ingestion completes, the system shall display the list of table names.
* **AC-CLMING-012.3:** When ingestion completes, the system shall report total execution time in seconds and minutes.

## Feature Behavior & Rules

The ingestion process leverages DuckDB's columnar storage and vectorized execution to efficiently process 11+ GB of CSV data. The system uses the `read_csv_auto` function with explicit column type casting to ensure data integrity and consistent type handling.

All summary tables are created using `CREATE TABLE AS SELECT` statements with aggregation functions, ensuring atomic creation and avoiding intermediate steps. The `NULLIF` function is used throughout to handle division by zero scenarios gracefully, returning NULL rather than causing errors.

The provider_summary, hcpcs_summary, and provider_hcpcs tables filter to rows where claims &gt; 0 to exclude zero-activity records from statistical calculations, while the raw claims table retains all records including zeros.

Indexes are created after data loading to avoid index maintenance overhead during the initial bulk insert. DuckDB automatically optimizes index creation using parallel threads.

The billing_servicing_network table provides the foundation for network analysis by capturing the relationships between billing NPIs and servicing NPIs, enabling detection of hub-spoke networks, circular billing, and shared servicing arrangements.

### Reference Data Enrichment

## Overview

After claims data is ingested, the system must enrich billing records with provider identity information, procedure code descriptions, and exclusion list cross-references that enable fraud detection methods to identify provider names, specialties, deactivated status, and excluded individuals. This feature downloads the NPPES National Provider Registry (10+ GB), loads HCPCS procedure code descriptions, and retrieves the OIG List of Excluded Individuals/Entities (LEIE), creating enrichment tables that are joined to claims data throughout the analytical pipeline.

This enrichment step runs as Milestone 2 and transforms anonymous NPI numbers into provider profiles with names, specialties, addresses, and deactivation dates, enabling human-readable reporting and cross-reference fraud detection methods.

## Terminology

* **NPPES (National Plan and Provider Enumeration System)**: The CMS registry containing all healthcare provider NPIs with names, addresses, specialties, entity types, and deactivation dates.
* **Taxonomy Code**: A 10-character code from the Healthcare Provider Taxonomy that classifies provider specialties (e.g., 207R00000X = Internal Medicine).
* **LEIE (List of Excluded Individuals/Entities)**: The OIG database of providers barred from receiving federal healthcare payments due to fraud, abuse, or license revocations.
* **Deactivation Date**: The date when an NPI was deactivated in NPPES, after which the provider should not bill Medicaid.
* **Entity Type**: A classification indicating whether an NPI represents an individual (Type 1) or an organization (Type 2).
* **HCPCS (Healthcare Common Procedure Coding System)**: The coding system used to identify medical services, procedures, and supplies billed to Medicare/Medicaid.

## Requirements

### REQ-REFENR-001: NPPES Download and Selection

**User Story:** As a data engineer, I want the system to download the NPPES provider registry automatically, so that I can enrich provider data without manual file handling.

**Acceptance Criteria:**

* **AC-REFENR-001.1:** When NPPES download begins, the system shall check for existing NPPES CSV files in the `reference_data/nppes/` directory.
* **AC-REFENR-001.2:** When an existing NPPES CSV file is found (matching pattern `npidata_pfile_*.csv`), the system shall use the existing file rather than re-downloading.
* **AC-REFENR-001.3:** When no existing NPPES CSV is found, the system shall check for local ZIP files matching pattern `NPPES_Data_Dissemination_*.zip`.
* **AC-REFENR-001.4:** When a local ZIP file is found, the system shall extract the CSV from the ZIP.
* **AC-REFENR-001.5:** When no local files are found, the system shall attempt to download from `https://download.cms.gov/nppes/NPPES_Data_Dissemination_{month_year}.zip` for the current month.
* **AC-REFENR-001.6:** When the current month download fails, the system shall retry with each of the previous 5 months until successful.
* **AC-REFENR-001.7:** When a ZIP is downloaded successfully, the system shall extract the `npidata_pfile_*.csv` file to the NPPES directory.
* **AC-REFENR-001.8:** When all download attempts fail, the system shall fall back to loading from the NPPES API for top providers.

### REQ-REFENR-002: NPPES CSV Loading and Filtering

**User Story:** As a data analyst, I want the system to load NPPES data efficiently by filtering to only NPIs present in claims data, so that the providers table remains manageable in size.

**Acceptance Criteria:**

* **AC-REFENR-002.1:** When loading NPPES from CSV, the system shall create a temp table `claim_npis` containing all distinct billing and servicing NPIs from the claims table.
* **AC-REFENR-002.2:** When loading NPPES from CSV, the system shall use DuckDB's `read_csv_auto` with `ignore_errors=true` to handle malformed rows.
* **AC-REFENR-002.3:** When loading NPPES from CSV, the system shall use `all_varchar=true` and `null_padding=true` to handle inconsistent column types.
* **AC-REFENR-002.4:** When loading NPPES from CSV, the system shall perform an INNER JOIN between NPPES data and `claim_npis` to load only relevant providers.
* **AC-REFENR-002.5:** When loading NPPES data, the system shall extract NPI, Entity Type Code, Provider Organization Name, Provider Last Name, Provider First Name, NPI Deactivation Date, NPI Reactivation Date, NPI Deactivation Reason Code, State, City, Address Line 1, Address Line 2, Zip Code, Mailing Address fields, and Taxonomy Code.
* **AC-REFENR-002.6:** When loading NPPES data, the system shall construct a provider name from either the organization name (for entity type 2) or last name + first name (for individuals).
* **AC-REFENR-002.7:** When loading NPPES data, the system shall concatenate address line 1 and line 2 into a single address field.
* **AC-REFENR-002.8:** When loading completes, the system shall report the count of providers loaded.

### REQ-REFENR-003: NPPES API Fallback Loading

**User Story:** As a data engineer, I want the system to fall back to the NPPES API when bulk file download fails, so that the pipeline can complete even without the full NPPES file.

**Acceptance Criteria:**

* **AC-REFENR-003.1:** When NPPES bulk file loading fails, the system shall query the top 10,000 providers by total_paid from provider_summary.
* **AC-REFENR-003.2:** When calling the NPPES API, the system shall use the endpoint `https://npiregistry.cms.hhs.gov/api/?number={npi}&version=2.1`.
* **AC-REFENR-003.3:** When calling the NPPES API, the system shall batch requests in groups of 100 with a 10-second timeout per request.
* **AC-REFENR-003.4:** When an API request succeeds, the system shall parse the JSON response and extract basic provider information, enumeration type, addresses, and taxonomy code.
* **AC-REFENR-003.5:** When an API request fails or times out, the system shall continue to the next NPI without halting the pipeline.
* **AC-REFENR-003.6:** When API loading processes every 1,000 NPIs, the system shall print a progress message.
* **AC-REFENR-003.7:** When API loading completes, the system shall report the count of providers successfully loaded.

### REQ-REFENR-004: Providers Table Creation

**User Story:** As a fraud analyst, I want the system to create a structured providers table with consistent schema, so that I can join provider metadata to claims findings.

**Acceptance Criteria:**

* **AC-REFENR-004.1:** When creating the providers table, the system shall drop any existing providers table.
* **AC-REFENR-004.2:** When creating the providers table, the system shall include columns: npi, entity_type, name, deactivation_date, reactivation_date, deactivation_reason, state, city, address, zip, mailing_address, mail_city, mail_state, mail_zip, taxonomy, specialty.
* **AC-REFENR-004.3:** When populating the providers table, the system shall initialize the specialty column to empty string (to be populated later from taxonomy mapping).

### REQ-REFENR-005: Specialty Mapping from Taxonomy Codes

**User Story:** As a fraud analyst, I want the system to map taxonomy codes to human-readable specialties, so that I can identify specialty mismatches and filter providers by specialty.

**Acceptance Criteria:**

* **AC-REFENR-005.1:** When specialty mapping executes, the system shall use a predefined taxonomy-to-specialty mapping covering the top 200 taxonomy codes.
* **AC-REFENR-005.2:** When updating specialties, the system shall execute an UPDATE query for each mapped taxonomy code.
* **AC-REFENR-005.3:** When a provider's taxonomy code matches the mapping, the system shall set the specialty field to the corresponding specialty name.
* **AC-REFENR-005.4:** When a provider's taxonomy code does not match any mapping, the system shall set the specialty to "Other".
* **AC-REFENR-005.5:** When specialty mapping completes, the system shall display a sample of 5 providers with their NPI, name, state, and specialty.

### REQ-REFENR-006: HCPCS Codes Table Initialization

**User Story:** As a data analyst, I want the system to create an HCPCS codes table with descriptions and categories, so that reports display human-readable procedure names.

**Acceptance Criteria:**

* **AC-REFENR-006.1:** When creating the hcpcs_codes table, the system shall drop any existing hcpcs_codes table.
* **AC-REFENR-006.2:** When creating the hcpcs_codes table, the system shall define columns: hcpcs_code (PRIMARY KEY), short_desc, category.
* **AC-REFENR-006.3:** When the hcpcs_codes table is created, it shall initially be empty (to be populated from external files or built-in descriptions).

### REQ-REFENR-007: HCPCS External File Loading

**User Story:** As a data engineer, I want the system to load HCPCS descriptions from external reference files when available, so that the system uses current CMS code definitions.

**Acceptance Criteria:**

* **AC-REFENR-007.1:** When loading HCPCS codes, the system shall check the `reference_data/hcpcs/` directory for CSV, TSV, or TXT files.
* **AC-REFENR-007.2:** When multiple HCPCS files exist, the system shall select the largest file by size.
* **AC-REFENR-007.3:** When ZIP files exist in the HCPCS directory, the system shall extract them and re-scan for CSV/TSV/TXT files.
* **AC-REFENR-007.4:** When loading from an external HCPCS file, the system shall use DuckDB's `read_csv_auto` with `ignore_errors=true` and `all_varchar=true`.
* **AC-REFENR-007.5:** When loading from an external HCPCS file, the system shall detect column names containing "hcpcs code", "hcpcs_code", "hcpcs", "procedure code", or "code".
* **AC-REFENR-007.6:** When loading from an external HCPCS file, the system shall detect description columns containing "short description", "short desc", "description", "long description", or "long desc".
* **AC-REFENR-007.7:** When loading from an external HCPCS file, the system shall categorize codes using prefix rules (T = Home Health, H = Behavioral Health, J = Pharmacy, S = Temp/Waiver, A04 = Transportation, A/E/K/L = DME, 97 = Therapy, 992/990 = E&M, 8 = Lab, Other = Other).
* **AC-REFENR-007.8:** When loading from a fixed-width TXT file, the system shall parse the first 5 characters as the HCPCS code and extract up to 60 characters of description starting from the first alphabetic character.

### REQ-REFENR-008: HCPCS Built-In Fallback Descriptions

**User Story:** As a data engineer, I want the system to use built-in HCPCS descriptions when no external file is available, so that the pipeline completes successfully without external dependencies.

**Acceptance Criteria:**

* **AC-REFENR-008.1:** When no external HCPCS file is found or external loading fails, the system shall load from a built-in dictionary of top 100 HCPCS codes.
* **AC-REFENR-008.2:** When loading built-in HCPCS codes, the system shall include codes such as T1019, T1015, 99213, 99214, H0015, T2003, T1005, and others.
* **AC-REFENR-008.3:** When loading built-in HCPCS codes, the system shall assign categories using the same prefix rules as external file loading.

### REQ-REFENR-009: HCPCS Code Completion from Claims Data

**User Story:** As a fraud analyst, I want the system to add entries for high-volume HCPCS codes not in the reference file, so that all codes in the claims data have at least a placeholder description.

**Acceptance Criteria:**

* **AC-REFENR-009.1:** When HCPCS loading completes, the system shall query hcpcs_summary for the top 500 codes by total_paid that are not yet in hcpcs_codes.
* **AC-REFENR-009.2:** When inserting missing codes, the system shall use `INSERT OR IGNORE` to avoid duplicate key errors.
* **AC-REFENR-009.3:** When inserting missing codes, the system shall generate a description of format "Code {HCPCS_CODE}".
* **AC-REFENR-009.4:** When inserting missing codes, the system shall assign category based on prefix rules.
* **AC-REFENR-009.5:** When HCPCS loading completes, the system shall report the total count of HCPCS codes loaded.

### REQ-REFENR-010: Verification and Sampling

**User Story:** As a data quality engineer, I want the system to verify enrichment tables after loading, so that I can confirm data was loaded successfully.

**Acceptance Criteria:**

* **AC-REFENR-010.1:** When enrichment completes, the system shall query the count of rows in the providers table and display the result.
* **AC-REFENR-010.2:** When enrichment completes, the system shall attempt to query a known high-volume NPI (e.g., 1417262056) and display the name, state, and specialty if found.
* **AC-REFENR-010.3:** When enrichment completes, the system shall query the description for HCPCS code T1019 and display the result if found.
* **AC-REFENR-010.4:** When enrichment completes, the system shall display total execution time in seconds.

## Feature Behavior & Rules

The NPPES download strategy prioritizes using locally available files to avoid repeated downloads of the 10+ GB NPPES file. The system checks for extracted CSVs first, then local ZIPs, then attempts download from CMS, and finally falls back to API loading.

The NPPES CSV contains millions of provider records, so the system filters to only NPIs present in the claims table using an INNER JOIN, reducing the providers table to only relevant NPIs (typically 600,000+ providers).

Taxonomy-to-specialty mapping uses a curated list of the top 200 taxonomy codes. Unmapped codes default to "Other" rather than leaving the specialty field NULL, ensuring all providers have a specialty value for filtering.

HCPCS code categorization uses prefix-based rules that assign codes to categories like Home Health, Behavioral Health, Pharmacy, DME, Therapy, E&M, and Lab. This categorization enables grouping codes by service type in fraud pattern analysis.

The system uses `INSERT OR IGNORE` when adding codes from claims data to avoid errors if a code was already loaded from the reference file. This ensures idempotent execution even if the feature is re-run.

Deactivation dates from NPPES enable detection of post-deactivation billing, a high-confidence fraud indicator where providers continue billing after their NPI was deactivated.

## Fraud Detection Execution

## Overview

Provide a clear and concise summary of the feature, explaining what it does and the value it delivers to the user. Describe the core problem this feature solves and how it fits into the overall product.

## Terminology

* **Key Term 1**: Brief description that ensures shared understanding across the team.
* **Key Term 2**: Definition that clarifies any ambiguity in how this concept is used.

## Requirements

### REQ-XXX-001: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-001.1:** When the user \[performs action\], the system shall \[respond with specific behavior\].
* **AC-XXX-001.2:** When \[condition exists\], the system shall \[handle appropriately\].
* **AC-XXX-001.N:** \[Continue for all acceptance criteria\]

### REQ-XXX-002: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-002.1:** When \[condition\], the system shall \[behavior\].
* **AC-XXX-002.2:** \[Continue for all acceptance criteria\]

## Feature Behavior & Rules

This section clarifies how the requirements behave in practice and how they interact. It explains cross-requirement interactions, defaults, constraints, and edge conditions without prescribing UI or user flows.

### Statistical Hypothesis Testing

## Overview

This feature executes Categories 1-5 of fraud detection hypotheses covering statistical outliers, temporal anomalies, peer comparisons, network analysis, and market concentration. It applies parametric statistical tests including Z-scores, IQR, GEV distributions, Benford's Law, change-point detection, peer median comparisons, graph analysis, and HHI calculations. Each hypothesis test produces findings with confidence scores, evidence strings, and estimated financial impact.

Runs as Milestone 5 in the pipeline and produces the first major batch of fraud findings.

## Terminology

* **Finding**: A single detection result where a provider meets a hypothesis's acceptance criteria, including NPI, confidence score, evidence, and financial impact.
* **Z-Score**: Standard deviations above the mean; providers exceeding threshold (typically 3.0) are flagged.
* **IQR (Interquartile Range)**: Outlier detection using Q3 + k\*IQR thresholds.
* **GEV (Generalized Extreme Value)**: Distribution for modeling rare extreme events; providers exceeding 99th percentile return levels are flagged.
* **Change-Point**: Statistical location where a time series shifts to a different mean/variance regime.

## Requirements

### REQ-STAT-001: Category 1 - Statistical Outlier Detection

**User Story:** As a fraud investigator, I want to detect statistical outliers, so that I can identify providers whose billing deviates significantly from normal patterns.

**Acceptance Criteria:**

* **AC-STAT-001.1:** The system shall execute all testable Category 1 hypotheses (H0001-H0150) using the StatisticalAnalyzer class.
* **AC-STAT-001.2:** For Z-score hypotheses (1A, 1B, 1C), the system shall calculate mean and standard deviation from peer groups, then flag providers exceeding Z &gt; 3.0.
* **AC-STAT-001.3:** For IQR hypotheses (1D), the system shall calculate Q1, Q3, IQR, and flag providers exceeding Q3 + 3\*IQR.
* **AC-STAT-001.4:** For GEV hypotheses (1E), the system shall fit GEV distributions using scipy, calculate 99th percentile return levels, and flag providers exceeding this threshold.
* **AC-STAT-001.5:** For Benford's Law hypotheses (1F), the system shall extract first digits from payment amounts, perform chi-squared tests, and flag providers with p < 0.001.
* **AC-STAT-001.6:** Each finding shall include hypothesis_id, provider NPI list, confidence score (0.6-0.99), evidence string, and total_impact in dollars.

### REQ-STAT-002: Category 2 - Temporal Anomaly Detection

**User Story:** As a CMS administrator, I want to detect temporal anomalies, so that I can identify sudden spikes, disappearances, and unusual timing patterns.

**Acceptance Criteria:**

* **AC-STAT-002.1:** The system shall execute all testable Category 2 hypotheses (H0151-H0270) using the TemporalAnalyzer class.
* **AC-STAT-002.2:** For spike detection (2A), the system shall calculate month-over-month ratios and flag providers exceeding 3x, 5x, or 10x thresholds.
* **AC-STAT-002.3:** For sudden appearance (2B), the system shall identify providers whose first billing month exceeds specified dollar thresholds ($100K-$1M).
* **AC-STAT-002.4:** For sudden disappearance (2C), the system shall detect providers active for 6+ months who abruptly stop billing.
* **AC-STAT-002.5:** For change-point detection (2H), the system shall apply CUSUM or PELT algorithms to identify statistical regime changes in billing series.
* **AC-STAT-002.6:** Confidence scores shall increase with spike magnitude (3x = 0.65, 5x = 0.75, 10x = 0.90).

### REQ-STAT-003: Category 3 - Peer Comparison

**User Story:** As a policy analyst, I want peer comparisons, so that I can identify providers billing at rates or volumes significantly above similar providers.

**Acceptance Criteria:**

* **AC-STAT-003.1:** The system shall execute all testable Category 3 hypotheses (H0271-H0400) using the PeerAnalyzer class.
* **AC-STAT-003.2:** For rate comparisons (3A), the system shall calculate peer median paid-per-claim for each HCPCS code and flag providers exceeding 2x median.
* **AC-STAT-003.3:** For volume comparisons (3B), the system shall calculate peer median claims and flag providers exceeding 10x median.
* **AC-STAT-003.4:** For geographic peer comparisons (3D), the system shall calculate state-level percentiles and flag providers exceeding the 95th percentile.
* **AC-STAT-003.5:** For specialty peer comparisons (3E), the system shall group providers by specialty and flag those exceeding specialty 95th percentile.
* **AC-STAT-003.6:** Financial impact shall be calculated as (provider_metric - peer_median) \* volume.

### REQ-STAT-004: Category 4 - Network Analysis

**User Story:** As a fraud investigator, I want network analysis, so that I can detect hub-and-spoke structures, circular billing, and shell networks.

**Acceptance Criteria:**

* **AC-STAT-004.1:** The system shall execute all testable Category 4 hypotheses (H0401-H0520) using the NetworkAnalyzer class.
* **AC-STAT-004.2:** For hub-and-spoke detection (4A), the system shall count unique servicing NPIs per billing NPI and flag those exceeding thresholds (50, 100, 200).
* **AC-STAT-004.3:** For circular billing (4C), the system shall detect bidirectional billing edges where both A→B and B→A exist with payments exceeding $50K.
* **AC-STAT-004.4:** For ghost network detection (4G), the system shall check for missing NPPES records, deactivated NPIs, and single-biller concentration patterns.
* **AC-STAT-004.5:** The system shall use NetworkX or similar graph library for connected component analysis and density calculations.

### REQ-STAT-005: Category 5 - Concentration and Market Power

**User Story:** As a competition analyst, I want concentration metrics, so that I can identify monopolistic billing patterns and market manipulation.

**Acceptance Criteria:**

* **AC-STAT-005.1:** The system shall execute all testable Category 5 hypotheses (H0521-H0600) using the ConcentrationAnalyzer class.
* **AC-STAT-005.2:** For provider dominance (5A), the system shall calculate each provider's share of total spending per HCPCS code and flag those exceeding 30%, 50%, or 80%.
* **AC-STAT-005.3:** For single-code specialists (5B), the system shall calculate revenue concentration ratios and flag providers with &gt;90% revenue from one code.
* **AC-STAT-005.4:** For HHI calculations (5C), the system shall compute Herfindahl-Hirschman Index per HCPCS code and flag markets exceeding 2500.
* **AC-STAT-005.5:** The system shall save all findings to `findings/statistical_findings_categories_1_5.json` with summary statistics.

## Feature Behavior & Rules

Each analyzer class (StatisticalAnalyzer, TemporalAnalyzer, PeerAnalyzer, NetworkAnalyzer, ConcentrationAnalyzer) inherits from BaseAnalyzer and implements an execute() method. Findings are accumulated in-memory during execution and written to JSON at completion. Database connections are read-only. Peer group calculations cache median values to avoid redundant queries. Confidence scoring follows category-specific formulas that increase with deviation magnitude or multiple detection signals.

### Machine Learning Anomaly Detection

## Overview

This feature executes Category 6 hypotheses using classical machine learning models including Isolation Forest, DBSCAN, Random Forest, XGBoost, K-means, and LOF to detect multidimensional anomalies not captured by univariate statistical tests. It transforms provider-level features into normalized vectors, trains unsupervised and semi-supervised models, and flags providers with extreme anomaly scores or distance metrics.

Runs as Milestone 6 in the pipeline and complements statistical methods with ML-based pattern recognition.

## Terminology

* **Isolation Forest**: Unsupervised anomaly detection that isolates outliers using random decision trees.
* **DBSCAN**: Density-based clustering that identifies noise points as anomalies.
* **XGBoost Semi-Supervised**: Trains on high-confidence findings from Categories 1-5 to predict novel anomalies.
* **LOF (Local Outlier Factor)**: Anomaly detection based on local density deviations.
* **Feature Vector**: Normalized provider metrics (total_paid, claims_per_bene, num_codes, etc.) used as ML model inputs.

## Requirements

### REQ-ML-001: Feature Engineering and Normalization

**User Story:** As a data scientist, I want provider data transformed into normalized feature vectors, so that ML models can detect multidimensional anomalies.

**Acceptance Criteria:**

* **AC-ML-001.1:** The system shall extract provider-level features including total_paid, total_claims, total_beneficiaries, avg_paid_per_claim, avg_claims_per_bene, num_codes, num_months, specialty, state, and top_code_concentration.
* **AC-ML-001.2:** The system shall apply StandardScaler normalization to all numeric features before model training.
* **AC-ML-001.3:** The system shall handle missing values using median imputation for numeric features.
* **AC-ML-001.4:** The system shall create segment-specific feature sets for home health, behavioral health, and high-volume providers where specified by hypotheses.

### REQ-ML-002: Isolation Forest Execution

**User Story:** As a fraud analyst, I want Isolation Forest anomaly detection, so that I can identify providers with unusual multidimensional profiles.

**Acceptance Criteria:**

* **AC-ML-002.1:** The system shall execute 40 Isolation Forest hypotheses (H0601-H0640) across overall and segment-specific models.
* **AC-ML-002.2:** The system shall train Isolation Forest with contamination=0.01 to flag the top 1% most anomalous providers.
* **AC-ML-002.3:** The system shall flag providers with anomaly_score < -0.5 and total_paid &gt; $100K.
* **AC-ML-002.4:** The system shall record which features contributed most to each provider's anomaly score.
* **AC-ML-002.5:** Confidence scores shall be calculated as min(0.95, 0.60 + 0.30 \* |anomaly_score|).

### REQ-ML-003: XGBoost Semi-Supervised Learning

**User Story:** As a machine learning engineer, I want XGBoost trained on known findings, so that I can discover novel fraud patterns not detected by statistical methods.

**Acceptance Criteria:**

* **AC-ML-003.1:** The system shall execute 30 XGBoost hypotheses (H0691-H0720) using semi-supervised learning.
* **AC-ML-003.2:** The system shall create training labels from high-confidence findings (confidence &gt;= 0.85) from Categories 1-5.
* **AC-ML-003.3:** The system shall train XGBoost with max_depth=6, n_estimators=100, learning_rate=0.1.
* **AC-ML-003.4:** The system shall flag providers with predicted fraud probability &gt; 0.8 that were not already flagged by Categories 1-5.
* **AC-ML-003.5:** The system shall save feature importance rankings for model interpretability.

### REQ-ML-004: Clustering and Distance-Based Methods

**User Story:** As a fraud investigator, I want clustering methods, so that I can identify providers that don't fit any normal billing pattern.

**Acceptance Criteria:**

* **AC-ML-004.1:** The system shall execute DBSCAN (30 hypotheses), K-means (15 hypotheses), and LOF (15 hypotheses).
* **AC-ML-004.2:** For DBSCAN, the system shall flag noise points (cluster=-1) and small clusters (size <= 3) with total_paid &gt; $100K.
* **AC-ML-004.3:** For K-means, the system shall train with k=20 clusters and flag providers with distance &gt; 3x cluster mean distance.
* **AC-ML-004.4:** For LOF, the system shall flag providers with LOF score &gt; 2.0 using n_neighbors=20.
* **AC-ML-004.5:** The system shall save all ML findings to `findings/ml_findings_category_6.json`.

### REQ-ML-005: Model Validation and Output

**User Story:** As a quality assurance analyst, I want ML model performance tracked, so that I can assess detection effectiveness.

**Acceptance Criteria:**

* **AC-ML-005.1:** The system shall log the number of providers flagged by each ML method.
* **AC-ML-005.2:** The system shall calculate and log the overlap between ML findings and statistical findings (Categories 1-5).
* **AC-ML-005.3:** The system shall report novel findings (detected by ML but not by statistical methods) separately.
* **AC-ML-005.4:** The system shall save trained models to `models/` directory for reproducibility.

## Feature Behavior & Rules

All ML models use scikit-learn implementations. Feature vectors are constructed from provider_summary and provider_hcpcs aggregations. Segment-specific models (home health, behavioral health) filter data before training. XGBoost uses stratified sampling to balance positive examples from Categories 1-5 findings. All models are trained fresh each pipeline run; no incremental learning. Missing specialty or state values are treated as a separate category rather than imputed.

### Domain-Specific Business Rules

## Overview

This feature executes Category 8 hypotheses testing domain-specific business rules that encode clinical impossibilities, regulatory violations, and known fraud schemes. It validates impossible service volumes based on time constraints, detects upcoding by analyzing E&M level distributions, identifies unbundling patterns, checks for phantom billing indicators, and flags providers in high-risk categories with additional red flags.

Runs as Milestone 7 in the pipeline and applies fraud expertise encoded as deterministic rules.

## Terminology

* **Impossible Volume**: Claims exceeding physical time limits (e.g., &gt;480 15-minute units of personal care in a month).
* **Upcoding**: Billing higher E&M levels at rates inconsistent with specialty or state norms.
* **Unbundling**: Billing separate line items for services that should be billed as a bundled package.
* **Phantom Billing**: Billing without corresponding service delivery (indicators include flat beneficiary counts, round numbers, zero variance).
* **High-Risk Category**: Service types with elevated fraud prevalence (Home Health, Behavioral Health, Personal Care, ABA Therapy, DME, Transportation).

## Requirements

### REQ-DOM-001: Impossible Volume Detection

**User Story:** As a fraud investigator, I want impossible volume detection, so that I can identify providers billing beyond physical capacity.

**Acceptance Criteria:**

* **AC-DOM-001.1:** The system shall execute 15 impossible volume hypotheses (H0831-H0845) for timed service codes including T1019, T1020, T1005, S5125, H0015, H2015, H2016.
* **AC-DOM-001.2:** For each code, the system shall calculate maximum units per beneficiary per month based on unit duration (e.g., T1019 = 15 min units, max 480 units = 120 hours).
* **AC-DOM-001.3:** The system shall flag claims where claims/beneficiaries exceeds the physical maximum with paid &gt; $10K.
* **AC-DOM-001.4:** Financial impact shall be calculated as 100% of payments above the physical maximum.
* **AC-DOM-001.5:** Confidence shall be set to 0.99 for impossible volumes (these are deterministic violations).

### REQ-DOM-002: Upcoding Detection

**User Story:** As a medical review specialist, I want upcoding detection, so that I can identify providers systematically billing higher-level services than peers.

**Acceptance Criteria:**

* **AC-DOM-002.1:** The system shall execute 15 upcoding hypotheses (H0846-H0860) targeting E&M level distributions.
* **AC-DOM-002.2:** For office visit families (99211-99215), the system shall calculate the percentage of claims at the highest level (99215) and flag providers exceeding 2x or 3x specialty median.
* **AC-DOM-002.3:** For ED visits (99281-99285), the system shall flag providers with 99285 rates exceeding 2x peer median.
* **AC-DOM-002.4:** The system shall detect progressive upcoding patterns where the average E&M level increases monotonically over time.
* **AC-DOM-002.5:** Financial impact shall be estimated as the difference between actual revenue and revenue expected at peer median level distribution.

### REQ-DOM-003: Unbundling Detection

**User Story:** As a billing compliance officer, I want unbundling detection, so that I can identify providers fragmenting bundled services into separate billings.

**Acceptance Criteria:**

* **AC-DOM-003.1:** The system shall execute 15 unbundling hypotheses (H0861-H0875) testing codes-per-beneficiary ratios.
* **AC-DOM-003.2:** The system shall flag providers with codes-per-beneficiary exceeding 3x peer median, sustained for 6+ months.
* **AC-DOM-003.3:** The system shall detect component code billing when bundle codes exist (e.g., lab panels vs individual tests, therapy evaluations vs components).
* **AC-DOM-003.4:** The system shall identify same-day sequential code patterns suggesting unbundling.
* **AC-DOM-003.5:** Financial impact shall be calculated as the difference between summed component billing and the bundled rate.

### REQ-DOM-004: Phantom Billing Indicators

**User Story:** As a fraud analyst, I want phantom billing detection, so that I can identify providers billing without delivering services.

**Acceptance Criteria:**

* **AC-DOM-004.1:** The system shall execute 10 phantom billing hypotheses (H0876-H0885) detecting patterns including constant beneficiary counts, flat monthly billing, zero variance, round numbers, and weekend/holiday concentration.
* **AC-DOM-004.2:** The system shall flag providers with identical billing amounts every month for 6+ consecutive months.
* **AC-DOM-004.3:** The system shall flag providers with beneficiary counts unchanging despite claims growth &gt;50%.
* **AC-DOM-004.4:** The system shall flag providers with monthly billing standard deviation < 5% of mean over 12+ months.
* **AC-DOM-004.5:** Confidence scores shall be composite: multiple phantom indicators increase confidence (1 indicator = 0.65, 2 indicators = 0.80, 3+ indicators = 0.95).

### REQ-DOM-005: High-Risk Category Analysis

**User Story:** As a program integrity specialist, I want high-risk category flagging, so that I can apply elevated scrutiny to providers in fraud-prone service types.

**Acceptance Criteria:**

* **AC-DOM-005.1:** The system shall execute 15 high-risk category hypotheses (H0886-H0900) combining category membership with additional red flags (rate outlier, volume outlier, network anomaly).
* **AC-DOM-005.2:** For Home Health providers, the system shall flag those in the top 1% by paid-per-claim AND with &gt;50 servicing NPIs.
* **AC-DOM-005.3:** For Behavioral Health providers, the system shall flag those exceeding state 95th percentile AND billing exclusively for a single code.
* **AC-DOM-005.4:** The system shall save all domain rule findings to `findings/domain_findings_category_8.json`.

## Feature Behavior & Rules

Domain rules are implemented as deterministic SQL queries or Python functions in the domain_rules module. Timed code limits are defined in the TIMED_CODES constant list. E&M level families are defined in EM_FAMILIES dict. Rules execute independently and findings are deduplicated at the provider level. Multiple rule violations for the same provider increment the composite confidence score. Rules are designed to have near-zero false positive rates but may have moderate false negative rates.

### Cross-Reference and Composite Scoring

## Overview

This feature executes Category 9 cross-reference validation and Category 10 composite scoring. It validates provider data against external registries (NPPES, LEIE, state licensing), detects specialty mismatches and entity type violations, calculates multi-method composite risk scores, and flags providers appearing across multiple analytical categories. This produces the final integrated fraud risk assessment.

Runs as Milestone 8 in the pipeline and synthesizes findings from all prior detection methods.

## Terminology

* **NPPES (National Plan & Provider Enumeration System)**: Federal registry of all healthcare providers; used to validate NPI records.
* **LEIE (List of Excluded Individuals and Entities)**: OIG database of providers excluded from federal programs.
* **Specialty Mismatch**: Provider billing for services outside their registered specialty scope.
* **Entity Type Violation**: Individual NPI billing at organization volumes or organizational NPI patterns inconsistent with entity type.
* **Composite Score**: Weighted risk score combining findings from multiple detection categories (1-9).
* **Multi-Method Flag**: Provider appearing in 3+ analytical categories, indicating systemic fraud pattern.

## Requirements

### REQ-CROSS-001: NPPES and LEIE Validation

**User Story:** As a program integrity officer, I want NPPES and LEIE cross-checks, so that I can identify providers with missing, deactivated, or excluded credentials.

**Acceptance Criteria:**

* **AC-CROSS-001.1:** The system shall execute NPPES validation hypotheses checking for NPIs not found in NPPES, deactivated NPIs, mismatched addresses, and mismatched specialties.
* **AC-CROSS-001.2:** The system shall execute LEIE validation hypotheses flagging any billing NPI appearing in the exclusion database.
* **AC-CROSS-001.3:** For providers billing despite LEIE exclusion, the system shall flag 100% of their payments as potentially improper.
* **AC-CROSS-001.4:** For providers with no NPPES record, the system shall flag with confidence 0.95 if total_paid &gt; $100K.
* **AC-CROSS-001.5:** The system shall flag NPIs billing after their NPPES deactivation date.

### REQ-CROSS-002: Specialty and Entity Type Validation

**User Story:** As a medical policy specialist, I want specialty validation, so that I can identify providers billing outside their scope of practice.

**Acceptance Criteria:**

* **AC-CROSS-002.1:** The system shall execute specialty mismatch hypotheses comparing billed HCPCS codes to NPPES-registered specialty.
* **AC-CROSS-002.2:** The system shall flag Individual (Type 1) NPIs with organizational-scale billing patterns (&gt;100 servicing NPIs, &gt;$10M total_paid).
* **AC-CROSS-002.3:** The system shall flag Organization (Type 2) NPIs exhibiting individual provider patterns (single servicing NPI, narrow code range).
* **AC-CROSS-002.4:** The system shall use HCPCS-to-specialty mapping tables to validate clinical appropriateness.
* **AC-CROSS-002.5:** Confidence for specialty mismatches shall be 0.75; for entity type violations shall be 0.85.

### REQ-CROSS-003: Geographic and Address Validation

**User Story:** As a fraud investigator, I want geographic validation, so that I can detect billing from impossible locations or across state boundaries.

**Acceptance Criteria:**

* **AC-CROSS-003.1:** The system shall execute geographic validation hypotheses comparing claim state to NPPES-registered state.
* **AC-CROSS-003.2:** The system shall flag providers billing in multiple states without corresponding NPPES practice locations.
* **AC-CROSS-003.3:** The system shall detect beneficiary state distributions inconsistent with provider location (e.g., NY provider with 80% FL beneficiaries).
* **AC-CROSS-003.4:** The system shall flag known mail-drop addresses or suspicious address patterns (PO boxes for high-volume billers, residential addresses for organizations).

### REQ-CROSS-004: Composite Risk Scoring

**User Story:** As a risk analyst, I want composite scores, so that I can prioritize investigations based on combined evidence from multiple detection methods.

**Acceptance Criteria:**

* **AC-CROSS-004.1:** For each provider, the system shall calculate a composite_score = sum(method_confidence \* method_impact) across all methods that flagged the provider.
* **AC-CROSS-004.2:** The system shall count the number of distinct analytical categories (1-9) that flagged each provider as num_methods.
* **AC-CROSS-004.3:** The system shall assign confidence tiers: HIGH (num_methods &gt;= 3 OR composite_score &gt;= 8.0), MEDIUM (num_methods = 2 OR composite_score &gt;= 4.0), LOW (num_methods = 1 OR composite_score &gt;= 2.0).
* **AC-CROSS-004.4:** The system shall flag providers appearing in 5+ categories as "systemic_fraud_pattern" with elevated priority.
* **AC-CROSS-004.5:** The system shall aggregate total financial impact across all findings per provider, deduplicating overlapping amounts.

### REQ-CROSS-005: Final Findings Integration

**User Story:** As a developer, I want all findings merged and scored, so that downstream modules receive a unified ranked provider risk list.

**Acceptance Criteria:**

* **AC-CROSS-005.1:** The system shall load findings from all prior milestones (Categories 1-9) and merge by provider NPI.
* **AC-CROSS-005.2:** The system shall create a consolidated findings file `findings/final_scored_findings.json` with fields: npi, name, state, specialty, confidence_tier, num_methods, composite_score, total_impact, methods_flagged, evidence_summary.
* **AC-CROSS-005.3:** The system shall generate summary statistics including total findings, confidence tier distribution, total estimated recoverable, and top 10 methods by impact.
* **AC-CROSS-005.4:** The system shall save cross-reference findings to `findings/crossref_findings_category_9.json`.

## Feature Behavior & Rules

Cross-reference validation requires reference data loaded in Milestone 2 (NPPES, LEIE, HCPCS). Missing reference data causes hypotheses to be skipped. Composite scoring weights findings by confidence and financial impact; multiple low-confidence findings can accumulate to high composite scores. Entity type classification uses NPI Type 1 (Individual) vs Type 2 (Organization) from NPPES. Geographic validation allows multi-state billing for organizations with documented practice locations but flags individuals. LEIE matches use exact NPI match plus fuzzy name/address matching.

## Exploratory Analysis and Hypothesis Design

## Overview

Provide a clear and concise summary of the feature, explaining what it does and the value it delivers to the user. Describe the core problem this feature solves and how it fits into the overall product.

## Terminology

* **Key Term 1**: Brief description that ensures shared understanding across the team.
* **Key Term 2**: Definition that clarifies any ambiguity in how this concept is used.

## Requirements

### REQ-XXX-001: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-001.1:** When the user \[performs action\], the system shall \[respond with specific behavior\].
* **AC-XXX-001.2:** When \[condition exists\], the system shall \[handle appropriately\].
* **AC-XXX-001.N:** \[Continue for all acceptance criteria\]

### REQ-XXX-002: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-002.1:** When \[condition\], the system shall \[behavior\].
* **AC-XXX-002.2:** \[Continue for all acceptance criteria\]

## Feature Behavior & Rules

This section clarifies how the requirements behave in practice and how they interact. It explains cross-requirement interactions, defaults, constraints, and edge conditions without prescribing UI or user flows.

### Exploratory Data Analysis

## Overview

This feature performs initial exploratory data analysis (EDA) and generates a comprehensive data profile for the entire Medicaid claims dataset. It calculates global statistics, identifies top providers and HCPCS codes by spending, analyzes monthly spending trends, and assesses spending concentration using Pareto analysis. The output is a JSON data profile and several baseline charts that provide a high-level understanding of the data's characteristics and highlight potential areas for deeper investigation.

This runs as Milestone 3 in the pipeline and serves as a foundational step for hypothesis generation and fraud detection, offering critical context for analysts and investigators.

## Terminology

* **Data Profile**: A JSON document summarizing key statistics and insights about the claims dataset.
* **Global Statistics**: Overall metrics such as total rows, unique NPIs, total paid, and average paid amounts.
* **Spending Concentration**: Analysis of how spending is distributed among providers or codes, often using Pareto principle (e.g., top X% of providers account for Y% of spending).
* **HHS Style Charts**: Visualizations conforming to the U.S. government's open data visualization conventions.

## Requirements

### REQ-EDA-001: Global Statistics Calculation

**User Story:** As a data analyst, I want the system to calculate core statistics for the entire dataset, so that I can quickly understand the overall scale and characteristics of the data.

**Acceptance Criteria:**

* AC-EDA-001.1: The system shall calculate and record `total_rows`, `unique_billing_npis`, `unique_servicing_npis`, `unique_hcpcs_codes`, `unique_months`, `total_paid`, `total_claims`, `total_beneficiaries`.
* AC-EDA-001.2: The system shall calculate and record `avg_paid`, `median_paid`, and `std_paid` for all claims.
* AC-EDA-001.3: The system shall count and record `negative_paid_rows` and `null_servicing_rows`.
* AC-EDA-001.4: All calculated statistics shall be included in the `data_profile.json` output.

### REQ-EDA-002: Top Entity Identification

**User Story:** As a fraud investigator, I want to see the highest spending providers and HCPCS codes, so that I can focus on areas with the largest financial impact.

**Acceptance Criteria:**

* AC-EDA-002.1: The system shall identify the top 100 providers by `total_paid` from the `provider_summary` table.
* AC-EDA-002.2: For each top provider, the system shall include NPI, name, state, specialty, `total_paid`, `total_claims`, `total_beneficiaries`, `num_codes`, and `num_months` in the data profile.
* AC-EDA-002.3: The system shall identify the top 100 HCPCS codes by `total_paid` from the `hcpcs_summary` table.
* AC-EDA-002.4: For each top HCPCS code, the system shall include code, description, category, `total_paid`, `total_claims`, and `num_providers` in the data profile.

### REQ-EDA-003: Monthly Spending Trend Analysis

**User Story:** As a CMS administrator, I want to view the overall monthly spending trend, so that I can monitor changes in program expenditures over time.

**Acceptance Criteria:**

* AC-EDA-003.1: The system shall aggregate `total_paid` and `total_claims` by `claim_month`.
* AC-EDA-003.2: The monthly spending data shall be recorded in the `data_profile.json`.
* AC-EDA-003.3: The system shall generate a line chart showing monthly spending trends, saved as `monthly_spending_trend.png` in the `output/charts` directory.

### REQ-EDA-004: Spending Concentration (Pareto) Analysis

**User Story:** As a policy analyst, I want to understand how concentrated spending is among providers, so that I can identify the few entities responsible for the majority of costs.

**Acceptance Criteria:**

* AC-EDA-004.1: The system shall calculate the cumulative percentage of total paid by ranked providers.
* AC-EDA-004.2: The system shall determine the percentage of providers accounting for 50%, 80%, 90%, and 99% of total spending.
* AC-EDA-004.3: These concentration metrics shall be included in the `data_profile.json`.
* AC-EDA-004.4: The system shall generate a Lorenz curve chart illustrating provider spending concentration, saved as `lorenz_curve.png`.

### REQ-EDA-005: Data Profile Output

**User Story:** As a developer, I want all calculated EDA metrics to be stored in a structured JSON file, so that they can be easily accessed by other parts of the pipeline or external tools.

**Acceptance Criteria:**

* AC-EDA-005.1: The system shall generate a `data_profile.json` file in the `output/` directory.
* AC-EDA-005.2: The `data_profile.json` file shall contain all global statistics, top provider and HCPCS code lists, monthly spending data, and spending concentration metrics.
* AC-EDA-005.3: The JSON output shall be formatted with an indent of 2 for readability and use `default=str` for serialization of non-standard types.

### REQ-EDA-006: Chart Generation and Formatting

**User Story:** As a business user, I want visual summaries of the data profile, so that I can quickly grasp key trends and outliers.

**Acceptance Criteria:**

* AC-EDA-006.1: The system shall generate a horizontal bar chart of the top 20 procedures by total spending, saved as `top20_procedures.png`.
* AC-EDA-006.2: The system shall generate a horizontal bar chart of the top 20 providers by total spending, saved as `top20_providers.png`.
* AC-EDA-006.3: All generated charts shall follow HHS OpenData styling conventions (e.g., monochromatic amber, minimal chrome, no 3D effects).
* AC-EDA-006.4: All charts shall include appropriate titles, subtitles, and branding.

## Feature Behavior & Rules

The EDA process utilizes the `claims`, `provider_summary`, `hcpcs_summary`, and `providers` tables from the DuckDB database. Database connections are read-only to ensure data integrity. Elapsed time for the milestone is reported upon completion.

Chart generation uses `matplotlib` with custom HHS styling applied via `chart_utils` functions. Charts are saved as PNG files. The Lorenz curve specifically handles subsampling for plotting efficiency with large datasets.

NPI names and specialties are enriched from the `providers` table for human-readable charts, defaulting to 'NPI {billing_npi}' if the name is not found.

Spending concentration calculations accurately reflect the proportion of providers for a given cumulative spending percentage, providing a clear measure of market power distribution. Calculations handle potential division by zero for small datasets. The `data_profile.json` serves as a central repository for all EDA-derived metrics.

### Hypothesis Generation

## Overview

This feature programmatically generates structured fraud detection hypotheses in JSON format, organized into 10 analytical categories. Each hypothesis defines specific detection parameters, acceptance criteria, and financial impact calculation methods that will be systematically tested against the Medicaid claims dataset. The hypothesis generation process creates exactly 1,000 core hypotheses plus additional gap analysis hypotheses covering statistical outliers, temporal anomalies, peer comparison, network analysis, concentration patterns, machine learning models, deep learning approaches, domain-specific red flags, cross-reference validation, and composite risk signals.

This runs as Milestone 4 in the pipeline and establishes the structured framework for all subsequent fraud detection analyses.

## Terminology

* **Hypothesis**: A structured JSON object that defines a specific fraud detection test, including its category, method, parameters, acceptance criteria, and impact calculation approach.
* **Acceptance Criteria**: The specific thresholds and conditions that must be met for a provider to be flagged under a hypothesis (e.g., "z-score &gt; 3.0, claims &gt;= 10, excess &gt; $10K").
* **Financial Impact Method**: The formula or approach used to calculate the estimated recoverable amount when a hypothesis flags a provider.
* **Hypothesis Category**: One of 10 high-level analytical approaches: Statistical Outlier (1), Temporal Anomaly (2), Peer Comparison (3), Network Analysis (4), Concentration (5), Classical ML (6), Deep Learning (7), Domain Rules (8), Cross-Reference (9), Composite (10).
* **Subcategory**: A specific analytical technique within a category (e.g., 1A = Z-score on paid-per-claim, 1B = Z-score on claims-per-bene).
* **Parametric Hypothesis**: A hypothesis template that can be instantiated with different parameters (e.g., top 30 HCPCS codes, multiple specialties, various thresholds).

## Requirements

### REQ-HYP-001: Core Hypothesis Structure

**User Story:** As a data analyst, I want each hypothesis to have a standardized JSON structure, so that I can systematically test and compare different fraud detection approaches.

**Acceptance Criteria:**

* **AC-HYP-001.1:** The system shall generate each hypothesis as a JSON object with the following required fields: `id`, `category`, `subcategory`, `description`, `method`, `acceptance_criteria`, `analysis_function`, `financial_impact_method`, and `parameters`.
* **AC-HYP-001.2:** The `id` field shall follow the format `HXXXX` where XXXX is a zero-padded 4-digit sequential number (e.g., H0001, H0042, H1000).
* **AC-HYP-001.3:** The `category` field shall be a string from '1' to '10' representing the analytical category.
* **AC-HYP-001.4:** The `subcategory` field shall follow the format `{category}{letter}` (e.g., '1A', '2B', '3F').
* **AC-HYP-001.5:** The `parameters` field shall be a nested JSON object containing all configurable values for the hypothesis (e.g., `{'hcpcs_code': 'T1019', 'z_threshold': 3.0, 'min_claims': 10}`).

### REQ-HYP-002: Category 1 - Statistical Outlier Detection

**User Story:** As a fraud investigator, I want hypotheses that detect statistical outliers, so that I can identify providers whose billing patterns deviate significantly from normal distributions.

**Acceptance Criteria:**

* **AC-HYP-002.1:** The system shall generate 150 Category 1 hypotheses (H0001-H0150) covering six subcategories: 1A (Z-score paid-per-claim), 1B (Z-score claims-per-bene), 1C (Z-score paid-per-bene), 1D (IQR outliers), 1E (GEV extreme value), 1F (Benford's Law).
* **AC-HYP-002.2:** For subcategory 1A, the system shall generate 30 hypotheses testing Z-score outliers on paid-per-claim for the top 30 HCPCS codes by spending.
* **AC-HYP-002.3:** For subcategory 1B, the system shall generate 30 hypotheses testing Z-score outliers on claims-per-beneficiary for the top 30 HCPCS codes.
* **AC-HYP-002.4:** For subcategory 1C, the system shall generate 30 hypotheses testing Z-score outliers on paid-per-beneficiary for the top 30 HCPCS codes.
* **AC-HYP-002.5:** For subcategory 1D, the system shall generate 7 hypotheses testing IQR outliers across 7 metrics: `total_paid`, `total_claims`, `total_beneficiaries`, `avg_paid_per_claim`, `avg_claims_per_bene`, `num_codes`, `num_months`.
* **AC-HYP-002.6:** For subcategory 1E, the system shall generate 20 hypotheses testing GEV extreme value analysis across 10 HCPCS categories for both `paid_per_claim` and `total_paid` metrics.
* **AC-HYP-002.7:** For subcategory 1F, the system shall generate 20 hypotheses testing Benford's Law violations, round number detection, duplicate amounts, and payment clustering patterns.

### REQ-HYP-003: Category 2 - Temporal Anomaly Detection

**User Story:** As a CMS administrator, I want hypotheses that detect temporal anomalies, so that I can identify sudden spikes, disappearances, and unusual billing timing patterns.

**Acceptance Criteria:**

* **AC-HYP-003.1:** The system shall generate 120 Category 2 hypotheses (H0151-H0270) covering eight subcategories: 2A (month-over-month spikes), 2B (sudden appearance), 2C (sudden disappearance), 2D (year-over-year growth), 2E (seasonal violations), 2F (COVID anomalies), 2G (December surges), 2H (change-point detection).
* **AC-HYP-003.2:** For subcategory 2A, the system shall generate 20 hypotheses testing billing spikes with thresholds of 3x, 5x, and 10x, filtered by various conditions (all providers, home health, behavioral, DME, rate-only, December-specific, COVID-onset, post-2022).
* **AC-HYP-003.3:** For subcategory 2B, the system shall generate 15 hypotheses testing sudden provider appearance with first-month thresholds ranging from $100K to $1M across different filters.
* **AC-HYP-003.4:** For subcategory 2C, the system shall generate 15 hypotheses testing sudden disappearance with various average billing thresholds and minimum active month requirements.
* **AC-HYP-003.5:** For subcategory 2D, the system shall generate 15 hypotheses testing year-over-year growth exceeding 3x, 5x, and 10x with filters for sustained growth, code expansion, and post-COVID patterns.
* **AC-HYP-003.6:** For subcategory 2H, the system shall generate 15 hypotheses using CUSUM, PELT, and variance-change methods to detect statistical change points in billing series.

### REQ-HYP-004: Category 3 - Peer Comparison

**User Story:** As a policy analyst, I want hypotheses comparing providers to their peers, so that I can identify those billing at rates or volumes significantly above similar providers.

**Acceptance Criteria:**

* **AC-HYP-004.1:** The system shall generate 130 Category 3 hypotheses (H0271-H0400) covering six subcategories: 3A (rate vs peers), 3B (volume vs peers), 3C (beneficiary concentration vs peers), 3D (geographic peer comparison), 3E (specialty peer comparison), 3F (size tier mismatches).
* **AC-HYP-004.2:** For subcategory 3A, the system shall generate 30 hypotheses testing paid-per-claim exceeding 2x peer median for the top 30 HCPCS codes.
* **AC-HYP-004.3:** For subcategory 3B, the system shall generate 20 hypotheses testing total claims exceeding 10x peer median for the top 20 HCPCS codes.
* **AC-HYP-004.4:** For subcategory 3C, the system shall generate 20 hypotheses testing claims-per-beneficiary exceeding 3x peer median for the top 20 HCPCS codes.
* **AC-HYP-004.5:** For subcategory 3E, the system shall generate 20 hypotheses testing providers exceeding specialty 95th percentile across 20 specialties.
* **AC-HYP-004.6:** For subcategory 3F, the system shall generate 20 hypotheses detecting size tier mismatches such as individual NPIs billing at organization scale, high paid with few codes, extreme variance, and other structural anomalies.

### REQ-HYP-005: Category 4 - Network Analysis

**User Story:** As a fraud investigator, I want hypotheses analyzing billing networks, so that I can detect hub-and-spoke structures, circular billing, and shell provider networks.

**Acceptance Criteria:**

* **AC-HYP-005.1:** The system shall generate 120 Category 4 hypotheses (H0401-H0520) covering seven subcategories: 4A (hub-and-spoke), 4B (shared servicing), 4C (circular billing), 4D (network density), 4E (new networks), 4F (pure billing entities), 4G (ghost networks).
* **AC-HYP-005.2:** For subcategory 4A, the system shall generate 20 hypotheses detecting hubs with varying servicing NPI counts (&gt;50, &gt;100, &gt;200) across different filters including captive arrangements, high-value networks, and cross-specialty patterns.
* **AC-HYP-005.3:** For subcategory 4B, the system shall generate 20 hypotheses detecting servicing NPIs appearing under multiple billing NPIs (&gt;10, &gt;20, &gt;50) with filters for rate arbitrage, multi-state operations, and sequential NPIs.
* **AC-HYP-005.4:** For subcategory 4C, the system shall generate 15 hypotheses detecting circular billing patterns with bilateral payment thresholds ranging from $50K to $500K.
* **AC-HYP-005.5:** For subcategory 4G, the system shall generate 20 hypotheses detecting ghost network indicators including single biller concentration, missing NPPES records, deactivated NPIs, identical patterns, sequential NPIs, and batch creations.

### REQ-HYP-006: Categories 5-10 Generation

**User Story:** As a data scientist, I want hypotheses across concentration, ML, DL, domain rules, cross-reference, and composite approaches, so that I can test multiple analytical paradigms for fraud detection.

**Acceptance Criteria:**

* **AC-HYP-006.1:** The system shall generate 80 Category 5 hypotheses (H0521-H0600) testing market concentration including provider dominance (&gt;30%, &gt;50%, &gt;80% share), single-code specialists (&gt;90%, &gt;95%, &gt;99% revenue concentration), HHI thresholds (&gt;2500, &gt;5000), geographic monopolies, and temporal concentration.
* **AC-HYP-006.2:** The system shall generate 150 Category 6 hypotheses (H0601-H0750) applying classical ML methods including Isolation Forest (40 hypotheses), DBSCAN (30), Random Forest (20), XGBoost (30), K-means (15), and LOF (15).
* **AC-HYP-006.3:** The system shall generate 80 Category 7 hypotheses (H0751-H0830) applying deep learning methods including Autoencoder (30), VAE (20), LSTM (15), and Transformer attention (15).
* **AC-HYP-006.4:** The system shall generate 100 Category 8 hypotheses (H0831-H0930) testing domain-specific red flags including impossible volumes (15), upcoding (15), unbundling (15), high-risk categories (15), phantom billing (10), adjustment anomalies (10), and duplicates (10).
* **AC-HYP-006.5:** The system shall generate 70 Category 9 hypotheses (H0931-H1000) testing cross-reference validations including specialty mismatches, entity type violations, geographic impossibilities, deactivated NPIs, LEIE exclusions, and NPPES inconsistencies.
* **AC-HYP-006.6:** For composite Category 10 hypotheses, the system shall include multi-signal detection rules that combine findings from multiple categories.

### REQ-HYP-007: Gap Analysis Hypotheses

**User Story:** As a fraud detection specialist, I want additional gap analysis hypotheses beyond the core 1,000, so that I can test domain-specific patterns not covered by the systematic taxonomy.

**Acceptance Criteria:**

* **AC-HYP-007.1:** The system shall generate 10 batches of gap analysis hypotheses (H1001-H1100) covering ABA therapy fraud (15), pharmacy fraud (10), addiction treatment fraud (10), kickback/referral concentration (10), sober homes (10), genetic testing (5), beneficiary anomalies (10), transportation fraud (10), address-based schemes (10), and advanced analytical methods (10).
* **AC-HYP-007.2:** Each gap analysis hypothesis shall follow the same JSON structure as core hypotheses.
* **AC-HYP-007.3:** Gap analysis hypotheses shall target specific high-risk service types identified through domain research including ABA therapy codes (97151-97158, H0031-H0032), pharmacy patterns, addiction treatment (H0001-H0020, G0396-G0397), genetic testing (81XXX codes), and transportation (A0428-A0436, T2001-T2005).

### REQ-HYP-008: JSON Output and Batch Organization

**User Story:** As a developer, I want hypotheses organized into manageable JSON batch files, so that I can process them efficiently in the fraud detection pipeline.

**Acceptance Criteria:**

* **AC-HYP-008.1:** The system shall save generated hypotheses as JSON files in the `output/hypotheses/` directory.
* **AC-HYP-008.2:** The system shall organize hypotheses into batch files of approximately 50-120 hypotheses each for efficient processing.
* **AC-HYP-008.3:** Each batch file shall be named `batch_XX.json` where XX is a zero-padded 2-digit batch number.
* **AC-HYP-008.4:** The JSON output shall be formatted with an indent of 2 for human readability.
* **AC-HYP-008.5:** The system shall log the count of hypotheses generated for each category and batch to enable verification.

### REQ-HYP-009: Hypothesis Validation

**User Story:** As a quality assurance analyst, I want the system to validate hypothesis counts and structure, so that I can ensure completeness and correctness before pipeline execution.

**Acceptance Criteria:**

* **AC-HYP-009.1:** The system shall verify that exactly 1,000 core hypotheses are generated (H0001-H1000).
* **AC-HYP-009.2:** The system shall verify that each category generates the expected number of hypotheses using assertions (Category 1 = 150, Category 2 = 120, Category 3 = 130, Category 4 = 120, Category 5 = 80, Category 6 = 150, Category 7 = 80, Category 8 = 100, Category 9 = 70, Category 10 = composite).
* **AC-HYP-009.3:** The system shall verify that gap analysis generates exactly 100 additional hypotheses (H1001-H1100).
* **AC-HYP-009.4:** The system shall validate that each hypothesis contains all required fields before writing to JSON.
* **AC-HYP-009.5:** The system shall report total generation time and hypothesis count upon completion.

## Feature Behavior & Rules

The hypothesis generation process is entirely deterministic and code-driven. Lists of codes (TOP_30_CODES, TOP_20_CODES), categories (HCPCS_CATEGORIES), metrics (IQR_METRICS), and specialties (SPECIALTIES) are defined as constants and used to parameterize hypothesis templates.

Each category's generation function (e.g., `gen_category_1()`, `gen_category_2()`) builds a list of hypothesis dictionaries and uses assertions to verify the expected count before returning. The sequential numbering is strictly maintained through the `h` variable that increments with each hypothesis.

SQL templates are included for some hypotheses to document the intended query logic, but the actual analysis is performed by Python analyzer classes. The `analysis_function` field references the module and method that will execute the hypothesis test (e.g., `statistical_analyzer._iqr_outlier`, `network_analyzer._billing_fan_out`).

Financial impact methods vary by hypothesis type: some calculate excess over peer median, others estimate total recoverable amounts, and some apply category-specific formulas. The `financial_impact_method` field is a human-readable string describing the calculation approach.

Gap analysis hypotheses address known high-risk domains identified through fraud research and stakeholder input. These include ABA therapy billing patterns, pharmacy fraud schemes, addiction treatment exploitation, genetic testing abuse, transportation fraud, and beneficiary-level anomalies. The gap analysis supplements the systematic core taxonomy with targeted domain expertise.

### Hypothesis Feasibility Matrix

## Overview

This feature evaluates each generated hypothesis for data feasibility and testability before pipeline execution. It produces a validation matrix that marks hypotheses as testable, not testable, or requiring data enrichment based on available data columns, row counts, peer group sizes, and temporal coverage. This prevents pipeline failures and provides a clear inventory of which detection methods can be executed with the current dataset.

Runs as Milestone 12 alongside hypothesis validation to ensure only viable hypotheses proceed to full analysis.

## Terminology

* **Feasibility Matrix**: A structured assessment of whether each hypothesis can be tested given current data availability and quality.
* **Testable Hypothesis**: A hypothesis with sufficient data coverage (required columns exist, minimum row counts met, peer groups adequate).
* **Data Enrichment Requirement**: Missing reference data or external sources needed to make a hypothesis testable.
* **Minimum Viable Peer Group**: The minimum number of providers needed for peer comparison hypotheses (typically 20-30).

## Requirements

### REQ-FEA-001: Data Coverage Assessment

**User Story:** As a pipeline administrator, I want the system to check data availability for each hypothesis, so that I can identify which detection methods are viable with current data.

**Acceptance Criteria:**

* **AC-FEA-001.1:** For each hypothesis, the system shall verify that all required data columns exist in the database schema.
* **AC-FEA-001.2:** The system shall calculate the number of providers or records available for testing each hypothesis.
* **AC-FEA-001.3:** The system shall mark a hypothesis as "testable" when data coverage exceeds minimum thresholds (&gt;100 rows for statistical tests, &gt;20 peers for peer comparisons).
* **AC-FEA-001.4:** The system shall mark a hypothesis as "not_testable" when required data is completely missing.
* **AC-FEA-001.5:** The system shall mark a hypothesis as "needs_enrichment" when the hypothesis is structurally valid but requires external reference data not yet loaded.

### REQ-FEA-002: Hypothesis Classification

**User Story:** As a data analyst, I want hypotheses classified by feasibility status, so that I can prioritize data enrichment efforts.

**Acceptance Criteria:**

* **AC-FEA-002.1:** The system shall classify each hypothesis into one of three categories: TESTABLE, NOT_TESTABLE, NEEDS_ENRICHMENT.
* **AC-FEA-002.2:** The system shall provide a reason code for each NOT_TESTABLE or NEEDS_ENRICHMENT classification (e.g., "missing_column", "insufficient_peers", "temporal_coverage_gap", "missing_nppes").
* **AC-FEA-002.3:** The system shall calculate the percentage of hypotheses that are testable within each analytical category (1-10).
* **AC-FEA-002.4:** The system shall identify which reference data sources would unlock the most currently non-testable hypotheses.

### REQ-FEA-003: Matrix Output Generation

**User Story:** As a fraud detection specialist, I want a feasibility matrix saved as CSV, so that I can review and plan hypothesis execution.

**Acceptance Criteria:**

* **AC-FEA-003.1:** The system shall generate a CSV file `hypothesis_feasibility_matrix.csv` with columns: hypothesis_id, category, subcategory, method, status, reason, available_records, min_required_records, peer_group_size.
* **AC-FEA-003.2:** The system shall generate a summary report `feasibility_summary.md` showing testable counts by category, top reasons for non-testability, and recommended enrichment priorities.
* **AC-FEA-003.3:** The system shall save both outputs to the `output/analysis/` directory.

### REQ-FEA-004: Pipeline Integration

**User Story:** As a developer, I want the feasibility matrix to inform pipeline execution, so that non-testable hypotheses are automatically skipped.

**Acceptance Criteria:**

* **AC-FEA-004.1:** The system shall load the feasibility matrix before hypothesis execution begins.
* **AC-FEA-004.2:** The system shall skip execution of any hypothesis marked NOT_TESTABLE or NEEDS_ENRICHMENT.
* **AC-FEA-004.3:** The system shall log skipped hypotheses with their reason codes for audit purposes.
* **AC-FEA-004.4:** The system shall report the count of testable, skipped, and enrichment-required hypotheses at pipeline start.

## Feature Behavior & Rules

The feasibility check examines both schema-level requirements (column existence) and data-level requirements (row counts, temporal coverage, peer group sizes). For peer comparison hypotheses, it validates that enough providers exist for meaningful statistical comparison. For temporal hypotheses, it checks that sufficient months of data exist to detect trends or change points.

The matrix is regenerated whenever the database schema changes or new reference data is loaded. Hypotheses initially marked NOT_TESTABLE may become testable after data enrichment. The feasibility status is advisory only and does not modify the hypothesis definitions themselves.

## Longitudinal and Panel Analysis

## Overview

Provide a clear and concise summary of the feature, explaining what it does and the value it delivers to the user. Describe the core problem this feature solves and how it fits into the overall product.

## Terminology

* **Key Term 1**: Brief description that ensures shared understanding across the team.
* **Key Term 2**: Definition that clarifies any ambiguity in how this concept is used.

## Requirements

### REQ-XXX-001: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-001.1:** When the user \[performs action\], the system shall \[respond with specific behavior\].
* **AC-XXX-001.2:** When \[condition exists\], the system shall \[handle appropriately\].
* **AC-XXX-001.N:** \[Continue for all acceptance criteria\]

### REQ-XXX-002: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-002.1:** When \[condition\], the system shall \[behavior\].
* **AC-XXX-002.2:** \[Continue for all acceptance criteria\]

## Feature Behavior & Rules

This section clarifies how the requirements behave in practice and how they interact. It explains cross-requirement interactions, defaults, constraints, and edge conditions without prescribing UI or user flows.

### Longitudinal Panel Construction

## Overview

This feature constructs longitudinal panel datasets aggregated by provider-month, state-month, specialty-month, and code-month to enable time-series analysis. It creates structured tables capturing billing dynamics across the full 84-month period (Jan 2018 - Dec 2024), computes growth rates and volatility metrics, and enables multivariate temporal pattern detection.

Runs as Milestone 13 in the pipeline and provides the foundation for advanced longitudinal analysis.

## Terminology

* **Panel Data**: Repeated observations of the same entities (providers, states, codes) over multiple time periods.
* **Provider-Month Record**: A single row capturing all billing activity for one provider in one calendar month.
* **Balanced Panel**: All entities present for all time periods (filled with zeros for inactive months).
* **Unbalanced Panel**: Only periods with actual billing activity are recorded.
* **Volatility Metric**: Standard deviation or coefficient of variation of monthly billing amounts over time.

## Requirements

### REQ-PANEL-001: Provider Monthly Panel Construction

**User Story:** As a data analyst, I want provider-level monthly panels, so that I can analyze temporal billing patterns for each provider.

**Acceptance Criteria:**

* **AC-PANEL-001.1:** The system shall create a `provider_monthly` table with columns: billing_npi, claim_month, total_paid, total_claims, total_beneficiaries, num_codes, avg_paid_per_claim, avg_claims_per_bene.
* **AC-PANEL-001.2:** The table shall contain one row per provider per month where the provider had any billing activity (unbalanced panel).
* **AC-PANEL-001.3:** The system shall calculate month-over-month growth rates as (current_paid - prior_paid) / prior_paid for each provider.
* **AC-PANEL-001.4:** The system shall calculate 12-month rolling statistics including mean, std, min, max, and coefficient of variation.
* **AC-PANEL-001.5:** The system shall save the panel as a DuckDB table and export the top 500 high-volatility providers to `longitudinal_provider_top500.csv`.

### REQ-PANEL-002: State and Specialty Aggregations

**User Story:** As a policy analyst, I want state and specialty temporal aggregations, so that I can analyze regional and specialty-specific trends.

**Acceptance Criteria:**

* **AC-PANEL-002.1:** The system shall create `state_monthly_totals` table with columns: state, claim_month, total_paid, total_claims, total_beneficiaries, num_providers.
* **AC-PANEL-002.2:** The system shall create `specialty_monthly_totals` table with columns: specialty, claim_month, total_paid, total_claims, total_beneficiaries, num_providers.
* **AC-PANEL-002.3:** For states and specialties, the system shall calculate year-over-year growth rates comparing each month to the same month in the prior year.
* **AC-PANEL-002.4:** The system shall export both tables to CSV in `output/analysis/`.

### REQ-PANEL-003: Code Monthly Aggregations

**User Story:** As a utilization analyst, I want HCPCS code temporal aggregations, so that I can track service-specific utilization trends.

**Acceptance Criteria:**

* **AC-PANEL-003.1:** The system shall create `code_monthly_totals` table with columns: hcpcs_code, claim_month, total_paid, total_claims, num_providers, avg_paid_per_claim.
* **AC-PANEL-003.2:** The system shall track monthly entry and exit of providers per code (new providers billing the code, providers who stopped).
* **AC-PANEL-003.3:** The system shall export the top 200 codes by total spending to `code_monthly_totals_top200.csv`.

### REQ-PANEL-004: Time Series Feature Engineering

**User Story:** As a data scientist, I want temporal features calculated, so that I can use them in predictive models and anomaly detection.

**Acceptance Criteria:**

* **AC-PANEL-004.1:** For each provider, the system shall calculate temporal features including first_month, last_month, months_active, months_inactive_between, longest_continuous_run, max_month_paid, min_month_paid.
* **AC-PANEL-004.2:** The system shall calculate Hurst exponent (measure of time series persistence) for providers with 24+ months of data.
* **AC-PANEL-004.3:** The system shall identify change points using CUSUM or PELT algorithms and record the change point month and magnitude for each provider.
* **AC-PANEL-004.4:** The system shall save temporal features to `provider_temporal_features` table.

## Feature Behavior & Rules

Panel construction uses window functions and self-joins to calculate prior-month and rolling statistics efficiently. Months with zero billing are not included in the unbalanced panel but are accounted for in months_active calculations. Growth rate calculations handle division by zero (prior month = 0) by setting growth to NULL or infinity marker. State and specialty aggregations join with the providers table to enrich with metadata. Code panels track market dynamics including provider entry/exit rates.

### Multivariate Temporal Analysis

## Overview

This feature performs multivariate time series analysis on longitudinal panel data to detect temporal anomalies not visible in single-period snapshots. It fits regression models to predict paid-per-claim from provider characteristics, identifies residual outliers, detects non-linear growth patterns, and calculates multivariate risk scores combining temporal and cross-sectional signals.

Runs as part of Milestone 13 and produces advanced temporal findings for validation.

## Terminology

* **Paid-Per-Claim Residual**: The difference between actual and predicted paid-per-claim after controlling for provider characteristics.
* **Non-Linear Growth**: Acceleration or deceleration in billing growth over time (e.g., quadratic or exponential patterns).
* **Vector Autoregression (VAR)**: Multivariate time series model capturing interdependencies between multiple variables.
* **Granger Causality**: Statistical test determining whether one time series helps predict another.
* **Multivariate Risk Score**: Composite score combining temporal volatility, growth anomalies, and residual outliers.

## Requirements

### REQ-MULTI-001: Paid-Per-Claim Regression and Residuals

**User Story:** As a statistician, I want residual analysis, so that I can identify providers with unexplained billing patterns after controlling for observable factors.

**Acceptance Criteria:**

* **AC-MULTI-001.1:** The system shall fit an OLS regression model predicting paid_per_claim from specialty, state, num_codes, claims_per_bene, and num_months.
* **AC-MULTI-001.2:** The system shall calculate residuals for each provider-month observation.
* **AC-MULTI-001.3:** The system shall flag provider-months with |residual| &gt; 3 \* residual_std as outliers.
* **AC-MULTI-001.4:** The system shall aggregate provider-level residual outlier counts and save the top 500 to `ppc_residuals_top500.csv`.
* **AC-MULTI-001.5:** Residual outliers shall be annotated with the predicted value, actual value, and standardized residual.

### REQ-MULTI-002: Growth Pattern Detection

**User Story:** As a fraud analyst, I want non-linear growth detection, so that I can identify providers with accelerating or suspicious growth trajectories.

**Acceptance Criteria:**

* **AC-MULTI-002.1:** The system shall fit quadratic time trends (month, month²) to each provider's monthly billing series with 12+ months of data.
* **AC-MULTI-002.2:** The system shall flag providers with significant positive quadratic coefficients (p < 0.01) indicating accelerating growth.
* **AC-MULTI-002.3:** The system shall calculate CAGR (Compound Annual Growth Rate) for each provider over the full 84-month period.
* **AC-MULTI-002.4:** The system shall flag providers with CAGR &gt; 100% (doubling annually) and save to `growth_anomalies_top500.csv`.

### REQ-MULTI-003: Volatility and Stability Analysis

**User Story:** As a risk manager, I want volatility metrics, so that I can identify erratic billing patterns indicative of fraud or instability.

**Acceptance Criteria:**

* **AC-MULTI-003.1:** The system shall calculate coefficient of variation (CV = std / mean) for each provider's monthly paid series.
* **AC-MULTI-003.2:** The system shall flag providers with CV &gt; 2.0 (high volatility) and CV < 0.1 (suspiciously stable).
* **AC-MULTI-003.3:** The system shall calculate the number of months with zero billing (gaps) and flag providers with gaps &gt; 6 months followed by resumption.
* **AC-MULTI-003.4:** The system shall detect alternating high/low billing patterns using autocorrelation analysis.

### REQ-MULTI-004: Multivariate Risk Scoring

**User Story:** As a data scientist, I want multivariate risk scores, so that I can rank providers by combined temporal and cross-sectional anomalies.

**Acceptance Criteria:**

* **AC-MULTI-004.1:** The system shall calculate a multivariate_risk_score combining: residual_outlier_count \* 1.0 + |growth_anomaly_score| \* 0.5 + volatility_zscore \* 0.3 + gap_penalty \* 0.2.
* **AC-MULTI-004.2:** The system shall rank all providers by multivariate_risk_score and save the top 500 to `multivariate_risk_top500.csv`.
* **AC-MULTI-004.3:** The system shall calculate correlation between multivariate_risk_score and findings from Categories 1-9 to validate predictive power.
* **AC-MULTI-004.4:** The system shall generate a summary report `longitudinal_multivariate_report.md` with key findings, time range, total spending, top states, top specialties, and top codes.

### REQ-MULTI-005: Output Integration

**User Story:** As a pipeline orchestrator, I want multivariate findings integrated, so that they inform final validation and risk prioritization.

**Acceptance Criteria:**

* **AC-MULTI-005.1:** The system shall save all multivariate findings (residual outliers, growth anomalies, volatility flags) to structured tables in DuckDB.
* **AC-MULTI-005.2:** The system shall export summary CSVs to `output/analysis/` directory.
* **AC-MULTI-005.3:** The system shall provide a lookup function for downstream milestones to query multivariate risk scores by NPI.
* **AC-MULTI-005.4:** The system shall log execution time and record counts for all multivariate analysis components.

## Feature Behavior & Rules

Multivariate analysis requires the longitudinal panel constructed in the prior milestone. Regression models use statsmodels OLS. Residuals are studentized for outlier detection. Growth pattern detection uses polynomial regression via numpy.polyfit. Autocorrelation uses pandas autocorr(). Providers with fewer than 12 months of data are excluded from growth pattern analysis but included in residual analysis. Multivariate risk scores are normalized to 0-100 scale for comparability. The report includes time range, aggregate statistics, and identifies the top states, specialties, and HCPCS codes by total spending.

## Validation and Calibration

## Overview

Provide a clear and concise summary of the feature, explaining what it does and the value it delivers to the user. Describe the core problem this feature solves and how it fits into the overall product.

## Terminology

* **Key Term 1**: Brief description that ensures shared understanding across the team.
* **Key Term 2**: Definition that clarifies any ambiguity in how this concept is used.

## Requirements

### REQ-XXX-001: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-001.1:** When the user \[performs action\], the system shall \[respond with specific behavior\].
* **AC-XXX-001.2:** When \[condition exists\], the system shall \[handle appropriately\].
* **AC-XXX-001.N:** \[Continue for all acceptance criteria\]

### REQ-XXX-002: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-002.1:** When \[condition\], the system shall \[behavior\].
* **AC-XXX-002.2:** \[Continue for all acceptance criteria\]

## Feature Behavior & Rules

This section clarifies how the requirements behave in practice and how they interact. It explains cross-requirement interactions, defaults, constraints, and edge conditions without prescribing UI or user flows.

### Holdout Validation and Calibration

## Overview

This feature validates hypothesis performance using holdout temporal validation and calibrates confidence scores based on precision metrics. It tests hypotheses on the most recent 6 months of data after training on prior periods, calculates precision at various confidence thresholds, and adjusts confidence scores to align with actual positive predictive values.

Runs as Milestone 14 and ensures detection methods are validated before final scoring.

## Terminology

* **Holdout Validation**: Testing hypotheses on recent data not used during hypothesis design to measure true performance.
* **Precision**: The proportion of flagged providers that are true positives (TP / (TP + FP)).
* **Calibration**: Adjusting confidence scores so that a 0.80 confidence score means 80% precision.
* **Temporal Split**: Using last 6 months as validation set and prior 78 months as training/analysis set.
* **Confidence Tier Precision**: Measured precision for HIGH (&gt;= 0.85), MEDIUM (0.65-0.84), and LOW (< 0.65) confidence tiers.

## Requirements

### REQ-VAL-001: Temporal Holdout Set Creation

**User Story:** As a data scientist, I want temporal holdout validation, so that I can measure hypothesis performance on unseen recent data.

**Acceptance Criteria:**

* **AC-VAL-001.1:** The system shall designate the last 6 months (Jul 2024 - Dec 2024) as the holdout validation set.
* **AC-VAL-001.2:** The system shall re-execute all testable hypotheses on the holdout period only.
* **AC-VAL-001.3:** The system shall compare holdout findings to full-period findings to identify hypothesis stability.
* **AC-VAL-001.4:** The system shall calculate per-hypothesis precision using known high-confidence findings from full period as ground truth approximation.

### REQ-VAL-002: Precision Calculation

**User Story:** As a fraud investigator, I want precision metrics, so that I understand the false positive rate of each detection method.

**Acceptance Criteria:**

* **AC-VAL-002.1:** For each hypothesis, the system shall calculate precision as: (num flagged in both full and holdout) / (num flagged in holdout).
* **AC-VAL-002.2:** The system shall calculate precision by confidence tier: HIGH, MEDIUM, LOW.
* **AC-VAL-002.3:** The system shall flag hypotheses with precision < 0.50 as "high_false_positive_rate".
* **AC-VAL-002.4:** The system shall save precision metrics to `validation_precision_by_hypothesis.csv` with columns: hypothesis_id, method, holdout_findings, full_period_findings, overlap, precision, confidence_tier_precision.

### REQ-VAL-003: Confidence Score Calibration

**User Story:** As a risk manager, I want calibrated confidence scores, so that a score accurately reflects the likelihood of true fraud.

**Acceptance Criteria:**

* **AC-VAL-003.1:** The system shall calculate the gap between nominal confidence scores and measured precision for each method.
* **AC-VAL-003.2:** The system shall apply calibration adjustments reducing confidence scores for methods with precision < nominal confidence.
* **AC-VAL-003.3:** The system shall not increase confidence scores during calibration (conservative approach).
* **AC-VAL-003.4:** The system shall save calibrated confidence scores to a lookup table for use in final scoring.
* **AC-VAL-003.5:** The system shall generate a calibration report `confidence_calibration_report.md` showing before/after precision and recommended adjustments.

### REQ-VAL-004: Hypothesis Performance Ranking

**User Story:** As a pipeline administrator, I want hypotheses ranked by validation performance, so that I can prioritize effective detection methods.

**Acceptance Criteria:**

* **AC-VAL-004.1:** The system shall rank hypotheses by validation performance score = precision \* finding_count \* avg_impact.
* **AC-VAL-004.2:** The system shall identify top 20 best-performing hypotheses and bottom 20 worst-performing hypotheses.
* **AC-VAL-004.3:** The system shall recommend hypotheses for retirement (precision < 0.30 consistently) or enhanced tuning.
* **AC-VAL-004.4:** The system shall save rankings to `hypothesis_performance_ranking.csv`.

## Feature Behavior & Rules

Holdout validation assumes the most recent 6 months are representative of future data. Precision calculation treats multi-method flagging as positive signal. Calibration uses isotonic regression or linear scaling. Hypotheses with fewer than 10 findings in holdout are marked as insufficient_sample. State-specific and code-specific hypotheses may have lower precision due to parameter specificity. Network and temporal hypotheses tend to have higher precision than pure statistical outliers.

### Hypothesis Validation Summary

## Overview

This feature aggregates validation results across all executed hypotheses to produce a summary report showing which detection methods produced findings, their precision, finding counts, total financial impact, and effectiveness rankings. It identifies which analytical categories and methods were most productive and which produced zero or low-value findings.

Runs as Milestone 12 and informs method selection for future analyses.

## Terminology

* **Hypothesis Validation**: Assessment of whether a hypothesis produced any findings and the quality of those findings.
* **Method Effectiveness**: Measured by finding count, total impact, precision, and overlap with other methods.
* **Zero-Finding Hypothesis**: A hypothesis that executed successfully but flagged zero providers.
* **Pruned Method**: A hypothesis recommended for removal due to zero findings or very low precision.

## Requirements

### REQ-HVAL-001: Finding Count Aggregation

**User Story:** As a program manager, I want finding counts by hypothesis, so that I can see which detection methods produced results.

**Acceptance Criteria:**

* **AC-HVAL-001.1:** The system shall aggregate finding counts for each hypothesis across all execution milestones.
* **AC-HVAL-001.2:** The system shall calculate total findings, unique providers flagged, and total financial impact per hypothesis.
* **AC-HVAL-001.3:** The system shall identify hypotheses with zero findings and mark them as "zero_finding".
* **AC-HVAL-001.4:** The system shall save aggregated counts to `hypothesis_validation_summary.md` with sections for each category (1-10).

### REQ-HVAL-002: Method Effectiveness Ranking

**User Story:** As a fraud detection specialist, I want methods ranked by effectiveness, so that I can focus on high-yield detection approaches.

**Acceptance Criteria:**

* **AC-HVAL-002.1:** The system shall rank detection methods by total financial impact across all hypotheses using that method.
* **AC-HVAL-002.2:** The system shall calculate average precision per method using validation results.
* **AC-HVAL-002.3:** The system shall identify the top 10 methods by impact and top 10 by finding count.
* **AC-HVAL-002.4:** The system shall save method rankings to `method_effectiveness_ranking.csv` with columns: method, num_hypotheses, total_findings, total_impact, avg_precision, rank.

### REQ-HVAL-003: Category Performance Analysis

**User Story:** As a data analyst, I want category-level summaries, so that I can understand which analytical paradigms worked best.

**Acceptance Criteria:**

* **AC-HVAL-003.1:** The system shall aggregate findings by analytical category (1 = Statistical, 2 = Temporal, etc.).
* **AC-HVAL-003.2:** For each category, the system shall calculate total hypotheses, testable hypotheses, hypotheses with findings, total findings, and total impact.
* **AC-HVAL-003.3:** The system shall calculate category effectiveness ratio = (hypotheses with findings) / (testable hypotheses).
* **AC-HVAL-003.4:** The system shall identify the most and least effective categories and include analysis in the summary report.

### REQ-HVAL-004: Pruning Recommendations

**User Story:** As a pipeline administrator, I want pruning recommendations, so that I can remove ineffective hypotheses from future runs.

**Acceptance Criteria:**

* **AC-HVAL-004.1:** The system shall recommend pruning for hypotheses with zero findings across two consecutive runs.
* **AC-HVAL-004.2:** The system shall recommend pruning for hypotheses with precision < 0.20 in validation.
* **AC-HVAL-004.3:** The system shall save the pruned hypothesis list to `pruned_methods.csv` with rationale.
* **AC-HVAL-004.4:** The system shall estimate the computational savings from pruning (execution time reduction).

### REQ-HVAL-005: Summary Report Generation

**User Story:** As a stakeholder, I want a validation summary report, so that I can understand overall pipeline performance.

**Acceptance Criteria:**

* **AC-HVAL-005.1:** The system shall generate `hypothesis_validation_summary.md` with sections: executive summary, findings by category, method rankings, pruning recommendations, and data quality notes.
* **AC-HVAL-005.2:** The summary shall include total hypotheses executed, total findings produced, total estimated recoverable, and precision by confidence tier.
* **AC-HVAL-005.3:** The summary shall include charts or tables showing category distribution of findings and method contribution to total impact.

## Feature Behavior & Rules

Validation summary aggregates data from findings files produced in Milestones 5-8. Zero-finding hypotheses are not necessarily failures—they may indicate clean data for that pattern. Method effectiveness considers both precision and impact magnitude. Categories with many zero-finding hypotheses suggest parameter tuning is needed. The summary is generated after validation and before final impact quantification.

### Provider Validation Scores

## Overview

This feature calculates comprehensive validation scores for each flagged provider combining multiple signal types: number of detection methods, confidence scores, financial impact, temporal persistence, network position, and external validation flags. It produces a single 0-100 provider_validation_score used for final risk ranking.

Runs as Milestone 23 and creates the authoritative provider risk score.

## Terminology

* **Provider Validation Score**: Composite 0-100 score reflecting fraud likelihood based on multiple evidence dimensions.
* **Signal Diversity**: Number of distinct detection categories (1-10) that flagged a provider.
* **Temporal Persistence**: Provider flagged in multiple time periods or with sustained anomalous patterns.
* **Network Centrality**: Provider's position in billing network (hub status, shared servicing, circular billing involvement).
* **External Validation**: Matches with LEIE, NPPES deactivations, specialty mismatches, or licensure issues.

## Requirements

### REQ-PVAL-001: Multi-Signal Scoring

**User Story:** As a fraud analyst, I want providers scored on multiple dimensions, so that I can identify those with strongest evidence.

**Acceptance Criteria:**

* **AC-PVAL-001.1:** The system shall calculate signal_diversity_score = min(30, num_methods \* 6) where num_methods is count of distinct categories (1-10) that flagged the provider.
* **AC-PVAL-001.2:** The system shall calculate confidence_score_component = avg(confidence scores across all findings for provider) \* 20.
* **AC-PVAL-001.3:** The system shall calculate impact_score_component = min(20, log10(total_impact) \* 3) normalized to 0-20 scale.
* **AC-PVAL-001.4:** The system shall calculate temporal_persistence_score = min(15, months_flagged \* 2) where months_flagged counts distinct months with anomalous activity.

### REQ-PVAL-002: Network and External Validation Scoring

**User Story:** As a network analyst, I want network position factored into scores, so that hub providers and network members are elevated.

**Acceptance Criteria:**

* **AC-PVAL-002.1:** The system shall calculate network_centrality_score = min(10, hub_servicing_count / 10) + (5 if in_circular_billing else 0) + (3 if pure_billing_entity else 0).
* **AC-PVAL-002.2:** The system shall calculate external_validation_score = (10 if LEIE_match else 0) + (8 if no_NPPES else 0) + (5 if deactivated_NPI else 0) + (5 if specialty_mismatch else 0).
* **AC-PVAL-002.3:** The system shall cap external_validation_score at 15 points maximum.

### REQ-PVAL-003: Composite Score Calculation

**User Story:** As a risk manager, I want a single composite score, so that I can rank all providers uniformly.

**Acceptance Criteria:**

* **AC-PVAL-003.1:** The system shall calculate provider_validation_score = signal_diversity_score (30 pts) + confidence_score_component (20 pts) + impact_score_component (20 pts) + temporal_persistence_score (15 pts) + network_centrality_score (10 pts) + external_validation_score (15 pts) - penalties.
* **AC-PVAL-003.2:** The system shall apply a -10 point penalty for single-method detections with confidence < 0.70.
* **AC-PVAL-003.3:** The system shall apply a +5 point bonus for providers flagged by domain rules (Category 8) indicating deterministic violations.
* **AC-PVAL-003.4:** The system shall normalize final scores to 0-100 range and save to `provider_validation_scores.csv` with columns: npi, name, state, provider_validation_score, signal_diversity, confidence_avg, total_impact, num_methods, external_flags.

### REQ-PVAL-004: Risk Tier Classification

**User Story:** As an investigator, I want providers classified into risk tiers, so that I can prioritize investigations.

**Acceptance Criteria:**

* **AC-PVAL-004.1:** The system shall classify providers into risk tiers: CRITICAL (score &gt;= 80), HIGH (65-79), MEDIUM (50-64), LOW (< 50).
* **AC-PVAL-004.2:** The system shall calculate the distribution of providers across risk tiers.
* **AC-PVAL-004.3:** The system shall flag CRITICAL tier providers for immediate review and save to `critical_risk_providers.csv`.
* **AC-PVAL-004.4:** The system shall generate a score distribution histogram showing provider counts by score decile.

### REQ-PVAL-005: Validation Score Report

**User Story:** As a program manager, I want a validation scoring report, so that I understand the risk profile of flagged providers.

**Acceptance Criteria:**

* **AC-PVAL-005.1:** The system shall generate `provider_validation_scoring_report.md` with sections: scoring methodology, score distribution, risk tier statistics, top 100 providers by score, and external validation match rates.
* **AC-PVAL-005.2:** The report shall include summary statistics: median score, mean score, score standard deviation, and correlation between score and financial impact.

## Feature Behavior & Rules

Provider validation scores are calculated only for providers flagged by at least one hypothesis. Unflagged providers are not scored. Signal diversity is the strongest component (30 points) reflecting the principle that multi-method detections are most reliable. Temporal persistence requires linking findings across the longitudinal panel. Network centrality uses network analysis results from Category 4. External validation requires NPPES/LEIE data. Scores are recalculated if new findings are added or validation results change.

## Impact Quantification and Risk Prioritization

## Overview

Provide a clear and concise summary of the feature, explaining what it does and the value it delivers to the user. Describe the core problem this feature solves and how it fits into the overall product.

## Terminology

* **Key Term 1**: Brief description that ensures shared understanding across the team.
* **Key Term 2**: Definition that clarifies any ambiguity in how this concept is used.

## Requirements

### REQ-XXX-001: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-001.1:** When the user \[performs action\], the system shall \[respond with specific behavior\].
* **AC-XXX-001.2:** When \[condition exists\], the system shall \[handle appropriately\].
* **AC-XXX-001.N:** \[Continue for all acceptance criteria\]

### REQ-XXX-002: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-002.1:** When \[condition\], the system shall \[behavior\].
* **AC-XXX-002.2:** \[Continue for all acceptance criteria\]

## Feature Behavior & Rules

This section clarifies how the requirements behave in practice and how they interact. It explains cross-requirement interactions, defaults, constraints, and edge conditions without prescribing UI or user flows.

### State Quality Weighting

## Overview

This feature assigns data quality weights to each state based on completeness, consistency, and reliability metrics calculated during the DQ Atlas assessment. It adjusts financial impact estimates by state quality weights to produce quality-weighted recoverable amounts that reflect confidence in the underlying data.

Runs as Milestone 15 and refines impact estimates based on data quality.

## Terminology

* **State Quality Weight**: A 0-1 multiplier reflecting data completeness and consistency for each state.
* **DQ Atlas**: Data quality assessment framework evaluating completeness, consistency, validity, and timeliness.
* **Quality-Weighted Impact**: Financial impact estimate adjusted by state quality weight to reflect data reliability.
* **Completeness Score**: Percentage of expected fields populated (non-null) for a state's claims.
* **Consistency Score**: Degree of internal consistency (e.g., paid &gt;= 0, claims <= physically possible, dates in valid ranges).

## Requirements

### REQ-SQW-001: State Data Quality Assessment

**User Story:** As a data quality analyst, I want state-level quality scores, so that I can understand data reliability by jurisdiction.

**Acceptance Criteria:**

* **AC-SQW-001.1:** The system shall calculate completeness_score per state as the percentage of non-null values across key fields (servicing_npi, beneficiaries, hcpcs_code).
* **AC-SQW-001.2:** The system shall calculate consistency_score per state as the percentage of records passing validation rules (paid &gt;= 0, claims &gt; 0, valid dates, known HCPCS codes).
* **AC-SQW-001.3:** The system shall calculate coverage_score per state as (actual_months_with_data / 84) for the full 2018-2024 period.
* **AC-SQW-001.4:** The system shall calculate outlier_score per state as 1 - (outlier_rate) where outlier_rate is the percentage of records with impossible values.

### REQ-SQW-002: Quality Weight Calculation

**User Story:** As a financial analyst, I want composite quality weights, so that I can adjust impact estimates appropriately.

**Acceptance Criteria:**

* **AC-SQW-002.1:** The system shall calculate state_quality_weight = (completeness_score \* 0.35) + (consistency_score \* 0.35) + (coverage_score \* 0.20) + (outlier_score \* 0.10).
* **AC-SQW-002.2:** The system shall normalize quality weights to 0.5 - 1.0 range (never below 0.5 to avoid over-discounting).
* **AC-SQW-002.3:** The system shall flag states with quality_weight < 0.70 as "low_quality_data" for analyst review.
* **AC-SQW-002.4:** The system shall save quality weights to `state_quality_weights.csv` with columns: state, completeness_score, consistency_score, coverage_score, outlier_score, quality_weight, quality_tier.

### REQ-SQW-003: Impact Adjustment Application

**User Story:** As a program integrity officer, I want impacts adjusted by data quality, so that estimates reflect confidence levels.

**Acceptance Criteria:**

* **AC-SQW-003.1:** For each finding, the system shall apply the state quality weight: quality_weighted_impact = total_impact \* state_quality_weight\[provider_state\].
* **AC-SQW-003.2:** The system shall recalculate aggregate financial impact across all findings using quality-weighted values.
* **AC-SQW-003.3:** The system shall save both raw and quality-weighted impacts in all downstream reports and exports.
* **AC-SQW-003.4:** The system shall calculate the total adjustment amount: sum(total_impact) - sum(quality_weighted_impact).

### REQ-SQW-004: Quality Tier Reporting

**User Story:** As a stakeholder, I want to see findings segmented by data quality, so that I understand confidence in different state portfolios.

**Acceptance Criteria:**

* **AC-SQW-004.1:** The system shall create quality tiers: GOLD (weight &gt;= 0.90), SILVER (0.80-0.89), BRONZE (0.70-0.79), NEEDS_IMPROVEMENT (< 0.70).
* **AC-SQW-004.2:** The system shall aggregate findings and impact by quality tier.
* **AC-SQW-004.3:** The system shall generate `state_quality_impact_report.md` showing findings and impact by state and quality tier.
* **AC-SQW-004.4:** The report shall include recommendations for states requiring data quality improvement efforts.

## Feature Behavior & Rules

State quality weights are calculated once per pipeline run using the full dataset. Quality assessment uses the DQ_SCAN results from Milestone 0 if available. States with fewer than 1000 total claims are automatically assigned a 0.60 weight. Quality weights apply multiplicatively to financial impacts but do not affect confidence scores or detection logic. Low-quality states may produce findings, but impacts are discounted. The adjustment is conservative—even low-quality data receives at least 50% weight.

### Financial Impact and Deduplication

## Overview

This feature deduplicates overlapping financial impact estimates across multiple hypotheses flagging the same provider and calculates final standardized provider-level recoverable amounts. It handles scenarios where different detection methods identify the same anomalous spending through different analytical lenses and ensures total impact is not double-counted.

Runs as Milestone 9 and produces the authoritative financial impact figures.

## Terminology

* **Impact Deduplication**: Removing overlapping financial impact when multiple hypotheses flag the same provider dollars.
* **Provider-Level Impact**: Single standardized estimate of recoverable amount per provider across all detection methods.
* **State/Code Aggregates**: Systemic exposure estimates for rate policy issues affecting entire markets.
* **Overlap Factor**: The degree to which multiple methods flag the same underlying spending.

## Requirements

### REQ-FIN-001: Overlap Detection and Quantification

**User Story:** As a financial analyst, I want overlap between methods quantified, so that I understand which methods detect the same vs. distinct issues.

**Acceptance Criteria:**

* **AC-FIN-001.1:** For each provider, the system shall identify all hypothesis findings and their associated financial impacts.
* **AC-FIN-001.2:** The system shall calculate pairwise overlap between methods as the percentage of flagged dollars detected by both methods.
* **AC-FIN-001.3:** The system shall create an overlap matrix showing which method pairs have high correlation (&gt; 80% overlap).
* **AC-FIN-001.4:** The system shall save the overlap matrix to `method_overlap_matrix.csv`.

### REQ-FIN-002: Provider-Level Deduplication

**User Story:** As a program integrity director, I want deduplicated provider-level impacts, so that I can report accurate total recoverable amounts.

**Acceptance Criteria:**

* **AC-FIN-002.1:** For each provider, the system shall take the maximum single-method impact as the baseline (conservative approach).
* **AC-FIN-002.2:** If multiple independent methods (< 50% overlap) flag the provider, the system shall sum 70% of additional method impacts to account for partial additivity.
* **AC-FIN-002.3:** The system shall cap provider-level impact at the provider's total_paid to prevent impossible estimates.
* **AC-FIN-002.4:** The system shall save deduplicated impacts to `deduplicated_provider_impacts.csv` with columns: npi, name, state, num_methods, raw_impact_sum, deduplicated_impact, total_paid, impact_ratio.

### REQ-FIN-003: Systemic vs. Provider-Level Separation

**User Story:** As a policy analyst, I want systemic rate issues separated from provider-level fraud, so that I can recommend appropriate interventions.

**Acceptance Criteria:**

* **AC-FIN-003.1:** The system shall classify findings as "provider_level" (specific NPI anomalies) or "systemic" (state/code rate issues affecting many providers).
* **AC-FIN-003.2:** For systemic findings (e.g., state-level HHI concentration, geographic monopolies), the system shall aggregate impact at state/code level rather than provider level.
* **AC-FIN-003.3:** The system shall save systemic findings separately to `systemic_policy_issues.csv`.
* **AC-FIN-003.4:** The system shall report total provider-level recoverable and total systemic exposure separately.

### REQ-FIN-004: Impact Attribution and Breakdown

**User Story:** As an investigator, I want to see which methods contributed to each provider's total impact, so that I understand the evidence basis.

**Acceptance Criteria:**

* **AC-FIN-004.1:** For each provider, the system shall save a breakdown showing: total_deduplicated_impact, method_contributions (list of methods with their raw impacts), deduplication_adjustment_amount.
* **AC-FIN-004.2:** The system shall calculate method_contribution_percentages showing how much each method added to the final impact.
* **AC-FIN-004.3:** The system shall save detailed breakdowns to `provider_impact_breakdown.json`.

### REQ-FIN-005: Final Impact Summary

**User Story:** As a stakeholder, I want a financial impact summary, so that I understand the total fraud exposure detected.

**Acceptance Criteria:**

* **AC-FIN-005.1:** The system shall generate `financial_impact_summary.md` with sections: total raw impact, deduplication adjustment, final deduplicated impact, systemic exposure, quality-weighted impact, and top 10 states/methods by impact.
* **AC-FIN-005.2:** The summary shall include impact distribution statistics: mean, median, P95, P99 provider-level impacts.
* **AC-FIN-005.3:** The summary shall report the deduplication rate: (raw_sum - deduplicated_sum) / raw_sum.

## Feature Behavior & Rules

Deduplication uses the maximum single-method impact as baseline to avoid underestimation. Additional methods contribute 70% of their impact unless they are highly correlated (&gt;80% overlap), in which case contribution is 0%. State/code systemic findings are never deduplicated against provider findings. Impact caps at total_paid prevent impossible claims. The deduplication algorithm is conservative, preferring to underestimate rather than overestimate recoverable amounts. Quality weights are applied after deduplication.

### Risk Queue Generation

## Overview

This feature generates prioritized investigation queues by ranking flagged providers using provider_validation_scores, dedu plicated financial impacts, confidence tiers, and investigative resource constraints. It produces the top 500 providers for investigation along with supporting evidence packages and recommended investigation sequences.

Runs as Milestone 16 and creates the actionable investigation work queue.

## Terminology

* **Risk Queue**: Priority-ranked list of providers recommended for investigation based on composite risk scoring.
* **Investigation Package**: Consolidated evidence dossier for a provider including all findings, methods, impacts, and external validation flags.
* **Resource Constraints**: Investigator capacity, expected hours per case, and budget limitations.
* **Queue Segmentation**: Dividing the risk queue into HIGH/MEDIUM/LOW priority tiers for resource allocation.

## Requirements

### REQ-QUEUE-001: Provider Ranking and Selection

**User Story:** As an investigation manager, I want providers ranked by risk, so that I can allocate investigative resources optimally.

**Acceptance Criteria:**

* **AC-QUEUE-001.1:** The system shall rank all flagged providers by provider_validation_score (primary) and quality_weighted_impact (secondary).
* **AC-QUEUE-001.2:** The system shall select the top 500 providers for the investigation queue.
* **AC-QUEUE-001.3:** The system shall ensure geographic diversity: no more than 30% of the queue from any single state unless justified by concentration of fraud.
* **AC-QUEUE-001.4:** The system shall save the risk queue to `risk_queue_top500.csv` with columns: rank, npi, name, state, specialty, provider_validation_score, quality_weighted_impact, num_methods, confidence_tier, external_flags.

### REQ-QUEUE-002: Evidence Package Assembly

**User Story:** As an investigator, I want consolidated evidence packages, so that I have all relevant information for each case.

**Acceptance Criteria:**

* **AC-QUEUE-002.1:** For each provider in the queue, the system shall create an evidence package containing: all findings (hypothesis IDs, methods, evidence strings), financial impact breakdown, temporal profile (months active, growth patterns), network position (hubs connected, servicing relationships), and external validation results (NPPES, LEIE, specialty).
* **AC-QUEUE-002.2:** The system shall save evidence packages to `risk_queue_packages/` directory with one JSON file per provider: `{npi}_evidence_package.json`.
* **AC-QUEUE-002.3:** The system shall generate a one-page summary PDF for each top 100 provider highlighting key red flags.

### REQ-QUEUE-003: Priority Tier Assignment

**User Story:** As a program manager, I want cases segmented by priority, so that I can assign appropriate investigative resources.

**Acceptance Criteria:**

* **AC-QUEUE-003.1:** The system shall assign priority tiers: IMMEDIATE (rank 1-50, validation_score &gt;= 80), HIGH (rank 51-200, validation_score &gt;= 65), MEDIUM (rank 201-400), REVIEW (rank 401-500).
* **AC-QUEUE-003.2:** The system shall estimate investigation hours per tier: IMMEDIATE = 40 hours, HIGH = 20 hours, MEDIUM = 10 hours, REVIEW = 5 hours.
* **AC-QUEUE-003.3:** The system shall calculate total investigative capacity needed and report it in the queue summary.
* **AC-QUEUE-003.4:** The system shall flag providers requiring specialized expertise (network analysis, clinical review, complex schemes).

### REQ-QUEUE-004: Investigation Sequence Recommendation

**User Story:** As an investigation director, I want a recommended investigation sequence, so that I can maximize early detection wins.

**Acceptance Criteria:**

* **AC-QUEUE-004.1:** The system shall recommend starting with providers having external validation flags (LEIE, deactivated NPI) for quick wins.
* **AC-QUEUE-004.2:** The system shall group network-related cases (hubs, spokes, circular billing rings) for coordinated investigation.
* **AC-QUEUE-004.3:** The system shall identify "gateway" providers whose investigation would unlock evidence for connected entities.
* **AC-QUEUE-004.4:** The system shall save the investigation sequence to `investigation_sequence_recommended.csv`.

### REQ-QUEUE-005: Queue Summary Report

**User Story:** As a stakeholder, I want a risk queue summary, so that I understand the scope and composition of recommended investigations.

**Acceptance Criteria:**

* **AC-QUEUE-005.1:** The system shall generate `risk_queue_summary.md` with sections: total providers in queue, priority tier distribution, total estimated recoverable, top 10 states, top 10 methods, external validation statistics.
* **AC-QUEUE-005.2:** The summary shall include resource estimates: total investigative hours needed, estimated duration at various staffing levels.
* **AC-QUEUE-005.3:** The summary shall highlight the top 20 providers with brief justifications for immediate action.

## Feature Behavior & Rules

Risk queue generation uses provider_validation_scores calculated in Milestone 23. Geographic diversity constraints prevent over-concentration in single states but can be overridden for major fraud rings. Evidence packages are self-contained JSON files that can be loaded by investigation management systems. Priority tiers map to investigation protocols and resource allocation policies. Network-related cases are flagged for coordinated investigation to prevent evidence destruction or entity dissolution. The queue is refreshed if new findings are added or scores are recalculated.

### Fraud Pattern Classification

## Overview

This feature classifies detected fraud into 10 distinct pattern categories based on the methods that flagged each provider and the characteristics of the anomalous behavior. It produces a taxonomy of fraud schemes with provider counts, financial impacts, and pattern descriptions to guide policy responses and investigation strategies.

Runs as Milestone 21 and provides strategic insight into fraud landscape.

## Terminology

* **Fraud Pattern**: A recurring scheme or behavioral anomaly detected across multiple providers (e.g., Home Health Rate Outliers, Middleman Billing, Sudden Starts/Stops).
* **Pattern Classification**: Assigning providers to one or more fraud pattern categories based on detection signals.
* **Pattern Exposure**: Total financial impact associated with a specific fraud pattern across all flagged providers.
* **Multi-Pattern Provider**: Provider exhibiting characteristics of multiple fraud patterns simultaneously.

## Requirements

### REQ-PAT-001: Pattern Definition and Taxonomy

**User Story:** As a fraud strategy analyst, I want fraud patterns categorized, so that I can understand the landscape of fraud schemes.

**Acceptance Criteria:**

* **AC-PAT-001.1:** The system shall define 10 fraud pattern categories: (1) Home Health & Personal Care Rate/Volume Outliers, (2) Middleman Billing Organizations, (3) Government Agencies as Outliers, (4) Providers That Cannot Exist, (5) Billing Every Single Day, (6) Sudden Starts and Stops, (7) Billing Networks & Circular Billing, (8) State-Level Spending Differences, (9) Upcoding & Impossible Volumes, (10) Shared Beneficiary Counts.
* **AC-PAT-001.2:** Each pattern shall have classification rules based on methods, service types, temporal signatures, and network characteristics.
* **AC-PAT-001.3:** The system shall document pattern definitions in `fraud_pattern_taxonomy.md`.

### REQ-PAT-002: Provider-to-Pattern Classification

**User Story:** As an investigator, I want providers mapped to fraud patterns, so that I can apply pattern-specific investigation protocols.

**Acceptance Criteria:**

* **AC-PAT-002.1:** For each flagged provider, the system shall apply pattern classification rules and assign to one or more pattern categories.
* **AC-PAT-002.2:** Pattern 1 (Home Health Outliers) shall include providers flagged by peer comparison or statistical outliers with Home Health specialty and &gt;$500K total.
* **AC-PAT-002.3:** Pattern 4 (Cannot Exist) shall include providers with no NPPES record, deactivated NPIs, or LEIE matches.
* **AC-PAT-002.4:** Pattern 6 (Sudden Starts/Stops) shall include providers flagged by temporal appearance/disappearance hypotheses.
* **AC-PAT-002.5:** Pattern 7 (Networks) shall include providers flagged by hub-spoke, circular billing, or ghost network hypotheses.
* **AC-PAT-002.6:** The system shall save provider-to-pattern mappings to `provider_fraud_patterns.csv` with columns: npi, name, state, primary_pattern, secondary_patterns, pattern_confidence.

### REQ-PAT-003: Pattern Exposure Calculation

**User Story:** As a policy maker, I want financial exposure by pattern, so that I can prioritize policy interventions.

**Acceptance Criteria:**

* **AC-PAT-003.1:** For each pattern, the system shall aggregate total provider-level exposure (deduplicated, quality-weighted impacts).
* **AC-PAT-003.2:** For systemic patterns (Pattern 3 Government, Pattern 8 State Differences), the system shall include state/code aggregate exposures.
* **AC-PAT-003.3:** The system shall calculate provider counts per pattern and average impact per provider.
* **AC-PAT-003.4:** The system shall save pattern exposure to `fraud_pattern_exposure.csv` with columns: pattern_id, pattern_name, provider_count, total_exposure, avg_per_provider, systemic_component.

### REQ-PAT-004: Pattern Characteristics and Signatures

**User Story:** As a data scientist, I want pattern signatures documented, so that I can refine detection methods.

**Acceptance Criteria:**

* **AC-PAT-004.1:** For each pattern, the system shall calculate characteristic signatures including: dominant detection methods, typical confidence distribution, geographic concentration, specialty distribution, service type mix, temporal profile.
* **AC-PAT-004.2:** The system shall identify distinguishing features that differentiate each pattern from others.
* **AC-PAT-004.3:** The system shall save pattern signatures to `fraud_pattern_signatures.json`.

### REQ-PAT-005: Fraud Pattern Summary Report

**User Story:** As a stakeholder, I want a pattern classification report, so that I understand the types of fraud detected.

**Acceptance Criteria:**

* **AC-PAT-005.1:** The system shall generate `fraud_pattern_summary_report.md` with sections for each of the 10 patterns including: definition, detection methods used, provider count, financial exposure, geographic concentration, example providers (anonymized NPI references), and recommended interventions.
* **AC-PAT-005.2:** The report shall include a pattern exposure ranking showing which patterns account for the most recoverable dollars.
* **AC-PAT-005.3:** The report shall include a pattern overlap analysis showing which patterns commonly co-occur.

## Feature Behavior & Rules

Pattern classification uses rule-based logic combining method signatures, specialty, service types, and behavioral characteristics. Providers can belong to multiple patterns. Primary pattern is the one with highest confidence or exposure. Pattern definitions are based on fraud domain research and stakeholder input. Systemic patterns (3, 8) often indicate rate policy issues rather than individual fraud. Pattern classification informs both investigation strategy and policy reform recommendations. Classification rules are documented in code comments and the taxonomy document.

## Reporting and Visualization

## Overview

Provide a clear and concise summary of the feature, explaining what it does and the value it delivers to the user. Describe the core problem this feature solves and how it fits into the overall product.

## Terminology

* **Key Term 1**: Brief description that ensures shared understanding across the team.
* **Key Term 2**: Definition that clarifies any ambiguity in how this concept is used.

## Requirements

### REQ-XXX-001: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-001.1:** When the user \[performs action\], the system shall \[respond with specific behavior\].
* **AC-XXX-001.2:** When \[condition exists\], the system shall \[handle appropriately\].
* **AC-XXX-001.N:** \[Continue for all acceptance criteria\]

### REQ-XXX-002: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-002.1:** When \[condition\], the system shall \[behavior\].
* **AC-XXX-002.2:** \[Continue for all acceptance criteria\]

## Feature Behavior & Rules

This section clarifies how the requirements behave in practice and how they interact. It explains cross-requirement interactions, defaults, constraints, and edge conditions without prescribing UI or user flows.

### Chart and Visualization Generation

## Overview

This feature generates HHS OpenData-style visualizations including line charts, bar charts, scatter plots, Lorenz curves, network graphs, and heatmaps. All charts follow government design standards with monochromatic amber color scheme, minimal chrome, accessible fonts, and clear labeling. Charts support the CMS Administrator Report and executive dashboards.

Runs as Milestone 10 and produces all visual assets for reporting.

## Terminology

* **HHS OpenData Style**: U.S. government data visualization design system using accessible colors, clear typography, and minimal decoration.
* **Lorenz Curve**: Graphical representation of spending concentration showing cumulative provider share vs. cumulative spending share.
* **Network Graph**: Visual representation of billing relationships between providers (hubs, spokes, circular billing).
* **State Heatmap**: Geographic visualization showing findings or impact intensity by state.

## Requirements

### REQ-CHART-001: Core Chart Types and Styling

**User Story:** As a data analyst, I want standardized chart generation functions, so that all visualizations follow consistent HHS styling.

**Acceptance Criteria:**

* **AC-CHART-001.1:** The system shall provide chart generation functions for: line charts, horizontal bar charts, scatter plots, Lorenz curves, network graphs, and geographic heatmaps.
* **AC-CHART-001.2:** All charts shall use HHS_AMBER (#F59F0A) as primary color, HHS_DARK (#221E1C) for text, HHS_MUTED (#78716D) for secondary text, and HHS_GRID (#E5E2DC) for gridlines.
* **AC-CHART-001.3:** All charts shall use title fonts (Inter or fallback) and mono fonts (JetBrains Mono or fallback) for data labels.
* **AC-CHART-001.4:** Charts shall include proper titles, subtitles, axis labels, and HHS branding footer.
* **AC-CHART-001.5:** All charts shall be saved as PNG files at 150 DPI in `output/charts/` directory.

### REQ-CHART-002: Time Series and Trend Charts

**User Story:** As a CMS administrator, I want temporal visualizations, so that I can see spending trends and anomalies over time.

**Acceptance Criteria:**

* **AC-CHART-002.1:** The system shall generate a monthly spending trend line chart covering Jan 2018 - Dec 2024.
* **AC-CHART-002.2:** The system shall generate per-provider time series charts for the top 20 flagged providers showing monthly billing with peer median reference lines.
* **AC-CHART-002.3:** Time series charts shall handle gaps in data gracefully (no connecting lines across missing months).
* **AC-CHART-002.4:** Charts shall use dollar formatters for y-axis labels (e.g., $1.5B, $250M).

### REQ-CHART-003: Ranking and Comparison Charts

**User Story:** As an investigator, I want ranking visualizations, so that I can quickly identify top entities.

**Acceptance Criteria:**

* **AC-CHART-003.1:** The system shall generate horizontal bar charts for: top 20 flagged providers, top 20 procedures, top 20 states by impact, top 10 detection methods.
* **AC-CHART-003.2:** Bar charts shall sort descending by value and truncate labels to fit (max 40 characters with ellipsis).
* **AC-CHART-003.3:** Bar charts shall include value labels on bars for exact amounts.

### REQ-CHART-004: Distribution and Concentration Charts

**User Story:** As a policy analyst, I want distribution visualizations, so that I can understand market concentration and spending patterns.

**Acceptance Criteria:**

* **AC-CHART-004.1:** The system shall generate a Lorenz curve showing provider spending concentration with reference line for perfect equality.
* **AC-CHART-004.2:** The system shall generate scatter plots for provider risk assessment (total paid vs. anomaly score) with color coding by confidence tier.
* **AC-CHART-004.3:** The system shall generate a findings-by-category bar chart showing detection method productivity.

### REQ-CHART-005: Network and Geographic Visualizations

**User Story:** As a fraud analyst, I want network and geographic charts, so that I can visualize relationships and regional patterns.

**Acceptance Criteria:**

* **AC-CHART-005.1:** The system shall generate network graphs for the top 3 hub providers showing billing-servicing relationships using NetworkX.
* **AC-CHART-005.2:** Network graphs shall use HHS_RED for hub nodes, HHS_AMBER for spoke nodes, and edge thickness proportional to payment volume.
* **AC-CHART-005.3:** The system shall generate a state heatmap showing findings or impact by state (if geographic data available).

## Feature Behavior & Rules

Chart generation uses matplotlib with custom HHS styling applied via setup_hhs_style(). All charts include HHS border and branding. Dollar amounts are formatted using custom formatter functions. Charts handle edge cases (zero values, missing data, outliers). Network visualizations use spring layout with manual positioning hints for clarity. Chart filenames follow convention: `{descriptive_name}.png` (e.g., `top20_flagged_providers.png`, `monthly_spending_trend.png`).

### CMS Administrator Report

## Overview

This feature assembles a comprehensive markdown report for CMS administrators containing executive summary, methodology overview, high-confidence findings, analytical approach, data profile, hypothesis taxonomy, and next steps. The report synthesizes results from all 24 milestones into a single authoritative document suitable for executive review and policy decisions.

Runs as Milestone 11 and produces the primary deliverable for CMS leadership.

## Terminology

* **CMS Administrator Report**: The comprehensive markdown document delivered to CMS leadership summarizing fraud detection findings.
* **Executive Summary**: High-level overview of total findings, confidence distribution, and estimated recoverable amount.
* **Hypothesis Taxonomy**: Structured catalog of the 1,000+ detection methods organized by category.
* **High-Confidence Findings**: Top providers flagged by multiple methods with elevated certainty.

## Requirements

### REQ-REP-001: Report Structure and Sections

**User Story:** As a CMS administrator, I want a structured comprehensive report, so that I can review findings systematically.

**Acceptance Criteria:**

* **AC-REP-001.1:** The system shall generate `CMS_Administrator_Report.md` with sections: Executive Summary, Methodology Overview, Data Profile, Hypothesis Taxonomy, High-Confidence Findings, Analytical Categories, Findings by State, Findings by Method, Validation Results, Next Steps, Technical Appendix.
* **AC-REP-001.2:** The report shall include a table of contents with internal markdown links.
* **AC-REP-001.3:** The report shall use proper markdown formatting including headers, tables, code blocks, and emphasis.
* **AC-REP-001.4:** The report shall be saved to `output/CMS_Administrator_Report.md`.

### REQ-REP-002: Executive Summary Content

**User Story:** As an executive, I want a concise summary, so that I can understand key findings in 2-3 minutes.

**Acceptance Criteria:**

* **AC-REP-002.1:** The executive summary shall report: total findings count, confidence tier distribution (high/medium/low), total estimated recoverable (deduplicated, quality-weighted), total systemic exposure, top 5 states by impact, top 5 detection methods.
* **AC-REP-002.2:** The summary shall highlight the number of CRITICAL tier providers (score &gt;= 80) requiring immediate investigation.
* **AC-REP-002.3:** The summary shall note any government agencies appearing in top flagged entities.
* **AC-REP-002.4:** The summary shall be limited to 500 words or one page equivalent.

### REQ-REP-003: Methodology and Hypothesis Sections

**User Story:** As a technical reviewer, I want methodology documented, so that I can understand the analytical approach.

**Acceptance Criteria:**

* **AC-REP-003.1:** The methodology section shall describe the 10 analytical categories with example hypotheses for each.
* **AC-REP-003.2:** The hypothesis taxonomy section shall list all categories with hypothesis counts and brief descriptions.
* **AC-REP-003.3:** The report shall include confidence tier definitions and explain how multi-method detection increases certainty.
* **AC-REP-003.4:** The report shall note the hypothesis delta (actual tested vs. designed) and explain any gap analysis hypotheses.

### REQ-REP-004: Findings and Data Tables

**User Story:** As a program integrity officer, I want findings data, so that I can review top flagged entities.

**Acceptance Criteria:**

* **AC-REP-004.1:** The report shall include a table of top 100 high-confidence findings with columns: rank, NPI (anonymized as "Provider-XXX"), state, specialty, validation_score, num_methods, quality_weighted_impact, primary_pattern.
* **AC-REP-004.2:** The report shall include findings distribution by state showing: state, finding_count, total_impact, avg_impact_per_provider.
* **AC-REP-004.3:** The report shall include method effectiveness ranking showing: method, finding_count, total_impact, avg_precision.
* **AC-REP-004.4:** All dollar amounts shall be formatted with thousands separators and billions notation where appropriate.

### REQ-REP-005: Visualizations and Next Steps

**User Story:** As a stakeholder, I want charts and recommendations, so that I can see patterns visually and understand next actions.

**Acceptance Criteria:**

* **AC-REP-005.1:** The report shall embed or reference key charts: monthly spending trend, top 20 flagged providers, Lorenz curve, findings by category.
* **AC-REP-005.2:** The next steps section shall provide concrete recommendations: prioritized investigation queue (top 50), policy interventions for systemic patterns, data quality improvement needs, hypothesis refinement suggestions.
* **AC-REP-005.3:** The report shall include an appendix with: data sources, time range, row counts, reference data versions, pipeline execution metadata.

## Feature Behavior & Rules

Report generation runs after all analysis milestones complete. The report assembles data from findings files, validation results, impact calculations, and pattern classifications. NPI anonymization for the report table uses "Provider-{rank}" formatting. Tables use markdown pipe format with alignment. Charts are referenced by filename with relative paths. The report is regenerated each pipeline run, overwriting the previous version. A timestamped copy is archived in `output/reports/archive/` for historical tracking.

### Executive Dashboard Cards

## Overview

This feature generates 3 executive dashboard card images (monthly spending, top procedures, top providers) as PNG files matching HHS OpenData design specifications. Cards are sized for web display (833x547, 833x969 pixels) with precise padding, typography, and branding for use in executive briefings and web dashboards.

Runs as Milestone 17 and produces shareable visual assets.

## Terminology

* **Dashboard Card**: Self-contained visual data card with title, subtitle, chart, and footer branding following HHS design spec.
* **Card Dimensions**: Pixel-perfect sizing (833x547 for Card 1, 833x969 for Cards 2-3) at 150 DPI.
* **HHS Styling**: Monochromatic amber (#E8A317), specific fonts (DejaVu Sans), minimal borders, government branding.

## Requirements

### REQ-DASH-001: Card 1 - Monthly Spending Trend

**User Story:** As an executive, I want a monthly spending card, so that I can see temporal trends at a glance.

**Acceptance Criteria:**

* **AC-DASH-001.1:** The system shall generate `card1-full-monthly-spending.png` at 833x547 pixels showing monthly Medicaid spending from Jan 2018 - Dec 2024.
* **AC-DASH-001.2:** The card shall include title "Monthly Medicaid Provider Spending", subtitle "January 2018 – December 2024 | Total Fee-for-Service and Managed Care".
* **AC-DASH-001.3:** The chart shall use a line plot with amber color, y-axis in billions ($XXB format), and minimal gridlines.
* **AC-DASH-001.4:** The card shall include HHS footer branding and border.

### REQ-DASH-002: Card 2 - Top 20 Procedures

**User Story:** As a utilization analyst, I want a top procedures card, so that I can identify high-spending HCPCS codes.

**Acceptance Criteria:**

* **AC-DASH-002.1:** The system shall generate `card2-full-top-procedures.png` at 833x969 pixels showing top 20 HCPCS codes by total spending.
* **AC-DASH-002.2:** The card shall use horizontal bar chart with HCPCS code and short description as labels (truncated to 28 chars).
* **AC-DASH-002.3:** Bars shall display values in billions with proper formatting.
* **AC-DASH-002.4:** The card layout shall reserve 120px for y-axis labels and follow design spec padding.

### REQ-DASH-003: Card 3 - Top 20 Providers

**User Story:** As a fraud investigator, I want a top flagged providers card, so that I can see the highest-risk entities.

**Acceptance Criteria:**

* **AC-DASH-003.1:** The system shall generate `card3-full-top-providers.png` at 833x969 pixels showing top 20 flagged providers by estimated recoverable amount.
* **AC-DASH-003.2:** Provider labels shall include anonymized name and state: "Provider Name (ST)".
* **AC-DASH-003.3:** The card shall sort providers descending by quality-weighted impact.
* **AC-DASH-003.4:** All three cards shall follow identical typography, padding, and branding standards.

## Feature Behavior & Rules

Cards use matplotlib with precise figure sizing, DPI, and padding calculations. Text uses plain-language transformations for readability. Cards are saved with white background and 1px border. The design follows chart-design-spec.json specifications exactly. Cards are regenerated each run and can be embedded in web dashboards or presentations.

### Hypothesis Cards

## Overview

This feature generates individual card images for each analytical category (Categories 1-10) showing top flagged providers per detection method. Each card visualizes the top 20 providers for that category with impact amounts, creating a visual catalog of detection method effectiveness.

Runs as Milestone 18 and produces method-specific visualizations.

## Terminology

* **Hypothesis Card**: Visual card showing top providers flagged by a specific analytical category or method.
* **Category Card**: Aggregation of all hypotheses within one of the 10 analytical categories.
* **Plain Language**: Simplified descriptions removing technical jargon (e.g., "z-score" → "far above peers").

## Requirements

### REQ-HCARD-001: Category Card Generation

**User Story:** As a data analyst, I want cards per category, so that I can see which detection methods were most productive.

**Acceptance Criteria:**

* **AC-HCARD-001.1:** The system shall generate one card per analytical category (Categories 1-10) showing top 20 providers flagged by any hypothesis in that category.
* **AC-HCARD-001.2:** Each card shall use card dimensions 833x969 pixels at 150 DPI.
* **AC-HCARD-001.3:** Card titles shall be category names: "Category 1: Statistical Outliers", "Category 2: Temporal Anomalies", etc.
* **AC-HCARD-001.4:** Bars shall show provider names (truncated to 28 chars) and quality-weighted impact in billions.

### REQ-HCARD-002: Plain Language Descriptions

**User Story:** As a non-technical stakeholder, I want readable descriptions, so that I can understand what each method detects.

**Acceptance Criteria:**

* **AC-HCARD-002.1:** The system shall apply plain language transformations to hypothesis descriptions: "z-score" → "far above peers", "IQR" → "outside typical range", "GEV" → "rare extreme", "HCPCS" → "procedure code".
* **AC-HCARD-002.2:** Category subtitles shall explain the detection approach in one sentence (e.g., "Identifies providers whose billing patterns deviate statistically from peer norms").

### REQ-HCARD-003: Method-Specific Cards

**User Story:** As a fraud investigator, I want method-level detail, so that I can understand specific technique effectiveness.

**Acceptance Criteria:**

* **AC-HCARD-003.1:** For high-yield methods (&gt;100 findings), the system may generate method-specific cards showing top providers for that single method.
* **AC-HCARD-003.2:** Method cards shall include the hypothesis ID and acceptance criteria in the subtitle.
* **AC-HCARD-003.3:** Cards with zero findings shall display "No findings in current data" message instead of empty chart.

### REQ-HCARD-004: Card Output and Organization

**User Story:** As a report assembler, I want organized card outputs, so that I can incorporate them into deliverables.

**Acceptance Criteria:**

* **AC-HCARD-004.1:** The system shall save all hypothesis cards to `output/cards/` directory with naming: `category_{N}_card.png`.
* **AC-HCARD-004.2:** The system shall generate an index file `card_index.md` listing all cards with thumbnails and descriptions.

## Feature Behavior & Rules

Cards use the same matplotlib styling as dashboard cards. Plain language replacements use regex transformations. Cards aggregate providers across all hypotheses in the category, de duplicating and taking maximum impact. Empty categories (zero findings) still generate cards with a "no findings" message. Cards are sized for web embedding and can be used in presentations or reports.

### Executive Brief

## Overview

This feature generates a 2-3 page executive brief in markdown format synthesizing the most critical findings, patterns, and recommendations for senior leadership. The brief is designed for fast reading (under 5 minutes) and focuses on actionable insights, policy implications, and strategic decisions.

Runs as Milestone 19 and produces the executive-level deliverable.

## Terminology

* **Executive Brief**: Concise 2-3 page summary designed for senior leadership review.
* **Strategic Insights**: High-level observations about fraud landscape, systemic issues, and policy implications.
* **Actionable Recommendations**: Specific next steps with assigned priorities and timelines.

## Requirements

### REQ-BRIEF-001: Brief Structure and Length

**User Story:** As an executive, I want a concise brief, so that I can grasp key findings quickly.

**Acceptance Criteria:**

* **AC-BRIEF-001.1:** The system shall generate `Executive_Brief.md` limited to 1500 words or 3 pages equivalent.
* **AC-BRIEF-001.2:** The brief shall include sections: Key Findings (bullet points), Financial Impact Summary, Top 10 Patterns, Strategic Observations, Immediate Actions, Policy Recommendations, Next 90 Days.
* **AC-BRIEF-001.3:** The brief shall use clear headings, bullet points, and bold emphasis for scannability.

### REQ-BRIEF-002: Key Findings and Impact

**User Story:** As a decision-maker, I want the bottom line up front, so that I know the magnitude and urgency.

**Acceptance Criteria:**

* **AC-BRIEF-002.1:** Key Findings shall list: total estimated recoverable, number of CRITICAL providers, top 3 states, top 3 fraud patterns, percentage of government agencies in top flagged.
* **AC-BRIEF-002.2:** Financial Impact Summary shall report deduplicated provider-level exposure and systemic policy issue exposure separately.
* **AC-BRIEF-002.3:** The brief shall highlight any findings requiring immediate legal or regulatory action.

### REQ-BRIEF-003: Pattern and Policy Insights

**User Story:** As a policy leader, I want strategic insights, so that I can understand systemic issues beyond individual fraud.

**Acceptance Criteria:**

* **AC-BRIEF-003.1:** The Top 10 Patterns section shall list fraud pattern names, provider counts, and exposure with one-sentence descriptions.
* **AC-BRIEF-003.2:** Strategic Observations shall identify: rate policy issues (if 11 of top 20 are government agencies), market concentration concerns, geographic hotspots, service type vulnerabilities.
* **AC-BRIEF-003.3:** Policy Recommendations shall suggest: rate adjustments for systemic patterns, enhanced monitoring for high-risk service types, data quality improvements for low-weight states.

### REQ-BRIEF-004: Actionable Next Steps

**User Story:** As a program director, I want clear action items, so that I can mobilize resources.

**Acceptance Criteria:**

* **AC-BRIEF-004.1:** Immediate Actions (next 30 days) shall include: initiate investigations of top 50 CRITICAL providers, convene policy review for systemic patterns, brief state partners on geographic findings.
* **AC-BRIEF-004.2:** Next 90 Days shall include: complete investigations of top 200 providers, implement policy changes for rate issues, enhance data collection for low-quality states, refine hypotheses based on validation results.
* **AC-BRIEF-004.3:** Each action item shall include responsible party (Investigation Team, Policy Unit, Data Quality Team) and expected outcome.

## Feature Behavior & Rules

The brief synthesizes content from CMS Administrator Report, fraud pattern classification, and risk queue. It prioritizes readability over comprehensiveness. Numbers are rounded for clarity (e.g., $355B instead of $354,986,926,844). The brief is stakeholder-appropriate with no technical jargon. It focuses on decisions and actions rather than methodology. The brief is suitable for distribution to congressional staff, state Medicaid directors, and OIG leadership.

### Merged Card Aggregation

## Overview

This feature merges individual dashboard and hypothesis cards into combined multi-card images for easier distribution and presentation. It creates composite images showing multiple cards side-by-side or in grid layouts, suitable for executive briefing slides and reports.

Runs as Milestone 20 and produces aggregated visual assets.

## Terminology

* **Merged Card**: Composite image containing multiple individual cards arranged in a layout.
* **Card Grid**: 2x2 or 3x1 arrangement of individual cards in a single image.
* **Composite Layout**: Horizontal or vertical stacking of cards with consistent spacing.

## Requirements

### REQ-MERGE-001: Dashboard Card Merging

**User Story:** As a presenter, I want combined dashboard views, so that I can show multiple metrics in one slide.

**Acceptance Criteria:**

* **AC-MERGE-001.1:** The system shall create a merged image combining Cards 1, 2, and 3 (monthly spending, top procedures, top providers) in a horizontal or vertical layout.
* **AC-MERGE-001.2:** Merged images shall maintain consistent spacing (20px gaps) between cards.
* **AC-MERGE-001.3:** The merged image shall be saved as `merged_dashboard_cards.png`.

### REQ-MERGE-002: Category Summary Grids

**User Story:** As a report assembler, I want category grids, so that I can show method comparison in one view.

**Acceptance Criteria:**

* **AC-MERGE-002.1:** The system shall create 2x2 grid images showing 4 category cards together (e.g., Categories 1-4 in one grid, Categories 5-8 in another).
* **AC-MERGE-002.2:** Grid layouts shall use consistent card sizing and spacing.
* **AC-MERGE-002.3:** Grid images shall be saved as `category_grid_{N}.png`.

### REQ-MERGE-003: Custom Layouts

**User Story:** As a stakeholder, I want flexible layouts, so that I can create custom presentations.

**Acceptance Criteria:**

* **AC-MERGE-003.1:** The system shall support configurable layouts via layout specification: horizontal (n cards in row), vertical (n cards in column), grid (rows x cols).
* **AC-MERGE-003.2:** Merged images shall support optional titles and captions.
* **AC-MERGE-003.3:** The system shall save all merged cards to `output/merged_cards/` directory.

## Feature Behavior & Rules

Card merging uses PIL (Python Imaging Library) to composite PNG images. Cards are loaded, resized if needed, and pasted into a new canvas with calculated dimensions. Spacing is consistent across layouts. Merged cards maintain original PNG quality. The feature can be run standalone or as part of the pipeline. Custom layouts can be specified via configuration file.

### Action Plan and Priority Lists

## Overview

This feature generates actionable priority lists and investigation action plans based on risk queue rankings, fraud pattern classifications, and resource constraints. It produces investigator assignment lists, geographic investigation plans, network coordination recommendations, and timeline/milestone schedules for the investigation phase.

Runs as Milestone 22 and produces operational planning documents.

## Terminology

* **Action Plan**: Structured document outlining investigation sequence, resource allocation, and timeline.
* **Priority List**: Ranked list of providers segmented by investigation urgency and resource requirements.
* **Investigation Milestone**: Checkpoint in the investigation workflow with expected deliverables and timelines.
* **Coordinated Investigation**: Multi-provider investigation targeting network or geographic clusters.

## Requirements

### REQ-ACTION-001: Investigation Priority Lists

**User Story:** As an investigation manager, I want prioritized action lists, so that I can assign cases to investigators.

**Acceptance Criteria:**

* **AC-ACTION-001.1:** The system shall generate `investigation_priority_list_top200.csv` with columns: rank, npi, name, state, specialty, priority_tier (IMMEDIATE/HIGH/MEDIUM), estimated_hours, recommended_investigator_type, coordination_flag.
* **AC-ACTION-001.2:** The system shall segment the list by priority tier with separate sections for each tier.
* **AC-ACTION-001.3:** Providers requiring specialized expertise (network analysis, clinical review) shall be flagged with required skill sets.
* **AC-ACTION-001.4:** Network-related providers shall be grouped for coordinated investigation.

### REQ-ACTION-002: Geographic and Network Plans

**User Story:** As a field investigator, I want geographic plans, so that I can conduct regional investigations efficiently.

**Acceptance Criteria:**

* **AC-ACTION-002.1:** The system shall generate state-specific investigation plans showing providers in each state with recommended visit sequences.
* **AC-ACTION-002.2:** For states with 10+ flagged providers, the system shall create a state action plan document.
* **AC-ACTION-002.3:** For network cases (hub-spoke, circular billing), the system shall generate network investigation plans identifying hub providers to investigate first.
* **AC-ACTION-002.4:** Network plans shall save to `action_plans/network_investigation_plan_{network_id}.md`.

### REQ-ACTION-003: Resource Allocation Plan

**User Story:** As a program director, I want resource planning, so that I can staff investigations appropriately.

**Acceptance Criteria:**

* **AC-ACTION-003.1:** The system shall calculate total investigation hours needed: IMMEDIATE tier \* 40hrs + HIGH tier \* 20hrs + MEDIUM tier \* 10hrs.
* **AC-ACTION-003.2:** The system shall estimate timeline at various staffing levels (5, 10, 20 investigators).
* **AC-ACTION-003.3:** The system shall identify skill gaps if specialized expertise is required but unavailable.
* **AC-ACTION-003.4:** Resource allocation shall be saved to `resource_allocation_plan.md`.

### REQ-ACTION-004: Investigation Milestones and Timeline

**User Story:** As a project manager, I want milestone schedules, so that I can track investigation progress.

**Acceptance Criteria:**

* **AC-ACTION-004.1:** The system shall define investigation milestones: M1 (IMMEDIATE cases start, week 1), M2 (IMMEDIATE cases complete, week 6), M3 (HIGH cases complete, week 16), M4 (MEDIUM cases complete, week 26).
* **AC-ACTION-004.2:** For each milestone, the system shall specify expected deliverables (case files, referrals, recoveries).
* **AC-ACTION-004.3:** The system shall generate a Gantt chart or timeline visualization (if matplotlib available).
* **AC-ACTION-004.4:** Timeline shall be saved to `investigation_timeline_schedule.md`.

### REQ-ACTION-005: Action Plan Summary Memo

**User Story:** As a stakeholder, I want an action plan memo, so that I understand the investigation strategy.

**Acceptance Criteria:**

* **AC-ACTION-005.1:** The system shall generate `Action_Plan_Memo.md` summarizing: total providers to investigate, priority distribution, geographic focus areas, network investigation strategy, resource requirements, expected timeline, anticipated outcomes.
* **AC-ACTION-005.2:** The memo shall be executive-appropriate (2 pages max) with clear section headings.
* **AC-ACTION-005.3:** The memo shall include quick wins (LEIE/deactivated NPI cases) for early momentum.

## Feature Behavior & Rules

Action plans use risk queue data from Milestone 16, fraud patterns from Milestone 21, and validation scores from Milestone 23. Investigation hour estimates are based on tier assignments. Network coordination flags are set when providers share billing relationships. Geographic plans prioritize states with high provider concentration. Resource calculations assume 8-hour workdays and 80% utilization (account for non-case work). Milestones include buffer time for complex cases.

## Pipeline Orchestration and Execution

## Overview

Provide a clear and concise summary of the feature, explaining what it does and the value it delivers to the user. Describe the core problem this feature solves and how it fits into the overall product.

## Terminology

* **Key Term 1**: Brief description that ensures shared understanding across the team.
* **Key Term 2**: Definition that clarifies any ambiguity in how this concept is used.

## Requirements

### REQ-XXX-001: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-001.1:** When the user \[performs action\], the system shall \[respond with specific behavior\].
* **AC-XXX-001.2:** When \[condition exists\], the system shall \[handle appropriately\].
* **AC-XXX-001.N:** \[Continue for all acceptance criteria\]

### REQ-XXX-002: Requirement Name

**User Story:** As a \[role\], I want to \[perform action\], so that I can \[achieve outcome\].

**Acceptance Criteria:**

* **AC-XXX-002.1:** When \[condition\], the system shall \[behavior\].
* **AC-XXX-002.2:** \[Continue for all acceptance criteria\]

## Feature Behavior & Rules

This section clarifies how the requirements behave in practice and how they interact. It explains cross-requirement interactions, defaults, constraints, and edge conditions without prescribing UI or user flows.

### Master Pipeline Orchestration

## Overview

This feature orchestrates the complete fraud detection pipeline by executing all 24 milestones in sequence, managing dependencies, handling milestone failures, tracking progress, and generating final summary reports. It provides the master run script that transforms raw CSV claims data into actionable fraud investigation queues.

Entry point: `scripts/run_all.py` - coordinates all pipeline components.

## Terminology

* **Pipeline Milestone**: One of 24 sequential processing stages from data quality scan through final reports.
* **Milestone Dependency**: Required prior milestones that must complete before a milestone can execute.
* **Pipeline Run**: Complete execution of all 24 milestones from start to finish.
* **Checkpoint**: Saved state after milestone completion allowing resumption from that point.

## Requirements

### REQ-ORCH-001: Milestone Sequencing and Execution

**User Story:** As a pipeline administrator, I want automated milestone sequencing, so that the pipeline runs without manual intervention.

**Acceptance Criteria:**

* **AC-ORCH-001.1:** The system shall execute milestones in order: M00 (DQ Scan), M01 (Ingestion), M02 (Enrichment), M03 (EDA), M04 (Hypothesis Gen), M05 (Stats), M06 (ML), M07 (Domain Rules), M08 (Cross-Ref), M09 (Dedup), M10 (Charts), M11 (Report), M12 (Feasibility/Validation), M13 (Longitudinal), M14 (Holdout), M15 (Quality Weights), M16 (Risk Queue), M17-20 (Cards/Brief), M21 (Patterns), M22 (Action Plan), M23 (Validation Scores).
* **AC-ORCH-001.2:** The system shall check for milestone completion markers (output files exist) before proceeding to dependent milestones.
* **AC-ORCH-001.3:** The system shall log the start and end time of each milestone with elapsed duration.
* **AC-ORCH-001.4:** The system shall display progress indicators showing current milestone (X of 24) during execution.

### REQ-ORCH-002: Dependency Management

**User Story:** As a developer, I want dependency tracking, so that milestones only run when prerequisites are met.

**Acceptance Criteria:**

* **AC-ORCH-002.1:** The system shall verify that M01 (Ingestion) output exists before running M02 (Enrichment).
* **AC-ORCH-002.2:** The system shall verify that M04 (Hypothesis Gen) completes before running M05-M08 (hypothesis execution milestones).
* **AC-ORCH-002.3:** The system shall verify that M05-M08 complete before running M09 (Deduplication).
* **AC-ORCH-002.4:** The system shall skip optional milestones (M00 DQ Scan, M14 Holdout Validation) if prerequisites missing.

### REQ-ORCH-003: Resume and Checkpoint Capabilities

**User Story:** As a pipeline operator, I want resume capability, so that I can restart from failures without reprocessing completed milestones.

**Acceptance Criteria:**

* **AC-ORCH-003.1:** The system shall save completion checkpoints after each milestone to `pipeline_checkpoints.json`.
* **AC-ORCH-003.2:** When restarted, the system shall detect the last completed checkpoint and resume from the next milestone.
* **AC-ORCH-003.3:** The system shall support a `--start-from` flag allowing manual resumption from a specific milestone number.
* **AC-ORCH-003.4:** The system shall support a `--skip` flag to skip specific milestones (for debugging or custom runs).

### REQ-ORCH-004: Run Summary and Reporting

**User Story:** As a stakeholder, I want a pipeline summary, so that I understand what was executed and the results.

**Acceptance Criteria:**

* **AC-ORCH-004.1:** The system shall generate `pipeline_run_summary.md` at completion showing: total execution time, milestone completion status, total findings, total impact, errors/warnings, output files created.
* **AC-ORCH-004.2:** The summary shall include a milestone execution table with columns: milestone_number, milestone_name, status, duration, output_files.
* **AC-ORCH-004.3:** The summary shall report overall pipeline success/failure status.
* **AC-ORCH-004.4:** The system shall save a timestamped run log to `logs/pipeline_run_{timestamp}.log`.

### REQ-ORCH-005: Configuration and Parameters

**User Story:** As a pipeline administrator, I want configurable parameters, so that I can customize pipeline behavior.

**Acceptance Criteria:**

* **AC-ORCH-005.1:** The system shall support configuration via `config.yaml` for: database path, output directories, milestone enable/disable flags, performance parameters (chunk sizes, thread counts).
* **AC-ORCH-005.2:** Command-line flags shall override config file settings.
* **AC-ORCH-005.3:** The system shall validate configuration on startup and report errors for invalid settings.
* **AC-ORCH-005.4:** The system shall log the active configuration at pipeline start.

## Feature Behavior & Rules

The master orchestrator uses subprocess calls to invoke individual milestone scripts. Each milestone script returns an exit code (0 = success, non-zero = failure). On milestone failure, the orchestrator logs the error and either halts or continues based on criticality flags. Database connections are managed per-milestone to avoid long-running locks. The orchestrator tracks memory usage and can pause between milestones if memory pressure is high. Environment variables pass paths and settings to milestone scripts. The orchestrator is idempotent—running it twice produces the same results if data is unchanged.

### Individual Milestone Execution

## Overview

This feature implements individual milestone execution scripts (M00-M23), each performing a specific data processing, analysis, or reporting task. Each milestone is independently executable, produces defined outputs, logs its progress, and reports completion status to the orchestrator.

Each milestone: `scripts/XX_milestone_name.py` - self-contained execution unit.

## Terminology

* **Milestone Script**: Python script implementing one pipeline stage (e.g., `03_eda.py`, `05_run_hypotheses_1_to_5.py`).
* **Milestone Output**: Files, tables, or reports produced by a milestone and consumed by downstream stages.
* **Milestone Metadata**: Execution timestamp, duration, row counts, and status saved to metadata file.
* **Read-Only Connection**: Database connection mode that prevents data modification during analysis.

## Requirements

### REQ-MILE-001: Standard Milestone Structure

**User Story:** As a developer, I want consistent milestone structure, so that scripts are maintainable and predictable.

**Acceptance Criteria:**

* **AC-MILE-001.1:** Each milestone script shall follow the structure: imports, constants, helper functions, main() function, if **name** == '**main**' block.
* **AC-MILE-001.2:** Each milestone shall use the project root path convention: `PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`.
* **AC-MILE-001.3:** Each milestone shall import utility modules from `scripts/utils/` for database connections, chart generation, and formatting.
* **AC-MILE-001.4:** Each milestone shall log its start time, end time, and elapsed duration.

### REQ-MILE-002: Input Validation and Prerequisites

**User Story:** As a pipeline operator, I want input validation, so that milestones fail fast if prerequisites are missing.

**Acceptance Criteria:**

* **AC-MILE-002.1:** Each milestone shall verify that required input files or tables exist before processing.
* **AC-MILE-002.2:** If inputs are missing, the milestone shall log a clear error message and exit with non-zero status.
* **AC-MILE-002.3:** Data-dependent milestones (M03 EDA, M05-M08 hypotheses) shall verify that the claims table is populated.
* **AC-MILE-002.4:** Enrichment-dependent milestones shall verify that reference tables (providers, hcpcs_codes, leie) exist if required.

### REQ-MILE-003: Output Generation and Validation

**User Story:** As a quality assurance analyst, I want output validation, so that malformed outputs are caught immediately.

**Acceptance Criteria:**

* **AC-MILE-003.1:** Each milestone shall create expected output files in designated directories (`output/`, `output/charts/`, `output/findings/`, `output/analysis/`).
* **AC-MILE-003.2:** JSON outputs shall be validated for correct structure and required fields.
* **AC-MILE-003.3:** CSV outputs shall be validated for expected column counts and non-empty content.
* **AC-MILE-003.4:** Markdown reports shall be validated for non-zero length.

### REQ-MILE-004: Progress Logging and Feedback

**User Story:** As a pipeline monitor, I want progress updates, so that I can track long-running milestones.

**Acceptance Criteria:**

* **AC-MILE-004.1:** Milestones processing large datasets shall log progress every N records or N seconds (e.g., "Processed 100K claims...").
* **AC-MILE-004.2:** Hypothesis execution milestones shall log completion of each hypothesis or batch.
* **AC-MILE-004.3:** Milestones shall log counts of output records (e.g., "Generated 532 findings from Category 1").
* **AC-MILE-004.4:** Milestones shall print a completion message: "Milestone XX complete. Time: XXs".

### REQ-MILE-005: Error Recovery and Graceful Degradation

**User Story:** As a developer, I want graceful error handling, so that partial failures don't crash the pipeline.

**Acceptance Criteria:**

* **AC-MILE-005.1:** Milestones shall use try-except blocks for file I/O and database operations.
* **AC-MILE-005.2:** Hypothesis execution milestones shall catch per-hypothesis failures, log the error, and continue with remaining hypotheses.
* **AC-MILE-005.3:** Chart generation failures shall log warnings but not fail the milestone if charts are supplementary.
* **AC-MILE-005.4:** Milestones shall save partial outputs if possible before exiting on fatal errors.

## Feature Behavior & Rules

Each milestone is designed to be idempotent—rerunning produces the same output. Milestones use sys.path.insert to ensure imports work regardless of working directory. Database connections use context managers (with blocks) for automatic cleanup. Milestones that modify data (M01 Ingestion, M02 Enrichment) use write connections; all others use read-only. Long-running milestones (M05-M08 hypothesis execution, M13 longitudinal analysis) may take hours and include memory-efficient chunking. Milestone numbering follows zero-padding (00, 01, 02, ..., 23) for sorting.

### Error Handling and Logging

## Overview

This feature implements centralized error handling, structured logging, exception management, and audit trail generation across all pipeline milestones. It captures errors, warnings, performance metrics, and data quality issues to enable debugging, compliance auditing, and operational monitoring.

Implemented in: `scripts/utils/logging_utils.py`, `scripts/utils/error_handlers.py`.

## Terminology

* **Structured Logging**: Log entries with consistent format including timestamp, level, milestone, message, and context data.
* **Error Classification**: Categorizing errors by severity (CRITICAL, ERROR, WARNING, INFO, DEBUG) and recoverability (fatal, recoverable, informational).
* **Audit Trail**: Complete chronological record of pipeline execution including decisions, data transformations, and findings.
* **Performance Metrics**: Execution times, memory usage, record counts, and throughput measurements.

## Requirements

### REQ-LOG-001: Structured Logging Framework

**User Story:** As a developer, I want structured logs, so that I can debug issues and analyze pipeline behavior.

**Acceptance Criteria:**

* **AC-LOG-001.1:** The system shall implement a logging framework that writes to both console (stdout) and file (`logs/pipeline.log`).
* **AC-LOG-001.2:** Log entries shall include: timestamp (ISO 8601), log level, milestone name, message, optional context data (JSON).
* **AC-LOG-001.3:** Log levels shall follow Python logging standard: DEBUG, INFO, WARNING, ERROR, CRITICAL.
* **AC-LOG-001.4:** The system shall rotate log files when they exceed 50MB, keeping the last 5 log files.

### REQ-LOG-002: Error Handling and Classification

**User Story:** As a pipeline operator, I want errors classified, so that I know which require immediate action.

**Acceptance Criteria:**

* **AC-LOG-002.1:** The system shall classify errors as: CRITICAL (pipeline halt required), ERROR (milestone fails but pipeline may continue), WARNING (issue noted but processing continues).
* **AC-LOG-002.2:** Critical errors shall include: database connection failure, required input file missing, memory exhaustion, corrupted data preventing ingestion.
* **AC-LOG-002.3:** Errors shall include: hypothesis execution failure, chart generation failure, validation test failure, missing reference data for specific hypotheses.
* **AC-LOG-002.4:** Warnings shall include: low data quality detected, hypothesis skipped due to insufficient data, output file already exists and will be overwritten.

### REQ-LOG-003: Exception Handling Patterns

**User Story:** As a developer, I want standard exception handling, so that errors are caught and logged consistently.

**Acceptance Criteria:**

* **AC-LOG-003.1:** All file I/O operations shall use try-except blocks catching FileNotFoundError, PermissionError, and IOError.
* **AC-LOG-003.2:** All database operations shall use try-except blocks catching duckdb.Error and its subclasses.
* **AC-LOG-003.3:** Hypothesis execution loops shall catch per-hypothesis exceptions, log them, and continue with remaining hypotheses.
* **AC-LOG-003.4:** Exception handlers shall log the full traceback for ERROR and CRITICAL levels.

### REQ-LOG-004: Audit Trail and Compliance Logging

**User Story:** As a compliance officer, I want an audit trail, so that I can demonstrate proper data handling and analysis integrity.

**Acceptance Criteria:**

* **AC-LOG-004.1:** The system shall log all data transformations including: ingestion row counts, enrichment match rates, deduplication adjustments, confidence score calibrations.
* **AC-LOG-004.2:** The system shall log all configuration settings and parameters used for each pipeline run.
* **AC-LOG-004.3:** The system shall log all findings generated including hypothesis ID, provider NPI, and financial impact.
* **AC-LOG-004.4:** The audit log shall be immutable (append-only) and saved to `logs/audit_trail_{timestamp}.log`.

### REQ-LOG-005: Performance Monitoring and Metrics

**User Story:** As a performance analyst, I want metrics collected, so that I can optimize pipeline execution.

**Acceptance Criteria:**

* **AC-LOG-005.1:** The system shall log execution time for each milestone and for the overall pipeline.
* **AC-LOG-005.2:** The system shall log memory usage at milestone boundaries (if psutil available).
* **AC-LOG-005.3:** The system shall log record counts for key operations: rows ingested, enrichment matches, findings generated, providers scored.
* **AC-LOG-005.4:** The system shall generate a performance report `performance_metrics.csv` with columns: milestone, duration_sec, peak_memory_mb, records_processed, throughput_records_per_sec.

## Feature Behavior & Rules

Logging uses Python's built-in logging module with custom formatters. Each milestone initializes logging at the start of main(). Console logs use INFO level by default; file logs use DEBUG level. Context data (e.g., hypothesis parameters, provider details) is logged as JSON for machine readability. Error handling distinguishes between expected failures (e.g., zero findings for a hypothesis) and unexpected failures (e.g., malformed data). Audit trails capture regulatory-relevant events for compliance review. Performance metrics help identify bottlenecks for optimization.

