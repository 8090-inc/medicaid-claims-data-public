---
title: "Hypothesis Cards"
feature_name: null
id: "b869f302-f1fd-4773-bb87-2848846c6876"
---

## Feature Summary

Hypothesis Cards generates individual PNG card images for each analytical category (Categories 1-10) showing top 20 providers flagged by that detection method. Cards translate technical hypothesis descriptions into plain language, providing a visual catalog of detection method effectiveness. Each card uses 833x969 pixel dimensions with HHS styling and is suitable for inclusion in presentations, reports, or web galleries.

## Component Blueprint Composition

This feature composes charting and styling capabilities:

* **Chart and Visualization Generation** — Uses chart utilities and HHS styling.

## Feature-Specific Components

```component
name: HypothesisCardGenerator
container: Reporting Service
responsibilities:
	- Generate one card per analytical category (Categories 1-10)
	- Show top 20 providers flagged by any hypothesis in that category
	- Use 833x969 pixels at 150 DPI
	- Format titles: "Category N: {Category Name}"
	- Apply plain language descriptions (e.g., z-score -> far above peers)
	- Include one-sentence category subtitle
```

```component
name: PlainLanguageTransformer
container: Reporting Service
responsibilities:
	- Replace technical terms with plain language
	- Z-score -> far above peers
	- IQR -> outside typical range
	- GEV -> rare extreme
	- HCPCS -> procedure code
	- Provide readable category subtitles for stakeholders
```

```component
name: ZeroFindingHandler
container: Reporting Service
responsibilities:
	- Display "No findings in current data" for categories with zero findings
	- Generate card with message rather than empty chart
	- Still follow consistent card styling and branding
```

## System Contracts

### Key Contracts

* **Plain Language Consistency**: All technical terms replaced with stakeholder-friendly descriptions.
* **Card Idempotency**: Identical hypotheses and findings produce identical cards.
* **Complete Coverage**: Card generated for every category, even zero-finding categories.

### Integration Contracts

* **Input**: Hypothesis findings data from @Fraud Detection Execution; category definitions
* **Output**: PNG files saved to `output/cards/` directory:
  * `category_1_card.png` through `category_10_card.png`
  * `card_index.md` — Index file with card listings
* **Downstream**: Embeddable in reports, presentations, or web galleries

## Architecture Decision Records

### ADR-001: Plain Language Translation Over Technical Descriptions

**Context:** Hypothesis cards are for diverse stakeholders, many non-technical. Technical descriptions confuse non-statistical audiences.

**Decision:** Systematically translate technical descriptions to plain language during card generation. Maintain mappings in a lookup dictionary.

**Consequences:**

* Benefits: Accessibility to non-technical audiences; improved stakeholder engagement
* Trade-off: May lose some precision of technical terminology
* Mitigation: Link to detailed methodology docs for those wanting technical details

## Testing & Validation

### Acceptance Tests

* **Card Generation**: Verify one card per analytical category (10 total); verify PNG format at 833x969 pixels, 150 DPI
* **Top 20 Providers**: Verify each card shows top 20 providers flagged by category hypotheses
* **Plain Language**: Verify technical terms translated
* **Zero Findings Handling**: Verify categories with zero findings display message with consistent styling
* **Consistent Styling**: Verify all cards apply HHS styling
* **File Output**: Verify PNG files saved to output/cards/

### Unit Tests

* **HypothesisCardGenerator**: Test card generation for each category; test dimension/DPI validation
* **PlainLanguageTransformer**: Test term translation mappings; test subtitle generation
* **ZeroFindingHandler**: Test zero-finding case; test message display

### Integration Tests

* **Full Card Suite**: Generate all 10 category cards -> verify all created -> verify styling consistent
* **Data Accuracy**: Verify top 20 providers per category correct
* **Visual Quality**: Inspect PNG files for rendering quality

### Test Data Requirements

* **Complete Findings**: All category hypotheses with results
* **Diverse Providers**: Sufficient provider mix to populate top 20 for each category
* **All Categories**: Ensure test data has findings from all 10 categories

### Success Criteria

* All 10 category cards generated with plain language descriptions
* Top 20 providers per category accurately displayed
* Cards suitable for distribution to non-technical stakeholders
* Zero-finding categories handled gracefully
* Cards embeddable in presentations and reports
