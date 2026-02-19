#!/usr/bin/env python3
"""Milestone 7: Domain-specific red flag detection.

Implements Category 8 hypotheses: impossible volumes, upcoding, unbundling,
phantom billing, adjustment anomalies, and duplicate billing.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.db_utils import get_connection, format_dollars

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINDINGS_DIR = os.path.join(PROJECT_ROOT, 'output', 'findings')

# Physical maximums for timed services (units per beneficiary per month)
# T1019 = 15-min increments: 24 hrs/day * 4 units/hr * 30 days = 2880 max, but realistic max ~480
PHYSICAL_LIMITS = {
    'T1019': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Personal Care 15min'},
    'T1020': {'unit_minutes': 1440, 'max_units_per_bene_per_month': 31, 'desc': 'Personal Care per diem'},
    'T1005': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Respite Care 15min'},
    'S5125': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Attendant Care 15min'},
    'S5130': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Homemaker 15min'},
    'S5150': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Unskilled Respite 15min'},
    'H0015': {'unit_minutes': 15, 'max_units_per_bene_per_month': 192, 'desc': 'Intensive Outpatient'},
    'H2015': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Community Support 15min'},
    'H2016': {'unit_minutes': 60, 'max_units_per_bene_per_month': 120, 'desc': 'Community Support per hr'},
    'H0036': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Psychiatric Support 15min'},
    'T1016': {'unit_minutes': 15, 'max_units_per_bene_per_month': 192, 'desc': 'Case Management 15min'},
    'T1017': {'unit_minutes': 15, 'max_units_per_bene_per_month': 192, 'desc': 'Targeted Case Mgmt 15min'},
    'H2017': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Psychosocial Rehab 15min'},
    'T2020': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Day Habilitation 15min'},
    'H2019': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Therapeutic Behavioral 15min'},
}

# E&M level families for upcoding detection
EM_FAMILIES = {
    'office_established': ['99211', '99212', '99213', '99214', '99215'],
    'office_new': ['99201', '99202', '99203', '99204', '99205'],
    'ed_visit': ['99281', '99282', '99283', '99284', '99285'],
    'hospital_initial': ['99221', '99222', '99223'],
    'hospital_subsequent': ['99231', '99232', '99233'],
}


def make_finding(h_id, providers, total_impact, confidence, method, evidence):
    return {
        'hypothesis_id': h_id,
        'flagged_providers': providers,
        'total_impact': total_impact,
        'confidence': confidence,
        'method_name': method,
        'evidence': evidence,
    }


def run_impossible_volumes(con):
    """8A: Detect physically impossible service volumes.

    NOTE: The source dataset does not include service units or time increments,
    only total claims. Without units, physical-limit logic is invalid.
    This detector is intentionally disabled until units are available.
    """
    print("\n--- 8A: Impossible Volumes ---")
    print("  Skipped: dataset lacks units/time increments needed for volume limits")
    return []


def run_upcoding(con):
    """8B: Detect E&M upcoding patterns."""
    print("\n--- 8B: Upcoding Detection ---")
    findings = []
    h_num = 846

    for family_name, codes in EM_FAMILIES.items():
        highest_code = codes[-1]

        rows = con.execute(f"""
            WITH provider_levels AS (
                SELECT
                    billing_npi,
                    hcpcs_code,
                    SUM(claims) AS claims
                FROM claims
                WHERE hcpcs_code IN ({','.join(f"'{c}'" for c in codes)})
                GROUP BY billing_npi, hcpcs_code
            ),
            provider_totals AS (
                SELECT
                    billing_npi,
                    SUM(claims) AS total_claims,
                    SUM(CASE WHEN hcpcs_code = '{highest_code}' THEN claims ELSE 0 END) AS high_claims
                FROM provider_levels
                GROUP BY billing_npi
                HAVING total_claims >= 50
            ),
            peer_stats AS (
                SELECT
                    AVG(high_claims * 1.0 / total_claims) AS peer_mean,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY high_claims * 1.0 / total_claims) AS peer_median
                FROM provider_totals
            )
            SELECT
                pt.billing_npi,
                pt.high_claims * 1.0 / pt.total_claims AS high_ratio,
                ps2.peer_median,
                pt.total_claims,
                pt.high_claims,
                COALESCE(p.name, 'NPI ' || pt.billing_npi) AS name,
                COALESCE(p.state, '') AS state,
                psum.total_paid
            FROM provider_totals pt
            CROSS JOIN peer_stats ps2
            LEFT JOIN providers p ON pt.billing_npi = p.npi
            LEFT JOIN provider_summary psum ON pt.billing_npi = psum.billing_npi
            WHERE pt.high_claims * 1.0 / pt.total_claims > 2 * ps2.peer_median
              AND ps2.peer_median > 0
              AND pt.high_claims > 20
            ORDER BY psum.total_paid DESC
            LIMIT 30
        """).fetchall()

        if rows:
            providers = []
            total_impact = 0
            for r in rows:
                npi, ratio, median, total_claims, high_claims, name, state, total_paid = r
                # Estimate excess: difference between this provider's high-code ratio and median
                excess_claims = high_claims - (total_claims * median)
                # Rough estimate of per-claim upcode premium
                premium = total_paid * 0.2 / total_claims if total_claims > 0 else 0
                impact = excess_claims * premium
                providers.append({
                    'npi': npi, 'name': name, 'state': state,
                    'amount': float(max(impact, 0)),
                    'score': float(ratio),
                    'evidence': f"{family_name}: {highest_code} ratio={ratio:.1%} vs peer median={median:.1%}, "
                                f"{high_claims:,} high-level claims of {total_claims:,} total"
                })
                total_impact += max(impact, 0)

            if providers:
                h_id = f"H{h_num:04d}"
                h_num += 1
                findings.append(make_finding(
                    h_id, providers[:20], total_impact, 'high' if total_impact > 1000000 else 'medium',
                    'upcoding',
                    f"{family_name}: {len(providers)} providers bill {highest_code} at >2x the peer median rate"
                ))

        if h_num > 860:
            break

    print(f"  Upcoding: {len(findings)} findings")
    return findings


def run_unbundling(con):
    """8C: Detect potential unbundling (excessive code diversity per beneficiary)."""
    print("\n--- 8C: Unbundling Detection ---")
    findings = []

    rows = con.execute("""
        WITH provider_code_diversity AS (
            SELECT
                billing_npi,
                claim_month,
                COUNT(DISTINCT hcpcs_code) AS codes_per_month,
                SUM(beneficiaries) AS total_benes,
                COUNT(DISTINCT hcpcs_code) * 1.0 / NULLIF(SUM(beneficiaries), 0) AS codes_per_bene
            FROM claims
            GROUP BY billing_npi, claim_month
            HAVING SUM(beneficiaries) > 10
        ),
        peer_stats AS (
            SELECT
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY codes_per_bene) AS median_cpb,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY codes_per_bene) AS p95_cpb
            FROM provider_code_diversity
        )
        SELECT
            pcd.billing_npi,
            AVG(pcd.codes_per_bene) AS avg_codes_per_bene,
            ps2.median_cpb,
            COUNT(*) AS months,
            COALESCE(p.name, 'NPI ' || pcd.billing_npi) AS name,
            COALESCE(p.state, '') AS state,
            psum.total_paid
        FROM provider_code_diversity pcd
        CROSS JOIN peer_stats ps2
        LEFT JOIN providers p ON pcd.billing_npi = p.npi
        LEFT JOIN provider_summary psum ON pcd.billing_npi = psum.billing_npi
        WHERE pcd.codes_per_bene > 3 * ps2.median_cpb
          AND ps2.median_cpb > 0
        GROUP BY pcd.billing_npi, ps2.median_cpb, p.name, p.state, psum.total_paid
        HAVING COUNT(*) >= 6 AND psum.total_paid > 100000
        ORDER BY psum.total_paid DESC
        LIMIT 50
    """).fetchall()

    if rows:
        providers = []
        total_impact = 0
        for r in rows:
            npi, avg_cpb, median, months, name, state, total_paid = r
            # Conservative estimate: 20% of total paid may be due to unbundling
            impact = total_paid * 0.2
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(impact),
                'score': float(avg_cpb),
                'evidence': f"Avg {avg_cpb:.1f} codes/bene/month vs peer median {median:.2f}, "
                            f"{months} months, total paid={format_dollars(total_paid)}"
            })
            total_impact += impact

        for i in range(0, min(len(providers), 15 * 3), 3):
            chunk = providers[i:i+3]
            h_id = f"H{861 + i // 3:04d}"
            findings.append(make_finding(
                h_id, chunk, sum(p['amount'] for p in chunk),
                'medium', 'unbundling',
                f"Potential unbundling: excessive code diversity per beneficiary"
            ))

    print(f"  Unbundling: {len(findings)} findings")
    return findings


def run_high_risk_categories(con):
    """8D: Flag top billers in high-risk categories with additional red flags."""
    print("\n--- 8D: High-Risk Category Flagging ---")
    findings = []

    high_risk_cats = [
        ('Home Health', "c.hcpcs_code LIKE 'T%'"),
        ('Behavioral Health', "c.hcpcs_code LIKE 'H%'"),
        ('Personal Care', "c.hcpcs_code IN ('T1019', 'T1020', 'S5125')"),
        ('DME', "c.hcpcs_code LIKE 'E%' OR c.hcpcs_code LIKE 'K%'"),
        ('Transportation', "c.hcpcs_code LIKE 'A04%' OR c.hcpcs_code IN ('T2001','T2002','T2003')"),
    ]

    h_num = 876
    for cat_name, where_clause in high_risk_cats:
        rows = con.execute(f"""
            WITH cat_providers AS (
                SELECT
                    c.billing_npi,
                    SUM(c.paid) AS cat_paid,
                    SUM(c.claims) AS cat_claims,
                    SUM(c.beneficiaries) AS cat_benes,
                    COUNT(DISTINCT c.claim_month) AS months
                FROM claims c
                WHERE {where_clause} AND c.paid > 0
                GROUP BY c.billing_npi
                HAVING SUM(c.paid) > 1000000
            ),
            cat_stats AS (
                SELECT
                    AVG(cat_paid / NULLIF(cat_claims, 0)) AS mean_rate,
                    STDDEV(cat_paid / NULLIF(cat_claims, 0)) AS std_rate,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cat_claims / NULLIF(cat_benes, 0)) AS median_cpb
                FROM cat_providers
            )
            SELECT
                cp.billing_npi,
                cp.cat_paid,
                cp.cat_claims,
                cp.cat_benes,
                cp.cat_paid / NULLIF(cp.cat_claims, 0) AS rate,
                cs.mean_rate,
                cs.std_rate,
                cp.cat_claims / NULLIF(cp.cat_benes, 0) AS cpb,
                cs.median_cpb,
                COALESCE(p.name, 'NPI ' || cp.billing_npi) AS name,
                COALESCE(p.state, '') AS state
            FROM cat_providers cp
            CROSS JOIN cat_stats cs
            LEFT JOIN providers p ON cp.billing_npi = p.npi
            WHERE (
                (cs.std_rate > 0 AND (cp.cat_paid / NULLIF(cp.cat_claims, 0) - cs.mean_rate) / cs.std_rate > 3)
                OR (cs.median_cpb > 0 AND cp.cat_claims / NULLIF(cp.cat_benes, 0) > 3 * cs.median_cpb)
            )
            ORDER BY cp.cat_paid DESC
            LIMIT 20
        """).fetchall()

        if rows:
            providers = []
            for r in rows:
                npi, cat_paid, cat_claims, cat_benes, rate, mean_rate, std_rate, cpb, median_cpb, name, state = r
                rate_z = (rate - mean_rate) / std_rate if std_rate and std_rate > 0 else 0
                cpb_ratio = cpb / median_cpb if median_cpb and median_cpb > 0 else 0
                excess = max(0, (rate - mean_rate) * cat_claims) if rate and mean_rate else 0
                providers.append({
                    'npi': npi, 'name': name, 'state': state,
                    'amount': float(excess),
                    'score': float(max(rate_z, cpb_ratio)),
                    'evidence': f"{cat_name}: rate_z={rate_z:.1f}, cpb_ratio={cpb_ratio:.1f}x, "
                                f"total={format_dollars(cat_paid)}"
                })

            if providers:
                h_id = f"H{h_num:04d}"
                h_num += 1
                findings.append(make_finding(
                    h_id, providers, sum(p['amount'] for p in providers),
                    'high' if len(providers) > 5 else 'medium',
                    'high_risk_category',
                    f"{cat_name}: {len(providers)} providers with rate or volume outliers"
                ))

        if h_num > 890:
            break

    print(f"  High-risk categories: {len(findings)} findings")
    return findings


def run_phantom_billing(con):
    """8E: Detect phantom billing indicators."""
    print("\n--- 8E: Phantom Billing ---")
    findings = []

    # Constant beneficiary count with growing claims
    rows = con.execute("""
        WITH monthly_stats AS (
            SELECT
                billing_npi,
                claim_month,
                SUM(beneficiaries) AS benes,
                SUM(claims) AS claims,
                SUM(paid) AS paid
            FROM claims
            GROUP BY billing_npi, claim_month
        ),
        provider_patterns AS (
            SELECT
                billing_npi,
                COUNT(*) AS months,
                STDDEV(benes) / NULLIF(AVG(benes), 0) AS bene_cv,
                STDDEV(claims) / NULLIF(AVG(claims), 0) AS claims_cv,
                SUM(paid) AS total_paid,
                AVG(benes) AS avg_benes,
                AVG(claims) AS avg_claims
            FROM monthly_stats
            GROUP BY billing_npi
            HAVING COUNT(*) >= 12 AND AVG(benes) > 10
        )
        SELECT
            pp.billing_npi,
            pp.bene_cv,
            pp.claims_cv,
            pp.total_paid,
            pp.months,
            pp.avg_benes,
            pp.avg_claims,
            COALESCE(p.name, 'NPI ' || pp.billing_npi) AS name,
            COALESCE(p.state, '') AS state
        FROM provider_patterns pp
        LEFT JOIN providers p ON pp.billing_npi = p.npi
        WHERE pp.bene_cv < 0.05
          AND pp.claims_cv > 0.3
          AND pp.total_paid > 500000
        ORDER BY pp.total_paid DESC
        LIMIT 50
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, bene_cv, claims_cv, total_paid, months, avg_benes, avg_claims, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(total_paid * 0.3),
                'score': float(claims_cv / max(bene_cv, 0.001)),
                'evidence': f"Bene CV={bene_cv:.3f} (near-constant) but Claims CV={claims_cv:.2f} (growing), "
                            f"avg_benes={avg_benes:.0f}, avg_claims={avg_claims:.0f}, "
                            f"total={format_dollars(total_paid)}"
            })

        for i in range(0, min(len(providers), 40), 4):
            chunk = providers[i:i+4]
            h_id = f"H{891 + i // 4:04d}"
            findings.append(make_finding(
                h_id, chunk, sum(p['amount'] for p in chunk),
                'high', 'phantom_billing',
                f"Phantom billing indicator: constant beneficiaries with growing claims"
            ))

    print(f"  Phantom billing: {len(findings)} findings")
    return findings


