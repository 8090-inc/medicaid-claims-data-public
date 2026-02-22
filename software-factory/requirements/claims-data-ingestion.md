---
title: "Claims Data Ingestion"
type: "feature"
id: "0a352f80-4fda-40ad-b56b-8990ef0229cf"
---

## Overview

After the CSV data quality validation passes, the system must load the validated claims data into a high-performance analytical database and create optimized summary tables that enable efficient fraud detection analysis. This feature ingests approximately 227 million billing records from the CMS CSV file into DuckDB, creates indexes for query performance, builds five pre-aggregated summary tables that power downstream analytical queries, and exports a compressed Parquet file for backup and external analysis.

This ingestion step runs as Milestone 1 and transforms the flat CSV structure into a relational database schema optimized for aggregation queries, temporal analysis, network detection, and peer comparisons. The feature enables all subsequent fraud detection methods by providing fast access to provider-level, code-level, and monthly aggregations.

## Terminology

* **Claims Table**: The primary fact table containing one row per billing_npi + servicing_npi + hcpcs_code + claim_month combination, representing aggregated billing activity for that combination.
* **Provider Summary**: A pre-aggregated table containing one row per provider with lifetime statistics (total codes, months active, beneficiaries, claims, paid amounts).
* **HCPCS Summary**: A pre-aggregated table containing one row per procedure code with cross-provider statistics (number of providers, median rates, percentile distributions).
* **Provider Monthly**: A time-series table containing one row per provider per month, enabling temporal anomaly detection.
* **Provider HCPCS**: A provider-code combination table showing which providers bill which codes and at what volumes and rates.
* **Billing Servicing Network**: An edge table representing relationships between billing providers and servicing providers, used for network fraud detection.

## Requirements

### REQ-CLMING-001: Database Connection and Configuration

**User Story:** As a data engineer, I want the system to establish a properly configured DuckDB connection, so that ingestion can leverage available system resources efficiently.

**Acceptance Criteria:**

* **AC-CLMING-001.1:** When the ingestion process starts, the system shall connect to the DuckDB database file at the project root.
* **AC-CLMING-001.2:** When the connection is established, the system shall configure the thread count to 16 for parallel processing.
* **AC-CLMING-001.3:** When the connection is established, the system shall set the memory limit to 96GB to handle large aggregations.

### REQ-CLMING-002: CSV File Validation

**User Story:** As a data engineer, I want the system to verify CSV file existence before attempting ingestion, so that I receive clear error messages if the file is missing.

**Acceptance Criteria:**

* **AC-CLMING-002.1:** When the CSV file does not exist at the expected path, the system shall exit with an error message.
* **AC-CLMING-002.2:** When the CSV file exists, the system shall proceed to ingest the data.

### REQ-CLMING-003: Claims Table Creation

**User Story:** As a data analyst, I want the system to load all valid CSV rows into a structured claims table, so that I can query billing data efficiently using SQL.

**Acceptance Criteria:**

* **AC-CLMING-003.1:** When creating the claims table, the system shall drop any existing claims table.
* **AC-CLMING-003.2:** When ingesting CSV data, the system shall cast billing_provider_npi_num to VARCHAR as billing_npi.
* **AC-CLMING-003.3:** When ingesting CSV data, the system shall cast servicing_provider_npi_num to VARCHAR as servicing_npi.
* **AC-CLMING-003.4:** When ingesting CSV data, the system shall cast hcpcs_code to VARCHAR.
* **AC-CLMING-003.5:** When ingesting CSV data, the system shall cast claim_from_month to VARCHAR as claim_month.
* **AC-CLMING-003.6:** When ingesting CSV data, the system shall cast total_unique_beneficiaries to INTEGER as beneficiaries.
* **AC-CLMING-003.7:** When ingesting CSV data, the system shall cast total_claims to INTEGER as claims.
* **AC-CLMING-003.8:** When ingesting CSV data, the system shall cast total_paid to DOUBLE as paid.
* **AC-CLMING-003.9:** When ingestion completes, the system shall report the total row count ingested.
* **AC-CLMING-003.10:** When ingestion completes, the system shall report the total paid amount across all claims.
* **AC-CLMING-003.11:** When ingestion completes, the system shall count and report the number of rows with negative paid amounts.
* **AC-CLMING-003.12:** When ingestion completes, the system shall count and report the number of rows with zero paid amounts.

### REQ-CLMING-004: Index Creation

**User Story:** As a database administrator, I want the system to create indexes on frequently queried columns, so that downstream analytical queries execute efficiently.

**Acceptance Criteria:**

