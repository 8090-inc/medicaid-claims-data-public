---
title: "Implement CSV Data Quality Validation (Milestone 00)"
number: 6
status: "completed"
feature_name: "CSV Data Quality Validation"
phase: 2
---

# Implement CSV Data Quality Validation (Milestone 00)

## Description

### **Summary**

Build the data quality scanning system that validates CMS Medicaid claims CSV structure, detects data quality issues, and ensures data integrity before ingestion. This milestone serves as the first step in the 24-milestone pipeline, preventing downstream processing errors by catching data quality problems early.

### **In Scope**

* Create CSV file existence and accessibility validation
* Implement data structure validation for required fields
* Build data quality checks for missing values, negatives, and anomalies
* Create data quality reporting in JSON format
* Set up early exit logic for critical data quality failures
* Implement file size and row count validation
* Create data quality metrics and thresholds framework

### **Out of Scope**

* Data ingestion to database (handled in separate work order)
* Reference data validation
* Complex statistical analysis

### **Requirements**

## Data and Infrastructure Requirements

**Primary Dataset: CMS Medicaid Provider Utilization and Payments** - The system shall ingest a CSV file (approximately 11 GB) containing all fee-for-service claims, managed care encounters, and CHIP claims. Required fields: BILLING_PROVIDER_NPI_NUM, SERVICING_PROVIDER_NPI_NUM, HCPCS_CODE, CLAIM_FROM_MONTH, TOTAL_UNIQUE_BENEFICIARIES, TOTAL_CLAIMS, TOTAL_PAID.

## Quality and Validation Requirements

**Data Quality Checks** - Milestone 0 shall validate input data structure, detect missing required fields, identify negative or zero paid amounts, and report null values in critical fields.

### **Blueprints**

* CSV Data Quality Validation -- Data quality scanning, structure validation, and quality reporting

### **Testing & Validation**

#### Acceptance Tests

* *AC-CSVDQ-001*: Verify CSV file existence check; confirm missing file error; confirm valid file proceeds
* *AC-CSVDQ-002*: Verify row column count validation; flag rows with != 7 columns
* *AC-CSVDQ-003*: Verify billing_npi validation: empty, non-numeric, wrong length flagged
* *AC-CSVDQ-004*: Verify servicing_npi validation: optional when empty; invalid when non-numeric or wrong length
* *AC-CSVDQ-005*: Verify hcpcs_code required; any format accepted
* *AC-CSVDQ-006*: Verify claim_month YYYY-MM format validation
* *AC-CSVDQ-007*: Verify beneficiaries integer conversion; reject negative
* *AC-CSVDQ-008*: Verify claims integer conversion; reject negative
* *AC-CSVDQ-009*: Verify paid float conversion; accept negative (count separately)
* *AC-CSVDQ-010*: Verify invalid_rows.csv written with row_number, reasons, raw data
* *AC-CSVDQ-011*: Verify data_quality_report.json written to output/qa
* *AC-CSVDQ-012*: Verify progress printed every 5M rows
* *AC-CSVDQ-013*: Verify --max-rows and --max-errors CLI limits

#### Unit Tests

* *CSVFileValidator*: Test file existence check; test empty file detection
* *StructuralValidator*: Test 7-column acceptance; test column count rejection
* *NPIValidator*: Test billing_npi format; test servicing_npi optional/format
* *CodeAndMonthValidator*: Test hcpcs required; test month format YYYY-MM
* *NumericFieldValidator*: Test type conversions; test range validation
* *InvalidRowWriter*: Test CSV header; test row writing with formatted reasons
* *DataQualityReporter*: Test JSON structure; test timestamp generation
* *ProgressReporter*: Test progress intervals; test summary output

#### Integration Tests

* *Full CSV Scan*: Load test CSV -> validate all rows -> generate report
* *Streaming Efficiency*: Scan 227M-row CSV in single pass; verify memory usage constant
* *Invalid Row Limit*: Generate > 5,000 invalid rows -> verify output limited
* *Idempotency*: Run validation twice -> verify identical outputs

#### Success Criteria

* All 13 requirements and 40+ acceptance criteria fully satisfied
* CSV validation completes in < 10 hours for full 227M-row dataset
* Memory usage remains constant during streaming validation
* Progress reporting functions correctly at 5M-row intervals

## Implementation Plan

| File Path | Operation | Description |
|-----------|-----------|-------------|
| `scripts/00_data_quality_validation.py` | create | Create a script to perform data quality validation on the input CSV file. |
| `scripts/validation/structural_validator.py` | create | Create a module for validating the structure of the CSV file. |
| `scripts/validation/field_validator.py` | create | Create a module for performing data quality checks on individual fields. |
| `scripts/validation/reporting.py` | create | Create a module for writing invalid rows and generating JSON reports. |
| `tests/test_data_quality_validation.py` | create | Create a test file for the data quality validation milestone. |
