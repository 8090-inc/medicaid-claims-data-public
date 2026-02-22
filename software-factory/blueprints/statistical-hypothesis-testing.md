---
title: "Statistical Hypothesis Testing"
feature_name: null
id: "8c7c3f36-d36b-4342-9c44-ca755ba1184b"
---

## Feature Summary

Statistical Hypothesis Testing executes Categories 1-5 fraud detection hypotheses across five analyzer classes: Statistical Outlier Detection (Z-score, IQR, GEV, Benford's Law), Temporal Anomaly Detection (spikes, sudden appearance/disappearance, change-point analysis), Peer Comparisons (rate and volume outliers), Network Analysis (hub-and-spoke, circular billing), and Concentration Metrics (provider dominance, code concentration, HHI). Each analyzer produces findings with confidence scores, evidence strings, and financial impact estimates, totaling up to 600 testable hypotheses across provider populations.

## Component Blueprint Composition

This feature depends on the ingested claims data:

* **@Claims Data Ingestion** — Provides all six tables.
* **@Reference Data Enrichment** — Provides `providers` table with specialty and state data.

## Feature-Specific Components

```component
name: StatisticalAnalyzer
container: Fraud Detection Engine
responsibilities:
	- Execute Category 1 hypotheses (H0001-H0150)
	- Implement Z-score, IQR, GEV, and Benford's Law detection
```

```component
name: TemporalAnalyzer
container: Fraud Detection Engine
responsibilities:
	- Execute Category 2 hypotheses (H0151-H0270)
	- Implement spike, sudden appearance/disappearance, and change-point detection
```

```component
name: PeerAnalyzer
container: Fraud Detection Engine
responsibilities:
	- Execute Category 3 hypotheses (H0271-H0400)
	- Implement rate, volume, geographic, and specialty peer comparisons
```

```component
name: NetworkAnalyzer
container: Fraud Detection Engine
responsibilities:
	- Execute Category 4 hypotheses (H0401-H0520)
	- Implement hub-and-spoke, circular billing, and ghost network detection
```

```component
name: ConcentrationAnalyzer
container: Fraud Detection Engine
responsibilities:
	- Execute Category 5 hypotheses (H0521-H0600)
	- Implement provider dominance, single-code specialist, and HHI calculations
```

```component
name: FindingsAggregator
container: Fraud Detection Engine
responsibilities:
	- Orchestrate all analyzer classes
	- Accumulate and deduplicate findings
	- Serialize to findings/statistical_findings_categories_1_5.json
```

## System Contracts

### Key Contracts

* **Read-Only Database Access**: All analyzers query pre-aggregated tables without modification.
* **Hypothesis Testability**: Edge cases handled gracefully (skip, not error).
* **Confidence Score Semantics**: Range 0.6 to 0.99; higher = stronger evidence.
* **Financial Impact Semantics**: Conservative; provably questionable portion only.

### Integration Contracts

* **Input Tables**: All six tables from ingestion plus providers
* **Output**: `findings/statistical_findings_categories_1_5.json`
* **Downstream**: @Machine Learning uses findings for training; @Composite Scoring uses for aggregation

## Architecture Decision Records

### ADR-001: Per-Analyzer Classes Over Monolithic Executor

**Context:** Five different analytical approaches; monolithic code would be 5000+ lines.

**Decision:** Five separate analyzer classes + FindingsAggregator.

**Consequences:** Each analyzer ~500 lines, testable in isolation.

### ADR-002: Pre-Aggregated Tables vs. Raw Claims

**Context:** Computing statistics on every test run is expensive.

**Decision:** All analyzers operate on pre-aggregated summary tables.

**Consequences:** 100-1000x speedup; hypothesis testing completes in minutes.

### ADR-003: Confidence Score Calculation Strategy

**Context:** Different methods produce different types of evidence.

**Decision:** Each analyzer implements its own scoring formula normalized to [0.6, 0.99].

**Consequences:** Intuitive within-category; cross-category comparison handled by composite scoring.

## Testing & Validation

### Acceptance Tests

* **Category 1**: Verify Z-score, IQR, GEV, Benford's detection
* **Category 2**: Verify spike, sudden appearance/disappearance, change-point detection
* **Category 3**: Verify rate, volume, geographic, specialty peer comparisons
* **Category 4**: Verify hub-and-spoke, circular billing, ghost network detection
* **Category 5**: Verify provider dominance, single-code, HHI calculations
* **Findings Output**: Verify JSON generated with all required fields

### Unit Tests

* **StatisticalAnalyzer**: Test Z-score, IQR, GEV, Benford's calculations
* **TemporalAnalyzer**: Test spike detection, threshold scaling
* **PeerAnalyzer**: Test peer median calculations, outlier flagging
* **NetworkAnalyzer**: Test hub counting, circular billing detection
* **ConcentrationAnalyzer**: Test dominance share, HHI computation
* **FindingsAggregator**: Test deduplication, JSON serialization

### Integration Tests

* **End-to-End Execution**: Execute all five analyzers -> accumulate -> deduplicate -> serialize
* **Analyzer Independence**: Run each separately -> compare with full pipeline
* **Confidence Range**: Verify all scores in [0.6, 0.99]
* **Financial Impact Sanity**: Verify non-negative; verify sums reasonable

### Test Data Requirements

* **Input Tables**: All six tables plus enriched providers
* **Provider Mix**: Normal providers, outliers, temporal anomalies, hub-spoke networks

### Success Criteria

* All ~600 testable hypotheses executed
* Findings generated with confidence and impact
* JSON output complete and well-structured
* Deterministic reproducibility verified
