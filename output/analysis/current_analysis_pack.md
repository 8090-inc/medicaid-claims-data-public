# Current Analysis Pack

## Summary

- Total findings: 607522
- High confidence: 15583
- Medium confidence: 27354
- Low confidence: 564585
- Total estimated recoverable (standardized, provider-level): $355,781,963,848
- Systemic exposure (state/code aggregates): $116,147,010,551
- Quality-weighted recoverable: $325,993,532,034
- Pruned methods: 4
- Pruned methods file: /Users/rohitkelapure/projects/medicaid-claims-data/output/analysis/pruned_methods.csv
- Quality weights applied: True

## Top 10 States by Weighted Impact

- CA: $43,418,481,333
- NY: $28,529,728,790
- TX: $17,255,731,525
- MA: $17,157,526,801
- NJ: $14,046,013,195
- MI: $12,234,548,768
- AZ: $10,413,024,910
- FL: $10,171,023,624
- NC: $9,884,526,544
- VA: $9,739,499,702

## Top 10 Methods by Weighted Impact (multi-method providers counted per method)

- gev_extreme_value: $325,863,383,655
- specialty_peer_comparison: $158,952,873,352
- iqr_outlier: $115,535,241,879
- volume_vs_median: $95,702,637,424
- paid_per_claim_vs_median: $85,049,807,256
- change_point_cusum: $65,035,548,628
- state_peer_comparison: $62,539,997,305
- yoy_growth: $48,256,984,641
- zscore_paid_per_claim: $34,638,815,484
- code_concentration_per_provider: $32,195,830,196

## Top 20 Risk Queue (weighted impact)

- 1699703827 LOS ANGELES COUNTY DEPARTMENT OF MENTAL HEALTH (CA): $4,985,377,850 (high)
- 1629436241 DEPARTMENT OF INTELLECTUAL AND DEVELOPMENTAL DISABILITIES, STATE OF TN (TN): $2,092,620,128 (high)
- 1982757688 ALABAMA DEPARTMENT OF MENTAL HEALTH AND MENTAL RETARDATION (AL): $1,930,799,310 (high)
- 1710176151 GUARDIANTRAC. LLC (MI): $1,239,287,858 (high)
- 1356709976 DEPARTMENT OF INTELLECTUAL AND DEVELOPMENTAL DISABILITIES, STATE OF TN (TN): $1,231,862,897 (high)
- 1376554592 CITY OF CHICAGO (IL): $1,058,450,582 (high)
- 1750504064 DEPARTMENT OF DEVELOPMENTAL SERVICES (MA): $987,376,435 (high)
- 1932341898 MAINS'L FLORIDA, INC. (MN): $899,767,032 (high)
- 1326168840 DEPARTMENT OF HEALTH AND SENIOR SERVICES (NJ): $889,736,254 (high)
- 1083783013 NEW PARTNERS, INC (NY): $837,549,467 (high)
- 1518096411 COMMONWEALTH OF MASSACHUSETS (MA): $813,902,090 (high)
- 1134250475 COMMONWEALTH OF MASS-DDS (MA): $790,543,084 (high)
- 1396049987 COMMUNITY ASSISTANCE RESOURCES & EXTENDED SERVICES INC (NY): $737,776,546 (high)
- 1124494059 TENNESSEE DEPARTMENT OF CHILDREN'S SERVICES (TN): $692,857,641 (high)
- 1245354000 COMMONWEALTH OF MASSACHUSETTS-DDS (MA): $690,891,280 (high)
- 1538649983 CONSUMER DIRECT CARE NETWORK VIRGINIA (MT): $609,777,638 (high)
- 1104963347 COUNTY OF ORANGE (CA): $608,036,871 (high)
- 1043386659 COUNTY OF SACRAMENTO (CA): $584,925,255 (high)
- 1124304621 PUBLIC PARTNERSHIPS-COLORADO, INC. (MA): $573,466,296 (high)
- 1306875695 YOUTH VILLAGES, INC. (TN): $539,537,122 (high)

## Top 20 Provider-Level Risk Queue (weighted impact)

