---
title: "Multivariate Temporal Analysis"
feature_name: null
id: "7f68c70d-eb40-4c21-881b-dd9cde310e77"
---

## Feature Summary

Multivariate Temporal Analysis detects temporal anomalies in provider billing patterns that are not visible in single-period snapshots. It implements eight distinct detection methods (2A-2H) including month-over-month spikes, ramp-ups, abrupt stops, year-over-year growth comparisons, seasonality violations, COVID-period anomalies, December spikes, and structural change-point detection. These temporal signals are combined into composite risk scores, enabling analysts to identify providers with accelerating growth, erratic billing patterns, or suspicious behavioral shifts.

## Component Blueprint Composition

This feature composes core analysis infrastructure to examine longitudinal time series:

* **Base Analyzer Framework** — Provides `#BaseAnalyzer` base class and hypothesis execution protocol; `#TemporalAnalyzer` extends this to implement temporal-specific handlers.

## Feature-Specific Components

```component
name: TemporalAnalyzer
container: Analysis Service
responsibilities:
	- Dispatch temporal hypotheses (subcategories 2A-2H) to appropriate detection handlers
	- Implement month-over-month spike detection via period-to-period ratio comparison
	- Implement provider ramp-up detection identifying smooth growth curves followed by plateaus
	- Implement abrupt stop detection identifying sudden termination of billing activity
	- Implement year-over-year growth comparison against same months in prior years
	- Implement seasonality anomaly detection identifying pattern violations
	- Implement COVID-period comparison (2019 baseline vs 2020-2021)
	- Implement December billing spike detection against provider's monthly average
	- Implement change-point detection using Pelt algorithm with CUSUM fallback
	- Generate Finding objects with evidence, confidence scores, and total impact estimates
```

## System Contracts

### Key Contracts

* **Hypothesis Structure**: Each hypothesis must contain 'id', 'subcategory' (2A-2H), and optional 'parameters' dict.
* **Data Requirements**: Requires `provider_monthly` table. Providers with <12 months excluded from growth analysis.
* **Finding Format**: All findings include hypothesis_id, providers, total_impact, confidence (0.5-0.95), method_name, evidence.
* **Idempotency**: Identical inputs produce identical findings.

### Integration Contracts

* **Input**: Hypothesis dict with 'subcategory' key and optional 'parameters' dict.
* **Output**: List of Finding dicts consumable by downstream milestones.
* **Database Interface**: Read-only access to `provider_monthly` and `provider_summary`.
* **Upstream Dependency**: Longitudinal panel construction populates `provider_monthly`.
* **Downstream Consumers**: Validation milestones aggregate findings and produce risk queues.

## Architecture Decision Records

### ADR-001: Subcategory-Based Dispatch Pattern

**Context:** Eight statistically distinct methods each with unique requirements.

**Decision:** Implement dispatch dictionary mapping subcategory codes to handler methods.

**Consequences:** Improves modularity, testability, and readability. New patterns can be added as new handlers.

### ADR-002: Dual-Strategy Change-Point Detection

**Context:** Advanced algorithms (ruptures.Pelt) may not be available everywhere.

**Decision:** Implement Pelt as primary with CUSUM fallback.

**Consequences:** Ensures availability in minimal environments.

## Testing & Validation

### Acceptance Tests

* **Spike Detection (2A)**: Verify ratio calculations; verify 3x, 5x, 10x thresholds
* **Ramp-Ups (2B)**: Verify smooth growth curve detection
* **Abrupt Stops (2C)**: Verify sudden termination detection
* **YoY Growth (2D)**: Verify same-month comparisons
* **Seasonality (2E)**: Verify seasonal pattern identification
* **COVID Comparison (2F)**: Verify 2019 baseline vs 2020-2021
* **December Spikes (2G)**: Verify December spike detection
* **Change-Point (2H)**: Verify Pelt and CUSUM algorithms

### Unit Tests

* **Dispatch**: Test subcategory routing; test parameter override; test unknown subcategory
* **Each Handler**: Test specific detection logic per subcategory

### Integration Tests

* **End-to-End**: Execute all 8 subcategories -> verify findings structure
* **Fallback Testing**: Disable ruptures -> verify CUSUM fallback
* **Idempotency**: Run twice -> verify identical findings

### Test Data Requirements

* **Provider Monthly Data**: 84 months with various billing patterns
* **Temporal Patterns**: Spikes, ramp-ups, abrupt stops, seasonality, COVID shifts, change points

### Success Criteria

* All 8 subcategories executable
* Findings include all required fields
* Confidence scales properly with magnitude
* Change-point detection robust with fallback
* Reproducibility verified
