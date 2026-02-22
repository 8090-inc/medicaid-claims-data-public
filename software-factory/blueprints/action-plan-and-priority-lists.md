---
title: "Action Plan and Priority Lists"
feature_name: null
id: "8863a556-378c-46ba-ad3a-801a8a7c22a5"
---

## Feature Summary

This feature generates actionable priority lists and investigation action plans based on risk queue rankings, fraud pattern classifications, and resource constraints. It produces structured outputs including investigator assignment lists, state-specific geographic investigation plans, network coordination recommendations, and timeline/milestone schedules for the investigation phase. The primary output is a CEO-ready memo summarizing the investigation strategy and deliverables.

## Component Blueprint Composition

This feature composes several upstream outputs and components to synthesize actionable plans:

* **Risk Queue Generation** — Provides ranked provider lists, validation scores, and initial actionable notes from `#RiskQueueOrchestrator` and `#RiskScoreCalculator`.
* **Fraud Pattern Classification** — Supplies detailed fraud pattern categories and associated findings from `#FraudPatternClassifier` which informs the narrative of the action plan.
* **Provider Validation Scores** — Consumed for refining priority scores and flagging providers with external validation hits.

## Feature-Specific Components

```component
name: ActionPlanGenerator
container: Reporting Service
responsibilities:
	- Load `final_scored_findings.json` and `provider_validation_scores.csv`
	- Calculate normalized impact and validation scores for each provider
	- Compute `priority_score` using a weighted formula (e.g., 0.7 * impact + 0.3 * validation)
	- Sort and filter providers to generate top N priority lists (e.g., top 200, top 500)
	- Apply geographic diversity constraints (e.g., max 30% from one state)
	- Generate actionable notes (`#ActionableNoteBuilder`) for each flagged provider summarizing fraud patterns
	- Write `investigation_priority_list_top200.csv` and other detailed CSVs
	- Construct `Action_Plan_Memo.md` with executive summary, immediate actions, policy recommendations, and deliverables
	- Identify network-related cases for coordinated investigation recommendations
	- Estimate resource allocation (investigator hours, timeline) based on priority tiers
```

The `#ActionPlanGenerator` is the core component that orchestrates the synthesis of all risk intelligence into coherent, actionable plans. It leverages utility functions to build detailed narratives and ensures compliance with strategic planning goals like geographic diversity.

```component
name: ActionableNoteBuilder
container: Utility Service
responsibilities:
	- Categorize findings based on method types: network, impossible volumes, temporal, post-deactivation
	- Identify high-confidence signals and multi-method flags
	- Detect public entity providers requiring policy-focused recommendations
	- Compile concise, human-readable summaries of fraud patterns for each provider
```

The `#ActionableNoteBuilder` translates the technical outputs of detection methods into practical, investigator-friendly descriptions. This component is crucial for making the priority lists immediately useful to field agents.

## System Contracts

### Key Contracts

* **Input Data Consistency**: Relies on `final_scored_findings.json` containing standardized impact and confidence tiers, and `provider_validation_scores.csv` for validated scores.
* **Priority Score Formula**: `priority_score = (0.7 * normalized_impact) + (0.3 * normalized_validation_score)` ensuring a balance between financial exposure and evidence strength.
* **Geographic Constraint Enforcement**: The system prioritizes a diverse queue by limiting state concentration, ensuring a broader and more robust investigation portfolio.
* **Output Format**: All priority lists are generated as CSV files with a predefined schema, facilitating easy import into case management systems.

### Integration Contracts

* **Input**: `output/findings/final_scored_findings.json`, `output/analysis/provider_validation_scores.csv`.
* **Output**:
  * `output/analysis/investigation_priority_list_top200.csv`
  * `output/analysis/Action_Plan_Memo.md`
  * `output/analysis/resource_allocation_plan.md`
  * `output/analysis/investigation_timeline_schedule.md` (if graphical libraries are available)
* **Upstream Dependency**: Risk queue generation, fraud pattern classification, and provider validation scoring must be completed first.
* **Downstream Consumers**: Investigation managers, field investigators, program directors, and CMS administrators rely on these documents for operational planning and strategic decision-making.

## Architecture Decision Records

### ADR-001: Weighted Priority Score for Actionable Ranking

**Context:** Purely impact-based ranking might prioritize cases with high financial exposure but low certainty. Purely confidence-based ranking might miss high-value targets. A balanced approach is needed for effective resource allocation.

