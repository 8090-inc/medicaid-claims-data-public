---
title: "Reference Data Enrichment"
type: "feature"
id: "4ef68222-b6b6-4091-bc74-a61ddecc6b09"
---

## Overview

After claims data is ingested, the system must enrich billing records with provider identity information, procedure code descriptions, and exclusion list cross-references that enable fraud detection methods to identify provider names, specialties, deactivated status, and excluded individuals. This feature downloads the NPPES National Provider Registry (10+ GB), loads HCPCS procedure code descriptions, and retrieves the OIG List of Excluded Individuals/Entities (LEIE), creating enrichment tables that are joined to claims data throughout the analytical pipeline.

This enrichment step runs as Milestone 2 and transforms anonymous NPI numbers into provider profiles with names, specialties, addresses, and deactivation dates, enabling human-readable reporting and cross-reference fraud detection methods.

## Terminology

* **NPPES (National Plan and Provider Enumeration System)**: The CMS registry containing all healthcare provider NPIs with names, addresses, specialties, entity types, and deactivation dates.
* **Taxonomy Code**: A 10-character code from the Healthcare Provider Taxonomy that classifies provider specialties (e.g., 207R00000X = Internal Medicine).
* **LEIE (List of Excluded Individuals/Entities)**: The OIG database of providers barred from receiving federal healthcare payments due to fraud, abuse, or license revocations.
* **Deactivation Date**: The date when an NPI was deactivated in NPPES, after which the provider should not bill Medicaid.
* **Entity Type**: A classification indicating whether an NPI represents an individual (Type 1) or an organization (Type 2).
* **HCPCS (Healthcare Common Procedure Coding System)**: The coding system used to identify medical services, procedures, and supplies billed to Medicare/Medicaid.

## Requirements

### REQ-REFENR-001: NPPES Download and Selection

**User Story:** As a data engineer, I want the system to download the NPPES provider registry automatically, so that I can enrich provider data without manual file handling.

**Acceptance Criteria:**

* **AC-REFENR-001.1:** When NPPES download begins, the system shall check for existing NPPES CSV files in the `reference_data/nppes/` directory.
* **AC-REFENR-001.2:** When an existing NPPES CSV file is found (matching pattern `npidata_pfile_*.csv`), the system shall use the existing file rather than re-downloading.
* **AC-REFENR-001.3:** When no existing NPPES CSV is found, the system shall check for local ZIP files matching pattern `NPPES_Data_Dissemination_*.zip`.
* **AC-REFENR-001.4:** When a local ZIP file is found, the system shall extract the CSV from the ZIP.
* **AC-REFENR-001.5:** When no local files are found, the system shall attempt to download from `https://download.cms.gov/nppes/NPPES_Data_Dissemination_{month_year}.zip` for the current month.
* **AC-REFENR-001.6:** When the current month download fails, the system shall retry with each of the previous 5 months until successful.
* **AC-REFENR-001.7:** When a ZIP is downloaded successfully, the system shall extract the `npidata_pfile_*.csv` file to the NPPES directory.
* **AC-REFENR-001.8:** When all download attempts fail, the system shall fall back to loading from the NPPES API for top providers.

### REQ-REFENR-002: NPPES CSV Loading and Filtering

**User Story:** As a data analyst, I want the system to load NPPES data efficiently by filtering to only NPIs present in claims data, so that the providers table remains manageable in size.

**Acceptance Criteria:**

* **AC-REFENR-002.1:** When loading NPPES from CSV, the system shall create a temp table `claim_npis` containing all distinct billing and servicing NPIs from the claims table.
* **AC-REFENR-002.2:** When loading NPPES from CSV, the system shall use DuckDB's `read_csv_auto` with `ignore_errors=true` to handle malformed rows.
* **AC-REFENR-002.3:** When loading NPPES from CSV, the system shall use `all_varchar=true` and `null_padding=true` to handle inconsistent column types.
* **AC-REFENR-002.4:** When loading NPPES from CSV, the system shall perform an INNER JOIN between NPPES data and `claim_npis` to load only relevant providers.
* **AC-REFENR-002.5:** When loading NPPES data, the system shall extract NPI, Entity Type Code, Provider Organization Name, Provider Last Name, Provider First Name, NPI Deactivation Date, NPI Reactivation Date, NPI Deactivation Reason Code, State, City, Address Line 1, Address Line 2, Zip Code, Mailing Address fields, and Taxonomy Code.
* **AC-REFENR-002.6:** When loading NPPES data, the system shall construct a provider name from either the organization name (for entity type 2) or last name + first name (for individuals).
* **AC-REFENR-002.7:** When loading NPPES data, the system shall concatenate address line 1 and line 2 into a single address field.
* **AC-REFENR-002.8:** When loading completes, the system shall report the count of providers loaded.

