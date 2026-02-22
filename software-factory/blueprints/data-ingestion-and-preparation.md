---
title: "Data Ingestion and Preparation"
feature_name: null
id: "238db5d7-249b-4bca-92b7-4aa263adc873"
---

# Data Ingestion and Preparation

## Overview

The Data Ingestion and Preparation system is the foundational layer of the fraud detection pipeline, responsible for consuming, validating, and preparing raw Medicaid claims data for downstream analysis. It orchestrates a three-stage workflow: (1) CSV quality scanning and validation, (2) claims ingestion into DuckDB with pre-aggregated summary tables and indexes, and (3) enrichment with provider and procedure code reference data from NPPES and HCPCS sources. The system processes **11 GB of raw claims data** (227 million records), validates structural integrity, detects data quality issues, and produces clean, indexed tables and aggregate summaries that support hypothesis generation, anomaly detection, and reporting.

## Component Breakdown

**Data Ingestion and Preparation** is implemented through three sequential milestones:

* **@Claims Data Ingestion** — Handles CSV validation, DuckDB ingestion, and creation of pre-aggregated summary tables
* **@CSV Data Quality Validation** — Pre-ingestion quality scanning to detect structural and type errors
* **@Reference Data Enrichment** — Enriches claims with provider registry (NPPES) and procedure code (HCPCS) reference data

The orchestration is managed by `scripts/run_all.py` (Master Pipeline Orchestration), which ensures these stages execute sequentially and validates prerequisites before proceeding.

## Data Flow

Raw CSV flows through validation -> DuckDB ingestion with indexing -> reference enrichment -> output to summary tables and Parquet export. #CSVValidator produces validation reports; #DataIngestor creates indexed `claims` table, pre-aggregated summaries (`provider_summary`, `hcpcs_summary`, `provider_monthly`, `provider_hcpcs`, `billing_servicing_network`), and Parquet export; #ReferenceEnricher populates `providers` and `hcpcs_codes` tables that are joined into findings and reports downstream.

## Testing & Validation

### Acceptance Tests

* **Three-Stage Workflow**: Verify sequential execution of CSV validation -> ingestion -> enrichment; verify each stage dependent on previous
* **Stage 1 - Validation**: Verify CSV quality scanning completes; verify data_quality_report.json and invalid_rows.csv generated
* **Stage 2 - Ingestion**: Verify DuckDB ingestion completes; verify 6 tables created (claims, provider_summary, hcpcs_summary, provider_monthly, provider_hcpcs, billing_servicing_network); verify indexes created
* **Stage 3 - Enrichment**: Verify providers and hcpcs_codes tables enriched; verify NPPES data loaded; verify specialty mapping applied; verify HCPCS codes populated
* **Output Completeness**: Verify all summary tables created with expected row counts; verify Parquet export successful; verify quality reports generated
* **Data Quality**: Verify invalid rows tracked and reported; verify enrichment rates documented; verify completeness metrics provided
* **Orchestration**: Verify three stages execute in correct order; verify each stage prerequisites verified; verify failures in early stages halt downstream stages

### Unit Tests

* **Stage Sequencing**: Test prerequisite checking logic; test halt-on-error logic
* **Validation Stage**: Test CSV scanning completes; test report generation
* **Ingestion Stage**: Test table creation; test index creation; test aggregation correctness
* **Enrichment Stage**: Test provider loading; test specialty mapping; test HCPCS code loading
* **Output Validation**: Test table row counts; test schema verification; test file output

### Integration Tests

* **Full Pipeline**: Run all three stages sequentially -> verify all outputs created -> verify data quality consistent across stages
* **Stage Dependencies**: Disable output from stage 1 -> verify stage 2 halts with clear error; fix stage 1 -> verify stage 2 proceeds
* **Data Continuity**: Track sample provider through all 3 stages (CSV -> claims -> enriched provider record) -> verify data integrity maintained
* **Quality Tracking**: Verify invalid row count from stage 1 matches documentation; verify enrichment rate documented; verify completeness metrics accurate
* **Idempotency**: Run full workflow twice -> verify identical outputs; verify no duplicate data from re-runs

### Test Data Requirements

* **CSV Dataset**: 227M-row claims file with mix of valid and invalid rows
* **NPPES Data**: Provider registry for enrichment
* **HCPCS Data**: Code descriptions for enrichment
* **Error Cases**: Data with quality issues for testing error handling

### Success Criteria

* All three stages execute sequentially and successfully
* CSV validation identifies data quality issues and produces diagnostic reports
* Ingestion creates all 6 summary tables with correct row counts and indexes
* Enrichment populates provider and code reference tables
* Output files suitable for downstream fraud detection analysis
* Data quality tracked and reported throughout all stages
* Re-running workflow produces identical results (idempotency verified)
