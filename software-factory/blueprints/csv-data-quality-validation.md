---
title: "CSV Data Quality Validation"
feature_name: null
id: "fa1f1602-0b75-4691-b247-045ceae18357"
---

## Feature Summary

CSV Data Quality Validation performs a pre-ingestion scan of the raw Medicaid claims CSV file to surface structural and data quality issues before processing. The feature streams the 11 GB file row-by-row, validating column counts, NPI formats, HCPCS codes, claim months, and numeric fields, then generates a comprehensive JSON report and CSV export of invalid rows. This critical early-stage gate ensures data integrity and prevents corrupt records from reaching the analytical database.

## Component Blueprint Composition

This feature is the first stage in the data preparation pipeline and runs before @Claims Data Ingestion.

## Feature-Specific Components

```component
name: CSVFileValidator
container: Data Validation
responsibilities:
	- Check CSV file existence at project root; exit with error if missing
	- Verify CSV is not empty (has header row)
	- Report file path and file size in GB
	- Provide early exit with clear messaging before processing begins
```

```component
name: StructuralValidator
container: Data Validation
responsibilities:
	- Validate each row has exactly 7 columns (billing_npi, servicing_npi, hcpcs_code, claim_month, beneficiaries, claims, paid)
	- Flag rows with incorrect column count as invalid with reason "column_count"
	- Count invalid rows by type for breakdown reporting
```

```component
name: NPIValidator
container: Data Validation
responsibilities:
	- Validate billing_npi: must be non-empty, 10 digits, numeric only
	- Validate servicing_npi: optional; if present, must be 10 digits, numeric only
	- Flag invalid NPIs with reasons "billing_npi" or "servicing_npi"
	- Track counts for reporting
```

```component
name: CodeAndMonthValidator
container: Data Validation
responsibilities:
	- Validate hcpcs_code: must be present (non-empty)
	- Validate claim_month: must match YYYY-MM format, month 01-12
	- Flag invalid codes/months with reasons "hcpcs" or "claim_month"
	- Track min/max month for temporal coverage analysis
```

```component
name: NumericFieldValidator
container: Data Validation
responsibilities:
	- Validate beneficiaries: must convert to integer >= 0
	- Validate claims: must convert to integer >= 0
	- Validate paid: must convert to float (accepts negative values for adjustments)
	- Flag type conversion failures with reasons "beneficiaries", "claims", or "paid"
	- Count negative paid rows separately (legitimate adjustments)
	- Flag anomalies: beneficiaries=0 but claims>0 (suspicious pairing)
```

```component
name: InvalidRowWriter
container: Data Validation
responsibilities:
	- Write header to output/qa/invalid_rows.csv
	- For each invalid row, write: row_number, concatenated semicolon-delimited reasons, pipe-delimited raw row data
	- Limit output to configurable max (default 5,000) to prevent memory exhaustion
	- Continue scanning after limit reached (for complete statistics)
```

```component
name: DataQualityReporter
container: Data Validation
responsibilities:
	- Generate data_quality_report.json in output/qa with comprehensive statistics
	- Include: csv_path, total_rows_scanned, valid_rows, invalid_rows, invalid_breakdown by category
	- Include: negative_paid_rows, zero_beneficiaries_positive_claims anomalies
	- Include: min_month, max_month, month_coverage_count, month_counts dict, month_paid dict
	- Include: generated_at timestamp
	- Write JSON with indentation for readability
```

```component
name: ProgressReporter
container: Data Validation
responsibilities:
	- Print progress every 5 million rows with elapsed time
	- Print final completion message with output file locations and total time
	- Allow streaming inspection of long-running scans
```

## System Contracts

### Key Contracts

* **Streaming Processing**: CSV is read once in a single pass with minimal memory overhead. No buffering of entire file or rows. Enables processing of arbitrarily large datasets on resource-constrained machines.
* **Comprehensive Failure Tracking**: Each row can have multiple validation failures; all are captured and reported in semicolon-delimited format. A single row can fail multiple validators (e.g., both invalid billing_npi and invalid claim_month).
* **Non-Fatal Anomalies**: Negative paid amounts are counted but not flagged as invalid (legitimate claim reversals). These rows are included in the valid set. Only zero-beneficiary + positive-claims pairs are flagged as suspicious.
* **Idempotency**: Running validation multiple times on the same CSV produces identical invalid_rows.csv and data_quality_report.json (same content, same row order).

