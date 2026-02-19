---

# ANALYSIS OF FRAUD, WASTE, AND ABUSE IN MEDICAID PROVIDER SPENDING

**HHS Provider Spending Dataset, January 2018 through December 2024**

**Prepared for:** Dr. Mehmet Oz, Administrator, Centers for Medicare & Medicaid Services

**Analyst:** Rohit Kelapure

**Date:** February 2026

---

## 1. Executive Summary

This analysis examined $1093.6B in Medicaid provider spending across 227,083,361 billing records spanning January 2018 through December 2024. The dataset covers 617,503 billing providers, 10,881 procedure codes, and 11,317,957,847 beneficiary-months of service.

Using 1,087 testable hypotheses across 10 analytical categories — statistical outlier detection, temporal anomaly analysis, peer comparison, network analysis, market concentration, classical machine learning, deep learning, domain-specific rules, cross-reference enrichment, and composite multi-signal scoring — this analysis identified:

- **10,913 high-confidence findings** representing an estimated $177.7B in potentially recoverable payments
- **19,379 medium-confidence findings** representing an estimated $59.1B
- **560,889 low-confidence findings** representing an estimated $118.1B

**Total estimated recoverable amount: $355.0B**
**Separate systemic exposure (state/code aggregates): $116.1B**

### Top 5 Findings

1. **LOS ANGELES COUNTY DEPARTMENT OF MENTAL HEALTH** (NPI 1699703827, CA): Estimated $5.5B in potentially improper payments. Flagged by 19 detection methods. Flagged by 7 categories: concentration, crossref, domain, ml, network, peer, statistical, 17 methods, 165 findings

2. **DEPARTMENT OF INTELLECTUAL AND DEVELOPMENTAL DISABILITIES, STATE OF TN** (NPI 1629436241, TN): Estimated $2.3B in potentially improper payments. Flagged by 12 detection methods. Flagged by 6 categories: crossref, domain, ml, network, peer, statistical, 11 methods, 43 findings

3. **ALABAMA DEPARTMENT OF MENTAL HEALTH AND MENTAL RETARDATION** (NPI 1982757688, AL): Estimated $2.1B in potentially improper payments. Flagged by 11 detection methods. Flagged by 5 categories: crossref, ml, network, peer, statistical, 9 methods, 38 findings

4. **GUARDIANTRAC. LLC** (NPI 1710176151, MI): Estimated $1.3B in potentially improper payments. Flagged by 15 detection methods. Flagged by 8 categories: concentration, crossref, domain, ml, network, peer, statistical, temporal, 12 methods, 100 findings

5. **DEPARTMENT OF INTELLECTUAL AND DEVELOPMENTAL DISABILITIES, STATE OF TN** (NPI 1356709976, TN): Estimated $1.4B in potentially improper payments. Flagged by 10 detection methods. Flagged by 6 categories: crossref, domain, ml, network, peer, statistical, 9 methods, 29 findings

![Top 20 Flagged Providers](charts/top20_flagged_providers.png)

## 2. Methodology

### Dataset

The analysis used the HHS Provider Spending dataset released by the U.S. Department of Health and Human Services. This dataset contains every fee-for-service claim, managed care encounter, and CHIP claim processed by state Medicaid agencies from January 2018 through December 2024. Each record contains the billing provider NPI, servicing provider NPI, HCPCS procedure code, claim month, number of unique beneficiaries, number of claims, and total amount paid.

### Reference Data

Provider identities (names, specialties, locations) were obtained from the NPPES National Provider registry. HCPCS procedure code descriptions were sourced from CMS reference files.

### Analytical Methods

1,087 structured hypotheses were generated and tested across 10 categories:

| Category | Hypotheses | Description |
|----------|-----------|-------------|
| 1. Statistical Outliers | 150 | Z-score, IQR, extreme value, and Benford's Law tests |
| 2. Temporal Anomalies | 120 | Month-over-month spikes, sudden appearance/disappearance, seasonality |
| 3. Peer Comparison | 130 | Rate, volume, and concentration compared to code/state/specialty peers |
| 4. Network Analysis | 120 | Hub-spoke, circular billing, ghost networks, pure billing entities |
| 5. Concentration | 80 | Market dominance, single-code specialists, geographic monopolies |
| 6. Machine Learning | 150 | Isolation Forest, DBSCAN, XGBoost, K-Means, LOF, Random Forest |
| 7. Deep Learning | 80 | Autoencoder, VAE, LSTM, Transformer attention anomalies |
| 8. Domain Rules | 100 | Impossible volumes, upcoding, unbundling, phantom billing |
| 9. Cross-Reference | 70 | Specialty mismatch, entity type, geographic impossibility |
| 10. Composite | Variable | Multi-signal providers flagged by 3+ categories |

**Note:** This includes 87 gap-analysis hypotheses beyond the base 1,000 taxonomy.

### Confidence Tiers

- **High:** Flagged by 3 or more analytical categories, or exhibits a known fraud pattern (impossible service volumes, circular billing), or has a z-score above 5.
- **Medium:** Flagged by 2 categories, or has a z-score between 3 and 5.
- **Low:** Flagged by 1 category with a z-score between 2 and 3.

## 3. High-Confidence Findings

### Finding 1: LOS ANGELES COUNTY DEPARTMENT OF MENTAL HEALTH

- **NPI:** 1699703827
- **Location:** LOS ANGELES, CA
- **Specialty:** Psychiatric Hospital
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-11
- **Total Medicaid Paid:** $6.8B
- **Total Claims:** 30,870,976
- **Total Beneficiaries:** 10,549,232

**Anomaly Description:** Flagged by 7 categories: concentration, crossref, domain, ml, network, peer, statistical, 17 methods, 165 findings

**Detection Methods:** Flagged by 19 of 10 analytical categories: provider_share_per_code, billing_fan_out, zscore_paid_per_claim, iqr_outlier, volume_vs_median, isolation_forest, lof, composite_multi_signal, impossible_em_visits_day, paid_per_claim_vs_median, new_network_high_paid, composite_network_plus_volume, duplicate_billing, low_entropy_billing, ensemble_agreement, no_days_off, gev_extreme_value, random_forest, dbscan

**Estimated Recoverable Amount:** $5.5B

![Monthly Billing](charts/finding_F001_timeseries.png)

---

### Finding 2: DEPARTMENT OF INTELLECTUAL AND DEVELOPMENTAL DISABILITIES, STATE OF TN

- **NPI:** 1629436241
- **Location:** NASHVILLE, TN
- **Specialty:** Nursing Home
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-06
- **Total Medicaid Paid:** $2.6B
- **Total Claims:** 16,349,155
- **Total Beneficiaries:** 1,174,610

**Anomaly Description:** Flagged by 6 categories: crossref, domain, ml, network, peer, statistical, 11 methods, 43 findings

**Detection Methods:** Flagged by 12 of 10 analytical categories: gev_extreme_value, claims_per_bene_vs_median, volume_vs_median, paid_per_claim_vs_median, new_network_high_paid, high_risk_category, low_entropy_billing, dbscan, billing_only_provider, lof, iqr_outlier, composite_multi_signal

**Estimated Recoverable Amount:** $2.3B

![Monthly Billing](charts/finding_F002_timeseries.png)

---

### Finding 3: ALABAMA DEPARTMENT OF MENTAL HEALTH AND MENTAL RETARDATION

- **NPI:** 1982757688
- **Location:** MONTGOMERY, AL
- **Specialty:** Community/Behavioral Health
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $2.3B
- **Total Claims:** 1,950,098
- **Total Beneficiaries:** 594,985

**Anomaly Description:** Flagged by 5 categories: crossref, ml, network, peer, statistical, 9 methods, 38 findings

**Detection Methods:** Flagged by 11 of 10 analytical categories: gev_extreme_value, paid_per_claim_vs_median, volume_vs_median, new_network_high_paid, new_relationship_high_volume, low_entropy_billing, dbscan, lof, iqr_outlier, address_cluster_flagged, composite_multi_signal

**Estimated Recoverable Amount:** $2.1B

![Monthly Billing](charts/finding_F003_timeseries.png)

---

### Finding 4: GUARDIANTRAC. LLC

