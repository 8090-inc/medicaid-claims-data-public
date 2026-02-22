---
title: "Financial Impact and Deduplication"
type: "feature"
id: "26c2471e-a48c-4691-b366-14d5d7588f9c"
---

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
* **AC-FIN-001.3:** The system shall create an overlap matrix showing which method pairs have high correlation (> 80% overlap).
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

Deduplication uses the maximum single-method impact as baseline to avoid underestimation. Additional methods contribute 70% of their impact unless they are highly correlated (>80% overlap), in which case contribution is 0%. State/code systemic findings are never deduplicated against provider findings. Impact caps at total_paid prevent impossible claims. The deduplication algorithm is conservative, preferring to underestimate rather than overestimate recoverable amounts. Quality weights are applied after deduplication.
