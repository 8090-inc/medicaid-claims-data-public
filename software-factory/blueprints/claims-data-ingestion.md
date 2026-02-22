---
title: "Claims Data Ingestion"
feature_name: null
id: "4e3926f5-f237-4a52-a1f9-455478bbfd9d"
---

## Feature Summary

Claims Data Ingestion consumes validated Medicaid claims CSV data and loads it into DuckDB, creating an indexed `claims` fact table with 227 million billing records and five pre-aggregated summary tables (`provider_summary`, `hcpcs_summary`, `provider_monthly`, `provider_hcpcs`, `billing_servicing_network`) that power all downstream fraud detection methods. The feature enables efficient temporal analysis, peer comparisons, network detection, and code-level anomaly detection through strategic aggregation and indexing.

## Component Blueprint Composition

This feature depends on successful completion of earlier pipeline stages:

* **@CSV Data Quality Validation** — Produces validated CSV data; this feature consumes and ingests that validated data into DuckDB.

## Feature-Specific Components

```component
name: DuckDBInitializer
container: Analytics Backend
responsibilities:
	- Establish DuckDB connection to medicaid.duckdb at project root
	- Configure 16 parallel threads and 96GB memory limit
	- Verify CSV file existence before proceeding
```

```component
name: ClaimsIngestor
container: Analytics Backend
responsibilities:
	- Read CSV file via DuckDB `read_csv_auto` with explicit column casting
	- Create indexed `claims` fact table with 227M billing records
	- Cast columns: billing_npi (VARCHAR), servicing_npi (VARCHAR), hcpcs_code (VARCHAR), claim_month (VARCHAR), beneficiaries (INTEGER), claims (INTEGER), paid (DOUBLE)
	- Report ingestion statistics: row count, total paid, negative/zero paid rows, null months
```

```component
name: SummaryTableBuilder
container: Analytics Backend
responsibilities:
	- Build `provider_summary` with lifetime provider statistics: total codes, months active, beneficiaries, claims, paid, avg paid-per-claim, avg claims-per-bene, first/last month
	- Build `hcpcs_summary` with code-level statistics: provider count, totals, average, std dev, median, 95th percentile paid-per-claim
	- Build `provider_monthly` with provider-month time series: monthly aggregations for temporal anomaly detection
	- Build `provider_hcpcs` with provider-code combinations: showing which providers bill which codes at what rates
	- Build `billing_servicing_network` with billing-to-servicing edges for network fraud detection
	- All aggregations handle division-by-zero gracefully; filter to claims > 0 for statistical tables
```

```component
name: IndexBuilder
container: Analytics Backend
responsibilities:
	- Create indexes on claims(billing_npi), claims(hcpcs_code), claims(claim_month) to enable efficient lookups
	- Execute indexes in parallel; confirm successful creation
```

```component
name: ParquetExporter
container: Analytics Backend
responsibilities:
	- Export `claims` table to claims.parquet at project root
	- Use ZSTD compression for file size optimization
	- Confirm successful export
```

```component
name: IngestReporter
container: Analytics Backend
responsibilities:
	- Generate ingest_report.json in output/qa with: row count, total paid, negative paid rows, zero paid rows, null month rows, timestamp
	- Display list of all created tables
	- Report total execution time
```

## System Contracts

### Key Contracts

* **Idempotency**: All summary tables are created via `CREATE TABLE IF NOT EXISTS...AS SELECT` or `DROP TABLE IF EXISTS` + `CREATE TABLE`, ensuring idempotent execution. Re-running on existing database succeeds without error.
* **Consistency**: The `claims` table is the source of truth; all summaries are derived atomically from it. No intermediate rows exposed during aggregation.
* **Data Integrity**: All rows ingested from CSV retain exact values (no rounding, truncation, or silent coercion). Division by zero handled explicitly with `NULLIF`.
* **Completeness**: Ingestion reports row counts, totals, and data quality metrics; mismatch between CSV rows and ingested rows is flagged as error.

### Integration Contracts

