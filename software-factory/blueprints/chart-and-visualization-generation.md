---
title: "Chart and Visualization Generation"
feature_name: null
id: "f9c96b4d-7e60-4436-8936-f758d4a6637d"
---

## Feature Summary

Chart and Visualization Generation creates HHS OpenData-style visualizations including line charts, horizontal bar charts, scatter plots, Lorenz curves, network graphs, and state heatmaps. All charts follow U.S. government design standards with monochromatic amber color scheme, minimal chrome, accessible typography, and clear labeling. The feature generates 11+ charts supporting the CMS Administrator Report and executive dashboards, with consistent styling and branding.

## Component Blueprint Composition

This feature composes visualization infrastructure and reporting utilities:

* **Database Layer** — Provides read-only access to findings, provider data, and network relationships; used by orchestration to populate charts.

## Feature-Specific Components

```component
name: ChartOrchestrator
container: Reporting Service
responsibilities:
	- Load findings from `final_scored_findings.json`
	- Orchestrate generation of 11+ charts by delegating to chart utility functions
	- Call #ChartUtilityFunctions to render line charts, bar charts, scatter plots, network graphs, heatmaps
	- Handle data retrieval, aggregation, and transformation for each chart type
	- Manage output directory (`output/charts/`) and file naming conventions
	- Log chart generation progress and completion
```

The `#ChartOrchestrator` queries findings and provider data, aggregates by category/method/state, and delegates rendering to `#ChartUtilityFunctions` which abstract matplotlib plotting and apply consistent HHS styling.

```component
name: ChartUtilityFunctions
container: Reporting Service
responsibilities:
	- Provide `create_line_chart()` function for time series visualizations
	- Provide `create_horizontal_bar_chart()` for ranking/comparison charts
	- Provide `create_scatter_chart()` for distribution analysis
	- Apply HHS styling via `setup_hhs_style()` to all figures
	- Format currency values using `dollar_formatter()`
	- Add HHS border and branding footer to all charts
	- Manage font selection and fallback logic
	- Handle axis configuration, gridlines, and label formatting
```

The `#ChartUtilityFunctions` module encapsulates matplotlib configuration, styling constants, and reusable chart generation functions. It ensures visual consistency across all charts by applying HHS design tokens (colors, fonts, spacing) uniformly.

## System Contracts

### Key Contracts

* **Chart Idempotency**: Identical findings and provider data produce identical charts across runs.
* **File Stability**: Chart PNG files are saved to `output/charts/{chart_name}.png` at 150 DPI with consistent metadata.
* **Design Consistency**: All charts apply HHS styling (colors, fonts, gridlines, branding) without modification.
* **Label Truncation**: Long category labels are truncated to fit (max 40 characters) with ellipsis; labels never overflow chart bounds.
* **Data Gaps**: Time series charts handle missing months gracefully (no connecting lines across data gaps).

### Integration Contracts

* **Input Data**: Expects `final_scored_findings.json` in output directory; queries to `provider_monthly`, `provider_summary`, `billing_servicing_network`, and `providers` tables.
* **Output**: PNG chart files saved to `output/charts/` directory with filenames: `monthly_spending_trend.png`, `top20_flagged_providers.png`, etc.
* **Upstream Dependency**: Chart data sourced from scored findings and analysis milestones.
* **Downstream Consumers**: CMS Administrator Report, executive dashboards, and presentation templates embed generated PNG files.

## Architecture Decision Records

### ADR-001: Utility Function Abstraction Over Matplotlib

**Context:** Direct matplotlib use across multiple chart types leads to repeated styling code, inconsistent appearance, and difficulty in maintaining design standards. Each chart writer must remember colors, fonts, and layout rules.

**Decision:** Create a utility module `chart_utils.py` with reusable functions (`create_line_chart`, `create_horizontal_bar_chart`, `create_scatter_chart`) that accept data and configuration, apply HHS styling internally, and handle file I/O. All styling constants are centralized (HHS_AMBER, HHS_DARK, etc.).

**Consequences:** Improves consistency, reduces code duplication, and centralizes styling decisions. Design changes (e.g., color updates) propagate automatically. Trade-off: utility functions are less flexible than raw matplotlib; highly custom charts require direct matplotlib.

### ADR-002: HHS Design Token Centralization

**Context:** Government design standards specify specific colors, fonts, and spacing. Embedding these values throughout the codebase creates maintenance burden and increases risk of inconsistency.

**Decision:** Define all HHS design tokens as module-level constants (HHS_AMBER, HHS_DARK, HHS_MUTED, HHS_GRID, HHS_RED, HHS_GREEN, HHS_BORDER) and font selection logic (`get_title_font()`, `get_mono_font()`) at the top of `chart_utils.py`. Apply these consistently across all chart functions.

**Consequences:** Single source of truth for design decisions. Changes to brand colors or fonts require only one update. Enables environment-aware font selection with automatic fallbacks, improving portability across systems.

## Testing & Validation

### Acceptance Tests

* **Chart Generation**: Verify 11+ charts generated from findings data; verify all chart types created (line, bar, scatter, network, heatmap)
* **HHS Styling**: Verify HHS OpenData styling applied to all charts (monochromatic amber, colors, fonts, gridlines, borders)
* **File Output**: Verify PNG files saved to output/charts/ with correct filenames at 150 DPI
* **Label Formatting**: Verify long labels truncated to 40 characters with ellipsis; verify no label overflow
* **Data Gap Handling**: Verify time series charts handle missing data without connecting lines
* **Currency Formatting**: Verify dollar amounts formatted with thousands separators and proper notation
* **Branding**: Verify HHS border and footer present on all charts
* **Consistency**: Verify identical findings produce identical charts across runs (idempotency)

### Unit Tests

* **ChartOrchestrator**: Test data loading; test chart delegation; test file management
* **ChartUtilityFunctions**: Test line/bar/scatter chart creation; test HHS styling application
* **Label Processing**: Test truncation; test ellipsis; test overflow prevention
* **Data Handling**: Test missing data; test null values; test aggregations
* **Formatting**: Test currency format; test number notation

### Integration Tests

* **Full Suite**: Generate all 11+ charts -> verify all created -> verify styling consistent
* **Data Accuracy**: Sample data matches findings; aggregations correct
* **Visual Quality**: PNG files valid; DPI correct; styling matches HHS standards
* **Reproducibility**: Run twice; verify byte-identical output

### Test Data Requirements

* **Diverse Findings**: Various impact levels, confidence, patterns
* **Geographic Mix**: Multiple states for heatmaps
* **Network Data**: Hub-spoke relationships
* **Time Series**: Multi-year monthly data

### Success Criteria

* All charts generated with HHS styling
* Consistent visual appearance across all charts
* Files saved at correct resolution
* Labels and formatting accurate
* Charts embeddable in reports
* Idempotent generation verified