**Decision:** Implement a weighted `priority_score` combining normalized financial impact and provider validation scores (from #RiskScoreCalculator). A 70/30 split (70% impact, 30% validation) was chosen to primarily target high-dollar fraud while incorporating evidence strength.

**Consequences:** Provides a more holistic and actionable ranking. Allows for strategic adjustment of weights based on program goals. Requires careful normalization of both impact and validation scores to a common scale (0-1) to ensure fair combination.

### ADR-002: Dynamic Actionable Note Generation

**Context:** Investigators need quick, summarized context on why a provider is flagged. Manually creating these summaries is time-consuming and prone to inconsistency. Automated generation is necessary for scalability.

**Decision:** Develop an `#ActionableNoteBuilder` component that dynamically constructs narrative summaries based on detected fraud patterns and confidence levels. This builder identifies key signals (e.g., network involvement, impossible volumes, public entity status) and synthesizes them into concise notes.

**Consequences:** Ensures consistency and reduces manual effort. Provides immediate insights for investigators. The note structure is rule-based and can be expanded as new patterns are identified or refined.

### ADR-003: Integration of Geographic and Network Coordination

**Context:** Fraud schemes often involve geographic clusters or inter-provider networks. Investigations benefit significantly from coordinated efforts rather than isolated case handling. The action plan should facilitate this.

**Decision:** The `#ActionPlanGenerator` will identify geographic concentrations and network-related findings. It will generate state-specific plans for high-concentration states and network investigation plans for identified hub-and-spoke or circular billing schemes. These plans will suggest optimal investigation sequences (e.g., investigate hub providers first).

**Consequences:** Enhances investigation efficiency and effectiveness by enabling coordinated efforts. Requires robust data on provider locations and network relationships. Output formats (e.g., `network_investigation_plan_{network_id}.md`) are designed for clarity and ease of use in the field.

## Testing & Validation

### Acceptance Tests

* **Priority Scoring**: Verify priority_score = 0.7 x normalized_impact + 0.3 x normalized_validation calculated per provider
* **Provider Ranking**: Verify all providers ranked by priority_score in descending order
* **Geographic Constraint**: Verify max 30% from single state enforced in final rankings; verify reordering preserves rank integrity
* **Top 200 Selection**: Verify exactly 200 providers selected after geographic reordering
* **Actionable Notes**: Verify human-readable fraud pattern notes generated; verify pattern types detected
* **Network Coordination**: Verify hub-spoke and circular billing cases identified for coordinated investigation
* **Resource Allocation**: Verify investigator hours estimated per tier; verify timeline proposed
* **CSV Outputs**: Verify investigation_priority_list_top200.csv generated with all required columns
* **Action Plan Memo**: Verify Action_Plan_Memo.md created with executive summary, immediate actions, policy recommendations
* **Geographic Plans**: Verify state-specific investigation plans generated for high-concentration states

### Unit Tests

* **ActionPlanGenerator**: Test priority scoring; test ranking logic; test geographic constraint; test tier assignment
* **ActionableNoteBuilder**: Test fraud pattern classification; test signal detection; test note generation
* **ResourceAllocator**: Test hour estimation; test timeline proposal; test team assignment

### Integration Tests

* **End-to-End Planning**: Load findings -> calculate priorities -> rank providers -> apply constraints -> assign tiers -> generate notes -> create plans
* **Score Validation**: Manually calculate priority_score for 5 providers -> verify tool results match
* **Geographic Validation**: Verify final rankings respect 30% per-state limit
* **Tier Distribution**: Verify appropriate distribution across priority tiers
* **Network Identification**: Identify hub-spoke cases manually -> verify tool identifies same
* **Action Clarity**: Review action plan -> verify immediate actions clear and assignable; verify timeline realistic

### Test Data Requirements

* **Comprehensive Findings**: All detection methods and patterns represented
* **Validation Scores**: Provider validation scores from prior milestones
* **Network Data**: Hub-spoke, circular billing relationships
* **Provider Data**: Geographic and specialty information
* **Resource Context**: Team size and capacity assumptions

### Success Criteria

* Top 200 providers prioritized by combined impact and validation score
* Geographic diversity enforced (max 30% per state)
* Investigation tiers assigned with resource estimates
* Fraud patterns classified and actionable notes generated
* Network cases grouped for coordinated investigation
* Action plan memo executive-ready
* Investigation queue deployable to field teams