* **Input**: CSV file at `medicaid-provider-spending.csv` with columns: BILLING_PROVIDER_NPI_NUM, SERVICING_PROVIDER_NPI_NUM, HCPCS_CODE, CLAIM_FROM_MONTH, TOTAL_UNIQUE_BENEFICIARIES, TOTAL_CLAIMS, TOTAL_PAID (assumed valid by prior @CSV Data Quality Validation stage).
* **Output Tables**:
  * `claims` — 227M rows; consumed by all downstream hypothesis and analysis modules
  * `provider_summary` — ~617k rows; consumed by peer comparison, concentration, financial impact modules
  * `hcpcs_summary` — ~10.8k rows; consumed by outlier code detection, Benford's analysis
  * `provider_monthly` — ~40M rows; consumed by temporal analysis, structural break detection
  * `provider_hcpcs` — ~48M rows; consumed by code specialty mismatch, concentration analysis
  * `billing_servicing_network` — ~1M rows; consumed by network circularity detection
* **Output Artifacts**:
  * `claims.parquet` — Parquet export for external analysis tools
  * `output/qa/ingest_report.json` — JSON summary of ingestion success/failure

## Architecture Decision Records

### ADR-001: DuckDB Over Traditional RDBMS

**Context:** Ingestion must handle 11 GB of CSV data, produce multiple aggregates, and support complex analytical queries (percentiles, string aggregations, window functions) with minimal latency.

**Decision:** Use DuckDB columnar in-process OLAP database rather than traditional row-oriented RDBMS or Spark. DuckDB provides:

* Vectorized execution and compression for 10-100x faster analytics than row-oriented DBs
* Native support for statistical functions (PERCENTILE_CONT, STDDEV) used in peer comparisons
* Single-machine simplicity: no cluster overhead, dependency management, or distributed query complexity
* Memory-mapped Parquet support for external tool integration

**Consequences:**

* Fast ingestion and aggregation (11GB ingests in ~5 min on 16-thread machine)
* Single-machine constraint: entire workflow must run on a machine with 96GB+ RAM. Scaling beyond this requires distributed redesign.
* No distributed transaction support, but unnecessary here since each milestone is idempotent.

### ADR-002: Pre-Aggregated Summary Tables vs. On-Demand Aggregation

**Context:** Downstream fraud detection modules need fast, interactive queries on provider-level and code-level statistics. Computing aggregates at query time would introduce latency and redundant computation.

**Decision:** Create five pre-aggregated summary tables (`provider_summary`, `hcpcs_summary`, `provider_monthly`, `provider_hcpcs`, `billing_servicing_network`) and store them persistently in DuckDB. All downstream modules query these pre-computed tables rather than re-aggregating from `claims`.

**Consequences:**

* Benefits: 100-1000x faster downstream queries; enables interactive exploration
* Trade-off: Ingestion time increases slightly (~20% of total pipeline) due to aggregate computation. Storage cost negligible (DuckDB compression handles efficiently).
* Consistency: Aggregates are deterministic functions of the claims table, so if claims changes, all summaries must be rebuilt -- which the pipeline ensures by dropping and recreating them each run.

### ADR-003: Filtering to Claims > 0 for Statistical Tables

**Context:** Some rows in the claims table have beneficiaries > 0 or paid > 0 but claims = 0 (billing errors). Including these in statistical aggregations (median, percentile, standard deviation) skews results and inflates outlier detection false positives.

**Decision:** All statistical tables (`hcpcs_summary`, `provider_hcpcs`) include a `WHERE claims > 0` filter in their CREATE TABLE AS SELECT statements. The raw `claims` table retains all rows for auditability.

**Consequences:**

