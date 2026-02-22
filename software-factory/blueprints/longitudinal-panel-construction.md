---
title: "Longitudinal Panel Construction"
feature_name: null
id: "be5b5f3d-75a5-4d74-84ac-1a023908369a"
---

## Feature Summary

Longitudinal Panel Construction transforms the flat monthly claims table (`provider_monthly`) into structured panel datasets tracking provider billing across the full 84-month period (Jan 2018 - Dec 2024). The feature creates provider-month records, calculates month-over-month growth rates, rolling volatility metrics, and temporal features (first/last month active, months active, Hurst exponent, change points). It also aggregates state, specialty, and code-level monthly totals enabling regional and service-type analysis.

## Component Blueprint Composition

This feature depends on ingested claims data:

* **@Claims Data Ingestion** — Provides `provider_monthly` base table from Milestone 1 aggregations.

## Feature-Specific Components

```component
name: ProviderMonthlyPanelBuilder
container: Longitudinal Analysis
responsibilities:
	- Construct provider-month panel from provider_monthly table
	- Calculate month-over-month growth rates (current_paid - prior_paid) / prior_paid
	- Calculate 12-month rolling statistics: mean, std, min, max, coefficient of variation
	- Identify high-volatility providers (CV > 2.0)
	- Export top 500 high-volatility providers to longitudinal_provider_top500.csv
```

```component
name: StateSpecialtyAggregator
container: Longitudinal Analysis
responsibilities:
	- Create state_monthly_totals table
	- Create specialty_monthly_totals table
	- Calculate year-over-year growth rates for states and specialties
	- Export both tables to CSV
```

```component
name: CodeMonthlyAggregator
container: Longitudinal Analysis
responsibilities:
	- Create code_monthly_totals table with HCPCS code-month aggregations
	- Track provider entry/exit per code
	- Export top 200 codes by total spending
```

```component
name: TemporalFeatureEngineer
container: Longitudinal Analysis
responsibilities:
	- Calculate per-provider temporal features: first_month, last_month, months_active, months_inactive_between, longest_continuous_run, max_month_paid, min_month_paid
	- Calculate Hurst exponent for providers with 24+ months
	- Detect change points using CUSUM or PELT algorithms
	- Save temporal features to provider_temporal_features table
```

## System Contracts

### Key Contracts

* **Completeness**: Panel includes all provider-month combinations where provider had activity; unbalanced panel.
* **Growth Rate Handling**: Division by zero handled by setting growth to NULL or infinity marker.
* **Idempotency**: Identical claims data produces identical panel and aggregations.

### Integration Contracts

* **Input**: `provider_monthly`, `provider_summary`, `providers` tables
* **Output**: Enhanced panel tables, state/specialty/code aggregation tables, CSV exports
* **Downstream Dependency**: @Multivariate Temporal Analysis uses these panels

## Architecture Decision Records

### ADR-001: Unbalanced Panel Design

**Context:** Many providers have irregular billing. Filling zeros for all missing months would bloat data 10-100x.

**Decision:** Use unbalanced panel structure: only include rows where provider had activity.

**Consequences:**

* Benefits: 90% space reduction; faster queries
* Trade-off: Downstream code must distinguish "zero activity" from "missing data"
* Mitigation: months_active field documents temporal coverage

## Testing & Validation

### Acceptance Tests

* **Panel Construction**: Verify provider-month panel created; verify growth rates calculated; verify rolling statistics computed
* **State/Specialty Aggregation**: Verify aggregation tables created with YoY growth rates
* **Code Aggregation**: Verify code-month table created; verify provider entry/exit tracking
* **Temporal Features**: Verify all features calculated including Hurst exponent and change points

### Unit Tests

* **ProviderMonthlyPanelBuilder**: Test growth rate calculation; test rolling statistics; test CV calculation
* **StateSpecialtyAggregator**: Test aggregation; test YoY growth
* **CodeMonthlyAggregator**: Test code-level aggregation; test provider entry/exit detection
* **TemporalFeatureEngineer**: Test temporal feature calculations; test Hurst exponent; test change-point detection

### Integration Tests

* **End-to-End Panel Construction**: Load provider_monthly -> create panel -> calculate features -> verify all output tables
* **Idempotency**: Run twice -> verify identical output
* **Growth Rate Handling**: Verify division by zero handled gracefully

### Test Data Requirements

* **Provider Monthly Data**: ~40M rows with various temporal patterns
* **Edge Cases**: Providers with 1 month, full 84 months, sparse months

### Success Criteria

* Unbalanced panel created with only active months
* All temporal features calculated
* Rolling statistics accurate
* State/specialty/code aggregations complete
* Idempotency verified
