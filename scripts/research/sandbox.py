"""SQL query sandbox for ad-hoc research queries."""

import json
import logging
import os
import time

from config.project_config import ANALYSIS_DIR

logger = logging.getLogger('medicaid_fwa.research')


def execute_research_query(con, sql, description='', save_results=False):
    """Run an ad-hoc SQL query and optionally save results.

    Args:
        con: DuckDB connection (read-only).
        sql: SQL query string.
        description: Human-readable description of the query.
        save_results: If True, write results to JSON.

    Returns:
        dict with 'columns', 'rows', 'row_count', 'elapsed_seconds'.
    """
    t0 = time.time()
    result = con.execute(sql)
    columns = [desc[0] for desc in result.description]
    rows = result.fetchall()
    elapsed = time.time() - t0

    output = {
        'description': description,
        'sql': sql,
        'columns': columns,
        'rows': [list(r) for r in rows],
        'row_count': len(rows),
        'elapsed_seconds': round(elapsed, 3),
    }

    logger.info(f'Research query: {len(rows)} rows in {elapsed:.3f}s — {description}')

    if save_results:
        os.makedirs(ANALYSIS_DIR, exist_ok=True)
        ts = time.strftime('%Y%m%d_%H%M%S')
        path = os.path.join(ANALYSIS_DIR, f'research_{ts}.json')
        with open(path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        logger.info(f'Saved research results to {path}')

    return output


def run_provider_deep_dive(con, npi):
    """Deep-dive analysis for a single provider.

    Args:
        con: DuckDB connection (read-only).
        npi: Provider NPI string.

    Returns:
        dict with summary, monthly_trend, top_codes, network sections.
    """
    summary = con.execute("""
        SELECT total_paid, total_claims, total_beneficiaries, num_codes, num_months
        FROM provider_summary WHERE billing_npi = ?
    """, [npi]).fetchone()

    monthly = con.execute("""
        SELECT claim_month, SUM(paid) AS paid, SUM(claims) AS claims
        FROM claims WHERE billing_npi = ?
        GROUP BY claim_month ORDER BY claim_month
    """, [npi]).fetchall()

    top_codes = con.execute("""
        SELECT hcpcs_code, SUM(paid) AS paid, SUM(claims) AS claims
        FROM claims WHERE billing_npi = ?
        GROUP BY hcpcs_code ORDER BY paid DESC LIMIT 20
    """, [npi]).fetchall()

    network = con.execute("""
        SELECT servicing_npi, total_paid, num_claims
        FROM billing_servicing_network
        WHERE billing_npi = ? AND servicing_npi != ?
        ORDER BY total_paid DESC LIMIT 20
    """, [npi, npi]).fetchall()

    return {
        'npi': npi,
        'summary': {
            'total_paid': summary[0] if summary else 0,
            'total_claims': summary[1] if summary else 0,
            'total_beneficiaries': summary[2] if summary else 0,
            'num_codes': summary[3] if summary else 0,
            'num_months': summary[4] if summary else 0,
        } if summary else {},
        'monthly_trend': [{'month': m, 'paid': p, 'claims': c} for m, p, c in monthly],
        'top_codes': [{'code': c, 'paid': p, 'claims': cl} for c, p, cl in top_codes],
        'network': [{'servicing_npi': s, 'paid': p, 'claims': c} for s, p, c in network],
    }
