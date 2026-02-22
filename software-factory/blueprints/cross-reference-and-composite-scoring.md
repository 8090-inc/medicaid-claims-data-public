---
title: "Cross-Reference and Composite Scoring"
feature_name: null
id: "29d4f2df-293b-4f1e-8908-e9214c217c11"
---

## Feature Summary

Cross-Reference and Composite Scoring validates provider credentials against external registries (NPPES, LEIE, state licensing), detects specialty mismatches and entity type violations, calculates multi-method composite risk scores, and produces a final ranked fraud risk assessment. The feature executes Category 9 cross-reference validation, Category 10 composite scoring, integrates findings from all prior detection methods (Categories 1-8), and flags high-risk providers appearing across multiple analytical dimensions for prioritized investigation.

## Component Blueprint Composition

This feature integrates findings and data from all prior fraud detection stages:

* **@Claims Data Ingestion** — Provides `provider_summary`, `billing_servicing_network` for validation.
* **@Statistical Hypothesis Testing** — Provides Category 1-5 findings.
* **@Machine Learning Anomaly Detection** — Provides Category 6 findings.
* **@Domain-Specific Business Rules** — Provides Category 8 findings.
* **@Reference Data Enrichment** — Provides NPPES and LEIE reference data in `providers` table.

## Feature-Specific Components

```component
name: NPPESValidator
container: Fraud Detection Engine
responsibilities:
	- Execute NPPES validation hypotheses checking for NPIs not found in NPPES, deactivated NPIs, mismatched addresses, mismatched specialties
	- Query providers table for missing NPPES records; flag with confidence 0.95 if total_paid > $100K
	- Identify billing from deactivated NPPES NPIs (check deactivation date against claim_month)
	- Compare NPPES-registered state to claims state; flag interstate billing without multi-state location records
	- Validate provider entity type (Individual Type 1 vs Organization Type 2) against billing patterns
```

```component
name: LEIEValidator
container: Fraud Detection Engine
responsibilities:
	- Execute LEIE validation hypotheses checking if any billing NPI appears in exclusion database
	- Perform exact NPI match; also attempt fuzzy name/address matching to catch obfuscated re-entries
	- Flag any provider billing despite LEIE exclusion with confidence 0.99 and 100% of payments as potentially improper
	- Track exclusion date relative to claim months to identify violations of exclusion period
```

```component
name: SpecialtyValidator
container: Fraud Detection Engine
responsibilities:
	- Execute specialty mismatch hypotheses comparing billed HCPCS codes to NPPES-registered specialty
	- Use HCPCS-to-specialty mapping tables to validate clinical appropriateness per code
	- Flag Individual (Type 1) NPIs with organizational-scale patterns: > 100 servicing NPIs, > $10M total_paid; confidence 0.85
	- Flag Organization (Type 2) NPIs with individual patterns: single servicing NPI, narrow code range; confidence 0.85
	- Set specialty mismatch confidence to 0.75
```

```component
name: GeographicValidator
container: Fraud Detection Engine
responsibilities:
	- Execute geographic validation hypotheses comparing claim state to NPPES-registered state
	- Flag providers billing in multiple states without corresponding NPPES practice locations
	- Detect beneficiary state distributions inconsistent with provider location (e.g., 80% FL beneficiaries for NY provider)
	- Flag known mail-drop addresses or suspicious address patterns (PO boxes for high-volume billers, residential for organizations)
```

```component
name: CompositeScorer
container: Fraud Detection Engine
responsibilities:
	- Load findings from all prior milestones (Categories 1-9) and merge by provider NPI
	- For each provider, calculate composite_score = sum(method_confidence * method_impact) across flagged methods
	- Count num_methods = distinct analytical categories that flagged the provider
	- Assign confidence tiers: HIGH (num_methods >= 3 OR composite_score >= 8.0), MEDIUM (num_methods = 2 OR composite_score >= 4.0), LOW (num_methods = 1 OR composite_score >= 2.0)
	- Flag providers in 5+ categories as "systemic_fraud_pattern" with elevated priority
	- Aggregate total financial impact across all findings per provider; deduplicate overlapping amounts
```