* **AC-CLMING-004.1:** When indexes are created, the system shall create an index on claims(billing_npi).
* **AC-CLMING-004.2:** When indexes are created, the system shall create an index on claims(hcpcs_code).
* **AC-CLMING-004.3:** When indexes are created, the system shall create an index on claims(claim_month).
* **AC-CLMING-004.4:** When index creation completes, the system shall confirm all indexes were created successfully.

### REQ-CLMING-005: Provider Summary Table Creation

**User Story:** As a fraud analyst, I want the system to pre-aggregate provider-level statistics, so that I can quickly analyze provider behavior without joining back to the claims table.

**Acceptance Criteria:**

* **AC-CLMING-005.1:** When creating provider_summary, the system shall drop any existing provider_summary table.
* **AC-CLMING-005.2:** When aggregating provider data, the system shall group by billing_npi.
* **AC-CLMING-005.3:** When aggregating provider data, the system shall calculate the count of distinct hcpcs_code as num_codes.
* **AC-CLMING-005.4:** When aggregating provider data, the system shall calculate the count of distinct claim_month as num_months.
* **AC-CLMING-005.5:** When aggregating provider data, the system shall calculate the sum of beneficiaries as total_beneficiaries.
* **AC-CLMING-005.6:** When aggregating provider data, the system shall calculate the sum of claims as total_claims.
* **AC-CLMING-005.7:** When aggregating provider data, the system shall calculate the sum of paid as total_paid.
* **AC-CLMING-005.8:** When aggregating provider data, the system shall calculate avg_paid_per_claim as total_paid divided by total_claims (handling division by zero).
* **AC-CLMING-005.9:** When aggregating provider data, the system shall calculate avg_claims_per_bene as total_claims divided by total_beneficiaries (handling division by zero).
* **AC-CLMING-005.10:** When aggregating provider data, the system shall calculate first_month as the minimum claim_month.
* **AC-CLMING-005.11:** When aggregating provider data, the system shall calculate last_month as the maximum claim_month.
* **AC-CLMING-005.12:** When provider_summary creation completes, the system shall report the count of unique providers.

### REQ-CLMING-006: HCPCS Summary Table Creation

**User Story:** As a fraud analyst, I want the system to pre-aggregate code-level statistics including percentile distributions, so that I can identify outlier billing rates for each procedure code.

**Acceptance Criteria:**

* **AC-CLMING-006.1:** When creating hcpcs_summary, the system shall drop any existing hcpcs_summary table.
* **AC-CLMING-006.2:** When aggregating code data, the system shall group by hcpcs_code.
* **AC-CLMING-006.3:** When aggregating code data, the system shall calculate the count of distinct billing_npi as num_providers.
* **AC-CLMING-006.4:** When aggregating code data, the system shall calculate sum of beneficiaries, claims, and paid.
* **AC-CLMING-006.5:** When aggregating code data, the system shall calculate avg_paid_per_claim.
* **AC-CLMING-006.6:** When aggregating code data, the system shall calculate std_paid_per_claim (standard deviation).
* **AC-CLMING-006.7:** When aggregating code data, the system shall calculate median_paid_per_claim (50th percentile).
* **AC-CLMING-006.8:** When aggregating code data, the system shall calculate p95_paid_per_claim (95th percentile).
* **AC-CLMING-006.9:** When aggregating code data, the system shall filter to rows where claims > 0.
* **AC-CLMING-006.10:** When hcpcs_summary creation completes, the system shall report the count of unique HCPCS codes.

### REQ-CLMING-007: Provider Monthly Table Creation

**User Story:** As a fraud analyst, I want the system to create a provider-month time series table, so that I can detect temporal anomalies and billing spikes.

**Acceptance Criteria:**

* **AC-CLMING-007.1:** When creating provider_monthly, the system shall drop any existing provider_monthly table.
* **AC-CLMING-007.2:** When aggregating monthly data, the system shall group by billing_npi and claim_month.
* **AC-CLMING-007.3:** When aggregating monthly data, the system shall calculate sum of beneficiaries, claims, and paid.
* **AC-CLMING-007.4:** When aggregating monthly data, the system shall calculate the count of distinct hcpcs_code as num_codes.
* **AC-CLMING-007.5:** When provider_monthly creation completes, the system shall report the row count.

### REQ-CLMING-008: Provider HCPCS Table Creation

**User Story:** As a fraud analyst, I want the system to create a provider-code combination table, so that I can analyze code concentration and specialty mismatches.

**Acceptance Criteria:**

