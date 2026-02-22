---
title: "State Quality Weighting"
type: "feature"
id: "3d98f7a1-c2b1-4163-a752-500279b63111"
---

## Overview

This feature assigns data quality weights to each state based on completeness, consistency, and reliability metrics calculated during the DQ Atlas assessment. It adjusts financial impact estimates by state quality weights to produce quality-weighted recoverable amounts that reflect confidence in the underlying data.

Runs as Milestone 15 and refines impact estimates based on data quality.

## Terminology

* **State Quality Weight**: A 0-1 multiplier reflecting data completeness and consistency for each state.
* **DQ Atlas**: Data quality assessment framework evaluating completeness, consistency, validity, and timeliness.
* **Quality-Weighted Impact**: Financial impact estimate adjusted by state quality weight to reflect data reliability.
* **Completeness Score**: Percentage of expected fields populated (non-null) for a state's claims.
* **Consistency Score**: Degree of internal consistency (e.g., paid >= 0, claims <= physically possible, dates in valid ranges).

## Requirements

### REQ-SQW-001: State Data Quality Assessment

**User Story:** As a data quality analyst, I want state-level quality scores, so that I can understand data reliability by jurisdiction.

**Acceptance Criteria:**

* **AC-SQW-001.1:** The system shall calculate completeness_score per state as the percentage of non-null values across key fields (servicing_npi, beneficiaries, hcpcs_code).
* **AC-SQW-001.2:** The system shall calculate consistency_score per state as the percentage of records passing validation rules (paid >= 0, claims > 0, valid dates, known HCPCS codes).
* **AC-SQW-001.3:** The system shall calculate coverage_score per state as (actual_months_with_data / 84) for the full 2018-2024 period.
* **AC-SQW-001.4:** The system shall calculate outlier_score per state as 1 - (outlier_rate) where outlier_rate is the percentage of records with impossible values.

### REQ-SQW-002: Quality Weight Calculation

**User Story:** As a financial analyst, I want composite quality weights, so that I can adjust impact estimates appropriately.

**Acceptance Criteria:**

* **AC-SQW-002.1:** The system shall calculate state_quality_weight = (completeness_score * 0.35) + (consistency_score * 0.35) + (coverage_score * 0.20) + (outlier_score * 0.10).
* **AC-SQW-002.2:** The system shall normalize quality weights to 0.5 - 1.0 range (never below 0.5 to avoid over-discounting).
* **AC-SQW-002.3:** The system shall flag states with quality_weight < 0.70 as "low_quality_data" for analyst review.
* **AC-SQW-002.4:** The system shall save quality weights to `state_quality_weights.csv` with columns: state, completeness_score, consistency_score, coverage_score, outlier_score, quality_weight, quality_tier.

### REQ-SQW-003: Impact Adjustment Application

**User Story:** As a program integrity officer, I want impacts adjusted by data quality, so that estimates reflect confidence levels.

**Acceptance Criteria:**

* **AC-SQW-003.1:** For each finding, the system shall apply the state quality weight: quality_weighted_impact = total_impact * state_quality_weight[provider_state].
* **AC-SQW-003.2:** The system shall recalculate aggregate financial impact across all findings using quality-weighted values.
* **AC-SQW-003.3:** The system shall save both raw and quality-weighted impacts in all downstream reports and exports.
* **AC-SQW-003.4:** The system shall calculate the total adjustment amount: sum(total_impact) - sum(quality_weighted_impact).

### REQ-SQW-004: Quality Tier Reporting

**User Story:** As a stakeholder, I want to see findings segmented by data quality, so that I understand confidence in different state portfolios.

**Acceptance Criteria:**

* **AC-SQW-004.1:** The system shall create quality tiers: GOLD (weight >= 0.90), SILVER (0.80-0.89), BRONZE (0.70-0.79), NEEDS_IMPROVEMENT (< 0.70).
* **AC-SQW-004.2:** The system shall aggregate findings and impact by quality tier.
* **AC-SQW-004.3:** The system shall generate `state_quality_impact_report.md` showing findings and impact by state and quality tier.
* **AC-SQW-004.4:** The report shall include recommendations for states requiring data quality improvement efforts.

## Feature Behavior & Rules

State quality weights are calculated once per pipeline run using the full dataset. Quality assessment uses the DQ_SCAN results from Milestone 0 if available. States with fewer than 1000 total claims are automatically assigned a 0.60 weight. Quality weights apply multiplicatively to financial impacts but do not affect confidence scores or detection logic. Low-quality states may produce findings, but impacts are discounted. The adjustment is conservative--even low-quality data receives at least 50% weight.
