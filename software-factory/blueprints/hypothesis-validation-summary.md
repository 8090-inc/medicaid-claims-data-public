---
title: "Hypothesis Validation Summary"
feature_name: null
id: "7beb7135-cd28-4486-a222-344e7ab76219"
---

## Feature Summary

Hypothesis Validation Summary aggregates validation results across all executed hypotheses, producing summary statistics on detection method effectiveness. The feature calculates finding counts, total financial impact, and precision by hypothesis and detection method, identifies high-performing vs. zero-finding hypotheses, ranks methods by impact, and produces pruning recommendations for ineffective detection approaches.

## Component Blueprint Composition

This feature depends on validation results from prior stages:

* **@Holdout Validation and Calibration** — Provides precision metrics and performance ranking data.
* **@Fraud Detection Execution** — Provides finding counts from all detection methods.

## Feature-Specific Components

```component
name: FindingCountAggregator
container: Validation Engine
responsibilities:
	- Aggregate finding counts for each hypothesis across all execution milestones
	- Calculate total findings, unique providers flagged, and total financial impact per hypothesis
	- Identify zero-finding hypotheses
	- Save aggregated counts to hypothesis_validation_summary.md
```

```component
name: MethodEffectivenessRanker
container: Validation Engine
responsibilities:
	- Rank detection methods by total financial impact
	- Calculate average precision per method using validation results
	- Identify top 10 methods by impact and top 10 by finding count
	- Save rankings to method_effectiveness_ranking.csv
```

```component
name: CategoryPerformanceAnalyzer
container: Validation Engine
responsibilities:
	- Aggregate findings by analytical category (1-10)
	- For each category: calculate total hypotheses, testable count, hypotheses with findings, total findings, total impact
	- Calculate category effectiveness ratio = (hypotheses with findings) / (testable hypotheses)
	- Identify most and least effective categories
```

```component
name: PruningRecommendationGenerator
container: Validation Engine
responsibilities:
	- Recommend pruning for hypotheses with zero findings across two consecutive runs
	- Recommend pruning for hypotheses with precision < 0.20
	- Save pruned hypothesis list to pruned_methods.csv with rationale
	- Estimate computational savings from pruning
```

```component
name: ValidationSummaryReporter
container: Validation Engine
responsibilities:
	- Generate hypothesis_validation_summary.md with sections: executive summary, findings by category, method rankings, pruning recommendations, data quality notes
	- Include total hypotheses, total findings, total estimated recoverable, precision by confidence tier
	- Generate charts showing category distribution and method contribution
```

## System Contracts

### Key Contracts

* **Zero-Finding Awareness**: Zero-finding hypotheses are not failures; they indicate clean data for that pattern.
* **Method Aggregation**: Methods can have multiple hypotheses; aggregation sums findings and impacts across all.

### Integration Contracts

* **Input**: Finding counts from @Fraud Detection Execution; validation results from @Holdout Validation and Calibration
* **Output**:
  * `output/analysis/hypothesis_validation_summary.md`
  * `output/analysis/method_effectiveness_ranking.csv`
  * `output/analysis/pruned_methods.csv`
* **Downstream Dependency**: @Provider Validation Scores uses effectiveness data to weight methods

## Architecture Decision Records

### ADR-001: Method Aggregation Over Hypothesis Ranking

**Context:** Ranking hypotheses individually can be noisy. Aggregating to methods provides clearer patterns.

**Decision:** Aggregate hypotheses into methods, rank methods by impact and effectiveness.

**Consequences:**

* Benefits: Clearer signal; easier to identify systematic issues
* Trade-off: Fine-grained hypothesis-level insights hidden at top level
* Mitigation: Provide both method-level and hypothesis-level reports

## Testing & Validation

### Acceptance Tests

* **Finding Count Aggregation**: Verify totals calculated per hypothesis
* **Zero-Finding Identification**: Verify zero-finding hypotheses identified but not marked as failures
* **Method Effectiveness Ranking**: Verify methods ranked by impact; verify top 10 identified
* **Category Performance**: Verify effectiveness ratio calculated per category
* **Pruning Recommendations**: Verify recommendations generated for low-precision hypotheses
* **Summary Report**: Verify comprehensive report generated

### Unit Tests

* **FindingCountAggregator**: Test summation; test unique provider counting; test zero-finding detection
* **MethodEffectivenessRanker**: Test ranking by impact; test precision averaging
* **CategoryPerformanceAnalyzer**: Test category aggregation; test effectiveness ratio
* **PruningRecommendationGenerator**: Test zero-finding detection; test precision threshold
* **ValidationSummaryReporter**: Test report generation; test statistics accuracy

### Integration Tests

* **End-to-End Summary**: Aggregate findings -> rank methods -> calculate category performance -> generate pruning recommendations -> produce report
* **Method Effectiveness Accuracy**: Manually rank top 10 methods -> compare to tool output
* **Pruning Precision**: Review recommendations -> verify low-precision hypotheses correctly identified

### Test Data Requirements

* **Diverse Hypotheses**: Mix of hypotheses with findings, zero-finding, high-precision and low-precision
* **Validation Results**: Precision metrics for all hypotheses
* **Finding Counts**: Various finding volume patterns

### Success Criteria

* All hypotheses aggregated and ranked
* Method effectiveness ranking identifies best approaches
* Category performance analysis shows effectiveness variation
* Zero-finding hypotheses properly handled
* Pruning recommendations justified
* Summary report comprehensive