- 1699703827 LOS ANGELES COUNTY DEPARTMENT OF MENTAL HEALTH (CA): $4,985,377,850 (high)
- 1629436241 DEPARTMENT OF INTELLECTUAL AND DEVELOPMENTAL DISABILITIES, STATE OF TN (TN): $2,092,620,128 (high)
- 1982757688 ALABAMA DEPARTMENT OF MENTAL HEALTH AND MENTAL RETARDATION (AL): $1,930,799,310 (high)
- 1710176151 GUARDIANTRAC. LLC (MI): $1,239,287,858 (high)
- 1356709976 DEPARTMENT OF INTELLECTUAL AND DEVELOPMENTAL DISABILITIES, STATE OF TN (TN): $1,231,862,897 (high)
- 1376554592 CITY OF CHICAGO (IL): $1,058,450,582 (high)
- 1750504064 DEPARTMENT OF DEVELOPMENTAL SERVICES (MA): $987,376,435 (high)
- 1932341898 MAINS'L FLORIDA, INC. (MN): $899,767,032 (high)
- 1326168840 DEPARTMENT OF HEALTH AND SENIOR SERVICES (NJ): $889,736,254 (high)
- 1083783013 NEW PARTNERS, INC (NY): $837,549,467 (high)
- 1518096411 COMMONWEALTH OF MASSACHUSETS (MA): $813,902,090 (high)
- 1134250475 COMMONWEALTH OF MASS-DDS (MA): $790,543,084 (high)
- 1396049987 COMMUNITY ASSISTANCE RESOURCES & EXTENDED SERVICES INC (NY): $737,776,546 (high)
- 1124494059 TENNESSEE DEPARTMENT OF CHILDREN'S SERVICES (TN): $692,857,641 (high)
- 1245354000 COMMONWEALTH OF MASSACHUSETTS-DDS (MA): $690,891,280 (high)
- 1538649983 CONSUMER DIRECT CARE NETWORK VIRGINIA (MT): $609,777,638 (high)
- 1104963347 COUNTY OF ORANGE (CA): $608,036,871 (high)
- 1043386659 COUNTY OF SACRAMENTO (CA): $584,925,255 (high)
- 1124304621 PUBLIC PARTNERSHIPS-COLORADO, INC. (MA): $573,466,296 (high)
- 1306875695 YOUTH VILLAGES, INC. (TN): $539,537,122 (high)

## Top 20 Systemic / Rate-Level Risk Queue (weighted impact)

- STATE_NY_T1019 NY - Personal care services, per 15 minutes, not for an inpatient (NY): $0 (medium)
- STATE_NJ_H2016 NJ - Comprehensive community support services, per diem (NJ): $0 (medium)
- PAIR_99242_H2015  (): $0 (medium)
- PAIR_99350_H2015  (): $0 (medium)
- STATE_NY_T1020 NY - Personal care services, per diem, not for an inpatient or re (NY): $0 (medium)
- PAIR_T2016_T5999  (): $0 (medium)
- PAIR_99345_H2015  (): $0 (medium)
- PAIR_99253_H2015  (): $0 (medium)
- PAIR_99243_H2015  (): $0 (medium)
- PAIR_99252_H2015  (): $0 (medium)
- PAIR_99309_H2015  (): $0 (medium)
- PAIR_99306_H2015  (): $0 (medium)
- PAIR_99307_H2015  (): $0 (medium)
- STATE_MI_H2015 MI - Comprehensive community support services, per 15 minutes (MI): $0 (medium)
- STATE_CA_H2010 CA - Comprehensive medication services, per 15 minutes (CA): $0 (medium)
- STATE_MO_T1040 MO - Medicaid certified community behavioral health clinic servic (MO): $0 (medium)
- A565813600 NPI A565813600 (): $0 (high)
- STATE_VA_T1019 VA - Personal care services, per 15 minutes, not for an inpatient (VA): $0 (medium)
- STATE_LA_S5125 LA - Attendant care services; per 15 minutes (LA): $0 (medium)
- STATE_CA_90999 CA - Code 90999 (CA): $0 (medium)

## Outputs

- risk_queue_top100.csv
- risk_queue_top500.csv
- risk_queue_providers_top100.csv
- risk_queue_providers_top500.csv
- risk_queue_systemic_top100.csv
- risk_queue_systemic_top500.csv
