#!/usr/bin/env python3
"""Milestone 4: Hypothesis generation.

Programmatically generates exactly 1,000 structured fraud hypotheses as JSON,
organized into 10 categories with SQL templates and analysis function references.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output', 'hypotheses')

# Top 30 HCPCS codes by spending (used for per-code hypotheses)
TOP_30_CODES = [
    'T1019', 'T1015', '99213', '99214', 'H0015', 'T2003', 'T1005', '99215',
    'T2025', '99212', 'T1020', 'H2015', 'H2016', '99203', '99204', '99202',
    '99211', 'T2024', '97110', '97530', '92507', '97140', '97116', '90834',
    '90837', '90832', 'H0031', 'H0036', 'H0004', 'T1017',
]

# Top 20 HCPCS codes (subset for some hypotheses)
TOP_20_CODES = TOP_30_CODES[:20]

# HCPCS categories
HCPCS_CATEGORIES = [
    'Home Health', 'Behavioral Health', 'E&M', 'DME', 'Lab',
    'Pharmacy', 'Therapy', 'Transportation', 'Temp/Waiver', 'Other',
]

# IQR metrics (provider_summary only)
IQR_METRICS = [
    'total_paid', 'total_claims', 'total_beneficiaries', 'avg_paid_per_claim',
    'avg_claims_per_bene', 'num_codes', 'num_months',
]

# Specialties for peer comparison
SPECIALTIES = [
    'Family Medicine', 'Internal Medicine', 'Pediatrics', 'Nurse Practitioner',
    'Clinical Social Worker', 'Psychologist', 'Physical Therapist',
    'Occupational Therapist', 'Speech-Language Pathologist', 'Home Health Agency',
    'Community/Behavioral Health', 'Pharmacist', 'Dentist', 'Chiropractor',
    'DME Supplier', 'Ambulance', 'Skilled Nursing Facility', 'Clinic/Center',
    'Counselor', 'Mental Health Counselor',
]

# E&M level families
EM_FAMILIES = {
    'office_established': ['99211', '99212', '99213', '99214', '99215'],
    'office_new': ['99201', '99202', '99203', '99204', '99205'],
    'ed_visit': ['99281', '99282', '99283', '99284', '99285'],
}

# Timed service codes with physical limits
TIMED_CODES = [
    ('T1019', 15, 480), ('T1020', 1440, 31), ('T1005', 15, 480),
    ('S5125', 15, 480), ('S5130', 15, 480), ('S5150', 15, 480),
    ('H0015', 15, 192), ('H2015', 15, 480), ('H2016', 60, 120),
    ('H0036', 15, 480), ('T1016', 15, 192), ('T1017', 15, 192),
    ('H2017', 15, 480), ('T2020', 15, 480), ('H2019', 15, 480),
]


def gen_category_1():
    """Statistical Outlier Detection: 150 hypotheses (H0001-H0150)."""
    hyps = []
    h = 0

    # 1A: paid-per-claim Z-score (H0001-H0030)
    for code in TOP_30_CODES:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '1', 'subcategory': '1A',
            'description': f'Providers with paid-per-claim z-score > 3.0 for {code}',
            'method': 'z_score_paid_per_claim',
            'acceptance_criteria': 'z > 3.0, claims >= 10, peers >= 20, excess > $10K',
            'sql_template': f"""
                WITH code_stats AS (
                    SELECT AVG(paid_per_claim) AS mean_ppc, STDDEV(paid_per_claim) AS std_ppc,
                           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY paid_per_claim) AS median_ppc,
                           COUNT(*) AS num_peers
                    FROM provider_hcpcs WHERE hcpcs_code = '{code}' AND claims >= 10
                )
                SELECT ph.billing_npi, ph.paid_per_claim, ph.claims, ph.paid,
                       (ph.paid_per_claim - cs.mean_ppc) / NULLIF(cs.std_ppc, 0) AS z_score,
                       (ph.paid_per_claim - cs.median_ppc) * ph.claims AS excess_amount,
                       cs.median_ppc, cs.num_peers
                FROM provider_hcpcs ph CROSS JOIN code_stats cs
                WHERE ph.hcpcs_code = '{code}' AND ph.claims >= 10
                  AND cs.num_peers >= 20 AND cs.std_ppc > 0
                  AND (ph.paid_per_claim - cs.mean_ppc) / cs.std_ppc > 3.0
                  AND (ph.paid_per_claim - cs.median_ppc) * ph.claims > 10000
                ORDER BY z_score DESC LIMIT 50
            """,
            'financial_impact_method': '(provider_rate - peer_median_rate) * provider_claims',
            'parameters': {'hcpcs_code': code, 'z_threshold': 3.0, 'min_claims': 10, 'min_peers': 20, 'min_excess': 10000},
        })

    # 1B: claims-per-beneficiary Z-score (H0031-H0060)
    for code in TOP_30_CODES:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '1', 'subcategory': '1B',
            'description': f'Providers with claims-per-bene z-score > 3.0 for {code}',
            'method': 'z_score_claims_per_bene',
            'acceptance_criteria': 'z > 3.0, beneficiaries >= 12, ratio > 2x peer median',
            'sql_template': f"""
                WITH code_stats AS (
                    SELECT AVG(claims_per_bene) AS mean_cpb, STDDEV(claims_per_bene) AS std_cpb,
                           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY claims_per_bene) AS median_cpb
                    FROM provider_hcpcs WHERE hcpcs_code = '{code}' AND beneficiaries >= 12
                )
                SELECT ph.billing_npi, ph.claims_per_bene, ph.beneficiaries, ph.paid,
                       (ph.claims_per_bene - cs.mean_cpb) / NULLIF(cs.std_cpb, 0) AS z_score,
                       cs.median_cpb
                FROM provider_hcpcs ph CROSS JOIN code_stats cs
                WHERE ph.hcpcs_code = '{code}' AND ph.beneficiaries >= 12 AND cs.std_cpb > 0
                  AND (ph.claims_per_bene - cs.mean_cpb) / cs.std_cpb > 3.0
                  AND ph.claims_per_bene > 2 * cs.median_cpb
                ORDER BY z_score DESC LIMIT 50
            """,
            'financial_impact_method': '(provider_cpb - peer_median_cpb) * peer_median_rate * beneficiaries',
            'parameters': {'hcpcs_code': code, 'z_threshold': 3.0, 'min_bene': 12},
        })

    # 1C: paid-per-beneficiary Z-score (H0061-H0090)
    for code in TOP_30_CODES:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '1', 'subcategory': '1C',
            'description': f'Providers with paid-per-bene z-score > 3.0 for {code}',
            'method': 'z_score_paid_per_bene',
            'acceptance_criteria': 'z > 3.0, excess > $500/beneficiary',
            'sql_template': f"""
                WITH code_stats AS (
                    SELECT AVG(paid / NULLIF(beneficiaries, 0)) AS mean_ppb,
                           STDDEV(paid / NULLIF(beneficiaries, 0)) AS std_ppb,
                           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY paid / NULLIF(beneficiaries, 0)) AS median_ppb
                    FROM provider_hcpcs WHERE hcpcs_code = '{code}' AND beneficiaries > 0
                )
                SELECT ph.billing_npi, ph.paid / NULLIF(ph.beneficiaries, 0) AS ppb,
                       ph.beneficiaries, ph.paid,
                       (ph.paid / NULLIF(ph.beneficiaries, 0) - cs.mean_ppb) / NULLIF(cs.std_ppb, 0) AS z_score,
                       cs.median_ppb
                FROM provider_hcpcs ph CROSS JOIN code_stats cs
                WHERE ph.hcpcs_code = '{code}' AND ph.beneficiaries > 0 AND cs.std_ppb > 0
                  AND (ph.paid / ph.beneficiaries - cs.mean_ppb) / cs.std_ppb > 3.0
                  AND (ph.paid / ph.beneficiaries - cs.median_ppb) > 500
                ORDER BY z_score DESC LIMIT 50
            """,
            'financial_impact_method': '(provider_ppb - peer_median_ppb) * beneficiaries',
            'parameters': {'hcpcs_code': code, 'z_threshold': 3.0, 'min_excess_per_bene': 500},
        })

    # 1D: IQR-based outliers (H0091-H0110)
    for metric in IQR_METRICS:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '1', 'subcategory': '1D',
            'description': f'Providers with {metric} exceeding Q3 + 3*IQR',
            'method': 'iqr_outlier',
            'acceptance_criteria': f'value > Q3 + 3*IQR, months >= 6, flagged amount > $50K',
            'analysis_function': 'statistical_analyzer._iqr_outlier',
            'financial_impact_method': 'amount above IQR threshold',
            'parameters': {'metric': metric, 'iqr_multiplier': 3.0, 'min_months': 6, 'min_amount': 50000},
        })

    # 1E: GEV extreme value (H0111-H0130)
    for i, cat in enumerate(HCPCS_CATEGORIES):
        for metric_name in ['paid_per_claim', 'total_paid']:
            h += 1
            hyps.append({
                'id': f'H{h:04d}', 'category': '1', 'subcategory': '1E',
                'description': f'GEV extreme value analysis for {cat} ({metric_name})',
                'method': 'gev_extreme',
                'acceptance_criteria': f'exceeds GEV 99th pct return level, p < 0.01, total > $50K',
                'analysis_function': 'statistical_analyzer._gev_extreme_value',
                'financial_impact_method': 'amount above GEV return level',
                'parameters': {'category': cat, 'metric': metric_name, 'p_threshold': 0.01, 'min_amount': 50000},
            })

    # 1F: Benford's Law and related (H0131-H0150)
    benford_tests = [
        ('first_digit_overall', 'First-digit Benford test on all payments'),
        ('first_digit_home_health', 'First-digit Benford test on Home Health payments'),
        ('first_digit_behavioral', 'First-digit Benford test on Behavioral Health payments'),
        ('first_digit_em', 'First-digit Benford test on E&M payments'),
        ('first_digit_dme', 'First-digit Benford test on DME payments'),
        ('first_two_digits_overall', 'First-two-digit Benford test'),
        ('first_two_digits_home_health', 'First-two-digit Benford (Home Health)'),
        ('round_number_overall', 'Round number detection (>30% ending 00)'),
        ('round_number_by_provider', 'Per-provider round number detection'),
        ('duplicate_amounts_overall', 'Duplicate exact payment amounts'),
        ('duplicate_amounts_by_provider', 'Per-provider duplicate amounts'),
        ('payment_clustering_overall', 'Payment amount clustering analysis'),
        ('first_digit_pharmacy', 'First-digit Benford (Pharmacy)'),
        ('first_digit_therapy', 'First-digit Benford (Therapy)'),
        ('first_digit_transport', 'First-digit Benford (Transportation)'),
        ('round_number_home_health', 'Round numbers in Home Health'),
        ('round_number_behavioral', 'Round numbers in Behavioral Health'),
        ('last_digit_uniformity', 'Last-digit uniformity test'),
        ('amount_mode_detection', 'Most frequent payment amount detection'),
        ('suspicious_amount_patterns', 'Suspicious repeating amount patterns'),
    ]
    for test_name, desc in benford_tests:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '1', 'subcategory': '1F',
            'description': desc,
            'method': 'benfords_law',
            'acceptance_criteria': 'chi-squared p < 0.001, >= 100 payment records',
            'analysis_function': 'statistical_analyzer._benfords_law',
            'financial_impact_method': 'total payments from non-conforming providers',
            'parameters': {'test_type': test_name, 'p_threshold': 0.001, 'min_records': 100},
        })

    expected = 90 + len(IQR_METRICS) + (len(HCPCS_CATEGORIES) * 2) + len(benford_tests)
    assert h == expected, f"Category 1: expected {expected}, got {h}"
    return hyps


def gen_category_2():
    """Temporal Anomaly Detection: 120 hypotheses (H0151-H0270)."""
    hyps = []
    h = 150

    # 2A: month-over-month spikes (H0151-H0170)
    spike_configs = [
        (3, 'all', 'All providers, 3x spike'), (5, 'all', 'All providers, 5x spike'),
        (10, 'all', 'All providers, 10x spike'), (3, 'home_health', 'Home health, 3x spike'),
        (5, 'home_health', 'Home health, 5x spike'), (3, 'behavioral', 'Behavioral, 3x spike'),
        (5, 'behavioral', 'Behavioral, 5x spike'), (3, 'dme', 'DME, 3x spike'),
        (3, 'no_bene_increase', 'Spike without bene increase'), (5, 'no_bene_increase', 'Spike without bene increase 5x'),
        (3, 'rate_only', 'Rate-only spike'), (5, 'rate_only', 'Rate-only spike 5x'),
        (3, 'december', 'December spikes 3x'), (5, 'december', 'December spikes 5x'),
        (3, 'covid_onset', 'COVID onset spikes (Mar-Jun 2020)'), (5, 'covid_onset', 'COVID onset 5x'),
        (3, 'new_code', 'New code addition spike'), (3, 'post_2022', 'Post-2022 spike'),
        (10, 'high_value', 'High-value 10x spike (>$100K)'), (3, 'consecutive', 'Consecutive month spikes'),
    ]
    for threshold, filter_type, desc in spike_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '2', 'subcategory': '2A',
            'description': f'Month-over-month billing spike: {desc}',
            'method': 'month_spike',
            'acceptance_criteria': f'ratio > {threshold}x, both months > $10K',
            'analysis_function': 'temporal_analyzer._month_over_month_spike',
            'financial_impact_method': 'spike_month_paid - prior_month_paid',
            'parameters': {'threshold': threshold, 'filter': filter_type, 'min_paid': 10000},
        })

    # 2B: sudden appearance (H0171-H0185)
    appearance_configs = [
        (500000, 'all'), (1000000, 'all'), (250000, 'high_risk_codes'),
        (500000, 'home_health'), (500000, 'behavioral'), (100000, 'p95_threshold'),
        (250000, 'covid_era'), (500000, 'covid_era'), (100000, 'cluster_appearance'),
        (250000, 'cluster_appearance'), (500000, 'dme'), (100000, 'transport'),
        (250000, 'pharmacy'), (1000000, 'any_category'), (500000, 'post_2022'),
    ]
    for threshold, filter_type in appearance_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '2', 'subcategory': '2B',
            'description': f'Sudden provider appearance: first month > ${threshold:,} ({filter_type})',
            'method': 'sudden_appearance',
            'acceptance_criteria': f'first month paid > ${threshold:,}',
            'analysis_function': 'temporal_analyzer._ramp_up',
            'financial_impact_method': 'first 6 months total paid',
            'parameters': {'threshold': threshold, 'filter': filter_type},
        })

    # 2C: sudden disappearance (H0186-H0200)
    disappear_configs = [
        (100000, 12, 'all'), (250000, 12, 'all'), (500000, 12, 'all'),
        (1000000, 12, 'all'), (100000, 24, 'long_active'),
        (250000, 24, 'long_active'), (100000, 12, 'spike_then_vanish'),
        (250000, 12, 'spike_then_vanish'), (500000, 12, 'spike_then_vanish'),
        (100000, 12, 'coordinated'), (250000, 12, 'coordinated'),
        (100000, 12, 'home_health'), (100000, 12, 'behavioral'),
        (100000, 6, 'rapid_exit'), (250000, 6, 'rapid_exit'),
    ]
    for avg_thresh, min_months, filter_type in disappear_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '2', 'subcategory': '2C',
            'description': f'Sudden disappearance: >{min_months}mo, >${avg_thresh:,}/mo avg ({filter_type})',
            'method': 'sudden_disappearance',
            'acceptance_criteria': f'active {min_months}+ months, avg > ${avg_thresh:,}, then stopped',
            'analysis_function': 'temporal_analyzer._abrupt_stop',
            'financial_impact_method': 'last 12 months total paid',
            'parameters': {'avg_threshold': avg_thresh, 'min_months': min_months, 'filter': filter_type},
        })

    # 2D: year-over-year growth (H0201-H0215)
    yoy_configs = [
        (3, 'all'), (5, 'all'), (10, 'all'), (3, 'home_health'), (5, 'home_health'),
        (3, 'behavioral'), (5, 'behavioral'), (3, 'rate_driven'), (5, 'rate_driven'),
        (3, 'sustained_3yr'), (5, 'sustained_3yr'), (10, 'full_period'),
        (3, 'code_expansion'), (5, 'code_expansion'), (3, 'post_covid'),
    ]
    for ratio, filter_type in yoy_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '2', 'subcategory': '2D',
            'description': f'YoY growth > {ratio*100}% ({filter_type})',
            'method': 'yoy_growth',
            'acceptance_criteria': f'annual growth > {ratio}x',
            'analysis_function': 'temporal_analyzer._yoy_growth',
            'financial_impact_method': 'growth_amount above baseline',
            'parameters': {'growth_ratio': ratio, 'filter': filter_type},
        })

    # 2E: seasonal violations (H0216-H0230)
    seasonal_configs = [
        ('flat_in_seasonal', 'Home Health'), ('flat_in_seasonal', 'Behavioral Health'),
        ('flat_in_seasonal', 'E&M'), ('flat_in_seasonal', 'Therapy'),
        ('flat_in_seasonal', 'DME'), ('inverse_seasonality', 'all'),
        ('inverse_seasonality', 'Home Health'), ('uniform_monthly', 'all'),
        ('uniform_monthly', 'high_paid'), ('single_month_dominance', 'all'),
        ('single_month_dominance', 'home_health'), ('cv_extremely_low', 'all'),
        ('cv_extremely_low', 'high_paid'), ('weekend_holiday_billing', 'all'),
        ('quarterly_pattern', 'all'),
    ]
    for pattern, filter_type in seasonal_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '2', 'subcategory': '2E',
            'description': f'Seasonal violation: {pattern} ({filter_type})',
            'method': 'seasonal_violation',
            'acceptance_criteria': 'billing pattern deviates from expected seasonal norm',
            'analysis_function': 'temporal_analyzer._seasonality_anomaly',
            'financial_impact_method': 'total paid from seasonally anomalous providers',
            'parameters': {'pattern': pattern, 'filter': filter_type},
        })

    # 2F: COVID anomalies (H0231-H0245)
    covid_configs = [
        (2, 'all'), (3, 'all'), (5, 'all'),
        (2, 'home_health'), (3, 'home_health'),
        (2, 'behavioral'), (3, 'behavioral'),
        (2, 'non_covid_codes'), (3, 'non_covid_codes'),
        (2, 'dme'), (3, 'dme'),
        (2, 'telehealth_surge'), (3, 'telehealth_surge'),
        (2, 'post_covid_sustained'), (3, 'post_covid_sustained'),
    ]
    for ratio, filter_type in covid_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '2', 'subcategory': '2F',
            'description': f'COVID-period anomaly: >{ratio}x pre-COVID ({filter_type})',
            'method': 'covid_anomaly',
            'acceptance_criteria': f'COVID billing > {ratio}x pre-COVID and > 2x peer COVID growth',
            'analysis_function': 'temporal_analyzer._covid_comparison',
            'financial_impact_method': 'covid_period_paid - pre_covid_annualized',
            'parameters': {'ratio': ratio, 'filter': filter_type},
        })

    # 2G: end-of-year surges (H0246-H0255)
    eoy_configs = [
        (2, 'all'), (3, 'all'), (2, 'home_health'), (3, 'home_health'),
        (2, 'behavioral'), (3, 'behavioral'), (2, 'repeated_years'),
        (3, 'repeated_years'), (2, 'high_value'), (3, 'high_value'),
    ]
    for ratio, filter_type in eoy_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '2', 'subcategory': '2G',
            'description': f'December billing > {ratio}x monthly avg ({filter_type})',
            'method': 'december_surge',
            'acceptance_criteria': f'December paid > {ratio}x average monthly paid',
            'analysis_function': 'temporal_analyzer._december_spike',
            'financial_impact_method': 'december_excess above average',
            'parameters': {'ratio': ratio, 'filter': filter_type},
        })

    # 2H: change-point detection (H0256-H0270)
    cp_configs = [
        ('cusum', 1.0, 'all'), ('cusum', 2.0, 'all'), ('cusum', 5.0, 'all'),
        ('pelt', 1.0, 'all'), ('pelt', 2.0, 'all'), ('pelt', 5.0, 'all'),
        ('cusum', 1.0, 'home_health'), ('cusum', 2.0, 'home_health'),
        ('pelt', 1.0, 'behavioral'), ('cusum', 1.0, 'high_value'),
        ('pelt', 2.0, 'high_value'), ('cusum', 1.0, 'last_12_months'),
        ('pelt', 1.0, 'last_12_months'), ('variance_change', 2.0, 'all'),
        ('variance_change', 3.0, 'all'),
    ]
    for method, ratio, filter_type in cp_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '2', 'subcategory': '2H',
            'description': f'Change-point detection ({method}): post/pre > {ratio}x ({filter_type})',
            'method': 'change_point',
            'acceptance_criteria': f'p < 0.01, post-change mean > {ratio}x pre-change mean',
            'analysis_function': 'temporal_analyzer._change_point_detection',
            'financial_impact_method': 'post_change_total - pre_change_total_annualized',
            'parameters': {'method': method, 'change_ratio': ratio, 'filter': filter_type, 'p_threshold': 0.01},
        })

    assert h == 270, f"Category 2: expected 270, got {h}"
    return hyps


def gen_category_3():
    """Peer Comparison: 130 hypotheses (H0271-H0400)."""
    hyps = []
    h = 270

    # 3A: payment/claim vs peers (H0271-H0300)
    for code in TOP_30_CODES:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '3', 'subcategory': '3A',
            'description': f'Paid per claim > 2x peer median for {code}',
            'method': 'peer_rate',
            'acceptance_criteria': '> 2x peer median, >= 50 claims, >= 30 peers',
            'sql_template': f"""
                WITH code_peers AS (
                    SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY paid_per_claim) AS median_ppc,
                           COUNT(*) AS num_peers
                    FROM provider_hcpcs WHERE hcpcs_code = '{code}' AND claims >= 50
                )
                SELECT ph.billing_npi, ph.paid_per_claim, ph.claims, ph.paid,
                       ph.paid_per_claim / NULLIF(cp.median_ppc, 0) AS ratio, cp.median_ppc
                FROM provider_hcpcs ph CROSS JOIN code_peers cp
                WHERE ph.hcpcs_code = '{code}' AND ph.claims >= 50 AND cp.num_peers >= 30
                  AND ph.paid_per_claim > 2 * cp.median_ppc
                ORDER BY ph.paid DESC LIMIT 50
            """,
            'financial_impact_method': '(provider_rate - peer_median) * claims',
            'parameters': {'hcpcs_code': code, 'ratio_threshold': 2.0, 'min_claims': 50, 'min_peers': 30},
        })

    # 3B: volume vs peers (H0301-H0320)
    for code in TOP_20_CODES:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '3', 'subcategory': '3B',
            'description': f'Total claims > 10x peer median for {code}',
            'method': 'peer_volume',
            'acceptance_criteria': '> 10x peer median, >= 12 months, > $100K',
            'sql_template': f"""
                WITH code_peers AS (
                    SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY claims) AS median_claims
                    FROM provider_hcpcs WHERE hcpcs_code = '{code}' AND months_active >= 12
                )
                SELECT ph.billing_npi, ph.claims, ph.paid, ph.months_active,
                       ph.claims / NULLIF(cp.median_claims, 0) AS ratio
                FROM provider_hcpcs ph CROSS JOIN code_peers cp
                WHERE ph.hcpcs_code = '{code}' AND ph.months_active >= 12 AND ph.paid > 100000
                  AND ph.claims > 10 * cp.median_claims
                ORDER BY ph.paid DESC LIMIT 50
            """,
            'financial_impact_method': '(provider_claims - peer_median_claims) * peer_median_rate',
            'parameters': {'hcpcs_code': code, 'ratio_threshold': 10.0, 'min_months': 12, 'min_paid': 100000},
        })

    # 3C: beneficiary concentration (H0321-H0340)
    for code in TOP_20_CODES:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '3', 'subcategory': '3C',
            'description': f'Claims per bene > 3x peer median for {code}',
            'method': 'peer_concentration',
            'acceptance_criteria': '> 3x peer median, persists 6+ months',
            'analysis_function': 'peer_analyzer._claims_per_bene_vs_median',
            'financial_impact_method': '(excess_claims_per_bene) * peer_rate * beneficiaries',
            'parameters': {'hcpcs_code': code, 'ratio_threshold': 3.0, 'min_months': 6},
        })

    # 3D: geographic peer (H0341-H0360)
    for code in TOP_20_CODES:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '3', 'subcategory': '3D',
            'description': f'Provider exceeds state-level 95th percentile for {code}',
            'method': 'geographic_peer',
            'acceptance_criteria': '> state 95th pct, >= 20 state peers, excess > $50K',
            'analysis_function': 'peer_analyzer._state_peer_comparison',
            'financial_impact_method': '(provider_paid - state_p95) * ratio',
            'parameters': {'hcpcs_code': code, 'percentile': 95, 'min_state_peers': 20, 'min_excess': 50000},
        })

    # 3E: specialty peer (H0361-H0380)
    for specialty in SPECIALTIES:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '3', 'subcategory': '3E',
            'description': f'Provider exceeds specialty 95th percentile ({specialty})',
            'method': 'specialty_peer',
            'acceptance_criteria': f'> {specialty} 95th percentile',
            'analysis_function': 'peer_analyzer._specialty_peer_comparison',
            'financial_impact_method': '(provider_paid - specialty_p95)',
            'parameters': {'specialty': specialty, 'percentile': 95},
        })

    # 3F: size tier mismatch (H0381-H0400)
    size_configs = [
        ('high_paid_low_claims', 'High paid but low claims (extreme rate)'),
        ('high_claims_low_bene', 'High claims but low beneficiaries (high intensity)'),
        ('individual_org_scale', 'Individual NPI billing at organization scale'),
        ('single_code_10m', 'Single HCPCS code with > $10M total'),
        ('all_84_months_increasing', 'Active all 84 months with increasing paid'),
        ('high_paid_few_codes', 'High paid with very few unique codes'),
        ('high_bene_low_paid', 'Many beneficiaries but low total paid'),
        ('extreme_rate_variance', 'Extreme paid-per-claim variance across codes'),
        ('individual_high_network', 'Individual NPI with large servicing network'),
        ('org_single_servicing', 'Organization with only 1 servicing NPI'),
        ('rapid_growth_new', 'New provider with rapid growth to top tier'),
        ('high_paid_single_month', 'High total paid concentrated in single month'),
        ('bene_count_mismatch', 'Beneficiary count inconsistent with claims'),
        ('extreme_avg_per_bene', 'Extreme average paid per beneficiary'),
        ('code_diversity_outlier', 'Unusually many codes for provider type'),
        ('code_homogeneity_outlier', 'Unusually few codes with high paid'),
        ('monthly_volatility_extreme', 'Extreme monthly billing volatility'),
        ('stable_high_billing', 'Unusually stable high-value billing'),
        ('top_decile_all_metrics', 'Top decile on 5+ metrics simultaneously'),
        ('bottom_codes_top_paid', 'Uses rarely-billed codes but has high total paid'),
    ]
    for config_name, desc in size_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '3', 'subcategory': '3F',
            'description': f'Size tier mismatch: {desc}',
            'method': 'size_mismatch',
            'acceptance_criteria': f'Size tier mismatch: {config_name}',
            'analysis_function': 'peer_analyzer._size_tier_mismatch',
            'financial_impact_method': 'total_paid for mismatched providers',
            'parameters': {'mismatch_type': config_name},
        })

    assert h == 400, f"Category 3: expected 400, got {h}"
    return hyps


def gen_category_4():
    """Network Analysis: 120 hypotheses (H0401-H0520)."""
    hyps = []
    h = 400

    # 4A: hub-and-spoke (H0401-H0420)
    hub_configs = [
        (50, 'all', '$0'), (100, 'all', '$0'), (200, 'all', '$0'),
        (50, 'captive_50pct', '$0'), (100, 'captive_50pct', '$0'),
        (20, 'high_value_10m', '$10M'), (20, 'high_value_50m', '$50M'),
        (20, 'high_value_100m', '$100M'), (50, 'new_24mo', '$0'),
        (20, 'rapid_expansion', '$0'), (50, 'home_health', '$0'),
        (50, 'behavioral', '$0'), (100, 'individual_npi', '$0'),
        (50, 'single_code', '$0'), (20, 'multi_state', '$0'),
        (50, 'cross_specialty', '$0'), (100, 'post_2022', '$0'),
        (20, 'all_captive', '$0'), (50, 'high_rate_variance', '$0'),
        (200, 'mega_hub', '$0'),
    ]
    for threshold, filter_type, val_label in hub_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '4', 'subcategory': '4A',
            'description': f'Hub with > {threshold} servicing NPIs ({filter_type})',
            'method': 'hub_spoke',
            'acceptance_criteria': f'> {threshold} servicing NPIs',
            'analysis_function': 'network_analyzer._billing_fan_out',
            'financial_impact_method': 'total payments through hub',
            'parameters': {'min_servicing': threshold, 'filter': filter_type},
        })

    # 4B: shared servicing NPIs (H0421-H0440)
    shared_configs = [
        (10, 'all'), (20, 'all'), (50, 'all'), (10, 'rate_arbitrage'),
        (20, 'rate_arbitrage'), (10, 'duplicate_billing'), (20, 'duplicate_billing'),
        (10, 'multi_state'), (20, 'multi_state'), (50, 'multi_state'),
        (10, 'same_code'), (20, 'same_code'), (10, 'sequential_npis'),
        (10, 'high_volume'), (20, 'high_volume'), (10, 'recent_only'),
        (10, 'home_health'), (10, 'behavioral'), (10, 'transport'),
        (5, 'extreme_rate_spread'),
    ]
    for threshold, filter_type in shared_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '4', 'subcategory': '4B',
            'description': f'Servicing NPI under > {threshold} billers ({filter_type})',
            'method': 'shared_servicing',
            'acceptance_criteria': f'appears under > {threshold} billing NPIs',
            'analysis_function': 'network_analyzer._servicing_fan_in',
            'financial_impact_method': 'total payments to shared NPI',
            'parameters': {'min_billers': threshold, 'filter': filter_type},
        })

    # 4C: circular billing (H0441-H0455)
    circular_configs = [
        (50000, 'bilateral'), (100000, 'bilateral'), (500000, 'bilateral'),
        (50000, 'trilateral'), (100000, 'trilateral'), (50000, 'same_codes'),
        (100000, 'same_codes'), (50000, 'same_month'), (100000, 'same_month'),
        (50000, 'high_frequency'), (100000, 'high_frequency'),
        (50000, 'growing'), (100000, 'growing'), (50000, 'new_relationship'),
        (100000, 'new_relationship'),
    ]
    for threshold, pattern in circular_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '4', 'subcategory': '4C',
            'description': f'Circular billing ({pattern}): > ${threshold:,} both directions',
            'method': 'circular_billing',
            'acceptance_criteria': f'bilateral edge > ${threshold:,} both directions',
            'analysis_function': 'network_analyzer._reciprocal_billing',
            'financial_impact_method': 'total in circular flow',
            'parameters': {'min_paid': threshold, 'pattern': pattern},
        })

    # 4D: network density (H0456-H0470)
    density_configs = [
        (0.5, 'all'), (0.3, 'high_value'), (0.5, 'high_value'),
        (0.3, 'near_clique'), (0.5, 'near_clique'), (0.3, 'star_topology'),
        (0.3, 'chain_topology'), (0.3, 'components_50m'), (0.5, 'components_50m'),
        (0.3, 'small_dense'), (0.5, 'small_dense'), (0.3, 'large_sparse'),
        (0.3, 'recent_formation'), (0.5, 'recent_formation'), (0.3, 'multi_state'),
    ]
    for density, filter_type in density_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '4', 'subcategory': '4D',
            'description': f'Network density > {density} ({filter_type})',
            'method': 'network_density',
            'acceptance_criteria': f'component density > {density}',
            'analysis_function': 'network_analyzer._network_density',
            'financial_impact_method': 'total payments in dense component',
            'parameters': {'min_density': density, 'filter': filter_type},
        })

    # 4E: new network formation (H0471-H0485)
    new_net_configs = [
        (1000000, 12), (5000000, 12), (10000000, 12),
        (1000000, 6), (5000000, 6), (500000, 12),
        (1000000, 24), (500000, 6), (2500000, 12),
        (1000000, 12), (5000000, 12), (500000, 12),
        (2000000, 6), (10000000, 24), (250000, 6),
    ]
    for val_thresh, months in new_net_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '4', 'subcategory': '4E',
            'description': f'New network > ${val_thresh:,} in first {months} months',
            'method': 'new_network',
            'acceptance_criteria': f'> ${val_thresh:,} in first {months} months',
            'analysis_function': 'network_analyzer._new_network_high_paid',
            'financial_impact_method': 'total payments in new network',
            'parameters': {'min_paid': val_thresh, 'max_months': months},
        })

    # 4F: pure billing entities (H0486-H0500)
    pure_configs = [
        (1000000, 5, 'all'), (5000000, 5, 'all'), (10000000, 5, 'all'),
        (1000000, 10, 'all'), (5000000, 10, 'all'),
        (1000000, 5, 'individual_npi'), (5000000, 5, 'individual_npi'),
        (1000000, 5, 'cross_state'), (5000000, 5, 'cross_state'),
        (1000000, 5, 'single_code'), (1000000, 5, 'new_entity'),
        (500000, 3, 'all'), (2500000, 5, 'all'),
        (1000000, 5, 'growing'), (1000000, 5, 'high_rate'),
    ]
    for min_paid, min_serv, filter_type in pure_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '4', 'subcategory': '4F',
            'description': f'Pure billing entity: > ${min_paid:,}, >= {min_serv} servicing ({filter_type})',
            'method': 'pure_billing',
            'acceptance_criteria': f'never servicing, > ${min_paid:,}, >= {min_serv} servicing NPIs',
            'analysis_function': 'network_analyzer._billing_only_providers',
            'financial_impact_method': 'total payments through pure biller',
            'parameters': {'min_paid': min_paid, 'min_servicing': min_serv, 'filter': filter_type},
        })

    # 4G: ghost network detection (H0501-H0520)
    ghost_configs = [
        ('single_biller', 500000, 6), ('single_biller', 1000000, 6),
        ('single_biller', 500000, 3), ('no_nppes', 500000, 12),
        ('no_nppes', 100000, 6), ('deactivated_npi', 100000, 12),
        ('identical_pattern', 0, 12), ('sequential_npi', 0, 12),
        ('batch_creation_5', 0, 1), ('batch_creation_10', 0, 1),
        ('short_lived', 500000, 6), ('short_lived', 250000, 3),
        ('mirror_billing', 0, 12), ('phantom_address', 0, 12),
        ('ghost_composite_3plus', 0, 12), ('single_biller_high', 2000000, 6),
        ('rapid_billing', 1000000, 3), ('no_independent_billing', 500000, 12),
        ('concentrated_codes', 500000, 6), ('ghost_network_cluster', 0, 12),
    ]
    for indicator, min_paid, max_months in ghost_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '4', 'subcategory': '4G',
            'description': f'Ghost network indicator: {indicator}',
            'method': 'ghost_network',
            'acceptance_criteria': f'ghost indicator: {indicator}',
            'analysis_function': 'network_analyzer._ghost_provider_indicators',
            'financial_impact_method': 'total payments to ghost provider',
            'parameters': {'indicator': indicator, 'min_paid': min_paid, 'max_months': max_months},
        })

    assert h == 520, f"Category 4: expected 520, got {h}"
    return hyps


def gen_category_5():
    """Concentration and Market Power: 80 hypotheses (H0521-H0600)."""
    hyps = []
    h = 520

    # 5A: provider dominance (H0521-H0540)
    dom_configs = [
        (0.3, 'all'), (0.5, 'all'), (0.8, 'all'),
        (0.3, 'dominant_and_expensive'), (0.5, 'dominant_and_expensive'),
        (0.3, 'new_entrant'), (0.5, 'new_entrant'),
        (0.3, 'individual_npi'), (0.5, 'individual_npi'),
        (0.3, 'home_health'), (0.5, 'home_health'),
        (0.3, 'behavioral'), (0.5, 'behavioral'),
        (0.3, 'dme'), (0.5, 'dme'),
        (0.3, 'pharmacy'), (0.3, 'transport'),
        (0.3, 'therapy'), (0.8, 'any_category'),
        (0.3, 'growing_share'),
    ]
    for share, filter_type in dom_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '5', 'subcategory': '5A',
            'description': f'Provider with > {share*100:.0f}% share of code spending ({filter_type})',
            'method': 'provider_dominance',
            'acceptance_criteria': f'> {share*100:.0f}% of national code spending',
            'analysis_function': 'concentration_analyzer._provider_share_per_code',
            'financial_impact_method': 'total spending by dominant provider',
            'parameters': {'share_threshold': share, 'filter': filter_type},
        })

    # 5B: single-code specialists (H0541-H0555)
    single_configs = [
        (0.9, 1000000, 'all'), (0.95, 1000000, 'all'), (0.99, 1000000, 'all'),
        (0.9, 5000000, 'all'), (0.95, 5000000, 'all'),
        (0.9, 1000000, 'home_health'), (0.9, 1000000, 'behavioral'),
        (0.9, 1000000, 'personal_care'), (0.9, 1000000, 'dme'),
        (0.9, 1000000, 'transport'), (0.9, 500000, 'individual_npi'),
        (0.95, 500000, 'individual_npi'), (0.9, 1000000, 'pharmacy'),
        (0.9, 1000000, 'therapy'), (0.9, 10000000, 'any'),
    ]
    for pct, min_rev, filter_type in single_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '5', 'subcategory': '5B',
            'description': f'> {pct*100:.0f}% revenue from one code, > ${min_rev:,} ({filter_type})',
            'method': 'single_code',
            'acceptance_criteria': f'> {pct*100:.0f}% revenue from single code, total > ${min_rev:,}',
            'analysis_function': 'concentration_analyzer._code_concentration_per_provider',
            'financial_impact_method': 'total revenue from concentrated code',
            'parameters': {'pct_threshold': pct, 'min_revenue': min_rev, 'filter': filter_type},
        })

    # 5C: HHI concentration (H0556-H0570)
    hhi_configs = [
        (2500, 'all'), (5000, 'all'), (7500, 'all'),
        (2500, 'top5_gt_50pct'), (2500, 'top3_gt_50pct'),
        (2500, 'home_health'), (2500, 'behavioral'), (2500, 'dme'),
        (2500, 'transport'), (2500, 'pharmacy'),
        (2500, 'high_spending_codes'), (5000, 'high_spending_codes'),
        (2500, 'increasing_hhi'), (2500, 'single_dominant'),
        (2500, 'new_monopoly'),
    ]
    for hhi_thresh, filter_type in hhi_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '5', 'subcategory': '5C',
            'description': f'HHI > {hhi_thresh} for HCPCS code ({filter_type})',
            'method': 'hhi_concentration',
            'acceptance_criteria': f'HHI > {hhi_thresh}',
            'analysis_function': 'concentration_analyzer._hhi_per_code',
            'financial_impact_method': 'excess spending above competitive market estimate',
            'parameters': {'hhi_threshold': hhi_thresh, 'filter': filter_type},
        })

    # 5D: geographic monopolies (H0571-H0585)
    geo_configs = [
        (0.4, 'all'), (0.6, 'all'), (0.8, 'all'),
        (0.4, 'home_health'), (0.4, 'behavioral'),
        (0.4, 'dme'), (0.4, 'transport'),
        (0.4, 'small_states'), (0.6, 'small_states'),
        (0.4, 'large_states'), (0.4, 'growing_share'),
        (0.4, 'individual_npi'), (0.6, 'individual_npi'),
        (0.4, 'high_spending'), (0.4, 'new_monopoly'),
    ]
    for share, filter_type in geo_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '5', 'subcategory': '5D',
            'description': f'Geographic monopoly: > {share*100:.0f}% state-level share ({filter_type})',
            'method': 'geographic_monopoly',
            'acceptance_criteria': f'> {share*100:.0f}% of state spending for a code',
            'analysis_function': 'concentration_analyzer._state_level_share',
            'financial_impact_method': 'monopoly premium estimate',
            'parameters': {'share_threshold': share, 'filter': filter_type},
        })

    # 5E: temporal concentration (H0586-H0600)
    temp_conc_configs = [
        (0.4, 1, 'all'), (0.4, 2, 'all'), (0.5, 1, 'all'),
        (0.4, 1, 'home_health'), (0.4, 1, 'behavioral'),
        (0.4, 1, 'dme'), (0.4, 1, 'repeated_years'),
        (0.5, 1, 'repeated_years'), (0.4, 1, 'december_concentrated'),
        (0.4, 1, 'quarter_concentrated'), (0.6, 1, 'all'),
        (0.4, 1, 'high_value'), (0.5, 2, 'high_value'),
        (0.4, 1, 'growing'), (0.4, 1, 'new_providers'),
    ]
    for share, months, filter_type in temp_conc_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '5', 'subcategory': '5E',
            'description': f'> {share*100:.0f}% annual revenue in {months} month(s) ({filter_type})',
            'method': 'temporal_concentration',
            'acceptance_criteria': f'> {share*100:.0f}% of annual revenue in {months} month(s)',
            'analysis_function': 'concentration_analyzer._temporal_revenue_concentration',
            'financial_impact_method': 'concentrated revenue amount',
            'parameters': {'share_threshold': share, 'max_months': months, 'filter': filter_type},
        })

    assert h == 600, f"Category 5: expected 600, got {h}"
    return hyps


def gen_category_6():
    """Classical ML: 150 hypotheses (H0601-H0750)."""
    hyps = []
    h = 600

    # 6A: Isolation Forest (H0601-H0640)
    segments = ['overall'] * 10 + ['home_health'] * 10 + ['behavioral'] * 10 + ['high_volume'] * 10
    for i, seg in enumerate(segments):
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '6', 'subcategory': '6A',
            'description': f'Isolation Forest anomaly #{i+1} ({seg})',
            'method': 'isolation_forest',
            'acceptance_criteria': 'anomaly score in top 1%, total paid > $100K, anomalous on 2+ features',
            'analysis_function': 'ml_pipeline.isolation_forest',
            'financial_impact_method': 'total_paid for anomalous provider',
            'parameters': {'segment': seg, 'contamination': 0.01, 'rank': i + 1},
        })

    # 6B: DBSCAN (H0641-H0670)
    for i in range(30):
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '6', 'subcategory': '6B',
            'description': f'DBSCAN noise/small cluster anomaly #{i+1}',
            'method': 'dbscan',
            'acceptance_criteria': 'cluster=-1 or cluster size <= 3',
            'analysis_function': 'ml_pipeline.dbscan',
            'financial_impact_method': 'total_paid for noise provider',
            'parameters': {'eps': 2.0, 'min_samples': 10, 'rank': i + 1},
        })

    # 6C: Random Forest (H0671-H0690)
    for i in range(20):
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '6', 'subcategory': '6C',
            'description': f'Random Forest top feature importance anomaly #{i+1}',
            'method': 'random_forest',
            'acceptance_criteria': 'extreme tail of top importance feature',
            'analysis_function': 'ml_pipeline.random_forest_importance',
            'financial_impact_method': 'total_paid for extreme-feature provider',
            'parameters': {'rank': i + 1},
        })

    # 6D: XGBoost (H0691-H0720)
    for i in range(30):
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '6', 'subcategory': '6D',
            'description': f'XGBoost semi-supervised novel finding #{i+1}',
            'method': 'xgboost',
            'acceptance_criteria': 'probability > 0.8, total paid > $100K, not in Categories 1-4',
            'analysis_function': 'ml_pipeline.xgboost_semisupervised',
            'financial_impact_method': 'total_paid for novel high-probability provider',
            'parameters': {'min_prob': 0.8, 'min_paid': 100000, 'rank': i + 1},
        })

    # 6E: K-means (H0721-H0735)
    for i in range(15):
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '6', 'subcategory': '6E',
            'description': f'K-means distance outlier #{i+1}',
            'method': 'kmeans',
            'acceptance_criteria': 'distance > 3x cluster mean distance',
            'analysis_function': 'ml_pipeline.kmeans_outlier',
            'financial_impact_method': 'total_paid for distance outlier',
            'parameters': {'k': 20, 'distance_multiplier': 3.0, 'rank': i + 1},
        })

    # 6F: LOF (H0736-H0750)
    for i in range(15):
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '6', 'subcategory': '6F',
            'description': f'Local Outlier Factor anomaly #{i+1}',
            'method': 'lof',
            'acceptance_criteria': 'LOF score > 2.0',
            'analysis_function': 'ml_pipeline.lof',
            'financial_impact_method': 'total_paid * lof_score',
            'parameters': {'n_neighbors': 20, 'min_lof': 2.0, 'rank': i + 1},
        })

    assert h == 750, f"Category 6: expected 750, got {h}"
    return hyps


def gen_category_7():
    """Deep Learning: 80 hypotheses (H0751-H0830)."""
    hyps = []
    h = 750

    # 7A: Autoencoder (H0751-H0780)
    segments = ['overall'] * 10 + ['home_health'] * 10 + ['behavioral'] * 10
    for i, seg in enumerate(segments):
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '7', 'subcategory': '7A',
            'description': f'Autoencoder reconstruction error anomaly #{i+1} ({seg})',
            'method': 'autoencoder',
            'acceptance_criteria': 'reconstruction error in top 1%, total paid > $100K',
            'analysis_function': 'dl_pipeline.autoencoder',
            'financial_impact_method': 'total_paid for high-error provider',
            'parameters': {'segment': seg, 'rank': i + 1},
        })

    # 7B: VAE (H0781-H0800)
    for i in range(20):
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '7', 'subcategory': '7B',
            'description': f'VAE anomaly #{i+1} (not in autoencoder top)',
            'method': 'vae',
            'acceptance_criteria': 'VAE score in top 1%, not already flagged by AE',
            'analysis_function': 'dl_pipeline.vae',
            'financial_impact_method': 'total_paid for VAE-novel provider',
            'parameters': {'rank': i + 1},
        })

    # 7C: LSTM (H0801-H0815)
    for i in range(15):
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '7', 'subcategory': '7C',
            'description': f'LSTM temporal prediction error anomaly #{i+1}',
            'method': 'lstm',
            'acceptance_criteria': 'MAE > 3x population mean, >= 24 months, > $200K',
            'analysis_function': 'dl_pipeline.lstm',
            'financial_impact_method': 'total_paid for temporally anomalous provider',
            'parameters': {'mae_multiplier': 3.0, 'min_months': 24, 'min_paid': 200000, 'rank': i + 1},
        })

    # 7D: Transformer (H0816-H0830)
    for i in range(15):
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '7', 'subcategory': '7D',
            'description': f'Transformer attention concentration anomaly #{i+1}',
            'method': 'transformer',
            'acceptance_criteria': 'attention concentration > 3x uniform',
            'analysis_function': 'dl_pipeline.transformer_attention',
            'financial_impact_method': 'total_paid for attention-anomalous provider',
            'parameters': {'concentration_threshold': 3.0, 'rank': i + 1},
        })

    assert h == 830, f"Category 7: expected 830, got {h}"
    return hyps


def gen_category_8():
    """Domain-Specific Red Flags: 100 hypotheses (H0831-H0930)."""
    hyps = []
    h = 830

    # 8A: impossible volumes (H0831-H0845)
    for code, unit_min, max_units in TIMED_CODES:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '8', 'subcategory': '8A',
            'description': f'Impossible volume: {code} > {max_units} units/bene/month',
            'method': 'impossible_volume',
            'acceptance_criteria': f'claims/bene exceeds physical max of {max_units}',
            'sql_template': f"""
                SELECT billing_npi, claim_month, claims, beneficiaries, paid,
                       claims * 1.0 / NULLIF(beneficiaries, 0) AS claims_per_bene
                FROM claims WHERE hcpcs_code = '{code}' AND beneficiaries > 0
                  AND claims * 1.0 / beneficiaries > {max_units} AND paid > 10000
                ORDER BY paid DESC LIMIT 50
            """,
            'financial_impact_method': '100% of payments above physical maximum',
            'parameters': {'hcpcs_code': code, 'unit_minutes': unit_min, 'max_units': max_units},
        })

    # 8B: upcoding (H0846-H0860)
    upcode_configs = [
        ('office_established', '99215', 2.0), ('office_established', '99215', 3.0),
        ('office_established', '99214', 2.0), ('office_new', '99205', 2.0),
        ('office_new', '99205', 3.0), ('office_new', '99204', 2.0),
        ('ed_visit', '99285', 2.0), ('ed_visit', '99285', 3.0),
        ('ed_visit', '99284', 2.0),
        ('level_distribution_skew', 'highest', 2.0),
        ('level_distribution_skew', 'highest', 3.0),
        ('progressive_upcoding', 'increasing_level', 0),
        ('state_comparison_upcode', '99215', 2.0),
        ('specialty_comparison_upcode', '99215', 2.0),
        ('new_provider_upcoding', '99215', 2.0),
    ]
    for family_or_type, code_or_level, ratio in upcode_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '8', 'subcategory': '8B',
            'description': f'Upcoding: {family_or_type} {code_or_level} > {ratio}x peer ratio',
            'method': 'upcoding',
            'acceptance_criteria': f'highest-level code ratio > {ratio}x peer median',
            'analysis_function': 'domain_rules.upcoding',
            'financial_impact_method': 'excess_claims * (high_code_rate - appropriate_code_rate)',
            'parameters': {'family': family_or_type, 'target_code': code_or_level, 'ratio': ratio},
        })

    # 8C: unbundling (H0861-H0875)
    unbundle_configs = [
        ('codes_per_bene_3x', 'all'), ('codes_per_bene_3x', 'home_health'),
        ('codes_per_bene_3x', 'behavioral'), ('codes_per_bene_5x', 'all'),
        ('codes_per_bene_3x', 'high_value'), ('component_vs_bundle', 'lab_panels'),
        ('component_vs_bundle', 'therapy_evals'), ('component_vs_bundle', 'em_addons'),
        ('sequential_codes_same_day', 'all'), ('sequential_codes_same_day', 'therapy'),
        ('modifier_abuse', 'all'), ('fragmented_billing', 'all'),
        ('fragmented_billing', 'home_health'), ('excessive_distinct_codes', 'all'),
        ('excessive_distinct_codes', 'individual'),
    ]
    for pattern, filter_type in unbundle_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '8', 'subcategory': '8C',
            'description': f'Unbundling: {pattern} ({filter_type})',
            'method': 'unbundling',
            'acceptance_criteria': f'unbundling pattern: {pattern}',
            'analysis_function': 'domain_rules.unbundling',
            'financial_impact_method': 'estimated bundled rate vs sum of components',
            'parameters': {'pattern': pattern, 'filter': filter_type},
        })

    # 8D: high-risk categories (H0876-H0890)
    risk_configs = [
        ('Home Health', 'rate_outlier'), ('Home Health', 'volume_outlier'),
        ('Home Health', 'network_anomaly'), ('Behavioral Health', 'rate_outlier'),
        ('Behavioral Health', 'volume_outlier'), ('Behavioral Health', 'network_anomaly'),
        ('Personal Care', 'rate_outlier'), ('Personal Care', 'volume_outlier'),
        ('DME', 'rate_outlier'), ('DME', 'volume_outlier'),
        ('ABA Therapy', 'rate_outlier'), ('Transportation', 'rate_outlier'),
        ('Transportation', 'volume_outlier'), ('Pharmacy', 'rate_outlier'),
        ('Pharmacy', 'volume_outlier'),
    ]
    for category, red_flag in risk_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '8', 'subcategory': '8D',
            'description': f'High-risk {category} with {red_flag}',
            'method': 'high_risk_category',
            'acceptance_criteria': f'top 1% in {category} + {red_flag}',
            'analysis_function': 'domain_rules.high_risk_category',
            'financial_impact_method': 'excess above category peer median',
            'parameters': {'category': category, 'red_flag': red_flag},
        })

    # 8E-8G: phantom billing, adjustment anomalies, duplicates (H0891-H0930)
    misc_configs = [
        ('phantom_constant_bene', 'Constant beneficiary count with growing claims'),
        ('phantom_flat_bene_growing_claims', 'Flat beneficiaries but claims increase > 50%'),
        ('phantom_identical_monthly', 'Identical billing amounts every month'),
        ('phantom_round_bene_counts', 'Round number beneficiary counts'),
        ('phantom_no_variance', 'Zero variance in monthly claims'),
        ('phantom_sequential_claims', 'Sequential claim patterns'),
        ('phantom_weekend_billing', 'Excessive weekend/holiday billing'),
        ('phantom_telehealth_volume', 'Impossible telehealth volumes'),
        ('phantom_deceased_bene', 'Claims for potentially deceased beneficiaries'),
        ('phantom_generic_pattern', 'Generic phantom billing pattern'),
        ('adjustment_20pct_negative', 'Negative payments > 20% of positive'),
        ('adjustment_30pct_negative', 'Negative payments > 30% of positive'),
        ('adjustment_increasing_negative', 'Increasing negative payment share over time'),
        ('adjustment_large_single', 'Single large negative adjustment > $500K'),
        ('adjustment_pattern_reversal', 'Pattern of bill-then-reverse'),
        ('adjustment_year_end', 'Year-end adjustment concentration'),
        ('adjustment_negative_net', 'Net negative total paid'),
        ('adjustment_selective_codes', 'Adjustments concentrated in specific codes'),
        ('adjustment_post_audit', 'Adjustment patterns suggesting audit response'),
        ('adjustment_growing_reversals', 'Growing reversal rate over time'),
        ('duplicate_same_biller_code_month', 'Same biller+code+month multiple servicing'),
        ('duplicate_overlapping_billers', 'Overlapping billers for same servicing NPI'),
        ('duplicate_identical_amounts', 'Identical payment amounts multiple times'),
        ('duplicate_same_day_same_bene', 'Same beneficiary billed by multiple providers'),
        ('duplicate_sequential_claims', 'Sequential duplicate claim patterns'),
        ('duplicate_cross_state', 'Same NPI billed in multiple states same month'),
        ('duplicate_code_splitting', 'Same service split across code variants'),
        ('duplicate_biller_servicing_same', 'Duplicate where billing=servicing'),
        ('duplicate_high_frequency', 'High-frequency duplicate patterns'),
        ('duplicate_growing', 'Growing duplicate rate over time'),
        ('phantom_composite', 'Composite phantom billing score > 3'),
        ('adjustment_composite', 'Composite adjustment anomaly score > 3'),
        ('duplicate_composite', 'Composite duplicate billing score > 3'),
        ('fraud_triangle', 'Pressure+opportunity+rationalization indicators'),
        ('organized_scheme', 'Coordinated phantom+adjustment+duplicate'),
        ('escalating_fraud', 'Escalating pattern across all indicators'),
        ('new_provider_red_flags', 'New provider with multiple domain red flags'),
        ('high_risk_composite', 'High-risk category + domain red flag composite'),
        ('exit_scam_pattern', 'Bill-spike-vanish pattern'),
        ('regulatory_arbitrage', 'Potential regulatory arbitrage across states'),
    ]
    for config, desc in misc_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '8', 'subcategory': '8E' if 'phantom' in config else ('8F' if 'adjustment' in config else '8G'),
            'description': desc,
            'method': config.split('_')[0],
            'acceptance_criteria': desc,
            'analysis_function': f'domain_rules.{config}',
            'financial_impact_method': 'total flagged payments',
            'parameters': {'rule': config},
        })

    assert h == 930, f"Category 8: expected 930, got {h}"
    return hyps


def gen_category_9():
    """Cross-Reference and Enrichment: 70 hypotheses (H0931-H1000)."""
    hyps = []
    h = 930

    # 9A: specialty mismatch (H0931-H0950)
    mismatch_configs = [
        ('Podiatrist', 'behavioral_codes'), ('Dentist', 'home_health_codes'),
        ('Optometrist', 'behavioral_codes'), ('Chiropractor', 'behavioral_codes'),
        ('Physical Therapist', 'pharmacy_codes'), ('Dermatology', 'behavioral_codes'),
        ('Pediatrics', 'geriatric_codes'), ('Psychiatrist', 'surgical_codes'),
        ('any_specialty', 'mismatch_50pct'), ('any_specialty', 'mismatch_75pct'),
        ('any_specialty', 'mismatch_90pct'), ('individual', 'org_specialty_mismatch'),
        ('organization', 'individual_specialty_codes'), ('primary_care', 'specialty_codes'),
        ('surgical', 'behavioral_codes'), ('anesthesiology', 'home_health_codes'),
        ('radiology', 'therapy_codes'), ('emergency', 'chronic_care_codes'),
        ('nursing', 'surgical_codes'), ('pharmacy', 'em_codes'),
    ]
    for specialty, mismatch_type in mismatch_configs:
        h += 1
        hyps.append({
            'id': f'H{h:04d}', 'category': '9', 'subcategory': '9A',
            'description': f'Specialty mismatch: {specialty} billing {mismatch_type}',
            'method': 'specialty_mismatch',
            'acceptance_criteria': f'> 50% claims outside expected codes for {specialty}',
            'analysis_function': 'crossref.specialty_mismatch',
            'financial_impact_method': 'total mismatched payments',
            'parameters': {'specialty': specialty, 'mismatch_type': mismatch_type},
        })

    # 9B-9F: entity type, geographic, deactivated, state, address (H0951-H1000)
    crossref_configs = [
        ('entity_individual_high_5m', 'Individual NPI > $5M total paid'),
        ('entity_individual_high_10m', 'Individual NPI > $10M total paid'),
        ('entity_individual_high_50m', 'Individual NPI > $50M total paid'),
        ('entity_individual_network', 'Individual NPI with > 20 servicing NPIs'),
        ('entity_individual_multi_code', 'Individual billing > 50 distinct codes'),
        ('entity_org_single_npi', 'Organization with single servicing NPI'),
        ('entity_org_no_nppes', 'Organization NPI not in NPPES'),
        ('geo_multi_state_3', 'Servicing NPI in > 3 states same month'),
        ('geo_multi_state_5', 'Servicing NPI in > 5 states same month'),
        ('geo_multi_state_10', 'Servicing NPI in > 10 states same month'),
        ('geo_distant_billing', 'Billing and servicing NPIs in distant states'),
        ('geo_cluster_same_zip', 'Multiple flagged NPIs at same zip code'),
        ('deactivated_still_billing', 'Deactivated NPI still billing'),
        ('excluded_provider', 'Provider on OIG exclusion list still billing'),
        ('no_nppes_record', 'NPI not found in NPPES registry'),
        ('no_nppes_high_billing', 'No NPPES record with > $1M billing'),
        ('state_spending_2x', 'State per-code spending > 2x national median'),
        ('state_spending_3x', 'State per-code spending > 3x national median'),
        ('state_spending_5x', 'State per-code spending > 5x national median'),
        ('state_growth_outlier', 'State spending growth > 3x national growth'),
        ('state_bene_cost_outlier', 'State per-beneficiary cost > 2x national'),
        ('address_cluster_5', '5+ NPIs at same NPPES address'),
        ('address_cluster_10', '10+ NPIs at same NPPES address'),
        ('address_cluster_anomalous', 'Address cluster with combined anomalous billing'),
        ('address_residential', 'High-billing NPI at residential address'),
        ('address_po_box', 'High-billing NPI at PO Box'),
        ('address_virtual_office', 'High-billing NPI at virtual office address'),
        ('taxonomy_change', 'Provider changed taxonomy code during period'),
        ('multiple_taxonomies', 'Provider with multiple active taxonomies'),
        ('name_similarity', 'Multiple NPIs with similar names same address'),
        ('phone_cluster', 'Multiple NPIs sharing phone number'),
        ('recently_enrolled', 'Recently enrolled provider with high immediate billing'),
        ('rural_urban_mismatch', 'Urban-specialty provider billing rural codes'),
        ('facility_type_mismatch', 'Facility type inconsistent with billing codes'),
        ('cross_program_billing', 'Same NPI billing both Medicare and Medicaid anomalously'),
        ('ownership_change', 'Provider ownership change followed by billing spike'),
        ('licensure_gap', 'Billing during licensure gap period'),
        ('sanctions_history', 'Provider with prior sanctions or penalties'),
        ('related_entity', 'Related entities with combined anomalous billing'),
        ('beneficial_ownership', 'Beneficial ownership links to excluded providers'),
        ('cross_state_billing', 'Billing in state different from NPPES registration'),
        ('inactive_address', 'Billing from address no longer active'),
        ('mail_drop_address', 'Billing from known mail drop location'),
        ('foreign_address', 'Provider with foreign NPPES address'),
        ('duplicate_npi', 'Multiple NPIs resolving to same provider'),
        ('shell_company_indicators', 'Shell company indicators (recent formation, minimal info)'),
        ('nominee_provider', 'Nominee provider indicators'),
        ('layered_billing', 'Multiple billing layers between patient and payer'),
        ('billing_address_change', 'Frequent billing address changes'),
        ('credential_verification', 'Credentials not verifiable through external sources'),
    ]
    for config, desc in crossref_configs:
        h += 1
        sub = '9B' if 'entity' in config else ('9C' if 'geo' in config else ('9D' if 'deactivated' in config or 'excluded' in config or 'no_nppes' in config else ('9E' if 'state' in config else '9F')))
        hyps.append({
            'id': f'H{h:04d}', 'category': '9', 'subcategory': sub,
            'description': desc,
            'method': 'crossref',
            'acceptance_criteria': desc,
            'analysis_function': f'crossref.{config}',
            'financial_impact_method': 'total payments to flagged provider',
            'parameters': {'rule': config},
        })

    assert h == 1000, f"Category 9: expected 1000, got {h}"
    return hyps


# ---------------------------------------------------------------------------
# Gap Analysis Hypotheses (H1001-H1100) — 10 new batches
# ---------------------------------------------------------------------------

# ABA therapy HCPCS codes
ABA_CODES = [
    '97151', '97152', '97153', '97154', '97155', '97156', '97157', '97158',
    'H0031', 'H0032', '0362T', '0373T', '0374T',
]

# Federal holidays (month-day)
FEDERAL_HOLIDAYS = [
    '01-01', '07-04', '12-25', '11-25', '11-26',  # NYD, July4, Christmas, Thanksgiving±
]


def gen_gap_batch_1():
    """Batch 1: ABA Therapy Fraud — 15 hypotheses (H1001-H1015)."""
    hyps = []
    h = 1000
    aba_code_list = ','.join(f"'{c}'" for c in ABA_CODES)

    configs = [
        ('H1001', 'Provider billing >32 units (8hr) of ABA per beneficiary per day',
         'impossible_aba_volume', 'claims_per_bene > 32 in single month for ABA codes',
         {'check': 'units_per_bene_per_day', 'threshold': 32}),
        ('H1002', 'Provider billing ABA on federal holidays',
         'aba_holiday_billing', 'ABA claims on known federal holidays',
         {'check': 'holiday_billing', 'holidays': FEDERAL_HOLIDAYS}),
        ('H1003', 'Provider with >90% revenue from ABA codes and total >$1M',
         'aba_concentration', '>90% revenue from ABA codes, total >$1M',
         {'pct_threshold': 0.9, 'min_revenue': 1000000}),
        ('H1004', 'ABA provider with claims_per_bene >3x state peer median',
         'aba_peer_cpb', 'claims_per_bene >3x state peer median for ABA',
         {'ratio_threshold': 3.0, 'peer_level': 'state'}),
        ('H1005', 'ABA provider rate (paid_per_claim) >2x state peer median',
         'aba_peer_rate', 'paid_per_claim >2x state peer median for ABA',
         {'ratio_threshold': 2.0, 'peer_level': 'state'}),
        ('H1006', 'ABA provider active <12 months with total >$500K (rapid entrant)',
         'aba_rapid_entrant', 'active <12 months, total >$500K in ABA',
         {'max_months': 12, 'min_revenue': 500000}),
        ('H1007', 'ABA provider billing more than 6 distinct beneficiaries per day (impossible caseload)',
         'aba_impossible_caseload', '>6 distinct beneficiaries per day for ABA',
         {'max_bene_per_day': 6}),
        ('H1008', 'ABA provider with zero supervision codes alongside high treatment volume',
         'aba_no_supervision', 'High ABA treatment volume with zero 97155/97156 supervision codes',
         {'supervision_codes': ['97155', '97156']}),
        ('H1009', 'ABA provider billing in multiple states same month',
         'aba_multi_state', 'ABA provider in >1 state same month',
         {'min_states': 2}),
        ('H1010', 'ABA provider with month-over-month growth >5x',
         'aba_spike', 'ABA billing month-over-month >5x',
         {'growth_threshold': 5.0}),
        ('H1011', 'ABA provider where billing NPI is individual but bills at organization volume',
         'aba_individual_org_volume', 'Individual NPI ABA billing >$500K',
         {'min_paid': 500000, 'entity_type': '1'}),
        ('H1012', 'ABA billing network with >10 servicing NPIs, all started same month (batch creation)',
         'aba_batch_creation', '>10 ABA servicing NPIs starting same month',
         {'min_servicing': 10}),
        ('H1013', 'ABA provider with identical beneficiary count every month (phantom pattern)',
         'aba_phantom_pattern', 'ABA bene count CV < 0.05 across 12+ months',
         {'max_bene_cv': 0.05, 'min_months': 12}),
        ('H1014', 'ABA provider in Florida billing during moratorium period',
         'aba_florida_moratorium', 'Florida ABA billing during moratorium',
         {'state': 'FL'}),
        ('H1015', 'ABA provider with >$10M total and only 1-2 HCPCS codes',
         'aba_code_concentration', '>$10M ABA from <=2 codes',
         {'min_revenue': 10000000, 'max_codes': 2}),
    ]

    for h_id, desc, method, criteria, params in configs:
        h += 1
        params['aba_codes'] = ABA_CODES
        hyps.append({
            'id': h_id, 'category': '8', 'subcategory': '8H',
            'description': desc,
            'method': method,
            'acceptance_criteria': criteria,
            'analysis_function': f'domain_rules.{method}',
            'financial_impact_method': 'total flagged ABA payments',
            'parameters': params,
        })

    assert h == 1015, f"Gap Batch 1: expected 1015, got {h}"
    return hyps


def gen_gap_batch_2():
    """Batch 2: Impossible Provider-Day Detection — 10 hypotheses (H1016-H1025)."""
    hyps = []
    h = 1015

    configs = [
        ('H1016', 'Provider billing >24 hours of timed services in a single day (all codes combined)',
         'impossible_provider_day_24h', 'total timed units across all benes exceed 24hr/day',
         {'max_hours': 24, 'scope': 'all_codes'}),
        ('H1017', 'Provider billing >16 hours of timed services per day, sustained >30 days/month',
         'impossible_sustained_16h', '>16hr/day for >30 days/month',
         {'max_hours': 16, 'min_days': 30}),
        ('H1018', 'Individual NPI billing >480 total 15-min units across all beneficiaries per day',
         'impossible_units_per_day', '>480 15-min units/day across all benes',
         {'max_units': 480, 'unit_minutes': 15}),
        ('H1019', 'Provider billing >12 hours per day of psychotherapy (90834/90837)',
         'impossible_psychotherapy_day', '>12hr/day psychotherapy',
         {'max_hours': 12, 'codes': ['90834', '90837']}),
        ('H1020', 'Provider billing >20 E&M visits per day (99213-99215)',
         'impossible_em_visits_day', '>20 E&M visits/day',
         {'max_visits': 20, 'codes': ['99213', '99214', '99215']}),
        ('H1021', 'Provider billing home health visits to >15 distinct beneficiaries per day',
         'impossible_home_health_day', '>15 home health benes/day',
         {'max_bene_per_day': 15, 'category': 'home_health'}),
        ('H1022', 'Provider with claims implying >365 service days in a year',
         'impossible_service_days', '>365 service days/year',
         {'max_days': 365}),
        ('H1023', 'Provider billing concurrent services (two timed codes overlapping) same beneficiary',
         'concurrent_services', 'overlapping timed codes same bene',
         {'check': 'concurrent'}),
        ('H1024', 'Servicing NPI appearing in >2 billing NPIs same day with combined >16 hours',
         'servicing_multi_biller_day', '>2 billers same day, combined >16hr',
         {'max_billers': 2, 'max_hours': 16}),
        ('H1025', 'Provider billing 7 days/week for >6 consecutive months',
         'no_days_off', '7 days/week sustained >6 months',
         {'min_months': 6}),
    ]

    for h_id, desc, method, criteria, params in configs:
        h += 1
        hyps.append({
            'id': h_id, 'category': '8', 'subcategory': '8I',
            'description': desc,
            'method': method,
            'acceptance_criteria': criteria,
            'analysis_function': f'domain_rules.{method}',
            'financial_impact_method': '100% of payments above physical capacity',
            'parameters': params,
        })

    assert h == 1025, f"Gap Batch 2: expected 1025, got {h}"
    return hyps


def gen_gap_batch_3():
    """Batch 3: LEIE & Excluded Provider Cross-Reference — 10 hypotheses (H1026-H1035)."""
    hyps = []
    h = 1025

    configs = [
        ('H1026', 'Billing NPI found on OIG LEIE exclusion list',
         'leie_billing_npi', 'billing NPI matches LEIE excluded provider',
         {'check': 'billing_npi', 'source': 'LEIE'}),
        ('H1027', 'Servicing NPI found on OIG LEIE exclusion list',
         'leie_servicing_npi', 'servicing NPI matches LEIE excluded provider',
         {'check': 'servicing_npi', 'source': 'LEIE'}),
        ('H1028', 'Billing NPI with same name/address as excluded individual',
         'leie_name_address_match', 'name+address fuzzy match to LEIE entry',
         {'check': 'name_address', 'source': 'LEIE'}),
        ('H1029', 'Provider billing after NPPES deactivation date',
         'post_deactivation_billing', 'claims after NPPES deactivation',
         {'check': 'deactivation_date'}),
        ('H1030', 'New NPI at same address as recently excluded NPI',
         'new_npi_excluded_address', 'new NPI at excluded provider address',
         {'check': 'address_reuse'}),
        ('H1031', 'Servicing NPI with no NPPES record and >$500K total',
         'no_nppes_high_billing', 'no NPPES record, >$500K billing',
         {'min_paid': 500000}),
        ('H1032', 'Billing NPI with NPPES enumeration date after first claim month',
         'enumeration_after_claims', 'NPPES enumeration postdates first claim',
         {'check': 'enumeration_date'}),
        ('H1033', 'Provider with NPPES entity type change during billing period',
         'entity_type_change', 'entity type changed during billing period',
         {'check': 'entity_type_change'}),
        ('H1034', 'NPI associated with known OIG settlement (from enforcement data)',
         'oig_settlement', 'NPI linked to OIG settlement',
         {'check': 'settlement', 'source': 'OIG'}),
        ('H1035', 'Provider at address associated with >3 excluded NPIs',
         'address_multiple_exclusions', 'address linked to >3 excluded NPIs',
         {'min_excluded': 3}),
    ]

    for h_id, desc, method, criteria, params in configs:
        h += 1
        hyps.append({
            'id': h_id, 'category': '9', 'subcategory': '9G',
            'description': desc,
            'method': method,
            'acceptance_criteria': criteria,
            'analysis_function': f'crossref.{method}',
            'financial_impact_method': 'total payments to excluded/suspect provider',
            'parameters': params,
        })

    assert h == 1035, f"Gap Batch 3: expected 1035, got {h}"
    return hyps


def gen_gap_batch_4():
    """Batch 4: Kickback/Referral Concentration — 10 hypotheses (H1036-H1045)."""
    hyps = []
    h = 1035

    configs = [
        ('H1036', 'Billing NPI sending >90% of claims through single servicing NPI (captive referral)',
         'captive_referral', '>90% claims through single servicing NPI',
         {'pct_threshold': 0.9, 'direction': 'billing_to_servicing'}),
        ('H1037', 'Servicing NPI receiving >80% of referrals from single billing NPI',
         'captive_servicing', '>80% referrals from single billing NPI',
         {'pct_threshold': 0.8, 'direction': 'servicing_from_billing'}),
        ('H1038', 'Billing-servicing pair where paid_per_claim is >2x the code median (potential kickback premium)',
         'kickback_premium', 'pair rate >2x code median',
         {'ratio_threshold': 2.0}),
        ('H1039', 'New billing-servicing relationship with immediate high volume (>$100K first month)',
         'new_relationship_high_volume', 'new pair >$100K first month',
         {'min_first_month': 100000}),
        ('H1040', 'Reciprocal referral pattern: A refers to B for code X, B refers to A for code Y',
         'reciprocal_referral', 'bilateral referral pattern',
         {'check': 'reciprocal'}),
        ('H1041', 'Referring provider patient mix suddenly shifts to one downstream provider',
         'referral_shift', 'sudden shift to single downstream provider',
         {'check': 'referral_concentration_change'}),
        ('H1042', 'Lab (80XXX codes) receiving >50% of volume from single referring provider',
         'lab_single_referrer', 'lab >50% from single referrer',
         {'pct_threshold': 0.5, 'code_prefix': '80'}),
        ('H1043', 'DME supplier with >80% of orders from single prescribing NPI',
         'dme_single_prescriber', 'DME >80% from single prescriber',
         {'pct_threshold': 0.8, 'category': 'dme'}),
        ('H1044', 'Home health agency with >90% of referrals from <3 physicians',
         'hha_concentrated_referrals', 'HHA >90% from <3 physicians',
         {'pct_threshold': 0.9, 'max_referrers': 3}),
        ('H1045', 'Transport provider (A04XX/T200X) with >80% of trips for single billing entity',
         'transport_single_entity', 'transport >80% for single biller',
         {'pct_threshold': 0.8, 'category': 'transport'}),
    ]

    for h_id, desc, method, criteria, params in configs:
        h += 1
        hyps.append({
            'id': h_id, 'category': '4', 'subcategory': '4H',
            'description': desc,
            'method': method,
            'acceptance_criteria': criteria,
            'analysis_function': f'crossref.{method}',
            'financial_impact_method': 'total payments in concentrated referral pattern',
            'parameters': params,
        })

    assert h == 1045, f"Gap Batch 4: expected 1045, got {h}"
    return hyps


def gen_gap_batch_5():
    """Batch 5: Pharmacy & Prescription Drug Fraud — 10 hypotheses (H1046-H1055)."""
    hyps = []
    h = 1045

    configs = [
        ('H1046', 'Pharmacy (J-code) provider with >$10M from single drug code',
         'pharmacy_single_drug', '>$10M from single J-code',
         {'min_revenue': 10000000, 'code_prefix': 'J'}),
        ('H1047', 'Same beneficiary receiving same J-code from >3 different pharmacies same month',
         'pharmacy_bene_shopping', 'same bene, same J-code, >3 pharmacies/month',
         {'min_pharmacies': 3}),
        ('H1048', 'Pharmacy with >90% of J-code claims for high-cost specialty drugs',
         'pharmacy_specialty_concentration', '>90% specialty drug J-codes',
         {'pct_threshold': 0.9}),
        ('H1049', 'Pharmacy with paid_per_claim >3x peer median for J-codes',
         'pharmacy_rate_outlier', 'J-code paid_per_claim >3x peer median',
         {'ratio_threshold': 3.0}),
        ('H1050', 'New pharmacy (<6 months) with >$1M in J-code claims',
         'pharmacy_rapid_entrant', 'new pharmacy <6mo, >$1M J-codes',
         {'max_months': 6, 'min_revenue': 1000000}),
        ('H1051', 'Pharmacy billing J-codes with zero corresponding E&M visits for same beneficiaries',
         'pharmacy_no_em', 'J-code billing with zero E&M for same benes',
         {'check': 'missing_em'}),
        ('H1052', 'Pharmacy with >50% of claims for controlled substances (specific J-codes)',
         'pharmacy_controlled_substances', '>50% controlled substance J-codes',
         {'pct_threshold': 0.5}),
        ('H1053', 'Pharmacy serving beneficiaries from >5 states (mail-order fraud indicator)',
         'pharmacy_multi_state', 'pharmacy benes from >5 states',
         {'min_states': 5}),
        ('H1054', 'Pharmacy with sudden 10x increase in single J-code billing',
         'pharmacy_spike', '10x increase in single J-code',
         {'growth_threshold': 10.0}),
        ('H1055', 'Pharmacy with identical monthly billing amounts (suggesting fabrication)',
         'pharmacy_identical_amounts', 'identical monthly billing amounts',
         {'max_cv': 0.01, 'min_months': 6}),
    ]

    for h_id, desc, method, criteria, params in configs:
        h += 1
        hyps.append({
            'id': h_id, 'category': '8', 'subcategory': '8J',
            'description': desc,
            'method': method,
            'acceptance_criteria': criteria,
            'analysis_function': f'domain_rules.{method}',
            'financial_impact_method': 'total flagged pharmacy payments',
            'parameters': params,
        })

    assert h == 1055, f"Gap Batch 5: expected 1055, got {h}"
    return hyps


def gen_gap_batch_6():
    """Batch 6: Sober Home & Addiction Treatment — 10 hypotheses (H1056-H1065)."""
    hyps = []
    h = 1055

    configs = [
        ('H1056', 'Substance abuse provider (H0001-H0020) with >$5M and >80% from urine drug tests',
         'addiction_udt_concentration', '>$5M with >80% from urine drug tests',
         {'min_revenue': 5000000, 'pct_threshold': 0.8}),
        ('H1057', 'Addiction treatment provider billing >$500K/month for <50 beneficiaries',
         'addiction_high_per_bene', '>$500K/month for <50 benes',
         {'min_monthly': 500000, 'max_bene': 50}),
        ('H1058', 'Sober home billing pattern: high volume H-codes with zero E&M follow-up',
         'sober_home_no_em', 'high H-code volume, zero E&M follow-up',
         {'check': 'missing_em_followup'}),
        ('H1059', 'Addiction provider with beneficiaries from >3 states (patient brokering indicator)',
         'addiction_patient_brokering', 'addiction benes from >3 states',
         {'min_states': 3}),
        ('H1060', 'Substance abuse treatment claims clustered at single residential address',
         'addiction_residential_cluster', 'claims clustered at residential address',
         {'check': 'residential_cluster'}),
        ('H1061', 'Provider billing both housing support codes and treatment codes (dual-billing)',
         'addiction_dual_billing', 'housing + treatment codes same provider',
         {'check': 'dual_billing'}),
        ('H1062', 'Addiction treatment with >90% of beneficiaries enrolled <3 months (churning)',
         'addiction_churning', '>90% benes enrolled <3 months',
         {'pct_threshold': 0.9, 'max_enrollment_months': 3}),
        ('H1063', 'Lab testing provider with >50% volume from sober home referrals',
         'lab_sober_home_referrals', 'lab >50% from sober home referrals',
         {'pct_threshold': 0.5}),
        ('H1064', 'Addiction treatment provider with December billing >5x average (year-end dump)',
         'addiction_december_dump', 'December billing >5x monthly average',
         {'ratio_threshold': 5.0}),
        ('H1065', 'Substance abuse provider appearing then disappearing within 18 months with >$1M',
         'addiction_rapid_exit', 'active <18 months, >$1M, then vanished',
         {'max_months': 18, 'min_revenue': 1000000}),
    ]

    for h_id, desc, method, criteria, params in configs:
        h += 1
        hyps.append({
            'id': h_id, 'category': '8', 'subcategory': '8K',
            'description': desc,
            'method': method,
            'acceptance_criteria': criteria,
            'analysis_function': f'domain_rules.{method}',
            'financial_impact_method': 'total flagged addiction treatment payments',
            'parameters': params,
        })

    assert h == 1065, f"Gap Batch 6: expected 1065, got {h}"
    return hyps


def gen_gap_batch_7():
    """Batch 7: Genetic Testing Fraud — 5 hypotheses (H1066-H1070)."""
    hyps = []
    h = 1065

    configs = [
        ('H1066', 'Genetic testing provider (81XXX codes) with >$5M total and <100 beneficiaries',
         'genetic_high_per_bene', '>$5M genetic testing, <100 benes',
         {'min_revenue': 5000000, 'max_bene': 100, 'code_prefix': '81'}),
        ('H1067', 'Genetic testing claims with >$1000 per test from telehealth-only referring providers',
         'genetic_telehealth_referral', '>$1K/test from telehealth referrers',
         {'min_per_test': 1000}),
        ('H1068', 'Genetic testing provider serving beneficiaries from >10 states',
         'genetic_multi_state', 'genetic testing benes from >10 states',
         {'min_states': 10}),
        ('H1069', 'New genetic testing provider (<12 months) billing >$1M',
         'genetic_rapid_entrant', 'genetic testing <12mo, >$1M',
         {'max_months': 12, 'min_revenue': 1000000}),
        ('H1070', 'Genetic testing code with >50% of national volume from <5 providers',
         'genetic_market_concentration', '>50% national volume from <5 providers',
         {'pct_threshold': 0.5, 'max_providers': 5}),
    ]

    for h_id, desc, method, criteria, params in configs:
        h += 1
        hyps.append({
            'id': h_id, 'category': '8', 'subcategory': '8L',
            'description': desc,
            'method': method,
            'acceptance_criteria': criteria,
            'analysis_function': f'domain_rules.{method}',
            'financial_impact_method': 'total flagged genetic testing payments',
            'parameters': params,
        })

    assert h == 1070, f"Gap Batch 7: expected 1070, got {h}"
    return hyps


def gen_gap_batch_8():
    """Batch 8: Beneficiary-Level Anomalies — 10 hypotheses (H1071-H1080)."""
    hyps = []
    h = 1070

    configs = [
        ('H1071', 'Beneficiary appearing in >10 unrelated billing networks same month',
         'bene_network_spread', 'bene in >10 billing networks/month',
         {'min_networks': 10}),
        ('H1072', 'Beneficiary with >$100K in claims same month from >5 providers',
         'bene_high_multi_provider', 'bene >$100K/month from >5 providers',
         {'min_paid': 100000, 'min_providers': 5}),
        ('H1073', 'Beneficiary count identical across multiple providers (shared patient list)',
         'shared_bene_count', 'identical bene count at multiple providers',
         {'min_providers': 3}),
        ('H1074', 'Provider pairs with >80% beneficiary overlap (potential billing ring)',
         'bene_overlap_ring', 'provider pair >80% bene overlap',
         {'pct_threshold': 0.8}),
        ('H1075', 'Beneficiary receiving services from providers in >3 states same month',
         'bene_multi_state', 'bene in >3 provider states/month',
         {'min_states': 3}),
        ('H1076', 'Provider with >50% of beneficiaries also appearing at another flagged provider',
         'shared_flagged_benes', '>50% benes shared with flagged provider',
         {'pct_threshold': 0.5}),
        ('H1077', 'Cluster of providers sharing >20% of the same beneficiary pool',
         'bene_pool_cluster', 'provider cluster >20% shared bene pool',
         {'pct_threshold': 0.2, 'min_cluster': 3}),
        ('H1078', 'Beneficiary receiving >$50K in personal care services per month',
         'bene_excessive_personal_care', 'bene >$50K personal care/month',
         {'min_paid': 50000, 'codes': ['T1019', 'T1020', 'S5125']}),
        ('H1079', 'Provider with beneficiary count growing >3x while paid grows >10x (phantom additions)',
         'bene_phantom_growth', 'bene count 3x growth but paid 10x growth',
         {'bene_growth': 3.0, 'paid_growth': 10.0}),
        ('H1080', 'Seasonal beneficiary pattern: same beneficiaries added/dropped synchronously across providers',
         'bene_synchronized_churn', 'synchronized bene add/drop across providers',
         {'check': 'synchronized_churn'}),
    ]

    for h_id, desc, method, criteria, params in configs:
        h += 1
        hyps.append({
            'id': h_id, 'category': '9', 'subcategory': '9H',
            'description': desc,
            'method': method,
            'acceptance_criteria': criteria,
            'analysis_function': f'crossref.{method}',
            'financial_impact_method': 'total payments to/for flagged beneficiaries',
            'parameters': params,
        })

    assert h == 1080, f"Gap Batch 8: expected 1080, got {h}"
    return hyps


def gen_gap_batch_9():
    """Batch 9: Ownership Change & Address Clustering — 5 hypotheses (H1081-H1085)."""
    hyps = []
    h = 1080

    configs = [
        ('H1081', 'Multiple NPIs at identical NPPES address with combined >$10M and any flagged NPI',
         'address_cluster_flagged', 'address cluster >$10M with flagged NPI',
         {'min_combined': 10000000, 'check': 'flagged_npi'}),
        ('H1082', 'New NPI at address of recently deactivated NPI with similar billing pattern',
         'address_npi_replacement', 'new NPI replacing deactivated NPI at same address',
         {'check': 'replacement_pattern'}),
        ('H1083', 'Provider with NPPES address change followed by >3x billing increase',
         'address_change_spike', 'address change then >3x billing increase',
         {'growth_threshold': 3.0}),
        ('H1084', '>5 NPIs with sequential NPI numbers at same address (batch enrollment)',
         'sequential_npi_address', '>5 sequential NPIs at same address',
         {'min_sequential': 5}),
        ('H1085', 'Address cluster where >50% of NPIs started billing within 3 months of each other',
         'coordinated_address_start', '>50% of address NPIs started within 3 months',
         {'pct_threshold': 0.5, 'max_spread_months': 3}),
    ]

    for h_id, desc, method, criteria, params in configs:
        h += 1
        hyps.append({
            'id': h_id, 'category': '9', 'subcategory': '9I',
            'description': desc,
            'method': method,
            'acceptance_criteria': criteria,
            'analysis_function': f'crossref.{method}',
            'financial_impact_method': 'total payments at flagged address cluster',
            'parameters': params,
        })

    assert h == 1085, f"Gap Batch 9: expected 1085, got {h}"
    return hyps


def gen_gap_batch_10():
    """Batch 10: Novel/Research-Frontier Methods — 15 hypotheses (H1086-H1100)."""
    hyps = []
    h = 1085

    configs = [
        ('H1086', "Zipf's Law deviation: billing amounts don't follow expected power-law distribution",
         'zipf_billing', "Billing distribution deviates from Zipf's Law",
         {'test': 'zipf', 'target': 'billing_amounts'}),
        ('H1087', "Zipf's Law on referral concentration: single provider receives disproportionate referrals",
         'zipf_referral', "Referral concentration violates Zipf's Law",
         {'test': 'zipf', 'target': 'referral_counts'}),
        ('H1088', 'Association rule mining: unusual HCPCS code combinations (clinically impossible pairings)',
         'association_rules', 'unusual code combinations via apriori/FP-growth',
         {'min_support': 0.01, 'min_confidence': 0.5}),
        ('H1089', 'Billing pattern cosine similarity: provider whose monthly pattern matches known fraud profiles',
         'cosine_similarity_fraud', 'monthly billing cosine similarity to fraud profiles',
         {'min_similarity': 0.9}),
        ('H1090', 'Entropy analysis: provider with unusually low entropy in billing distribution (too uniform)',
         'low_entropy_billing', 'billing distribution entropy below 1st percentile',
         {'percentile': 1}),
        ('H1091', 'Provider billing codes from >3 unrelated clinical families (scope-of-practice violation proxy)',
         'scope_of_practice', '>3 unrelated clinical code families',
         {'max_families': 3}),
        ('H1092', "Geospatial outlier: provider's beneficiaries' state distribution inconsistent with provider location",
         'geospatial_bene_mismatch', 'beneficiary states inconsistent with provider location',
         {'check': 'state_distribution'}),
        ('H1093', 'Temporal autocorrelation: provider with zero autocorrelation in monthly series (random/fabricated)',
         'zero_autocorrelation', 'monthly billing series autocorrelation near zero',
         {'max_autocorr': 0.1, 'min_months': 24}),
        ('H1094', 'Claim-to-beneficiary ratio changes direction abruptly (suggests record manipulation)',
         'cpb_direction_change', 'abrupt reversal in claims-per-bene trend',
         {'check': 'trend_reversal'}),
        ('H1095', 'Claims-per-day exceeds physical capacity based on provider type (individual vs org)',
         'capacity_based_limit', 'claims/day exceeds individual provider capacity',
         {'individual_max': 40, 'org_max': 500}),
        ('H1096', 'Provider with negative payments >10% but only in specific months (selective reversal)',
         'selective_reversal', 'negative payments concentrated in specific months',
         {'min_neg_pct': 0.1, 'check': 'temporal_concentration'}),
        ('H1097', 'Code pair frequency deviation: two codes that typically co-occur nationally appear at anomalous ratio',
         'code_pair_deviation', 'code pair ratio deviates from national norm',
         {'min_deviation': 3.0}),
        ('H1098', 'Network motif detection: triangles in billing graph where A->B->C->A all have high-value edges',
         'network_triangles', 'billing graph triangles with high-value edges',
         {'min_edge_value': 100000}),
        ('H1099', 'Provider with Benford violation PLUS temporal spike PLUS peer outlier (triple signal)',
         'triple_signal', "Benford's + temporal spike + peer outlier combined",
         {'min_signals': 3}),
        ('H1100', "GNN-inspired feature: provider's neighborhood risk score based on connected providers' anomaly scores",
         'neighborhood_risk', 'provider risk score from network neighbor anomalies',
         {'check': 'neighborhood_propagation'}),
    ]

    for h_id, desc, method, criteria, params in configs:
        h += 1
        hyps.append({
            'id': h_id, 'category': '6', 'subcategory': '6G',
            'description': desc,
            'method': method,
            'acceptance_criteria': criteria,
            'analysis_function': f'ml_pipeline.{method}',
            'financial_impact_method': 'total payments from novel-method flagged providers',
            'parameters': params,
        })

    assert h == 1100, f"Gap Batch 10: expected 1100, got {h}"
    return hyps


def main():
    t0 = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_hypotheses = []
    all_hypotheses.extend(gen_category_1())
    all_hypotheses.extend(gen_category_2())
    all_hypotheses.extend(gen_category_3())
    all_hypotheses.extend(gen_category_4())
    all_hypotheses.extend(gen_category_5())
    all_hypotheses.extend(gen_category_6())
    all_hypotheses.extend(gen_category_7())
    all_hypotheses.extend(gen_category_8())
    all_hypotheses.extend(gen_category_9())

    # Gap Analysis hypotheses (H1001-H1100)
    all_hypotheses.extend(gen_gap_batch_1())   # ABA Therapy (15)
    all_hypotheses.extend(gen_gap_batch_2())   # Impossible Provider-Day (10)
    all_hypotheses.extend(gen_gap_batch_3())   # LEIE Cross-Reference (10)
    all_hypotheses.extend(gen_gap_batch_4())   # Kickback/Referral (10)
    all_hypotheses.extend(gen_gap_batch_5())   # Pharmacy Fraud (10)
    all_hypotheses.extend(gen_gap_batch_6())   # Sober Home/Addiction (10)
    all_hypotheses.extend(gen_gap_batch_7())   # Genetic Testing (5)
    all_hypotheses.extend(gen_gap_batch_8())   # Beneficiary Anomalies (10)
    all_hypotheses.extend(gen_gap_batch_9())   # Address Clustering (5)
    all_hypotheses.extend(gen_gap_batch_10())  # Novel Methods (15)

    if len(all_hypotheses) < 1000:
        print(f"WARNING: Expected ~1100 hypotheses, got {len(all_hypotheses)}")

    # Verify unique IDs
    ids = [h['id'] for h in all_hypotheses]
    assert len(set(ids)) == len(ids), f"Duplicate IDs found: {len(ids)} total, {len(set(ids))} unique"

    # Write all hypotheses
    all_path = os.path.join(OUTPUT_DIR, 'all_hypotheses.json')
    with open(all_path, 'w') as f:
        json.dump(all_hypotheses, f, indent=2)
    print(f"Written {len(all_hypotheses)} hypotheses to {all_path}")

    # Split into 22 batch files of 50
    num_batches = (len(all_hypotheses) + 49) // 50  # ceiling division
    for batch_num in range(num_batches):
        start = batch_num * 50
        end = start + 50
        batch = all_hypotheses[start:end]
        batch_path = os.path.join(OUTPUT_DIR, f'batch_{batch_num:02d}.json')
        with open(batch_path, 'w') as f:
            json.dump(batch, f, indent=2)

    print(f"Split into {num_batches} batch files of 50 at {OUTPUT_DIR}/batch_00.json through batch_{num_batches-1:02d}.json")

    # Category counts
    from collections import Counter
    cat_counts = Counter(h['category'] for h in all_hypotheses)
    print(f"\nCategory distribution:")
    for cat in sorted(cat_counts.keys(), key=lambda x: int(x)):
        print(f"  Category {cat}: {cat_counts[cat]} hypotheses")

    print(f"\nGenerated {len(all_hypotheses)} hypotheses")
    print(f"Time: {time.time() - t0:.1f}s")


if __name__ == '__main__':
    main()