* **AC-CLMING-008.1:** When creating provider_hcpcs, the system shall drop any existing provider_hcpcs table.
* **AC-CLMING-008.2:** When aggregating provider-code data, the system shall group by billing_npi and hcpcs_code.
* **AC-CLMING-008.3:** When aggregating provider-code data, the system shall calculate sum of beneficiaries, claims, and paid.
* **AC-CLMING-008.4:** When aggregating provider-code data, the system shall calculate paid_per_claim.
* **AC-CLMING-008.5:** When aggregating provider-code data, the system shall calculate claims_per_bene.
* **AC-CLMING-008.6:** When aggregating provider-code data, the system shall calculate count of distinct claim_month as months_active.
* **AC-CLMING-008.7:** When aggregating provider-code data, the system shall filter to rows where claims > 0.
* **AC-CLMING-008.8:** When provider_hcpcs creation completes, the system shall report the row count.

### REQ-CLMING-009: Billing Servicing Network Table Creation

**User Story:** As a network analyst, I want the system to create an edge table representing billing-to-servicing relationships, so that I can detect circular billing and hub-spoke fraud networks.

**Acceptance Criteria:**

* **AC-CLMING-009.1:** When creating billing_servicing_network, the system shall drop any existing billing_servicing_network table.
* **AC-CLMING-009.2:** When aggregating network data, the system shall group by billing_npi and servicing_npi.
* **AC-CLMING-009.3:** When aggregating network data, the system shall calculate count of distinct hcpcs_code as shared_codes.
* **AC-CLMING-009.4:** When aggregating network data, the system shall calculate count of distinct claim_month as shared_months.
* **AC-CLMING-009.5:** When aggregating network data, the system shall calculate sum of paid as total_paid.
* **AC-CLMING-009.6:** When aggregating network data, the system shall calculate sum of claims as total_claims.
* **AC-CLMING-009.7:** When aggregating network data, the system shall filter to rows where servicing_npi is not null and not empty.
* **AC-CLMING-009.8:** When billing_servicing_network creation completes, the system shall report the edge count.

### REQ-CLMING-010: Parquet Export

**User Story:** As a data scientist, I want the system to export the claims table to Parquet format, so that I can load the data into external analytical tools.

**Acceptance Criteria:**

* **AC-CLMING-010.1:** When exporting to Parquet, the system shall write the claims table to a file named claims.parquet in the project root.
* **AC-CLMING-010.2:** When exporting to Parquet, the system shall use ZSTD compression to minimize file size.
* **AC-CLMING-010.3:** When the export completes, the system shall confirm successful Parquet creation.

### REQ-CLMING-011: Ingestion Report Generation

**User Story:** As a data engineer, I want the system to generate an ingestion summary report in JSON format, so that I can verify ingestion completeness and track data quality metrics.

**Acceptance Criteria:**

* **AC-CLMING-011.1:** When ingestion completes, the system shall write a JSON report to `output/qa/ingest_report.json`.
* **AC-CLMING-011.2:** The report shall include row_count, total_paid, negative_paid_rows, zero_paid_rows, null_claim_month_rows, and generated_at timestamp.
* **AC-CLMING-011.3:** When the report is written, the system shall confirm the output file location.

### REQ-CLMING-012: Table Verification

**User Story:** As a database administrator, I want the system to verify that all expected tables were created, so that I can confirm the ingestion process completed successfully.

**Acceptance Criteria:**

* **AC-CLMING-012.1:** When ingestion completes, the system shall query the list of all tables in the database.
* **AC-CLMING-012.2:** When ingestion completes, the system shall display the list of table names.
* **AC-CLMING-012.3:** When ingestion completes, the system shall report total execution time in seconds and minutes.

## Feature Behavior & Rules

The ingestion process leverages DuckDB's columnar storage and vectorized execution to efficiently process 11+ GB of CSV data. The system uses the `read_csv_auto` function with explicit column type casting to ensure data integrity and consistent type handling.

All summary tables are created using `CREATE TABLE AS SELECT` statements with aggregation functions, ensuring atomic creation and avoiding intermediate steps. The `NULLIF` function is used throughout to handle division by zero scenarios gracefully, returning NULL rather than causing errors.

The provider_summary, hcpcs_summary, and provider_hcpcs tables filter to rows where claims > 0 to exclude zero-activity records from statistical calculations, while the raw claims table retains all records including zeros.

Indexes are created after data loading to avoid index maintenance overhead during the initial bulk insert. DuckDB automatically optimizes index creation using parallel threads.

The billing_servicing_network table provides the foundation for network analysis by capturing the relationships between billing NPIs and servicing NPIs, enabling detection of hub-spoke networks, circular billing, and shared servicing arrangements.
