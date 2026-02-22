---
title: "UI"
feature_name: null
id: "8b2dcd39-9402-4e99-91a0-717a4038ffab"
---

# UI

## Technology Stack and Frameworks

* **Dashboard Platform**: Markdown-based reports (human-readable, version-controllable)
* **Visualization**: Matplotlib with custom HHS styling for PNG generation (no web framework)
* **Chart Export**: PNG format for embedding in reports, presentations, and web dashboards
* **Card Design**: PIL (Python Imaging Library) for image composition and merged card generation
* **Color Scheme**: HHS OpenData monochromatic amber (#F59F0A) for government compliance
* **Fonts**: Inter (titles), JetBrains Mono (data labels), with fallback to system fonts

## Key Principles

* **Report-First**: Primary deliverable is markdown reports, not interactive dashboards
* **Government Compliance**: All visualizations follow HHS OpenData design standards (monochromatic, minimal chrome, accessible)
* **Embeddable Assets**: Charts are PNG files suitable for embedding in presentations, reports, and web pages
* **NPI Anonymization**: Public-facing tables use "Provider-{rank}" rather than actual NPIs for privacy
* **Dollar Formatting**: Billions with $XXB notation; millions with $XXXM; consistent thousands separators
* **Scannable Design**: Executive documents use bullet points, bold emphasis, minimal prose; limit to 2-3 pages for briefs

## Standards and Conventions

* **Chart Filenames**: Descriptive names (monthly_spending_trend.png, top20_flagged_providers.png)
* **Card Dimensions**: Dashboard cards 833x547 (monthly) or 833x969 (bars); 150 DPI
* **Color Palette**:
  * HHS_AMBER #F59F0A (primary)
  * HHS_DARK #221E1C (text)
  * HHS_MUTED #78716D (secondary text)
  * HHS_GRID #E5E2DC (gridlines)
  * HHS_RED #DC2626 (negative/alerts)
  * HHS_GREEN #16A34A (positive/success)
* **Chart Styling**: No 3D effects, no shadows, minimal gradients; clear titles, subtitles, axis labels
* **Data Label Format**:
  * Payments: $1.5B, $250M, $50K
  * Counts: "532 findings", "617K providers"
  * Percentages: "42.3%"
  * Confidence: "HIGH", "MEDIUM", "LOW"
* **Report Structure**: Table of contents with links, clear section headings, consistent formatting
* **Card Footer**: HHS branding and government seal on all report cards
* **Accessibility**: No color-only distinctions; use patterns/hatching for colorblind users where possible

## Testing & Validation

### Acceptance Tests

* **Report Generation**: Verify markdown reports generated with all required sections
* **Chart Generation**: Verify 11+ charts generated with correct filenames and PNG format
* **Card Dimensions**: Verify correct pixel dimensions at 150 DPI
* **HHS Styling**: Verify color scheme follows HHS palette
* **Branding**: Verify HHS footer and seal on all cards
* **Data Formatting**: Verify dollar amounts formatted correctly
* **Anonymization**: Verify NPIs anonymized in public tables
* **Accessibility**: Verify no color-only distinctions

### Unit Tests

* **Chart Generation**: Test matplotlib styling; test HHS color palette; test label formatting
* **Card Generation**: Test PIL composition; test sizing; test branding footer
* **Data Formatting**: Test dollar format conversions; test confidence tier labeling
* **Font Selection**: Test availability and fallbacks

### Integration Tests

* **Full Reporting**: Generate all reports and visualizations -> verify styling consistent
* **Embeddability**: Import PNG cards into presentation software; verify correct display
* **Accessibility Review**: Review charts with accessibility checker

### Test Data Requirements

* **Diverse Findings**: All detection categories and patterns represented
* **Financial Data**: Wide range of impact values for formatting testing

### Success Criteria

* All reports and visualizations follow HHS OpenData design standards
* Charts and cards properly branded
* Dollar amounts formatted consistently
* NPIs anonymized in public reports
* Accessibility verified
* PNG files embeddable
