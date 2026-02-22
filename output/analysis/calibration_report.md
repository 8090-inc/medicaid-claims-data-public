# Calibration Report (Holdout + Placebo)

- Holdout window: 2023-01 to 2024-12
- Baseline holdout rate (all providers): 65.44%

## Most Unstable Methods (lowest holdout z-score delta)

- phantom_billing: holdout_rate=50.00%, baseline=65.44%, z_delta=-1.76, flagged=40
- seasonality_anomaly_low_cv: holdout_rate=31.03%, baseline=65.44%, z_delta=-0.89, flagged=58
- impossible_aba_volume: holdout_rate=100.00%, baseline=65.44%, z_delta=-0.88, flagged=2
- ramp_up: holdout_rate=87.88%, baseline=65.44%, z_delta=-0.53, flagged=66
- addiction_rapid_exit: holdout_rate=95.00%, baseline=65.44%, z_delta=-0.43, flagged=20
- high_risk_category: holdout_rate=94.90%, baseline=65.44%, z_delta=-0.34, flagged=98
- ensemble_agreement: holdout_rate=100.00%, baseline=65.44%, z_delta=-0.33, flagged=4
- zscore_paid_per_bene: holdout_rate=84.00%, baseline=65.44%, z_delta=-0.26, flagged=1000
- aba_peer_cpb: holdout_rate=95.00%, baseline=65.44%, z_delta=-0.24, flagged=20
- aba_concentration: holdout_rate=100.00%, baseline=65.44%, z_delta=-0.24, flagged=20
- code_concentration_per_provider: holdout_rate=98.00%, baseline=65.44%, z_delta=-0.16, flagged=1000
- low_entropy_billing: holdout_rate=100.00%, baseline=65.44%, z_delta=-0.15, flagged=15
- dbscan: holdout_rate=100.00%, baseline=65.44%, z_delta=-0.13, flagged=30
- seasonality_anomaly_concentration: holdout_rate=72.73%, baseline=65.44%, z_delta=-0.11, flagged=22
- composite_network_plus_volume: holdout_rate=100.00%, baseline=65.44%, z_delta=-0.09, flagged=9

## Most Stable Methods (highest holdout z-score delta)

- addiction_high_per_bene: holdout_rate=100.00%, baseline=65.44%, z_delta=2.82, flagged=10
- pharmacy_single_drug: holdout_rate=100.00%, baseline=65.44%, z_delta=1.84, flagged=18
- pharmacy_rate_outlier: holdout_rate=100.00%, baseline=65.44%, z_delta=1.66, flagged=20
- provider_share_per_code: holdout_rate=100.00%, baseline=65.44%, z_delta=0.75, flagged=60
- post_deactivation_billing: holdout_rate=95.00%, baseline=65.44%, z_delta=0.46, flagged=20
- random_forest: holdout_rate=90.00%, baseline=65.44%, z_delta=0.34, flagged=10
- aba_rapid_entrant: holdout_rate=95.00%, baseline=65.44%, z_delta=0.28, flagged=20
- composite_temporal_plus_statistical: holdout_rate=100.00%, baseline=65.44%, z_delta=0.27, flagged=15
- size_tier_high_paid_low_claims: holdout_rate=76.00%, baseline=65.44%, z_delta=0.25, flagged=500
- iqr_outlier: holdout_rate=87.09%, baseline=65.44%, z_delta=0.24, flagged=4059
- captive_servicing: holdout_rate=15.00%, baseline=65.44%, z_delta=0.23, flagged=20
- shared_bene_count: holdout_rate=94.74%, baseline=65.44%, z_delta=0.20, flagged=19
- lof: holdout_rate=100.00%, baseline=65.44%, z_delta=0.18, flagged=15
- address_cluster_flagged: holdout_rate=90.00%, baseline=65.44%, z_delta=0.17, flagged=20
- kickback_premium: holdout_rate=95.00%, baseline=65.44%, z_delta=0.17, flagged=20

## Positive Control Overlaps

- LEIE: 8302 NPIs loaded
  See positive_control_overlaps.csv for per-method overlap rates.
