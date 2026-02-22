---
title: "Holdout Validation and Calibration"
type: "feature"
id: "66c11322-d02a-42c0-baf0-7247e1fc9bdf"
---

## Overview

This feature validates hypothesis performance using holdout temporal validation and calibrates confidence scores based on precision metrics. It tests hypotheses on the most recent 6 months of data after training on prior periods, calculates precision at various confidence thresholds, and adjusts confidence scores to align with actual positive predictive values.

Runs as Milestone 14 and ensures detection methods are validated before final scoring.

## Terminology

* **Holdout Validation**: Testing hypotheses on recent data not used during hypothesis design to measure true performance.
* **Precision**: The proportion of flagged providers that are true positives (TP / (TP + FP)).
* **Calibration**: Adjusting confidence scores so that a 0.80 confidence score means 80% precision.
* **Temporal Split**: Using last 6 months as validation set and prior 78 months as training/analysis set.
* **Confidence Tier Precision**: Measured precision for HIGH (>= 0.85), MEDIUM (0.65-0.84), and LOW (< 0.65) confidence tiers.

## Requirements

### REQ-VAL-001: Temporal Holdout Set Creation

**User Story:** As a data scientist, I want temporal holdout validation, so that I can measure hypothesis performance on unseen recent data.

**Acceptance Criteria:**

* **AC-VAL-001.1:** The system shall designate the last 6 months (Jul 2024 - Dec 2024) as the holdout validation set.
* **AC-VAL-001.2:** The system shall re-execute all testable hypotheses on the holdout period only.
* **AC-VAL-001.3:** The system shall compare holdout findings to full-period findings to identify hypothesis stability.
* **AC-VAL-001.4:** The system shall calculate per-hypothesis precision using known high-confidence findings from full period as ground truth approximation.

### REQ-VAL-002: Precision Calculation

**User Story:** As a fraud investigator, I want precision metrics, so that I understand the false positive rate of each detection method.

**Acceptance Criteria:**

* **AC-VAL-002.1:** For each hypothesis, the system shall calculate precision as: (num flagged in both full and holdout) / (num flagged in holdout).
* **AC-VAL-002.2:** The system shall calculate precision by confidence tier: HIGH, MEDIUM, LOW.
* **AC-VAL-002.3:** The system shall flag hypotheses with precision < 0.50 as "high_false_positive_rate".
* **AC-VAL-002.4:** The system shall save precision metrics to `validation_precision_by_hypothesis.csv` with columns: hypothesis_id, method, holdout_findings, full_period_findings, overlap, precision, confidence_tier_precision.

### REQ-VAL-003: Confidence Score Calibration

**User Story:** As a risk manager, I want calibrated confidence scores, so that a score accurately reflects the likelihood of true fraud.

**Acceptance Criteria:**

* **AC-VAL-003.1:** The system shall calculate the gap between nominal confidence scores and measured precision for each method.
* **AC-VAL-003.2:** The system shall apply calibration adjustments reducing confidence scores for methods with precision < nominal confidence.
* **AC-VAL-003.3:** The system shall not increase confidence scores during calibration (conservative approach).
* **AC-VAL-003.4:** The system shall save calibrated confidence scores to a lookup table for use in final scoring.
* **AC-VAL-003.5:** The system shall generate a calibration report `confidence_calibration_report.md` showing before/after precision and recommended adjustments.

### REQ-VAL-004: Hypothesis Performance Ranking

**User Story:** As a pipeline administrator, I want hypotheses ranked by validation performance, so that I can prioritize effective detection methods.

**Acceptance Criteria:**

* **AC-VAL-004.1:** The system shall rank hypotheses by validation performance score = precision * finding_count * avg_impact.
* **AC-VAL-004.2:** The system shall identify top 20 best-performing hypotheses and bottom 20 worst-performing hypotheses.
* **AC-VAL-004.3:** The system shall recommend hypotheses for retirement (precision < 0.30 consistently) or enhanced tuning.
* **AC-VAL-004.4:** The system shall save rankings to `hypothesis_performance_ranking.csv`.

## Feature Behavior & Rules

Holdout validation assumes the most recent 6 months are representative of future data. Precision calculation treats multi-method flagging as positive signal. Calibration uses isotonic regression or linear scaling. Hypotheses with fewer than 10 findings in holdout are marked as insufficient_sample. State-specific and code-specific hypotheses may have lower precision due to parameter specificity. Network and temporal hypotheses tend to have higher precision than pure statistical outliers.