```component
name: FinalFindingsIntegrator
container: Fraud Detection Engine
responsibilities:
	- Create consolidated findings file findings/final_scored_findings.json
	- Output fields: npi, name, state, specialty, confidence_tier, num_methods, composite_score, total_impact, methods_flagged, evidence_summary
	- Generate summary statistics: total findings, confidence tier distribution, total estimated recoverable, top 10 methods by impact
	- Rank providers by composite_score (descending) for prioritized investigation queue
	- Save cross-reference findings to findings/crossref_findings_category_9.json
	- Produce human-readable summary for downstream reporting
```

## System Contracts

### Key Contracts

* **Reference Data Completeness**: Cross-reference validation requires NPPES and LEIE data from Milestone 2. Missing reference data causes hypotheses to be skipped with warning logged.
* **Composite Score Semantics**: Score is weighted sum of confidence and impact; higher scores indicate more evidence and higher financial impact. Scores are not probabilities but relative risk rankings.
* **Deduplication Strategy**: Overlapping financial impact (e.g., same billing appearing in both rate outlier and volume outlier findings) is deduplicated at provider level; total_impact is the maximum amount provably questionable, not the sum.
* **Reproducibility**: Composite scoring is deterministic; same input findings produce identical scores and rankings.

### Integration Contracts

* **Input**: All prior findings (Categories 1-9 JSON files); `providers` table with NPPES and LEIE enrichment; `provider_summary` and `billing_servicing_network` tables
* **Output**:
  * `findings/final_scored_findings.json` — Ranked provider risk list
  * `findings/crossref_findings_category_9.json` — Cross-reference findings detail
  * Summary statistics and evidence document
* **Downstream Dependency**: Feeds into @Reporting and Visualization for dashboard, @Impact Quantification for financial analysis, and investigation prioritization

## Architecture Decision Records

### ADR-001: Composite Score as Weighted Evidence Accumulation

**Context:** Combining findings from 10 different analytical methods with different confidence distributions is non-trivial. A simple average obscures impact magnitude; a maximum obscures evidence accumulation.

**Decision:** Composite score = sum(method_confidence * method_impact) normalized to [0, 10] range. This weights confidence by financial impact; multiple moderate-confidence findings can accumulate to high risk.

**Consequences:**

* Benefits: Captures both evidence strength and financial significance; a single 0.99-confidence finding with $5K impact scores lower than three 0.75-confidence findings totaling $1M impact
* Trade-off: Score magnitude is less intuitive than percentage-based probabilities
* Mitigation: Pair scores with confidence tiers (HIGH/MEDIUM/LOW) for user interpretation

### ADR-002: Multi-Method Flagging as Systemic Pattern Indicator

**Context:** A provider flagged by a single method might be a false positive. A provider flagged by 5+ independent analytical methods is very unlikely to be innocent.

**Decision:** Count num_methods = distinct categories (1-9) that flagged the provider. Flag providers with num_methods >= 5 as "systemic_fraud_pattern" with priority boost.

**Consequences:**

* Benefits: Multi-method flagging has near-zero false positive rate; indicates coordinated, sophisticated fraud
* Trade-off: Single-method findings (even with high confidence) are scored lower; may miss focused fraud schemes
* Sensitivity: Ensure each detection category is truly independent to avoid inflating method counts through correlated detections

### ADR-003: Reference Data Graceful Degradation

**Context:** NPPES and LEIE data may be incomplete, stale, or unavailable. Validation should not fail the entire pipeline.

**Decision:** If reference data is missing or incomplete, cross-reference hypotheses are skipped with warning logged. Composite score calculation proceeds without those methods.

**Consequences:**

