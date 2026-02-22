---
title: "Merged Card Aggregation"
feature_name: null
id: "c83b2f8a-b837-4e6e-881e-21b6b464d278"
---

## Feature Summary

Merged Card Aggregation combines individual dashboard and hypothesis cards into composite multi-card PNG images for easier distribution, presentation, and comparison. The feature creates merged layouts of dashboard cards (horizontal stacking) and category card grids (2x2 arrangements) with consistent spacing and formatting, producing self-contained visual assets suitable for embedding in presentations and reports.

## Component Blueprint Composition

This feature composes outputs from card generation stages:

* **@Executive Dashboard Cards** — Provides three individual dashboard cards for merging.
* **@Hypothesis Cards** — Provides 10 individual hypothesis cards for grid layouts.
* **@Chart and Visualization Generation** — Provides styling and formatting utilities.

## Feature-Specific Components

```component
name: CardCompositor
container: Reporting Service
responsibilities:
	- Load individual PNG card files from output/cards/
	- Compose dashboard cards (3 cards in horizontal/vertical layout)
	- Compose category grids (2x2 layouts showing 4 cards together)
	- Maintain consistent 20px spacing between cards
	- Save merged images as PNG files
```

```component
name: LayoutOrchestrator
container: Reporting Service
responsibilities:
	- Support configurable layouts: horizontal, vertical, grid
	- Calculate canvas dimensions based on card sizes and layout
	- Support optional titles and captions
	- Apply consistent styling and spacing rules
```

```component
name: MergedCardSerializer
container: Reporting Service
responsibilities:
	- Save merged dashboard cards to merged_dashboard_cards.png
	- Save category grids to category_grid_1.png, etc.
	- Save all to output/merged_cards/ directory
	- Maintain PNG quality and metadata
```

## System Contracts

### Key Contracts

* **Spacing Consistency**: 20px gaps between all cards.
* **Quality Preservation**: Original PNG quality maintained.
* **Layout Flexibility**: Support multiple arrangement configurations.

### Integration Contracts

* **Input**: Individual PNG card files from `output/cards/`
* **Output**: Merged PNG images saved to `output/merged_cards/`
* **Downstream**: Embeddable in presentations, reports, and dashboards

## Architecture Decision Records

### ADR-001: PIL for Card Composition

**Context:** Merging PNG images requires image manipulation.

**Decision:** Use PIL for in-process image composition.

**Consequences:**

* Benefits: Pure Python, no external tool dependencies, programmatic flexibility
* Trade-off: Limited by PIL capabilities
* Portability: Works on all platforms

## Testing & Validation

### Acceptance Tests

* **Card Loading**: Verify PNG card files loaded
* **Dashboard Composition**: Verify 3 dashboard cards composed
* **Category Grids**: Verify 2x2 grids created
* **Spacing**: Verify consistent 20px gaps
* **Quality Preservation**: Verify PNG quality maintained

### Unit Tests

* **CardCompositor**: Test card loading; test composition logic
* **LayoutOrchestrator**: Test layout calculation; test spacing
* **MergedCardSerializer**: Test file saving; test quality preservation

### Integration Tests

* **Full Merging**: Load cards -> compose -> verify all outputs created
* **Layout Accuracy**: Verify card positioning
* **Quality Check**: Compare original vs merged quality

### Test Data Requirements

* **Individual Cards**: Dashboard cards (3) and hypothesis cards (10)

### Success Criteria

* Dashboard cards merged into single composite image
* Category grids created with 2x2 arrangements
* Spacing consistent throughout
* PNG quality maintained
