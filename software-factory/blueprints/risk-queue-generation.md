---
title: "Risk Queue Generation"
feature_name: null
id: "2fcfea05-b696-4ea6-bee7-8e6244fc48c8"
---

## Feature Summary

Risk Queue Generation creates a prioritized investigation queue of fraud risks by ranking flagged providers using composite risk scores, financial impacts, validation metrics, and investigative constraints. It produces ranked lists of top providers for investigation, evidence packages consolidating findings and provider details, priority tier assignments with resource estimates, and recommended investigation sequences that maximize early detection wins through strategic case selection.

## Component Blueprint Composition

This feature composes data aggregation, scoring, and ranking capabilities:

* **Database Layer** — Provides access to `final_scored_findings.json`, provider validation scores, and network relationship data.

## Feature-Specific Components

```component
name: RiskScoreCalculator
container: Ranking Service
responsibilities:
	- Load scored findings and provider validation scores
	- Calculate normalized impact scores (0-1 scale)
	- Calculate normalized validation scores
	- Combine into composite priority_score using weighted formula
	- Handle missing validation data gracefully
```

```component
name: RiskQueueOrchestrator
container: Ranking Service
responsibilities:
	- Execute provider ranking by composite priority score
	- Apply geographic diversity constraints (max 30% from any single state)
	- Select top 500 providers for investigation queue
	- Generate evidence packages per provider
	- Assign priority tiers: IMMEDIATE (top 50, >=80), HIGH (51-200, >=65), MEDIUM (201-400), REVIEW (401-500)
	- Estimate investigation hours per tier
	- Output structured CSV files
```

```component
name: ActionableNoteGenerator
container: Ranking Service
responsibilities:
	- Analyze flagged methods and detection patterns for each provider
	- Identify high-confidence signals, multi-method agreements, network patterns
	- Generate human-readable actionable notes
	- Classify fraud pattern types
```

```component
name: InvestigationSequenceOptimizer
container: Ranking Service
responsibilities:
	- Identify external validation flags for quick-win prioritization
	- Group network-related cases for coordinated investigation
	- Identify gateway providers whose investigation unlocks connected entities
	- Recommend start-with cases
```

## System Contracts

### Key Contracts

* **Provider Ranking**: priority_score = 0.7 * impact_normalized + 0.3 * validation_score.
* **Geographic Diversity**: No more than 30% of top 500 from any single state.
* **Priority Tier Assignment**: Deterministic by rank and score.
* **Idempotency**: Identical upstream findings produce identical queue.

### Integration Contracts

* **Input Data**: `final_scored_findings.json`, `provider_validation_scores.csv`
* **Output**: `risk_queue_top500.csv`, `priority_queue_with_notes.csv`, `investigation_sequence_recommended.csv`, evidence packages
* **Downstream Consumers**: Investigation management systems, law enforcement partners

## Architecture Decision Records

### ADR-001: Composite Scoring Formula

**Context:** Single-metric ranking misses value of multi-signal agreement.

**Decision:** Use priority_score = 0.7 * impact + 0.3 * validation.

**Consequences:** Balances financial ROI with confidence.

### ADR-002: Geographic Diversity Constraint

**Context:** Concentration in one state creates systemic risk.

**Decision:** Enforce max 30% per state.

**Consequences:** Adds robustness; may not return strict top 500 by score.

### ADR-003: Evidence Packages as JSON

**Context:** Investigators need consolidated case narratives.

**Decision:** Generate per-provider JSON files with complete evidence.

**Consequences:** Offline accessibility; enables targeted handoff.

## Testing & Validation

### Acceptance Tests

* **Risk Score Calculation**: Verify composite formula applied
* **Provider Ranking**: Verify descending order
* **Geographic Diversity**: Verify max 30% constraint
* **Priority Tiers**: Verify tier assignment and hour estimates
* **Evidence Packages**: Verify JSON files created with complete data
* **Actionable Notes**: Verify human-readable notes generated
* **Investigation Sequence**: Verify LEIE/deactivation cases prioritized

### Unit Tests

* **RiskScoreCalculator**: Test normalization; test weighting
* **RiskQueueOrchestrator**: Test ranking; test geographic constraint; test tier boundaries
* **ActionableNoteGenerator**: Test fraud pattern classification
* **InvestigationSequenceOptimizer**: Test prioritization logic

### Integration Tests

* **End-to-End Queue**: Load findings -> calculate scores -> rank -> apply constraints -> create packages -> export
* **Geographic Constraint Verification**: Count providers by state; verify no state exceeds 30%
* **Package Content**: Review evidence packages for completeness

### Test Data Requirements

* **Scored Findings**: Full findings with impacts and validation scores
* **Diverse Providers**: Geographic spread, varying impact
* **External Flags**: LEIE matches, NPPES deactivations

### Success Criteria

* Risk queue contains top 500 ranked providers
* Geographic diversity enforced
* Priority tiers enable resource allocation
* Evidence packages provide complete case context
* Investigation sequence optimized for strategic wins
