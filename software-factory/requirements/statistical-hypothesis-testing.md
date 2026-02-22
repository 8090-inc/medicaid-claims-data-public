---
title: "Statistical Hypothesis Testing"
type: "feature"
id: "7cd1a7be-8a5b-4f54-819a-7cfd95de1c67"
---

## Overview

This feature executes Categories 1-5 of fraud detection hypotheses covering statistical outliers, temporal anomalies, peer comparisons, network analysis, and market concentration. It applies parametric statistical tests including Z-scores, IQR, GEV distributions, Benford's Law, change-point detection, peer median comparisons, graph analysis, and HHI calculations. Each hypothesis test produces findings with confidence scores, evidence strings, and estimated financial impact.

Runs as Milestone 5 in the pipeline and produces the first major batch of fraud findings.

## Terminology

* **Finding**: A single detection result where a provider meets a hypothesis's acceptance criteria, including NPI, confidence score, evidence, and financial impact.
* **Z-Score**: Standard deviations above the mean; providers exceeding threshold (typically 3.0) are flagged.
* **IQR (Interquartile Range)**: Outlier detection using Q3 + k*IQR thresholds.
* **GEV (Generalized Extreme Value)**: Distribution for modeling rare extreme events; providers exceeding 99th percentile return levels are flagged.
* **Change-Point**: Statistical location where a time series shifts to a different mean/variance regime.

## Requirements

### REQ-STAT-001: Category 1 - Statistical Outlier Detection

**User Story:** As a fraud investigator, I want to detect statistical outliers, so that I can identify providers whose billing deviates significantly from normal patterns.

**Acceptance Criteria:**

* **AC-STAT-001.1:** The system shall execute all testable Category 1 hypotheses (H0001-H0150) using the StatisticalAnalyzer class.
* **AC-STAT-001.2:** For Z-score hypotheses (1A, 1B, 1C), the system shall calculate mean and standard deviation from peer groups, then flag providers exceeding Z > 3.0.
* **AC-STAT-001.3:** For IQR hypotheses (1D), the system shall calculate Q1, Q3, IQR, and flag providers exceeding Q3 + 3*IQR.
* **AC-STAT-001.4:** For GEV hypotheses (1E), the system shall fit GEV distributions using scipy, calculate 99th percentile return levels, and flag providers exceeding this threshold.
* **AC-STAT-001.5:** For Benford's Law hypotheses (1F), the system shall extract first digits from payment amounts, perform chi-squared tests, and flag providers with p < 0.001.
* **AC-STAT-001.6:** Each finding shall include hypothesis_id, provider NPI list, confidence score (0.6-0.99), evidence string, and total_impact in dollars.

### REQ-STAT-002: Category 2 - Temporal Anomaly Detection

**User Story:** As a CMS administrator, I want to detect temporal anomalies, so that I can identify sudden spikes, disappearances, and unusual timing patterns.

**Acceptance Criteria:**

* **AC-STAT-002.1:** The system shall execute all testable Category 2 hypotheses (H0151-H0270) using the TemporalAnalyzer class.
* **AC-STAT-002.2:** For spike detection (2A), the system shall calculate month-over-month ratios and flag providers exceeding 3x, 5x, or 10x thresholds.
* **AC-STAT-002.3:** For sudden appearance (2B), the system shall identify providers whose first billing month exceeds specified dollar thresholds ($100K-$1M).
* **AC-STAT-002.4:** For sudden disappearance (2C), the system shall detect providers active for 6+ months who abruptly stop billing.
* **AC-STAT-002.5:** For change-point detection (2H), the system shall apply CUSUM or PELT algorithms to identify statistical regime changes in billing series.
* **AC-STAT-002.6:** Confidence scores shall increase with spike magnitude (3x = 0.65, 5x = 0.75, 10x = 0.90).

### REQ-STAT-003: Category 3 - Peer Comparison

**User Story:** As a policy analyst, I want peer comparisons, so that I can identify providers billing at rates or volumes significantly above similar providers.

**Acceptance Criteria:**

* **AC-STAT-003.1:** The system shall execute all testable Category 3 hypotheses (H0271-H0400) using the PeerAnalyzer class.
* **AC-STAT-003.2:** For rate comparisons (3A), the system shall calculate peer median paid-per-claim for each HCPCS code and flag providers exceeding 2x median.
* **AC-STAT-003.3:** For volume comparisons (3B), the system shall calculate peer median claims and flag providers exceeding 10x median.
* **AC-STAT-003.4:** For geographic peer comparisons (3D), the system shall calculate state-level percentiles and flag providers exceeding the 95th percentile.
* **AC-STAT-003.5:** For specialty peer comparisons (3E), the system shall group providers by specialty and flag those exceeding specialty 95th percentile.
* **AC-STAT-003.6:** Financial impact shall be calculated as (provider_metric - peer_median) * volume.

### REQ-STAT-004: Category 4 - Network Analysis

**User Story:** As a fraud investigator, I want network analysis, so that I can detect hub-and-spoke structures, circular billing, and shell networks.

**Acceptance Criteria:**

* **AC-STAT-004.1:** The system shall execute all testable Category 4 hypotheses (H0401-H0520) using the NetworkAnalyzer class.
* **AC-STAT-004.2:** For hub-and-spoke detection (4A), the system shall count unique servicing NPIs per billing NPI and flag those exceeding thresholds (50, 100, 200).
* **AC-STAT-004.3:** For circular billing (4C), the system shall detect bidirectional billing edges where both A->B and B->A exist with payments exceeding $50K.
* **AC-STAT-004.4:** For ghost network detection (4G), the system shall check for missing NPPES records, deactivated NPIs, and single-biller concentration patterns.
* **AC-STAT-004.5:** The system shall use NetworkX or similar graph library for connected component analysis and density calculations.

### REQ-STAT-005: Category 5 - Concentration and Market Power

**User Story:** As a competition analyst, I want concentration metrics, so that I can identify monopolistic billing patterns and market manipulation.

**Acceptance Criteria:**

* **AC-STAT-005.1:** The system shall execute all testable Category 5 hypotheses (H0521-H0600) using the ConcentrationAnalyzer class.
* **AC-STAT-005.2:** For provider dominance (5A), the system shall calculate each provider's share of total spending per HCPCS code and flag those exceeding 30%, 50%, or 80%.
* **AC-STAT-005.3:** For single-code specialists (5B), the system shall calculate revenue concentration ratios and flag providers with >90% revenue from one code.
* **AC-STAT-005.4:** For HHI calculations (5C), the system shall compute Herfindahl-Hirschman Index per HCPCS code and flag markets exceeding 2500.
* **AC-STAT-005.5:** The system shall save all findings to `findings/statistical_findings_categories_1_5.json` with summary statistics.

## Feature Behavior & Rules

Each analyzer class (StatisticalAnalyzer, TemporalAnalyzer, PeerAnalyzer, NetworkAnalyzer, ConcentrationAnalyzer) inherits from BaseAnalyzer and implements an execute() method. Findings are accumulated in-memory during execution and written to JSON at completion. Database connections are read-only. Peer group calculations cache median values to avoid redundant queries. Confidence scoring follows category-specific formulas that increase with deviation magnitude or multiple detection signals.