- **NPI:** 1710176151
- **Location:** STURGIS, MI
- **Specialty:** Supports Brokerage
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $2.7B
- **Total Claims:** 35,557,539
- **Total Beneficiaries:** 2,441,087

**Anomaly Description:** Flagged by 8 categories: concentration, crossref, domain, ml, network, peer, statistical, temporal, 12 methods, 100 findings

**Detection Methods:** Flagged by 15 of 10 analytical categories: gev_extreme_value, provider_share_per_code, claims_per_bene_vs_median, composite_temporal_plus_statistical, volume_vs_median, paid_per_claim_vs_median, composite_growth_plus_concentration, composite_network_plus_volume, high_risk_category, dbscan, lof, iqr_outlier, change_point_cusum, composite_multi_signal, no_days_off

**Estimated Recoverable Amount:** $1.3B

![Monthly Billing](charts/finding_F004_timeseries.png)

---

### Finding 5: DEPARTMENT OF INTELLECTUAL AND DEVELOPMENTAL DISABILITIES, STATE OF TN

- **NPI:** 1356709976
- **Location:** NASHVILLE, TN
- **Specialty:** Nursing Home
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-06
- **Total Medicaid Paid:** $1.5B
- **Total Claims:** 5,287,026
- **Total Beneficiaries:** 389,567

**Anomaly Description:** Flagged by 6 categories: crossref, domain, ml, network, peer, statistical, 9 methods, 29 findings

**Detection Methods:** Flagged by 10 of 10 analytical categories: gev_extreme_value, claims_per_bene_vs_median, volume_vs_median, paid_per_claim_vs_median, high_risk_category, low_entropy_billing, dbscan, billing_only_provider, iqr_outlier, composite_multi_signal

**Estimated Recoverable Amount:** $1.4B

![Monthly Billing](charts/finding_F005_timeseries.png)

---

### Finding 6: CITY OF CHICAGO

- **NPI:** 1376554592
- **Location:** CHICAGO, IL
- **Specialty:** Emergency Medical Technician
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $1.2B
- **Total Claims:** 1,593,649
- **Total Beneficiaries:** 1,193,380

**Anomaly Description:** temporal_plus_statistical: temporal+statistical signals, total categories=5

**Detection Methods:** Flagged by 9 of 10 analytical categories: gev_extreme_value, covid_comparison, kickback_premium, yoy_growth, low_entropy_billing, dbscan, iqr_outlier, change_point_cusum, composite_temporal_plus_statistical

**Estimated Recoverable Amount:** $1.2B

![Monthly Billing](charts/finding_F006_timeseries.png)

---

### Finding 7: DEPARTMENT OF DEVELOPMENTAL SERVICES

- **NPI:** 1750504064
- **Location:** SOUTHBRIDGE, MA
- **Specialty:** Case Management Agency
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-10
- **Total Medicaid Paid:** $1.3B
- **Total Claims:** 1,662,383
- **Total Beneficiaries:** 224,187

**Anomaly Description:** Flagged by 7 categories: concentration, crossref, domain, ml, network, peer, statistical, 11 methods, 52 findings

**Detection Methods:** Flagged by 13 of 10 analytical categories: gev_extreme_value, claims_per_bene_vs_median, composite_multi_signal, volume_vs_median, paid_per_claim_vs_median, kickback_premium, composite_network_plus_volume, code_concentration_per_provider, high_risk_category, low_entropy_billing, dbscan, iqr_outlier, zscore_claims_per_bene

**Estimated Recoverable Amount:** $1.1B

![Monthly Billing](charts/finding_F007_timeseries.png)

---

### Finding 8: MAINS'L FLORIDA, INC.

- **NPI:** 1932341898
- **Location:** BROOKLYN PARK, MN
- **Specialty:** Home Health Agency
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $996.8M
- **Total Claims:** 306,131
- **Total Beneficiaries:** 283,973

**Anomaly Description:** Kickback premium: pair rate=$3,256.13 vs median=$40.06 (81.3x), servicing=1932341898

**Detection Methods:** Flagged by 7 of 10 analytical categories: gev_extreme_value, provider_share_per_code, month_over_month_spike, kickback_premium, code_concentration_per_provider, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $973.2M

![Monthly Billing](charts/finding_F008_timeseries.png)

---

### Finding 9: DEPARTMENT OF HEALTH AND SENIOR SERVICES

- **NPI:** 1326168840
- **Location:** TRENTON, NJ
- **Specialty:** Specialist
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $1.1B
- **Total Claims:** 3,312,341
- **Total Beneficiaries:** 621,736

**Anomaly Description:** network_plus_volume: network+concentration signals, total categories=5

**Detection Methods:** Flagged by 7 of 10 analytical categories: gev_extreme_value, provider_share_per_code, kickback_premium, composite_network_plus_volume, low_entropy_billing, dbscan, iqr_outlier

**Estimated Recoverable Amount:** $973.8M

![Monthly Billing](charts/finding_F009_timeseries.png)

---

### Finding 10: NEW PARTNERS, INC

- **NPI:** 1083783013
- **Location:** NEW YORK, NY
- **Specialty:** Hospice
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $1.1B
- **Total Claims:** 5,875,713
- **Total Beneficiaries:** 264,344

**Anomaly Description:** Flagged by 7 categories: crossref, domain, ml, network, peer, statistical, temporal, 9 methods, 47 findings

**Detection Methods:** Flagged by 11 of 10 analytical categories: gev_extreme_value, volume_vs_median, kickback_premium, yoy_growth, high_risk_category, low_entropy_billing, dbscan, iqr_outlier, composite_temporal_plus_statistical, composite_multi_signal, no_days_off

**Estimated Recoverable Amount:** $911.6M

![Monthly Billing](charts/finding_F010_timeseries.png)

---

### Finding 11: COMMONWEALTH OF MASSACHUSETS

- **NPI:** 1518096411
- **Location:** BEVERLY, MA
- **Specialty:** Case Management Agency
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-10
- **Total Medicaid Paid:** $1.1B
- **Total Claims:** 1,557,105
- **Total Beneficiaries:** 197,206

**Anomaly Description:** Transportation: rate_z=-0.3, cpb_ratio=23.6x, total=$31.4M

**Detection Methods:** Flagged by 12 of 10 analytical categories: gev_extreme_value, claims_per_bene_vs_median, volume_vs_median, paid_per_claim_vs_median, kickback_premium, composite_network_plus_volume, code_concentration_per_provider, high_risk_category, low_entropy_billing, dbscan, iqr_outlier, zscore_claims_per_bene

**Estimated Recoverable Amount:** $887.9M

![Monthly Billing](charts/finding_F011_timeseries.png)

---

### Finding 12: COMMONWEALTH OF MASS-DDS

- **NPI:** 1134250475
- **Location:** HYDE PARK, MA
- **Specialty:** Case Management Agency
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-10
- **Total Medicaid Paid:** $1.1B
- **Total Claims:** 1,432,892
- **Total Beneficiaries:** 259,050

**Anomaly Description:** Transportation: rate_z=-0.3, cpb_ratio=24.9x, total=$22.6M

**Detection Methods:** Flagged by 10 of 10 analytical categories: gev_extreme_value, claims_per_bene_vs_median, volume_vs_median, paid_per_claim_vs_median, kickback_premium, high_risk_category, low_entropy_billing, dbscan, iqr_outlier, zscore_claims_per_bene

**Estimated Recoverable Amount:** $862.4M

![Monthly Billing](charts/finding_F012_timeseries.png)

---

### Finding 13: COMMUNITY ASSISTANCE RESOURCES & EXTENDED SERVICES INC

- **NPI:** 1396049987
- **Location:** NEW YORK, NY
- **Specialty:** Day Training/Habilitation
- **Entity Type:** Organization
- **Active Period:** 2019-10 through 2024-12
- **Total Medicaid Paid:** $1.0B
- **Total Claims:** 2,757,160
- **Total Beneficiaries:** 240,183

**Anomaly Description:** Matched bene count (240183): 1396049987 ($1.0B) and 1750705364 ($12.4M)

