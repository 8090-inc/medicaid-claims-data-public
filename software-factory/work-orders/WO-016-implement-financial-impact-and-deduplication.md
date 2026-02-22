---
title: "Implement Financial Impact and Deduplication (Milestone 10)"
number: 16
status: "completed"
feature_name: "Financial Impact and Deduplication"
phase: 3
---

# Implement Financial Impact and Deduplication (Milestone 10)

## Description

### **Summary**

Build the financial impact quantification and finding deduplication system that calculates potential recoveries, eliminates duplicate findings across methods, and provides impact-based prioritization.

### **In Scope**

- Calculate financial impact estimates for each finding using various methodologies
- Implement finding deduplication across detection methods to eliminate overlaps
- Build impact quantification models (conservative, moderate, aggressive estimates)
- Create potential recovery calculations based on fraud type and evidence strength
- Implement finding consolidation logic for providers flagged by multiple methods
- Generate impact-prioritized finding lists with financial justification
- Create impact visualization and summary reporting

### **Out of Scope**

- Individual fraud detection methods
- Risk queue generation (handled in separate work order)
- Final action plan creation

### **Blueprints**

- Financial Impact and Deduplication -- Impact calculation methodologies and finding consolidation

### **Testing & Validation**

#### Acceptance Tests

* Verify overlap detection and pairwise overlap calculation between methods
* Verify high correlation identification for method pairs with > 80% overlap
* Verify deduplication calculation: maximum single-method impact as baseline per provider
* Verify impact capping: provider-level impact never exceeds total_paid
* Verify systemic vs provider classification
* Verify financial_impact_summary.md generated with all required metrics

#### Unit Tests

* *OverlapCalculator*: Test pairwise overlap calculation; test correlation matrix generation
* *DeduplicationEngine*: Test maximum baseline calculation; test independent method summing
* *ImpactCalculator*: Test conservative vs aggressive impact models
* *FindingClassifier*: Test provider vs systemic classification
* *ImpactCapper*: Test total_paid ceiling enforcement

#### Integration Tests

* *Full Impact Pipeline*: Load all findings -> calculate overlaps -> apply deduplication -> generate summaries
* *Financial Accuracy*: Verify impact calculations conservative and defensible

#### Success Criteria

* Financial impact calculated for all findings with appropriate deduplication
* Provider-level and systemic findings properly classified
* Impact estimates conservative and supportable for recovery actions

## Implementation Plan

| File Path | Operation | Description |
|-----------|-----------|-------------|
| `scripts/10_financial_impact_deduplication.py` | create | Create the main script for Milestone 10. |
| `scripts/financial/impact_calculator.py` | create | Create a module for calculating financial impact. |
| `scripts/financial/deduplicator.py` | create | Create a module for deduplicating findings. |
| `scripts/financial/prioritizer.py` | create | Create a module for generating impact-prioritized finding lists. |
| `tests/test_financial_impact_deduplication.py` | create | Create a test file for the financial impact milestone. |
