---
title: "Individual Milestone Execution"
type: "feature"
id: "6319236e-2167-49fb-8b0a-589c79d02b93"
---

## Overview

This feature implements individual milestone execution scripts (M00-M23), each performing a specific data processing, analysis, or reporting task. Each milestone is independently executable, produces defined outputs, logs its progress, and reports completion status to the orchestrator.

Each milestone: `scripts/XX_milestone_name.py` - self-contained execution unit.

## Terminology

* **Milestone Script**: Python script implementing one pipeline stage (e.g., `03_eda.py`, `05_run_hypotheses_1_to_5.py`).
* **Milestone Output**: Files, tables, or reports produced by a milestone and consumed by downstream stages.
* **Milestone Metadata**: Execution timestamp, duration, row counts, and status saved to metadata file.
* **Read-Only Connection**: Database connection mode that prevents data modification during analysis.

## Requirements

### REQ-MILE-001: Standard Milestone Structure

**User Story:** As a developer, I want consistent milestone structure, so that scripts are maintainable and predictable.

**Acceptance Criteria:**

* **AC-MILE-001.1:** Each milestone script shall follow the structure: imports, constants, helper functions, main() function, if __name__ == '__main__' block.
* **AC-MILE-001.2:** Each milestone shall use the project root path convention: `PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`.
* **AC-MILE-001.3:** Each milestone shall import utility modules from `scripts/utils/` for database connections, chart generation, and formatting.
* **AC-MILE-001.4:** Each milestone shall log its start time, end time, and elapsed duration.

### REQ-MILE-002: Input Validation and Prerequisites

**User Story:** As a pipeline operator, I want input validation, so that milestones fail fast if prerequisites are missing.

**Acceptance Criteria:**

* **AC-MILE-002.1:** Each milestone shall verify that required input files or tables exist before processing.
* **AC-MILE-002.2:** If inputs are missing, the milestone shall log a clear error message and exit with non-zero status.
* **AC-MILE-002.3:** Data-dependent milestones (M03 EDA, M05-M08 hypotheses) shall verify that the claims table is populated.
* **AC-MILE-002.4:** Enrichment-dependent milestones shall verify that reference tables (providers, hcpcs_codes, leie) exist if required.

### REQ-MILE-003: Output Generation and Validation

**User Story:** As a quality assurance analyst, I want output validation, so that malformed outputs are caught immediately.

**Acceptance Criteria:**

* **AC-MILE-003.1:** Each milestone shall create expected output files in designated directories (`output/`, `output/charts/`, `output/findings/`, `output/analysis/`).
* **AC-MILE-003.2:** JSON outputs shall be validated for correct structure and required fields.
* **AC-MILE-003.3:** CSV outputs shall be validated for expected column counts and non-empty content.
* **AC-MILE-003.4:** Markdown reports shall be validated for non-zero length.

### REQ-MILE-004: Progress Logging and Feedback

**User Story:** As a pipeline monitor, I want progress updates, so that I can track long-running milestones.

**Acceptance Criteria:**

* **AC-MILE-004.1:** Milestones processing large datasets shall log progress every N records or N seconds (e.g., "Processed 100K claims...").
* **AC-MILE-004.2:** Hypothesis execution milestones shall log completion of each hypothesis or batch.
* **AC-MILE-004.3:** Milestones shall log counts of output records (e.g., "Generated 532 findings from Category 1").
* **AC-MILE-004.4:** Milestones shall print a completion message: "Milestone XX complete. Time: XXs".

### REQ-MILE-005: Error Recovery and Graceful Degradation

**User Story:** As a developer, I want graceful error handling, so that partial failures don't crash the pipeline.

**Acceptance Criteria:**

* **AC-MILE-005.1:** Milestones shall use try-except blocks for file I/O and database operations.
* **AC-MILE-005.2:** Hypothesis execution milestones shall catch per-hypothesis failures, log the error, and continue with remaining hypotheses.
* **AC-MILE-005.3:** Chart generation failures shall log warnings but not fail the milestone if charts are supplementary.
* **AC-MILE-005.4:** Milestones shall save partial outputs if possible before exiting on fatal errors.

## Feature Behavior & Rules

Each milestone is designed to be idempotent--rerunning produces the same output. Milestones use sys.path.insert to ensure imports work regardless of working directory. Database connections use context managers (with blocks) for automatic cleanup. Milestones that modify data (M01 Ingestion, M02 Enrichment) use write connections; all others use read-only. Long-running milestones (M05-M08 hypothesis execution, M13 longitudinal analysis) may take hours and include memory-efficient chunking. Milestone numbering follows zero-padding (00, 01, 02, ..., 23) for sorting.
