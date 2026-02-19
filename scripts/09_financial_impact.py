#!/usr/bin/env python3
"""Milestone 9: Financial impact estimation and deduplication.

Merges all findings, deduplicates by NPI+HCPCS, calculates financial impact,
assigns confidence tiers, and produces the final scored findings file.
"""

import csv
import json
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.db_utils import get_connection, format_dollars

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINDINGS_DIR = os.path.join(PROJECT_ROOT, 'output', 'findings')
DQ_ATLAS_DIR = os.path.join(PROJECT_ROOT, 'reference_data', 'dq_atlas')
CALIBRATION_PATH = os.path.join(PROJECT_ROOT, 'output', 'analysis', 'method_calibration.csv')
PRUNED_METHODS_PATH = os.path.join(PROJECT_ROOT, 'output', 'analysis', 'pruned_methods.csv')
PRUNE_MIN_FLAGGED = 50
PRUNE_HOLDOUT_RATE_MULT = 0.5
PRUNE_Z_DELTA = -0.5


def load_all_findings():
    """Load findings from all milestone outputs."""
    all_findings = []
    files = [
        'categories_1_to_5.json',
        'categories_6_and_7.json',
        'category_8.json',
        'categories_9_and_10.json',
    ]
    for fname in files:
        path = os.path.join(FINDINGS_DIR, fname)
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            print(f"  Loaded {len(data)} findings from {fname}")
            all_findings.extend(data)
        else:
            print(f"  WARNING: {path} not found")
    return all_findings


def load_state_quality_weights():
    """Load state quality weights from a DQ Atlas export if present.

    Expected CSV with a state column (e.g., state/state_code) and a numeric
    weight/score column. Scores are normalized to [0.5, 1.0] if needed.
    """
    if not os.path.isdir(DQ_ATLAS_DIR):
        return {}

    candidates = [
        os.path.join(DQ_ATLAS_DIR, 'state_quality_weights.csv'),
        os.path.join(DQ_ATLAS_DIR, 'dq_atlas_state_quality.csv'),
        os.path.join(DQ_ATLAS_DIR, 'dq_atlas.csv'),
    ]
    csv_path = next((p for p in candidates if os.path.exists(p)), None)
    if not csv_path:
        return {}

    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return {}
        state_col = None
        score_col = None
        for col in reader.fieldnames:
            lower = col.lower()
            if state_col is None and lower in {'state', 'state_code', 'state_abbrev', 'state_abbr'}:
                state_col = col
            if score_col is None and any(k in lower for k in ('weight', 'score', 'quality', 'completeness', 'overall')):
                score_col = col
        if not state_col or not score_col:
            return {}

        scores = []
        rows = []
        for row in reader:
            state = (row.get(state_col, '') or '').strip().upper()
            if not state:
                continue
            raw = (row.get(score_col, '') or '').strip()
            try:
                score = float(raw)
            except ValueError:
                continue
            scores.append(score)
            rows.append((state, score))

    if not rows:
        return {}

    min_score = min(scores)
    max_score = max(scores)
    weights = {}
    # If already in 0-1 range, use as-is (clamped to [0.5, 1.0])
    if 0 <= min_score and max_score <= 1.5:
        for state, score in rows:
            weights[state] = min(max(score, 0.5), 1.0)
    else:
        # Normalize to [0.5, 1.0]
        span = max_score - min_score if max_score != min_score else 1.0
        for state, score in rows:
            norm = (score - min_score) / span
            weights[state] = 0.5 + 0.5 * norm

    print(f"Loaded state quality weights for {len(weights)} states from {csv_path}")
    return weights