### Integration Contracts

* **Input**: CSV file at `medicaid-provider-spending.csv` in project root. Expected columns: BILLING_PROVIDER_NPI_NUM, SERVICING_PROVIDER_NPI_NUM, HCPCS_CODE, CLAIM_FROM_MONTH, TOTAL_UNIQUE_BENEFICIARIES, TOTAL_CLAIMS, TOTAL_PAID (227M rows, ~11 GB, estimated 2-10 hours to scan).
* **Output Files**:
  * `output/qa/invalid_rows.csv` — up to 5,000 invalid rows with failure reasons
  * `output/qa/data_quality_report.json` — comprehensive validation statistics
* **Downstream Dependency**: @Claims Data Ingestion requires a passing data quality report; if invalid row count is significant, ingestion may be delayed or CSV corrected.
* **Configuration**: `--max-rows` (limits scan for testing); `--max-errors` (limits invalid row output; default 5,000)

## Architecture Decision Records

### ADR-001: Streaming vs. Full-Load Validation

**Context:** The input CSV is 11 GB. Loading the entire file into memory would require 96+ GB of RAM and preclude validation on many systems.

**Decision:** Validate via streaming single-pass. Open CSV, iterate row-by-row, apply validation rules, write results to disk. Use `csv.reader()` (Python standard library) to manage I/O.

**Consequences:**

* Benefits: O(1) memory regardless of file size; validation completes in ~2-10 hours on commodity hardware
* Trade-off: Cannot perform cross-row comparisons (e.g., detect if provider NPI appears before first month or after last month). Deferred to ingestion and downstream stages.
* Row-by-row processing is simple, debuggable, and predictable

### ADR-002: Multiple Validation Failures Per Row

**Context:** A single CSV row can fail multiple validators (e.g., invalid NPI and invalid month). Prior designs captured only the first failure, losing information.

**Decision:** Maintain a `reasons` list for each row. Append each failure reason as validation rules are applied. Concatenate with semicolons in output. Example: "billing_npi;claim_month" if both fail.

**Consequences:**

* Benefits: Complete visibility into all data quality issues per row; easier to prioritize fixes
* Trade-off: Reporting is more complex; downstream tools must parse semicolon-delimited reason strings
* Enables root cause analysis: "84% of invalid rows fail billing_npi validation"

### ADR-003: Legitimate vs. Suspicious Anomalies

**Context:** Some "invalid" conditions are legitimate (negative paid = reversal/adjustment) while others are suspicious (zero beneficiaries but positive claims = potential data entry error).

**Decision:** Separate concerns:

* Negative paid: Count but do NOT flag as invalid. These rows pass validation and are included in valid_rows.
* Zero beneficiaries + positive claims: Count separately in counter but do NOT flag as invalid. Flag in report as suspicious but let downstream rules decide.
* All other type/format failures: Flag as invalid and exclude from valid_rows.

**Consequences:**

* Benefits: Prevents false positives and respects domain knowledge (reversals are normal)
* Trade-off: Report includes both "valid_rows" and "suspicious_rows" as distinct categories; downstream must interpret nuances
* Responsibility pushed to analyst: Data quality report flags anomalies; data engineer/analyst decides whether to investigate or accept

## Testing & Validation

### Acceptance Tests

