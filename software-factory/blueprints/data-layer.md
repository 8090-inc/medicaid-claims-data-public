---
title: "Data Layer"
feature_name: null
id: "0186833a-1757-47bd-8a02-0bf089ac0dc2"
---

# Data Layer

## Technology Stack and Frameworks

* **Primary Database**: DuckDB (in-process columnar OLAP)
* **Data Format**: Parquet (compressed, columnar export format)
* **CSV Import**: DuckDB's read_csv_auto for flexible CSV parsing
* **Schema Management**: DuckDB SQL DDL for table creation; no ORM
* **Backup/Export**: Parquet export for external tool integration

## Key Principles

* **Columnar Storage**: DuckDB's columnar architecture enables fast aggregations and statistical queries
* **Pre-Aggregated Tables**: Summary tables (provider_summary, hcpcs_summary, provider_monthly) pre-computed during ingestion, not on-demand
* **Immutable Ingestion**: Claims table loaded once in Milestone 01; subsequent milestones use read-only access
* **Deterministic Aggregations**: All summary tables created via CREATE TABLE AS SELECT with explicit GROUP BY and aggregation functions
* **Index Strategy**: Indexes created post-ingestion to avoid write-time overhead; focus on frequently-queried dimensions (npi, code, month)
* **No Deletions**: Data never deleted; corrections handled via re-ingestion with DROP TABLE IF EXISTS semantics
* **Normalized Reference Data**: providers and hcpcs_codes tables include descriptive fields (name, specialty, description) to support human-readable output

## Standards and Conventions

* **Table Naming**: Lowercase snake_case (provider_summary, billing_servicing_network, provider_monthly)
* **Column Naming**: Lowercase snake_case; prefix with table context if ambiguous (billing_npi vs servicing_npi, not just npi)
* **Data Types**:
  * NPIs: VARCHAR (preserve leading zeros)
  * Dates/Months: VARCHAR YYYY-MM format (no timezone issues)
  * Money: DOUBLE (floating-point; handles calculations and precision)
  * Counts: INTEGER (exact counts of records, claims, months)
* **Null Handling**: NULLIF used for division-by-zero (e.g., avg_paid_per_claim = total_paid / NULLIF(total_claims, 0))
* **Index Naming**: `idx_{table}_{column}` (e.g., idx_claims_billing_npi)
* **Aggregation Filters**: Tables like provider_hcpcs filter to claims > 0 to exclude data entry errors from statistical calculations
* **Temporal Consistency**: All months stored as YYYY-MM strings; comparison via string ordering (e.g., claim_month >= '2018-01')
* **Completeness Semantics**: Missing months = zero billing; never null; handled explicitly via unbalanced panel design

## Testing & Validation

### Acceptance Tests

* **DuckDB Setup**: Verify DuckDB database initialized at project root (medicaid.duckdb); verify connected successfully
* **Table Creation**: Verify all 8 tables created with correct schemas: claims, provider_summary, hcpcs_summary, provider_monthly, provider_hcpcs, billing_servicing_network, providers, hcpcs_codes
* **Index Creation**: Verify indexes created on frequently-queried columns (billing_npi, hcpcs_code, claim_month, etc.)
* **Column Naming**: Verify all columns use lowercase snake_case; verify context-specific naming (billing_npi vs servicing_npi)
* **Data Type Correctness**: Verify NPIs stored as VARCHAR; verify dates as YYYY-MM VARCHAR; verify money as DOUBLE; verify counts as INTEGER
* **Null Handling**: Verify NULLIF used for division-by-zero operations; verify no division errors in aggregations
* **Aggregation Filtering**: Verify claims > 0 filter applied to statistical tables (provider_hcpcs, hcpcs_summary); verify raw claims unfiltered
* **Parquet Export**: Verify claims table exported to claims.parquet at project root with compression
* **Immutability**: Verify claims table loaded once; verify read-only access in subsequent milestones; verify no deletions (only DROP/recreate)

### Unit Tests

* **Table Schema**: Verify each table has correct columns and types
* **Index Presence**: Verify all expected indexes created
* **Aggregation Logic**: Test summary table creation; verify correctness on sample data
* **NULLIF Handling**: Test division-by-zero scenarios; verify NULL results
* **Filtering Logic**: Test claims > 0 filtering; verify data excluded correctly

### Integration Tests

* **Data Integrity**: Load claims -> create summaries -> verify totals consistent (sum of provider_summary = claims aggregate)
* **Read-Only Enforcement**: Attempt modification in read-only context; verify denied
* **Query Performance**: Execute complex queries on summary tables; verify acceptable speed
* **Temporal Consistency**: Verify month string comparisons work correctly (YYYY-MM sorting)
* **Reference Data Normalization**: Verify providers and hcpcs_codes tables properly enriched and indexed

### Test Data Requirements

* **Full Claims Dataset**: 227M records with diverse patterns
* **Summary Verification Data**: Manual calculations for spot-checks
* **Edge Cases**: NULL values, division-by-zero scenarios, filtering edge cases

### Success Criteria

* DuckDB database properly configured and indexed
* All 8 tables created with correct schema
* Summary tables correctly aggregated and filtered
* Column naming consistent and semantic
* Data types correct (NPIs as VARCHAR, money as DOUBLE, etc.)
* Read-only access enforced for analytical queries
* Query performance adequate for interactive analysis
