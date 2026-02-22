---
title: "Domain-Specific Business Rules"
type: "feature"
id: "bad39bba-f0ee-453f-bfd1-0baf19c57bbb"
---

## Overview

This feature executes Category 8 hypotheses testing domain-specific business rules that encode clinical impossibilities, regulatory violations, and known fraud schemes. It validates impossible service volumes based on time constraints, detects upcoding by analyzing E&M level distributions, identifies unbundling patterns, checks for phantom billing indicators, and flags providers in high-risk categories with additional red flags.

Runs as Milestone 7 in the pipeline and applies fraud expertise encoded as deterministic rules.

## Terminology

* **Impossible Volume**: Claims exceeding physical time limits (e.g., >480 15-minute units of personal care in a month).
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
* **AC-DOM-001.3:** The system shall flag claims where claims/beneficiaries exceeds the physical maximum with paid > $10K.
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
* **AC-DOM-004.3:** The system shall flag providers with beneficiary counts unchanging despite claims growth >50%.
* **AC-DOM-004.4:** The system shall flag providers with monthly billing standard deviation < 5% of mean over 12+ months.
* **AC-DOM-004.5:** Confidence scores shall be composite: multiple phantom indicators increase confidence (1 indicator = 0.65, 2 indicators = 0.80, 3+ indicators = 0.95).

### REQ-DOM-005: High-Risk Category Analysis

**User Story:** As a program integrity specialist, I want high-risk category flagging, so that I can apply elevated scrutiny to providers in fraud-prone service types.

**Acceptance Criteria:**

* **AC-DOM-005.1:** The system shall execute 15 high-risk category hypotheses (H0886-H0900) combining category membership with additional red flags (rate outlier, volume outlier, network anomaly).
* **AC-DOM-005.2:** For Home Health providers, the system shall flag those in the top 1% by paid-per-claim AND with >50 servicing NPIs.
* **AC-DOM-005.3:** For Behavioral Health providers, the system shall flag those exceeding state 95th percentile AND billing exclusively for a single code.
* **AC-DOM-005.4:** The system shall save all domain rule findings to `findings/domain_findings_category_8.json`.

## Feature Behavior & Rules

Domain rules are implemented as deterministic SQL queries or Python functions in the domain_rules module. Timed code limits are defined in the TIMED_CODES constant list. E&M level families are defined in EM_FAMILIES dict. Rules execute independently and findings are deduplicated at the provider level. Multiple rule violations for the same provider increment the composite confidence score. Rules are designed to have near-zero false positive rates but may have moderate false negative rates.
