---
title: "Backend"
feature_name: null
id: "3b90a643-d6b9-4998-9f76-b27219a7642a"
---

# Backend

## Technology Stack and Frameworks

* **Language**: Python 3.11+
* **Data Processing**: DuckDB (columnar OLAP database for analytics), Pandas (data manipulation)
* **Statistical Analysis**: SciPy, NumPy, Statsmodels (OLS regression, time series analysis)
* **Machine Learning**: scikit-learn (Isolation Forest, DBSCAN, K-means, LOF, Random Forest), XGBoost (gradient boosting), scikit-optimize (hyperparameter tuning)
* **Time Series Analysis**: ruptures (change-point detection), CUSUM algorithms, autocorrelation analysis
* **Graph Analysis**: NetworkX (network analysis, hub-spoke detection)
* **Database**: DuckDB (primary), SQLite (optional lightweight alternative)
* **JSON/CSV Processing**: Built-in JSON/CSV modules, custom serialization utilities
* **Configuration Management**: PyYAML for config files

## Key Principles

* **Modularity**: Each analytical component (statistical, temporal, network, ML) implemented as independent classes/modules
* **Idempotency**: All processing is deterministic; rerunning produces identical outputs for identical inputs
* **Read-Only Analysis**: All hypothesis execution uses read-only database access, preventing accidental data modification
* **Error Resilience**: Milestone-level and hypothesis-level failures are caught and logged; pipeline continues processing remaining items
* **Logging First**: All operations logged with timestamp, context, and outcome; enables debugging and compliance auditing
* **Performance Awareness**: Long-running operations (30+ minutes) log progress every 5 minutes; memory usage tracked at milestone boundaries
* **Data Integrity**: All aggregations use window functions and explicit type casting; division-by-zero handled with NULLIF

## Standards and Conventions

* **File Naming**: Milestones follow zero-padded numbering (00_dq_scan.py, 01_ingest.py, ..., 23_reporting.py); output files named descriptively (statistical_findings_categories_1_5.json)
* **Function Naming**: Snake_case for functions (execute_hypothesis, calculate_zscore); PascalCase for classes (StatisticalAnalyzer, TemporalAnalyzer)
* **Column Naming**: Snake_case in databases; aliases use semantic names (billing_npi, servicing_npi, claim_month)
* **JSON Structure**: All findings JSON objects include required fields: hypothesis_id, providers (list), confidence, evidence, total_impact
* **CSV Headers**: Descriptive names with units (total_paid [USD], num_months, avg_paid_per_claim)
* **Comment Style**: Document "why" not "what"; include example values and constraints
* **Error Messages**: Include context (milestone name, file path, row count) to enable rapid diagnosis
* **Code Organization**: Imports by category (stdlib, third-party, local); constants in CAPS at module top; main() function last

## Testing & Validation

### Acceptance Tests

* **Technology Stack**: Verify Python 3.11+ runtime; verify required libraries installed (DuckDB, pandas, scipy, scikit-learn, etc.)
* **Modularity**: Verify analytical components (statistical, temporal, network, ML) implemented as independent modules/classes
* **Idempotency**: Verify rerunning on identical data produces identical outputs; verify no random state pollution between runs
* **Read-Only Analysis**: Verify all hypothesis execution uses read-only database access; verify no accidental data modification
* **Error Resilience**: Verify milestone-level errors logged; verify hypothesis-level errors caught without halting milestone
* **Logging**: Verify all operations logged with timestamp, context, outcome; verify compliance auditing enabled
* **Performance Monitoring**: Verify long-running operations log progress every 5 minutes; verify memory tracked at boundaries

### Unit Tests

* **Modularity**: Test individual analyzer classes independently; verify proper encapsulation
* **Naming Conventions**: Verify file naming (00_dq_scan.py, etc.); verify function naming (snake_case); verify class naming (PascalCase)
* **JSON Structure**: Verify findings JSON includes all required fields; verify CSV headers include units
* **Error Handling**: Verify errors include sufficient context for diagnosis
* **Type Handling**: Verify NULLIF used for division-by-zero; verify data types correct

### Integration Tests

* **Full Pipeline**: Run complete pipeline -> verify all milestones use consistent standards
* **Code Quality**: Review codebase for adherence to standards; verify consistency across modules
* **Error Messages**: Verify error messages include context (milestone, file, row count); verify helpful for diagnosis
* **Logging Consistency**: Verify all milestones use consistent logging patterns; verify logs properly structured

### Test Data Requirements

* **Diverse Test Cases**: Data covering normal, edge case, and error scenarios
* **Performance Baselines**: Understand expected performance for 227M records

### Success Criteria

* Codebase consistently follows Python best practices and project standards
* Modularity enables independent testing and development of components
* Error messages provide sufficient context for debugging
* Logging enables compliance auditing and issue diagnosis
* Idempotency verified across full pipeline
