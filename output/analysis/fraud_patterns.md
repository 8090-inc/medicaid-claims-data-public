# Fraud, Waste, and Abuse Patterns in Medicaid Provider Spending

**HHS Provider Spending Dataset, January 2018 through December 2024**

---

## Overview

We analyzed $1,093,562,833,512 in Medicaid provider spending across 227,083,361 billing records from January 2018 through December 2024.
Provider-level pattern totals use a standardized impact formula: excess above peer median paid-per-claim, capped at total paid per provider. These are exposure ceilings, not guaranteed recoveries.
Provider-level standardized exposure totals $355,781,963,848. Systemic rate/code exposure totals $116,147,010,551 and is reported separately.
Patterns are not mutually exclusive. A provider flagged in one pattern may also appear in others. The $355.8B total is deduplicated at the provider level (max finding per provider), not at the pattern level.
Exposure estimates are statistical ceilings reflecting the sum of per-code excess amounts. For individual providers, actual recoverable amounts cannot exceed total payments received. These figures should be interpreted as risk-ranking scores, not dollar-for-dollar recovery targets.
Confidence tiers: High = flagged by 3+ independent detection methods; Medium = 2 methods; Low = 1 method.
December 2024 data may be incomplete in some states; late submissions can depress recent-month totals.

## Provider-Level Patterns (Standardized Impact)

| #  | Pattern                                | Providers | Estimated Impact |
| -- | -------------------------------------- | --------- | ---------------- |
| 1  | Home Health and Personal Care        |     20041 | $55.1B           |
| 2  | Middleman Billing Organizations      |      1915 | $36.5B           |
| 3  | Government Agencies as Outliers      |     20583 | $53.5B           |
| 4  | Providers That Cannot Exist          |       407 | $0.9B           |
| 5  | Billing Every Single Day             |        20 | $9.6B           |
| 6  | Sudden Starts and Stops              |      2433 | $91.8B           |
| 7  | Billing Networks and Circular Billing |       846 | $11.3B           |
| 9  | Upcoding and Impossible Volumes      |        36 | $3.4B           |
| 10  | Shared Beneficiary Counts            |        19 | $2.4B           |

---

## Systemic Rate/Code Patterns (Reported Separately)

| #  | Pattern                                | Providers | Estimated Exposure |
| -- | -------------------------------------- | --------- | ------------------ |
| 4  | Providers That Cannot Exist          |      2701 | $116.1B             |
| 8  | State-Level Spending Differences     |        20 | $77.5B             |
| 10  | Shared Beneficiary Counts            |         0 | $0.0B             |

---

## Methodology (Reproducible Mapping)

- **Home Health and Personal Care**: providers whose top paid code is T1019/T1020/S5125/S5126/S5130/S5131/S5170/S5175,
  or specialties containing 'Home Health', 'In Home', or 'Personal'.
- **Middleman Billing Organizations**: methods include hub_spoke, shared_servicing, pure_billing, captive_servicing,
  billing_only_provider, billing_fan_out.
- **Government Agencies as Outliers**: provider name contains Department/County/State/City/Public/University.
- **Providers That Cannot Exist**: identifiers are STATE_/PAIR_ or non-10-digit NPIs or missing names,
  plus post_deactivation_billing.
- **Billing Every Single Day**: method includes no_days_off.
- **Sudden Starts and Stops**: methods include sudden_appearance, sudden_disappearance, change_point(_cusum), yoy_growth.
- **Billing Networks and Circular Billing**: methods include circular_billing, network_density, ghost_network, new_network,
  hub_spoke, composite_network_plus_volume, reciprocal_billing.
- **State-Level Spending Differences**: systemic identifiers with state_spending_anomaly, state_peer_comparison,
  geographic_monopoly, or peer_concentration. Reported separately as systemic exposure.
- **Upcoding and Impossible Volumes**: methods include upcoding, impossible_volume, impossible_units_per_day, impossible_service_days, unbundling.
- **Shared Beneficiary Counts**: methods include shared_bene_count, shared_flagged_benes, bene_overlap_ring, bene_network_spread.

---

*All patterns described above come from statistical analysis of the HHS Provider Spending dataset. They are risk indicators, not findings of fraud. Each one requires further investigation before enforcement action.*