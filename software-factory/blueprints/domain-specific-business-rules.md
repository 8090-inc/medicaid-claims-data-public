---
title: "Domain-Specific Business Rules"
feature_name: null
id: "1afa2170-9ed9-4ddc-889b-075b6045588d"
---

## Feature Summary

Domain-Specific Business Rules executes Category 8 hypotheses encoding clinical impossibilities, regulatory violations, and known fraud schemes as deterministic SQL and Python rules. The feature validates impossible service volumes based on time constraints, detects upcoding through E&M level distribution analysis, identifies unbundling patterns, flags phantom billing indicators (flat amounts, zero variance, constant beneficiary counts), and applies high-risk category analysis to service types with elevated fraud prevalence (Home Health, Behavioral Health, Personal Care, ABA, DME, Transportation).

## Component Blueprint Composition

This feature depends on enriched claims data from earlier stages:

* **@Claims Data Ingestion** — Provides `provider_hcpcs`, `provider_monthly`, `hcpcs_summary` tables for volume and rate analysis.
* **@Reference Data Enrichment** — Provides `providers` table with specialty and entity type for high-risk category flagging.

## Feature-Specific Components

```component
name: ImpossibleVolumeDetector
container: Fraud Detection Engine
responsibilities:
	- Execute 15 impossible volume hypotheses (H0831-H0845) for timed service codes (T1019, T1020, T1005, S5125, H0015, H2015, H2016)
	- Define maximum units per beneficiary per month for each code based on unit duration (T1019 = 15-min units, max 480 = 120 hours/month)
	- Query provider_hcpcs table; flag providers where claims/beneficiaries exceeds physical maximum with paid > $10K
	- Calculate financial impact as 100% of payments above the physical maximum
	- Set confidence to 0.99 (deterministic violations)
```

```component
name: UpcodingDetector
container: Fraud Detection Engine
responsibilities:
	- Execute 15 upcoding hypotheses (H0846-H0860) targeting E&M code level distributions
	- For office visit families (99211-99215), calculate % of claims at highest level (99215); flag providers exceeding 2x or 3x specialty median
	- For ED visits (99281-99285), flag providers with 99285 rates exceeding 2x peer median
	- Detect progressive upcoding: average E&M level increasing monotonically over time
	- Estimate financial impact as difference between actual and peer median-expected revenue
```

```component
name: UnbundlingDetector
container: Fraud Detection Engine
responsibilities:
	- Execute 15 unbundling hypotheses (H0861-H0875) testing codes-per-beneficiary ratios
	- Flag providers with codes-per-beneficiary exceeding 3x peer median, sustained for 6+ months
	- Detect component code billing when bundle codes exist (lab panels vs individual tests, therapy evaluations vs components)
	- Identify same-day sequential code patterns suggesting unbundling
	- Calculate impact as difference between component sum and bundle rate
```

```component
name: PhantomBillingDetector
container: Fraud Detection Engine
responsibilities:
	- Execute 10 phantom billing hypotheses (H0876-H0885) detecting patterns: constant amounts, flat monthly billing, zero variance, round numbers, weekend/holiday concentration
	- Flag providers with identical billing amounts every month for 6+ consecutive months
	- Flag providers with beneficiary counts unchanging despite claims growth > 50%
	- Flag providers with monthly billing standard deviation < 5% of mean over 12+ months
	- Assign composite confidence: 1 indicator = 0.65, 2 indicators = 0.80, 3+ indicators = 0.95
```

```component
name: HighRiskCategoryAnalyzer
container: Fraud Detection Engine
responsibilities:
	- Execute 15 high-risk category hypotheses (H0886-H0900) for service types: Home Health, Behavioral Health, Personal Care, ABA Therapy, DME, Transportation
	- For Home Health: flag providers in top 1% by paid-per-claim AND > 50 servicing NPIs
	- For Behavioral Health: flag those exceeding state 95th percentile AND billing exclusively for one code
	- Combine category membership with additional red flags (rate outlier, volume outlier, network anomaly)
	- Boost confidence for providers in multiple high-risk categories
```

