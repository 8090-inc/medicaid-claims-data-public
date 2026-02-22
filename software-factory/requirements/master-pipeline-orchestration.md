---
title: "Master Pipeline Orchestration"
type: "feature"
id: "f0bdfe7e-1a1e-4a09-98e5-dbb0106ffb38"
---

## Overview

This feature orchestrates the complete fraud detection pipeline by executing all 24 milestones in sequence, managing dependencies, handling milestone failures, tracking progress, and generating final summary reports. It provides the master run script that transforms raw CSV claims data into actionable fraud investigation queues.

Entry point: `scripts/run_all.py` - coordinates all pipeline components.

## Terminology

* **Pipeline Milestone**: One of 24 sequential processing stages from data quality scan through final reports.
* **Milestone Dependency**: Required prior milestones that must complete before a milestone can execute.
* **Pipeline Run**: Complete execution of all 24 milestones from start to finish.
* **Checkpoint**: Saved state after milestone completion allowing resumption from that point.

## Requirements

### REQ-ORCH-001: Milestone Sequencing and Execution

**User Story:** As a pipeline administrator, I want automated milestone sequencing, so that the pipeline runs without manual intervention.

**Acceptance Criteria:**

* **AC-ORCH-001.1:** The system shall execute milestones in order: M00 (DQ Scan), M01 (Ingestion), M02 (Enrichment), M03 (EDA), M04 (Hypothesis Gen), M05 (Stats), M06 (ML), M07 (Domain Rules), M08 (Cross-Ref), M09 (Dedup), M10 (Charts), M11 (Report), M12 (Feasibility/Validation), M13 (Longitudinal), M14 (Holdout), M15 (Quality Weights), M16 (Risk Queue), M17-20 (Cards/Brief), M21 (Patterns), M22 (Action Plan), M23 (Validation Scores).
* **AC-ORCH-001.2:** The system shall check for milestone completion markers (output files exist) before proceeding to dependent milestones.
* **AC-ORCH-001.3:** The system shall log the start and end time of each milestone with elapsed duration.
* **AC-ORCH-001.4:** The system shall display progress indicators showing current milestone (X of 24) during execution.

### REQ-ORCH-002: Dependency Management

**User Story:** As a developer, I want dependency tracking, so that milestones only run when prerequisites are met.

**Acceptance Criteria:**

* **AC-ORCH-002.1:** The system shall verify that M01 (Ingestion) output exists before running M02 (Enrichment).
* **AC-ORCH-002.2:** The system shall verify that M04 (Hypothesis Gen) completes before running M05-M08 (hypothesis execution milestones).
* **AC-ORCH-002.3:** The system shall verify that M05-M08 complete before running M09 (Deduplication).
* **AC-ORCH-002.4:** The system shall skip optional milestones (M00 DQ Scan, M14 Holdout Validation) if prerequisites missing.

### REQ-ORCH-003: Resume and Checkpoint Capabilities

**User Story:** As a pipeline operator, I want resume capability, so that I can restart from failures without reprocessing completed milestones.

**Acceptance Criteria:**

* **AC-ORCH-003.1:** The system shall save completion checkpoints after each milestone to `pipeline_checkpoints.json`.
* **AC-ORCH-003.2:** When restarted, the system shall detect the last completed checkpoint and resume from the next milestone.
* **AC-ORCH-003.3:** The system shall support a `--start-from` flag allowing manual resumption from a specific milestone number.
* **AC-ORCH-003.4:** The system shall support a `--skip` flag to skip specific milestones (for debugging or custom runs).

### REQ-ORCH-004: Run Summary and Reporting

**User Story:** As a stakeholder, I want a pipeline summary, so that I understand what was executed and the results.

**Acceptance Criteria:**

* **AC-ORCH-004.1:** The system shall generate `pipeline_run_summary.md` at completion showing: total execution time, milestone completion status, total findings, total impact, errors/warnings, output files created.
* **AC-ORCH-004.2:** The summary shall include a milestone execution table with columns: milestone_number, milestone_name, status, duration, output_files.
* **AC-ORCH-004.3:** The summary shall report overall pipeline success/failure status.
* **AC-ORCH-004.4:** The system shall save a timestamped run log to `logs/pipeline_run_{timestamp}.log`.

### REQ-ORCH-005: Configuration and Parameters

**User Story:** As a pipeline administrator, I want configurable parameters, so that I can customize pipeline behavior.

**Acceptance Criteria:**

* **AC-ORCH-005.1:** The system shall support configuration via `config.yaml` for: database path, output directories, milestone enable/disable flags, performance parameters (chunk sizes, thread counts).
* **AC-ORCH-005.2:** Command-line flags shall override config file settings.
* **AC-ORCH-005.3:** The system shall validate configuration on startup and report errors for invalid settings.
* **AC-ORCH-005.4:** The system shall log the active configuration at pipeline start.

## Feature Behavior & Rules

The master orchestrator uses subprocess calls to invoke individual milestone scripts. Each milestone script returns an exit code (0 = success, non-zero = failure). On milestone failure, the orchestrator logs the error and either halts or continues based on criticality flags. Database connections are managed per-milestone to avoid long-running locks. The orchestrator tracks memory usage and can pause between milestones if memory pressure is high. Environment variables pass paths and settings to milestone scripts. The orchestrator is idempotent--running it twice produces the same results if data is unchanged.
