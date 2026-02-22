---
title: "Exploratory Data Analysis"
type: "feature"
id: "89329613-b44d-4e38-9d0b-81fa1d72f13d"
---

## Overview

This feature performs initial exploratory data analysis (EDA) and generates a comprehensive data profile for the entire Medicaid claims dataset. It calculates global statistics, identifies top providers and HCPCS codes by spending, analyzes monthly spending trends, and assesses spending concentration using Pareto analysis. The output is a JSON data profile and several baseline charts that provide a high-level understanding of the data's characteristics and highlight potential areas for deeper investigation.

This runs as Milestone 3 in the pipeline and serves as a foundational step for hypothesis generation and fraud detection, offering critical context for analysts and investigators.

## Terminology

* **Data Profile**: A JSON document summarizing key statistics and insights about the claims dataset.
* **Global Statistics**: Overall metrics such as total rows, unique NPIs, total paid, and average paid amounts.
* **Spending Concentration**: Analysis of how spending is distributed among providers or codes, often using Pareto principle (e.g., top X% of providers account for Y% of spending).
* **HHS Style Charts**: Visualizations conforming to the U.S. government's open data visualization conventions.

## Requirements

### REQ-EDA-001: Global Statistics Calculation

**User Story:** As a data analyst, I want the system to calculate core statistics for the entire dataset, so that I can quickly understand the overall scale and characteristics of the data.

**Acceptance Criteria:**

* AC-EDA-001.1: The system shall calculate and record `total_rows`, `unique_billing_npis`, `unique_servicing_npis`, `unique_hcpcs_codes`, `unique_months`, `total_paid`, `total_claims`, `total_beneficiaries`.
* AC-EDA-001.2: The system shall calculate and record `avg_paid`, `median_paid`, and `std_paid` for all claims.
* AC-EDA-001.3: The system shall count and record `negative_paid_rows` and `null_servicing_rows`.
* AC-EDA-001.4: All calculated statistics shall be included in the `data_profile.json` output.

### REQ-EDA-002: Top Entity Identification

**User Story:** As a fraud investigator, I want to see the highest spending providers and HCPCS codes, so that I can focus on areas with the largest financial impact.

**Acceptance Criteria:**

* AC-EDA-002.1: The system shall identify the top 100 providers by `total_paid` from the `provider_summary` table.
* AC-EDA-002.2: For each top provider, the system shall include NPI, name, state, specialty, `total_paid`, `total_claims`, `total_beneficiaries`, `num_codes`, and `num_months` in the data profile.
* AC-EDA-002.3: The system shall identify the top 100 HCPCS codes by `total_paid` from the `hcpcs_summary` table.
* AC-EDA-002.4: For each top HCPCS code, the system shall include code, description, category, `total_paid`, `total_claims`, and `num_providers` in the data profile.

### REQ-EDA-003: Monthly Spending Trend Analysis

**User Story:** As a CMS administrator, I want to view the overall monthly spending trend, so that I can monitor changes in program expenditures over time.

**Acceptance Criteria:**

* AC-EDA-003.1: The system shall aggregate `total_paid` and `total_claims` by `claim_month`.
* AC-EDA-003.2: The monthly spending data shall be recorded in the `data_profile.json`.
* AC-EDA-003.3: The system shall generate a line chart showing monthly spending trends, saved as `monthly_spending_trend.png` in the `output/charts` directory.

### REQ-EDA-004: Spending Concentration (Pareto) Analysis

**User Story:** As a policy analyst, I want to understand how concentrated spending is among providers, so that I can identify the few entities responsible for the majority of costs.

**Acceptance Criteria:**

* AC-EDA-004.1: The system shall calculate the cumulative percentage of total paid by ranked providers.
* AC-EDA-004.2: The system shall determine the percentage of providers accounting for 50%, 80%, 90%, and 99% of total spending.
* AC-EDA-004.3: These concentration metrics shall be included in the `data_profile.json`.
* AC-EDA-004.4: The system shall generate a Lorenz curve chart illustrating provider spending concentration, saved as `lorenz_curve.png`.

### REQ-EDA-005: Data Profile Output

**User Story:** As a developer, I want all calculated EDA metrics to be stored in a structured JSON file, so that they can be easily accessed by other parts of the pipeline or external tools.

**Acceptance Criteria:**

* AC-EDA-005.1: The system shall generate a `data_profile.json` file in the `output/` directory.
* AC-EDA-005.2: The `data_profile.json` file shall contain all global statistics, top provider and HCPCS code lists, monthly spending data, and spending concentration metrics.
* AC-EDA-005.3: The JSON output shall be formatted with an indent of 2 for readability and use `default=str` for serialization of non-standard types.

### REQ-EDA-006: Chart Generation and Formatting

**User Story:** As a business user, I want visual summaries of the data profile, so that I can quickly grasp key trends and outliers.

**Acceptance Criteria:**

* AC-EDA-006.1: The system shall generate a horizontal bar chart of the top 20 procedures by total spending, saved as `top20_procedures.png`.
* AC-EDA-006.2: The system shall generate a horizontal bar chart of the top 20 providers by total spending, saved as `top20_providers.png`.
* AC-EDA-006.3: All generated charts shall follow HHS OpenData styling conventions (e.g., monochromatic amber, minimal chrome, no 3D effects).
* AC-EDA-006.4: All charts shall include appropriate titles, subtitles, and branding.

## Feature Behavior & Rules

The EDA process utilizes the `claims`, `provider_summary`, `hcpcs_summary`, and `providers` tables from the DuckDB database. Database connections are read-only to ensure data integrity. Elapsed time for the milestone is reported upon completion.

Chart generation uses `matplotlib` with custom HHS styling applied via `chart_utils` functions. Charts are saved as PNG files. The Lorenz curve specifically handles subsampling for plotting efficiency with large datasets.

NPI names and specialties are enriched from the `providers` table for human-readable charts, defaulting to 'NPI {billing_npi}' if the name is not found.

Spending concentration calculations accurately reflect the proportion of providers for a given cumulative spending percentage, providing a clear measure of market power distribution. Calculations handle potential division by zero for small datasets. The `data_profile.json` serves as a central repository for all EDA-derived metrics.