def load_pruned_methods():
    """Identify unstable methods from calibration output."""
    if not os.path.exists(CALIBRATION_PATH):
        return set()

    pruned = []
    baseline = None
    with open(CALIBRATION_PATH, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            method = (row.get('method_name') or '').strip()
            if not method:
                continue
            try:
                flagged = int(float(row.get('flagged_npis') or 0))
            except ValueError:
                flagged = 0
            try:
                holdout_rate = float(row.get('holdout_rate') or 0)
            except ValueError:
                holdout_rate = 0
            try:
                base = float(row.get('baseline_holdout_rate') or 0)
            except ValueError:
                base = 0
            try:
                z_delta = float(row.get('holdout_z_delta') or 0)
            except ValueError:
                z_delta = 0

            if baseline is None and base:
                baseline = base
            if flagged < PRUNE_MIN_FLAGGED:
                continue

            reasons = []
            if base > 0 and holdout_rate < base * PRUNE_HOLDOUT_RATE_MULT:
                reasons.append('low_holdout_rate')
            if z_delta < PRUNE_Z_DELTA:
                reasons.append('negative_z_delta')

            if reasons:
                pruned.append({
                    'method_name': method,
                    'flagged_npis': flagged,
                    'holdout_rate': holdout_rate,
                    'baseline_holdout_rate': base,
                    'holdout_z_delta': z_delta,
                    'reasons': ';'.join(reasons),
                })

    if pruned:
        with open(PRUNED_METHODS_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    'method_name',
                    'flagged_npis',
                    'holdout_rate',
                    'baseline_holdout_rate',
                    'holdout_z_delta',
                    'reasons',
                ],
            )
            writer.writeheader()
            writer.writerows(pruned)
        print(f"Pruned {len(pruned)} methods using calibration at {PRUNED_METHODS_PATH}")
    return {p['method_name'] for p in pruned}


def filter_findings_by_methods(findings, excluded_methods):
    if not excluded_methods:
        return findings, 0
    kept = []
    removed = 0
    for f in findings:
        method = f.get('method_name', '')
        if method in excluded_methods:
            removed += 1
            continue
        kept.append(f)
    return kept, removed


def collapse_ghost_network_metadata(findings):
    """Collapse ghost-network hypothesis IDs into a single composite marker."""
    for f in findings:
        methods = f.get('methods') or []
        if 'ghost_network' not in methods:
            continue
        hyp_ids = f.get('hypothesis_ids') or []
        non_ghost = [h for h in hyp_ids if not h.startswith('H05')]
        # Keep a single composite placeholder
        f['hypothesis_ids'] = non_ghost + ['H-GHOST-COMPOSITE']
        f['ghost_network_collapsed'] = True
    return findings


def apply_state_quality_weights(findings, weights):
    """Apply state-level quality weights to impact and score."""
    if not weights:
        return findings, False
    for f in findings:
        state = (f.get('state') or '').strip().upper()
        weight = weights.get(state, 1.0)
        f['state_quality_weight'] = weight
        f['weighted_impact'] = f.get('total_impact', 0) * weight
        f['weighted_score'] = f.get('score', 0) * weight
    return findings, True


def deduplicate_findings(findings):
    """Deduplicate by NPI, keeping highest-confidence finding per provider."""
    confidence_rank = {'high': 3, 'medium': 2, 'low': 1}

    # Group by NPI
    npi_findings = defaultdict(list)
    for finding in findings:
        for provider in finding.get('flagged_providers', []):
            if isinstance(provider, dict):
                npi = provider.get('npi', '')
                amount = provider.get('amount', 0)
                score = provider.get('score', 0)
                evidence = provider.get('evidence', '')
                name = provider.get('name', '')
                state = provider.get('state', '')
            else:
                npi = str(provider)
                amount = 0
                score = 0
                evidence = ''
                name = ''
                state = ''
            if not npi:
                continue
            npi_findings[npi].append({
                'finding': finding,
                'provider': {
                    'npi': npi,
                    'amount': amount,
                    'score': score,
                    'evidence': evidence,
                    'name': name,
                    'state': state,
                },
                'confidence': finding.get('confidence', 'low'),
                'method': finding.get('method_name', ''),
                'hypothesis_id': finding.get('hypothesis_id', ''),
                'amount': amount,
            })

    # For each NPI, keep track of all methods and use highest-impact finding
    deduped = []
    for npi, entries in npi_findings.items():
        # Collect all methods and hypothesis IDs
        methods = list(set(e['method'] for e in entries))
        hypothesis_ids = list(set(e['hypothesis_id'] for e in entries))

        # Sort by confidence rank then amount
        entries.sort(key=lambda e: (confidence_rank.get(e['confidence'], 0), e['amount']), reverse=True)
        best = entries[0]

        # Determine final confidence
        num_methods = len(methods)
        max_conf = max(confidence_rank.get(e['confidence'], 0) for e in entries)
        if num_methods >= 3 or max_conf == 3:
            final_confidence = 'high'
        elif num_methods >= 2 or max_conf == 2:
            final_confidence = 'medium'
        else:
            final_confidence = 'low'

        # Calculate total impact (max of all findings for this NPI to avoid double-counting)
        max_amount = max(e['amount'] for e in entries)

        provider_info = best['provider'].copy()
        provider_info['amount'] = max_amount
        provider_info['num_methods'] = num_methods
        provider_info['methods'] = methods
        provider_info['hypothesis_ids'] = hypothesis_ids

        deduped.append({
            'npi': npi,
            'name': provider_info.get('name', ''),
            'state': provider_info.get('state', ''),
            'total_impact': max_amount,
            'confidence': final_confidence,
            'num_methods': num_methods,
            'methods': methods,
            'hypothesis_ids': hypothesis_ids,
            'evidence': provider_info.get('evidence', best['finding'].get('evidence', '')),
            'primary_method': best['method'],
            'score': provider_info.get('score', 0),
        })

    # Sort by total_impact descending
    deduped.sort(key=lambda x: -x['total_impact'])
    return deduped


