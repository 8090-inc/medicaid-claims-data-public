---
title: "Financial Impact and Deduplication"
feature_name: null
id: "ec415049-79eb-4822-bed8-bb0d4d800d1c"
---

## Feature Summary

Financial Impact and Deduplication calculates deduplicated financial impact per provider, preventing double-counting when multiple detection methods flag the same spending. The feature detects overlaps between methods, takes the maximum single-method impact as baseline, sums 70% of additional independent method impacts, separates systemic vs. provider-level findings, and produces the authoritative deduplicated impact figures.

## Component Blueprint Composition

This feature depends on findings from all detection stages:

* **@Fraud Detection Execution** — Provides raw findings with financial impacts from all methods.
* **@State Quality Weighting** — Provides quality-weighted adjustments.

## Feature-Specific Components

```component
name: OverlapDetector
container: Impact Quantification
responsibilities:
	- For each provider, identify all hypothesis findings and impacts
	- Calculate pairwise overlap between methods (% of flagged dollars detected by both)
	- Create overlap matrix showing method pair correlations
	- Flag method pairs with > 80% overlap as highly correlated
```

```component
name: DedupplicationCalculator
container: Impact Quantification
responsibilities:
	- For each provider, take maximum single-method impact as baseline
	- Sum 70% of additional independent method impacts (< 50% overlap)
	- For highly correlated methods (> 80% overlap), contribute 0% additional
	- Cap provider-level impact at total_paid
	- Save deduplicated impacts to deduplicated_provider_impacts.csv
```

```component
name: Systemic vs ProviderClassifier
container: Impact Quantification
responsibilities:
	- Classify findings as provider_level (specific NPI) or systemic (state/code rate issues)
	- Aggregate systemic findings at state/code level rather than provider level
	- Save systemic findings separately to systemic_policy_issues.csv
	- Report provider-level and systemic exposures separately
```

```component
name: ImpactAttributionCalculator
container: Impact Quantification
responsibilities:
	- Per provider, save breakdown: total_deduplicated_impact, method_contributions, deduplication_adjustment
	- Calculate method_contribution_percentages
	- Save detailed breakdowns to provider_impact_breakdown.json
```

```component
name: FinancialImpactReporter
container: Impact Quantification
responsibilities:
	- Generate financial_impact_summary.md with: total raw, deduplication adjustment, deduplicated impact, systemic exposure, quality-weighted values
	- Include top 10 states/methods by impact
	- Report impact distribution: mean, median, P95, P99
	- Calculate deduplication rate: (raw - deduplicated) / raw
```

## System Contracts

### Key Contracts

* **Conservative Deduplication**: Use maximum single-method as baseline to avoid underestimation.
* **Additivity Strategy**: Additional methods contribute 70% to account for partial independence.
* **Impact Cap**: No provider exceeds total_paid.
* **Provider-Level Focus**: Systemic findings never deduplicated against individual findings.

### Integration Contracts

* **Input**: Raw findings from all detection methods (Categories 1-9)
* **Output**:
  * `output/analysis/deduplicated_provider_impacts.csv`
  * `output/analysis/method_overlap_matrix.csv`
  * `output/analysis/systemic_policy_issues.csv`
  * `output/analysis/provider_impact_breakdown.json`
  * `output/analysis/financial_impact_summary.md`
* **Downstream**: @Impact Quantification uses deduplicated values for final prioritization

## Architecture Decision Records

### ADR-001: Maximum Single Method Baseline

**Context:** Multiple overlapping methods detecting same spending could inflate impact if simply summed.

**Decision:** Use maximum single-method impact as conservative baseline. Additional methods contribute only if independent.

**Consequences:**

* Benefits: Prevents over-estimation; simple to explain
* Trade-off: May underestimate if methods capture truly distinct fraud signals
* Validation: Additivity formula (70%) accounts for partial independence

## Testing & Validation

### Acceptance Tests

* **Overlap Detection**: Verify all hypotheses findings loaded per provider; verify pairwise overlap calculated between methods; verify overlap matrix created
* **High Correlation Identification**: Verify method pairs with > 80% overlap flagged as highly correlated
* **Deduplication Calculation**: Verify maximum single-method impact identified as baseline per provider; verify 70% of additional independent method impacts summed; verify highly correlated methods contribute 0% additional
* **Impact Capping**: Verify provider-level impact never exceeds total_paid
* **Systemic vs Provider Classification**: Verify findings classified as provider_level vs systemic; verify systemic findings aggregated separately
* **Impact Attribution**: Verify detailed breakdown per provider saved
* **Final Reporting**: Verify financial_impact_summary.md generated with all required metrics

### Unit Tests

* **OverlapDetector**: Test pairwise overlap calculation; test overlap matrix generation; test correlation threshold
* **DedupplicationCalculator**: Test max selection; test 70% additivity formula; test 80% correlation handling; test capping
* **Systemic vs ProviderClassifier**: Test finding type classification; test systemic aggregation logic
* **ImpactAttributionCalculator**: Test breakdown calculation; test method contribution percentages
* **FinancialImpactReporter**: Test summary generation; test distribution statistics calculation

### Integration Tests

* **End-to-End Deduplication**: Load all findings -> detect overlaps -> calculate deduplicated impact -> separate systemic findings -> generate report
* **Overlap Accuracy**: Manually identify overlapping findings for sample provider -> verify matches tool output
* **Deduplication Formula**: Manually apply max + 70% formula to sample provider -> compare to tool calculation
* **Impact Cap Enforcement**: Identify provider with sum of method impacts > total_paid -> verify capped correctly

### Test Data Requirements

* **Finding Distribution**: Providers with diverse finding patterns
* **Overlap Variations**: Method pairs with varying overlap percentages
* **Impact Ranges**: Providers with small, medium, and large total_paid
* **Systemic Findings**: Policy-level findings for separation testing

### Success Criteria

* Overlapping financial estimates deduplicated correctly
* Deduplication formula applied consistently
* Highly correlated methods identified and handled
* Provider-level impacts capped at total_paid
* Systemic findings separated correctly
* Total deduplicated impact reasonable and documented
