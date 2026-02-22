---
title: "Hypothesis Cards"
type: "feature"
id: "d8128606-b2ba-41a9-a79d-8fe75a938421"
---

## Overview

This feature generates individual card images for each analytical category (Categories 1-10) showing top flagged providers per detection method. Each card visualizes the top 20 providers for that category with impact amounts, creating a visual catalog of detection method effectiveness.

Runs as Milestone 18 and produces method-specific visualizations.

## Terminology

* **Hypothesis Card**: Visual card showing top providers flagged by a specific analytical category or method.
* **Category Card**: Aggregation of all hypotheses within one of the 10 analytical categories.
* **Plain Language**: Simplified descriptions removing technical jargon (e.g., "z-score" -> "far above peers").

## Requirements

### REQ-HCARD-001: Category Card Generation

**User Story:** As a data analyst, I want cards per category, so that I can see which detection methods were most productive.

**Acceptance Criteria:**

* **AC-HCARD-001.1:** The system shall generate one card per analytical category (Categories 1-10) showing top 20 providers flagged by any hypothesis in that category.
* **AC-HCARD-001.2:** Each card shall use card dimensions 833x969 pixels at 150 DPI.
* **AC-HCARD-001.3:** Card titles shall be category names: "Category 1: Statistical Outliers", "Category 2: Temporal Anomalies", etc.
* **AC-HCARD-001.4:** Bars shall show provider names (truncated to 28 chars) and quality-weighted impact in billions.

### REQ-HCARD-002: Plain Language Descriptions

**User Story:** As a non-technical stakeholder, I want readable descriptions, so that I can understand what each method detects.

**Acceptance Criteria:**

* **AC-HCARD-002.1:** The system shall apply plain language transformations to hypothesis descriptions: "z-score" -> "far above peers", "IQR" -> "outside typical range", "GEV" -> "rare extreme", "HCPCS" -> "procedure code".
* **AC-HCARD-002.2:** Category subtitles shall explain the detection approach in one sentence (e.g., "Identifies providers whose billing patterns deviate statistically from peer norms").

### REQ-HCARD-003: Method-Specific Cards

**User Story:** As a fraud investigator, I want method-level detail, so that I can understand specific technique effectiveness.

**Acceptance Criteria:**

* **AC-HCARD-003.1:** For high-yield methods (>100 findings), the system may generate method-specific cards showing top providers for that single method.
* **AC-HCARD-003.2:** Method cards shall include the hypothesis ID and acceptance criteria in the subtitle.
* **AC-HCARD-003.3:** Cards with zero findings shall display "No findings in current data" message instead of empty chart.

### REQ-HCARD-004: Card Output and Organization

**User Story:** As a report assembler, I want organized card outputs, so that I can incorporate them into deliverables.

**Acceptance Criteria:**

* **AC-HCARD-004.1:** The system shall save all hypothesis cards to `output/cards/` directory with naming: `category_{N}_card.png`.
* **AC-HCARD-004.2:** The system shall generate an index file `card_index.md` listing all cards with thumbnails and descriptions.

## Feature Behavior & Rules

Cards use the same matplotlib styling as dashboard cards. Plain language replacements use regex transformations. Cards aggregate providers across all hypotheses in the category, deduplicating and taking maximum impact. Empty categories (zero findings) still generate cards with a "no findings" message. Cards are sized for web embedding and can be used in presentations or reports.