def run_adjustment_anomalies(con):
    """8F: Detect excessive negative payment adjustments."""
    print("\n--- 8F: Adjustment Anomalies ---")
    findings = []

    rows = con.execute("""
        WITH provider_adjustments AS (
            SELECT
                billing_npi,
                SUM(CASE WHEN paid > 0 THEN paid ELSE 0 END) AS positive_paid,
                SUM(CASE WHEN paid < 0 THEN ABS(paid) ELSE 0 END) AS negative_paid,
                COUNT(CASE WHEN paid < 0 THEN 1 END) AS neg_count,
                COUNT(*) AS total_rows
            FROM claims
            GROUP BY billing_npi
            HAVING SUM(CASE WHEN paid > 0 THEN paid ELSE 0 END) > 100000
        )
        SELECT
            pa.billing_npi,
            pa.positive_paid,
            pa.negative_paid,
            pa.negative_paid / NULLIF(pa.positive_paid, 0) AS neg_ratio,
            pa.neg_count,
            COALESCE(p.name, 'NPI ' || pa.billing_npi) AS name,
            COALESCE(p.state, '') AS state
        FROM provider_adjustments pa
        LEFT JOIN providers p ON pa.billing_npi = p.npi
        WHERE pa.negative_paid / NULLIF(pa.positive_paid, 0) > 0.2
        ORDER BY pa.negative_paid DESC
        LIMIT 30
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, pos, neg, ratio, neg_count, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(neg),
                'score': float(ratio),
                'evidence': f"Negative payments={format_dollars(neg)} ({ratio:.1%} of positive), "
                            f"{neg_count} negative rows, positive={format_dollars(pos)}"
            })

        for i in range(0, min(len(providers), 30), 3):
            chunk = providers[i:i+3]
            h_id = f"H{911 + i // 3:04d}"
            findings.append(make_finding(
                h_id, chunk, sum(p['amount'] for p in chunk),
                'medium', 'adjustment_anomaly',
                f"Excessive negative payment adjustments (>20% of positive payments)"
            ))

    print(f"  Adjustment anomalies: {len(findings)} findings")
    return findings


def run_duplicate_billing(con):
    """8G: Detect potential duplicate billing."""
    print("\n--- 8G: Duplicate Billing ---")
    findings = []

    rows = con.execute("""
        SELECT
            c.billing_npi,
            c.hcpcs_code,
            c.claim_month,
            COUNT(DISTINCT c.servicing_npi) AS num_servicing,
            SUM(c.claims) AS total_claims,
            SUM(c.paid) AS total_paid,
            COALESCE(p.name, 'NPI ' || c.billing_npi) AS name,
            COALESCE(p.state, '') AS state
        FROM claims c
        LEFT JOIN providers p ON c.billing_npi = p.npi
        WHERE c.servicing_npi IS NOT NULL AND c.servicing_npi != ''
        GROUP BY c.billing_npi, c.hcpcs_code, c.claim_month, p.name, p.state
        HAVING COUNT(DISTINCT c.servicing_npi) > 5
           AND SUM(c.paid) > 50000
        ORDER BY SUM(c.paid) DESC
        LIMIT 50
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, code, month, num_serv, claims, paid, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid * 0.3),
                'score': float(num_serv),
                'evidence': f"Code {code}, month {month}: {num_serv} servicing NPIs, "
                            f"{claims:,} claims, {format_dollars(paid)}"
            })

        for i in range(0, min(len(providers), 40), 4):
            chunk = providers[i:i+4]
            h_id = f"H{921 + i // 4:04d}"
            findings.append(make_finding(
                h_id, chunk, sum(p['amount'] for p in chunk),
                'medium', 'duplicate_billing',
                f"Potential duplicate billing: same billing NPI + code + month with many servicing NPIs"
            ))

    print(f"  Duplicate billing: {len(findings)} findings")
    return findings


