---
title: "Hypothesis Feasibility Matrix"
feature_name: null
id: "8e949377-5790-4418-bb45-8ab6d8a5f4ef"
---

## Feature Summary

Hypothesis Feasibility Matrix evaluates each of the 1,000+ generated hypotheses for testability against current data availability and characteristics. The feature assesses data coverage (required columns, row counts, peer group sizes), produces a feasibility classification (TESTABLE, NOT_TESTABLE, NEEDS_ENRICHMENT), identifies data enrichment priorities, and prevents pipeline failures by skipping non-viable hypotheses during execution.

## Component Blueprint Composition

This feature depends on hypothesis generation and data ingestion:

* **@Hypothesis Generation** — Provides hypothesis definitions to be feasibility-assessed.
* **@Claims Data Ingestion** — Provides database schema and record counts for coverage assessment.

## Feature-Specific Components

```component
name: DataCoverageAssessor
container: Hypothesis Engine
responsibilities:
	- For each hypothesis, verify all required data columns exist in database schema
	- Calculate number of providers or records available for testing
	- Verify temporal coverage (sufficient months for temporal hypotheses)
	- Verify peer group size meets minimums (>20 for peer comparisons, >100 for statistical tests)
	- Mark hypothesis TESTABLE when coverage exceeds thresholds
	- Mark NOT_TESTABLE when required data is completely missing
	- Mark NEEDS_ENRICHMENT when structurally valid but requires external reference data
```

```component
name: FeasibilityClassifier
container: Hypothesis Engine
responsibilities:
	- Classify each hypothesis: TESTABLE, NOT_TESTABLE, or NEEDS_ENRICHMENT
	- Assign reason codes: missing_column, insufficient_peers, temporal_coverage_gap, missing_nppes, missing_leie, etc.
	- Calculate testability percentage by category (1-10)
	- Identify which reference data sources would unlock most non-testable hypotheses
```

```component
name: FeasibilityMatrixGenerator
container: Hypothesis Engine
responsibilities:
	- Generate hypothesis_feasibility_matrix.csv with columns: hypothesis_id, category, subcategory, method, status, reason, available_records, min_required_records, peer_group_size
	- Generate feasibility_summary.md report showing testable counts by category, non-testability reasons, enrichment priorities
	- Save both to output/analysis/ directory
```

```component
name: PipelineIntegrator
container: Hypothesis Engine
responsibilities:
	- Load feasibility matrix before hypothesis execution begins
	- Skip execution of any hypothesis marked NOT_TESTABLE or NEEDS_ENRICHMENT
	- Log skipped hypotheses with reason codes for audit
	- Report testable, skipped, and enrichment-required hypothesis counts at pipeline start
```

## System Contracts

### Key Contracts

* **Feasibility Stability**: Feasibility status is stable within pipeline run but regenerated after data enrichment or schema changes.
* **Conservative Evaluation**: Hypotheses are marked testable only when all requirements are confidently met.
* **Auditability**: All feasibility decisions are logged with reason codes.

### Integration Contracts

* **Input**: Hypothesis definitions from @Hypothesis Generation; database schema and record counts from @Claims Data Ingestion
* **Output**:
  * `output/analysis/hypothesis_feasibility_matrix.csv`
  * `output/analysis/feasibility_summary.md`
* **Downstream Dependency**: @Fraud Detection Execution loads feasibility matrix and skips non-testable hypotheses

## Architecture Decision Records

### ADR-001: Feasibility Assessment as Data-Driven Gating

**Context:** Executing non-testable hypotheses wastes time and produces spurious findings.

**Decision:** Automatically assess feasibility for all hypotheses; gate execution on TESTABLE status.

**Consequences:**

* Benefits: Prevents wasted computation; transparent decision-making
* Trade-off: Requires schema and data-level introspection overhead (negligible)
* Governance: Feasibility matrix becomes documentation of tested vs untested hypotheses

### ADR-002: Three-Tier Feasibility Classification

**Context:** Some hypotheses fail outright; others require specific enrichment; others are marginal.

**Decision:** Use three tiers: TESTABLE, NOT_TESTABLE, NEEDS_ENRICHMENT.

**Consequences:**

* Benefits: Nuanced decision-making; NEEDS_ENRICHMENT guides data collection priorities
* Trade-off: Requires threshold definitions for boundary cases
* Transparency: Reason codes explain classification rationale

### ADR-003: Regeneration on Data Changes

**Context:** Adding reference data changes feasibility. Stale matrices are misleading.

**Decision:** Feasibility matrix is generated fresh each pipeline run.

**Consequences:**

* Benefits: Always current; reflects impact of recent data enrichment
* Trade-off: Small overhead regenerating matrix each run (negligible)

## Testing & Validation

### Acceptance Tests

* **Data Coverage Assessment**: Verify required columns detected; verify record counts calculated; verify temporal coverage assessed; verify peer group sizes evaluated
* **Feasibility Classification**: Verify TESTABLE/NOT_TESTABLE/NEEDS_ENRICHMENT assigned correctly
* **Reason Codes**: Verify detailed reason codes assigned
* **Matrix Generation**: Verify CSV created with all required columns
* **Summary Report**: Verify feasibility_summary.md created
* **Pipeline Integration**: Verify non-testable hypotheses skipped during execution

### Unit Tests

* **DataCoverageAssessor**: Test column existence verification; test record count calculation; test temporal coverage; test peer group size
* **FeasibilityClassifier**: Test status assignment; test reason code generation
* **FeasibilityMatrixGenerator**: Test CSV generation; test summary report
* **PipelineIntegrator**: Test hypothesis execution gating; test NOT_TESTABLE skipping

### Integration Tests

* **End-to-End Assessment**: Load hypotheses and database schema -> assess all -> classify -> generate matrix
* **Data Enrichment Impact**: Run before and after enrichment -> verify improvement in TESTABLE count
* **Hypothesis Execution Gating**: Create matrix -> execute pipeline -> verify non-testable skipped

### Test Data Requirements

* **Hypotheses**: Mix of testable, not-testable, and needs-enrichment
* **Database Schema**: Claims table with columns for all hypothesis types
* **Record Counts**: Providers, HCPCS codes, temporal records

### Success Criteria

* Feasibility matrix accurately classifies all hypotheses
* Reason codes explain all non-testable classifications
* Summary report identifies enrichment priorities
* Pipeline execution respects feasibility matrix
* Re-running produces identical matrix (idempotency)
