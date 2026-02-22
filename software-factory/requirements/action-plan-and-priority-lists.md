---
title: "Action Plan and Priority Lists"
type: "feature"
id: "43a76405-31bf-4414-94f5-1e7a163d26b6"
---

## Overview

This feature generates actionable priority lists and investigation action plans based on risk queue rankings, fraud pattern classifications, and resource constraints. It produces investigator assignment lists, geographic investigation plans, network coordination recommendations, and timeline/milestone schedules for the investigation phase.

Runs as Milestone 22 and produces operational planning documents.

## Terminology

* **Action Plan**: Structured document outlining investigation sequence, resource allocation, and timeline.
* **Priority List**: Ranked list of providers segmented by investigation urgency and resource requirements.
* **Investigation Milestone**: Checkpoint in the investigation workflow with expected deliverables and timelines.
* **Coordinated Investigation**: Multi-provider investigation targeting network or geographic clusters.

## Requirements

### REQ-ACTION-001: Investigation Priority Lists

**User Story:** As an investigation manager, I want prioritized action lists, so that I can assign cases to investigators.

**Acceptance Criteria:**

* **AC-ACTION-001.1:** The system shall generate `investigation_priority_list_top200.csv` with columns: rank, npi, name, state, specialty, priority_tier (IMMEDIATE/HIGH/MEDIUM), estimated_hours, recommended_investigator_type, coordination_flag.
* **AC-ACTION-001.2:** The system shall segment the list by priority tier with separate sections for each tier.
* **AC-ACTION-001.3:** Providers requiring specialized expertise (network analysis, clinical review) shall be flagged with required skill sets.
* **AC-ACTION-001.4:** Network-related providers shall be grouped for coordinated investigation.

### REQ-ACTION-002: Geographic and Network Plans

**User Story:** As a field investigator, I want geographic plans, so that I can conduct regional investigations efficiently.

**Acceptance Criteria:**

* **AC-ACTION-002.1:** The system shall generate state-specific investigation plans showing providers in each state with recommended visit sequences.
* **AC-ACTION-002.2:** For states with 10+ flagged providers, the system shall create a state action plan document.
* **AC-ACTION-002.3:** For network cases (hub-spoke, circular billing), the system shall generate network investigation plans identifying hub providers to investigate first.
* **AC-ACTION-002.4:** Network plans shall save to `action_plans/network_investigation_plan_{network_id}.md`.

### REQ-ACTION-003: Resource Allocation Plan

**User Story:** As a program director, I want resource planning, so that I can staff investigations appropriately.

**Acceptance Criteria:**

* **AC-ACTION-003.1:** The system shall calculate total investigation hours needed: IMMEDIATE tier * 40hrs + HIGH tier * 20hrs + MEDIUM tier * 10hrs.
* **AC-ACTION-003.2:** The system shall estimate timeline at various staffing levels (5, 10, 20 investigators).
* **AC-ACTION-003.3:** The system shall identify skill gaps if specialized expertise is required but unavailable.
* **AC-ACTION-003.4:** Resource allocation shall be saved to `resource_allocation_plan.md`.

### REQ-ACTION-004: Investigation Milestones and Timeline

**User Story:** As a project manager, I want milestone schedules, so that I can track investigation progress.

**Acceptance Criteria:**

* **AC-ACTION-004.1:** The system shall define investigation milestones: M1 (IMMEDIATE cases start, week 1), M2 (IMMEDIATE cases complete, week 6), M3 (HIGH cases complete, week 16), M4 (MEDIUM cases complete, week 26).
* **AC-ACTION-004.2:** For each milestone, the system shall specify expected deliverables (case files, referrals, recoveries).
* **AC-ACTION-004.3:** The system shall generate a Gantt chart or timeline visualization (if matplotlib available).
* **AC-ACTION-004.4:** Timeline shall be saved to `investigation_timeline_schedule.md`.

### REQ-ACTION-005: Action Plan Summary Memo

**User Story:** As a stakeholder, I want an action plan memo, so that I understand the investigation strategy.

**Acceptance Criteria:**

* **AC-ACTION-005.1:** The system shall generate `Action_Plan_Memo.md` summarizing: total providers to investigate, priority distribution, geographic focus areas, network investigation strategy, resource requirements, expected timeline, anticipated outcomes.
* **AC-ACTION-005.2:** The memo shall be executive-appropriate (2 pages max) with clear section headings.
* **AC-ACTION-005.3:** The memo shall include quick wins (LEIE/deactivated NPI cases) for early momentum.

## Feature Behavior & Rules

Action plans use risk queue data from Milestone 16, fraud patterns from Milestone 21, and validation scores from Milestone 23. Investigation hour estimates are based on tier assignments. Network coordination flags are set when providers share billing relationships. Geographic plans prioritize states with high provider concentration. Resource calculations assume 8-hour workdays and 80% utilization (account for non-case work). Milestones include buffer time for complex cases.
