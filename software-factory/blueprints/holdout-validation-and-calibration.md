---
title: "Holdout Validation and Calibration"
feature_name: null
id: "d3a72843-e88e-4b10-97e1-b369c4ebd8e2"
---

## Feature Summary

Holdout Validation and Calibration evaluates hypothesis performance using temporal holdout validation, testing hypotheses on the most recent 6 months of data (Jul-Dec 2024) withheld from hypothesis design. The feature calculates precision metrics (TP / (TP + FP)) for each hypothesis and by confidence tier, identifies high-false-positive-rate hypotheses, and calibrates confidence scores to align with measured precision. This ensures detection findings are grounded in measured accuracy rather than nominal confidence.

## Component Blueprint Composition

This feature depends on prior detection results:

* **@Fraud Detection Execution** — Provides hypotheses and findings from full-period analysis (Jan 2018-Dec 2024).

## Feature-Specific Components

```component
name: TemporalHoldoutSetCreator
container: Validation Engine
responsibilities:
	- Designate last 6 months (Jul-Dec 2024) as holdout validation set
	- Designate prior 78 months (Jan 2018-Jun 2024) as training/analysis set
	- Re-execute all testable hypotheses on holdout period only
	- Compare holdout findings to full-period findings
```

```component
name: PrecisionCalculator
container: Validation Engine
responsibilities:
	- For each hypothesis, calculate precision = (overlap) / (holdout_findings)
	- Calculate precision by confidence tier: HIGH (>= 0.85), MEDIUM (0.65-0.84), LOW (< 0.65)
	- Flag hypotheses with precision < 0.50 as "high_false_positive_rate"
	- Save precision metrics to validation_precision_by_hypothesis.csv
```

```component
name: ConfidenceScoreCalibrator
container: Validation Engine
responsibilities:
	- Calculate gap between nominal confidence and measured precision
	- Apply calibration adjustments reducing scores when precision < nominal confidence
	- Maintain conservative approach: never increase confidence during calibration
	- Save calibrated scores to lookup table for final scoring
```

```component
name: HypothesisPerformanceRanker
container: Validation Engine
responsibilities:
	- Rank hypotheses by performance_score = precision * finding_count * avg_impact
	- Identify top 20 best-performing and bottom 20 worst-performing hypotheses
	- Recommend hypotheses for retirement (precision < 0.30 consistently) or tuning
	- Save rankings to hypothesis_performance_ranking.csv
```

```component
name: CalibrationReporter
container: Validation Engine
responsibilities:
	- Generate confidence_calibration_report.md with before/after precision
	- Document recommended adjustments for each hypothesis
	- Report calibration impact on overall confidence distribution
```

## System Contracts

### Key Contracts

* **Ground Truth Assumption**: Full-period findings treated as ground truth approximation; multi-method flagging signals positive case.
* **Holdout Independence**: Holdout period is completely withheld from hypothesis design; any hypothesis tuning is informed only by training data.
* **Conservative Calibration**: Scores reduced but never increased; prevents overconfidence.

### Integration Contracts

* **Input**: Full-period findings and hypotheses from @Fraud Detection Execution; holdout period claims data
* **Output**:
  * `output/analysis/validation_precision_by_hypothesis.csv` — Precision metrics
  * `output/analysis/hypothesis_performance_ranking.csv` — Ranked hypotheses
  * `output/analysis/confidence_calibration_report.md` — Calibration documentation
  * Calibrated score lookup table for @Cross-Reference and Composite Scoring
* **Downstream Dependency**: @Cross-Reference and Composite Scoring uses calibrated scores in final composite risk calculation

## Architecture Decision Records

### ADR-001: Temporal Holdout Over Random Holdout

**Context:** Random train/test splits ignore temporal order. In time-series fraud, recent patterns differ from historical; random split leaks future information into training.

**Decision:** Use temporal holdout: train on Jan 2018-Jun 2024, holdout test on Jul-Dec 2024 (6 most recent months). This reflects operational scenario where we validate using recently available data.

**Consequences:**

* Benefits: Realistic assessment of deployment performance; captures recent pattern shifts
* Trade-off: Shorter holdout period (6 months vs random 20%) reduces sample size; may have higher variance
* Validation: Multi-method overlap serves as additional ground truth signal

## Testing & Validation

### Acceptance Tests

* **Holdout Set Designation**: Verify last 6 months designated as holdout; verify prior 78 months designated as training period
* **Hypothesis Re-execution**: Verify all testable hypotheses re-executed on holdout period only
* **Precision Calculation**: Verify precision = (overlap) / (holdout_findings) calculated per hypothesis
* **High False Positive Detection**: Verify hypotheses with precision < 0.50 flagged
* **Confidence Score Calibration**: Verify calibration adjustments applied; verify never increased
* **Performance Ranking**: Verify performance_score calculated; verify top 20 and bottom 20 identified
* **Reporting**: Verify confidence_calibration_report.md generated

### Unit Tests

* **TemporalHoldoutSetCreator**: Test date range validation; test hypothesis re-execution
* **PrecisionCalculator**: Test overlap calculation; test precision formula; test confidence tier boundaries
* **ConfidenceScoreCalibrator**: Test gap calculation; test adjustment formula; test conservative direction
* **HypothesisPerformanceRanker**: Test performance score calculation; test ranking logic; test retirement criteria
* **CalibrationReporter**: Test report generation; test before/after statistics

### Integration Tests

* **End-to-End Holdout Validation**: Re-execute hypotheses on holdout period -> calculate precision -> calibrate scores
* **Temporal Independence**: Verify holdout period independent from training
* **Calibration Correctness**: Manually verify sample hypothesis precision
* **Calibration Application**: Apply calibrated scores to composite scoring -> verify downstream impact

### Test Data Requirements

* **Training Claims Data**: Jan 2018-Jun 2024 (78 months)
* **Holdout Claims Data**: Jul-Dec 2024 (6 months)
* **Full Period Findings**: Results from Fraud Detection Execution
* **Overlap Indicators**: Providers flagged in both training and holdout

### Success Criteria

* Holdout validation identifies reproducible detections with measurable false positive rate
* Precision metrics calculated and confidence tiers determined
* Hypotheses with high false positive rates identified
* Confidence scores calibrated to measured precision
* Performance ranking identifies best and worst hypotheses
* Calibrated scores enable better-prioritized investigation queues
