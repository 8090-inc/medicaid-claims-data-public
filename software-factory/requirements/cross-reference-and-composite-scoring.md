---
title: "Cross-Reference and Composite Scoring"
type: "feature"
id: "710cc271-ca19-4ffb-a15d-f18418c89e70"
---

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
* **AC-CROSS-001.4:** For providers with no NPPES record, the system shall flag with confidence 0.95 if total_paid > $100K.
* **AC-CROSS-001.5:** The system shall flag NPIs billing after their NPPES deactivation date.

### REQ-CROSS-002: Specialty and Entity Type Validation

**User Story:** As a medical policy specialist, I want specialty validation, so that I can identify providers billing outside their scope of practice.

**Acceptance Criteria:**

* **AC-CROSS-002.1:** The system shall execute specialty mismatch hypotheses comparing billed HCPCS codes to NPPES-registered specialty.
* **AC-CROSS-002.2:** The system shall flag Individual (Type 1) NPIs with organizational-scale billing patterns (>100 servicing NPIs, >$10M total_paid).
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

* **AC-CROSS-004.1:** For each provider, the system shall calculate a composite_score = sum(method_confidence * method_impact) across all methods that flagged the provider.
* **AC-CROSS-004.2:** The system shall count the number of distinct analytical categories (1-9) that flagged each provider as num_methods.
* **AC-CROSS-004.3:** The system shall assign confidence tiers: HIGH (num_methods >= 3 OR composite_score >= 8.0), MEDIUM (num_methods = 2 OR composite_score >= 4.0), LOW (num_methods = 1 OR composite_score >= 2.0).
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