### REQ-REFENR-003: NPPES API Fallback Loading

**User Story:** As a data engineer, I want the system to fall back to the NPPES API when bulk file download fails, so that the pipeline can complete even without the full NPPES file.

**Acceptance Criteria:**

* **AC-REFENR-003.1:** When NPPES bulk file loading fails, the system shall query the top 10,000 providers by total_paid from provider_summary.
* **AC-REFENR-003.2:** When calling the NPPES API, the system shall use the endpoint `https://npiregistry.cms.hhs.gov/api/?number={npi}&version=2.1`.
* **AC-REFENR-003.3:** When calling the NPPES API, the system shall batch requests in groups of 100 with a 10-second timeout per request.
* **AC-REFENR-003.4:** When an API request succeeds, the system shall parse the JSON response and extract basic provider information, enumeration type, addresses, and taxonomy code.
* **AC-REFENR-003.5:** When an API request fails or times out, the system shall continue to the next NPI without halting the pipeline.
* **AC-REFENR-003.6:** When API loading processes every 1,000 NPIs, the system shall print a progress message.
* **AC-REFENR-003.7:** When API loading completes, the system shall report the count of providers successfully loaded.

### REQ-REFENR-004: Providers Table Creation

**User Story:** As a fraud analyst, I want the system to create a structured providers table with consistent schema, so that I can join provider metadata to claims findings.

**Acceptance Criteria:**

* **AC-REFENR-004.1:** When creating the providers table, the system shall drop any existing providers table.
* **AC-REFENR-004.2:** When creating the providers table, the system shall include columns: npi, entity_type, name, deactivation_date, reactivation_date, deactivation_reason, state, city, address, zip, mailing_address, mail_city, mail_state, mail_zip, taxonomy, specialty.
* **AC-REFENR-004.3:** When populating the providers table, the system shall initialize the specialty column to empty string (to be populated later from taxonomy mapping).

### REQ-REFENR-005: Specialty Mapping from Taxonomy Codes

**User Story:** As a fraud analyst, I want the system to map taxonomy codes to human-readable specialties, so that I can identify specialty mismatches and filter providers by specialty.

**Acceptance Criteria:**

* **AC-REFENR-005.1:** When specialty mapping executes, the system shall use a predefined taxonomy-to-specialty mapping covering the top 200 taxonomy codes.
* **AC-REFENR-005.2:** When updating specialties, the system shall execute an UPDATE query for each mapped taxonomy code.
* **AC-REFENR-005.3:** When a provider's taxonomy code matches the mapping, the system shall set the specialty field to the corresponding specialty name.
* **AC-REFENR-005.4:** When a provider's taxonomy code does not match any mapping, the system shall set the specialty to "Other".
* **AC-REFENR-005.5:** When specialty mapping completes, the system shall display a sample of 5 providers with their NPI, name, state, and specialty.

### REQ-REFENR-006: HCPCS Codes Table Initialization

**User Story:** As a data analyst, I want the system to create an HCPCS codes table with descriptions and categories, so that reports display human-readable procedure names.

**Acceptance Criteria:**

* **AC-REFENR-006.1:** When creating the hcpcs_codes table, the system shall drop any existing hcpcs_codes table.
* **AC-REFENR-006.2:** When creating the hcpcs_codes table, the system shall define columns: hcpcs_code (PRIMARY KEY), short_desc, category.
* **AC-REFENR-006.3:** When the hcpcs_codes table is created, it shall initially be empty (to be populated from external files or built-in descriptions).

### REQ-REFENR-007: HCPCS External File Loading

**User Story:** As a data engineer, I want the system to load HCPCS descriptions from external reference files when available, so that the system uses current CMS code definitions.

**Acceptance Criteria:**

