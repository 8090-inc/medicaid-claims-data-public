---
title: "Impact Quantification and Risk Prioritization"
feature_name: null
id: "dae10973-c261-44de-ab8a-e875dcf373d3"
---

# Impact Quantification and Risk Prioritization

## Overview

Impact Quantification and Risk Prioritization estimates financial impact of detected fraud findings, assigns state quality weights reflecting varying fraud risk across Medicaid programs, deduplicates overlapping financial estimates, and produces prioritized investigation queues. The module transforms composite risk scores into actionable recovery targets and investigator assignments, incorporating state-specific context to guide resource allocation and enforcement priorities.

## Component Breakdown

**State Quality Weighting** — @State Quality Weighting applies state-specific fraud prevalence factors, program integrity maturity, and recovery success rates to adjust provider risk scores by state.

**Financial Impact and Deduplication** — @Financial Impact and Deduplication estimates financial exposure per provider, deduplicates overlapping impact estimates from multiple hypotheses, and produces conservative total impact figures.

**Risk Queue Generation** — @Risk Queue Generation ranks providers by composite_score x state_weight x financial_impact, assigns investigation priority tiers, and generates investigation queue exports.

**Fraud Pattern Classification** — @Fraud Pattern Classification categorizes providers by dominant fraud pattern to inform investigation strategy.

## Pipeline Integration

Impact Quantification receives composite risk scores from @Fraud Detection Execution and validated scores from @Validation and Calibration. Produces investigation queues consumed by @Reporting and Visualization.

## Testing & Validation

### Acceptance Tests

* **State Quality Weighting**: Verify state-specific factors applied; verify risk scores adjusted by state_weight
* **Financial Impact Estimation**: Verify financial exposure calculated per provider; verify conservative figures
* **Finding Deduplication**: Verify overlapping estimates deduplicated; verify total impact = maximum provably questionable
* **Risk Queue Generation**: Verify providers ranked by composite metric; verify priority tiers assigned
* **Fraud Pattern Classification**: Verify dominant pattern detected per provider
* **Queue Outputs**: Verify investigation queue generated for case management

### Unit Tests

* **StateWeighter**: Test state-specific factor application
* **FinancialImpactCalculator**: Test exposure calculation methods
* **DuplicationHandler**: Test overlapping finding identification; test deduplication logic
* **RiskRanker**: Test composite score calculation; test tier assignment
* **PatternClassifier**: Test dominant fraud pattern detection

### Integration Tests

* **End-to-End**: Load findings -> apply state weights -> estimate impact -> deduplicate -> rank -> classify -> generate queues
* **Deduplication Accuracy**: Create overlapping findings -> verify deduplication correct
* **Priority Queue Accuracy**: Manually verify top 10 rankings

### Test Data Requirements

* **Findings**: Full set with varying composite scores and financial impacts
* **Provider Profiles**: Representatives from all states
* **Validation Scores**: Calibrated risk scores

### Success Criteria

* State quality weights appropriately adjust risk scores
* Financial impact estimates conservative and non-duplicated
* Risk queue properly ranked
* Fraud pattern classification accurate
* Investigation queue ready for case management
