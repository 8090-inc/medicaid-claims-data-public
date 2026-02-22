---
title: "Executive Dashboard Cards"
feature_name: null
id: "af26d05f-5299-42aa-b24c-e21f01e08e6d"
---

## Feature Summary

Executive Dashboard Cards generates three pixel-perfect PNG dashboard cards (monthly spending trend, top 20 procedures, top 20 flagged providers) sized for web and presentation embedding (833x547 and 833x969 pixels). All cards follow HHS OpenData design specifications with monochromatic amber styling, precise typography, and government branding. Cards are self-contained visual assets suitable for web dashboards, briefing slides, and executive briefing materials.

## Component Blueprint Composition

This feature composes charting and styling capabilities:

* **Chart and Visualization Generation** — Uses chart utility functions and HHS styling infrastructure.

## Feature-Specific Components

```component
name: DashboardCardRenderer
container: Reporting Service
responsibilities:
	- Generate card1 (monthly spending): 833x547 pixels, line chart, 150 DPI
	- Generate card2 (top procedures): 833x969 pixels, horizontal bar chart
	- Generate card3 (top providers): 833x969 pixels, horizontal bar chart
	- Apply HHS footer branding and border to all cards
	- Use precise padding calculations per design spec
	- Format currency values in billions with proper notation
```

```component
name: HHSStyleApplier
container: Reporting Service
responsibilities:
	- Apply monochromatic amber color scheme (HHS_AMBER #F59F0A)
	- Configure fonts: title fonts (Inter/fallback), mono fonts (JetBrains Mono/fallback)
	- Apply minimal gridlines and borders
	- Add HHS branding footer with government seal
	- Ensure consistent padding and spacing across cards
```

## System Contracts

### Key Contracts

* **Pixel-Perfect Sizing**: Cards saved at exact dimensions (833x547 / 833x969) and 150 DPI.
* **Design Consistency**: All cards use identical styling, typography, padding, and branding.
* **Data Accuracy**: Charts reflect current findings and provider data; regenerated each pipeline run.

### Integration Contracts

* **Input**: Findings data from @Fraud Detection Execution; provider data and financial impacts
* **Output**: PNG files saved to `output/cards/` directory:
  * `card1-full-monthly-spending.png`
  * `card2-full-top-procedures.png`
  * `card3-full-top-providers.png`
* **Downstream**: Embeddable in web dashboards, presentations, and briefing materials

## Architecture Decision Records

### ADR-001: Separate Card Files Over Single Dashboard

**Context:** Dashboard cards may be used individually in different contexts (dashboard, presentation, report). Combining into single image reduces flexibility.

**Decision:** Generate three separate PNG files that can be embedded independently or combined via @Merged Card Aggregation.

**Consequences:**

* Benefits: Flexible reuse in various contexts; easier updates to individual cards
* Trade-off: Requires users to manage three files rather than one dashboard image
* Mitigation: @Merged Card Aggregation provides pre-built combinations