**Detection Methods:** Flagged by 12 of 10 analytical categories: gev_extreme_value, volume_vs_median, paid_per_claim_vs_median, covid_comparison, kickback_premium, yoy_growth, shared_bene_count, random_forest, lof, iqr_outlier, change_point_cusum, zscore_claims_per_bene

**Estimated Recoverable Amount:** $803.0M

![Monthly Billing](charts/finding_F013_timeseries.png)

---

### Finding 14: TENNESSEE DEPARTMENT OF CHILDREN'S SERVICES

- **NPI:** 1124494059
- **Location:** NASHVILLE, TN
- **Specialty:** Nursing Home
- **Entity Type:** Organization
- **Active Period:** 2019-07 through 2024-11
- **Total Medicaid Paid:** $781.0M
- **Total Claims:** 910,831
- **Total Beneficiaries:** 877,965

**Anomaly Description:** 

**Detection Methods:** Flagged by 6 of 10 analytical categories: gev_extreme_value, month_over_month_spike, covid_comparison, yoy_growth, code_concentration_per_provider, iqr_outlier

**Estimated Recoverable Amount:** $765.1M

![Monthly Billing](charts/finding_F014_timeseries.png)

---

### Finding 15: COMMONWEALTH OF MASSACHUSETTS-DDS

- **NPI:** 1245354000
- **Location:** HYANNIS, MA
- **Specialty:** Case Management Agency
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-10
- **Total Medicaid Paid:** $881.9M
- **Total Claims:** 781,227
- **Total Beneficiaries:** 138,263

**Anomaly Description:** Transportation: rate_z=-0.3, cpb_ratio=20.4x, total=$13.2M

**Detection Methods:** Flagged by 7 of 10 analytical categories: gev_extreme_value, claims_per_bene_vs_median, volume_vs_median, paid_per_claim_vs_median, code_concentration_per_provider, high_risk_category, iqr_outlier

**Estimated Recoverable Amount:** $753.7M

![Monthly Billing](charts/finding_F015_timeseries.png)

---

### Finding 16: CONSUMER DIRECT CARE NETWORK VIRGINIA

- **NPI:** 1538649983
- **Location:** MISSOULA, MT
- **Specialty:** Case Manager/Care Coordinator
- **Entity Type:** Organization
- **Active Period:** 2018-07 through 2024-12
- **Total Medicaid Paid:** $2.1B
- **Total Claims:** 22,162,533
- **Total Beneficiaries:** 1,069,174

**Anomaly Description:** Flagged by 5 categories: concentration, ml, network, statistical, temporal, 9 methods, 98 findings

**Detection Methods:** Flagged by 14 of 10 analytical categories: gev_extreme_value, provider_share_per_code, month_over_month_spike, kickback_premium, address_cluster_flagged, yoy_growth, composite_network_plus_volume, composite_growth_plus_concentration, dbscan, lof, iqr_outlier, change_point_cusum, composite_multi_signal, composite_temporal_plus_statistical

**Estimated Recoverable Amount:** $674.8M

![Monthly Billing](charts/finding_F016_timeseries.png)

---

### Finding 17: COUNTY OF ORANGE

- **NPI:** 1104963347
- **Location:** SANTA ANA, CA
- **Specialty:** Other
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $806.7M
- **Total Claims:** 4,933,775
- **Total Beneficiaries:** 1,554,907

**Anomaly Description:** ed_visit: 99285 ratio=100.0% vs peer median=16.7%, 101 high-level claims of 101 total

**Detection Methods:** Flagged by 6 of 10 analytical categories: gev_extreme_value, paid_per_claim_vs_median, volume_vs_median, upcoding, zscore_paid_per_claim, iqr_outlier

**Estimated Recoverable Amount:** $667.2M

![Monthly Billing](charts/finding_F017_timeseries.png)

---

### Finding 18: COUNTY OF SACRAMENTO

- **NPI:** 1043386659
- **Location:** SACRAMENTO, CA
- **Specialty:** Case Manager/Care Coordinator
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-11
- **Total Medicaid Paid:** $903.1M
- **Total Claims:** 4,320,082
- **Total Beneficiaries:** 1,851,576

**Anomaly Description:** 

**Detection Methods:** Flagged by 6 of 10 analytical categories: gev_extreme_value, volume_vs_median, paid_per_claim_vs_median, zscore_paid_per_claim, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $641.9M

![Monthly Billing](charts/finding_F018_timeseries.png)

---

### Finding 19: PUBLIC PARTNERSHIPS-COLORADO, INC.

- **NPI:** 1124304621
- **Location:** BOSTON, MA
- **Specialty:** Supports Brokerage
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $887.5M
- **Total Claims:** 5,599,208
- **Total Beneficiaries:** 465,275

**Anomaly Description:** Home Health: rate_z=-0.3, cpb_ratio=3.0x, total=$887.5M

**Detection Methods:** Flagged by 6 of 10 analytical categories: gev_extreme_value, claims_per_bene_vs_median, volume_vs_median, code_concentration_per_provider, high_risk_category, iqr_outlier

**Estimated Recoverable Amount:** $625.6M

![Monthly Billing](charts/finding_F019_timeseries.png)

---

### Finding 20: YOUTH VILLAGES, INC.

- **NPI:** 1306875695
- **Location:** BARTLETT, TN
- **Specialty:** Psychiatric Residential
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-11
- **Total Medicaid Paid:** $615.3M
- **Total Claims:** 790,946
- **Total Beneficiaries:** 215,938

**Anomaly Description:** 

**Detection Methods:** Flagged by 6 of 10 analytical categories: gev_extreme_value, paid_per_claim_vs_median, covid_comparison, yoy_growth, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $595.8M

![Monthly Billing](charts/finding_F020_timeseries.png)

---

### Finding 21: ACUMEN FISCAL AGENT LLC

- **NPI:** 1720145378
- **Location:** MESA, AZ
- **Specialty:** Case Manager/Care Coordinator
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $1.1B
- **Total Claims:** 10,544,174
- **Total Beneficiaries:** 655,257

**Anomaly Description:** 

**Detection Methods:** Flagged by 5 of 10 analytical categories: gev_extreme_value, claims_per_bene_vs_median, volume_vs_median, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $567.2M

---

### Finding 22: AOC TX, LLC

- **NPI:** 1952346876
- **Location:** SHERMAN, TX
- **Specialty:** Case Management Agency
- **Entity Type:** Organization
- **Active Period:** 2019-07 through 2024-12
- **Total Medicaid Paid:** $708.5M
- **Total Claims:** 1,626,136
- **Total Beneficiaries:** 116,046

**Anomaly Description:** 

**Detection Methods:** Flagged by 8 of 10 analytical categories: gev_extreme_value, volume_vs_median, covid_comparison, paid_per_claim_vs_median, month_over_month_spike, yoy_growth, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $546.0M

---

### Finding 23: NV ST DV MH DS DESERT DEV CENTER

- **NPI:** 1780045542
- **Location:** LAS VEGAS, NV
- **Specialty:** Respite In-Home
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $545.4M
- **Total Claims:** 702,749
- **Total Beneficiaries:** 233,607

**Anomaly Description:** Address cluster: 6 NPIs at 1391 S JONES BLVD, LAS VEGAS, NV, combined=$703.1M

**Detection Methods:** Flagged by 7 of 10 analytical categories: gev_extreme_value, claims_per_bene_vs_median, paid_per_claim_vs_median, volume_vs_median, billing_only_provider, iqr_outlier, address_cluster_flagged

**Estimated Recoverable Amount:** $512.6M

---

### Finding 24: CENTRIA HEALTHCARE LLC

- **NPI:** 1053641498
- **Location:** FARMINGTON HILLS, MI
- **Specialty:** Other
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $590.6M
- **Total Claims:** 2,755,271
- **Total Beneficiaries:** 357,738

**Anomaly Description:** 

**Detection Methods:** Flagged by 4 of 10 analytical categories: gev_extreme_value, iqr_outlier, paid_per_claim_vs_median, new_network_high_paid

**Estimated Recoverable Amount:** $500.4M

---

### Finding 25: BANCROFT, A NEW JERSEY NONPROFIT CORPORATION

