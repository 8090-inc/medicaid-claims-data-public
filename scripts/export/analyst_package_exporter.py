"""Analyst-level case file export for investigation teams."""

import csv
import json
import logging
import os

from config.project_config import ANALYSIS_DIR, FINDINGS_DIR, OUTPUT_DIR

logger = logging.getLogger('medicaid_fwa.export')


def export_provider_case_files(scored_findings, con, output_dir=None, top_n=50):
    """Generate per-provider case files for top flagged providers.

    Each case file includes: provider summary, billing history,
    flagged findings, top HCPCS codes, and network connections.

    Args:
        scored_findings: List of scored finding dicts.
        con: DuckDB connection (read-only).
        output_dir: Destination directory.
        top_n: Number of top providers to generate files for.

    Returns:
        list of generated file paths.
    """
    output_dir = output_dir or os.path.join(OUTPUT_DIR, 'packages', 'analyst', 'cases')
    os.makedirs(output_dir, exist_ok=True)

    # Get unique providers sorted by total impact
    provider_impacts = {}
    provider_findings = {}
    for f in scored_findings:
        for npi in f.get('flagged_providers', []):
            provider_impacts[npi] = provider_impacts.get(npi, 0) + f.get('total_impact', 0)
            provider_findings.setdefault(npi, []).append(f)

    top_providers = sorted(provider_impacts.keys(),
                           key=lambda n: provider_impacts[n], reverse=True)[:top_n]

    paths = []
    for npi in top_providers:
        path = _generate_case_file(npi, provider_findings[npi], con, output_dir)
        if path:
            paths.append(path)

    logger.info(f'Generated {len(paths)} provider case files in {output_dir}')
    return paths


def _generate_case_file(npi, findings, con, output_dir):
    """Generate a single provider case file."""
    # Provider summary
    summary = con.execute("""
        SELECT total_paid, total_claims, total_beneficiaries, num_codes, num_months
        FROM provider_summary WHERE billing_npi = ?
    """, [npi]).fetchone()

    # Provider details from NPPES
    details = con.execute("""
        SELECT provider_name, specialty, state, city
        FROM providers WHERE npi = ?
    """, [npi]).fetchone()

    # Top codes
    top_codes = con.execute("""
        SELECT hcpcs_code, total_paid, total_claims
        FROM provider_hcpcs WHERE billing_npi = ?
        ORDER BY total_paid DESC LIMIT 10
    """, [npi]).fetchall()

    case = {
        'npi': npi,
        'provider_name': details[0] if details else 'Unknown',
        'specialty': details[1] if details else 'Unknown',
        'state': details[2] if details else '',
        'city': details[3] if details else '',
        'total_paid': summary[0] if summary else 0,
        'total_claims': summary[1] if summary else 0,
        'total_beneficiaries': summary[2] if summary else 0,
        'num_codes': summary[3] if summary else 0,
        'num_months': summary[4] if summary else 0,
        'findings': [{
            'hypothesis_id': f.get('hypothesis_id'),
            'method': f.get('method_name'),
            'confidence': f.get('confidence'),
            'impact': f.get('total_impact'),
            'evidence': f.get('evidence', ''),
        } for f in findings],
        'top_codes': [{'code': c[0], 'paid': c[1], 'claims': c[2]} for c in top_codes],
    }

    path = os.path.join(output_dir, f'case_{npi}.json')
    with open(path, 'w') as f:
        json.dump(case, f, indent=2, default=str)

    return path


def export_findings_csv(scored_findings, filename='all_findings.csv', output_dir=None):
    """Export all scored findings to a flat CSV for analyst tools.

    Args:
        scored_findings: List of scored finding dicts.
        filename: Output filename.
        output_dir: Output directory.

    Returns:
        Path to exported CSV.
    """
    output_dir = output_dir or os.path.join(OUTPUT_DIR, 'packages', 'analyst')
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)

    if not scored_findings:
        logger.warning('No findings to export')
        return path

    fieldnames = ['hypothesis_id', 'method_name', 'confidence', 'total_impact',
                  'flagged_providers', 'evidence']
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for finding in scored_findings:
            row = dict(finding)
            row['flagged_providers'] = ';'.join(row.get('flagged_providers', []))
            writer.writerow(row)

    logger.info(f'Exported {len(scored_findings)} findings to {path}')
    return path