* Benefits: Outlier detection methods (Benford's, percentile-based) avoid false positives from data entry errors
* Trade-off: Statistical tables exclude ~0.01% of billing records; this is acceptable and documented in ingest report
* Auditability: Raw `claims` table is unfiltered, so data quality issues can be investigated without losing the original records

## Testing & Validation

### Acceptance Tests

* **AC-CLMING-001.1**: Verify DuckDB connection to medicaid.duckdb at project root succeeds
* **AC-CLMING-001.2**: Verify thread count configured to 16 for parallel processing
* **AC-CLMING-001.3**: Verify memory limit set to 96GB; log configuration on startup
* **AC-CLMING-002.1**: Verify system exits with error message when CSV file missing at expected path
* **AC-CLMING-002.2**: Verify system proceeds to ingestion when CSV file exists at expected location
* **AC-CLMING-003.1**: Verify existing claims table dropped before creation (idempotency)
* **AC-CLMING-003.2 through AC-CLMING-003.8**: Verify all column type casts (billing_npi, servicing_npi, hcpcs_code, claim_month, beneficiaries, claims, paid) applied correctly; spot-check converted values match source CSV
* **AC-CLMING-003.9 through AC-CLMING-003.12**: Verify ingest_report.json includes row_count, total_paid, negative_paid_rows, zero_paid_rows, null_month_rows
* **AC-CLMING-004.1 through AC-CLMING-004.3**: Verify indexes created on claims(billing_npi), claims(hcpcs_code), claims(claim_month)
* **AC-CLMING-004.4**: Verify index creation confirmation logged
* **AC-CLMING-005.1 through AC-CLMING-005.11**: Verify provider_summary aggregations: num_codes, num_months, total_beneficiaries, total_claims, total_paid, avg_paid_per_claim (with NULLIF division handling), avg_claims_per_bene, first_month, last_month
* **AC-CLMING-005.12**: Verify provider_summary row count reported (expect ~617k rows)
* **AC-CLMING-006.1 through AC-CLMING-006.10**: Verify hcpcs_summary aggregations with WHERE claims > 0 filter; confirm ~10.8k codes reported
* **AC-CLMING-007.1 through AC-CLMING-007.5**: Verify provider_monthly time-series created; validate temporal ordering by claim_month
* **AC-CLMING-008.1 through AC-CLMING-008.8**: Verify provider_hcpcs aggregations with WHERE claims > 0 filter; expect ~48M rows
* **AC-CLMING-009.1 through AC-CLMING-009.8**: Verify billing_servicing_network edge table created with ~1M edges; confirm WHERE servicing_npi IS NOT NULL filter
* **AC-CLMING-010.1 through AC-CLMING-010.3**: Verify claims.parquet exported with ZSTD compression; validate file integrity
* **AC-CLMING-011.1 through AC-CLMING-011.3**: Verify ingest_report.json written to output/qa with all required fields and timestamp
* **AC-CLMING-012.1 through AC-CLMING-012.3**: Verify all 6 tables created; report execution time in seconds and minutes

### Unit Tests

* **DuckDBInitializer**: Test connection with thread/memory configs; test missing file error handling
* **ClaimsIngestor**: Test column casting correctness; test null/zero value handling; test row count and paid calculations
* **SummaryTableBuilder**: Test aggregation correctness; test NULLIF division-by-zero handling; test WHERE claims > 0 filtering
* **IndexBuilder**: Test index creation on all three columns; test concurrent creation
* **ParquetExporter**: Test export path and compression; test file integrity
* **IngestReporter**: Test JSON structure; test timestamp generation; test table list display

### Integration Tests

* **End-to-End Pipeline**: Load CSV -> create all 6 tables -> create indexes -> export Parquet -> generate report -> verify all outputs
* **Idempotency**: Run ingestion twice -> verify second run succeeds without error -> verify final row counts unchanged
* **Summary Consistency**: Verify provider_summary row count = COUNT(DISTINCT billing_npi) from claims; verify sum of totals match claims aggregates
* **Time-Series Alignment**: Verify provider_monthly contains only valid claim_month values from claims
* **Network Coverage**: Verify all unique (billing_npi, servicing_npi) pairs with servicing_npi IS NOT NULL represented in billing_servicing_network

### Test Data Requirements

* **Full Dataset**: 227M rows from validated medicaid-provider-spending.csv with all columns
* **Edge Cases**: Rows with claims=0, beneficiaries=0, paid=0, null servicing_npi, null claim_month, negative paid amounts
* **Variety**: Providers with 1-month, full 84-month, and sparse activity; codes with high concentration and providers with 100+ codes

### Success Criteria

* All 12 requirements (REQ-CLMING-001-REQ-CLMING-012) and 40+ acceptance criteria fully satisfied
* Ingestion completes in < 5 minutes on 16-thread, 96GB machine
* All 6 tables created with expected row counts (+/-1% variance)
* ingest_report.json generated with correct values
* Parquet export succeeds; file readable by external tools
* Re-run on existing database succeeds (idempotency verified)
* Downstream fraud detection modules successfully consume output tables