- **NPI:** 1720121106
- **Location:** CHERRY HILL, NJ
- **Specialty:** Other
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $560.4M
- **Total Claims:** 1,802,919
- **Total Beneficiaries:** 115,599

**Anomaly Description:** Behavioral Health: rate_z=0.0, cpb_ratio=4.1x, total=$417.9M

**Detection Methods:** Flagged by 7 of 10 analytical categories: gev_extreme_value, claims_per_bene_vs_median, volume_vs_median, paid_per_claim_vs_median, high_risk_category, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $515.0M

---

### Finding 26: CITY & COUNTY OF SAN FRANCISCO

- **NPI:** 1417099789
- **Location:** SAN FRANCISCO, CA
- **Specialty:** Supports Brokerage
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $1.3B
- **Total Claims:** 6,184,815
- **Total Beneficiaries:** 1,302,440

**Anomaly Description:** New relationship: $4.8M first month (2018-01), servicing=1508933862

**Detection Methods:** Flagged by 8 of 10 analytical categories: gev_extreme_value, paid_per_claim_vs_median, volume_vs_median, new_relationship_high_volume, zscore_paid_per_claim, dbscan, iqr_outlier, zscore_claims_per_bene

**Estimated Recoverable Amount:** $502.4M

---

### Finding 27: ZOLL SERVICES LLC

- **NPI:** 1164535274
- **Location:** PITTSBURGH, PA
- **Specialty:** DME Supplier
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $504.0M
- **Total Claims:** 477,988
- **Total Beneficiaries:** 391,060

**Anomaly Description:** 

**Detection Methods:** Flagged by 5 of 10 analytical categories: gev_extreme_value, provider_share_per_code, code_concentration_per_provider, hhi_per_code, iqr_outlier

**Estimated Recoverable Amount:** $486.3M

---

### Finding 28: MA-DEPARTMENT OF SOCIAL SERVICES-REHAB

- **NPI:** 1073730347
- **Location:** BOSTON, MA
- **Specialty:** Nursing Home
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-08
- **Total Medicaid Paid:** $490.7M
- **Total Claims:** 225,775
- **Total Beneficiaries:** 106,190

**Anomaly Description:** Matched bene count (106190): 1073730347 ($490.7M) and 1326007915 ($5.8M)

**Detection Methods:** Flagged by 4 of 10 analytical categories: gev_extreme_value, iqr_outlier, code_concentration_per_provider, shared_bene_count

**Estimated Recoverable Amount:** $487.1M

---

### Finding 29: NATERA, INC.

- **NPI:** 1558672279
- **Location:** SAN CARLOS, CA
- **Specialty:** Clinical Lab
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $641.5M
- **Total Claims:** 7,257,656
- **Total Beneficiaries:** 6,431,366

**Anomaly Description:** 

**Detection Methods:** Flagged by 6 of 10 analytical categories: gev_extreme_value, provider_share_per_code, reciprocal_billing, hhi_per_code, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $477.0M

---

### Finding 30: SHIELD CALIFORNIA HEALTH CARE CENTER INC

- **NPI:** 1881708899
- **Location:** VALENCIA, CA
- **Specialty:** Pharmacy
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $522.6M
- **Total Claims:** 10,338,535
- **Total Beneficiaries:** 10,087,772

**Anomaly Description:** 

**Detection Methods:** Flagged by 3 of 10 analytical categories: gev_extreme_value, iqr_outlier, reciprocal_billing

**Estimated Recoverable Amount:** $473.1M

---

### Finding 31: NATIONWIDE CHILDREN'S HOSPITAL

- **NPI:** 1134152986
- **Location:** COLUMBUS, OH
- **Specialty:** Dental Clinic
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $777.5M
- **Total Claims:** 11,019,261
- **Total Beneficiaries:** 8,541,239

**Anomaly Description:** IsolationForest high_volume: anomaly_score=0.752, top_features=[num_servicing_npis, max_single_month_paid, total_paid]

**Detection Methods:** Flagged by 9 of 10 analytical categories: gev_extreme_value, billing_fan_out, volume_vs_median, paid_per_claim_vs_median, isolation_forest, address_cluster_flagged, iqr_outlier, change_point_cusum, kmeans

**Estimated Recoverable Amount:** $447.0M

---

### Finding 32: DAP HEALTH, INC.

- **NPI:** 1275849283
- **Location:** DESERT HOT SPRINGS, CA
- **Specialty:** Family Medicine
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $463.0M
- **Total Claims:** 1,868,258
- **Total Beneficiaries:** 905,720

**Anomaly Description:** 

**Detection Methods:** Flagged by 5 of 10 analytical categories: gev_extreme_value, volume_vs_median, reciprocal_billing, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $445.4M

---

### Finding 33: RECTOR & VISITORS OF THE UNIVERSITY OF VIRGINIA

- **NPI:** 1780630608
- **Location:** CHARLOTTESVILLE, VA
- **Specialty:** Clinical Lab
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $500.5M
- **Total Claims:** 7,181,828
- **Total Beneficiaries:** 5,089,874

**Anomaly Description:** 

**Detection Methods:** Flagged by 7 of 10 analytical categories: gev_extreme_value, volume_vs_median, paid_per_claim_vs_median, hhi_per_code, zscore_paid_per_claim, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $439.7M

---

### Finding 34: ARION CARE SOLUTIONS, LLC

- **NPI:** 1932721834
- **Location:** CHANDLER, AZ
- **Specialty:** Other
- **Entity Type:** Organization
- **Active Period:** 2019-07 through 2024-12
- **Total Medicaid Paid:** $606.7M
- **Total Claims:** 5,766,334
- **Total Beneficiaries:** 393,994

**Anomaly Description:** 

**Detection Methods:** Flagged by 4 of 10 analytical categories: gev_extreme_value, iqr_outlier, change_point_cusum, yoy_growth

**Estimated Recoverable Amount:** $440.7M

---

### Finding 35: PHOENIX CHILDREN'S HOSPITAL

- **NPI:** 1760480503
- **Location:** PHOENIX, AZ
- **Specialty:** Other
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $555.7M
- **Total Claims:** 4,185,462
- **Total Beneficiaries:** 3,641,942

**Anomaly Description:** Address cluster: 54 NPIs at 1919 E THOMAS RD, PHOENIX, AZ, combined=$721.3M

**Detection Methods:** Flagged by 5 of 10 analytical categories: gev_extreme_value, volume_vs_median, hhi_per_code, iqr_outlier, address_cluster_flagged

**Estimated Recoverable Amount:** $435.3M

---

### Finding 36: UNIVERSITY OF KENTUCKY

- **NPI:** 1518911338
- **Location:** LEXINGTON, KY
- **Specialty:** Ambulance
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $716.4M
- **Total Claims:** 8,817,197
- **Total Beneficiaries:** 6,877,120

**Anomaly Description:** Address cluster: 19 NPIs at 800 ROSE ST, LEXINGTON, KY, combined=$720.2M

**Detection Methods:** Flagged by 5 of 10 analytical categories: gev_extreme_value, volume_vs_median, pharmacy_rate_outlier, iqr_outlier, address_cluster_flagged

**Estimated Recoverable Amount:** $427.3M

---

### Finding 37: CONSUMER DIRECTED SERVICES IN TEXAS, INC.

- **NPI:** 1801027404
- **Location:** SAN ANTONIO, TX
- **Specialty:** Home Health Agency
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $624.8M
- **Total Claims:** 3,406,847
- **Total Beneficiaries:** 599,363

**Anomaly Description:** 

**Detection Methods:** Flagged by 7 of 10 analytical categories: gev_extreme_value, provider_share_per_code, volume_vs_median, yoy_growth, hhi_per_code, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $415.5M

---

### Finding 38: SCOTTISH RITE CHILDREN'S MEDICAL CENTER

- **NPI:** 1184779332
- **Location:** ATLANTA, GA
- **Specialty:** Other
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $493.4M
- **Total Claims:** 3,556,445
- **Total Beneficiaries:** 3,026,103

**Anomaly Description:** New relationship: $4.5M first month (2018-01), servicing=1922178789

**Detection Methods:** Flagged by 8 of 10 analytical categories: gev_extreme_value, paid_per_claim_vs_median, volume_vs_median, captive_referral, new_relationship_high_volume, hhi_per_code, upcoding, iqr_outlier

