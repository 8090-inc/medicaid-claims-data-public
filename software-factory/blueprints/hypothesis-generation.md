---
title: "Hypothesis Generation"
feature_name: null
id: "6a0024bd-4f8d-4f0c-b421-a8533f5aabc3"
---

## Feature Summary

Hypothesis Generation programmatically creates 1,000+ structured fraud detection hypotheses in JSON format, organized into 10 analytical categories (statistical outliers, temporal anomalies, peer comparisons, network analysis, concentration, classical ML, deep learning, domain rules, cross-reference, composite scoring). Each hypothesis defines specific detection parameters, acceptance criteria, and financial impact calculation methods. The feature establishes the structured testing framework for all downstream fraud detection, enabling systematic hypothesis execution and evidence-based fraud investigation.

## Component Blueprint Composition

This feature depends on exploratory analysis for parametrization:

* **@Exploratory Data Analysis** — Provides data profile statistics (top codes, concentrations, distributions) used to parametrize hypothesis templates.

## Feature-Specific Components

```component
name: Category1StatisticalHypothesisGenerator
container: Hypothesis Engine
responsibilities:
	- Generate 150 Category 1 hypotheses for statistical outlier detection
	- Subcategory 1A: 30 Z-score hypotheses on paid-per-claim for top 30 HCPCS codes
	- Subcategory 1B: 30 Z-score hypotheses on claims-per-beneficiary for top 30 HCPCS codes
	- Subcategory 1C: 30 Z-score hypotheses on paid-per-beneficiary for top 30 HCPCS codes
	- Subcategory 1D: 7 IQR hypotheses across 7 provider-level metrics
	- Subcategory 1E: 20 GEV extreme value hypotheses across HCPCS categories
	- Subcategory 1F: 20 Benford's Law and pattern hypotheses
```

```component
name: Category2TemporalHypothesisGenerator
container: Hypothesis Engine
responsibilities:
	- Generate 120 Category 2 hypotheses for temporal anomaly detection
	- Subcategory 2A: 20 month-over-month spike hypotheses with 3x/5x/10x thresholds
	- Subcategory 2B: 15 sudden appearance hypotheses with varying first-month thresholds
	- Subcategory 2C: 15 sudden disappearance hypotheses
	- Subcategory 2D: 15 year-over-year growth hypotheses
	- Subcategory 2H: 15 change-point detection hypotheses (CUSUM, PELT, variance-change)
```

```component
name: Category3PeerComparisonHypothesisGenerator
container: Hypothesis Engine
responsibilities:
	- Generate 130 Category 3 hypotheses for peer-based detection
	- Subcategory 3A: 30 rate-vs-peers hypotheses (2x median paid-per-claim) for top 30 codes
	- Subcategory 3B: 20 volume-vs-peers hypotheses (10x median claims)
	- Subcategory 3C: 20 beneficiary-concentration hypotheses (3x median claims-per-bene)
	- Subcategory 3D-3F: 60 geographic, specialty, and size-tier comparison hypotheses
```

```component
name: Category4NetworkHypothesisGenerator
container: Hypothesis Engine
responsibilities:
	- Generate 120 Category 4 hypotheses for network fraud detection
	- Subcategory 4A: 20 hub-and-spoke hypotheses with varying servicing NPI counts (>50, >100, >200)
	- Subcategory 4B: 20 shared servicing hypotheses (>10, >20, >50 billing NPIs per servicing)
	- Subcategory 4C: 15 circular billing hypotheses with payment thresholds $50K-$500K
	- Subcategory 4G: 20 ghost network hypotheses (missing NPPES, deactivated, single-biller)
	- Subcategory 4D-4F: 45 network density, new network, and pure billing entity hypotheses
```

```component
name: Category5Through10HypothesisGenerator
container: Hypothesis Engine
responsibilities:
	- Generate 80 Category 5 hypotheses for concentration (provider dominance, single-code, HHI)
	- Generate 150 Category 6 hypotheses for classical ML (Isolation Forest, DBSCAN, Random Forest, XGBoost, K-means, LOF)
	- Generate 80 Category 7 hypotheses for deep learning (Autoencoder, VAE, LSTM, Transformer)
	- Generate 100 Category 8 hypotheses for domain rules (impossible volumes, upcoding, unbundling, phantom billing, adjustments)
	- Generate 70 Category 9 hypotheses for cross-reference (specialty mismatches, entity types, geographic, NPPES, LEIE)
	- Generate composite Category 10 hypotheses combining multi-method signals
```

