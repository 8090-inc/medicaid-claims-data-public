# Independent Audit Review: fraud_patterns.md

**Reviewer:** Waste, Fraud & Abuse Auditor
**Date:** February 2026
**Document Under Review:** `output/analysis/fraud_patterns.md`
**Scope:** Independent verification of claims, methodology, and dollar figures against pipeline source code, output data files, and intermediate analysis artifacts

---

## FINDING 1 (CRITICAL): "227 million claims" is factually wrong

**Report says (line 9):** "227 million claims from January 2018 through December 2024"

**What the data actually shows:**
- `data_profile.json` → `"total_rows": 227,083,361` (provider x code x month aggregated records)
- `data_profile.json` → `"total_claims": 18,825,564,012` (individual claim transactions)

The dataset has 227 million **rows**, not 227 million **claims**. Each row is a pre-aggregated billing record (one provider, one HCPCS code, one month). The actual number of individual claims is 18.8 billion — 83x larger. The CMS administrator report (line 17) correctly calls these "claims records," but fraud_patterns.md drops the qualifier. This distinction matters because it misleads the reader about the granularity of the data: the analysis never examines individual claims, only monthly aggregates per provider per code.

**Recommendation:** Change "227 million claims" to "227 million billing records" or "227 million provider-code-month combinations."

---

## FINDING 2 (CRITICAL): Estimated impact exceeds actual billing for top providers

The report's headline number is $377.5B in estimated recoverable payments — 34.5% of the $1.09T total spend. But the impact figures for individual providers are mathematically impossible:

| Provider | Total Actually Billed | Estimated Impact | Ratio |
|---|---|---|---|
| PUBLIC PARTNERSHIPS LLC | $7.2B | $45.8B | 6.4x |
| LA COUNTY DMH | $6.8B | $37.2B | 5.5x |
| TEMPUS UNLIMITED | $5.6B | $18.7B | 3.3x |
| FREEDOM CARE LLC | $3.0B | $9.1B | 3.0x |
| GUARDIANTRAC LLC | $2.7B | $6.4B | 2.4x |

These estimated impacts exceed actual billing by 2x to 6x. The maximum theoretically recoverable from any provider is 100% of what they were paid. You cannot recover $45.8B from an entity that received $7.2B.

**Root cause:** The impact calculation uses `(provider_rate - peer_median) × volume` applied per code, then takes the maximum single finding per provider during deduplication. When a provider is flagged across many codes, each code-level excess calculation can be large, and the per-code figures are not capped at actual total_paid. Additionally, some ML methods (DBSCAN, LOF) simply use total_paid as the impact figure, which is exposure rather than estimated excess.

**Implication for the report:** The $377.5B total is not a defensible estimate of recoverable dollars. It is a measure of statistical exposure that includes methodological over-counting. No auditor should cite these figures as potential recoveries without re-calculating impacts capped at actual provider payments.

---

## FINDING 3 (CRITICAL): Nearly a third of top-500 exposure is not provider-level fraud

The executive brief states: "29% of top-500 weighted exposure comes from state- or code-level aggregates (STATE_/PAIR_ entries)."

The top 20 risk queue includes:
- 2 `STATE_` entries (rate anomalies between states — e.g., STATE_NY_T1019 at $35.4B)
- 4 `PAIR_` entries (association rule code pairs — e.g., PAIR_99242_H2015 at $3.6B)

These are not fraud. They are programmatic rate differences and billing code associations. Each has only 1 detection method and medium confidence. Including them in the same ranked list as high-confidence, multi-method provider findings conflates systemic rate-setting issues with individual provider misconduct.

**The report partially acknowledges this** in Pattern 8 and the cross-cutting section, but the Summary table (lines 11-22) mixes pattern-level and provider-level totals without distinguishing them.

---

## FINDING 4 (SIGNIFICANT): Pattern 4 provider count and dollar figure are not reproducible

**Report says (line 17):** "Providers That Cannot Exist — 20 providers — $12.5B"

**What I can verify:**
- 3 providers flagged for `geographic_impossibility` (billing in 24, 29, and 30 states respectively)
- Their combined impact: $2.1B + $1.1B + $826M = $4.0B
- These 3 providers match the description in lines 69-73 perfectly