**Estimated Recoverable Amount:** $387.9M

---

### Finding 39: COUNTY OF SANTA CLARA

- **NPI:** 1528263910
- **Location:** SAN JOSE, CA
- **Specialty:** Mental Health Center
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-10
- **Total Medicaid Paid:** $1.7B
- **Total Claims:** 4,656,205
- **Total Beneficiaries:** 1,617,142

**Anomaly Description:** Flagged by 6 categories: crossref, ml, network, peer, statistical, temporal, 12 methods, 61 findings

**Detection Methods:** Flagged by 14 of 10 analytical categories: gev_extreme_value, composite_temporal_plus_statistical, composite_multi_signal, paid_per_claim_vs_median, volume_vs_median, new_network_high_paid, new_relationship_high_volume, low_entropy_billing, zscore_paid_per_claim, dbscan, iqr_outlier, change_point_cusum, zscore_claims_per_bene, no_days_off

**Estimated Recoverable Amount:** $387.8M

---

### Finding 40: CHILDREN'S HOSPITAL MEDICAL CENTER OF AKRON

- **NPI:** 1861506560
- **Location:** AKRON, OH
- **Specialty:** Other
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $556.6M
- **Total Claims:** 6,634,271
- **Total Beneficiaries:** 5,639,593

**Anomaly Description:** Address cluster: 24 NPIs at 1 PERKINS SQ, AKRON, OH, combined=$649.0M

**Detection Methods:** Flagged by 9 of 10 analytical categories: gev_extreme_value, billing_fan_out, volume_vs_median, paid_per_claim_vs_median, address_cluster_flagged, yoy_growth, zscore_paid_per_claim, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $378.7M

---

### Finding 41: WALL RESIDENCES, LLC

- **NPI:** 1063436723
- **Location:** FLOYD, VA
- **Specialty:** ID/MR Community
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-11
- **Total Medicaid Paid:** $481.6M
- **Total Claims:** 89,469
- **Total Beneficiaries:** 69,770

**Anomaly Description:** Behavioral Health: rate_z=7.4, cpb_ratio=0.2x, total=$184.5M

**Detection Methods:** Flagged by 7 of 10 analytical categories: gev_extreme_value, paid_per_claim_vs_median, shared_bene_count, random_forest, high_risk_category, zscore_paid_per_claim, iqr_outlier

**Estimated Recoverable Amount:** $375.7M

---

### Finding 42: TEXAS DEPARTMENT OF STATE HEALTH

- **NPI:** 1114931391
- **Location:** AUSTIN, TX
- **Specialty:** Clinical Lab
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $381.9M
- **Total Claims:** 2,710,132
- **Total Beneficiaries:** 2,323,406

**Anomaly Description:** 

**Detection Methods:** Flagged by 10 of 10 analytical categories: gev_extreme_value, provider_share_per_code, month_over_month_spike, covid_comparison, yoy_growth, code_concentration_per_provider, hhi_per_code, december_spike, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $369.8M

---

### Finding 43: STATE OF MISSOURI

- **NPI:** 1447886288
- **Location:** JEFFERSON CITY, MO
- **Specialty:** Other
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $493.6M
- **Total Claims:** 3,328,210
- **Total Beneficiaries:** 845,819

**Anomaly Description:** Address cluster: 5 NPIs at 1706 E ELM ST, JEFFERSON CITY, MO, combined=$857.0M

**Detection Methods:** Flagged by 7 of 10 analytical categories: gev_extreme_value, paid_per_claim_vs_median, address_cluster_flagged, zscore_paid_per_claim, billing_only_provider, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $363.2M

---

### Finding 44: COMMONWEALTH OF MASSACHUSETTS-DDS

- **NPI:** 1023140498
- **Location:** S WEYMOUTH, MA
- **Specialty:** Case Management Agency
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-10
- **Total Medicaid Paid:** $447.5M
- **Total Claims:** 578,640
- **Total Beneficiaries:** 121,972

**Anomaly Description:** 

**Detection Methods:** Flagged by 5 of 10 analytical categories: gev_extreme_value, claims_per_bene_vs_median, paid_per_claim_vs_median, volume_vs_median, iqr_outlier

**Estimated Recoverable Amount:** $352.6M

---

### Finding 45: COMMONWEALTH OF MASSACHUSETTS

- **NPI:** 1942339825
- **Location:** HAVERHILL, MA
- **Specialty:** Case Management Agency
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-10
- **Total Medicaid Paid:** $444.0M
- **Total Claims:** 584,358
- **Total Beneficiaries:** 163,989

**Anomaly Description:** 

**Detection Methods:** Flagged by 4 of 10 analytical categories: gev_extreme_value, iqr_outlier, claims_per_bene_vs_median, volume_vs_median

**Estimated Recoverable Amount:** $348.1M

---

### Finding 46: DEPARTMENT OF DEVELOPMENTAL SERVICES

- **NPI:** 1528281532
- **Location:** SPRINGFIELD, MA
- **Specialty:** Case Management Agency
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-10
- **Total Medicaid Paid:** $465.4M
- **Total Claims:** 750,654
- **Total Beneficiaries:** 157,791

**Anomaly Description:** Matched bene count (157791): 1528281532 ($465.4M) and 1609143452 ($3.3M)

**Detection Methods:** Flagged by 6 of 10 analytical categories: gev_extreme_value, claims_per_bene_vs_median, paid_per_claim_vs_median, volume_vs_median, shared_bene_count, iqr_outlier

**Estimated Recoverable Amount:** $342.2M

---

### Finding 47: COMMUNITY ACCESS UNLIMITED

- **NPI:** 1821456526
- **Location:** ELIZABETH, NJ
- **Specialty:** Supports Brokerage
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $355.7M
- **Total Claims:** 855,357
- **Total Beneficiaries:** 93,205

**Anomaly Description:** Behavioral Health: rate_z=0.1, cpb_ratio=4.3x, total=$321.8M

**Detection Methods:** Flagged by 6 of 10 analytical categories: gev_extreme_value, claims_per_bene_vs_median, volume_vs_median, high_risk_category, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $330.4M

---

### Finding 48: COMMONWEALTH OF MASS-DDS

- **NPI:** 1982735643
- **Location:** WALPOLE, MA
- **Specialty:** Case Management Agency
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-10
- **Total Medicaid Paid:** $435.8M
- **Total Claims:** 658,415
- **Total Beneficiaries:** 125,032

**Anomaly Description:** 

**Detection Methods:** Flagged by 5 of 10 analytical categories: gev_extreme_value, claims_per_bene_vs_median, paid_per_claim_vs_median, volume_vs_median, iqr_outlier

**Estimated Recoverable Amount:** $327.7M

---

### Finding 49: ACADIAN AMBULANCE SERVICE, INC.

- **NPI:** 1316943566
- **Location:** LAFAYETTE, LA
- **Specialty:** Other
- **Entity Type:** Organization
- **Active Period:** 2018-01 through 2024-12
- **Total Medicaid Paid:** $422.7M
- **Total Claims:** 3,712,955
- **Total Beneficiaries:** 2,598,536

**Anomaly Description:** 

**Detection Methods:** Flagged by 3 of 10 analytical categories: gev_extreme_value, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $306.9M

---

### Finding 50: COORDINATED BEHAVIORAL CARE, INC

- **NPI:** 1730451071
- **Location:** NEW YORK, NY
- **Specialty:** Case Management Agency
- **Entity Type:** Organization
- **Active Period:** 2018-07 through 2024-12
- **Total Medicaid Paid:** $407.2M
- **Total Claims:** 1,213,709
- **Total Beneficiaries:** 1,212,752

**Anomaly Description:** 

**Detection Methods:** Flagged by 5 of 10 analytical categories: gev_extreme_value, covid_comparison, yoy_growth, iqr_outlier, change_point_cusum

**Estimated Recoverable Amount:** $308.8M

---

## 4. Medium-Confidence Findings