# ---------------------------------------------------------------------------
# Gap Analysis: New domain-specific fraud detection functions
# ---------------------------------------------------------------------------

# ABA therapy HCPCS codes
ABA_TREATMENT_CODES = ['97153', '97154', '97155', '97156', '97157', '97158']
ABA_EVAL_CODES = ['97151', '97152']
ABA_SUPERVISION_CODES = ['97155', '97156']
ABA_ALL_CODES = ABA_TREATMENT_CODES + ABA_EVAL_CODES + ['H0031', 'H0032', '0362T', '0373T', '0374T']


def run_aba_therapy_fraud(con):
    """8H: ABA therapy-specific fraud detection (H1001-H1015)."""
    print("\n--- 8H: ABA Therapy Fraud ---")
    findings = []
    aba_code_list = ','.join(f"'{c}'" for c in ABA_ALL_CODES)

    # H1001: Impossible ABA volumes per beneficiary
    rows = con.execute(f"""
        SELECT
            c.billing_npi,
            c.claim_month,
            c.claims,
            c.beneficiaries,
            c.paid,
            c.claims * 1.0 / NULLIF(c.beneficiaries, 0) AS claims_per_bene,
            COALESCE(p.name, 'NPI ' || c.billing_npi) AS name,
            COALESCE(p.state, '') AS state
        FROM claims c
        LEFT JOIN providers p ON c.billing_npi = p.npi
        WHERE c.hcpcs_code IN ({aba_code_list})
          AND c.beneficiaries > 0
          AND c.claims * 1.0 / c.beneficiaries > 32
          AND c.paid > 5000
        ORDER BY c.paid DESC
        LIMIT 50
    """).fetchall()

    if rows:
        providers = []
        total_impact = 0
        for r in rows:
            npi, month, claims, benes, paid, cpb, name, state = r
            excess = (cpb - 32) * benes * (paid / claims) if claims > 0 else 0
            if excess > 0:
                providers.append({
                    'npi': npi, 'name': name, 'state': state,
                    'amount': float(excess), 'score': float(cpb),
                    'evidence': f"ABA: {cpb:.0f} claims/bene/month (max=32), month={month}, "
                                f"excess=${excess:,.0f}"
                })
                total_impact += excess
        if providers:
            findings.append(make_finding('H1001', providers[:20], total_impact, 'high',
                                         'impossible_aba_volume',
                                         f"ABA impossible volume: {len(providers)} provider-months exceed 32 units/bene/day"))

    # H1003: ABA concentration >90% revenue
    rows = con.execute(f"""
        WITH provider_aba AS (
            SELECT billing_npi,
                   SUM(CASE WHEN hcpcs_code IN ({aba_code_list}) THEN paid ELSE 0 END) AS aba_paid,
                   SUM(paid) AS total_paid
            FROM claims
            GROUP BY billing_npi
            HAVING SUM(paid) > 1000000
        )
        SELECT pa.billing_npi, pa.aba_paid, pa.total_paid,
               pa.aba_paid / NULLIF(pa.total_paid, 0) AS aba_pct,
               COALESCE(p.name, 'NPI ' || pa.billing_npi) AS name,
               COALESCE(p.state, '') AS state
        FROM provider_aba pa
        LEFT JOIN providers p ON pa.billing_npi = p.npi
        WHERE pa.aba_paid / NULLIF(pa.total_paid, 0) > 0.9
        ORDER BY pa.total_paid DESC
        LIMIT 30
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, aba_paid, total_paid, pct, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(aba_paid), 'score': float(pct),
                'evidence': f"ABA concentration: {pct:.1%} of {format_dollars(total_paid)} from ABA codes"
            })
        findings.append(make_finding('H1003', providers[:20],
                                     sum(p['amount'] for p in providers), 'medium',
                                     'aba_concentration',
                                     f"ABA revenue concentration: {len(providers)} providers with >90% ABA"))

    # H1004: ABA claims per bene vs state peer median
    rows = con.execute(f"""
        WITH aba_providers AS (
            SELECT c.billing_npi,
                   SUM(c.claims) AS total_claims,
                   SUM(c.beneficiaries) AS total_benes,
                   SUM(c.paid) AS total_paid,
                   SUM(c.claims) * 1.0 / NULLIF(SUM(c.beneficiaries), 0) AS cpb,
                   COALESCE(p.state, '') AS state
            FROM claims c
            LEFT JOIN providers p ON c.billing_npi = p.npi
            WHERE c.hcpcs_code IN ({aba_code_list}) AND c.beneficiaries > 0
            GROUP BY c.billing_npi, p.state
            HAVING SUM(c.beneficiaries) >= 10
        ),
        state_medians AS (
            SELECT state,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cpb) AS median_cpb,
                   COUNT(*) AS num_peers
            FROM aba_providers
            WHERE state != ''
            GROUP BY state
            HAVING COUNT(*) >= 5
        )
        SELECT ap.billing_npi, ap.cpb, sm.median_cpb, ap.total_paid,
               ap.cpb / NULLIF(sm.median_cpb, 0) AS ratio,
               COALESCE(pr.name, 'NPI ' || ap.billing_npi) AS name, ap.state
        FROM aba_providers ap
        INNER JOIN state_medians sm ON ap.state = sm.state
        LEFT JOIN providers pr ON ap.billing_npi = pr.npi
        WHERE sm.median_cpb > 0 AND ap.cpb > 3 * sm.median_cpb
        ORDER BY ap.total_paid DESC
        LIMIT 30
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, cpb, median, paid, ratio, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': float(ratio),
                'evidence': f"ABA cpb={cpb:.1f} vs state median={median:.1f} ({ratio:.1f}x), "
                            f"total={format_dollars(paid)}"
            })
        findings.append(make_finding('H1004', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'aba_peer_cpb',
                                     f"ABA claims/bene >3x state median: {len(providers)} providers"))

    # H1006: ABA rapid entrants
    rows = con.execute(f"""
        WITH aba_monthly AS (
            SELECT billing_npi,
                   MIN(claim_month) AS first_month,
                   MAX(claim_month) AS last_month,
                   COUNT(DISTINCT claim_month) AS num_months,
                   SUM(paid) AS total_paid
            FROM claims
            WHERE hcpcs_code IN ({aba_code_list})
            GROUP BY billing_npi
            HAVING COUNT(DISTINCT claim_month) < 12 AND SUM(paid) > 500000
        )
        SELECT am.billing_npi, am.num_months, am.total_paid,
               am.first_month, am.last_month,
               COALESCE(p.name, 'NPI ' || am.billing_npi) AS name,
               COALESCE(p.state, '') AS state
        FROM aba_monthly am
        LEFT JOIN providers p ON am.billing_npi = p.npi
        ORDER BY am.total_paid DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, months, paid, first, last, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': float(paid / max(months, 1)),
                'evidence': f"ABA rapid entrant: {months} months, {format_dollars(paid)}, "
                            f"first={first}, last={last}"
            })
        findings.append(make_finding('H1006', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'aba_rapid_entrant',
                                     f"ABA rapid entrants: {len(providers)} providers <12mo with >$500K"))

    # H1008: ABA no supervision codes
    rows = con.execute(f"""
        WITH aba_treatment AS (
            SELECT billing_npi, SUM(claims) AS treat_claims, SUM(paid) AS treat_paid
            FROM claims
            WHERE hcpcs_code IN ('97153', '97154', '97157', '97158')
            GROUP BY billing_npi
            HAVING SUM(claims) > 100
        ),
        aba_supervision AS (
            SELECT billing_npi, SUM(claims) AS super_claims
            FROM claims
            WHERE hcpcs_code IN ('97155', '97156')
            GROUP BY billing_npi
        )
        SELECT at2.billing_npi, at2.treat_claims, at2.treat_paid,
               COALESCE(as2.super_claims, 0) AS super_claims,
               COALESCE(p.name, 'NPI ' || at2.billing_npi) AS name,
               COALESCE(p.state, '') AS state
        FROM aba_treatment at2
        LEFT JOIN aba_supervision as2 ON at2.billing_npi = as2.billing_npi
        LEFT JOIN providers p ON at2.billing_npi = p.npi
        WHERE COALESCE(as2.super_claims, 0) = 0
          AND at2.treat_paid > 100000
        ORDER BY at2.treat_paid DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, treat, paid, super_c, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': float(treat),
                'evidence': f"ABA no supervision: {treat:,} treatment claims, "
                            f"0 supervision codes, {format_dollars(paid)}"
            })
        findings.append(make_finding('H1008', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'aba_no_supervision',
                                     f"ABA no supervision codes: {len(providers)} providers"))

    print(f"  ABA therapy fraud: {len(findings)} findings")
    return findings


