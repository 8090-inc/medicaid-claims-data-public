---
title: "Provider Validation Scores"
type: "feature"
id: "151ebc74-2398-4022-98fc-1885062c4dac"
---

## Overview

This feature calculates comprehensive validation scores for each flagged provider combining multiple signal types: number of detection methods, confidence scores, financial impact, temporal persistence, network position, and external validation flags. It produces a single 0-100 provider_validation_score used for final risk ranking.

Runs as Milestone 23 and creates the authoritative provider risk score.

## Terminology

* **Provider Validation Score**: Composite 0-100 score reflecting fraud likelihood based on multiple evidence dimensions.
* **Signal Diversity**: Number of distinct detection categories (1-10) that flagged a provider.
* **Temporal Persistence**: Provider flagged in multiple time periods or with sustained anomalous patterns.
* **Network Centrality**: Provider's position in billing network (hub status, shared servicing, circular billing involvement).
* **External Validation**: Matches with LEIE, NPPES deactivations, specialty mismatches, or licensure issues.

## Requirements

### REQ-PVAL-001: Multi-Signal Scoring

**User Story:** As a fraud analyst, I want providers scored on multiple dimensions, so that I can identify those with strongest evidence.

**Acceptance Criteria:**

* **AC-PVAL-001.1:** The system shall calculate signal_diversity_score = min(30, num_methods * 6) where num_methods is count of distinct categories (1-10) that flagged the provider.
* **AC-PVAL-001.2:** The system shall calculate confidence_score_component = avg(confidence scores across all findings for provider) * 20.
* **AC-PVAL-001.3:** The system shall calculate impact_score_component = min(20, log10(total_impact) * 3) normalized to 0-20 scale.
* **AC-PVAL-001.4:** The system shall calculate temporal_persistence_score = min(15, months_flagged * 2) where months_flagged counts distinct months with anomalous activity.

### REQ-PVAL-002: Network and External Validation Scoring

**User Story:** As a network analyst, I want network position factored into scores, so that hub providers and network members are elevated.

**Acceptance Criteria:**

* **AC-PVAL-002.1:** The system shall calculate network_centrality_score = min(10, hub_servicing_count / 10) + (5 if in_circular_billing else 0) + (3 if pure_billing_entity else 0).
* **AC-PVAL-002.2:** The system shall calculate external_validation_score = (10 if LEIE_match else 0) + (8 if no_NPPES else 0) + (5 if deactivated_NPI else 0) + (5 if specialty_mismatch else 0).
* **AC-PVAL-002.3:** The system shall cap external_validation_score at 15 points maximum.

### REQ-PVAL-003: Composite Score Calculation

**User Story:** As a risk manager, I want a single composite score, so that I can rank all providers uniformly.

**Acceptance Criteria:**

* **AC-PVAL-003.1:** The system shall calculate provider_validation_score = signal_diversity_score (30 pts) + confidence_score_component (20 pts) + impact_score_component (20 pts) + temporal_persistence_score (15 pts) + network_centrality_score (10 pts) + external_validation_score (15 pts) - penalties.
* **AC-PVAL-003.2:** The system shall apply a -10 point penalty for single-method detections with confidence < 0.70.
* **AC-PVAL-003.3:** The system shall apply a +5 point bonus for providers flagged by domain rules (Category 8) indicating deterministic violations.
* **AC-PVAL-003.4:** The system shall normalize final scores to 0-100 range and save to `provider_validation_scores.csv` with columns: npi, name, state, provider_validation_score, signal_diversity, confidence_avg, total_impact, num_methods, external_flags.

### REQ-PVAL-004: Risk Tier Classification

**User Story:** As an investigator, I want providers classified into risk tiers, so that I can prioritize investigations.

**Acceptance Criteria:**

* **AC-PVAL-004.1:** The system shall classify providers into risk tiers: CRITICAL (score >= 80), HIGH (65-79), MEDIUM (50-64), LOW (< 50).
* **AC-PVAL-004.2:** The system shall calculate the distribution of providers across risk tiers.
* **AC-PVAL-004.3:** The system shall flag CRITICAL tier providers for immediate review and save to `critical_risk_providers.csv`.
* **AC-PVAL-004.4:** The system shall generate a score distribution histogram showing provider counts by score decile.

### REQ-PVAL-005: Validation Score Report

**User Story:** As a program manager, I want a validation scoring report, so that I understand the risk profile of flagged providers.

**Acceptance Criteria:**

* **AC-PVAL-005.1:** The system shall generate `provider_validation_scoring_report.md` with sections: scoring methodology, score distribution, risk tier statistics, top 100 providers by score, and external validation match rates.
* **AC-PVAL-005.2:** The report shall include summary statistics: median score, mean score, score standard deviation, and correlation between score and financial impact.

## Feature Behavior & Rules

Provider validation scores are calculated only for providers flagged by at least one hypothesis. Unflagged providers are not scored. Signal diversity is the strongest component (30 points) reflecting the principle that multi-method detections are most reliable. Temporal persistence requires linking findings across the longitudinal panel. Network centrality uses network analysis results from Category 4. External validation requires NPPES/LEIE data. Scores are recalculated if new findings are added or validation results change.