```component
name: DomainRulesExecutor
container: Fraud Detection Engine
responsibilities:
	- Orchestrate execution of all domain rule detectors
	- Implement rules as deterministic SQL queries or Python functions
	- Define TIMED_CODES constant list with unit durations and maximums
	- Define EM_FAMILIES dict mapping code families to ranges
	- Execute rules independently; accumulate findings by provider
	- Deduplicate findings by (provider_npi, hypothesis_id)
	- Serialize to findings/domain_findings_category_8.json
```

## System Contracts

### Key Contracts

* **Deterministic Rule Execution**: All domain rules produce same output given same input; no randomness or learning required.
* **Zero False Positives for Impossible Volumes**: Impossible volume violations are mathematical impossibilities and result in 0.99 confidence; these are deterministic fraud signals.
* **Multiple Violation Accumulation**: Providers violating multiple domain rules (e.g., impossible volume + phantom billing) have composite confidence increased.
* **Independence**: Each domain rule executes independently; a violation in one rule does not affect others.

### Integration Contracts

* **Input**: `provider_hcpcs`, `provider_monthly`, `hcpcs_summary`, `providers` tables
* **Output**: `findings/domain_findings_category_8.json` with fields: `{hypothesis_id, provider_npi, violation_type, confidence, evidence, financial_impact}`
* **Downstream Dependency**: @Cross-Reference and Composite Scoring weights domain findings (0.99 confidence = high weight) in final risk aggregation

## Architecture Decision Records

### ADR-001: Deterministic Rules Over Trained Models

**Context:** Domain fraud patterns (impossible volumes, upcoding, phantom billing) are well-understood violations that do not benefit from machine learning. Training a model introduces noise and reduces interpretability.

**Decision:** Implement domain rules as deterministic SQL and Python code. Each rule encodes a specific fraud pattern with clear thresholds, logic, and evidence trails.

**Consequences:**

* Benefits: Interpretability is perfect; findings are auditable and defensible; zero model overfitting risk
* Trade-off: Must manually maintain rule logic as billing landscape evolves; new patterns require manual rule creation
* Governance: Rules can be easily reviewed, approved, and modified by domain experts without retraining

### ADR-002: Time-Based Unit Limits for Timed Codes

**Context:** Personal care (T1019), homemaking (T1020), and other time-based codes have physical maximums determined by unit duration and calendar constraints.

**Decision:** Define TIMED_CODES constant with (code, unit_minutes, max_units_per_bene_per_month) tuples. For T1019 (15-min units), max = 480 units = 120 hours. Calculate claims/beneficiaries; flag if exceeds maximum.

**Consequences:**

* Benefits: Captures absolute fraud: billing more than 120 hours of personal care per beneficiary per month is physically impossible
* Trade-off: Requires external domain expertise to define correct maximums per code; incorrect maximums cause false positives/negatives
* Mitigation: Validate maximums with CMS guidance and subject matter experts

### ADR-003: Composite Confidence for Phantom Billing

**Context:** No single phantom billing indicator is definitive proof (e.g., constant amounts could be legitimate bulk billing; flat variance could be steady-state). Combining indicators increases confidence.

**Decision:** Assign base confidence 0.65 for one indicator. Add 0.15 per additional indicator (2 indicators = 0.80, 3+ = 0.95). This reflects increasing certainty as patterns converge.

**Consequences:**

* Benefits: Acknowledges that multiple weak signals are stronger than one; avoids false positives from isolated anomalies
* Trade-off: Phantom billing detected with 1 indicator are scored lower and may be missed in prioritization
* Sensitivity: Set indicator thresholds conservatively to capture true patterns while minimizing false positives

## Testing & Validation

### Acceptance Tests

