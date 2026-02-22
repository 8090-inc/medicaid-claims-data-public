---
title: "Chart and Visualization Generation"
type: "feature"
id: "2b7000c4-cab4-4c46-86ec-9927e5e877ce"
---

## Overview

This feature generates HHS OpenData-style visualizations including line charts, bar charts, scatter plots, Lorenz curves, network graphs, and heatmaps. All charts follow government design standards with monochromatic amber color scheme, minimal chrome, accessible fonts, and clear labeling. Charts support the CMS Administrator Report and executive dashboards.

Runs as Milestone 10 and produces all visual assets for reporting.

## Terminology

* **HHS OpenData Style**: U.S. government data visualization design system using accessible colors, clear typography, and minimal decoration.
* **Lorenz Curve**: Graphical representation of spending concentration showing cumulative provider share vs. cumulative spending share.
* **Network Graph**: Visual representation of billing relationships between providers (hubs, spokes, circular billing).
* **State Heatmap**: Geographic visualization showing findings or impact intensity by state.

## Requirements

### REQ-CHART-001: Core Chart Types and Styling

**User Story:** As a data analyst, I want standardized chart generation functions, so that all visualizations follow consistent HHS styling.

**Acceptance Criteria:**

* **AC-CHART-001.1:** The system shall provide chart generation functions for: line charts, horizontal bar charts, scatter plots, Lorenz curves, network graphs, and geographic heatmaps.
* **AC-CHART-001.2:** All charts shall use HHS_AMBER (#F59F0A) as primary color, HHS_DARK (#221E1C) for text, HHS_MUTED (#78716D) for secondary text, and HHS_GRID (#E5E2DC) for gridlines.
* **AC-CHART-001.3:** All charts shall use title fonts (Inter or fallback) and mono fonts (JetBrains Mono or fallback) for data labels.
* **AC-CHART-001.4:** Charts shall include proper titles, subtitles, axis labels, and HHS branding footer.
* **AC-CHART-001.5:** All charts shall be saved as PNG files at 150 DPI in `output/charts/` directory.

### REQ-CHART-002: Time Series and Trend Charts

**User Story:** As a CMS administrator, I want temporal visualizations, so that I can see spending trends and anomalies over time.

**Acceptance Criteria:**

* **AC-CHART-002.1:** The system shall generate a monthly spending trend line chart covering Jan 2018 - Dec 2024.
* **AC-CHART-002.2:** The system shall generate per-provider time series charts for the top 20 flagged providers showing monthly billing with peer median reference lines.
* **AC-CHART-002.3:** Time series charts shall handle gaps in data gracefully (no connecting lines across missing months).
* **AC-CHART-002.4:** Charts shall use dollar formatters for y-axis labels (e.g., $1.5B, $250M).

### REQ-CHART-003: Ranking and Comparison Charts

**User Story:** As an investigator, I want ranking visualizations, so that I can quickly identify top entities.

**Acceptance Criteria:**

* **AC-CHART-003.1:** The system shall generate horizontal bar charts for: top 20 flagged providers, top 20 procedures, top 20 states by impact, top 10 detection methods.
* **AC-CHART-003.2:** Bar charts shall sort descending by value and truncate labels to fit (max 40 characters with ellipsis).
* **AC-CHART-003.3:** Bar charts shall include value labels on bars for exact amounts.

### REQ-CHART-004: Distribution and Concentration Charts

**User Story:** As a policy analyst, I want distribution visualizations, so that I can understand market concentration and spending patterns.

**Acceptance Criteria:**

* **AC-CHART-004.1:** The system shall generate a Lorenz curve showing provider spending concentration with reference line for perfect equality.
* **AC-CHART-004.2:** The system shall generate scatter plots for provider risk assessment (total paid vs. anomaly score) with color coding by confidence tier.
* **AC-CHART-004.3:** The system shall generate a findings-by-category bar chart showing detection method productivity.

### REQ-CHART-005: Network and Geographic Visualizations

**User Story:** As a fraud analyst, I want network and geographic charts, so that I can visualize relationships and regional patterns.

**Acceptance Criteria:**

* **AC-CHART-005.1:** The system shall generate network graphs for the top 3 hub providers showing billing-servicing relationships using NetworkX.
* **AC-CHART-005.2:** Network graphs shall use HHS_RED for hub nodes, HHS_AMBER for spoke nodes, and edge thickness proportional to payment volume.
* **AC-CHART-005.3:** The system shall generate a state heatmap showing findings or impact by state (if geographic data available).

## Feature Behavior & Rules

Chart generation uses matplotlib with custom HHS styling applied via setup_hhs_style(). All charts include HHS border and branding. Dollar amounts are formatted using custom formatter functions. Charts handle edge cases (zero values, missing data, outliers). Network visualizations use spring layout with manual positioning hints for clarity. Chart filenames follow convention: `{descriptive_name}.png` (e.g., `top20_flagged_providers.png`, `monthly_spending_trend.png`).