def run_impossible_provider_day(con):
    """8I: Detect impossible provider-day totals (H1016-H1025)."""
    print("\n--- 8I: Impossible Provider-Day ---")
    findings = []

    # H1016: Provider billing >24h total timed services per day (estimated from monthly)
    # Since we have monthly data, estimate: if total_claims * unit_minutes / 30 days > 24*60
    rows = con.execute("""
        WITH timed_monthly AS (
            SELECT
                c.billing_npi,
                c.claim_month,
                SUM(c.claims) AS total_claims,
                SUM(c.paid) AS total_paid,
                -- Estimate daily hours assuming 30 service days/month, 15-min units
                SUM(c.claims) * 15.0 / 60.0 / 30.0 AS est_daily_hours,
                COALESCE(p.name, 'NPI ' || c.billing_npi) AS name,
                COALESCE(p.state, '') AS state
            FROM claims c
            LEFT JOIN providers p ON c.billing_npi = p.npi
            WHERE c.hcpcs_code IN ('T1019','T1005','S5125','S5130','S5150','H2015','H0036',
                                    'H2017','T2020','H2019','97110','97530','97140','97116')
            GROUP BY c.billing_npi, c.claim_month, p.name, p.state
            HAVING SUM(c.claims) * 15.0 / 60.0 / 30.0 > 24
        )
        SELECT billing_npi, claim_month, total_claims, total_paid, est_daily_hours, name, state
        FROM timed_monthly
        WHERE total_paid > 50000
        ORDER BY total_paid DESC
        LIMIT 50
    """).fetchall()

    if rows:
        providers = []
        total_impact = 0
        for r in rows:
            npi, month, claims, paid, hours, name, state = r
            excess_ratio = (hours - 24) / hours if hours > 24 else 0
            excess_amount = paid * excess_ratio
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(excess_amount), 'score': float(hours),
                'evidence': f"Est. {hours:.1f} hr/day timed services (max=24), "
                            f"month={month}, {format_dollars(paid)}"
            })
            total_impact += excess_amount
        findings.append(make_finding('H1016', providers[:20], total_impact, 'high',
                                     'impossible_provider_day_24h',
                                     f"Impossible provider-day: {len(providers)} months >24hr/day"))

    # H1020: Provider billing >20 E&M visits per day
    rows = con.execute("""
        WITH em_monthly AS (
            SELECT
                c.billing_npi,
                c.claim_month,
                SUM(c.claims) AS total_em_claims,
                SUM(c.paid) AS total_paid,
                SUM(c.claims) * 1.0 / 22.0 AS est_daily_visits,
                COALESCE(p.name, 'NPI ' || c.billing_npi) AS name,
                COALESCE(p.state, '') AS state
            FROM claims c
            LEFT JOIN providers p ON c.billing_npi = p.npi
            WHERE c.hcpcs_code IN ('99213', '99214', '99215', '99212', '99211')
            GROUP BY c.billing_npi, c.claim_month, p.name, p.state
            HAVING SUM(c.claims) * 1.0 / 22.0 > 20
        )
        SELECT billing_npi, claim_month, total_em_claims, total_paid,
               est_daily_visits, name, state
        FROM em_monthly
        WHERE total_paid > 10000
        ORDER BY total_paid DESC
        LIMIT 30
    """).fetchall()

    if rows:
        providers = []
        total_impact = 0
        for r in rows:
            npi, month, claims, paid, daily, name, state = r
            excess_ratio = (daily - 20) / daily if daily > 20 else 0
            excess = paid * excess_ratio
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(excess), 'score': float(daily),
                'evidence': f"Est. {daily:.0f} E&M visits/day (max=20), month={month}, "
                            f"{format_dollars(paid)}"
            })
            total_impact += excess
        findings.append(make_finding('H1020', providers[:20], total_impact, 'high',
                                     'impossible_em_visits_day',
                                     f"Impossible E&M visits/day: {len(providers)} provider-months"))

    # H1025: Provider billing 7 days/week sustained (estimated from claims volume)
    rows = con.execute("""
        WITH monthly_patterns AS (
            SELECT
                billing_npi,
                COUNT(DISTINCT claim_month) AS active_months,
                SUM(claims) AS total_claims,
                SUM(paid) AS total_paid,
                AVG(claims) AS avg_monthly_claims
            FROM claims
            WHERE hcpcs_code IN ('T1019','T1005','H2015','H0036')
            GROUP BY billing_npi
            HAVING COUNT(DISTINCT claim_month) >= 6
        )
        SELECT mp.billing_npi, mp.active_months, mp.total_claims, mp.total_paid,
               mp.avg_monthly_claims,
               mp.avg_monthly_claims / 30.0 AS est_daily_claims,
               COALESCE(p.name, 'NPI ' || mp.billing_npi) AS name,
               COALESCE(p.state, '') AS state
        FROM monthly_patterns mp
        LEFT JOIN providers p ON mp.billing_npi = p.npi
        WHERE mp.avg_monthly_claims / 30.0 > 10
          AND mp.total_paid > 500000
        ORDER BY mp.total_paid DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, months, claims, paid, avg_monthly, daily, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': float(daily),
                'evidence': f"Sustained billing: {months} months, est. {daily:.0f} claims/day, "
                            f"{format_dollars(paid)}"
            })
        findings.append(make_finding('H1025', providers[:20],
                                     sum(p['amount'] for p in providers), 'medium',
                                     'no_days_off',
                                     f"Sustained daily billing: {len(providers)} providers"))

    print(f"  Impossible provider-day: {len(findings)} findings")
    return findings


def run_pharmacy_fraud(con):
    """8J: Pharmacy and prescription drug fraud detection (H1046-H1055)."""
    print("\n--- 8J: Pharmacy Fraud ---")
    findings = []

    # H1046: Pharmacy with >$10M from single J-code
    rows = con.execute("""
        SELECT
            c.billing_npi,
            c.hcpcs_code,
            SUM(c.paid) AS code_paid,
            SUM(c.claims) AS code_claims,
            COALESCE(p.name, 'NPI ' || c.billing_npi) AS name,
            COALESCE(p.state, '') AS state
        FROM claims c
        LEFT JOIN providers p ON c.billing_npi = p.npi
        WHERE c.hcpcs_code LIKE 'J%'
        GROUP BY c.billing_npi, c.hcpcs_code, p.name, p.state
        HAVING SUM(c.paid) > 10000000
        ORDER BY SUM(c.paid) DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, code, paid, claims, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': float(paid / 1e6),
                'evidence': f"Single J-code {code}: {format_dollars(paid)}, {claims:,} claims"
            })
        findings.append(make_finding('H1046', providers[:20],
                                     sum(p['amount'] for p in providers), 'medium',
                                     'pharmacy_single_drug',
                                     f"Pharmacy single-drug concentration: {len(providers)} providers"))

    # H1049: Pharmacy rate outlier for J-codes
    rows = con.execute("""
        WITH jcode_providers AS (
            SELECT billing_npi,
                   SUM(paid) AS total_paid,
                   SUM(claims) AS total_claims,
                   SUM(paid) / NULLIF(SUM(claims), 0) AS ppc
            FROM claims
            WHERE hcpcs_code LIKE 'J%'
            GROUP BY billing_npi
            HAVING SUM(claims) >= 50
        ),
        jcode_stats AS (
            SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppc) AS median_ppc
            FROM jcode_providers
        )
        SELECT jp.billing_npi, jp.ppc, js.median_ppc,
               jp.ppc / NULLIF(js.median_ppc, 0) AS ratio,
               jp.total_paid,
               COALESCE(p.name, 'NPI ' || jp.billing_npi) AS name,
               COALESCE(p.state, '') AS state
        FROM jcode_providers jp
        CROSS JOIN jcode_stats js
        LEFT JOIN providers p ON jp.billing_npi = p.npi
        WHERE js.median_ppc > 0 AND jp.ppc > 3 * js.median_ppc
          AND jp.total_paid > 500000
        ORDER BY jp.total_paid DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, ppc, median, ratio, paid, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': float(ratio),
                'evidence': f"J-code rate: ${ppc:,.2f}/claim vs median ${median:,.2f} ({ratio:.1f}x), "
                            f"total={format_dollars(paid)}"
            })
        findings.append(make_finding('H1049', providers[:20],
                                     sum(p['amount'] for p in providers), 'medium',
                                     'pharmacy_rate_outlier',
                                     f"Pharmacy rate outlier: {len(providers)} providers >3x median"))

    # H1050: New pharmacy rapid entrant
    rows = con.execute("""
        WITH pharmacy_monthly AS (
            SELECT billing_npi,
                   MIN(claim_month) AS first_month,
                   COUNT(DISTINCT claim_month) AS num_months,
                   SUM(paid) AS total_paid
            FROM claims
            WHERE hcpcs_code LIKE 'J%'
            GROUP BY billing_npi
            HAVING COUNT(DISTINCT claim_month) <= 6 AND SUM(paid) > 1000000
        )
        SELECT pm.billing_npi, pm.num_months, pm.total_paid, pm.first_month,
               COALESCE(p.name, 'NPI ' || pm.billing_npi) AS name,
               COALESCE(p.state, '') AS state
        FROM pharmacy_monthly pm
        LEFT JOIN providers p ON pm.billing_npi = p.npi
        ORDER BY pm.total_paid DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, months, paid, first, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': float(paid / max(months, 1)),
                'evidence': f"New pharmacy: {months} months, {format_dollars(paid)}, first={first}"
            })
        findings.append(make_finding('H1050', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'pharmacy_rapid_entrant',
                                     f"New pharmacy rapid entrants: {len(providers)} providers"))

    print(f"  Pharmacy fraud: {len(findings)} findings")
    return findings