```component
name: GapAnalysisHypothesisGenerator
container: Hypothesis Engine
responsibilities:
	- Generate 100 gap analysis hypotheses (H1001-H1100) targeting high-risk domains
	- Generate 15 ABA therapy fraud hypotheses (codes 97151-97158, H0031-H0032)
	- Generate 10 pharmacy fraud hypotheses
	- Generate 10 addiction treatment fraud hypotheses (H0001-H0020, G0396-G0397)
	- Generate 10 kickback/referral concentration hypotheses
	- Generate 10 sober home hypotheses
	- Generate additional specialized hypotheses: genetic testing, beneficiary anomalies, transportation, address-based schemes, advanced analytics
```

```component
name: HypothesisStructureValidator
container: Hypothesis Engine
responsibilities:
	- Validate each generated hypothesis contains required JSON fields: id, category, subcategory, description, method, acceptance_criteria, analysis_function, financial_impact_method, parameters
	- Verify hypothesis ids follow H#### format with zero-padded 4-digit sequential numbering
	- Verify category field is '1'-'10'
	- Assert total core hypotheses = 1,000 (H0001-H1000), gap analysis = 100 (H1001-H1100)
```

```component
name: HypothesisSerializer
container: Hypothesis Engine
responsibilities:
	- Organize hypotheses into batch files of 50-120 hypotheses each
	- Save as batch_XX.json files in output/hypotheses/ directory
	- Format JSON with indent=2 for human readability
	- Log hypothesis counts per category and batch
```

## System Contracts

### Key Contracts

* **Deterministic Generation**: Same code + same parameters = same hypotheses every time.
* **Completeness**: Exactly 1,000 core hypotheses + 100 gap analysis = 1,100 total.
* **Structure Consistency**: All hypotheses follow identical JSON schema.

### Integration Contracts

* **Input**: Data profile from @Exploratory Data Analysis
* **Output**: `output/hypotheses/batch_XX.json` files
* **Downstream Dependency**: @Hypothesis Feasibility Matrix and @Fraud Detection Execution

## Architecture Decision Records

### ADR-001: Parametric Hypothesis Templates Over Hardcoded Rules

**Context:** Manually defining 1,000 hypotheses would introduce errors and be unmaintainable.

**Decision:** Define hypothesis templates. Instantiate using lists of codes, metrics, and parameters.

**Consequences:**

* Benefits: 1,000 hypotheses generated in minutes; easy to extend
* Trade-off: Requires careful constant definitions
* Maintainability: Adding new hypotheses = updating constants or adding a new generator function

### ADR-002: 10-Category Taxonomy

**Context:** Fraud manifests in diverse ways. A single detection method misses patterns.

**Decision:** Organize hypotheses into 10 analytical categories.

**Consequences:**

* Benefits: Comprehensive coverage; multiple independent detection paths
* Trade-off: 1,000+ hypotheses is large; requires efficient execution
* Mitigation: Feasibility matrix filters to testable hypotheses

### ADR-003: Gap Analysis Beyond Taxonomy

**Context:** Systematic hypotheses may miss domain-specific patterns.

**Decision:** Generate additional 100 gap analysis hypotheses targeting high-risk domains.

**Consequences:**

* Benefits: Leverages fraud expertise; captures known patterns
* Trade-off: Gap hypotheses less generalizable

## Testing & Validation

### Acceptance Tests

* **Core Hypothesis Count**: Verify exactly 1,000 core + 100 gap = 1,100 total
* **Category Distribution**: Verify counts match specification per category
* **JSON Structure**: Verify all required fields present in every hypothesis
* **Batch Organization**: Verify batch files created with proper sizing

### Unit Tests

* **HypothesisStructureValidator**: Test JSON schema validation; test ID format; test category validation
* **Category Generators**: Test template instantiation; test count accuracy per category
* **HypothesisSerializer**: Test batch file creation; test JSON formatting

### Integration Tests

* **Full Generation**: Run all generators -> validate structure -> verify total counts -> verify no duplicates
* **Parametrization Accuracy**: Verify parameters match EDA data profile
* **Idempotency**: Run twice -> verify identical hypotheses generated

### Test Data Requirements

* **EDA Input**: data_profile.json with top codes and concentration metrics
* **Constants**: TOP_30_CODES, METRICS, SPECIALTIES, STATES lists

### Success Criteria

* Exactly 1,100 hypotheses generated
* All hypotheses follow consistent JSON schema
* Category distribution matches specification
* Hypothesis IDs sequential and zero-padded
* Batch files created with proper organization
* Re-running produces identical hypothesis set