def enrich_with_provider_details(findings, con):
    """Add provider details from DuckDB for each finding."""
    try:
        provider_count = con.execute("SELECT COUNT(*) FROM providers").fetchone()[0]
    except Exception:
        provider_count = 0
    if provider_count == 0:
        return findings

    npis = [f.get('npi') for f in findings if f.get('npi') and not f.get('npi', '').startswith('STATE_')]
    if not npis:
        return findings

    details = {}
    chunk_size = 10000
    for i in range(0, len(npis), chunk_size):
        chunk = npis[i:i + chunk_size]
        rows = con.execute("""
            SELECT
                ps.billing_npi,
                COALESCE(p.name, 'NPI ' || ps.billing_npi) AS name,
                COALESCE(p.state, '') AS state,
                COALESCE(p.city, '') AS city,
                COALESCE(p.specialty, '') AS specialty,
                COALESCE(p.entity_type, '') AS entity_type,
                ps.total_paid,
                ps.total_claims,
                ps.total_beneficiaries,
                ps.num_codes,
                ps.num_months,
                ps.first_month,
                ps.last_month,
                ps.avg_paid_per_claim
            FROM provider_summary ps
            LEFT JOIN providers p ON ps.billing_npi = p.npi
            WHERE ps.billing_npi IN (SELECT UNNEST(?::VARCHAR[]))
        """, [chunk]).fetchall()

        for row in rows:
            details[row[0]] = row[1:]

    for finding in findings:
        npi = finding.get('npi', '')
        if not npi or npi.startswith('STATE_'):
            continue

        row = details.get(npi)
        if row:
            finding['name'] = row[0]
            finding['state'] = row[1]
            finding['city'] = row[2]
            finding['specialty'] = row[3]
            finding['entity_type'] = 'Organization' if row[4] == '2' else 'Individual'
            finding['total_paid'] = row[5]
            finding['total_claims'] = row[6]
            finding['total_beneficiaries'] = row[7]
            finding['num_codes'] = row[8]
            finding['num_months'] = row[9]
            finding['first_month'] = row[10]
            finding['last_month'] = row[11]
            finding['avg_paid_per_claim'] = row[12]

    return findings


