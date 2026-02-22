---
title: "Infrastructure"
feature_name: null
id: "b7b35779-e84c-4f8f-a8a0-5e34b0995890"
---

# Infrastructure

## Technology Stack and Frameworks

* **Compute**: Linux (Ubuntu 20.04+) or macOS; requires 16+ CPU cores, 96GB RAM for full pipeline
* **Database**: DuckDB (embedded, no server); medicaid.duckdb file persisted at project root
* **File System**: Local disk storage; output/ directory structure for findings, charts, reports
* **Network**: Optional cloud storage (S3) for Parquet export and report archival
* **Development**: VS Code, PyCharm, or vim; Python 3.11+ with venv
* **Orchestration**: Manual or cron-based scheduling of scripts/run_all.py

## Key Principles

* **Single-Machine Execution**: Entire pipeline runs on one machine; no distributed computing required
* **Persistent State**: DuckDB database file persists between runs; checkpoints enable resume capability
* **Modular Output**: All outputs (findings, charts, reports) are files; no external service dependencies
* **Scalability**: Horizontal scaling via larger machines (more cores, more RAM); vertical scaling via chunked processing
* **Disaster Recovery**: Checkpoint files and timestamped archives enable recovery from mid-pipeline failures

## Standards and Conventions

* **Project Root**: Scripts assume PROJECTROOT environment variable or os.path.dirname detection

* **Directory Structure**:

  ```
  medicaid-fraud-detection/
    scripts/
      00_dq_scan.py
      01_ingest.py
      ...
      23_reporting.py
      run_all.py
      utils/
    output/
      findings/
      charts/
      cards/
      merged_cards/
      analysis/
      reports/
    logs/
    data/
      medicaid-provider-spending.csv
    reference_data/
      nppes/
      hcpcs/
      leie/
    config.yaml
    requirements.txt
    medicaid.duckdb
  ```

* **Temporary Files**: Stored in system temp directory; cleaned up automatically after milestone completion

* **Archive Strategy**: Timestamped copies of reports saved to output/reports/archive/; pipeline_checkpoints.json saved at project root

* **Memory Management**: DuckDB configured with 96GB memory limit; milestones log memory usage if psutil available

* **Logging Paths**: logs/pipeline.log (rotating), logs/pipeline_run_{timestamp}.log (per-run), logs/audit_trail_{timestamp}.log (immutable)

## Testing & Validation

### Acceptance Tests

* **Hardware Verification**: Verify machine meets minimum specs (16+ cores, 96GB RAM)
* **Directory Setup**: Verify all directories created per structure
* **Database Persistence**: Verify medicaid.duckdb created and persists across runs
* **Output Organization**: Verify all output subdirectories created
* **Configuration**: Verify config.yaml loaded; verify PROJECTROOT detected
* **Logging**: Verify logs/ created; verify pipeline.log rotating
* **Checkpoint System**: Verify pipeline_checkpoints.json created; verify resume capability

### Unit Tests

* **Path Resolution**: Test PROJECTROOT detection; test path construction
* **Directory Creation**: Test mkdir operations; test permission handling
* **Configuration**: Test YAML parsing; test environment variable override

### Integration Tests

* **Full Setup**: Create structure -> initialize -> run pipeline -> verify all outputs organized
* **Checkpoint Recovery**: Run pipeline -> interrupt -> verify checkpoint -> resume -> verify recovery
* **Scale Testing**: Run on minimum hardware; verify acceptable performance

### Test Data Requirements

* **Machine**: 16+ cores, 96GB RAM
* **Full Dataset**: 227M records for realistic testing

### Success Criteria

* Infrastructure supports single-machine execution
* Directory structure organized and auto-created
* Database persists across runs
* No external service dependencies
* Archive provides version history
