---
title: "Machine Learning Anomaly Detection"
type: "feature"
id: "46305153-c177-4cf8-8fc2-b7f4d8247f52"
---

## Overview

This feature executes Category 6 hypotheses using classical machine learning models including Isolation Forest, DBSCAN, Random Forest, XGBoost, K-means, and LOF to detect multidimensional anomalies not captured by univariate statistical tests. It transforms provider-level features into normalized vectors, trains unsupervised and semi-supervised models, and flags providers with extreme anomaly scores or distance metrics.

Runs as Milestone 6 in the pipeline and complements statistical methods with ML-based pattern recognition.

## Terminology

* **Isolation Forest**: Unsupervised anomaly detection that isolates outliers using random decision trees.
* **DBSCAN**: Density-based clustering that identifies noise points as anomalies.
* **XGBoost Semi-Supervised**: Trains on high-confidence findings from Categories 1-5 to predict novel anomalies.
* **LOF (Local Outlier Factor)**: Anomaly detection based on local density deviations.
* **Feature Vector**: Normalized provider metrics (total_paid, claims_per_bene, num_codes, etc.) used as ML model inputs.

## Requirements

### REQ-ML-001: Feature Engineering and Normalization

**User Story:** As a data scientist, I want provider data transformed into normalized feature vectors, so that ML models can detect multidimensional anomalies.

**Acceptance Criteria:**

* **AC-ML-001.1:** The system shall extract provider-level features including total_paid, total_claims, total_beneficiaries, avg_paid_per_claim, avg_claims_per_bene, num_codes, num_months, specialty, state, and top_code_concentration.
* **AC-ML-001.2:** The system shall apply StandardScaler normalization to all numeric features before model training.
* **AC-ML-001.3:** The system shall handle missing values using median imputation for numeric features.
* **AC-ML-001.4:** The system shall create segment-specific feature sets for home health, behavioral health, and high-volume providers where specified by hypotheses.

### REQ-ML-002: Isolation Forest Execution

**User Story:** As a fraud analyst, I want Isolation Forest anomaly detection, so that I can identify providers with unusual multidimensional profiles.

**Acceptance Criteria:**

* **AC-ML-002.1:** The system shall execute 40 Isolation Forest hypotheses (H0601-H0640) across overall and segment-specific models.
* **AC-ML-002.2:** The system shall train Isolation Forest with contamination=0.01 to flag the top 1% most anomalous providers.
* **AC-ML-002.3:** The system shall flag providers with anomaly_score < -0.5 and total_paid > $100K.
* **AC-ML-002.4:** The system shall record which features contributed most to each provider's anomaly score.
* **AC-ML-002.5:** Confidence scores shall be calculated as min(0.95, 0.60 + 0.30 * |anomaly_score|).

### REQ-ML-003: XGBoost Semi-Supervised Learning

**User Story:** As a machine learning engineer, I want XGBoost trained on known findings, so that I can discover novel fraud patterns not detected by statistical methods.

**Acceptance Criteria:**

* **AC-ML-003.1:** The system shall execute 30 XGBoost hypotheses (H0691-H0720) using semi-supervised learning.
* **AC-ML-003.2:** The system shall create training labels from high-confidence findings (confidence >= 0.85) from Categories 1-5.
* **AC-ML-003.3:** The system shall train XGBoost with max_depth=6, n_estimators=100, learning_rate=0.1.
* **AC-ML-003.4:** The system shall flag providers with predicted fraud probability > 0.8 that were not already flagged by Categories 1-5.
* **AC-ML-003.5:** The system shall save feature importance rankings for model interpretability.

### REQ-ML-004: Clustering and Distance-Based Methods

**User Story:** As a fraud investigator, I want clustering methods, so that I can identify providers that don't fit any normal billing pattern.

**Acceptance Criteria:**

* **AC-ML-004.1:** The system shall execute DBSCAN (30 hypotheses), K-means (15 hypotheses), and LOF (15 hypotheses).
* **AC-ML-004.2:** For DBSCAN, the system shall flag noise points (cluster=-1) and small clusters (size <= 3) with total_paid > $100K.
* **AC-ML-004.3:** For K-means, the system shall train with k=20 clusters and flag providers with distance > 3x cluster mean distance.
* **AC-ML-004.4:** For LOF, the system shall flag providers with LOF score > 2.0 using n_neighbors=20.
* **AC-ML-004.5:** The system shall save all ML findings to `findings/ml_findings_category_6.json`.

### REQ-ML-005: Model Validation and Output

**User Story:** As a quality assurance analyst, I want ML model performance tracked, so that I can assess detection effectiveness.

**Acceptance Criteria:**

* **AC-ML-005.1:** The system shall log the number of providers flagged by each ML method.
* **AC-ML-005.2:** The system shall calculate and log the overlap between ML findings and statistical findings (Categories 1-5).
* **AC-ML-005.3:** The system shall report novel findings (detected by ML but not by statistical methods) separately.
* **AC-ML-005.4:** The system shall save trained models to `models/` directory for reproducibility.

## Feature Behavior & Rules

All ML models use scikit-learn implementations. Feature vectors are constructed from provider_summary and provider_hcpcs aggregations. Segment-specific models (home health, behavioral health) filter data before training. XGBoost uses stratified sampling to balance positive examples from Categories 1-5 findings. All models are trained fresh each pipeline run; no incremental learning. Missing specialty or state values are treated as a separate category rather than imputed.