| # | Provider | NPI | State | Estimated Impact | Methods | Primary Method |
|---|----------|-----|-------|-----------------|---------|----------------|
| 10914 | NEW YORK CITY HEALTH AND HOSPI | 1083715460 | NY | $293.6M | 2 | gev_extreme_value |
| 10915 | ROCKY MOUNTAIN HOLDINGS, LLC | 1407855240 | AL | $279.7M | 2 | gev_extreme_value |
| 10916 | NATIONAL MENTOR HEALTHCARE | 1114070752 | AZ | $274.6M | 2 | iqr_outlier |
| 10917 | HHSC WIC PROGRAM | 1245765163 | TX | $238.4M | 2 | iqr_outlier |
| 10918 | CAREGIVERS HOME HEALTH TX INC | 1689712481 | TX | $228.1M | 2 | iqr_outlier |
| 10919 | HOME CARE DELIVERED, INC. | 1245239540 | VA | $210.5M | 2 | iqr_outlier |
| 10920 | BAYADA HOME HEALTH CARE, INC. | 1003847807 | NJ | $208.3M | 2 | iqr_outlier |
| 10921 | INDIANA UNIVERSITY HEALTH, INC | 1518032622 | IN | $177.9M | 2 | iqr_outlier |
| 10922 | NORTHEAST KINGDOM HUMAN SERVIC | 1538292768 | VT | $164.9M | 2 | iqr_outlier |
| 10923 | STARLIGHT HOME CARE AGENCY, IN | 1033370317 | NJ | $159.9M | 2 | iqr_outlier |
| 10924 | LUTHERAN FAMILY SERVICES OF VI | 1104986017 | VA | $156.0M | 2 | iqr_outlier |
| 10925 | CREATIVE WORKS | 1205962883 | ME | $138.8M | 2 | iqr_outlier |
| 10926 | NEW MEXICO CONSUMER DIRECT PER | 1740376292 | NM | $125.2M | 2 | iqr_outlier |
| 10927 | BYRAM HEALTHCARE CENTERS, INC. | 1215982913 | OR | $120.1M | 2 | iqr_outlier |
| 10928 | BRANDI'S HOPE COMMUNITY SERVIC | 1528387859 | MS | $119.5M | 2 | iqr_outlier |
| 10929 | OPTION 1 NUTRITION SOLUTIONS L | 1548347156 | CO | $116.6M | 2 | iqr_outlier |
| 10930 | WASHINGTON COUNTY MENTAL HEALT | 1710901939 | VT | $120.3M | 2 | iqr_outlier |
| 10931 | CITY OF PHOENIX ARIZONA | 1982781571 | AZ | $116.1M | 2 | iqr_outlier |
| 10932 | ABLELIGHT INC. | 1417010604 | WI | $116.0M | 2 | iqr_outlier |
| 10933 | REHABILITATION CENTERS, LLC | 1033201157 | MS | $105.2M | 2 | gev_extreme_value |
| 10934 | HEALTH CARE & REHABILITATION S | 1376760835 | VT | $108.5M | 2 | iqr_outlier |
| 10935 | NEW ENGLAND HOME CARE INC. | 1255333597 | CT | $107.9M | 2 | gev_extreme_value |
| 10936 | NFI NORTH, INC | 1619148277 | NH | $101.4M | 2 | gev_extreme_value |
| 10937 | PALOMAR HEALTH | 1457321317 | CA | $101.3M | 2 | iqr_outlier |
| 10938 | SHARP CHULA VISTA MEDICAL CENT | 1396728630 | CA | $96.8M | 2 | iqr_outlier |
| 10939 | SPURWINK SERVICES | 1295994804 | ME | $97.4M | 2 | zscore_paid_per_bene |
| 10940 | LOUISIANA UNITED METHODIST CHI | 1588744015 | LA | $92.6M | 2 | code_concentration_per_provider |
| 10941 | JUSTICE RESOURCE INSTITUTE, IN | 1093787095 | MA | $94.1M | 2 | iqr_outlier |
| 10942 | D & D SERVICES INC | 1629080254 | OK | $94.4M | 2 | gev_extreme_value |
| 10943 | DEVELOPMENTAL DISABILITIES CEN | 1831236009 | CO | $91.7M | 2 | gev_extreme_value |
| 10944 | BANNER - UNIVERSITY MEDICAL CE | 1265820179 | AZ | $92.2M | 2 | iqr_outlier |
| 10945 | NORTHWESTERN COUNSELING & SUPP | 1780708263 | VT | $95.0M | 2 | iqr_outlier |
| 10946 | COVENANT CARE SERVICES, LLC | 1245370808 | MO | $92.2M | 2 | gev_extreme_value |
| 10947 | FOUR COUNTY COMPREHENSIVE MENT | 1972545945 | IN | $88.6M | 2 | iqr_outlier |
| 10948 | NORTH METRO COMMUNITY SERVICES | 1720125115 | CO | $88.1M | 2 | gev_extreme_value |
| 10949 | REM EAST LLC | 1235569112 | MS | $86.2M | 2 | gev_extreme_value |
| 10950 | PRECISION TOXICOLOGY, LLC | 1730466590 | CA | $85.8M | 2 | iqr_outlier |
| 10951 | PEABODY RESIDENT SERVICES INC | 1124236724 | MA | $84.7M | 2 | gev_extreme_value |
| 10952 | COUNTY OF CHESTERFIELD VIRGINI | 1336293000 | VA | $82.5M | 2 | gev_extreme_value |
| 10953 | BYRAM HEALTHCARE CENTERS, INC. | 1609024397 | WA | $81.6M | 2 | gev_extreme_value |
| 10954 | STATE OF ALABAMA DEPT OF FINAN | 1447335930 | AL | $83.6M | 2 | gev_extreme_value |
| 10955 | 180 MEDICAL INC | 1639160708 | OK | $81.9M | 2 | iqr_outlier |
| 10956 | HEGIRA HEALTH, INC | 1184684979 | MI | $78.0M | 2 | gev_extreme_value |
| 10957 | CUMMINS BEHAVIORAL HEALTH SYST | 1740232115 | IN | $77.4M | 2 | gev_extreme_value |
| 10958 | BOSWELL REGIONAL CENTER | 1861414781 | MS | $75.6M | 2 | iqr_outlier |
| 10959 | GOOD NEIGHBOR ASSISTED LIVING  | 1609947845 | AZ | $75.2M | 2 | code_concentration_per_provider |
| 10960 | MONMOUTH MEDICAL CENTER INC | 1609983790 | NJ | $75.1M | 2 | iqr_outlier |
| 10961 | NORTHEAST BEHAVIORAL HEALTH CO | 1154302586 | MA | $74.7M | 2 | iqr_outlier |
| 10962 | EDWARDS HEALTH CARE SERVICES,  | 1962731570 | KY | $73.5M | 2 | gev_extreme_value |
| 10963 | LINCOLN BEHAVIORAL SERVICES | 1669451944 | MI | $71.7M | 2 | gev_extreme_value |
| 10964 | EL MIRADOR INCORPORATED | 1942617600 | NM | $71.1M | 2 | gev_extreme_value |
| 10965 | CREATIVE OPTIONS, LLC | 1245699461 | ME | $74.4M | 2 | gev_extreme_value |
| 10966 | MOTIVATIONAL SERVICES INC | 1609983907 | ME | $74.3M | 2 | gev_extreme_value |
| 10967 | VITRA HEALTH, INC. | 1073887246 | MA | $71.8M | 2 | gev_extreme_value |
| 10968 | HURON AREA CENTER FOR INDEPEND | 1538203211 | SD | $72.5M | 2 | gev_extreme_value |
| 10969 | LIFEMED ALASKA, LLC | 1871754473 | AK | $71.4M | 2 | gev_extreme_value |
| 10970 | ORTHOFIX US LLC | 1235136060 | TX | $71.6M | 2 | hhi_per_code |
| 10971 | MA DEPARTMENT OF YOUTH SERVICE | 1003038365 | MA | $70.2M | 2 | gev_extreme_value |
| 10972 | GOODWILL INDUSTRIES OF NORTHER | 1588785463 | ME | $71.4M | 2 | gev_extreme_value |
| 10973 | COUNTY OF LOS ANGELES | 1407878150 | CA | $69.3M | 2 | hhi_per_code |
| 10974 | CAMDEN COUNTY PARTNERSHIP FOR  | 1396887543 | NJ | $68.9M | 2 | gev_extreme_value |
| 10975 | CENTRAL STATE COMMUNITY SERVIC | 1245459460 | MI | $65.5M | 2 | gev_extreme_value |
| 10976 | HOMETOWN OXYGEN CHARLOTTE LLC | 1871738153 | NC | $66.9M | 2 | change_point_cusum |
| 10977 | HELP AT HOME, LLC | 1790813095 | MO | $67.4M | 2 | gev_extreme_value |
| 10978 | LANCASTER HOSPITAL CORPORATION | 1508856535 | CA | $65.0M | 2 | iqr_outlier |
| 10979 | POSITIVE BEHAVIOR SUPPORTS | 1700024296 | FL | $65.6M | 2 | iqr_outlier |
| 10980 | SENIORCARE EMERGENCY MEDICAL S | 1265542765 | NY | $64.1M | 2 | gev_extreme_value |
| 10981 | WATTS HEALTHCARE CORPORATION | 1477649119 | CA | $63.7M | 2 | gev_extreme_value |
| 10982 | DAP HEALTH, INC. | 1619036514 | CA | $63.4M | 2 | gev_extreme_value |
| 10983 | ALTERNATIVE SERVICES-NE, INC. | 1114152089 | ME | $64.8M | 2 | gev_extreme_value |
| 10984 | MASSACHUSETTS REHABILITATION C | 1326250150 | MA | $62.7M | 2 | iqr_outlier |
| 10985 | HEALTHY LIVING MEDICAL SUPPLY, | 1033142948 | MI | $61.0M | 2 | gev_extreme_value |
| 10986 | CAPITAL HEALTH SYSTEM, INC. | 1073516183 | NJ | $62.8M | 2 | iqr_outlier |
| 10987 | BERGEN'S PROMISE, INC. | 1083738868 | NJ | $62.7M | 2 | gev_extreme_value |
| 10988 | SHALOM HOUSE, INC. | 1992702955 | ME | $64.3M | 2 | gev_extreme_value |
| 10989 | LINX COMMUNITY SERVICE, LLC | 1891293056 | WV | $61.1M | 2 | code_concentration_per_provider |
| 10990 | WILLOWS WAY, INC. | 1275654923 | MO | $62.7M | 2 | gev_extreme_value |
| 10991 | RESPIRATORY TECHNOLOGIES, INC. | 1962459537 | MN | $61.3M | 2 | code_concentration_per_provider |
| 10992 | DUNGARVIN NEW MEXICO LLC | 1033288626 | NM | $60.4M | 2 | gev_extreme_value |
| 10993 | NISHNA PRODUCTIONS, INC. | 1265526248 | IA | $60.3M | 2 | gev_extreme_value |

