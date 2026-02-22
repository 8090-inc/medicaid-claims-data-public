# Executive Brief — Medicaid Fraud & Abuse Risk

## What matters most (plain language)

- We reviewed 617,503 providers and prioritized 500 high-risk leads.
- Quality-weighted potential overpayment (provider-level, standardized) is $325,993,532,034.
- Separate systemic exposure (state/code aggregates) totals $116,147,010,551 and is not comparable to provider-level impact.
- The top 10 leads account for $17,697,096,555 (5.0% of provider exposure).
- The top 100 leads account for $51,131,158,301 (14.4% of provider exposure).

**Exposure pipeline:** Raw statistical exposure ($377.5B) → standardized and capped ($355.8B) → quality-weighted ($326.0B). Each stage applies additional filters; see fraud_patterns.md and action_plan_memo.md for details.

**Impact caveat:** Exposure estimates are statistical ceilings reflecting the sum of per-code excess amounts. For individual providers, actual recoverable amounts cannot exceed total payments received. These figures should be interpreted as risk-ranking scores, not dollar-for-dollar recovery targets.

**Validation status:** Findings have not been validated against confirmed fraud cases. Precision and recall are unknown. The calibration report uses holdout-rate as a stability proxy, not an accuracy metric.

## Contrarian takeaways (high-entropy, decision-grade)

- Many of the largest signals are public or government-linked entities (11 of the top 20). That points to **policy or rate issues**, not just bad actors.
- 0% of top-500 weighted exposure comes from **state- or code-level aggregates** (STATE_/PAIR_ entries). That is a red flag for **rate design and authorization rules**, not just individual provider behavior.
- The single biggest paid code is T1019 (Personal care services, per 15 minutes, not for an inpatient) at $122,739,547,514 (~11% of total paid). Routine, high-volume services dominate exposure.
- We removed four unstable methods and eliminated ~4.9M low-quality flags, yet total estimated recoverable stayed almost flat. That means **most dollar risk is concentrated in a smaller, more defensible set**.
- 97% of the top-500 list triggers **3+ independent signals**. Those are the most defensible investigation targets.
- Some signals reflect **billing concentration and network patterns**, not unusual clinical behavior. These are best handled with **contracting and program integrity controls**, not medical review alone.

## Dominant signal families (provider count, top-500)

- Cost per claim outlier: 500 providers
- Other patterns: 457 providers
- Sudden shifts over time: 278 providers
- High volume per beneficiary: 273 providers
- Code concentration: 90 providers