def load_peer_medians(con):
    """Load peer median paid-per-claim benchmarks for standard impact."""
    overall = con.execute("""
        SELECT QUANTILE_CONT(avg_paid_per_claim, 0.5)
        FROM provider_summary
        WHERE avg_paid_per_claim IS NOT NULL
          AND total_claims > 0
    """).fetchone()[0] or 0

    state_specialty = {}
    for state, specialty, median_ppc in con.execute("""
        SELECT p.state, p.specialty, QUANTILE_CONT(ps.avg_paid_per_claim, 0.5) AS median_ppc
        FROM provider_summary ps
        LEFT JOIN providers p ON ps.billing_npi = p.npi
        WHERE ps.avg_paid_per_claim IS NOT NULL
          AND ps.total_claims > 0
          AND p.state IS NOT NULL AND p.state != ''
          AND p.specialty IS NOT NULL AND p.specialty != ''
        GROUP BY p.state, p.specialty
        HAVING COUNT(*) >= 20
    """).fetchall():
        state_specialty[(state, specialty)] = median_ppc

    by_state = {}
    for state, median_ppc in con.execute("""
        SELECT p.state, QUANTILE_CONT(ps.avg_paid_per_claim, 0.5) AS median_ppc
        FROM provider_summary ps
        LEFT JOIN providers p ON ps.billing_npi = p.npi
        WHERE ps.avg_paid_per_claim IS NOT NULL
          AND ps.total_claims > 0
          AND p.state IS NOT NULL AND p.state != ''
        GROUP BY p.state
        HAVING COUNT(*) >= 50
    """).fetchall():
        by_state[state] = median_ppc

    by_specialty = {}
    for specialty, median_ppc in con.execute("""
        SELECT p.specialty, QUANTILE_CONT(ps.avg_paid_per_claim, 0.5) AS median_ppc
        FROM provider_summary ps
        LEFT JOIN providers p ON ps.billing_npi = p.npi
        WHERE ps.avg_paid_per_claim IS NOT NULL
          AND ps.total_claims > 0
          AND p.specialty IS NOT NULL AND p.specialty != ''
        GROUP BY p.specialty
        HAVING COUNT(*) >= 50
    """).fetchall():
        by_specialty[specialty] = median_ppc

    return {
        "overall": overall,
        "state_specialty": state_specialty,
        "state": by_state,
        "specialty": by_specialty,
    }


def apply_standardized_impact(findings, con):
    """Standardize impact: excess above peer median PPC, capped at total_paid."""
    medians = load_peer_medians(con)
    for finding in findings:
        npi = finding.get('npi', '')
        raw_impact = finding.get('total_impact', 0) or 0
        finding['raw_impact'] = raw_impact

        # Systemic identifiers are not provider-level; exclude from standardized totals
        if npi.startswith('STATE_') or npi.startswith('PAIR_') or not (len(npi) == 10 and npi.isdigit()):
            finding['systemic_impact_raw'] = raw_impact
            finding['total_impact'] = 0
            finding['impact_standardized'] = False
            finding['impact_reason'] = 'systemic_entry'
            continue

        avg_ppc = finding.get('avg_paid_per_claim')
        total_claims = finding.get('total_claims')
        if not avg_ppc or not total_claims:
            finding['impact_standardized'] = False
            finding['impact_reason'] = 'missing_ppc_or_claims'
            finding['total_impact'] = 0
            continue

        state = finding.get('state', '')
        specialty = finding.get('specialty', '')
        median = (
            medians["state_specialty"].get((state, specialty))
            or medians["state"].get(state)
            or medians["specialty"].get(specialty)
            or medians["overall"]
            or 0
        )
        if median <= 0:
            finding['impact_standardized'] = False
            finding['impact_reason'] = 'missing_peer_median'
            finding['total_impact'] = 0
            continue

        uncapped = max(0, (avg_ppc - median) * total_claims)
        total_paid = finding.get('total_paid')
        capped = min(uncapped, total_paid) if total_paid is not None and total_paid > 0 else uncapped

        finding['peer_median_ppc'] = median
        finding['uncapped_impact'] = uncapped
        finding['total_impact'] = capped
        finding['impact_capped'] = capped < uncapped
        finding['impact_standardized'] = True
        finding['impact_formula'] = 'max(0, (avg_ppc - peer_median_ppc) * total_claims), capped at total_paid'

    return findings


