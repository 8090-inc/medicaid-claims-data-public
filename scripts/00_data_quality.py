#!/usr/bin/env python3
"""Milestone 0: CSV data-quality scan.

Streams the raw CSV to surface structural and type issues before ingestion.
Writes a JSON summary plus a CSV of invalid rows (capped).
"""

import argparse
import csv
import json
import os
import re
import time


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(PROJECT_ROOT, 'medicaid-provider-spending.csv')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output', 'qa')

MONTH_RE = re.compile(r'^\d{4}-\d{2}$')


def parse_args():
    p = argparse.ArgumentParser(description='CSV data-quality scan')
    p.add_argument('--max-rows', type=int, default=None,
                   help='Optional cap on number of rows scanned')
    p.add_argument('--max-errors', type=int, default=5000,
                   help='Max invalid rows to write to CSV')
    return p.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(CSV_PATH):
        raise SystemExit(f"CSV not found at {CSV_PATH}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    invalid_path = os.path.join(OUTPUT_DIR, 'invalid_rows.csv')
    report_path = os.path.join(OUTPUT_DIR, 'data_quality_report.json')

    counters = {
        'total_rows': 0,
        'valid_rows': 0,
        'invalid_rows': 0,
        'invalid_column_count': 0,
        'invalid_npi': 0,
        'invalid_servicing_npi': 0,
        'invalid_hcpcs': 0,
        'invalid_month': 0,
        'invalid_beneficiaries': 0,
        'invalid_claims': 0,
        'invalid_paid': 0,
        'negative_paid': 0,
        'zero_beneficiaries_positive_claims': 0,
    }

    month_counts = {}
    month_paid = {}
    min_month = None
    max_month = None

    t0 = time.time()
    with open(CSV_PATH, 'r', newline='') as f, open(invalid_path, 'w', newline='') as out:
        reader = csv.reader(f)
        writer = csv.writer(out)
        writer.writerow(['row_number', 'reason', 'raw_row'])

        header = next(reader, None)
        if header is None:
            raise SystemExit('CSV appears to be empty')

        for idx, row in enumerate(reader, start=2):
            counters['total_rows'] += 1
            if args.max_rows and counters['total_rows'] > args.max_rows:
                break

            reasons = []
            if len(row) != 7:
                counters['invalid_column_count'] += 1
                reasons.append('column_count')
            else:
                billing_npi, servicing_npi, hcpcs, claim_month, beneficiaries, claims, paid = row

                if not billing_npi or not billing_npi.isdigit() or len(billing_npi) != 10:
                    counters['invalid_npi'] += 1
                    reasons.append('billing_npi')

                if servicing_npi:
                    if not servicing_npi.isdigit() or len(servicing_npi) != 10:
                        counters['invalid_servicing_npi'] += 1
                        reasons.append('servicing_npi')

                if not hcpcs:
                    counters['invalid_hcpcs'] += 1
                    reasons.append('hcpcs')

                if not MONTH_RE.match(claim_month):
                    counters['invalid_month'] += 1
                    reasons.append('claim_month')
                else:
                    yr = int(claim_month[:4])
                    mo = int(claim_month[5:7])
                    if mo < 1 or mo > 12:
                        counters['invalid_month'] += 1
                        reasons.append('claim_month')
                    else:
                        if min_month is None or claim_month < min_month:
                            min_month = claim_month
                        if max_month is None or claim_month > max_month:
                            max_month = claim_month

                try:
                    bene_val = int(beneficiaries)
                    if bene_val < 0:
                        raise ValueError('negative')
                except Exception:
                    counters['invalid_beneficiaries'] += 1
                    reasons.append('beneficiaries')
                    bene_val = None

                try:
                    claims_val = int(claims)
                    if claims_val < 0:
                        raise ValueError('negative')
                except Exception:
                    counters['invalid_claims'] += 1
                    reasons.append('claims')
                    claims_val = None

                try:
                    paid_val = float(paid)
                except Exception:
                    counters['invalid_paid'] += 1
                    reasons.append('paid')
                    paid_val = None

                if paid_val is not None and paid_val < 0:
                    counters['negative_paid'] += 1

                if bene_val == 0 and claims_val and claims_val > 0:
                    counters['zero_beneficiaries_positive_claims'] += 1

                if not reasons:
                    counters['valid_rows'] += 1
                    if claim_month:
                        month_counts[claim_month] = month_counts.get(claim_month, 0) + 1
                        if paid_val is not None:
                            month_paid[claim_month] = month_paid.get(claim_month, 0.0) + paid_val

            if reasons:
                counters['invalid_rows'] += 1
                if counters['invalid_rows'] <= args.max_errors:
                    writer.writerow([idx, ';'.join(reasons), '|'.join(row)])

            if counters['total_rows'] % 5_000_000 == 0:
                elapsed = time.time() - t0
                print(f"  Scanned {counters['total_rows']:,} rows in {elapsed/60:.1f} min")

    report = {
        'csv_path': CSV_PATH,
        'total_rows_scanned': counters['total_rows'],
        'valid_rows': counters['valid_rows'],
        'invalid_rows': counters['invalid_rows'],
        'invalid_breakdown': {k: v for k, v in counters.items() if k.startswith('invalid_')},
        'negative_paid_rows': counters['negative_paid'],
        'zero_beneficiaries_positive_claims': counters['zero_beneficiaries_positive_claims'],
        'min_month': min_month,
        'max_month': max_month,
        'month_coverage_count': len(month_counts),
        'month_counts': month_counts,
        'month_paid': month_paid,
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
    }

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    elapsed = time.time() - t0
    print(f"Data-quality report written to {report_path} ({elapsed/60:.1f} min)")


if __name__ == '__main__':
    main()
