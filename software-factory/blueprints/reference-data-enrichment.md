---
title: "Reference Data Enrichment"
feature_name: null
id: "f4f30af1-522e-426e-bf6a-87fec33eca3e"
---

## Feature Summary

Reference Data Enrichment integrates external datasets -- NPPES (National Plan and Provider Enumeration System) for provider details and HCPCS (Healthcare Common Procedure Coding System) for procedure descriptions -- to enhance the claims data. This feature automates the download, processing, and loading of these reference datasets into DuckDB, creating `providers` and `hcpcs_codes` tables. It enables fraud detection methods to use human-readable provider names, specialties, and procedure descriptions, and identifies critical information like NPI deactivation dates for cross-reference fraud patterns.

## Component Blueprint Composition

This feature runs as Milestone 2 in the fraud detection pipeline, directly following successful data ingestion:

* **@Claims Data Ingestion** — Provides the `claims` table and derived summary tables containing all NPIs and HCPCS codes that require enrichment.

## Feature-Specific Components

```component
name: NppesDataLoader
container: Data Enrichment
responsibilities:
	- Manage NPPES data acquisition: prioritize existing local files, then attempt CMS downloads, fallback to NPPES API
	- Extract NPPES data from ZIP archives
	- Load NPPES CSV into temporary raw table
	- Filter NPPES records to only NPIs present in claims table
	- Parse and standardize provider names and addresses
	- Populate providers table
```

```component
name: SpecialtyMapper
container: Data Enrichment
responsibilities:
	- Map raw NPPES taxonomy codes to human-readable specialties using TAXONOMY_MAP
	- Update specialty column in providers table
	- Assign "Other" for unmapped taxonomy codes
```

```component
name: HcpcsDataLoader
container: Data Enrichment
responsibilities:
	- Initialize hcpcs_codes table
	- Load HCPCS descriptions from external files
	- Fallback to built-in dictionary of top 100 codes
	- Categorize HCPCS codes based on prefix rules
	- Supplement with descriptions for top 500 high-spending codes
```

## System Contracts

### Key Contracts

* **Idempotency**: Re-running will not introduce duplicates or corrupt data.
* **Completeness (NPPES)**: All NPIs in claims are either enriched or flagged as missing.
* **Consistency (HCPCS)**: All high-volume codes have at least a generated description and category.
* **Error Tolerance**: CSV parsing uses ignore_errors=true.

### Integration Contracts

* **Input**: DuckDB `claims` table, `provider_summary`, `hcpcs_summary`
* **External Data Sources**: CMS NPPES files, CMS HCPCS files
* **Output Tables**: `providers`, `hcpcs_codes`
* **Downstream Dependency**: Used by EDA, hypothesis generation, and fraud detection modules

## Architecture Decision Records

### ADR-001: Hybrid NPPES Data Acquisition

**Context:** NPPES dataset is very large (10+ GB).

**Decision:** Multi-tiered acquisition: local files -> local ZIPs -> CMS download -> NPPES API fallback.

**Consequences:**

* Benefits: Robustness against download failures; partial enrichment guaranteed
* Trade-off: API fallback provides less comprehensive data

### ADR-002: Dynamic HCPCS Column Detection

**Context:** External HCPCS files have varying column names.

**Decision:** Implement dynamic column detection searching for common keyword patterns.

**Consequences:**

* Benefits: Flexibility and resilience to format variations
* Trade-off: Potential for incorrect detection with ambiguous names

### ADR-003: Lazy LEIE Integration

**Context:** OIG LEIE is critical but not needed at this stage.

**Decision:** Postpone direct LEIE integration; handle in cross-reference hypotheses.

**Consequences:**

* Benefits: Simplifies enrichment step
* Trade-off: LEIE not denormalized into providers table

## Testing & Validation

### Acceptance Tests

* **NPPES Loading**: Verify file discovery, download, extraction, loading, filtering, name construction
* **NPPES API Fallback**: Verify API requests; verify errors handled
* **Specialty Mapping**: Verify taxonomy-to-specialty mapping applied; verify unmapped codes set to "Other"
* **HCPCS Loading**: Verify external file loading; verify built-in fallback; verify categorization
* **Completeness**: Verify providers and hcpcs_codes tables populated for all relevant entities

### Unit Tests

* **NppesDataLoader**: Test file existence checks; test CSV loading; test name construction
* **SpecialtyMapper**: Test taxonomy mapping; test unmapped code handling
* **HcpcsDataLoader**: Test column detection; test categorization; test fallback

### Integration Tests

* **End-to-End Enrichment**: Download -> load -> map specialties -> load HCPCS -> verify complete
* **NPPES Completeness**: Verify all NPIs from claims present in providers table
* **Idempotency**: Run twice -> verify identical tables
* **Fallback Chains**: Disable downloads -> verify fallbacks succeed

### Test Data Requirements

* **NPPES File**: Sample with Type 1 and Type 2 entities
* **HCPCS Files**: Multiple format samples
* **Claims Data**: Reference NPIs and HCPCS codes

### Success Criteria

* All NPIs successfully loaded to providers table
* Specialty mapping covers >95% of providers
* All HCPCS codes present in claims loaded
* Graceful degradation when external data unavailable
* Idempotency verified
