---
title: "Technical Requirements"
type: "overview"
id: "c5358685-1c6c-4595-a1ac-15496e9491cc"
---

## Data and Infrastructure Requirements

### Input Data Specifications

**Primary Dataset: CMS Medicaid Provider Utilization and Payments** - The system shall ingest a CSV file (approximately 11 GB) containing all fee-for-service claims, managed care encounters, and CHIP claims. Required fields: BILLING_PROVIDER_NPI_NUM, SERVICING_PROVIDER_NPI_NUM, HCPCS_CODE, CLAIM_FROM_MONTH, TOTAL_UNIQUE_BENEFICIARIES, TOTAL_CLAIMS, TOTAL_PAID.

**NPPES National Provider Registry** - The system shall load and index NPPES data (10+ GB) providing provider names, specialties, locations, entity types, and deactivation dates. This reference dataset enables provider identity validation and specialty mismatch detection.

**HCPCS Procedure Code Reference** - The system shall load HCPCS code descriptions (2026 or current year version) to enable human-readable reporting and domain-specific rule application (e.g., timed services, high-risk categories).

**OIG List of Excluded Individuals/Entities (LEIE)** - The system shall load the current LEIE dataset (approximately 8,302+ NPIs) to cross-reference findings and flag providers billing after exclusion.

**CMS Data Quality Atlas** - The system shall incorporate state-level data quality measures to weight findings based on known reporting completeness and accuracy issues.

**Positive Control Dataset** (optional but recommended) - The system should support loading known fraud cases (SAM exclusions, licensure revocations, confirmed settlements) for validation and calibration of detection methods.

### Storage and Database Requirements

**DuckDB Analytical Database** - The system shall use DuckDB as the analytical database engine, creating a database file (approximately 30 GB) with optimized indexes on billing_npi, hcpcs_code, and claim_month. DuckDB enables efficient SQL-based aggregation and windowing functions over billions of rows without distributed infrastructure.

**Output Directory Structure** - The system shall organize outputs in standardized directories: `output/analysis/` (reports and queues), `output/charts/` (PNG visualizations), `output/hypotheses/` (hypothesis batches and validation), `output/findings/` (scored findings by category, regenerable), `output/qa/` (data quality reports), `output/cards/` (dashboard card components).

**File Retention and Versioning** - Large generated datasets in `output/findings/` (8+ GB, regenerable) shall be excluded from version control. Reports, charts, and queues shall be retained for historical comparison.

### Compute and Performance Requirements

**Memory** - The system shall run on hardware with at least 16 GB of RAM to support in-memory aggregations and machine learning model training.

**Storage** - The system requires at least 100 GB of available storage for input data (11 GB CSV), DuckDB database (30 GB), NPPES registry (10 GB), output findings (8 GB), and output reports/charts/queues (5 GB).

**Execution Time** - The complete 24-milestone pipeline should complete in under 4 hours on standard server hardware (16+ GB RAM, SSD storage, multi-core CPU).

**Scalability** - DuckDB's columnar storage and vectorized execution enable processing of billions of claim transactions without requiring distributed computing infrastructure.

## Technology Stack Requirements

**Programming Language** - The system is implemented in Python 3.7+ and shall use standard Python libraries for compatibility and maintainability.

**Core Libraries**:

* **pandas** - Data manipulation and CSV ingestion
* **NumPy** - Statistical calculations and array operations
* **DuckDB** - Analytical database engine
* **scikit-learn** - Machine learning models (Isolation Forest, Random Forest, DBSCAN, K-Means, Local Outlier Factor)
* **XGBoost** - Gradient boosting for anomaly scoring
* **Matplotlib and Seaborn** - Visualization and chart generation
* **NetworkX** - Graph analysis for billing network detection

**Optional Libraries**:

* **TensorFlow or PyTorch** - Deep learning models (autoencoders, VAE, LSTM, transformers) if enabled
* **Plotly** - Interactive HTML visualizations

