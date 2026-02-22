---
title: "CMS Administrator Report"
type: "feature"
id: "98474bf8-58fd-4036-9986-04f0f26e2083"
---

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
* **AC-REP-002.2:** The summary shall highlight the number of CRITICAL tier providers (score >= 80) requiring immediate investigation.
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
