---
title: "Master Pipeline Orchestration"
feature_name: null
id: "d3be21a2-fb89-43e2-8db1-d88751bf2511"
---

## Feature Summary

Master Pipeline Orchestration is the central control system that executes all 24 analytical milestones in sequence, manages dependencies, handles failures, tracks progress, and generates final summary reports. It orchestrates the complete workflow from raw CSV validation through final fraud investigation queues, providing the master run script (`scripts/run_all.py`) that transforms claims data into actionable fraud findings. Entry point for the entire pipeline.

## Component Blueprint Composition

This feature orchestrates all other analytical and reporting components. No direct composition; instead, coordinates sequential execution of modules.

## Feature-Specific Components

```component
name: MilestoneExecutor
container: Orchestration Service
responsibilities:
	- Execute milestones in correct sequence (M00-M23)
	- Check for milestone completion markers
	- Verify milestone dependencies before proceeding
	- Log start/end time and elapsed duration
	- Display progress indicators (X of 24 milestones complete)
	- Handle milestone failures: log errors, halt or continue based on criticality
```

```component
name: DependencyManager
container: Orchestration Service
responsibilities:
	- Define milestone dependencies
	- Verify prerequisites are met before executing
	- Skip optional milestones if prerequisites missing
	- Report dependency issues clearly
```

```component
name: CheckpointManager
container: Orchestration Service
responsibilities:
	- Save completion checkpoints after each milestone to pipeline_checkpoints.json
	- Detect last completed checkpoint on restart
	- Support --start-from flag for manual resumption
	- Support --skip flag for skipping specific milestones
```

```component
name: PipelineSummaryGenerator
container: Orchestration Service
responsibilities:
	- Generate pipeline_run_summary.md
	- Create milestone execution table with status and duration
	- Report overall success/failure
	- Save timestamped run log
```

```component
name: ConfigurationLoader
container: Orchestration Service
responsibilities:
	- Load configuration from config.yaml
	- Support command-line flag overrides
	- Validate configuration on startup
	- Log active configuration at pipeline start
```

## System Contracts

### Key Contracts

* **Sequential Execution**: Milestones execute in strict order M00-M23; no parallelization.
* **Dependency Verification**: Each milestone's prerequisites verified before execution.
* **Idempotency**: Identical input data and configuration produce identical results.
* **Graceful Degradation**: Optional milestones skipped if prerequisites missing.

### Integration Contracts

* **Input**: Configuration file, CSV data file, reference data files
* **Output**: Complete pipeline outputs, `pipeline_run_summary.md`, checkpoint state
* **Consumers**: All downstream pipeline users

## Architecture Decision Records

### ADR-001: Subprocess-Based Milestone Execution

**Context:** 24 milestones are complex. Single Python process risks memory buildup.

**Decision:** Use subprocess.run() to invoke each milestone as independent Python script.

**Consequences:**

* Benefits: Isolation prevents state carryover; memory releases after each milestone
* Trade-off: Subprocess overhead; inter-process data via files/database
* Robustness: Enables graceful recovery from failures

### ADR-002: Checkpoint-Based Resume Capability

**Context:** Pipeline can take many hours. Failure at milestone 18 should not force re-running 0-17.

**Decision:** Save completion checkpoints after each milestone. Resume from last checkpoint on restart.

**Consequences:**

* Benefits: Enables resume without reprocessing completed work
* Trade-off: Requires careful checkpoint format and verification