def run_addiction_treatment_fraud(con):
    """8K: Sober home and addiction treatment fraud detection (H1056-H1065)."""
    print("\n--- 8K: Addiction Treatment Fraud ---")
    findings = []

    addiction_codes = ','.join(f"'H{i:04d}'" for i in range(1, 21))

    # H1057: High per-beneficiary billing
    rows = con.execute(f"""
        WITH addiction_providers AS (
            SELECT
                c.billing_npi,
                c.claim_month,
                SUM(c.paid) AS month_paid,
                SUM(c.beneficiaries) AS month_benes,
                COALESCE(p.name, 'NPI ' || c.billing_npi) AS name,
                COALESCE(p.state, '') AS state
            FROM claims c
            LEFT JOIN providers p ON c.billing_npi = p.npi
            WHERE c.hcpcs_code IN ({addiction_codes})
            GROUP BY c.billing_npi, c.claim_month, p.name, p.state
            HAVING SUM(c.paid) > 500000 AND SUM(c.beneficiaries) < 50
                   AND SUM(c.beneficiaries) > 0
        )
        SELECT billing_npi, claim_month, month_paid, month_benes,
               month_paid / month_benes AS paid_per_bene, name, state
        FROM addiction_providers
        ORDER BY month_paid DESC
        LIMIT 30
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, month, paid, benes, ppb, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': float(ppb),
                'evidence': f"Addiction: ${paid:,.0f}/month for {benes} benes "
                            f"(${ppb:,.0f}/bene), month={month}"
            })
        findings.append(make_finding('H1057', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'addiction_high_per_bene',
                                     f"Addiction high per-bene: {len(providers)} provider-months"))

    # H1065: Rapid exit pattern for substance abuse providers
    rows = con.execute(f"""
        WITH addiction_timeline AS (
            SELECT billing_npi,
                   MIN(claim_month) AS first_month,
                   MAX(claim_month) AS last_month,
                   COUNT(DISTINCT claim_month) AS num_months,
                   SUM(paid) AS total_paid
            FROM claims
            WHERE hcpcs_code IN ({addiction_codes})
            GROUP BY billing_npi
            HAVING COUNT(DISTINCT claim_month) <= 18 AND SUM(paid) > 1000000
        )
        SELECT at2.billing_npi, at2.num_months, at2.total_paid,
               at2.first_month, at2.last_month,
               COALESCE(p.name, 'NPI ' || at2.billing_npi) AS name,
               COALESCE(p.state, '') AS state
        FROM addiction_timeline at2
        LEFT JOIN providers p ON at2.billing_npi = p.npi
        ORDER BY at2.total_paid DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, months, paid, first, last, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': float(paid / max(months, 1)),
                'evidence': f"Addiction rapid exit: {months} months ({first} to {last}), "
                            f"{format_dollars(paid)}"
            })
        findings.append(make_finding('H1065', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'addiction_rapid_exit',
                                     f"Addiction rapid exit: {len(providers)} providers"))

    print(f"  Addiction treatment fraud: {len(findings)} findings")
    return findings