* Benefits: Pipeline robustness; allows continued operation with partial data
* Trade-off: Findings are incomplete; cross-reference findings are underweighted if reference data unavailable
* Monitoring: Surface data quality warnings to operators so missing reference data can be corrected

## Testing & Validation

### Acceptance Tests

* **Category 9 Cross-Reference**: Verify NPPES validation (missing NPIs, deactivated NPIs, address/specialty mismatches) executed
* **Category 9 Cross-Reference**: Verify LEIE validation (excluded provider billing) executed with 0.99 confidence; verify fuzzy name/address matching attempted
* **Category 9 Cross-Reference**: Verify specialty mismatch detected for individual/organization type violations; verify geographic validation executed
* **Composite Scoring**: Verify composite_score = sum(method_confidence * method_impact) calculated per provider
* **Composite Scoring**: Verify num_methods counts distinct analytical categories flagging provider; verify confidence tiers assigned (HIGH >= 3 methods OR score >= 8.0; MEDIUM >= 2 methods OR score >= 4.0)
* **Systemic Pattern Flagging**: Verify providers flagged in >= 5 categories marked as "systemic_fraud_pattern"
* **Financial Impact**: Verify total impact aggregated across all findings per provider; verify overlapping amounts deduplicated
* **Final Output**: Verify final_scored_findings.json generated with npi, name, state, specialty, confidence_tier, num_methods, composite_score, total_impact, methods_flagged, evidence_summary fields

### Unit Tests

* **NPPESValidator**: Test missing NPI detection; test deactivation date validation; test address/specialty comparison; test entity type validation
* **LEIEValidator**: Test exact NPI matching; test fuzzy name/address matching; test exclusion date comparison with claim periods
* **SpecialtyValidator**: Test HCPCS-specialty mapping; test individual/organization type pattern detection; test specialty mismatch confidence assignment
* **GeographicValidator**: Test state mismatch detection; test beneficiary distribution analysis; test suspicious address pattern detection (PO boxes, mail-drops)
* **CompositeScorer**: Test composite score calculation (confidence * impact summation); test confidence tier assignment; test method counting; test financial impact aggregation
* **FinalFindingsIntegrator**: Test findings consolidation from all categories; test ranking by composite score; test summary statistics generation; test JSON serialization

### Integration Tests

* **End-to-End Cross-Reference & Scoring**: Load findings from all categories (1-9) -> validate providers via NPPES/LEIE/specialty/geographic -> calculate composite scores -> assign confidence tiers -> rank by score -> serialize to JSON
* **Multi-Category Aggregation**: Load 9 separate findings files -> merge by NPI -> count method flags per provider -> verify num_methods accurate -> verify composite score correctly combines all evidence
* **Reference Data Handling**: Run with complete NPPES/LEIE data -> run with incomplete data -> verify graceful degradation; verify warnings logged for missing reference data
* **Deduplication Strategy**: Create overlapping findings (e.g., provider flagged in both rate outlier and volume outlier with same impact) -> verify total_impact deduplicated correctly
* **Reproducibility**: Run cross-reference & scoring twice with same findings input -> verify identical final_scored_findings.json output; verify provider ranking unchanged

### Test Data Requirements

* **All Prior Findings**: Categories 1-9 JSON files with diverse providers and impact values
* **Reference Data**: NPPES provider table with mix of valid/deactivated/mismatched providers; LEIE list with excluded NPIs
* **Provider Mix**: Flagged by 1, 2, 3, 5+ categories; varying composite score ranges; overlapping findings from different detection methods

### Success Criteria

* All cross-reference validation hypotheses executed
* final_scored_findings.json generated with all providers ranked by composite_score
* Confidence tiers correctly assigned based on num_methods and composite_score
* Systemic fraud pattern providers (5+ methods) identified and elevated
* Financial impact aggregated without double-counting overlapping findings
* Multi-method findings show near-zero false positive rate; single-method findings properly weighted lower
* Reference data missing or incomplete handled gracefully with warnings logged