* **AC-REFENR-007.1:** When loading HCPCS codes, the system shall check the `reference_data/hcpcs/` directory for CSV, TSV, or TXT files.
* **AC-REFENR-007.2:** When multiple HCPCS files exist, the system shall select the largest file by size.
* **AC-REFENR-007.3:** When ZIP files exist in the HCPCS directory, the system shall extract them and re-scan for CSV/TSV/TXT files.
* **AC-REFENR-007.4:** When loading from an external HCPCS file, the system shall use DuckDB's `read_csv_auto` with `ignore_errors=true` and `all_varchar=true`.
* **AC-REFENR-007.5:** When loading from an external HCPCS file, the system shall detect column names containing "hcpcs code", "hcpcs_code", "hcpcs", "procedure code", or "code".
* **AC-REFENR-007.6:** When loading from an external HCPCS file, the system shall detect description columns containing "short description", "short desc", "description", "long description", or "long desc".
* **AC-REFENR-007.7:** When loading from an external HCPCS file, the system shall categorize codes using prefix rules (T = Home Health, H = Behavioral Health, J = Pharmacy, S = Temp/Waiver, A04 = Transportation, A/E/K/L = DME, 97 = Therapy, 992/990 = E&M, 8 = Lab, Other = Other).
* **AC-REFENR-007.8:** When loading from a fixed-width TXT file, the system shall parse the first 5 characters as the HCPCS code and extract up to 60 characters of description starting from the first alphabetic character.

### REQ-REFENR-008: HCPCS Built-In Fallback Descriptions

**User Story:** As a data engineer, I want the system to use built-in HCPCS descriptions when no external file is available, so that the pipeline completes successfully without external dependencies.

**Acceptance Criteria:**

* **AC-REFENR-008.1:** When no external HCPCS file is found or external loading fails, the system shall load from a built-in dictionary of top 100 HCPCS codes.
* **AC-REFENR-008.2:** When loading built-in HCPCS codes, the system shall include codes such as T1019, T1015, 99213, 99214, H0015, T2003, T1005, and others.
* **AC-REFENR-008.3:** When loading built-in HCPCS codes, the system shall assign categories using the same prefix rules as external file loading.

### REQ-REFENR-009: HCPCS Code Completion from Claims Data

**User Story:** As a fraud analyst, I want the system to add entries for high-volume HCPCS codes not in the reference file, so that all codes in the claims data have at least a placeholder description.

**Acceptance Criteria:**

* **AC-REFENR-009.1:** When HCPCS loading completes, the system shall query hcpcs_summary for the top 500 codes by total_paid that are not yet in hcpcs_codes.
* **AC-REFENR-009.2:** When inserting missing codes, the system shall use `INSERT OR IGNORE` to avoid duplicate key errors.
* **AC-REFENR-009.3:** When inserting missing codes, the system shall generate a description of format "Code {HCPCS_CODE}".
* **AC-REFENR-009.4:** When inserting missing codes, the system shall assign category based on prefix rules.
* **AC-REFENR-009.5:** When HCPCS loading completes, the system shall report the total count of HCPCS codes loaded.

### REQ-REFENR-010: Verification and Sampling

**User Story:** As a data quality engineer, I want the system to verify enrichment tables after loading, so that I can confirm data was loaded successfully.

**Acceptance Criteria:**

* **AC-REFENR-010.1:** When enrichment completes, the system shall query the count of rows in the providers table and display the result.
* **AC-REFENR-010.2:** When enrichment completes, the system shall attempt to query a known high-volume NPI (e.g., 1417262056) and display the name, state, and specialty if found.
* **AC-REFENR-010.3:** When enrichment completes, the system shall query the description for HCPCS code T1019 and display the result if found.
* **AC-REFENR-010.4:** When enrichment completes, the system shall display total execution time in seconds.

## Feature Behavior & Rules

The NPPES download strategy prioritizes using locally available files to avoid repeated downloads of the 10+ GB NPPES file. The system checks for extracted CSVs first, then local ZIPs, then attempts download from CMS, and finally falls back to API loading.

The NPPES CSV contains millions of provider records, so the system filters to only NPIs present in the claims table using an INNER JOIN, reducing the providers table to only relevant NPIs (typically 600,000+ providers).

Taxonomy-to-specialty mapping uses a curated list of the top 200 taxonomy codes. Unmapped codes default to "Other" rather than leaving the specialty field NULL, ensuring all providers have a specialty value for filtering.

HCPCS code categorization uses prefix-based rules that assign codes to categories like Home Health, Behavioral Health, Pharmacy, DME, Therapy, E&M, and Lab. This categorization enables grouping codes by service type in fraud pattern analysis.

The system uses `INSERT OR IGNORE` when adding codes from claims data to avoid errors if a code was already loaded from the reference file. This ensures idempotent execution even if the feature is re-run.

Deactivation dates from NPPES enable detection of post-deactivation billing, a high-confidence fraud indicator where providers continue billing after their NPI was deactivated.