def run_genetic_testing_fraud(con):
    """8L: Genetic testing fraud detection (H1066-H1070)."""
    print("\n--- 8L: Genetic Testing Fraud ---")
    findings = []

    # H1066: High per-beneficiary genetic testing
    rows = con.execute("""
        WITH genetic_providers AS (
            SELECT billing_npi,
                   SUM(paid) AS total_paid,
                   SUM(beneficiaries) AS total_benes,
                   SUM(paid) / NULLIF(SUM(beneficiaries), 0) AS paid_per_bene
            FROM claims
            WHERE hcpcs_code LIKE '81%'
            GROUP BY billing_npi
            HAVING SUM(paid) > 5000000 AND SUM(beneficiaries) < 100
                   AND SUM(beneficiaries) > 0
        )
        SELECT gp.billing_npi, gp.total_paid, gp.total_benes, gp.paid_per_bene,
               COALESCE(p.name, 'NPI ' || gp.billing_npi) AS name,
               COALESCE(p.state, '') AS state
        FROM genetic_providers gp
        LEFT JOIN providers p ON gp.billing_npi = p.npi
        ORDER BY gp.total_paid DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, paid, benes, ppb, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': float(ppb),
                'evidence': f"Genetic testing: {format_dollars(paid)} for {benes} benes "
                            f"(${ppb:,.0f}/bene)"
            })
        findings.append(make_finding('H1066', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'genetic_high_per_bene',
                                     f"Genetic testing high per-bene: {len(providers)} providers"))

    # H1069: New genetic testing rapid entrant
    rows = con.execute("""
        WITH genetic_monthly AS (
            SELECT billing_npi,
                   MIN(claim_month) AS first_month,
                   COUNT(DISTINCT claim_month) AS num_months,
                   SUM(paid) AS total_paid
            FROM claims
            WHERE hcpcs_code LIKE '81%'
            GROUP BY billing_npi
            HAVING COUNT(DISTINCT claim_month) <= 12 AND SUM(paid) > 1000000
        )
        SELECT gm.billing_npi, gm.num_months, gm.total_paid, gm.first_month,
               COALESCE(p.name, 'NPI ' || gm.billing_npi) AS name,
               COALESCE(p.state, '') AS state
        FROM genetic_monthly gm
        LEFT JOIN providers p ON gm.billing_npi = p.npi
        ORDER BY gm.total_paid DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, months, paid, first, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': float(paid / max(months, 1)),
                'evidence': f"New genetic testing: {months} months, {format_dollars(paid)}, first={first}"
            })
        findings.append(make_finding('H1069', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'genetic_rapid_entrant',
                                     f"New genetic testing entrants: {len(providers)} providers"))

    # H1070: Genetic testing market concentration
    rows = con.execute("""
        WITH code_totals AS (
            SELECT hcpcs_code, SUM(paid) AS total_paid
            FROM claims
            WHERE hcpcs_code LIKE '81%'
            GROUP BY hcpcs_code
            HAVING SUM(paid) > 1000000
        ),
        top_providers AS (
            SELECT c.hcpcs_code, c.billing_npi, SUM(c.paid) AS provider_paid
            FROM claims c
            INNER JOIN code_totals ct ON c.hcpcs_code = ct.hcpcs_code
            GROUP BY c.hcpcs_code, c.billing_npi
        ),
        ranked AS (
            SELECT hcpcs_code,
                   SUM(provider_paid) AS total,
                   SUM(CASE WHEN rn <= 5 THEN provider_paid ELSE 0 END) AS top5_paid
            FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY hcpcs_code ORDER BY provider_paid DESC) AS rn
                FROM top_providers
            )
            GROUP BY hcpcs_code
            HAVING SUM(CASE WHEN rn <= 5 THEN provider_paid ELSE 0 END)
                   / NULLIF(SUM(provider_paid), 0) > 0.5
        )
        SELECT hcpcs_code, top5_paid, total,
               top5_paid / NULLIF(total, 0) AS concentration
        FROM ranked
        ORDER BY total DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            code, top5, total, conc = r
            providers.append({
                'npi': f"CODE_{code}", 'name': f"Genetic code {code}",
                'state': 'NA',
                'amount': float(top5), 'score': float(conc),
                'evidence': f"Code {code}: top 5 providers = {conc:.1%} of {format_dollars(total)}"
            })
        findings.append(make_finding('H1070', providers[:20],
                                     sum(p['amount'] for p in providers), 'medium',
                                     'genetic_market_concentration',
                                     f"Genetic testing concentration: {len(providers)} codes"))

    print(f"  Genetic testing fraud: {len(findings)} findings")
    return findings


def main():
    t0 = time.time()
    os.makedirs(FINDINGS_DIR, exist_ok=True)
    con = get_connection(read_only=True)

    all_findings = []

    all_findings.extend(run_impossible_volumes(con))
    all_findings.extend(run_upcoding(con))
    all_findings.extend(run_unbundling(con))
    all_findings.extend(run_high_risk_categories(con))
    all_findings.extend(run_phantom_billing(con))
    all_findings.extend(run_adjustment_anomalies(con))
    all_findings.extend(run_duplicate_billing(con))

    # Gap analysis: new domain-specific rules
    all_findings.extend(run_aba_therapy_fraud(con))
    all_findings.extend(run_impossible_provider_day(con))
    all_findings.extend(run_pharmacy_fraud(con))
    all_findings.extend(run_addiction_treatment_fraud(con))
    all_findings.extend(run_genetic_testing_fraud(con))

    output_path = os.path.join(FINDINGS_DIR, 'category_8.json')
    with open(output_path, 'w') as f:
        json.dump(all_findings, f, indent=2, default=str)

    print(f"\nTotal Category 8 findings (incl. gap analysis): {len(all_findings)}")
    total_impact = sum(f.get('total_impact', 0) for f in all_findings)
    print(f"Total estimated impact: {format_dollars(total_impact)}")
    print(f"Findings written to {output_path}")

    con.close()
    print(f"\nMilestone 7 complete. Time: {time.time() - t0:.1f}s")


if __name__ == '__main__':
    main()
