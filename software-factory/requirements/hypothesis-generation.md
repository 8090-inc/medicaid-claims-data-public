---
title: "Hypothesis Generation"
type: "feature"
id: "3dc2cb24-97b8-45c1-8a27-ac5bc3f80c48"
---

## Overview

This feature programmatically generates structured fraud detection hypotheses in JSON format, organized into 10 analytical categories. Each hypothesis defines specific detection parameters, acceptance criteria, and financial impact calculation methods that will be systematically tested against the Medicaid claims dataset. The hypothesis generation process creates exactly 1,000 core hypotheses plus additional gap analysis hypotheses covering statistical outliers, temporal anomalies, peer comparison, network analysis, concentration patterns, machine learning models, deep learning approaches, domain-specific red flags, cross-reference validation, and composite risk signals.

This runs as Milestone 4 in the pipeline and establishes the structured framework for all subsequent fraud detection analyses.

## Terminology

* **Hypothesis**: A structured JSON object that defines a specific fraud detection test, including its category, method, parameters, acceptance criteria, and impact calculation approach.
* **Acceptance Criteria**: The specific thresholds and conditions that must be met for a provider to be flagged under a hypothesis (e.g., "z-score > 3.0, claims >= 10, excess > $10K").
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
* **AC-HYP-005.2:** For subcategory 4A, the system shall generate 20 hypotheses detecting hubs with varying servicing NPI counts (>50, >100, >200) across different filters including captive arrangements, high-value networks, and cross-specialty patterns.
* **AC-HYP-005.3:** For subcategory 4B, the system shall generate 20 hypotheses detecting servicing NPIs appearing under multiple billing NPIs (>10, >20, >50) with filters for rate arbitrage, multi-state operations, and sequential NPIs.
* **AC-HYP-005.4:** For subcategory 4C, the system shall generate 15 hypotheses detecting circular billing patterns with bilateral payment thresholds ranging from $50K to $500K.
* **AC-HYP-005.5:** For subcategory 4G, the system shall generate 20 hypotheses detecting ghost network indicators including single biller concentration, missing NPPES records, deactivated NPIs, identical patterns, sequential NPIs, and batch creations.

### REQ-HYP-006: Categories 5-10 Generation

**User Story:** As a data scientist, I want hypotheses across concentration, ML, DL, domain rules, cross-reference, and composite approaches, so that I can test multiple analytical paradigms for fraud detection.

**Acceptance Criteria:**

* **AC-HYP-006.1:** The system shall generate 80 Category 5 hypotheses (H0521-H0600) testing market concentration including provider dominance (>30%, >50%, >80% share), single-code specialists (>90%, >95%, >99% revenue concentration), HHI thresholds (>2500, >5000), geographic monopolies, and temporal concentration.
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
