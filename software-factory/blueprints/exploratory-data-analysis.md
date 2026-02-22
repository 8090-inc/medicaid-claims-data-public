---
title: "Exploratory Data Analysis"
feature_name: null
id: "c90812af-b73d-4204-a70a-0ac7f5b34791"
---

## Feature Summary

Exploratory Data Analysis performs initial discovery on the claims dataset, calculating global statistics, identifying top providers and codes by spending, analyzing monthly trends, and assessing spending concentration. The feature produces a comprehensive `data_profile.json` containing all descriptive statistics and generates publication-ready visualizations (monthly spending trends, Lorenz curve, top providers/codes) that provide essential context for analysts and inform hypothesis generation.

## Component Blueprint Composition

This feature depends on ingested and enriched claims data:

* **@Claims Data Ingestion** — Provides `claims`, `provider_summary`, `hcpcs_summary` tables for aggregation.
* **@Reference Data Enrichment** — Provides `providers` table with names and specialties for enriched visualizations.

## Feature-Specific Components

```component
name: GlobalStatisticsCalculator
container: Analysis Engine
responsibilities:
	- Calculate global metrics: total_rows, unique_billing_npis, unique_servicing_npis, unique_hcpcs_codes, unique_months, total_paid, total_claims, total_beneficiaries
	- Calculate distribution metrics: avg_paid, median_paid, std_paid
	- Count data anomalies: negative_paid_rows, null_servicing_rows
	- Include all metrics in data_profile.json output
```

```component
name: TopEntityIdentifier
container: Analysis Engine
responsibilities:
	- Identify top 100 providers by total_paid from provider_summary table
	- For each: include NPI, name, state, specialty, total_paid, total_claims, total_beneficiaries, num_codes, num_months
	- Identify top 100 HCPCS codes by total_paid from hcpcs_summary table
	- For each: include code, description, category, total_paid, total_claims, num_providers
```

```component
name: MonthlyTrendAnalyzer
container: Analysis Engine
responsibilities:
	- Aggregate total_paid and total_claims by claim_month from provider_monthly table
	- Record monthly trends in data_profile.json
	- Detect month-over-month changes and growth patterns
```

```component
name: SpendingConcentrationCalculator
container: Analysis Engine
responsibilities:
	- Calculate cumulative percentage of total_paid by ranked providers (Lorenz curve)
	- Determine percentage of providers accounting for 50%, 80%, 90%, 99% of total spending
	- Include concentration metrics in data_profile.json
	- Support Pareto analysis identifying market power concentration
```

```component
name: ChartGenerator
container: Analysis Engine
responsibilities:
	- Generate monthly_spending_trend.png line chart showing spending trends over time
	- Generate lorenz_curve.png illustrating provider spending concentration
	- Generate top20_providers.png horizontal bar chart of top 20 providers by spending
	- Generate top20_procedures.png horizontal bar chart of top 20 procedures by spending
	- Apply HHS OpenData styling conventions (monochromatic amber, minimal chrome, readable fonts)
	- Save all charts to output/charts directory with titles, subtitles, and branding
```

```component
name: DataProfileSerializer
container: Analysis Engine
responsibilities:
	- Serialize all EDA metrics to data_profile.json in output/ directory
	- Include: global statistics, top providers/codes, monthly trends, concentration metrics
	- Format JSON with indent=2 for readability
	- Use default=str for non-standard type serialization
```

## System Contracts

### Key Contracts

* **Read-Only Database Access**: All calculations read from pre-aggregated summary tables without modification, ensuring data integrity.
* **Idempotency**: Running EDA multiple times on same database produces identical data_profile.json and charts.
* **Completeness**: Data profile includes all global statistics, preventing gaps in analyst understanding.

### Integration Contracts

* **Input**: `claims`, `provider_summary`, `hcpcs_summary`, `provider_monthly`, `providers` tables
* **Output**:
  * `output/data_profile.json` — Comprehensive statistics and entity lists
  * `output/charts/monthly_spending_trend.png`, `lorenz_curve.png`, `top20_providers.png`, `top20_procedures.png`
* **Downstream Dependency**: @Hypothesis Generation uses EDA statistics to inform hypothesis parametrization

## Architecture Decision Records

### ADR-001: Pre-Aggregated Table Access for Speed