* **AC-CSVDQ-001.1 through AC-CSVDQ-001.3**: Verify CSV file existence check; confirm missing file error; confirm empty file error; confirm valid file proceeds
* **AC-CSVDQ-002.1 through AC-CSVDQ-002.3**: Verify row column count validation; flag rows with != 7 columns; stop writing invalid rows after max threshold
* **AC-CSVDQ-003.1 through AC-CSVDQ-003.3**: Verify billing_npi validation: empty, non-numeric, wrong length flagged
* **AC-CSVDQ-004.1 through AC-CSVDQ-004.3**: Verify servicing_npi validation: optional when empty; invalid when non-numeric or wrong length
* **AC-CSVDQ-005.1 through AC-CSVDQ-005.2**: Verify hcpcs_code required; any format accepted
* **AC-CSVDQ-006.1 through AC-CSVDQ-006.3**: Verify claim_month YYYY-MM format validation; month range 01-12; track min/max/counts
* **AC-CSVDQ-007.1 through AC-CSVDQ-007.3**: Verify beneficiaries integer conversion; reject negative; count zero-beneficiaries-positive-claims anomalies
* **AC-CSVDQ-008.1 through AC-CSVDQ-008.2**: Verify claims integer conversion; reject negative
* **AC-CSVDQ-009.1 through AC-CSVDQ-009.2**: Verify paid float conversion; accept negative (count separately); no invalid flag for negative
* **AC-CSVDQ-010.1 through AC-CSVDQ-010.3**: Verify invalid_rows.csv written with row_number, semicolon-delimited reasons, pipe-delimited raw data; limit to max rows; skip valid rows
* **AC-CSVDQ-011.1 through AC-CSVDQ-011.3**: Verify data_quality_report.json written to output/qa with all required fields; invalid_breakdown includes all failure types; timestamp generated
* **AC-CSVDQ-012.1 through AC-CSVDQ-012.3**: Verify progress printed every 5M rows; summary printed at completion
* **AC-CSVDQ-013.1 through AC-CSVDQ-013.3**: Verify --max-rows limits scan; --max-errors limits invalid row output

### Unit Tests

* **CSVFileValidator**: Test file existence check; test empty file detection; test missing file error
* **StructuralValidator**: Test 7-column acceptance; test column count != 7 rejection; test counter increments
* **NPIValidator**: Test billing_npi format (empty, non-numeric, length); test servicing_npi optional/format
* **CodeAndMonthValidator**: Test hcpcs required; test month format YYYY-MM; test month range 01-12; test min/max tracking
* **NumericFieldValidator**: Test type conversions; test range validation (>= 0); test negative paid acceptance; test zero-beneficiaries-positive-claims detection
* **InvalidRowWriter**: Test CSV header; test row writing with formatted reasons/data; test max limit enforcement
* **DataQualityReporter**: Test JSON structure; test invalid_breakdown categories; test timestamp generation
* **ProgressReporter**: Test progress intervals; test summary output

### Integration Tests

* **Full CSV Scan**: Load test CSV -> validate all rows -> generate report and invalid_rows.csv -> verify all metrics match expected counts
* **Streaming Efficiency**: Scan 227M-row CSV in single pass; verify memory usage constant throughout; verify processing rate consistent
* **Invalid Row Limit**: Generate > 5,000 invalid rows -> verify output limited to 5,000 -> verify full scan continues -> verify final counts accurate
* **Anomaly Detection**: Verify negative_paid_rows counted correctly; verify zero_beneficiaries-positive_claims flagged; verify month coverage calculated
* **Idempotency**: Run validation twice on same CSV -> verify identical invalid_rows.csv and data_quality_report.json

### Test Data Requirements

* **Full Dataset**: 227M rows with all 7 columns; representatives of all month combinations (2018-01 through 2024-12)
* **Invalid Rows**: Examples of each failure type: missing fields, non-numeric NPIs, invalid month format, negative beneficiaries/claims, non-float paid
* **Edge Cases**: Empty servicing_npi (valid); negative paid amounts (valid); zero claims with positive beneficiaries (anomaly); month values 01, 12, and out-of-range
* **Volume**: Sufficient test data to verify progress reporting at 5M-row intervals

### Success Criteria

* All 13 requirements (REQ-CSVDQ-001-REQ-CSVDQ-013) and 40+ acceptance criteria fully satisfied
* CSV validation completes in < 10 hours for full 227M-row dataset
* data_quality_report.json generated with all required metrics and accurate counts
* invalid_rows.csv generated with correct row format; limited to configured max
* Progress messages printed at configured intervals
* Re-running validation produces identical reports (idempotency verified)
* Report enables data engineers to prioritize corrections and proceed to ingestion
