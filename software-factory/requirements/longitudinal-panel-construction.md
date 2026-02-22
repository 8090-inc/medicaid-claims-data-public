---
title: "Longitudinal Panel Construction"
type: "feature"
id: "4679abd1-8ea4-48d2-9bf5-093e2d01bf47"
---

## Overview

This feature constructs longitudinal panel datasets aggregated by provider-month, state-month, specialty-month, and code-month to enable time-series analysis. It creates structured tables capturing billing dynamics across the full 84-month period (Jan 2018 - Dec 2024), computes growth rates and volatility metrics, and enables multivariate temporal pattern detection.

Runs as Milestone 13 in the pipeline and provides the foundation for advanced longitudinal analysis.

## Terminology

* **Panel Data**: Repeated observations of the same entities (providers, states, codes) over multiple time periods.
* **Provider-Month Record**: A single row capturing all billing activity for one provider in one calendar month.
* **Balanced Panel**: All entities present for all time periods (filled with zeros for inactive months).
* **Unbalanced Panel**: Only periods with actual billing activity are recorded.
* **Volatility Metric**: Standard deviation or coefficient of variation of monthly billing amounts over time.

## Requirements

### REQ-PANEL-001: Provider Monthly Panel Construction

**User Story:** As a data analyst, I want provider-level monthly panels, so that I can analyze temporal billing patterns for each provider.

**Acceptance Criteria:**

* **AC-PANEL-001.1:** The system shall create a `provider_monthly` table with columns: billing_npi, claim_month, total_paid, total_claims, total_beneficiaries, num_codes, avg_paid_per_claim, avg_claims_per_bene.
* **AC-PANEL-001.2:** The table shall contain one row per provider per month where the provider had any billing activity (unbalanced panel).
* **AC-PANEL-001.3:** The system shall calculate month-over-month growth rates as (current_paid - prior_paid) / prior_paid for each provider.
* **AC-PANEL-001.4:** The system shall calculate 12-month rolling statistics including mean, std, min, max, and coefficient of variation.
* **AC-PANEL-001.5:** The system shall save the panel as a DuckDB table and export the top 500 high-volatility providers to `longitudinal_provider_top500.csv`.

### REQ-PANEL-002: State and Specialty Aggregations

**User Story:** As a policy analyst, I want state and specialty temporal aggregations, so that I can analyze regional and specialty-specific trends.

**Acceptance Criteria:**

* **AC-PANEL-002.1:** The system shall create `state_monthly_totals` table with columns: state, claim_month, total_paid, total_claims, total_beneficiaries, num_providers.
* **AC-PANEL-002.2:** The system shall create `specialty_monthly_totals` table with columns: specialty, claim_month, total_paid, total_claims, total_beneficiaries, num_providers.
* **AC-PANEL-002.3:** For states and specialties, the system shall calculate year-over-year growth rates comparing each month to the same month in the prior year.
* **AC-PANEL-002.4:** The system shall export both tables to CSV in `output/analysis/`.

### REQ-PANEL-003: Code Monthly Aggregations

**User Story:** As a utilization analyst, I want HCPCS code temporal aggregations, so that I can track service-specific utilization trends.

**Acceptance Criteria:**

* **AC-PANEL-003.1:** The system shall create `code_monthly_totals` table with columns: hcpcs_code, claim_month, total_paid, total_claims, num_providers, avg_paid_per_claim.
* **AC-PANEL-003.2:** The system shall track monthly entry and exit of providers per code (new providers billing the code, providers who stopped).
* **AC-PANEL-003.3:** The system shall export the top 200 codes by total spending to `code_monthly_totals_top200.csv`.

### REQ-PANEL-004: Time Series Feature Engineering

**User Story:** As a data scientist, I want temporal features calculated, so that I can use them in predictive models and anomaly detection.

**Acceptance Criteria:**

* **AC-PANEL-004.1:** For each provider, the system shall calculate temporal features including first_month, last_month, months_active, months_inactive_between, longest_continuous_run, max_month_paid, min_month_paid.
* **AC-PANEL-004.2:** The system shall calculate Hurst exponent (measure of time series persistence) for providers with 24+ months of data.
* **AC-PANEL-004.3:** The system shall identify change points using CUSUM or PELT algorithms and record the change point month and magnitude for each provider.
* **AC-PANEL-004.4:** The system shall save temporal features to `provider_temporal_features` table.

## Feature Behavior & Rules

Panel construction uses window functions and self-joins to calculate prior-month and rolling statistics efficiently. Months with zero billing are not included in the unbalanced panel but are accounted for in months_active calculations. Growth rate calculations handle division by zero (prior month = 0) by setting growth to NULL or infinity marker. State and specialty aggregations join with the providers table to enrich with metadata. Code panels track market dynamics including provider entry/exit rates.
