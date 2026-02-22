---
title: "CSV Data Quality Validation"
type: "feature"
id: "38c2b9ef-3fa2-45a8-8232-4ca64df5910b"
---

## Overview

Before any fraud detection analysis can begin, the system must validate the incoming CMS Medicaid Provider Utilization and Payments dataset to ensure data quality and structural integrity. This feature scans the raw CSV file row-by-row to identify formatting issues, missing required fields, invalid data types, and data anomalies that would compromise downstream analysis. By catching data quality problems early, the system prevents ingestion of corrupted records and provides clear visibility into dataset completeness and coverage.

This validation step runs as Milestone 0 and is critical for establishing trust in subsequent analytical findings. The feature outputs a comprehensive data quality report and a list of invalid rows for manual review and correction.

## Terminology

* **Invalid Row**: A billing record that fails one or more validation rules, such as missing required fields, incorrect data types, or values outside acceptable ranges.
* **Data Quality Report**: A JSON summary document containing validation statistics, month coverage, total volumes, and identified anomalies.
* **Column Count**: The expected number of fields in each CSV row (7 fields: billing NPI, servicing NPI, HCPCS code, claim month, beneficiaries, claims, paid).
* **NPI (National Provider Identifier)**: A 10-digit numeric identifier assigned to healthcare providers in the United States.
* **HCPCS Code**: Healthcare Common Procedure Coding System code that identifies the medical service or procedure billed.
* **Claim Month**: The month in which services were provided, formatted as YYYY-MM.

## Requirements

### REQ-CSVDQ-001: CSV File Existence Check

**User Story:** As a data analyst, I want the system to verify that the input CSV file exists before attempting validation, so that I receive a clear error message if the file is missing.

**Acceptance Criteria:**

* **AC-CSVDQ-001.1:** When the CSV file does not exist at the expected path, the system shall exit with an error message indicating the expected file location.
* **AC-CSVDQ-001.2:** When the CSV file exists, the system shall proceed to open and scan the file.
* **AC-CSVDQ-001.3:** When the CSV file appears to be empty (no header row), the system shall exit with an error message.

### REQ-CSVDQ-002: Structural Validation

**User Story:** As a data quality engineer, I want the system to validate the structure of each CSV row, so that I can identify records with incorrect column counts or malformed data before ingestion.

**Acceptance Criteria:**

* **AC-CSVDQ-002.1:** When a row contains fewer or more than 7 columns, the system shall flag it as invalid with reason "column_count".
* **AC-CSVDQ-002.2:** When a row contains exactly 7 columns, the system shall proceed to field-level validation.
* **AC-CSVDQ-002.3:** When the total invalid row count exceeds the configured maximum (default 5,000), the system shall stop writing additional invalid rows to the output CSV but shall continue scanning.

### REQ-CSVDQ-003: Billing NPI Validation

**User Story:** As a data quality engineer, I want the system to validate billing provider NPIs, so that I can ensure all providers have properly formatted identifiers.

**Acceptance Criteria:**

* **AC-CSVDQ-003.1:** When the billing_npi field is empty, the system shall flag the row as invalid with reason "billing_npi".
* **AC-CSVDQ-003.2:** When the billing_npi field contains non-numeric characters, the system shall flag the row as invalid with reason "billing_npi".
* **AC-CSVDQ-003.3:** When the billing_npi field does not contain exactly 10 digits, the system shall flag the row as invalid with reason "billing_npi".

### REQ-CSVDQ-004: Servicing NPI Validation

**User Story:** As a data quality engineer, I want the system to validate servicing provider NPIs when present, so that I can identify malformed servicing NPIs.

**Acceptance Criteria:**

* **AC-CSVDQ-004.1:** When the servicing_npi field is empty, the system shall not flag an error (servicing NPI is optional).
* **AC-CSVDQ-004.2:** When the servicing_npi field is present and contains non-numeric characters, the system shall flag the row as invalid with reason "servicing_npi".
* **AC-CSVDQ-004.3:** When the servicing_npi field is present and does not contain exactly 10 digits, the system shall flag the row as invalid with reason "servicing_npi".

### REQ-CSVDQ-005: HCPCS Code Validation

**User Story:** As a data quality engineer, I want the system to validate that every row contains an HCPCS code, so that I can ensure all billing records have an associated procedure code.

**Acceptance Criteria:**

* **AC-CSVDQ-005.1:** When the hcpcs_code field is empty, the system shall flag the row as invalid with reason "hcpcs".
* **AC-CSVDQ-005.2:** When the hcpcs_code field is present, the system shall accept it (format validation is not performed at this stage).

### REQ-CSVDQ-006: Claim Month Validation

**User Story:** As a data quality engineer, I want the system to validate claim month formatting and values, so that I can ensure temporal data is consistent and analyzable.

**Acceptance Criteria:**

* **AC-CSVDQ-006.1:** When the claim_month field does not match the pattern YYYY-MM, the system shall flag the row as invalid with reason "claim_month".
* **AC-CSVDQ-006.2:** When the month value is less than 01 or greater than 12, the system shall flag the row as invalid with reason "claim_month".
* **AC-CSVDQ-006.3:** When the claim_month is valid, the system shall track it for coverage analysis (min month, max month, month counts).

### REQ-CSVDQ-007: Beneficiary Count Validation

