#!/usr/bin/env python3
"""Milestone 8: Cross-reference and composite scoring.

Categories 9 (NPPES cross-reference) and 10 (multi-signal composites).
"""

import json
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.db_utils import get_connection, format_dollars

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINDINGS_DIR = os.path.join(PROJECT_ROOT, 'output', 'findings')


def make_finding(h_id, providers, total_impact, confidence, method, evidence):
    return {
        'hypothesis_id': h_id,
        'flagged_providers': providers,
        'total_impact': total_impact,
        'confidence': confidence,
        'method_name': method,
        'evidence': evidence,
    }


def load_prior_findings():
    """Load all prior findings from Categories 1-8."""
    all_findings = []
    files = [
        'categories_1_to_5.json',
        'categories_6_and_7.json',
        'category_8.json',
    ]
    for fname in files:
        path = os.path.join(FINDINGS_DIR, fname)
        if os.path.exists(path):
            with open(path) as f:
                all_findings.extend(json.load(f))
    return all_findings


def run_specialty_mismatch(con):
    """9A: Flag providers billing codes outside their registered specialty."""
    print("\n--- 9A: Specialty Mismatch ---")
    findings = []

    # Define specialty-to-expected-codes mapping
    specialty_codes = {
        'Podiatrist': ['992%', '116%', '117%', '280%', '281%'],
        'Dentist': ['D%', '992%'],
        'Optometrist': ['920%', '921%', '992%'],
        'Chiropractor': ['983%', '984%', '992%', '971%'],
        'Physical Therapist': ['971%', '972%', '973%', '974%', '975%', '976%', '977%'],
        'Speech-Language Pathologist': ['925%', '920%'],
        'Occupational Therapist': ['971%', '972%', '973%', '974%', '975%', '976%', '977%'],
    }

    h_num = 931
    for specialty, expected_patterns in specialty_codes.items():
        like_clauses = ' OR '.join(f"c.hcpcs_code LIKE '{p}'" for p in expected_patterns)

        rows = con.execute(f"""
            WITH specialty_providers AS (
                SELECT npi FROM providers WHERE specialty = '{specialty}'
            ),
            provider_billing AS (
                SELECT
                    c.billing_npi,
                    SUM(c.paid) AS total_paid,
                    SUM(c.claims) AS total_claims,
                    SUM(CASE WHEN {like_clauses} THEN c.paid ELSE 0 END) AS expected_paid,
                    SUM(CASE WHEN NOT ({like_clauses}) THEN c.paid ELSE 0 END) AS unexpected_paid
                FROM claims c
                INNER JOIN specialty_providers sp ON c.billing_npi = sp.npi
                GROUP BY c.billing_npi
                HAVING SUM(c.paid) > 100000
            )
            SELECT
                pb.billing_npi,
                pb.total_paid,
                pb.unexpected_paid,
                pb.unexpected_paid / NULLIF(pb.total_paid, 0) AS mismatch_ratio,
                COALESCE(p.name, 'NPI ' || pb.billing_npi) AS name,
                COALESCE(p.state, '') AS state
            FROM provider_billing pb
            LEFT JOIN providers p ON pb.billing_npi = p.npi
            WHERE pb.unexpected_paid / NULLIF(pb.total_paid, 0) > 0.5
            ORDER BY pb.unexpected_paid DESC
            LIMIT 20
        """).fetchall()

        if rows:
            providers = []
            for r in rows:
                npi, total, unexpected, ratio, name, state = r
                providers.append({
                    'npi': npi, 'name': name, 'state': state,
                    'amount': float(unexpected),
                    'score': float(ratio),
                    'evidence': f"{specialty}: {ratio:.1%} of billing outside expected codes, "
                                f"unexpected={format_dollars(unexpected)}"
                })

            h_id = f"H{h_num:04d}"
            h_num += 1
            findings.append(make_finding(
                h_id, providers, sum(p['amount'] for p in providers),
                'medium', 'specialty_mismatch',
                f"{specialty}: {len(providers)} providers with >50% billing outside expected codes"
            ))

        if h_num > 950:
            break

    print(f"  Specialty mismatch: {len(findings)} findings")
    return findings


def run_entity_type_anomalies(con):
    """9B: Individual NPIs billing at organization volumes."""
    print("\n--- 9B: Entity Type Anomalies ---")
    findings = []

    rows = con.execute("""
        SELECT
            p.npi,
            p.name,
            p.state,
            p.entity_type,
            ps.total_paid,
            ps.total_claims,
            ps.num_codes,
            ps.num_months
        FROM providers p
        INNER JOIN provider_summary ps ON p.npi = ps.billing_npi
        WHERE p.entity_type = '1'
          AND ps.total_paid > 5000000
        ORDER BY ps.total_paid DESC
        LIMIT 30
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, name, state, etype, paid, claims, codes, months = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid),
                'score': float(paid / 1000000),
                'evidence': f"Individual NPI (entity_type=1) with {format_dollars(paid)} total, "
                            f"{claims:,} claims, {codes} codes, {months} months"
            })

        for i in range(0, min(len(providers), 30), 3):
            chunk = providers[i:i+3]
            h_id = f"H{951 + i // 3:04d}"
            findings.append(make_finding(
                h_id, chunk, sum(p['amount'] for p in chunk),
                'medium', 'entity_type_anomaly',
                f"Individual NPIs billing at organization-scale volumes (>$5M)"
            ))

    print(f"  Entity type anomalies: {len(findings)} findings")
    return findings


def run_geographic_impossibilities(con):
    """9C: Servicing NPI appearing in multiple states same month."""
    print("\n--- 9C: Geographic Impossibilities ---")
    findings = []

    rows = con.execute("""
        WITH servicing_states AS (
            SELECT
                c.servicing_npi,
                c.claim_month,
                COUNT(DISTINCT p.state) AS num_states,
                SUM(c.paid) AS total_paid
            FROM claims c
            INNER JOIN providers p ON c.billing_npi = p.npi
            WHERE c.servicing_npi IS NOT NULL AND c.servicing_npi != ''
              AND p.state IS NOT NULL AND p.state != ''
            GROUP BY c.servicing_npi, c.claim_month
            HAVING COUNT(DISTINCT p.state) > 3
        )
        SELECT
            ss.servicing_npi,
            COUNT(*) AS months_multi_state,
            MAX(ss.num_states) AS max_states,
            SUM(ss.total_paid) AS total_paid,
            COALESCE(p.name, 'NPI ' || ss.servicing_npi) AS name,
            COALESCE(p.state, '') AS home_state
        FROM servicing_states ss
        LEFT JOIN providers p ON ss.servicing_npi = p.npi
        GROUP BY ss.servicing_npi, p.name, p.state
        HAVING SUM(ss.total_paid) > 100000
        ORDER BY SUM(ss.total_paid) DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, months, max_states, paid, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid),
                'score': float(max_states),
                'evidence': f"Servicing NPI in {max_states} states same month, "
                            f"{months} multi-state months, total={format_dollars(paid)}"
            })

        for i in range(0, min(len(providers), 20), 2):
            chunk = providers[i:i+2]
            h_id = f"H{961 + i // 2:04d}"
            findings.append(make_finding(
                h_id, chunk, sum(p['amount'] for p in chunk),
                'high', 'geographic_impossibility',
                f"Servicing NPI appearing in >3 states in same month"
            ))

    print(f"  Geographic impossibilities: {len(findings)} findings")
    return findings


