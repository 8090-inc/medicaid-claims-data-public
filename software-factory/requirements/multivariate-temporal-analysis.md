---
title: "Multivariate Temporal Analysis"
type: "feature"
id: "35fdb4a9-0dbc-471c-a24b-17b1bd915315"
---

## Overview

This feature performs multivariate time series analysis on longitudinal panel data to detect temporal anomalies not visible in single-period snapshots. It fits regression models to predict paid-per-claim from provider characteristics, identifies residual outliers, detects non-linear growth patterns, and calculates multivariate risk scores combining temporal and cross-sectional signals.

Runs as part of Milestone 13 and produces advanced temporal findings for validation.

## Terminology

* **Paid-Per-Claim Residual**: The difference between actual and predicted paid-per-claim after controlling for provider characteristics.
* **Non-Linear Growth**: Acceleration or deceleration in billing growth over time (e.g., quadratic or exponential patterns).
* **Vector Autoregression (VAR)**: Multivariate time series model capturing interdependencies between multiple variables.
* **Granger Causality**: Statistical test determining whether one time series helps predict another.
* **Multivariate Risk Score**: Composite score combining temporal volatility, growth anomalies, and residual outliers.

## Requirements

### REQ-MULTI-001: Paid-Per-Claim Regression and Residuals

**User Story:** As a statistician, I want residual analysis, so that I can identify providers with unexplained billing patterns after controlling for observable factors.

**Acceptance Criteria:**

* **AC-MULTI-001.1:** The system shall fit an OLS regression model predicting paid_per_claim from specialty, state, num_codes, claims_per_bene, and num_months.
* **AC-MULTI-001.2:** The system shall calculate residuals for each provider-month observation.
* **AC-MULTI-001.3:** The system shall flag provider-months with |residual| > 3 * residual_std as outliers.
* **AC-MULTI-001.4:** The system shall aggregate provider-level residual outlier counts and save the top 500 to `ppc_residuals_top500.csv`.
* **AC-MULTI-001.5:** Residual outliers shall be annotated with the predicted value, actual value, and standardized residual.

### REQ-MULTI-002: Growth Pattern Detection

**User Story:** As a fraud analyst, I want non-linear growth detection, so that I can identify providers with accelerating or suspicious growth trajectories.

**Acceptance Criteria:**

* **AC-MULTI-002.1:** The system shall fit quadratic time trends (month, month^2) to each provider's monthly billing series with 12+ months of data.
* **AC-MULTI-002.2:** The system shall flag providers with significant positive quadratic coefficients (p < 0.01) indicating accelerating growth.
* **AC-MULTI-002.3:** The system shall calculate CAGR (Compound Annual Growth Rate) for each provider over the full 84-month period.
* **AC-MULTI-002.4:** The system shall flag providers with CAGR > 100% (doubling annually) and save to `growth_anomalies_top500.csv`.

### REQ-MULTI-003: Volatility and Stability Analysis

**User Story:** As a risk manager, I want volatility metrics, so that I can identify erratic billing patterns indicative of fraud or instability.

**Acceptance Criteria:**

* **AC-MULTI-003.1:** The system shall calculate coefficient of variation (CV = std / mean) for each provider's monthly paid series.
* **AC-MULTI-003.2:** The system shall flag providers with CV > 2.0 (high volatility) and CV < 0.1 (suspiciously stable).
* **AC-MULTI-003.3:** The system shall calculate the number of months with zero billing (gaps) and flag providers with gaps > 6 months followed by resumption.
* **AC-MULTI-003.4:** The system shall detect alternating high/low billing patterns using autocorrelation analysis.

### REQ-MULTI-004: Multivariate Risk Scoring

**User Story:** As a data scientist, I want multivariate risk scores, so that I can rank providers by combined temporal and cross-sectional anomalies.

**Acceptance Criteria:**

* **AC-MULTI-004.1:** The system shall calculate a multivariate_risk_score combining: residual_outlier_count * 1.0 + |growth_anomaly_score| * 0.5 + volatility_zscore * 0.3 + gap_penalty * 0.2.
* **AC-MULTI-004.2:** The system shall rank all providers by multivariate_risk_score and save the top 500 to `multivariate_risk_top500.csv`.
* **AC-MULTI-004.3:** The system shall calculate correlation between multivariate_risk_score and findings from Categories 1-9 to validate predictive power.
* **AC-MULTI-004.4:** The system shall generate a summary report `longitudinal_multivariate_report.md` with key findings, time range, total spending, top states, top specialties, and top codes.

### REQ-MULTI-005: Output Integration

**User Story:** As a pipeline orchestrator, I want multivariate findings integrated, so that they inform final validation and risk prioritization.

**Acceptance Criteria:**

* **AC-MULTI-005.1:** The system shall save all multivariate findings (residual outliers, growth anomalies, volatility flags) to structured tables in DuckDB.
* **AC-MULTI-005.2:** The system shall export summary CSVs to `output/analysis/` directory.
* **AC-MULTI-005.3:** The system shall provide a lookup function for downstream milestones to query multivariate risk scores by NPI.
* **AC-MULTI-005.4:** The system shall log execution time and record counts for all multivariate analysis components.

## Feature Behavior & Rules

Multivariate analysis requires the longitudinal panel constructed in the prior milestone. Regression models use statsmodels OLS. Residuals are studentized for outlier detection. Growth pattern detection uses polynomial regression via numpy.polyfit. Autocorrelation uses pandas autocorr(). Providers with fewer than 12 months of data are excluded from growth pattern analysis but included in residual analysis. Multivariate risk scores are normalized to 0-100 scale for comparability. The report includes time range, aggregate statistics, and identifies the top states, specialties, and HCPCS codes by total spending.
