---
title: "Implement Cross-Reference and Composite Scoring (Milestone 09)"
number: 15
status: "completed"
feature_name: "Cross-Reference and Composite Scoring"
phase: 3
---

# Implement Cross-Reference and Composite Scoring (Milestone 09)

## Description

### **Summary**

Build the cross-reference validation and composite scoring system that validates findings against external databases (OIG LEIE, NPPES status), deduplicates overlapping findings, and calculates composite risk scores.

### **In Scope**

- Implement OIG LEIE exclusion list cross-reference validation
- Build NPPES deactivation status checking and post-deactivation detection
- Create finding deduplication logic to eliminate overlaps between methods
- Implement composite scoring algorithm combining multiple detection methods
- Build evidence aggregation and strength assessment
- Create cross-reference validation reporting
- Generate consolidated findings with composite confidence scores

### **Out of Scope**

- Individual detection method implementations
- Financial impact calculation (handled in separate work order)
- Final prioritization and queuing

### **Blueprints**

- Cross-Reference and Composite Scoring -- External validation and multi-method score consolidation

### **Testing & Validation**

#### Acceptance Tests

* Verify NPPES validation and LEIE validation executed with 0.99 confidence
* Verify composite_score calculated per provider
* Verify confidence tiers assigned (HIGH >= 3 methods OR score >= 8.0)
* Verify systemic_fraud_pattern flagging for >= 5 categories
* Verify final_scored_findings.json generated with all required fields

#### Unit Tests

* *NPPESValidator*: Test missing NPI detection; test deactivation date validation
* *LEIEValidator*: Test exact NPI matching; test fuzzy name/address matching
* *CompositeScorer*: Test multi-method score aggregation; test confidence tier assignment
* *FindingDeduplicator*: Test overlap detection; test financial impact deduplication

#### Integration Tests

* *Full Cross-Reference Pipeline*: Execute all external validations -> consolidate findings -> calculate composite scores
* *Multi-Method Consolidation*: Verify findings from all detection methods properly consolidated

#### Success Criteria

* Cross-reference validation successfully executed against external databases
* Composite scores provide unified risk assessment
* Finding deduplication eliminates overlapping financial impacts

## Implementation Plan

| File Path | Operation | Description |
|-----------|-----------|-------------|
| `scripts/09_cross_reference_scoring.py` | create | Create the main script for Milestone 09. |
| `scripts/validation/oig_leie_check.py` | create | Create a module for OIG LEIE cross-referencing. |
| `scripts/validation/nppes_deactivation_check.py` | create | Create a module for NPPES deactivation status checking. |
| `scripts/scoring/composite_scorer.py` | create | Create a module for calculating composite risk scores. |
| `tests/test_cross_reference_scoring.py` | create | Create a test file for the cross-reference and composite scoring milestone. |
