#!/usr/bin/env python3
"""Milestone 12: Hypothesis feasibility matrix.

Classifies hypotheses based on whether required data fields exist in the
current dataset. Produces a JSON report and a slimmed hypothesis list.
"""

import json
import os


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HYPOTHESES_PATH = os.path.join(PROJECT_ROOT, 'output', 'hypotheses', 'all_hypotheses.json')
OUT_DIR = os.path.join(PROJECT_ROOT, 'output', 'hypotheses')
REPORT_PATH = os.path.join(OUT_DIR, 'feasibility_matrix.json')
TESTABLE_PATH = os.path.join(OUT_DIR, 'all_hypotheses_testable.json')


# Fields available in this dataset
AVAILABLE_FIELDS = {
    'billing_npi', 'servicing_npi', 'hcpcs_code', 'claim_month',
    'beneficiaries', 'claims', 'paid',
}


REQUIRED_FIELDS_BY_METHOD = {
    # Category 1
    'z_score_paid_per_claim': {'paid', 'claims', 'hcpcs_code', 'billing_npi'},
    'z_score_claims_per_bene': {'claims', 'beneficiaries', 'hcpcs_code', 'billing_npi'},
    'z_score_paid_per_bene': {'paid', 'beneficiaries', 'billing_npi'},
    'iqr_outlier': {'paid', 'claims', 'beneficiaries', 'billing_npi'},
    'gev_extreme': {'paid', 'claims', 'beneficiaries', 'billing_npi'},
    'benfords_law': {'paid', 'billing_npi'},
    # Category 2
    'month_over_month_spike': {'paid', 'claim_month', 'billing_npi'},
    'ramp_up': {'paid', 'claim_month', 'billing_npi'},
    'abrupt_stop': {'paid', 'claim_month', 'billing_npi'},
    'yoy_growth': {'paid', 'claim_month', 'billing_npi'},
    'seasonality_anomaly': {'paid', 'claim_month', 'billing_npi'},
    'covid_comparison': {'paid', 'claim_month', 'billing_npi'},
    'december_spike': {'paid', 'claim_month', 'billing_npi'},
    'change_point': {'paid', 'claim_month', 'billing_npi'},
    # Category 3
    'paid_per_claim_vs_median': {'paid', 'claims', 'hcpcs_code', 'billing_npi'},
    'volume_vs_median': {'claims', 'hcpcs_code', 'billing_npi', 'claim_month'},
    'claims_per_bene_vs_median': {'claims', 'beneficiaries', 'hcpcs_code', 'billing_npi'},
    'state_peer_comparison': {'paid', 'claims', 'hcpcs_code', 'billing_npi'},
    'specialty_peer_comparison': {'paid', 'claims', 'hcpcs_code', 'billing_npi'},
    'size_tier_mismatch': {'paid', 'claims', 'beneficiaries', 'billing_npi'},
    # Category 4/5
    'hub_spoke': {'billing_npi', 'servicing_npi', 'paid'},
    'shared_servicing': {'billing_npi', 'servicing_npi', 'paid'},
    'circular_billing': {'billing_npi', 'servicing_npi', 'paid'},
    'network_density': {'billing_npi', 'servicing_npi', 'paid'},
    'new_network': {'billing_npi', 'servicing_npi', 'paid'},
    'pure_billing': {'billing_npi', 'servicing_npi', 'paid'},
    'ghost_network': {'billing_npi', 'servicing_npi', 'paid'},
    'provider_dominance': {'paid', 'billing_npi', 'hcpcs_code'},
    'single_code': {'paid', 'billing_npi', 'hcpcs_code'},
    'hhi_concentration': {'paid', 'billing_npi', 'hcpcs_code'},
    'geographic_monopoly': {'paid', 'billing_npi'},
    'temporal_concentration': {'paid', 'claim_month', 'billing_npi'},
    # Category 6/7/8/9/10 are handled downstream with feature matrices;
    # they remain testable as long as core fields exist.
}


def classify(hypothesis):
    method = hypothesis.get('method') or hypothesis.get('method_name')
    required = REQUIRED_FIELDS_BY_METHOD.get(method, set())
    missing = sorted(required - AVAILABLE_FIELDS)
    status = 'testable' if not missing else 'not_testable'
    return status, missing


def main():
    if not os.path.exists(HYPOTHESES_PATH):
        raise SystemExit(f"Hypotheses not found at {HYPOTHESES_PATH}")

    with open(HYPOTHESES_PATH) as f:
        hypotheses = json.load(f)

    report = {
        'total': len(hypotheses),
        'testable': 0,
        'not_testable': 0,
        'by_method': {},
        'items': [],
    }

    testable = []

    for h in hypotheses:
        status, missing = classify(h)
        method = h.get('method') or h.get('method_name') or 'unknown'
        report['by_method'].setdefault(method, {'testable': 0, 'not_testable': 0})

        if status == 'testable':
            report['testable'] += 1
            report['by_method'][method]['testable'] += 1
            testable.append(h)
        else:
            report['not_testable'] += 1
            report['by_method'][method]['not_testable'] += 1

        report['items'].append({
            'id': h.get('id'),
            'method': method,
            'status': status,
            'missing_fields': missing,
        })

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)

    with open(TESTABLE_PATH, 'w') as f:
        json.dump(testable, f, indent=2)

    print(f"Feasibility matrix written to {REPORT_PATH}")
    print(f"Testable hypotheses written to {TESTABLE_PATH}")


if __name__ == '__main__':
    main()
