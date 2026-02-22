---
title: "Longitudinal and Panel Analysis"
feature_name: null
id: "011ef80f-40c9-40b7-a31b-b3aec46f5b12"
---

# Longitudinal and Panel Analysis

## Overview

Longitudinal and Panel Analysis constructs and analyzes time-series provider profiles, enabling detection of temporal fraud patterns (spikes, regime changes, structural breaks) and network evolution. The module builds persistent provider-panel datasets tracking billing behavior across time, applies multivariate temporal methods (vector autoregression, structural change detection, dynamic panel models), and identifies temporal anomalies characteristic of fraud schemes that evolve or escalate over time.

## Component Breakdown

**Longitudinal Panel Construction** — @Longitudinal Panel Construction builds persistent provider-panel datasets from `provider_monthly` aggregations, structuring monthly provider observations as balanced or unbalanced panels. Handles provider entry/exit, missing months, and temporal alignment for downstream analysis.

**Multivariate Temporal Analysis** — @Multivariate Temporal Analysis applies advanced time-series methods: VAR models for billing relationships, CUSUM/PELT for change-point detection, structural break tests for regime shifts. Detects billing patterns consistent with fraud escalation or sudden behavioral changes.

## Pipeline Integration

Longitudinal Analysis outputs inform temporal anomaly components of @Fraud Detection Execution. Change-point findings integrate into @Cross-Reference and Composite Scoring. Baseline temporal profiles enable @Validation and Calibration to assess hypothesis stability across time.

## Testing & Validation

### Acceptance Tests

* **Two-Component Integration**: Verify @Longitudinal Panel Construction and @Multivariate Temporal Analysis executed sequentially
* **Panel Construction**: Verify provider-month panel created; verify growth rates calculated; verify rolling statistics computed; verify temporal features extracted
* **Temporal Analysis**: Verify 8 temporal detection methods (2A-2H) executed; verify change-points detected; verify temporal anomalies identified
* **Output Integration**: Verify panel data feeds temporal analysis; verify temporal findings integrate into fraud detection
* **Stability Assessment**: Verify temporal profiles suitable for stability analysis
* **Completeness**: Verify all temporal analysis methods functional

### Unit Tests

* **Panel Construction**: Test growth rate calculation; test rolling statistics; test temporal feature engineering
* **Temporal Analysis**: Test spike detection; test ramp-up detection; test abrupt stop detection; test YoY comparison; test seasonality; test COVID comparison; test December spike; test change-point detection

### Integration Tests

* **Full Workflow**: Construct panel -> apply temporal analysis -> generate findings -> verify integration
* **Temporal Accuracy**: Manually calculate growth rates for sample providers; verify tool calculations match
* **Change-Point Accuracy**: Identify change-points manually; verify tool detects same
* **Downstream Integration**: Pass temporal findings to fraud detection; verify incorporated in risk scores

### Test Data Requirements

* **Complete Provider-Monthly Data**: 84 months of monthly aggregations
* **Diverse Temporal Patterns**: Providers with spikes, ramp-ups, abrupt stops, seasonal patterns, COVID shifts, structural breaks
* **Edge Cases**: Providers with < 12 months, missing months, constant values

### Success Criteria

* Provider-month panel created with growth rates and rolling statistics
* All 8 temporal detection methods executed successfully
* Change-points detected accurately
* Temporal anomalies identified and scored appropriately
* Panel and analysis outputs enable investigation of evolving fraud patterns