The report then says "Three such IDs" account for $4.0B (line 73), which matches. But the Summary table says 20 providers, $12.5B — where do the other 17 providers and $8.5B come from?

The `ghost_provider_indicators` method (which flags no-NPPES-record, short-duration, single-biller entities) flagged 556,521 providers at $543B — but it was **pruned** by calibration for having a 14.2% holdout rate vs 65.4% baseline. After pruning, only geographic_impossibility findings survive. There is no output file that confirms 20 providers or $12.5B for this pattern.

---

## FINDING 5 (SIGNIFICANT): Pattern dollar totals cannot be independently verified

The 10-pattern table (lines 11-22) assigns specific provider counts and dollar amounts to each pattern category. But:

1. These pattern categories are **editorial groupings** created by the author, not pipeline output categories
2. No output file categorizes findings by these 10 patterns
3. The pipeline uses 10 *analytical* categories (statistical, temporal, peer, network, etc.) which do not map 1:1 to the report's 10 *narrative* patterns
4. Verifying the totals would require manually classifying each of the 500 providers in risk_queue_top500.csv into these patterns — a subjective exercise

I can verify individual data points that the report quotes (the 81.3x rate, the 240,183 beneficiary match, the geographic impossibility details) but cannot verify the aggregate totals per pattern.

---

## FINDING 6 (SIGNIFICANT): December 2024 data is incomplete, creating false positives

Monthly spending from `data_profile.json`:
- November 2024: $12.87B, 183,955 rows
- December 2024: $4.20B, 63,394 rows (67% drop)

This strongly indicates that December 2024 data had not been fully submitted when the dataset was produced. Any provider flagged for "sudden stops" (Pattern 6) with a last billing month in late 2024 may be a data-completeness artifact, not an actual billing cessation. The report does not acknowledge this data limitation.

---

## FINDING 7 (SIGNIFICANT): Positive control validation was never completed

The pipeline includes a script (`14_validation_calibration.py`) designed to cross-validate findings against:
- SAM exclusion list (`reference_data/positive_controls/sam_exclusions.csv`)
- State licensure actions (`reference_data/positive_controls/licensure_actions.csv`)

The `reference_data/positive_controls/` directory is empty. Without known-fraud benchmarks, the analysis cannot report its precision (what fraction of flagged providers are genuinely problematic) or recall (what fraction of actual fraud it catches). The calibration report uses holdout-rate as a stability metric, which measures temporal persistence, not accuracy.

---

## FINDING 8 (MODERATE): Impact calculation methodology is inconsistent across methods

Different methods calculate "impact" in fundamentally different ways, yet the dollar figures are treated as comparable:

| Method Type | Impact Calculation | What It Measures |
|---|---|---|
| Z-score, Peer comparison | (provider_rate - peer_rate) × volume | Excess above median |
| Unbundling (8C) | total_paid × 20% | Flat percentage guess |
| Phantom billing (8E) | total_paid × 30% | Flat percentage guess |
| DBSCAN, LOF, LSTM | total_paid (entire amount) | Total exposure, not excess |
| Upcoding (8B) | excess_claims × 20% premium | Clinical excess estimate |
| State spending anomaly | (state_rate - national_median) × volume | Rate difference |

A provider with $1B in billing flagged by DBSCAN shows $1B impact. The same provider flagged by peer comparison might show $200M (the estimated excess). These are not the same thing but appear as equivalent numbers in the risk queue.

---

## FINDING 9 (MODERATE): Calibration baseline is not a precision metric

The calibration report uses a baseline holdout rate of 65.44% — meaning 65.44% of all providers (flagged or not) have billing activity in the 2023-2024 holdout window. A method that flags random providers would match this baseline. The pruning criteria (holdout rate < 0.5 × baseline, or z_delta < -0.5) filters out the worst methods, but a method with 65% holdout rate — matching random chance — would pass. The z_delta metric is more meaningful, but even it measures whether flagged providers maintain high z-scores over time, not whether they are actually engaged in fraud.

Four methods were correctly pruned: `ramp_up`, `seasonality_anomaly_low_cv`, `servicing_fan_in`, and `ghost_provider_indicators`. The ghost_provider_indicators pruning alone removed 556,521 findings and $543B in raw impact — a responsible decision.