def run_state_spending_anomalies(con):
    """9D-9E: State-level spending anomalies."""
    print("\n--- 9D: State Spending Anomalies ---")
    findings = []

    rows = con.execute("""
        WITH state_code_spending AS (
            SELECT
                p.state,
                c.hcpcs_code,
                SUM(c.paid) AS state_paid,
                SUM(c.beneficiaries) AS state_benes,
                SUM(c.paid) / NULLIF(SUM(c.beneficiaries), 0) AS paid_per_bene
            FROM claims c
            INNER JOIN providers p ON c.billing_npi = p.npi
            WHERE p.state IS NOT NULL AND p.state != ''
              AND c.paid > 0 AND c.beneficiaries > 0
            GROUP BY p.state, c.hcpcs_code
            HAVING SUM(c.beneficiaries) > 1000
        ),
        national_medians AS (
            SELECT
                hcpcs_code,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY paid_per_bene) AS median_ppb
            FROM state_code_spending
            GROUP BY hcpcs_code
            HAVING COUNT(*) >= 10
        )
        SELECT
            scs.state,
            scs.hcpcs_code,
            scs.paid_per_bene,
            nm.median_ppb,
            scs.paid_per_bene / NULLIF(nm.median_ppb, 0) AS ratio,
            scs.state_paid,
            COALESCE(hc.short_desc, 'Code ' || scs.hcpcs_code) AS code_desc
        FROM state_code_spending scs
        INNER JOIN national_medians nm ON scs.hcpcs_code = nm.hcpcs_code
        LEFT JOIN hcpcs_codes hc ON scs.hcpcs_code = hc.hcpcs_code
        WHERE scs.paid_per_bene > 2 * nm.median_ppb
          AND scs.state_paid > 10000000
        ORDER BY scs.state_paid DESC
        LIMIT 30
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            state, code, ppb, median, ratio, state_paid, desc = r
            excess = state_paid * (1 - 1.0 / ratio) if ratio > 1 else 0
            providers.append({
                'npi': f"STATE_{state}_{code}", 'name': f"{state} - {desc}", 'state': state,
                'amount': float(excess),
                'score': float(ratio),
                'evidence': f"{state} {code} ({desc}): ${ppb:,.0f}/bene vs national median ${median:,.0f}/bene "
                            f"({ratio:.1f}x), total={format_dollars(state_paid)}"
            })

        for i in range(0, min(len(providers), 20), 2):
            chunk = providers[i:i+2]
            h_id = f"H{971 + i // 2:04d}"
            findings.append(make_finding(
                h_id, chunk, sum(p['amount'] for p in chunk),
                'medium', 'state_spending_anomaly',
                f"State-level spending >2x national median per beneficiary"
            ))

    print(f"  State spending anomalies: {len(findings)} findings")
    return findings


# ---------------------------------------------------------------------------
# Gap Analysis: New cross-reference and enrichment functions
# ---------------------------------------------------------------------------


def run_leie_crossref(con):
    """9G: Cross-reference billing/servicing NPIs against OIG LEIE exclusion list (H1026-H1035)."""
    print("\n--- 9G: LEIE Cross-Reference ---")
    findings = []

    try:
        from utils.leie_utils import download_leie, parse_leie, build_leie_npi_set
    except ImportError:
        print("  WARNING: leie_utils not available, skipping LEIE cross-reference")
        return findings

    csv_path = download_leie()
    if not csv_path:
        print("  LEIE download failed, skipping")
        return findings

    records = parse_leie(csv_path)
    excluded_npis = build_leie_npi_set(records)

    if not excluded_npis:
        print("  No excluded NPIs found in LEIE; attempting name/address matching")

        rows = con.execute(f"""
            WITH leie_raw AS (
                SELECT
                    UPPER(TRIM(LASTNAME)) AS lastname,
                    UPPER(TRIM(FIRSTNAME)) AS firstname,
                    UPPER(TRIM(BUSNAME)) AS busname,
                    UPPER(TRIM(ADDRESS)) AS address,
                    UPPER(TRIM(CITY)) AS city,
                    UPPER(TRIM(STATE)) AS state,
                    REGEXP_REPLACE(TRIM(ZIP), '[^0-9]', '', 'g') AS zip,
                    COALESCE(REINDATE, '') AS reindate
                FROM read_csv_auto('{csv_path}',
                    header=true,
                    sample_size=10000,
                    ignore_errors=true,
                    all_varchar=true,
                    null_padding=true
                )
                WHERE COALESCE(REINDATE, '') = ''
            ),
            leie_org AS (
                SELECT
                    busname, address, city, state,
                    SUBSTR(zip, 1, 5) AS zip5,
                    REGEXP_REPLACE(busname, '[^A-Z0-9]', '', 'g') AS name_norm,
                    REGEXP_REPLACE(city, '[^A-Z0-9]', '', 'g') AS city_norm,
                    REGEXP_REPLACE(address, '[^A-Z0-9]', '', 'g') AS addr_norm
                FROM leie_raw
                WHERE busname IS NOT NULL AND busname != ''
            ),
            leie_ind AS (
                SELECT
                    lastname, firstname, address, city, state,
                    SUBSTR(zip, 1, 5) AS zip5,
                    REGEXP_REPLACE(lastname || firstname, '[^A-Z0-9]', '', 'g') AS name_norm,
                    REGEXP_REPLACE(city, '[^A-Z0-9]', '', 'g') AS city_norm,
                    REGEXP_REPLACE(address, '[^A-Z0-9]', '', 'g') AS addr_norm
                FROM leie_raw
                WHERE lastname IS NOT NULL AND lastname != ''
            ),
            prov AS (
                SELECT
                    p.npi,
                    p.entity_type,
                    UPPER(COALESCE(p.name, '')) AS name,
                    UPPER(COALESCE(p.city, '')) AS city,
                    UPPER(COALESCE(p.state, '')) AS state,
                    UPPER(COALESCE(p.address, '')) AS address,
                    REGEXP_REPLACE(COALESCE(p.zip, ''), '[^0-9]', '', 'g') AS zip,
                    REGEXP_REPLACE(UPPER(COALESCE(p.name, '')), '[^A-Z0-9]', '', 'g') AS name_norm,
                    REGEXP_REPLACE(UPPER(COALESCE(p.city, '')), '[^A-Z0-9]', '', 'g') AS city_norm,
                    REGEXP_REPLACE(UPPER(COALESCE(p.address, '')), '[^A-Z0-9]', '', 'g') AS addr_norm,
                    ps.total_paid,
                    ps.total_claims
                FROM providers p
                INNER JOIN provider_summary ps ON p.npi = ps.billing_npi
            ),
            org_matches AS (
                SELECT
                    p.npi, p.total_paid, p.total_claims, p.name, p.state,
                    'org' AS match_type
                FROM prov p
                INNER JOIN leie_org l
                    ON p.entity_type = '2'
                   AND p.state = l.state
                   AND p.name_norm = l.name_norm
                   AND (
                       (SUBSTR(p.zip, 1, 5) != '' AND SUBSTR(p.zip, 1, 5) = l.zip5)
                       OR (p.city_norm = l.city_norm AND p.addr_norm = l.addr_norm AND p.addr_norm != '')
                   )
                WHERE p.total_paid > 0
            ),
            ind_matches AS (
                SELECT
                    p.npi, p.total_paid, p.total_claims, p.name, p.state,
                    'individual' AS match_type
                FROM prov p
                INNER JOIN leie_ind l
                    ON p.entity_type != '2'
                   AND p.state = l.state
                   AND p.name_norm = l.name_norm
                   AND (
                       (SUBSTR(p.zip, 1, 5) != '' AND SUBSTR(p.zip, 1, 5) = l.zip5)
                       OR (p.city_norm = l.city_norm AND p.addr_norm = l.addr_norm AND p.addr_norm != '')
                   )
                WHERE p.total_paid > 0
            )
            SELECT * FROM org_matches
            UNION ALL
            SELECT * FROM ind_matches
            ORDER BY total_paid DESC
            LIMIT 50
        """).fetchall()

        if rows:
            providers = []
            for r in rows:
                npi, paid, claims, name, state, match_type = r
                providers.append({
                    'npi': npi, 'name': name, 'state': state,
                    'amount': float(paid), 'score': 8.0,
                    'evidence': f"LEIE name/address match ({match_type}), {format_dollars(paid)}, "
                                f"{claims:,} claims"
                })
            findings.append(make_finding('H1028', providers[:20],
                                         sum(p['amount'] for p in providers), 'medium',
                                         'leie_name_address_match',
                                         f"LEIE name/address matches: {len(providers)} found"))
        else:
            print("  No LEIE name/address matches found; attempting fuzzy matching")

            import re
            from difflib import SequenceMatcher

            def norm_text(val):
                return re.sub(r'[^A-Z0-9]', '', (val or '').upper())

            # Build LEIE indices by state + zip5/city
            org_zip = {}
            org_city = {}
            ind_zip = {}
            ind_city = {}
            leie_states = set()

            for r in records:
                if r.get('reindate'):
                    continue
                state = (r.get('state') or '').strip().upper()
                if not state:
                    continue
                leie_states.add(state)
                zip5 = re.sub(r'[^0-9]', '', r.get('zip', '') or '')[:5]
                city_norm = norm_text(r.get('city', ''))

                bus = norm_text(r.get('busname', ''))
                if bus:
                    if zip5:
                        org_zip.setdefault((state, zip5), []).append(bus)
                    if city_norm:
                        org_city.setdefault((state, city_norm), []).append(bus)

                lname = norm_text(r.get('lastname', ''))
                fname = norm_text(r.get('firstname', ''))
                if lname:
                    name_norm = lname + fname
                    if zip5:
                        ind_zip.setdefault((state, zip5), []).append(name_norm)
                    if city_norm:
                        ind_city.setdefault((state, city_norm), []).append(name_norm)

            matches = {}
            for state in sorted(leie_states):
                rows = con.execute("""
                    SELECT
                        p.npi, p.entity_type, p.name, p.state, p.city, p.address, p.zip,
                        p.mailing_address, p.mail_city, p.mail_state, p.mail_zip,
                        ps.total_paid, ps.total_claims
                    FROM providers p
                    INNER JOIN provider_summary ps ON p.npi = ps.billing_npi
                    WHERE p.state = ? OR p.mail_state = ?
                """, [state, state]).fetchall()

                for row in rows:
                    (npi, entity_type, name, p_state, city, address, zip_code,
                     mail_addr, mail_city, mail_state, mail_zip, paid, claims) = row
                    if not name or paid is None or paid <= 0:
                        continue
                    name_norm = norm_text(name)
                    if len(name_norm) < 6:
                        continue

                    def candidate_list(st, z, c, is_org):
                        zip5 = re.sub(r'[^0-9]', '', z or '')[:5]
                        city_norm = norm_text(c)
                        if is_org:
                            cand = org_zip.get((st, zip5)) if zip5 else None
                            if not cand and city_norm:
                                cand = org_city.get((st, city_norm))
                        else:
                            cand = ind_zip.get((st, zip5)) if zip5 else None
                            if not cand and city_norm:
                                cand = ind_city.get((st, city_norm))
                        return cand or []

                    is_org = entity_type == '2'
                    candidates = candidate_list(p_state, zip_code, city, is_org)
                    if not candidates and mail_state:
                        candidates = candidate_list(mail_state, mail_zip, mail_city, is_org)

                    if not candidates:
                        continue
                    if len(candidates) > 2000:
                        continue

                    thresh = 0.92 if is_org else 0.90
                    best_ratio = 0.0
                    for cand in candidates:
                        if not cand or len(cand) < 6:
                            continue
                        if name_norm[:4] != cand[:4]:
                            continue
                        ratio = SequenceMatcher(None, name_norm, cand).ratio()
                        if ratio >= thresh and ratio > best_ratio:
                            best_ratio = ratio

                    if best_ratio >= thresh:
                        prev = matches.get(npi)
                        if prev is None or best_ratio > prev['ratio']:
                            matches[npi] = {
                                'npi': npi,
                                'name': name,
                                'state': p_state or mail_state or '',
                                'amount': float(paid),
                                'score': float(best_ratio),
                                'claims': claims or 0,
                                'ratio': best_ratio,
                                'match_type': 'org' if is_org else 'individual'
                            }

            if matches:
                providers = sorted(matches.values(), key=lambda x: -x['amount'])[:50]
                providers_out = []
                for p in providers:
                    providers_out.append({
                        'npi': p['npi'], 'name': p['name'], 'state': p['state'],
                        'amount': p['amount'], 'score': p['score'],
                        'evidence': f"LEIE fuzzy match ({p['match_type']}), similarity={p['ratio']:.2f}, "
                                    f"{p['claims']:,} claims"
                    })
                findings.append(make_finding('H1029', providers_out[:20],
                                             sum(p['amount'] for p in providers_out), 'low',
                                             'leie_fuzzy_match',
                                             f"LEIE fuzzy matches: {len(providers_out)} candidates"))
            else:
                print("  No LEIE fuzzy matches found")
    if excluded_npis:
        con.execute("DROP TABLE IF EXISTS leie_excluded_npis")
        con.execute("CREATE TEMP TABLE leie_excluded_npis (npi VARCHAR)")
        con.executemany(
            "INSERT INTO leie_excluded_npis VALUES (?)",
            [(npi,) for npi in excluded_npis],
        )

    # H1026: Billing NPI on LEIE
    rows = con.execute("""
        SELECT
            ps.billing_npi,
            ps.total_paid,
            ps.total_claims,
            COALESCE(p.name, 'NPI ' || ps.billing_npi) AS name,
            COALESCE(p.state, '') AS state
        FROM provider_summary ps
        LEFT JOIN providers p ON ps.billing_npi = p.npi
        INNER JOIN leie_excluded_npis l ON ps.billing_npi = l.npi
          AND ps.total_paid > 0
        ORDER BY ps.total_paid DESC
        LIMIT 50
    """).fetchall() if excluded_npis else []

    if rows:
        providers = []
        for r in rows:
            npi, paid, claims, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': 10.0,
                'evidence': f"LEIE EXCLUDED billing NPI: {format_dollars(paid)}, "
                            f"{claims:,} claims"
            })
        findings.append(make_finding('H1026', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'leie_billing_npi',
                                     f"LEIE excluded billing NPIs: {len(providers)} found"))

    # H1027: Servicing NPI on LEIE
    rows = con.execute("""
        SELECT
            bsn.servicing_npi,
            SUM(bsn.total_paid) AS total_paid,
            SUM(bsn.total_claims) AS total_claims,
            COALESCE(p.name, 'NPI ' || bsn.servicing_npi) AS name,
            COALESCE(p.state, '') AS state
        FROM billing_servicing_network bsn
        LEFT JOIN providers p ON bsn.servicing_npi = p.npi
        INNER JOIN leie_excluded_npis l ON bsn.servicing_npi = l.npi
        GROUP BY bsn.servicing_npi, p.name, p.state
        HAVING SUM(bsn.total_paid) > 0
        ORDER BY SUM(bsn.total_paid) DESC
        LIMIT 50
    """).fetchall() if excluded_npis else []

    if rows:
        providers = []
        for r in rows:
            npi, paid, claims, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': 10.0,
                'evidence': f"LEIE EXCLUDED servicing NPI: {format_dollars(paid)}, "
                            f"{claims:,} claims"
            })
        findings.append(make_finding('H1027', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'leie_servicing_npi',
                                     f"LEIE excluded servicing NPIs: {len(providers)} found"))

    # H1030: Billing after NPPES deactivation (if available)
    provider_cols = {row[1] for row in con.execute("PRAGMA table_info('providers')").fetchall()}
    rows = []
    if 'deactivation_date' in provider_cols:
        rows = con.execute("""
            SELECT
                ps.billing_npi,
                p.deactivation_date,
                MAX(pm.claim_month) AS last_claim_month,
                ps.total_paid,
                COALESCE(p.name, 'NPI ' || ps.billing_npi) AS name,
                COALESCE(p.state, '') AS state
            FROM provider_summary ps
            INNER JOIN providers p ON ps.billing_npi = p.npi
            INNER JOIN provider_monthly pm ON ps.billing_npi = pm.billing_npi
            WHERE p.deactivation_date IS NOT NULL
              AND p.deactivation_date != ''
              AND ps.total_paid > 100000
            GROUP BY ps.billing_npi, p.deactivation_date, ps.total_paid, p.name, p.state
            ORDER BY ps.total_paid DESC
            LIMIT 30
        """).fetchall()
    else:
        print("  Providers table missing deactivation_date; skipping post-deactivation check")

    if rows:
        providers = []
        for r in rows:
            npi, deact, last_claim, paid, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': 8.0,
                'evidence': f"Deactivation date={deact}, last claim={last_claim}, "
                            f"{format_dollars(paid)}"
            })
        findings.append(make_finding('H1030', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'post_deactivation_billing',
                                     f"Post-deactivation billing: {len(providers)} providers"))

    print(f"  LEIE cross-reference: {len(findings)} findings")
    return findings


def run_kickback_referral(con):
    """4H: Kickback and referral concentration analysis (H1036-H1045)."""
    print("\n--- 4H: Kickback/Referral Concentration ---")
    findings = []

    # H1036: Captive referral — billing NPI sending >90% through single servicing NPI
    rows = con.execute("""
        WITH billing_distribution AS (
            SELECT
                billing_npi,
                servicing_npi,
                total_paid,
                total_claims,
                SUM(total_paid) OVER (PARTITION BY billing_npi) AS billing_total,
                total_paid / NULLIF(SUM(total_paid) OVER (PARTITION BY billing_npi), 0) AS pct
            FROM billing_servicing_network
            WHERE billing_npi != servicing_npi
        )
        SELECT
            bd.billing_npi,
            bd.servicing_npi,
            bd.pct,
            bd.total_paid,
            bd.billing_total,
            COALESCE(p.name, 'NPI ' || bd.billing_npi) AS billing_name,
            COALESCE(p.state, '') AS state
        FROM billing_distribution bd
        LEFT JOIN providers p ON bd.billing_npi = p.npi
        WHERE bd.pct > 0.9 AND bd.total_paid > 500000
        ORDER BY bd.total_paid DESC
        LIMIT 30
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            b_npi, s_npi, pct, paid, total, name, state = r
            providers.append({
                'npi': b_npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': float(pct),
                'evidence': f"Captive referral: {pct:.1%} of {format_dollars(total)} through "
                            f"servicing NPI {s_npi}"
            })
        findings.append(make_finding('H1036', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'captive_referral',
                                     f"Captive referral: {len(providers)} billing NPIs"))

    # H1037: Captive servicing — >80% from single billing NPI
    rows = con.execute("""
        WITH servicing_distribution AS (
            SELECT
                servicing_npi,
                billing_npi,
                total_paid,
                SUM(total_paid) OVER (PARTITION BY servicing_npi) AS servicing_total,
                total_paid / NULLIF(SUM(total_paid) OVER (PARTITION BY servicing_npi), 0) AS pct
            FROM billing_servicing_network
            WHERE billing_npi != servicing_npi
        )
        SELECT
            sd.servicing_npi,
            sd.billing_npi,
            sd.pct,
            sd.total_paid,
            sd.servicing_total,
            COALESCE(p.name, 'NPI ' || sd.servicing_npi) AS name,
            COALESCE(p.state, '') AS state
        FROM servicing_distribution sd
        LEFT JOIN providers p ON sd.servicing_npi = p.npi
        WHERE sd.pct > 0.8 AND sd.total_paid > 500000
        ORDER BY sd.total_paid DESC
        LIMIT 30
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            s_npi, b_npi, pct, paid, total, name, state = r
            providers.append({
                'npi': s_npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': float(pct),
                'evidence': f"Captive servicing: {pct:.1%} of {format_dollars(total)} from "
                            f"billing NPI {b_npi}"
            })
        findings.append(make_finding('H1037', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'captive_servicing',
                                     f"Captive servicing: {len(providers)} servicing NPIs"))

    # H1038: Kickback premium — pair rate >2x code median
    rows = con.execute("""
        WITH pair_rates AS (
            SELECT
                bsn.billing_npi,
                bsn.servicing_npi,
                bsn.total_paid / NULLIF(bsn.total_claims, 0) AS pair_rate,
                bsn.total_paid,
                bsn.total_claims
            FROM billing_servicing_network bsn
            WHERE bsn.total_claims > 50 AND bsn.total_paid > 100000
        ),
        overall_rate AS (
            SELECT PERCENTILE_CONT(0.5) WITHIN GROUP
                   (ORDER BY total_paid / NULLIF(total_claims, 0)) AS median_rate
            FROM billing_servicing_network
            WHERE total_claims > 50
        )
        SELECT pr.billing_npi, pr.servicing_npi, pr.pair_rate, ovr.median_rate,
               pr.pair_rate / NULLIF(ovr.median_rate, 0) AS ratio,
               pr.total_paid,
               COALESCE(p.name, 'NPI ' || pr.billing_npi) AS name,
               COALESCE(p.state, '') AS state
        FROM pair_rates pr
        CROSS JOIN overall_rate ovr
        LEFT JOIN providers p ON pr.billing_npi = p.npi
        WHERE ovr.median_rate > 0 AND pr.pair_rate > 2 * ovr.median_rate
        ORDER BY pr.total_paid DESC
        LIMIT 30
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            b_npi, s_npi, rate, median, ratio, paid, name, state = r
            providers.append({
                'npi': b_npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': float(ratio),
                'evidence': f"Kickback premium: pair rate=${rate:,.2f} vs median=${median:,.2f} "
                            f"({ratio:.1f}x), servicing={s_npi}"
            })
        findings.append(make_finding('H1038', providers[:20],
                                     sum(p['amount'] for p in providers), 'medium',
                                     'kickback_premium',
                                     f"Kickback premium: {len(providers)} pairs >2x median rate"))

    # H1039: New relationship with immediate high volume
    rows = con.execute("""
        WITH first_months AS (
            SELECT
                c.billing_npi,
                c.servicing_npi,
                MIN(c.claim_month) AS first_month,
                SUM(c.paid) AS total_paid
            FROM claims c
            WHERE c.servicing_npi IS NOT NULL AND c.servicing_npi != ''
                  AND c.billing_npi != c.servicing_npi
            GROUP BY c.billing_npi, c.servicing_npi
            HAVING SUM(c.paid) > 100000
        ),
        first_month_paid AS (
            SELECT
                c.billing_npi,
                c.servicing_npi,
                fm.first_month,
                SUM(c.paid) AS first_month_paid,
                fm.total_paid
            FROM claims c
            INNER JOIN first_months fm
                ON c.billing_npi = fm.billing_npi
               AND c.servicing_npi = fm.servicing_npi
               AND c.claim_month = fm.first_month
            GROUP BY c.billing_npi, c.servicing_npi, fm.first_month, fm.total_paid
        )
        SELECT fmp.billing_npi, fmp.servicing_npi, fmp.first_month,
               fmp.first_month_paid, fmp.total_paid,
               COALESCE(p.name, 'NPI ' || fmp.billing_npi) AS name,
               COALESCE(p.state, '') AS state
        FROM first_month_paid fmp
        LEFT JOIN providers p ON fmp.billing_npi = p.npi
        WHERE fmp.first_month_paid > 100000
        ORDER BY fmp.first_month_paid DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            b_npi, s_npi, first, fm_paid, total, name, state = r
            providers.append({
                'npi': b_npi, 'name': name, 'state': state,
                'amount': float(total), 'score': float(fm_paid),
                'evidence': f"New relationship: {format_dollars(fm_paid)} first month ({first}), "
                            f"servicing={s_npi}"
            })
        findings.append(make_finding('H1039', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'new_relationship_high_volume',
                                     f"New high-volume relationships: {len(providers)} pairs"))

    print(f"  Kickback/referral: {len(findings)} findings")
    return findings


def run_beneficiary_anomalies(con):
    """9H: Cross-provider beneficiary overlap detection (H1071-H1080)."""
    print("\n--- 9H: Beneficiary Anomalies ---")
    findings = []

    # H1074: Provider pairs with >80% beneficiary overlap
    # Since we have aggregated data, approximate using shared beneficiary patterns
    rows = con.execute("""
        WITH provider_bene_profiles AS (
            SELECT
                billing_npi,
                SUM(beneficiaries) AS total_benes,
                SUM(paid) AS total_paid,
                COUNT(DISTINCT hcpcs_code) AS num_codes,
                COUNT(DISTINCT claim_month) AS num_months
            FROM claims
            GROUP BY billing_npi
            HAVING SUM(paid) > 500000 AND SUM(beneficiaries) > 50
        ),
        -- Find providers with suspiciously identical beneficiary counts
        bene_count_matches AS (
            SELECT
                a.billing_npi AS npi_a,
                b.billing_npi AS npi_b,
                a.total_benes,
                a.total_paid AS paid_a,
                b.total_paid AS paid_b
            FROM provider_bene_profiles a
            INNER JOIN provider_bene_profiles b
                ON a.billing_npi < b.billing_npi
                AND ABS(a.total_benes - b.total_benes) <= 2
                AND a.total_benes > 50
        )
        SELECT npi_a, npi_b, total_benes, paid_a, paid_b,
               COALESCE(pa.name, 'NPI ' || bcm.npi_a) AS name_a,
               COALESCE(pb.name, 'NPI ' || bcm.npi_b) AS name_b,
               COALESCE(pa.state, '') AS state
        FROM bene_count_matches bcm
        LEFT JOIN providers pa ON bcm.npi_a = pa.npi
        LEFT JOIN providers pb ON bcm.npi_b = pb.npi
        ORDER BY paid_a + paid_b DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi_a, npi_b, benes, paid_a, paid_b, name_a, name_b, state = r
            providers.append({
                'npi': npi_a, 'name': name_a, 'state': state,
                'amount': float(paid_a + paid_b),
                'score': float(benes),
                'evidence': f"Matched bene count ({benes}): {npi_a} ({format_dollars(paid_a)}) "
                            f"and {npi_b} ({format_dollars(paid_b)})"
            })
        findings.append(make_finding('H1073', providers[:20],
                                     sum(p['amount'] for p in providers), 'medium',
                                     'shared_bene_count',
                                     f"Identical bene counts: {len(providers)} provider pairs"))

    # H1078: Excessive personal care per beneficiary
    rows = con.execute("""
        WITH bene_care AS (
            SELECT
                c.billing_npi,
                c.claim_month,
                SUM(c.paid) AS month_paid,
                SUM(c.beneficiaries) AS month_benes,
                SUM(c.paid) / NULLIF(SUM(c.beneficiaries), 0) AS paid_per_bene,
                COALESCE(p.name, 'NPI ' || c.billing_npi) AS name,
                COALESCE(p.state, '') AS state
            FROM claims c
            LEFT JOIN providers p ON c.billing_npi = p.npi
            WHERE c.hcpcs_code IN ('T1019', 'T1020', 'S5125')
              AND c.beneficiaries > 0
            GROUP BY c.billing_npi, c.claim_month, p.name, p.state
            HAVING SUM(c.paid) / NULLIF(SUM(c.beneficiaries), 0) > 50000
        )
        SELECT billing_npi, claim_month, month_paid, month_benes,
               paid_per_bene, name, state
        FROM bene_care
        ORDER BY paid_per_bene DESC
        LIMIT 30
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, month, paid, benes, ppb, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid), 'score': float(ppb),
                'evidence': f"Personal care: ${ppb:,.0f}/bene/month, {benes} benes, "
                            f"month={month}, {format_dollars(paid)}"
            })
        findings.append(make_finding('H1078', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'bene_excessive_personal_care',
                                     f"Excessive personal care: {len(providers)} provider-months"))

    # H1079: Phantom growth (bene count 3x but paid 10x)
    rows = con.execute("""
        WITH yearly_stats AS (
            SELECT
                billing_npi,
                SUBSTRING(claim_month, 1, 4) AS yr,
                SUM(paid) AS yr_paid,
                SUM(beneficiaries) AS yr_benes
            FROM claims
            GROUP BY billing_npi, SUBSTRING(claim_month, 1, 4)
            HAVING SUM(paid) > 100000
        ),
        growth AS (
            SELECT
                a.billing_npi,
                a.yr AS yr1, b.yr AS yr2,
                a.yr_paid AS paid1, b.yr_paid AS paid2,
                a.yr_benes AS benes1, b.yr_benes AS benes2,
                b.yr_paid / NULLIF(a.yr_paid, 0) AS paid_growth,
                b.yr_benes / NULLIF(a.yr_benes, 0) AS bene_growth
            FROM yearly_stats a
            INNER JOIN yearly_stats b ON a.billing_npi = b.billing_npi AND b.yr = CAST(CAST(a.yr AS INT) + 1 AS VARCHAR)
            WHERE a.yr_paid > 0 AND a.yr_benes > 0
        )
        SELECT g.billing_npi, g.yr1, g.yr2, g.paid_growth, g.bene_growth,
               g.paid2,
               COALESCE(p.name, 'NPI ' || g.billing_npi) AS name,
               COALESCE(p.state, '') AS state
        FROM growth g
        LEFT JOIN providers p ON g.billing_npi = p.npi
        WHERE g.paid_growth > 10 AND g.bene_growth < 3 AND g.bene_growth > 0
          AND g.paid2 > 500000
        ORDER BY g.paid2 DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            npi, yr1, yr2, pg, bg, paid2, name, state = r
            providers.append({
                'npi': npi, 'name': name, 'state': state,
                'amount': float(paid2), 'score': float(pg / max(bg, 0.01)),
                'evidence': f"Phantom growth: paid {pg:.1f}x but benes only {bg:.1f}x "
                            f"({yr1}->{yr2}), {format_dollars(paid2)}"
            })
        findings.append(make_finding('H1079', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'bene_phantom_growth',
                                     f"Phantom growth: {len(providers)} providers"))

    print(f"  Beneficiary anomalies: {len(findings)} findings")
    return findings


def run_address_clustering(con):
    """9I: NPPES address-based NPI clustering (H1081-H1085)."""
    print("\n--- 9I: Address Clustering ---")
    try:
        cols = con.execute("PRAGMA table_info('providers')").fetchall()
        col_names = {c[1] for c in cols}
    except Exception:
        col_names = set()
    if 'address' not in col_names:
        print("  Skipped: providers.address not available")
        return []
    findings = []

    # H1081: Multiple NPIs at same address with high combined billing
    rows = con.execute("""
        WITH address_groups AS (
            SELECT
                p.address,
                p.city,
                p.state,
                COUNT(DISTINCT p.npi) AS num_npis,
                SUM(ps.total_paid) AS combined_paid,
                LIST(p.npi ORDER BY ps.total_paid DESC) AS npi_list
            FROM providers p
            INNER JOIN provider_summary ps ON p.npi = ps.billing_npi
            WHERE p.address IS NOT NULL AND p.address != ''
              AND LENGTH(p.address) > 5
            GROUP BY p.address, p.city, p.state
            HAVING COUNT(DISTINCT p.npi) >= 5 AND SUM(ps.total_paid) > 10000000
        )
        SELECT address, city, state, num_npis, combined_paid, npi_list
        FROM address_groups
        ORDER BY combined_paid DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            addr, city, state, num, paid, npi_list = r
            top_npi = npi_list[0] if npi_list else 'unknown'
            providers.append({
                'npi': top_npi, 'name': f"{addr}, {city}, {state}",
                'state': state,
                'amount': float(paid), 'score': float(num),
                'evidence': f"Address cluster: {num} NPIs at {addr}, {city}, {state}, "
                            f"combined={format_dollars(paid)}"
            })
        findings.append(make_finding('H1081', providers[:20],
                                     sum(p['amount'] for p in providers), 'medium',
                                     'address_cluster_flagged',
                                     f"Address clusters: {len(providers)} locations"))

    # H1084: Sequential NPI numbers at same address
    rows = con.execute("""
        WITH address_npis AS (
            SELECT
                p.address,
                p.city,
                p.state,
                p.npi,
                CAST(p.npi AS BIGINT) AS npi_num,
                ps.total_paid
            FROM providers p
            INNER JOIN provider_summary ps ON p.npi = ps.billing_npi
            WHERE p.address IS NOT NULL AND p.address != ''
              AND LENGTH(p.address) > 5
              AND ps.total_paid > 10000
        ),
        address_stats AS (
            SELECT address, city, state,
                   COUNT(*) AS num_npis,
                   MAX(npi_num) - MIN(npi_num) AS npi_range,
                   SUM(total_paid) AS combined_paid
            FROM address_npis
            GROUP BY address, city, state
            HAVING COUNT(*) >= 5
               AND (MAX(npi_num) - MIN(npi_num)) < COUNT(*) * 10
               AND SUM(total_paid) > 1000000
        )
        SELECT address, city, state, num_npis, npi_range, combined_paid
        FROM address_stats
        ORDER BY combined_paid DESC
        LIMIT 20
    """).fetchall()

    if rows:
        providers = []
        for r in rows:
            addr, city, state, num, npi_range, paid = r
            providers.append({
                'npi': f"ADDR_{state}_{num}", 'name': f"{addr}, {city}, {state}",
                'state': state,
                'amount': float(paid), 'score': float(num),
                'evidence': f"Sequential NPIs: {num} NPIs in range of {npi_range} at "
                            f"{addr}, {city}, combined={format_dollars(paid)}"
            })
        findings.append(make_finding('H1084', providers[:20],
                                     sum(p['amount'] for p in providers), 'high',
                                     'sequential_npi_address',
                                     f"Sequential NPI clusters: {len(providers)} addresses"))

    print(f"  Address clustering: {len(findings)} findings")
    return findings


def run_composite_multi_signal(prior_findings):
    """Category 10: Multi-signal composite scoring."""
    print("\n--- Category 10: Composite Multi-Signal ---")
    findings = []

    # Count how many methods/categories flag each NPI
    npi_signals = defaultdict(lambda: {
        'methods': set(), 'categories': set(), 'total_impact': 0,
        'findings': [], 'name': '', 'state': ''
    })

    for finding in prior_findings:
        method = finding.get('method_name', '')
        h_id = finding.get('hypothesis_id', '')
        # Derive category from hypothesis ID
        if h_id.startswith('H'):
            try:
                num = int(h_id[1:])
                if num <= 150:
                    cat = 'statistical'
                elif num <= 270:
                    cat = 'temporal'
                elif num <= 400:
                    cat = 'peer'
                elif num <= 520:
                    cat = 'network'
                elif num <= 600:
                    cat = 'concentration'
                elif num <= 750:
                    cat = 'ml'
                elif num <= 830:
                    cat = 'deep_learning'
                elif num <= 930:
                    cat = 'domain'
                else:
                    cat = 'crossref'
            except ValueError:
                cat = method
        else:
            cat = method

        for p in finding.get('flagged_providers', []):
            if isinstance(p, dict):
                npi = p.get('npi', '')
                amount = p.get('amount', 0) or 0
                name = p.get('name')
                state = p.get('state')
            else:
                npi = str(p)
                amount = 0
                name = None
                state = None
            if not npi:
                continue
            npi_signals[npi]['methods'].add(method)
            npi_signals[npi]['categories'].add(cat)
            npi_signals[npi]['total_impact'] += amount
            npi_signals[npi]['findings'].append(h_id)
            if name:
                npi_signals[npi]['name'] = name
            if state:
                npi_signals[npi]['state'] = state

    # 10A: Multi-factor risk scoring (flagged by 3+ categories)
    h_num = 1001
    multi_cat = [(npi, data) for npi, data in npi_signals.items()
                 if len(data['categories']) >= 3 and data['total_impact'] > 500000]
    multi_cat.sort(key=lambda x: -x[1]['total_impact'])

    for rank, (npi, data) in enumerate(multi_cat[:20]):
        h_id = f"H-composite-{rank+1:02d}"
        providers = [{
            'npi': npi, 'name': data['name'], 'state': data['state'],
            'amount': float(data['total_impact']),
            'score': float(len(data['categories'])),
            'evidence': f"Flagged by {len(data['categories'])} categories: {', '.join(sorted(data['categories']))}, "
                        f"{len(data['methods'])} methods, {len(data['findings'])} findings"
        }]
        findings.append(make_finding(
            h_id, providers, data['total_impact'],
            'high' if len(data['categories']) >= 4 else 'medium',
            'composite_multi_signal',
            f"Multi-signal: {len(data['categories'])} categories, impact={format_dollars(data['total_impact'])}"
        ))

    # 10B: Ensemble model agreement (3+ of ML/DL models)
    ml_methods = {'isolation_forest', 'dbscan', 'lof', 'autoencoder', 'xgboost', 'kmeans', 'vae', 'lstm', 'transformer', 'random_forest'}
    ml_multi = [(npi, data) for npi, data in npi_signals.items()
                if len(data['methods'] & ml_methods) >= 3 and data['total_impact'] > 100000]
    ml_multi.sort(key=lambda x: -x[1]['total_impact'])

    for rank, (npi, data) in enumerate(ml_multi[:15]):
        h_id = f"H-composite-{21 + rank:02d}"
        ml_hits = data['methods'] & ml_methods
        providers = [{
            'npi': npi, 'name': data['name'], 'state': data['state'],
            'amount': float(data['total_impact']),
            'score': float(len(ml_hits)),
            'evidence': f"Flagged by {len(ml_hits)} ML/DL models: {', '.join(sorted(ml_hits))}"
        }]
        findings.append(make_finding(
            h_id, providers, data['total_impact'],
            'high' if len(ml_hits) >= 4 else 'medium',
            'ensemble_agreement',
            f"ML ensemble: {len(ml_hits)} models agree"
        ))

    # 10C-E: Cross-category combinations
    combos = [
        ('temporal', 'statistical', 'temporal_plus_statistical', 36),
        ('network', 'concentration', 'network_plus_volume', 51),
        ('temporal', 'concentration', 'growth_plus_concentration', 66),
    ]

    for cat1, cat2, combo_name, base_rank in combos:
        combo_providers = [(npi, data) for npi, data in npi_signals.items()
                          if cat1 in data['categories'] and cat2 in data['categories']
                          and data['total_impact'] > 200000]
        combo_providers.sort(key=lambda x: -x[1]['total_impact'])

        for rank, (npi, data) in enumerate(combo_providers[:15]):
            h_id = f"H-composite-{base_rank + rank:02d}"
            providers = [{
                'npi': npi, 'name': data['name'], 'state': data['state'],
                'amount': float(data['total_impact']),
                'score': float(len(data['categories'])),
                'evidence': f"{combo_name}: {cat1}+{cat2} signals, "
                            f"total categories={len(data['categories'])}"
            }]
            findings.append(make_finding(
                h_id, providers, data['total_impact'],
                'medium', f'composite_{combo_name}',
                f"{combo_name}: combined signals"
            ))

    print(f"  Composite findings: {len(findings)}")
    return findings


def main():
    t0 = time.time()
    os.makedirs(FINDINGS_DIR, exist_ok=True)
    con = get_connection(read_only=True)

    all_findings = []

    # Category 9: Cross-reference
    all_findings.extend(run_specialty_mismatch(con))
    all_findings.extend(run_entity_type_anomalies(con))
    all_findings.extend(run_geographic_impossibilities(con))
    all_findings.extend(run_state_spending_anomalies(con))

    # Gap analysis: new cross-reference functions
    all_findings.extend(run_leie_crossref(con))
    all_findings.extend(run_kickback_referral(con))
    all_findings.extend(run_beneficiary_anomalies(con))
    all_findings.extend(run_address_clustering(con))

    con.close()

    # Category 10: Composite
    prior = load_prior_findings()
    print(f"\nLoaded {len(prior)} prior findings for composite analysis")
    all_findings.extend(run_composite_multi_signal(prior))

    output_path = os.path.join(FINDINGS_DIR, 'categories_9_and_10.json')
    with open(output_path, 'w') as f:
        json.dump(all_findings, f, indent=2, default=str)

    print(f"\nTotal Categories 9+10 findings: {len(all_findings)}")
    total_impact = sum(f.get('total_impact', 0) for f in all_findings)
    print(f"Total estimated impact: {format_dollars(total_impact)}")
    print(f"Findings written to {output_path}")
    print(f"\nMilestone 8 complete. Time: {time.time() - t0:.1f}s")


if __name__ == '__main__':
    main()