def main():
    t0 = time.time()
    os.makedirs(FINDINGS_DIR, exist_ok=True)

    # Load all findings
    print("Loading all findings ...")
    all_findings = load_all_findings()
    print(f"Total raw findings: {len(all_findings)}")

    # Prune unstable methods using calibration output
    pruned_methods = load_pruned_methods()
    if pruned_methods:
        all_findings, removed = filter_findings_by_methods(all_findings, pruned_methods)
        print(f"Removed {removed} findings from {len(pruned_methods)} pruned methods")

    # Count total flagged providers across all findings
    total_providers = sum(len(f.get('flagged_providers', [])) for f in all_findings)
    print(f"Total provider-level flags: {total_providers}")

    # Deduplicate
    print("\nDeduplicating by NPI ...")
    deduped = deduplicate_findings(all_findings)
    print(f"Unique providers after dedup: {len(deduped)}")

    # Enrich with provider details
    print("Enriching with provider details ...")
    con = get_connection(read_only=True)
    deduped = enrich_with_provider_details(deduped, con)

    # Standardize impact methodology before weighting
    print("Standardizing impact using peer median paid-per-claim ...")
    deduped = apply_standardized_impact(deduped, con)
    con.close()

    # Collapse ghost network hypothesis IDs to avoid stacked reporting
    deduped = collapse_ghost_network_metadata(deduped)

    # Apply state quality weights if available
    weights = load_state_quality_weights()
    deduped, used_weights = apply_state_quality_weights(deduped, weights)

    # Sort by weighted impact if available
    if used_weights:
        deduped.sort(key=lambda x: -x.get('weighted_impact', x.get('total_impact', 0)))

    # Compute summary statistics
    high_conf = [f for f in deduped if f['confidence'] == 'high']
    med_conf = [f for f in deduped if f['confidence'] == 'medium']
    low_conf = [f for f in deduped if f['confidence'] == 'low']

    total_impact = sum(f['total_impact'] for f in deduped)
    high_impact = sum(f['total_impact'] for f in high_conf)
    med_impact = sum(f['total_impact'] for f in med_conf)
    low_impact = sum(f['total_impact'] for f in low_conf)
    systemic_total = sum(f.get('systemic_impact_raw', 0) for f in deduped)

    weighted_total = sum(f.get('weighted_impact', f['total_impact']) for f in deduped) if used_weights else None
    weighted_high = sum(f.get('weighted_impact', f['total_impact']) for f in high_conf) if used_weights else None
    weighted_med = sum(f.get('weighted_impact', f['total_impact']) for f in med_conf) if used_weights else None
    weighted_low = sum(f.get('weighted_impact', f['total_impact']) for f in low_conf) if used_weights else None

    print(f"\n{'='*60}")
    print(f"FINANCIAL IMPACT SUMMARY")
    print(f"{'='*60}")
    print(f"Total estimated recoverable: {format_dollars(total_impact)}")
    if used_weights:
        print(f"Quality-weighted recoverable: {format_dollars(weighted_total)}")
    print(f"  High confidence ({len(high_conf)} providers): {format_dollars(high_impact)}")
    print(f"  Medium confidence ({len(med_conf)} providers): {format_dollars(med_impact)}")
    print(f"  Low confidence ({len(low_conf)} providers): {format_dollars(low_impact)}")
    print(f"{'='*60}")

    # Top 10 findings
    print(f"\nTop 10 findings by estimated impact:")
    for i, f in enumerate(deduped[:10]):
        impact_value = f.get('weighted_impact', f['total_impact']) if used_weights else f['total_impact']
        print(f"  {i+1}. {f.get('name', f['npi'])} ({f.get('state', '')}): "
              f"{format_dollars(impact_value)} - {f['confidence']} conf, "
              f"{f['num_methods']} methods")

    # Save final scored findings
    output = {
        'summary': {
            'total_findings': len(deduped),
            'high_confidence': len(high_conf),
            'medium_confidence': len(med_conf),
            'low_confidence': len(low_conf),
            'total_estimated_recoverable': total_impact,
            'high_confidence_impact': high_impact,
            'medium_confidence_impact': med_impact,
            'low_confidence_impact': low_impact,
            'systemic_exposure_total': systemic_total,
            'quality_weighted_total': weighted_total,
            'quality_weighted_high': weighted_high,
            'quality_weighted_medium': weighted_med,
            'quality_weighted_low': weighted_low,
            'quality_weights_applied': used_weights,
            'impact_capped_at_total_paid': True,
            'impact_standardized': True,
            'impact_formula': 'max(0, (avg_ppc - peer_median_ppc) * total_claims), capped at total_paid',
            'peer_median_precedence': 'state+specialty, then state, then specialty, then overall',
            'pruned_methods_count': len(pruned_methods),
            'pruned_methods_path': PRUNED_METHODS_PATH if pruned_methods else '',
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        },
        'findings': deduped,
    }

    output_path = os.path.join(FINDINGS_DIR, 'final_scored_findings.json')
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nFinal scored findings written to {output_path}")
    print(f"\nMilestone 9 complete. Time: {time.time() - t0:.1f}s")


if __name__ == '__main__':
    main()
