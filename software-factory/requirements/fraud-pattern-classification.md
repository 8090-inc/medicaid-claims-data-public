---
title: "Fraud Pattern Classification"
type: "feature"
id: "c778f785-e5b2-4994-8476-f1fdd1a7abe7"
---

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
* **AC-PAT-002.2:** Pattern 1 (Home Health Outliers) shall include providers flagged by peer comparison or statistical outliers with Home Health specialty and >$500K total.
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
