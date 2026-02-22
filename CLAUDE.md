# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A 24-milestone Python analytics pipeline for detecting fraud, waste, and abuse in CMS Medicaid provider spending. Analyzes $1.09 trillion in payments across 227M billing records, 617K providers, and 10.9K procedure codes (Jan 2018 – Dec 2024).

## Commands

```bash
# Run full pipeline (requires medicaid-provider-spending.csv in project root)
python3 scripts/run_all.py

# Run individual milestones
python3 scripts/03_eda.py
python3 scripts/10_generate_charts.py

# Use python3, not python (python is not on PATH)
```

There are no tests, linting, or build steps. The pipeline is a sequential data analysis workflow.

## Architecture

### Pipeline Flow

The orchestrator (`scripts/run_all.py`) runs milestones sequentially. Each milestone is a standalone Python script that reads from DuckDB and writes JSON/CSV/Markdown outputs. The pipeline halts on first failure.

```
CSV (11GB) → DuckDB Ingestion → Reference Enrichment → Hypothesis Generation →
Parallel Testing (5 Categories) → ML/DL Detection → Domain Rules →
Cross-Reference → Financial Impact → Deduplication → Priority Ranking →
Reports + Visualizations
```

**Milestone execution order** differs from numbering (see `MILESTONES` list in `run_all.py`). For example, milestone 12 (feasibility) runs before milestone 5 (hypothesis testing), and milestone 15 (DQ Atlas weights) runs before milestone 9 (financial impact).

### DuckDB Schema (6 tables)

All created in milestone 01. Most scripts open the database read-only.

- **claims** — Primary table, 227M+ rows (billing_npi, servicing_npi, hcpcs_code, claim_month, beneficiaries, claims, paid)
- **provider_summary** — Aggregated by provider (total_paid, num_codes, num_months)
- **hcpcs_summary** — Aggregated by procedure code (avg/stddev/median/p95 paid_per_claim)
- **provider_monthly** — Provider × month aggregates
- **provider_hcpcs** — Provider × code aggregates
- **billing_servicing_network** — Network edges for billing/servicing relationships

### Detection Methods (scripts/analyzers/)

Five analyzer classes inherit from `BaseAnalyzer` (`base_analyzer.py`). Each implements `execute(hypothesis, con)` → list of finding dicts.

| Analyzer | Categories | Methods |
|----------|-----------|---------|
| `StatisticalAnalyzer` | 1A-1F | Z-scores, IQR, GEV, Benford's Law |
| `TemporalAnalyzer` | 2A-2E | Sudden start/stop, seasonal anomalies, CUSUM breaks |
| `PeerAnalyzer` | 3A-3D | Peer group deviation, code-specialty mismatches |
| `NetworkAnalyzer` | 4A-4D | Circular billing, hub-and-spoke, middleman detection |
| `ConcentrationAnalyzer` | 5A-5C | Gini coefficient, Lorenz curves, Herfindahl index |

Additional detection in standalone scripts:
- **ML/DL** (milestone 06): Isolation Forest, Random Forest, XGBoost, DBSCAN, K-Means, LOF, Autoencoder, VAE, LSTM, Transformer
- **Domain Rules** (milestone 07): Impossible volumes, billing after deactivation, self-billing
- **Cross-Reference** (milestone 08): LEIE exclusion matching, NPPES validation

### Hypothesis System

Milestone 04 generates 1,000 structured hypotheses as JSON. Each hypothesis has: `id`, `category`, `subcategory`, `description`, `method`, `sql_template`, `parameters`, `financial_impact_method`. Milestone 05 tests Categories 1-5 in parallel using `ProcessPoolExecutor` (max_workers=10).

### Utilities (scripts/utils/)

- **db_utils.py** — `get_connection(read_only=True)` returns DuckDB connection. Write mode uses 16 threads / 96GB memory limit. `format_dollars()` for display formatting.
- **chart_utils.py** — HHS OpenData design system for matplotlib. Call `setup_hhs_style()` before plotting. Provides `create_horizontal_bar_chart()`, `create_line_chart()`, `create_scatter_chart()`, `dollar_formatter()`. All charts use `matplotlib.use('Agg')` (non-interactive).
- **leie_utils.py** — Downloads and parses OIG LEIE exclusion list.

### Output Organization

- `output/analysis/` — Final reports (executive_brief.md, fraud_patterns.md, action_plan_memo.md), priority queues (CSV), validation summaries. `INDEX.md` is the master navigation document.
- `output/charts/` — 43+ PNG visualizations in HHS OpenData style
- `output/hypotheses/` — JSON batches (batch_00 through batch_21) + feasibility matrix
- `output/findings/` — Scored findings by category (8GB+, gitignored, regenerable)
- `output/cards/` — Executive dashboard cards
- `output/qa/` — Data quality and ingest reports

### Large Files (gitignored)

- `medicaid-provider-spending.csv` (11GB) — source data, must be in project root
- `medicaid.duckdb` (30GB) — analytical database
- `claims.parquet` (2.9GB) — export
- `reference_data/nppes/` (10GB+) — NPI registry
- `output/findings/` (8GB+) — regenerable

### Key Dependencies

Python: `duckdb`, `scikit-learn`, `xgboost`, `torch`, `numpy`, `scipy`, `matplotlib`, `joblib`, `requests`

### Design Conventions

- Charts follow HHS OpenData design: amber (#F59F0A), dark (#221E1C), muted (#78716D), Inter font, 150 DPI, "HHS // OPENDATA" branding
- Dollar formatting uses `format_dollars()` from db_utils ($X.XB / $X.XM / $X.XK)
- Findings are standardized dicts with keys: `hypothesis_id`, `flagged_providers`, `total_impact`, `confidence`, `method_name`, `evidence`
- DuckDB connections default to read-only; only milestone 01 (ingestion) and 02 (enrichment) use write mode
