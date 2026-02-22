---
title: "Hypothesis Validation Summary"
type: "feature"
id: "dcec5935-5b5a-4cab-8a01-11262ce063b2"
---

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

Validation summary aggregates data from findings files produced in Milestones 5-8. Zero-finding hypotheses are not necessarily failures--they may indicate clean data for that pattern. Method effectiveness considers both precision and impact magnitude. Categories with many zero-finding hypotheses suggest parameter tuning is needed. The summary is generated after validation and before final impact quantification.
