---
title: "Implement State Quality Weighting System (Milestone 14)"
number: 20
status: "completed"
feature_name: "State Quality Weighting"
phase: 3
---

# Implement State Quality Weighting System (Milestone 14)

## Description

### **Summary**

Build the state quality weighting system that adjusts fraud detection confidence scores based on known data quality issues and reporting completeness by state.

### **In Scope**

* Implement state-level data quality scoring based on CMS Data Quality Atlas
* Create confidence score adjustment algorithms using quality weights
* Build state-specific validation and calibration factors
* Implement quality-adjusted composite scoring
* Create state quality reporting and visualization
* Generate quality-weighted findings with adjusted confidence scores

### **Out of Scope**

* Base fraud detection methods
* Data quality measurement (uses external CMS quality data)
* Final risk prioritization

### **Blueprints**

* State Quality Weighting -- Data quality adjustment and state-specific confidence calibration

### **Testing & Validation**

#### Acceptance Tests

* Verify completeness_score (0-1 range) per state
* Verify consistency_score per state
* Verify coverage_score (actual_months / 84) per state
* Verify outlier_score = 1 - impossible_values_pct per state
* Verify state_quality_weight formula: (completeness x 0.35) + (consistency x 0.35) + (coverage x 0.20) + (outlier x 0.10)
* Verify weights normalized to 0.5-1.0 range
* Verify states with weight < 0.70 flagged as "low_quality_data"
* Verify state_quality_weights.csv created

#### Unit Tests

* *CompletenessScorer*: Test non-null percentage calculation
* *ConsistencyScorer*: Test validation rule application
* *CoverageScorer*: Test temporal coverage calculation
* *OutlierScorer*: Test impossible value detection
* *QualityWeightCalculator*: Test weighted combination formula; test normalization

#### Integration Tests

* *Full Quality Weighting Pipeline*: Calculate all components -> combine into weights -> flag low quality states
* *Weight Application*: Apply quality weights -> verify confidence adjustments appropriate

#### Success Criteria

* State quality weights calculated for all states with meaningful differentiation
* Low quality states properly flagged for additional analyst review
* Weight calculation methodology defensible and transparent

## Implementation Plan

| File Path | Operation | Description |
|-----------|-----------|-------------|
| `scripts/14_state_quality_weighting.py` | create | Create the main script for Milestone 14. |
| `scripts/quality/state_quality_scorer.py` | create | Create a module for scoring state-level data quality. |
| `scripts/quality/confidence_adjuster.py` | create | Create a module for adjusting confidence scores. |
| `scripts/quality/reporting.py` | create | Create a module for generating state quality reports. |
| `tests/test_state_quality_weighting.py` | create | Create a test file for the state quality weighting milestone. |
