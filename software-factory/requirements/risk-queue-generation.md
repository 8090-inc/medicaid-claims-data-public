---
title: "Risk Queue Generation"
type: "feature"
id: "d6fe3274-9344-4102-831b-b653f624ad75"
---

## Overview

This feature generates prioritized investigation queues by ranking flagged providers using provider_validation_scores, deduplicated financial impacts, confidence tiers, and investigative resource constraints. It produces the top 500 providers for investigation along with supporting evidence packages and recommended investigation sequences.

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

* **AC-QUEUE-003.1:** The system shall assign priority tiers: IMMEDIATE (rank 1-50, validation_score >= 80), HIGH (rank 51-200, validation_score >= 65), MEDIUM (rank 201-400), REVIEW (rank 401-500).
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
