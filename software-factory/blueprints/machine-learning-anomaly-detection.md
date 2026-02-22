---
title: "Machine Learning Anomaly Detection"
feature_name: null
id: "305b922c-5eff-40d0-9d92-8af9dcc2ec13"
---

## Feature Summary

Machine Learning Anomaly Detection executes Category 6 hypotheses using scikit-learn models (Isolation Forest, DBSCAN, K-means, LOF) and semi-supervised XGBoost trained on high-confidence findings from Categories 1-5. The feature transforms provider-level features into normalized vectors, trains unsupervised and semi-supervised models, and flags providers with extreme anomaly scores or distance metrics. This complements statistical methods with multidimensional pattern recognition, capturing fraud patterns not visible in univariate analysis.

## Component Blueprint Composition

This feature depends on findings and data from earlier analysis stages:

* **@Claims Data Ingestion** — Provides `provider_summary`, `provider_hcpcs`, and `providers` tables for feature extraction.
* **@Statistical Hypothesis Testing** — Provides high-confidence findings (confidence >= 0.85) for semi-supervised XGBoost training.

## Feature-Specific Components

```component
name: FeatureEngineer
container: Fraud Detection Engine
responsibilities:
	- Extract provider-level features from provider_summary and provider_hcpcs tables
	- Features include: total_paid, total_claims, total_beneficiaries, avg_paid_per_claim, avg_claims_per_bene, num_codes, num_months, top_code_concentration
	- Apply StandardScaler normalization to all numeric features
	- Handle missing values using median imputation
	- Create segment-specific feature sets for home health, behavioral health, and high-volume providers
```

```component
name: IsolationForestExecutor
container: Fraud Detection Engine
responsibilities:
	- Execute 40 Isolation Forest hypotheses (H0601-H0640) across overall and segment-specific models
	- Train Isolation Forest with contamination=0.01 to flag top 1% anomalous providers
	- Flag providers with anomaly_score < -0.5 and total_paid > $100K
	- Record feature contributions to anomaly scores for interpretability
	- Calculate confidence as min(0.95, 0.60 + 0.30 * |anomaly_score|)
```

```component
name: XGBoostSemiSupervisedExecutor
container: Fraud Detection Engine
responsibilities:
	- Execute 30 XGBoost hypotheses (H0691-H0720) using semi-supervised learning
	- Create training labels from statistical findings with confidence >= 0.85
	- Train XGBoost with max_depth=6, n_estimators=100, learning_rate=0.1
	- Flag providers with predicted fraud probability > 0.8 not already flagged by Categories 1-5
	- Save feature importance rankings for model interpretation
```

```component
name: DBSCANExecutor
container: Fraud Detection Engine
responsibilities:
	- Execute DBSCAN clustering hypotheses (30 hypotheses)
	- Identify noise points (cluster=-1) and small clusters (size <= 3) with total_paid > $100K
	- Flag providers in sparse regions of feature space as anomalous
```

```component
name: KMeansExecutor
container: Fraud Detection Engine
responsibilities:
	- Execute K-means clustering hypotheses (15 hypotheses)
	- Train K-means with k=20 clusters
	- Flag providers with distance > 3x cluster mean distance
```

```component
name: LOFExecutor
container: Fraud Detection Engine
responsibilities:
	- Execute Local Outlier Factor hypotheses (15 hypotheses)
	- Flag providers with LOF score > 2.0 using n_neighbors=20
```

```component
name: MLFindingsAggregator
container: Fraud Detection Engine
responsibilities:
	- Orchestrate execution of all ML model executors
	- Accumulate findings from all executors
	- Deduplicate findings by (provider_npi, hypothesis_id)
	- Calculate overlap with Categories 1-5 findings for novelty assessment
	- Serialize to findings/ml_findings_category_6.json
```

## System Contracts

### Key Contracts

* **Feature Vector Consistency**: All models operate on the same normalized feature vectors.
* **Semi-Supervised Training**: XGBoost uses only high-confidence findings (>= 0.85).
* **Model Reproducibility**: Models trained with fixed random seeds for deterministic results.
* **Segment-Specific Isolation**: Home Health, Behavioral Health, and high-volume models trained separately.

### Integration Contracts

* **Input**: `provider_summary`, `provider_hcpcs`, `providers` tables; high-confidence findings
* **Output**: `findings/ml_findings_category_6.json`
* **Downstream Dependency**: @Cross-Reference and Composite Scoring aggregates ML findings

## Architecture Decision Records

### ADR-001: Scikit-Learn Over Custom ML Implementations

**Context:** Implementing algorithms from scratch would be error-prone and maintenance-heavy.

**Decision:** Use scikit-learn implementations for all clustering and density-based methods.

**Consequences:**

* Benefits: Production-ready, well-tested algorithms
* Trade-off: Dependency on scikit-learn
* Mitigation: Pin version for reproducibility

### ADR-002: Semi-Supervised XGBoost Training

**Context:** Unsupervised models can detect outliers but may miss subtle patterns.

**Decision:** Use semi-supervised approach with high-confidence findings as pseudo-labels.

**Consequences:**

* Benefits: Captures patterns from statistical methods; generalizes to novel examples
* Trade-off: Pseudo-labels may have ~5-10% error
* Mitigation: Only use findings with confidence >= 0.85

### ADR-003: Segment-Specific Models

**Context:** Different service segments have different billing patterns.

**Decision:** Train separate models for home health, behavioral health, and high-volume providers.

**Consequences:**

* Benefits: Segment-specific anomalies not masked by global patterns
* Trade-off: Training overhead increases

## Testing & Validation

### Acceptance Tests

* **Isolation Forest**: Verify 40 hypotheses executed; verify anomaly scores calculated; verify confidence scaling
* **XGBoost**: Verify 30 hypotheses executed; verify semi-supervised training; verify feature importance
* **DBSCAN**: Verify clustering; verify noise point identification
* **K-Means**: Verify clustering with k=20; verify distance thresholds
* **LOF**: Verify LOF scores; verify threshold application
* **Aggregation**: Verify findings accumulated and deduplicated

### Unit Tests

* **FeatureEngineer**: Test feature extraction; test normalization; test imputation
* **IsolationForestExecutor**: Test model training; test anomaly score calculation
* **XGBoostSemiSupervisedExecutor**: Test pseudo-label creation; test model training
* **DBSCANExecutor**: Test clustering; test noise detection
* **KMeansExecutor**: Test k-means training; test distance calculations
* **LOFExecutor**: Test LOF computation
* **MLFindingsAggregator**: Test orchestration; test deduplication

### Integration Tests

* **End-to-End ML Pipeline**: Extract features -> train all models -> accumulate findings -> serialize
* **Novelty Detection**: Compare ML findings with Categories 1-5 findings -> verify novel_flag accurate
* **Reproducibility**: Run twice with same data and seed -> verify identical findings

### Test Data Requirements

* **Input Tables**: provider_summary, provider_hcpcs, providers; high-confidence findings
* **Provider Mix**: Normal providers, outliers, hub-spoke networks, high-concentration specialists

### Success Criteria

* All ~130 ML hypotheses executed
* Findings generated with required fields
* All model types execute successfully
* Novel findings identified
* Reproducibility verified
