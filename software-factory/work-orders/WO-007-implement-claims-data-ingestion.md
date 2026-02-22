---
title: "Implement Claims Data Ingestion (Milestone 01)"
number: 7
status: "completed"
feature_name: "Claims Data Ingestion"
phase: 2
---

# Implement Claims Data Ingestion (Milestone 01)

## Description

### **Summary**

Build the core data ingestion system that loads validated CMS claims CSV data into DuckDB and creates five optimized summary tables. This milestone transforms 227 million billing records into a structured analytical database that powers all downstream fraud detection methods.

### **In Scope**

* Implement DuckDB connection with 16-thread and 96GB memory configuration
* Create claims fact table with proper column type casting
* Build five pre-aggregated summary tables (provider_summary, hcpcs_summary, provider_monthly, provider_hcpcs, billing_servicing_network)
* Create optimized indexes on billing_npi, hcpcs_code, and claim_month
* Export claims table to compressed Parquet format
* Generate ingestion report with statistics and data quality metrics
* Implement table verification and execution timing

### **Out of Scope**

* Data quality validation (handled in previous milestone)
* Reference data enrichment (handled in separate work order)
* Fraud detection logic

### **Requirements**

* REQ-CLMING-001: Database Connection and Configuration (16 threads, 96GB memory)
* REQ-CLMING-002: CSV File Validation (existence check before ingestion)
* REQ-CLMING-003: Claims Table Creation (proper column type casting)
* REQ-CLMING-004: Index Creation (billing_npi, hcpcs_code, claim_month)

### **Blueprints**

* Claims Data Ingestion -- Core ingestion logic, summary table creation, and performance optimization

### **Testing & Validation**

#### Acceptance Tests

* Verify DuckDB connection, thread count (16), memory limit (96GB)
* Verify all column type casts applied correctly
* Verify indexes created on all three columns
* Verify all 6 tables created with correct aggregations
* Verify Parquet export with ZSTD compression
* Verify ingest_report.json written to output/qa

#### Unit Tests

* *DuckDBInitializer*: Test connection with thread/memory configs
* *ClaimsIngestor*: Test column casting correctness; test null/zero value handling
* *SummaryTableBuilder*: Test aggregation correctness; test NULLIF division-by-zero handling
* *IndexBuilder*: Test index creation on all three columns
* *ParquetExporter*: Test export path and compression
* *IngestReporter*: Test JSON structure; test timestamp generation

#### Integration Tests

* *End-to-End Pipeline*: Load CSV -> create all 6 tables -> create indexes -> export Parquet -> generate report
* *Idempotency*: Run ingestion twice -> verify second run succeeds without error
* *Summary Consistency*: Verify provider_summary row count matches claims aggregates

#### Success Criteria

* Ingestion completes in < 5 minutes on 16-thread, 96GB machine
* All 6 tables created with expected row counts
* Parquet export succeeds; file readable by external tools
* Re-run on existing database succeeds (idempotency verified)

## Implementation Plan

| File Path | Operation | Description |
|-----------|-----------|-------------|
| `scripts/01_claims_data_ingestion.py` | create | Create the main script for Milestone 01. |
| `scripts/ingestion/claims_ingestor.py` | create | Create a module for loading claims data from CSV into DuckDB. |
| `scripts/ingestion/summary_table_builder.py` | create | Create a module for building five pre-aggregated summary tables. |
| `scripts/ingestion/index_builder.py` | create | Create a module for creating indexes on the claims table. |
| `tests/test_claims_data_ingestion.py` | create | Create a test file for the claims data ingestion milestone. |