* **Impossible Volumes (H0831-H0845)**: Verify 15 hypotheses execute on timed service codes; verify max units-per-beneficiary-per-month enforced (T1019=480 units=120 hours); verify providers exceeding maximum with paid > $10K flagged with 0.99 confidence; verify impact calculated as 100% of excess payment
* **Upcoding (H0846-H0860)**: Verify 15 hypotheses execute; verify E&M code level distribution analyzed; verify providers with 99215 (highest level) exceeding 2x-3x specialty median flagged; verify progressive upcoding (monotonic level increase over time) detected; verify impact calculated as excess revenue
* **Unbundling (H0861-H0875)**: Verify 15 hypotheses execute; verify codes-per-beneficiary exceeding 3x peer median flagged; verify sustained (6+ months) patterns identified; verify component code billing detected when bundles exist; verify same-day sequences identified; verify impact calculated as component-bundle differential
* **Phantom Billing (H0876-H0885)**: Verify 10 hypotheses execute; verify indicators detected: constant amounts (6+ months), flat billing, zero variance (<5% of mean over 12+ months), round numbers, weekend concentration; verify composite confidence scoring (1 indicator=0.65, 2=0.80, 3+=0.95); verify false-beneficiary-count (unchanged despite 50%+ claims growth) detected
* **High-Risk Categories (H0886-H0900)**: Verify 15 hypotheses execute; verify service types analyzed (Home Health, Behavioral Health, Personal Care, ABA, DME, Transportation); verify category-specific rules applied (Home Health: top 1% paid-per-claim AND >50 servicing NPIs; Behavioral Health: state 95th percentile AND single code); verify confidence boosted for multiple high-risk indicators

### Unit Tests

* **ImpossibleVolumeDetector**: Test max units constant definition; test units-per-beneficiary calculation; test threshold comparison; test impact calculation (100% excess)
* **UpcodingDetector**: Test E&M code level distribution; test specialty peer median comparison; test progressive upcoding curve fitting; test impact calculation (excess vs median)
* **UnbundlingDetector**: Test codes-per-beneficiary ratio; test peer median calculation; test 6-month sustainability check; test component-bundle matching; test same-day sequence detection
* **PhantomBillingDetector**: Test constant amount detection; test variance threshold (5% of mean); test round-number pattern; test beneficiary-count anomalies; test composite confidence scoring
* **HighRiskCategoryAnalyzer**: Test service type classification; test category-specific rule application; test confidence boosting; test combination signals
* **DomainRulesExecutor**: Test orchestration of all detectors; test independent rule execution; test finding accumulation; test deduplication by (npi, hypothesis_id)

### Integration Tests

* **End-to-End Domain Rules**: Execute all 70 hypotheses across 5 detector categories -> accumulate findings by provider -> deduplicate -> serialize to findings/domain_findings_category_8.json
* **Impossible Volume Accuracy**: Manually calculate max units for sample codes (T1019, H0015, etc.); compare provider violations to query results; verify within tolerance
* **Upcoding Pattern Detection**: Analyze E&M code distributions manually for sample specialty cohorts; verify program detects same patterns
* **Phantom Billing Indicator Combination**: Create test data with 0, 1, 2, 3+ phantom indicators; verify confidence scores scale correctly
* **High-Risk Category Assignment**: Verify providers classified correctly into service types based on code/specialty; verify multi-category providers scored higher
* **Deterministic Reproducibility**: Run domain rules twice on same data -> verify identical findings and scores

### Test Data Requirements

* **Provider HCPCS Data**: provider_hcpcs table with diverse volume patterns including impossible volumes, upcoding patterns, unbundling indicators
* **Temporal Data**: provider_monthly with constant-amount providers, flat-billing periods, and progressive growth patterns for phantom billing detection
* **Service Types**: Providers coded as Home Health, Behavioral Health, Personal Care, ABA, DME, Transportation for category analysis
* **High-Risk Patterns**: Providers combining multiple red flags

### Success Criteria

* All 70 domain rule hypotheses execute successfully
* findings/domain_findings_category_8.json generated with all violations identified
* Impossible volume violations detected with 0.99 confidence (deterministic fraud signals)
* Upcoding patterns identified; E&M code distributions analyzed correctly
* Unbundling indicators detected; component-bundle relationships understood
* Phantom billing indicators accumulate appropriately; composite confidence scores reflect evidence strength
* High-risk category analysis completed; category-specific thresholds applied
* Re-running domain rules produces identical findings (deterministic reproducibility verified)
* Findings serve as high-confidence input for composite scoring