## 5. Low-Confidence Findings

An additional 560,889 providers were flagged at low confidence, representing $118.1B in potential recoverable payments. These findings warrant further investigation but do not meet the threshold for immediate referral.

| # | Provider | NPI | State | Impact | Method |
|---|----------|-----|-------|--------|--------|
| 1 | WAYPOINT MAINE, INC. | 1649495110 | ME | $100.8M | gev_extreme_value |
| 2 | RUTGERS HEALTH - UNIVERSI | 1942217054 | NJ | $94.1M | gev_extreme_value |
| 3 | KYPPEC,INC | 1114052057 | KY | $92.6M | gev_extreme_value |
| 4 | NATIONAL CHILDREN'S CENTE | 1700099959 | DC | $88.0M | gev_extreme_value |
| 5 | ST. JOHN'S COMMUNITY SERV | 1780806828 | DC | $85.7M | gev_extreme_value |
| 6 | COMMUNITY LIVING SERVICES | 1326657602 | ND | $84.4M | gev_extreme_value |
| 7 | CAPITAL CARE, INC | 1366527111 | MD | $84.3M | gev_extreme_value |
| 8 | UAHSF NEONATOLOGY | 1619987302 | AL | $86.3M | gev_extreme_value |
| 9 | CRAIG RESOURCES LLC | 1689699837 | KS | $81.0M | gev_extreme_value |
| 10 | MGA HOME HEALTHCARE LLC | 1174546063 | AZ | $78.0M | gev_extreme_value |
| 11 | BREWSTER AMBULANCE SERVIC | 1760707582 | MA | $77.6M | gev_extreme_value |
| 12 | LIFE FLIGHT NETWORK LLC | 1386837367 | OR | $75.8M | gev_extreme_value |
| 13 | REACH AIR MEDICAL SERVICE | 1134169535 | CA | $76.9M | gev_extreme_value |
| 14 | PORT RESOURCES | 1053467779 | ME | $76.7M | gev_extreme_value |
| 15 | MPS HEALTHCARE INC | 1689638488 | VA | $74.2M | gev_extreme_value |
| 16 | GREEN RIVER REGIONAL MENT | 1629134663 | KY | $73.7M | gev_extreme_value |
| 17 | RESCARE MINNESOTA, INC. | 1881946564 | MN | $72.9M | gev_extreme_value |
| 18 | CCRI, INC | 1295870699 | MN | $72.2M | gev_extreme_value |
| 19 | COMMUNITY OPTIONS FOR RES | 1356951503 | ND | $71.8M | gev_extreme_value |
| 20 | NORTHEAST ARC INC | 1679570113 | MA | $70.1M | gev_extreme_value |
| 21 | SUPPORT SERVICES OF VIRGI | 1487747135 | VA | $69.5M | gev_extreme_value |
| 22 | FOREVER CARE DBA INDEPEND | 1033275755 | KY | $65.2M | gev_extreme_value |
| 23 | SUPPORT SOLUTIONS INC | 1235299496 | ME | $67.6M | gev_extreme_value |
| 24 | DEVELOPMENTAL SERVICES OF | 1275531295 | KS | $64.2M | gev_extreme_value |
| 25 | WHOLISTIC SERVICES, INC. | 1083883243 | DC | $63.3M | gev_extreme_value |
| 26 | ELM WASECA COUNTY SLS INC | 1770625477 | MN | $61.0M | gev_extreme_value |
| 27 | CAPITOL COUNTY CHILDREN'S | 1942350020 | NJ | $61.1M | gev_extreme_value |
| 28 | SUPERIOR AIR-GROUND AMBUL | 1336107838 | IL | $61.1M | gev_extreme_value |
| 29 | DOCTORS MEDICAL CENTER OF | 1184654923 | CA | $60.9M | gev_extreme_value |
| 30 | PRIDE INC. | 1356453484 | ND | $59.3M | gev_extreme_value |
| 31 | STATEWIDE HEALTHCARE SERV | 1629199351 | MS | $59.5M | gev_extreme_value |
| 32 | CG OF TENNESSEE, LLC | 1306364054 | TN | $60.4M | gev_extreme_value |
| 33 | LIFESKILLS, INC. | 1669401816 | KY | $58.7M | gev_extreme_value |
| 34 | Individual | 1184653388 |  | $52.3M | gev_extreme_value |
| 35 | OPTUM PHARMACY 702, LLC | 1083045140 | IN | $55.1M | gev_extreme_value |
| 36 | SAGUARO FOUNDATION | 1992998348 | AZ | $56.1M | gev_extreme_value |
| 37 | CITY OF LAS VEGAS | 1336290964 | NV | $55.2M | gev_extreme_value |
| 38 | DIABETES MANAGEMENT AND S | 1164537452 | LA | $54.9M | gev_extreme_value |
| 39 | PREFERRED TOUCH HOME CARE | 1447522685 | FL | $56.7M | gev_extreme_value |
| 40 | PERRYLEE HOME HEALTH CARE | 1568591725 | TX | $55.9M | gev_extreme_value |
| 41 | SPECIALIZED COMMUNITY CAR | 1275651267 | VT | $57.1M | gev_extreme_value |
| 42 | JED ADAM ENTERPRISES, LLC | 1598901100 | NV | $54.3M | gev_extreme_value |
| 43 | ONE SOURCE MEDICAL GROUP  | 1366653545 | FL | $55.4M | gev_extreme_value |
| 44 | RAMSEY COUNTY COMMUNITY H | 1811055957 | MN | $53.7M | gev_extreme_value |
| 45 | EASTER SEALS BLAKE FOUNDA | 1548356207 | AZ | $54.0M | gev_extreme_value |
| 46 | PHOENIX HOUSES OF LONG IS | 1174691281 | NY | $52.4M | gev_extreme_value |
| 47 | SOUTHERN MS PLANNING AND  | 1568558161 | MS | $51.7M | gev_extreme_value |
| 48 | COMMUNITY ALTERNATIVES VI | 1306252804 | VA | $51.8M | gev_extreme_value |
| 49 | HOME DELIVERY INCONTINENT | 1649383084 | MO | $52.4M | gev_extreme_value |
| 50 | ALL POINTE HOMECARE LLC | 1497078315 | CT | $52.7M | gev_extreme_value |