---

## FINDING 10 (MODERATE): Confidence tier definitions are inconsistent across reports

The CMS administrator report (lines 70-72) defines confidence as:
- High: 3+ categories OR known fraud pattern OR z-score > 5
- Medium: 2 categories OR z-score 3-5
- Low: 1 category with z-score 2-3

The actual code (`09_financial_impact.py`) uses:
- High: `num_methods >= 3` OR `max_conf == 3 (high)`
- Medium: `num_methods >= 2` OR `max_conf == 2`
- Low: everything else

The z-score thresholds described in the CMS report are not implemented in the deduplication logic. The fraud_patterns.md does not define confidence levels at all, despite referencing "high-confidence findings" (line 141) and "560,889 low-confidence findings" (line 141).

---

## CLAIMS VERIFIED AS ACCURATE

The following specific claims in fraud_patterns.md were confirmed against source data:

| Claim | Source | Verdict |
|---|---|---|
| $1.09 trillion total spending | data_profile.json: $1,093,562,833,512.56 | Accurate |
| $377.5B estimated impact | current_analysis_pack.md: $377,470,731,798 | Accurate |
| Top 10 = 48.2% of top-500 pool | executive_brief.md: $168.1B / $349.2B = 48.17% | Accurate |
| Top 100 = 90.7% | executive_brief.md: $316.3B / $349.2B = 90.59% | Accurate |
| 74% of top-500 triggers 3+ signals | executive_brief.md | Confirmed |
| T1019/T1020 billed in 15-min increments | HCPCS reference file | Confirmed |
| 81.3x median rate (Pattern 2) | categories_9_and_10.json: pair rate $3,256.13 vs median $40.06 | Confirmed |
| Three provider IDs billing in 24-30 states | CMS report findings 22, 32, 43: 30, 29, 24 states | Confirmed |
| $4.0B from those three IDs ($826M-$2.1B each) | CMS report: $2.1B + $1.1B + $826.4M = $4.03B | Confirmed |
| No name/specialty/entity type for ghost providers | CMS report: entity type, active period all blank | Confirmed |
| Exactly 240,183 beneficiaries (shared count) | data_profile.json NPI 1396049987 | Confirmed |
| Exactly 231,057 beneficiaries (shared count) | data_profile.json NPI 1528338282 | Confirmed |
| NY T1019: $3,159/bene vs $1,526 median (2.1x) | CMS report finding 2, current_analysis_pack.md | Confirmed verbatim |
| 560,889 low-confidence findings at $0 impact | current_analysis_pack.md | Confirmed (though $0 is by design, not because they have no financial footprint) |

---

## OVERALL ASSESSMENT

The fraud_patterns.md report is **well-written and directionally correct** in identifying the major risk categories in Medicaid provider spending. Its strongest contribution is the cross-cutting section (lines 137-153), which correctly identifies that most of the dollar exposure is waste and poor program design rather than classic fraud.

However, the report has **three material accuracy problems** that undermine confidence in the numbers:

1. The "227 million claims" label misrepresents what the data contains
2. The estimated impact figures are inflated beyond what is mathematically recoverable
3. The per-pattern provider counts and dollar totals cannot be reproduced from the pipeline output

An auditor relying on this report should **trust the pattern descriptions and qualitative analysis** but should **not cite the dollar figures** without independent re-calculation capping impact at actual provider payments. The estimated recoverable of $377.5B should be understood as a statistical exposure ceiling, not a recovery target.

---

## RECOMMENDED ACTIONS

1. **Fix the "claims" terminology** — Change "227 million claims" to "227 million billing records"
2. **Cap impact at actual billing** — Re-run the impact calculation with `min(estimated_impact, total_paid)` per provider
3. **Separate provider findings from rate/code findings** — Split the risk queue into (a) provider-level findings and (b) systemic rate/code-pair findings
4. **Caveat December 2024** — Add a data limitation note about incomplete December 2024 data
5. **Complete positive control validation** — Populate `reference_data/positive_controls/` and re-run calibration
6. **Publish pattern categorization methodology** — Document how providers were classified into the 10 patterns so totals can be reproduced
7. **Standardize impact methodology** — Choose one impact formula (excess above peer median, capped at total_paid) and apply it consistently across all methods
