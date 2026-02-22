---
title: "Merged Card Aggregation"
type: "feature"
id: "c821baf2-fe72-4085-9ab1-95723bdbb4f6"
---

## Overview

This feature merges individual dashboard and hypothesis cards into combined multi-card images for easier distribution and presentation. It creates composite images showing multiple cards side-by-side or in grid layouts, suitable for executive briefing slides and reports.

Runs as Milestone 20 and produces aggregated visual assets.

## Terminology

* **Merged Card**: Composite image containing multiple individual cards arranged in a layout.
* **Card Grid**: 2x2 or 3x1 arrangement of individual cards in a single image.
* **Composite Layout**: Horizontal or vertical stacking of cards with consistent spacing.

## Requirements

### REQ-MERGE-001: Dashboard Card Merging

**User Story:** As a presenter, I want combined dashboard views, so that I can show multiple metrics in one slide.

**Acceptance Criteria:**

* **AC-MERGE-001.1:** The system shall create a merged image combining Cards 1, 2, and 3 (monthly spending, top procedures, top providers) in a horizontal or vertical layout.
* **AC-MERGE-001.2:** Merged images shall maintain consistent spacing (20px gaps) between cards.
* **AC-MERGE-001.3:** The merged image shall be saved as `merged_dashboard_cards.png`.

### REQ-MERGE-002: Category Summary Grids

**User Story:** As a report assembler, I want category grids, so that I can show method comparison in one view.

**Acceptance Criteria:**

* **AC-MERGE-002.1:** The system shall create 2x2 grid images showing 4 category cards together (e.g., Categories 1-4 in one grid, Categories 5-8 in another).
* **AC-MERGE-002.2:** Grid layouts shall use consistent card sizing and spacing.
* **AC-MERGE-002.3:** Grid images shall be saved as `category_grid_{N}.png`.

### REQ-MERGE-003: Custom Layouts

**User Story:** As a stakeholder, I want flexible layouts, so that I can create custom presentations.

**Acceptance Criteria:**

* **AC-MERGE-003.1:** The system shall support configurable layouts via layout specification: horizontal (n cards in row), vertical (n cards in column), grid (rows x cols).
* **AC-MERGE-003.2:** Merged images shall support optional titles and captions.
* **AC-MERGE-003.3:** The system shall save all merged cards to `output/merged_cards/` directory.

## Feature Behavior & Rules

Card merging uses PIL (Python Imaging Library) to composite PNG images. Cards are loaded, resized if needed, and pasted into a new canvas with calculated dimensions. Spacing is consistent across layouts. Merged cards maintain original PNG quality. The feature can be run standalone or as part of the pipeline. Custom layouts can be specified via configuration file.
