---
title: "State Quality Weighting"
feature_name: null
id: "e2d0acf5-8413-4d92-a9cf-e5336a83c394"
---

## Feature Summary

State Quality Weighting assigns data quality weights (0.5-1.0) to each state based on completeness, consistency, coverage, and outlier metrics. The feature adjusts financial impact estimates by state quality weights, producing quality-weighted recoverable amounts that reflect confidence in underlying data. This ensures states with unreliable data do not inflate aggregate impact estimates.

## Component Blueprint Composition

This feature depends on data quality assessment from prior stages:

* **@CSV Data Quality Validation** — Provides quality metrics from Milestone 0 scanning.
* **@Claims Data Ingestion** — Provides claims tables for completeness and consistency assessment.

## Feature-Specific Components

```component
name: StateDataQualityAssessor
container: Impact Quantification
responsibilities:
	- Calculate completeness_score per state as % non-null values
	- Calculate consistency_score per state as % records passing validation
	- Calculate coverage_score per state as (actual_months / 84)
	- Calculate outlier_score per state as 1 - (impossible_values_pct)
```

```component
name: QualityWeightCalculator
container: Impact Quantification
responsibilities:
	- Calculate state_quality_weight = (completeness * 0.35) + (consistency * 0.35) + (coverage * 0.20) + (outlier * 0.10)
	- Normalize weights to 0.5-1.0 range
	- Flag states with weight < 0.70 as "low_quality_data"
	- Save weights to state_quality_weights.csv
```

```component
name: ImpactAdjustmentApplier
container: Impact Quantification
responsibilities:
	- Apply quality weights: quality_weighted_impact = impact * state_quality_weight
	- Recalculate aggregate financial impact using quality-weighted values
	- Save both raw and quality-weighted impacts in all reports
```

```component
name: QualityTierReporter
container: Impact Quantification
responsibilities:
	- Create quality tiers: GOLD (>= 0.90), SILVER (0.80-0.89), BRONZE (0.70-0.79), NEEDS_IMPROVEMENT (< 0.70)
	- Generate state_quality_impact_report.md
```

## System Contracts

### Key Contracts

* **Conservative Weighting**: Minimum 50% weight even for poorest data.
* **Multiplicative Application**: Weights apply to impacts, not confidence scores.
* **State-Level Granularity**: All providers in same state share quality weight.

### Integration Contracts

* **Input**: Claims tables, DQ metrics
* **Output**:
  * `output/analysis/state_quality_weights.csv`
  * `output/analysis/state_quality_impact_report.md`
* **Downstream**: @Financial Impact and Deduplication uses quality-weighted values

## Architecture Decision Records

### ADR-001: Conservative 50% Minimum Weight

**Context:** Some states may have incomplete data; over-discounting could hide real fraud.

**Decision:** Never weight below 50%.

**Consequences:**

* Benefits: Conservative approach; does not silence low-quality states
* Trade-off: May overestimate in worst-quality states
* Mitigation: Explicitly flag low-quality states for review

## Testing & Validation

### Acceptance Tests

* **Completeness Scoring**: Verify % non-null calculated per state
* **Consistency Scoring**: Verify % records passing validation calculated
* **Coverage Scoring**: Verify actual_months / 84 calculated
* **Quality Weight**: Verify weighted formula applied; verify 0.5-1.0 range
* **Low Quality Flagging**: Verify states < 0.70 flagged
* **Quality Tiers**: Verify GOLD/SILVER/BRONZE/NEEDS_IMPROVEMENT assigned

### Unit Tests

* **StateDataQualityAssessor**: Test each scoring component
* **QualityWeightCalculator**: Test weighted average; test normalization; test flagging
* **ImpactAdjustmentApplier**: Test multiplicative application
* **QualityTierReporter**: Test tier assignment logic

### Integration Tests

* **End-to-End**: Load claims -> calculate metrics -> generate weights -> assign tiers
* **Weight Calibration**: Manually calculate for sample state -> verify matches
* **Conservative Minimum**: Verify no state below 0.50

### Test Data Requirements

* **State-Level Data**: Claims from all 50 states with varying quality
* **Quality Variations**: Different completeness, consistency, coverage levels

### Success Criteria

* Quality weights calculated using weighted formula
* All states assigned weight in 0.5-1.0 range
* Low-quality states flagged
* Quality-weighted impacts calculated
* Tier distribution meaningful