## 6. Systemic Patterns

### State-Level Anomalies

![State Heatmap](charts/state_heatmap.png)

Several states show disproportionately high per-beneficiary spending for specific service categories, particularly personal care services and behavioral health. These state-level patterns may indicate systemic issues with rate-setting, program integrity, or oversight rather than individual provider fraud.

### High-Risk HCPCS Categories

![Top 20 Procedures](charts/top20_flagged_procedures.png)

The highest-risk procedure categories are:

- **T1019** (Personal Care Services (15 min)): $122.7B total, 9,780 providers
- **T1015** (Clinic Visit/Encounter): $49.2B total, 13,829 providers
- **T2016** (Code T2016): $34.9B total, 1,761 providers
- **99213** (Office Visit, Est Patient (Low)): $33.0B total, 164,075 providers
- **S5125** (Attendant Care (15 min)): $31.3B total, 4,555 providers

### Temporal Trends

![Monthly Spending Trend](charts/monthly_spending_trend.png)

Total Medicaid spending shows a clear upward trend from 2018 through 2024, with a notable dip during the early COVID-19 pandemic (April-May 2020) followed by rapid recovery and acceleration. Several flagged providers show billing patterns that diverge sharply from this population trend.

### Network and Organized Billing Schemes

![Network Graph](charts/network_graph_top3.png)

The network analysis identified several large billing networks with characteristics consistent with organized fraud schemes, including hub-and-spoke structures where a single billing entity submits claims on behalf of dozens of servicing providers, some of whom show signs of being phantom providers (very short activity periods, no independent billing, and concentrated billing patterns).

## 7. Financial Impact Summary

| Metric | Value |
|--------|-------|
| Total Medicaid Spending Analyzed | $1093.6B |
| Total Findings | 591,181 |
| High-Confidence Findings | 10,913 |
| Medium-Confidence Findings | 19,379 |
| Low-Confidence Findings | 560,889 |
| **Total Estimated Recoverable** | **$355.0B** |
| High-Confidence Impact | $177.7B |
| Medium-Confidence Impact | $59.1B |
| Low-Confidence Impact | $118.1B |

![Findings by Category](charts/findings_by_category.png)

![Provider Risk Scatter](charts/provider_risk_scatter.png)

![Benford's Law](charts/benfords_law.png)

![Lorenz Curve](charts/lorenz_curve.png)

## 8. Recommendations

### Immediate Referrals to OIG

The following providers should be referred to the HHS Office of Inspector General for investigation:

1. **LOS ANGELES COUNTY DEPARTMENT OF MENTAL HEALTH** (NPI 1699703827, CA): $5.5B estimated improper payments. Flagged by 19 detection methods.
2. **DEPARTMENT OF INTELLECTUAL AND DEVELOPMENTAL DISABILITIES, STATE OF TN** (NPI 1629436241, TN): $2.3B estimated improper payments. Flagged by 12 detection methods.
3. **ALABAMA DEPARTMENT OF MENTAL HEALTH AND MENTAL RETARDATION** (NPI 1982757688, AL): $2.1B estimated improper payments. Flagged by 11 detection methods.
4. **GUARDIANTRAC. LLC** (NPI 1710176151, MI): $1.3B estimated improper payments. Flagged by 15 detection methods.
5. **DEPARTMENT OF INTELLECTUAL AND DEVELOPMENTAL DISABILITIES, STATE OF TN** (NPI 1356709976, TN): $1.4B estimated improper payments. Flagged by 10 detection methods.
6. **CITY OF CHICAGO** (NPI 1376554592, IL): $1.2B estimated improper payments. Flagged by 9 detection methods.
7. **DEPARTMENT OF DEVELOPMENTAL SERVICES** (NPI 1750504064, MA): $1.1B estimated improper payments. Flagged by 13 detection methods.
8. **MAINS'L FLORIDA, INC.** (NPI 1932341898, MN): $973.2M estimated improper payments. Flagged by 7 detection methods.
9. **DEPARTMENT OF HEALTH AND SENIOR SERVICES** (NPI 1326168840, NJ): $973.8M estimated improper payments. Flagged by 7 detection methods.
10. **NEW PARTNERS, INC** (NPI 1083783013, NY): $911.6M estimated improper payments. Flagged by 11 detection methods.

### Policy Changes

- **Strengthen pre-payment review** for personal care services (T1019, T1020) and behavioral health codes (H-series), which account for a disproportionate share of flagged spending.
- **Implement real-time volume limits** for timed services to prevent physically impossible billing (e.g., more than 8 hours of personal care per beneficiary per day).
- **Require periodic re-validation** of billing networks, particularly pure billing entities that never deliver services directly.
- **Enhance cross-state data sharing** to detect providers billing in geographic impossibility patterns.

### Enhanced Monitoring Targets

- New providers billing more than $500,000 in their first month of activity
- Billing networks that add more than 5 servicing NPIs in a single month
- Providers whose December billing exceeds 3x their monthly average
- Providers deriving more than 90% of revenue from a single HCPCS code
- States where per-beneficiary spending for specific codes exceeds 2x the national median

## 9. Appendix

### Data Dictionary

| Field | Description |
|-------|-------------|
| BILLING_PROVIDER_NPI_NUM | National Provider Identifier of the billing entity |
| SERVICING_PROVIDER_NPI_NUM | NPI of the provider who delivered the service |
| HCPCS_CODE | Healthcare Common Procedure Coding System code |
| CLAIM_FROM_MONTH | Month of service (YYYY-MM format) |
| TOTAL_UNIQUE_BENEFICIARIES | Number of distinct Medicaid patients |
| TOTAL_CLAIMS | Number of billing events |
| TOTAL_PAID | Dollar amount paid by Medicaid |

### Charts

- `benfords_law.png`
- `finding_F001_timeseries.png`
- `finding_F002_timeseries.png`
- `finding_F003_timeseries.png`
- `finding_F004_timeseries.png`
- `finding_F005_timeseries.png`
- `finding_F006_timeseries.png`
- `finding_F007_timeseries.png`
- `finding_F008_timeseries.png`
- `finding_F009_timeseries.png`
- `finding_F010_timeseries.png`
- `finding_F011_timeseries.png`
- `finding_F012_timeseries.png`
- `finding_F013_timeseries.png`
- `finding_F014_timeseries.png`
- `finding_F015_timeseries.png`
- `finding_F016_timeseries.png`
- `finding_F017_timeseries.png`
- `finding_F018_timeseries.png`
- `finding_F019_timeseries.png`
- `finding_F020_timeseries.png`
- `findings_by_category.png`
- `lorenz_curve.png`
- `monthly_spending_trend.png`
- `network_graph_top3.png`
- `provider_risk_scatter.png`
- `state_heatmap.png`
- `temporal_anomalies_top5.png`
- `top20_flagged_procedures.png`
- `top20_flagged_providers.png`
- `top20_procedures.png`
- `top20_providers.png`

### Analytical Framework

This analysis tested 1,087 structured hypotheses organized into 10 categories. Each hypothesis has a defined acceptance criterion, statistical threshold, and financial impact method. The full hypothesis set is available in `output/hypotheses/all_hypotheses.json`.

---

*This report was generated from the HHS Provider Spending dataset using automated analytical methods. All findings should be verified through additional investigation before taking enforcement action.*
