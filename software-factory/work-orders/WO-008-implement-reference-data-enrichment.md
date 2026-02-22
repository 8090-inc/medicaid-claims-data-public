---
title: "Implement Reference Data Enrichment (Milestone 02)"
number: 8
status: "completed"
feature_name: "Reference Data Enrichment"
phase: 2
---

# Implement Reference Data Enrichment (Milestone 02)

## Description

### **Summary**

Build the reference data enrichment system that downloads and loads NPPES provider registry, HCPCS procedure code descriptions, and OIG exclusion lists to enrich claims data with provider identities, specialties, and cross-reference information.

### **In Scope**

* Implement NPPES registry download with fallback strategies (local files, API)
* Create providers table with name, specialty, address, deactivation status
* Load and map taxonomy codes to human-readable specialties
* Build HCPCS codes table with descriptions and categorization
* Implement smart loading from external files with built-in fallbacks
* Create data verification and sampling utilities
* Set up efficient filtering to claims-relevant NPIs only

### **Out of Scope**

* Claims data processing (handled in previous milestone)
* Fraud detection logic
* OIG LEIE loading (can be added as enhancement)

### **Requirements**

* REQ-REFENR-001: NPPES Download and Selection
* REQ-REFENR-002: NPPES CSV Loading and Filtering
* REQ-REFENR-003: Providers Table Creation

### **Blueprints**

* Reference Data Enrichment -- NPPES loading, HCPCS enrichment, and provider profiling

### **Testing & Validation**

#### Acceptance Tests

* Verify NPPES file discovery and download strategy
* Verify claim_npis temp table created; verify CSV loaded with ignore_errors
* Verify providers table dropped and recreated with correct columns
* Verify taxonomy-to-specialty mapping applied
* Verify hcpcs_codes table created with proper columns

#### Unit Tests

* *NPPESDownloader*: Test file discovery logic; test download URL construction
* *NPPESLoader*: Test CSV loading with error handling; test claim NPI filtering
* *SpecialtyMapper*: Test taxonomy code mapping; test unmapped code handling
* *HCPCSLoader*: Test file discovery; test format detection; test categorization rules
* *DataVerifier*: Test row count validation; test sampling queries

#### Integration Tests

* *Full Enrichment Pipeline*: Run complete enrichment -> verify tables populated
* *Fallback Testing*: Block bulk downloads -> verify API fallback executes
* *Data Quality*: Join enriched providers to claims -> verify high NPI coverage

#### Success Criteria

* NPPES data successfully loaded for providers in claims data
* Providers table created with name, specialty, and geographic information
* HCPCS codes table populated with descriptions and categories
* Fallback mechanisms functional when primary data sources unavailable

## Implementation Plan

| File Path | Operation | Description |
|-----------|-----------|-------------|
| `scripts/02_reference_data_enrichment.py` | create | Create the main script for Milestone 02. |
| `scripts/enrichment/nppes_loader.py` | create | Create a module for downloading and loading NPPES provider registry data. |
| `scripts/enrichment/specialty_mapper.py` | create | Create a module for loading and mapping taxonomy codes to specialties. |
| `scripts/enrichment/hcpcs_loader.py` | create | Create a module for loading HCPCS procedure code descriptions. |
| `tests/test_reference_data_enrichment.py` | create | Create a test file for the reference data enrichment milestone. |