### Pipeline Architecture Requirements

**Sequential Milestone Execution** - The system shall execute 24 milestones in a defined order via the master orchestrator script `scripts/run_all.py`. Each milestone must complete successfully before the next begins.

**Individual Milestone Execution** - Each milestone script (e.g., `03_eda.py`, `10_generate_charts.py`) shall be executable independently for iterative development, debugging, and partial re-runs.

**Error Handling and Logging** - Each milestone shall log progress to console, report errors with context, and halt pipeline execution on failure. The orchestrator shall display a summary of PASS/FAIL status for each milestone.

**Idempotency** - Milestones that generate derived tables or output files shall drop and recreate outputs, enabling re-runs without manual cleanup.

## Integration Requirements

**Input Data Integration** - The system shall accept CMS data exports in CSV format placed in the project root directory. Future enhancements may support direct connection to CMS data APIs or cloud storage (S3, Azure Blob).

**Output Data Exchange** - Investigation queues shall be exported as CSV files compatible with standard case management systems. Reports shall be generated in Markdown and HTML formats for distribution. Visualizations shall be exported as PNG files suitable for presentation decks.

**Potential Future Integrations**:

* Real-time claims processing systems for prospective fraud flagging
* Case management platforms to track investigation outcomes and recoveries
* Provider enrollment systems to automate suspension or termination workflows
* Data warehouses or business intelligence platforms for trend analysis

**API and Programmatic Access** (future consideration) - The system may expose findings via REST API or SQL views for integration with external dashboards and reporting tools.

## Security and Compliance Requirements

**Data Privacy** - The system processes aggregate provider-level data and does not contain individually identifiable beneficiary health information (PHI). However, provider NPIs and payment amounts are sensitive and shall be protected according to organizational data handling policies.

**Access Controls** - The system shall run in a controlled environment with appropriate file system permissions. Output reports containing provider identities and exposure estimates shall be shared only with authorized investigators and administrators.

**Audit Trail** - Each pipeline run shall log execution timestamps, data volume processed, and output file locations to support reproducibility and compliance reporting.

**Data Retention** - Input datasets and outputs shall be retained according to organizational records retention policies (typically 7 years for federal healthcare programs).

## Quality and Validation Requirements

**Data Quality Checks** - Milestone 0 (CSV Data Quality Scan) shall validate input data structure, detect missing required fields, identify negative or zero paid amounts, and report null values in critical fields.

**Reference Data Freshness** - The system shall document the version and effective date of all reference datasets (NPPES, HCPCS, LEIE) to ensure findings are cross-referenced against current exclusion lists and provider registries.

**Hypothesis Reproducibility** - All hypotheses shall have documented acceptance criteria, statistical thresholds, and financial impact formulas. The full hypothesis taxonomy shall be exported to `output/hypotheses/all_hypotheses.json` for transparency and reproducibility.

**Validation and Calibration** - Milestone 14 shall validate findings against holdout data (2023-2024) and report holdout persistence rates per method. Unstable methods with negative z-delta shall be flagged for pruning.

**Cross-Reference Validation** - All findings shall be checked against the LEIE exclusion list, NPPES registry, and state quality measures to provide cross-validation and evidence strength.

## Extensibility and Customization Requirements

**Hypothesis Taxonomy Extensibility** - The system shall support adding new hypotheses without modifying core pipeline code. New hypotheses can be defined in JSON configuration files or Python modules.

**Configurable Thresholds** - Statistical thresholds (z-score cutoffs, IQR multipliers, confidence tier boundaries) should be configurable via parameters or configuration files rather than hard-coded.

**Custom Fraud Pattern Definitions** - The fraud pattern classification logic (10 patterns) should be defined in a structured way that allows customization for different jurisdictions or program types (Medicare, CHIP, state-specific programs).

**Pluggable Detection Methods** - The system architecture should support adding new machine learning models, statistical tests, or domain rules as separate modules without requiring changes to the orchestrator or reporting logic.