**Context:** Computing global statistics directly from 227M claims rows would be slow. Pre-aggregated tables from Milestone 1 enable instant calculations.

**Decision:** All EDA calculations operate on `provider_summary`, `hcpcs_summary`, `provider_monthly` tables rather than raw claims.

**Consequences:**

* Benefits: EDA completes in seconds; enables fast exploratory iteration
* Trade-off: EDA cannot compute sub-group statistics not in pre-aggregates (e.g., provider-code-state combinations)
* Mitigation: @Hypothesis Generation can request custom aggregates for specific hypothesis parametrization

### ADR-002: HHS OpenData Visualization Style

**Context:** CMS and HHS stakeholders expect visualizations conforming to federal open data standards.

**Decision:** Apply HHS styling to all charts: monochromatic amber color scheme, minimal chrome, large readable fonts, clear titles/subtitles, consistent branding.

**Consequences:**

* Benefits: Professional appearance; consistency across CMS reporting
* Trade-off: Limited to monochromatic palette; less visually striking than color-rich dashboards
* Compliance: Meets federal accessibility and consistency standards

## Testing & Validation

### Acceptance Tests

* **AC-EDA-001.1 through AC-EDA-001.4**: Verify global statistics calculated: total_rows, unique_billing_npis, unique_servicing_npis, unique_hcpcs_codes, unique_months, total_paid, total_claims, total_beneficiaries, avg_paid, median_paid, std_paid, negative_paid_rows, null_servicing_rows; all included in data_profile.json
* **AC-EDA-002.1 through AC-EDA-002.4**: Verify top 100 providers identified by total_paid with NPI, name, state, specialty, metrics; verify top 100 HCPCS codes identified with code, description, category, metrics
* **AC-EDA-003.1 through AC-EDA-003.3**: Verify monthly aggregations by claim_month; verify monthly_spending_trend.png generated as line chart
* **AC-EDA-004.1 through AC-EDA-004.4**: Verify spending concentration calculated; verify percentages for 50%, 80%, 90%, 99% cumulative spending identified; verify lorenz_curve.png generated
* **AC-EDA-005.1 through AC-EDA-005.3**: Verify data_profile.json generated in output/ with all metrics; verify JSON formatted with indent=2
* **AC-EDA-006.1 through AC-EDA-006.4**: Verify top20_providers.png and top20_procedures.png generated; verify HHS OpenData styling applied (monochromatic amber, titles, subtitles, branding)

### Unit Tests

* **GlobalStatisticsCalculator**: Test aggregation queries; test unique counting; test anomaly counting; test distribution metrics
* **TopEntityIdentifier**: Test top 100 providers query; test top 100 codes query; test field inclusion
* **MonthlyTrendAnalyzer**: Test monthly aggregation by claim_month; test trend detection
* **SpendingConcentrationCalculator**: Test Lorenz curve calculation; test percentile determination; test HHI-style concentration metrics
* **ChartGenerator**: Test chart creation (line, bar); test HHS styling application; test PNG file output
* **DataProfileSerializer**: Test JSON structure; test indent=2 formatting; test default=str serialization

### Integration Tests

* **End-to-End EDA**: Load tables -> calculate global statistics -> identify top entities -> analyze trends -> compute concentration -> generate charts -> serialize to JSON
* **Data Completeness**: Verify data_profile.json includes all expected fields and entities
* **Chart Quality**: Generate all 4 charts; verify readability; verify file formats correct (PNG)
* **Idempotency**: Run EDA twice on same database -> verify identical data_profile.json and charts
* **Concentration Accuracy**: Manually calculate top-N providers' cumulative share; compare to data_profile.json; verify within 0.1% tolerance

### Test Data Requirements

* **Input Tables**: claims (full 227M rows), provider_summary (~617k), hcpcs_summary (~10.8k), provider_monthly (~40M), providers (enriched)
* **Distribution Variety**: Mix of high-volume and low-volume providers; codes with varying utilization; monthly trends showing growth, decline, and stable periods

### Success Criteria

* All 6 requirements (REQ-EDA-001-REQ-EDA-006) fully satisfied
* data_profile.json generated with all required statistics
* All 4 charts generated with HHS OpenData styling applied correctly
* Spending concentration metrics accurate
* Charts readable and professional quality
* Re-running EDA on same data produces identical results (idempotency verified)
* Data profile enables hypothesis generation with accurate baseline statistics
