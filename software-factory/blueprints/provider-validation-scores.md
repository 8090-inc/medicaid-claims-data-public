---
title: "Provider Validation Scores"
feature_name: null
id: "d8348575-5280-4474-94a9-966cfae3d68b"
---

## Feature Summary

Provider Validation Scores calculates comprehensive multi-signal risk scores (0-100) for each flagged provider, combining signal diversity (number of detection categories), confidence scores, financial impact, temporal persistence, network centrality, and external validation flags (LEIE, NPPES, specialty mismatches). The feature produces the authoritative provider risk ranking used for investigation prioritization and enforcement action.

## Component Blueprint Composition

This feature depends on all prior analytical stages:

* **@Fraud Detection Execution** — Provides findings from all categories (1-9).
* **@Validation and Calibration** — Provides calibrated confidence scores.
* **@Longitudinal and Panel Analysis** — Provides temporal persistence data.
* **@Cross-Reference and Composite Scoring** — Provides external validation flags and network data.

## Feature-Specific Components

```component
name: SignalDiversityScorer
container: Scoring Engine
responsibilities:
	- Count num_methods = distinct detection categories flagging each provider
	- Calculate signal_diversity_score = min(30, num_methods * 6)
	- Calculate confidence_score_component = avg(confidence scores) * 20
	- Calculate impact_score_component = min(20, log10(total_impact) * 3)
```

```component
name: TemporalPersistenceScorer
container: Scoring Engine
responsibilities:
	- Count months_flagged = distinct months with anomalous activity
	- Calculate temporal_persistence_score = min(15, months_flagged * 2)
```

```component
name: NetworkAndExternalScorer
container: Scoring Engine
responsibilities:
	- Calculate network_centrality_score from hub status, circular billing, pure billing entity flags
	- Calculate external_validation_score from LEIE match, NPPES deactivation, specialty mismatch
	- Cap external score at 15 points maximum
```

```component
name: CompositeProviderScorer
container: Scoring Engine
responsibilities:
	- Calculate provider_validation_score = signal_diversity (30) + confidence (20) + impact (20) + temporal (15) + network (10) + external (15) - penalties
	- Apply -10 penalty for single-method detections with confidence < 0.70
	- Apply +5 bonus for domain rule findings
	- Normalize to 0-100 range
```

```component
name: RiskTierClassifier
container: Scoring Engine
responsibilities:
	- Classify: CRITICAL (>= 80), HIGH (65-79), MEDIUM (50-64), LOW (< 50)
	- Calculate distribution across tiers
	- Flag CRITICAL tier for immediate review
```

```component
name: ValidationScoringReporter
container: Scoring Engine
responsibilities:
	- Generate provider_validation_scores.csv
	- Generate critical_risk_providers.csv
	- Generate provider_validation_scoring_report.md
```

## System Contracts

### Key Contracts

* **Multi-Signal Design**: Signal diversity (30 pts) is strongest component.
* **Conservative Scoring**: External validation never dominates single-method evidence.
* **Temporal Requirement**: Temporal persistence requires linking findings across panel.

### Integration Contracts

* **Input**: Findings from all categories; calibrated confidence scores; network and external validation data
* **Output**:
  * `output/analysis/provider_validation_scores.csv`
  * `output/analysis/critical_risk_providers.csv`
  * `output/analysis/provider_validation_scoring_report.md`
* **Downstream Dependency**: @Impact Quantification and @Reporting use scores

## Architecture Decision Records

### ADR-001: Multi-Signal Risk Aggregation

**Context:** Single detection methods have false positives.

**Decision:** Weight signal diversity as largest component (30/100).

**Consequences:**

* Benefits: Multi-method detections nearly perfect; reduces false positives
* Trade-off: Single-method findings scored lower
* Validation: External validation provides independent ground truth

## Testing & Validation

### Acceptance Tests

* **Signal Diversity Scoring**: Verify num_methods counted; verify score formula applied
* **Confidence Component**: Verify average confidence calculated; verify component formula
* **Impact Component**: Verify log10 formula applied; verify capping
* **Temporal Persistence**: Verify months_flagged counted; verify score formula
* **Composite Score**: Verify all components summed; verify penalties and bonuses
* **Risk Tier Classification**: Verify tier boundaries applied correctly

### Unit Tests

* **SignalDiversityScorer**: Test method counting; test score calculation
* **TemporalPersistenceScorer**: Test month counting; test score formula
* **NetworkAndExternalScorer**: Test network signal calculation; test external flags
* **CompositeProviderScorer**: Test score summation; test penalty/bonus logic
* **RiskTierClassifier**: Test tier boundaries; test distribution calculation

### Integration Tests

* **End-to-End Scoring**: Load all findings -> calculate all components -> assign tiers
* **Multi-Signal Provider**: Manually calculate for sample provider -> verify matches
* **Score Distribution**: Verify reasonable distribution across tiers

### Test Data Requirements

* **Complete Findings**: All categories for diverse provider set
* **Calibrated Scores**: From validation and calibration
* **External Validation**: LEIE, NPPES, specialty mismatches

### Success Criteria

* All providers scored using multi-signal formula
* Signal diversity drives highest contributions
* Risk tier classification distributes providers appropriately
* CRITICAL tier identifies strongest evidence
* Scores enable prioritized investigation