**User Story:** As a data quality engineer, I want the system to validate beneficiary counts, so that I can identify records with invalid or negative patient counts.

**Acceptance Criteria:**

* **AC-CSVDQ-007.1:** When the beneficiaries field cannot be converted to an integer, the system shall flag the row as invalid with reason "beneficiaries".
* **AC-CSVDQ-007.2:** When the beneficiaries field is negative, the system shall flag the row as invalid with reason "beneficiaries".
* **AC-CSVDQ-007.3:** When the beneficiaries field is zero but the claims field is positive, the system shall increment the "zero_beneficiaries_positive_claims" counter.

### REQ-CSVDQ-008: Claims Count Validation

**User Story:** As a data quality engineer, I want the system to validate claims counts, so that I can identify records with invalid or negative claim counts.

**Acceptance Criteria:**

* **AC-CSVDQ-008.1:** When the claims field cannot be converted to an integer, the system shall flag the row as invalid with reason "claims".
* **AC-CSVDQ-008.2:** When the claims field is negative, the system shall flag the row as invalid with reason "claims".

### REQ-CSVDQ-009: Paid Amount Validation

**User Story:** As a data quality engineer, I want the system to validate paid amounts, so that I can identify records with invalid or suspicious payment values.

**Acceptance Criteria:**

* **AC-CSVDQ-009.1:** When the paid field cannot be converted to a float, the system shall flag the row as invalid with reason "paid".
* **AC-CSVDQ-009.2:** When the paid field is negative, the system shall increment the "negative_paid" counter (but shall not flag the row as invalid, as negative adjustments are legitimate).

### REQ-CSVDQ-010: Invalid Row Recording

**User Story:** As a data quality engineer, I want the system to write invalid rows to a separate CSV file, so that I can manually review and correct data quality issues.

**Acceptance Criteria:**

* **AC-CSVDQ-010.1:** When a row is flagged as invalid, the system shall write a record to `output/qa/invalid_rows.csv` containing the row number, all validation failure reasons (semicolon-delimited), and the raw row data (pipe-delimited).
* **AC-CSVDQ-010.2:** When the invalid row count exceeds the configured maximum (default 5,000), the system shall stop writing additional rows to the invalid rows CSV.
* **AC-CSVDQ-010.3:** When a row is valid, the system shall not write it to the invalid rows CSV.

### REQ-CSVDQ-011: Data Quality Report Generation

**User Story:** As a data quality engineer, I want the system to generate a comprehensive data quality report in JSON format, so that I can review validation statistics and dataset coverage.

**Acceptance Criteria:**

* **AC-CSVDQ-011.1:** When the scan completes, the system shall write a JSON report to `output/qa/data_quality_report.json`.
* **AC-CSVDQ-011.2:** The report shall include: csv_path, total_rows_scanned, valid_rows, invalid_rows, invalid_breakdown (by reason), negative_paid_rows, zero_beneficiaries_positive_claims, min_month, max_month, month_coverage_count, month_counts (dictionary), month_paid (dictionary), and generated_at timestamp.
* **AC-CSVDQ-011.3:** The invalid_breakdown field shall contain counts for each validation failure type: invalid_column_count, invalid_npi, invalid_servicing_npi, invalid_hcpcs, invalid_month, invalid_beneficiaries, invalid_claims, invalid_paid.

### REQ-CSVDQ-012: Progress Reporting

**User Story:** As a data analyst, I want the system to display progress updates during scanning, so that I can monitor execution status for large datasets.

**Acceptance Criteria:**

* **AC-CSVDQ-012.1:** When the system has scanned 5 million rows, it shall print a progress message showing rows scanned and elapsed time.
* **AC-CSVDQ-012.2:** When the system has scanned each subsequent 5 million rows, it shall print an updated progress message.
* **AC-CSVDQ-012.3:** When the scan completes, the system shall print a summary message showing the output file location and total elapsed time.

### REQ-CSVDQ-013: Configurable Scan Limits

**User Story:** As a developer, I want to limit the number of rows scanned during testing, so that I can validate the feature quickly without processing the entire dataset.

**Acceptance Criteria:**

* **AC-CSVDQ-013.1:** When the `--max-rows` argument is provided, the system shall stop scanning after processing that many rows.
* **AC-CSVDQ-013.2:** When the `--max-rows` argument is not provided, the system shall scan all rows in the CSV.
* **AC-CSVDQ-013.3:** When the `--max-errors` argument is provided, the system shall limit invalid row output to that number (default: 5,000).

## Feature Behavior & Rules

The validation logic processes the CSV in a single streaming pass, maintaining minimal memory overhead regardless of dataset size. The system distinguishes between structural errors (which prevent ingestion) and data anomalies (which are flagged for review but may be legitimate).

Negative paid amounts are counted but not flagged as invalid, as they represent legitimate claim adjustments or reversals. However, beneficiary counts of zero with positive claim counts are flagged as suspicious.

Month coverage analysis tracks the temporal span of the dataset, enabling downstream features to verify expected data completeness (e.g., 84 months for January 2018 through December 2024).

The system uses regular expressions for month format validation and explicit type conversion for numeric fields to provide clear error categorization. Multiple validation failures on a single row are recorded with all applicable failure reasons concatenated.
