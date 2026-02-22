---
title: "Individual Milestone Execution"
feature_name: null
id: "5663ffa6-5fa1-4d3c-b915-402758e8e0e2"
---

## Feature Summary

Individual Milestone Execution defines the structure and standards for all 24 milestone scripts (M00-M23), each implementing a specific pipeline stage. Each milestone is independently executable, validates its inputs, produces defined outputs, logs progress, and reports completion status. The feature ensures consistency, maintainability, and predictability across all pipeline components through standardized structure, error handling, and logging.

## Component Blueprint Composition

This feature establishes standards used by all analytical and reporting milestones. No composition; provides structural framework.

## Feature-Specific Components

```component
name: MilestoneScriptTemplate
container: Execution Framework
responsibilities:
	- Define standard structure: imports, constants, helpers, main(), if __name__ == '__main__' block
	- Use project root path convention for consistency
	- Import utilities from scripts/utils/ for database, charting, formatting
	- Log start/end time and elapsed duration
```

```component
name: InputValidator
container: Execution Framework
responsibilities:
	- Verify required input files or tables exist
	- Verify claims table populated for data-dependent milestones
	- Verify reference tables (providers, hcpcs_codes, leie) exist if required
	- Exit with clear error messages if inputs missing
```

```component
name: OutputValidator
container: Execution Framework
responsibilities:
	- Validate JSON outputs for correct structure and required fields
	- Validate CSV outputs for expected column counts and non-empty content
	- Validate markdown reports for non-zero length
	- Raise exceptions for malformed outputs
```

```component
name: ProgressLogger
container: Execution Framework
responsibilities:
	- Log progress every N records or N seconds for long-running milestones
	- Log completion of each hypothesis or batch
	- Log output record counts (findings, rows, etc.)
	- Print completion message with execution time
```

```component
name: ErrorRecovery
container: Execution Framework
responsibilities:
	- Use try-except blocks for file I/O and database operations
	- Catch per-hypothesis failures in loops; log and continue
	- Log warnings for supplementary failures (charts)
	- Save partial outputs if possible before fatal exit
```

## System Contracts

### Key Contracts

* **Idempotency**: Rerunning produces same output for same input.
* **Independence**: Milestone operates standalone; can be invoked directly or via orchestrator.
* **Standard Imports**: All milestones use sys.path.insert for working-directory independence.
* **Connection Management**: Using context managers for automatic cleanup.

### Integration Contracts

* **Input**: Varies per milestone; validated before processing
* **Output**: Saved to designated directories
* **Upstream**: Depends on prerequisites from earlier milestones
* **Downstream**: Outputs consumed by later milestones

## Architecture Decision Records

### ADR-001: Context Manager Pattern for Database Connections

**Context:** Database connections must be properly closed.

**Decision:** All database operations use Python context managers for automatic connection cleanup.

**Consequences:**

* Benefits: Guarantees cleanup; prevents resource leaks; exception-safe
* Trade-off: Slightly more boilerplate
* Standard: Follows Python best practices

### ADR-002: Long-Running Milestone Progress Logging

**Context:** Hypotheses M05-M08 may take hours.

**Decision:** Log progress every N records or N seconds.

**Consequences:**

* Benefits: Operators see activity; can detect hangs
* Trade-off: Slight performance overhead
* Transparency: Clear visibility into long-running operations
