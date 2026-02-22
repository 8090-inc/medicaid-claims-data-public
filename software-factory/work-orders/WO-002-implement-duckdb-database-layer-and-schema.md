---
title: "Implement DuckDB Database Layer and Schema"
number: 2
status: "completed"
feature_name: null
phase: 1
---

# Implement DuckDB Database Layer and Schema

## Description

### **Summary**

Set up the DuckDB analytical database foundation with connection management, schema definitions, and index strategy. This establishes the core data storage layer that supports all 24 pipeline milestones with optimized columnar storage and aggregation capabilities.

### **In Scope**

* Implement DuckDB connection manager with 16-thread configuration
* Create database schema for core tables (claims, provider_summary, hcpcs_summary, etc.)
* Establish index strategy for billing_npi, hcpcs_code, and claim_month
* Implement database initialization and health check utilities
* Set up data type casting and null handling conventions
* Create backup and export utilities framework

### **Out of Scope**

* Actual data ingestion (handled in separate work order)
* Specific table population logic
* Business logic for fraud detection queries

### **Requirements**

## Technical Requirements

**DuckDB Analytical Database** - The system shall use DuckDB as the analytical database engine, creating a database file (approximately 30 GB) with optimized indexes on billing_npi, hcpcs_code, and claim_month.

**Memory** - The system shall run on hardware with at least 16 GB of RAM to support in-memory aggregations and machine learning model training.

**Storage** - The system requires at least 100 GB of available storage for input data (11 GB CSV), DuckDB database (30 GB), NPPES registry (10 GB), output findings (8 GB), and output reports/charts/queues (5 GB).

**Scalability** - DuckDB's columnar storage and vectorized execution enable processing of billions of claim transactions without requiring distributed computing infrastructure.

### **Blueprints**

* Data Layer -- DuckDB configuration, schema management, and indexing strategy
* Backend -- Python standards and database interaction patterns

### **Testing & Validation**

#### Acceptance Tests

* *DuckDB Setup*: Verify DuckDB database initialized at project root (medicaid.duckdb); verify connected successfully
* *Table Creation*: Verify all 8 tables created with correct schemas
* *Index Creation*: Verify indexes created on frequently-queried columns
* *Column Naming*: Verify all columns use lowercase snake_case
* *Data Type Correctness*: Verify NPIs stored as VARCHAR; verify dates as YYYY-MM VARCHAR; verify money as DOUBLE; verify counts as INTEGER
* *Null Handling*: Verify NULLIF used for division-by-zero operations
* *Aggregation Filtering*: Verify claims > 0 filter applied to statistical tables
* *Parquet Export*: Verify claims table exported to claims.parquet
* *Immutability*: Verify claims table loaded once; verify read-only access in subsequent milestones

#### Unit Tests

* *Connection Management*: Test DuckDB connection setup; test 16-thread configuration
* *Table Schema*: Verify each table has correct columns and types
* *Index Presence*: Verify all expected indexes created
* *Aggregation Logic*: Test summary table creation; verify correctness on sample data
* *NULLIF Handling*: Test division-by-zero scenarios; verify NULL results
* *Filtering Logic*: Test claims > 0 filtering; verify data excluded correctly

#### Integration Tests

* *Data Integrity*: Load claims -> create summaries -> verify totals consistent
* *Read-Only Enforcement*: Attempt modification in read-only context; verify denied
* *Query Performance*: Execute complex queries on summary tables; verify acceptable speed
* *Temporal Consistency*: Verify month string comparisons work correctly
* *Reference Data Normalization*: Verify providers and hcpcs_codes tables properly enriched and indexed

#### Success Criteria

* DuckDB database properly configured and indexed
* All 8 tables created with correct schema
* Summary tables correctly aggregated and filtered
* Column naming consistent and semantic
* Data types correct (NPIs as VARCHAR, money as DOUBLE, etc.)
* Read-only access enforced for analytical queries

## Implementation Plan

| File Path | Operation | Description |
|-----------|-----------|-------------|
| `scripts/utils/db_utils.py` | modify | Update the get_connection function to set the database path dynamically based on the PROJECT_ROOT. |
| `scripts/utils/database_setup.py` | create | Create a new script responsible for setting up the database schema. |
| `scripts/01_setup_and_ingest.py` | modify | Update the main data ingestion script to call the new database setup script before ingesting the data. |
| `tests/test_database_setup.py` | create | Create a new test file for the database setup script. |
