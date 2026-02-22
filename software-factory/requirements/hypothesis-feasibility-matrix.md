---
title: "Hypothesis Feasibility Matrix"
type: "feature"
id: "7ac18ff9-6967-4c81-8e8e-0cfb91490054"
---

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
* **AC-FEA-001.3:** The system shall mark a hypothesis as "testable" when data coverage exceeds minimum thresholds (>100 rows for statistical tests, >20 peers for peer comparisons).
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
