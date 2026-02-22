"""Market concentration analysis — extracted from ConcentrationAnalyzer."""

import logging

import numpy as np

logger = logging.getLogger('medicaid_fwa.analysis')


def compute_hhi_by_code(con, min_providers=5, min_total_paid=100000):
    """Compute Herfindahl-Hirschman Index per HCPCS code.

    Args:
        con: DuckDB connection (read-only).
        min_providers: Minimum providers billing a code.
        min_total_paid: Minimum total paid for a code.

    Returns:
        list of dicts with hcpcs_code, hhi, num_providers, total_paid, top_provider_share.
    """
    codes = con.execute(f"""
        SELECT hcpcs_code, SUM(total_paid) AS total, COUNT(*) AS n
        FROM provider_hcpcs
        GROUP BY hcpcs_code
        HAVING COUNT(*) >= {min_providers} AND SUM(total_paid) >= {min_total_paid}
        ORDER BY total DESC
    """).fetchall()

    results = []
    for code, total, n_prov in codes:
        shares = con.execute("""
            SELECT total_paid * 1.0 / ? AS share
            FROM provider_hcpcs
            WHERE hcpcs_code = ?
            ORDER BY total_paid DESC
        """, [total, code]).fetchall()

        share_vals = [s[0] for s in shares]
        hhi = sum(s ** 2 for s in share_vals)
        top_share = share_vals[0] if share_vals else 0

        results.append({
            'hcpcs_code': code,
            'hhi': round(hhi, 6),
            'num_providers': n_prov,
            'total_paid': total,
            'top_provider_share': round(top_share, 4),
            'concentrated': hhi > 0.25,
        })

    concentrated = sum(1 for r in results if r['concentrated'])
    logger.info(f'HHI analysis: {len(results)} codes, {concentrated} concentrated (HHI>0.25)')
    return results


def compute_gini_by_code(con, min_providers=10):
    """Compute Gini coefficient per HCPCS code for billing concentration.

    Args:
        con: DuckDB connection (read-only).
        min_providers: Minimum providers billing a code.

    Returns:
        list of dicts with hcpcs_code, gini, num_providers.
    """
    codes = con.execute(f"""
        SELECT hcpcs_code, COUNT(*) AS n
        FROM provider_hcpcs
        GROUP BY hcpcs_code
        HAVING COUNT(*) >= {min_providers}
    """).fetchall()

    results = []
    for code, n_prov in codes:
        rows = con.execute("""
            SELECT total_paid FROM provider_hcpcs
            WHERE hcpcs_code = ?
            ORDER BY total_paid
        """, [code]).fetchall()

        values = np.array([r[0] for r in rows], dtype=float)
        if len(values) == 0 or np.sum(values) == 0:
            continue

        n = len(values)
        index = np.arange(1, n + 1)
        gini = float((2 * np.sum(index * values) - (n + 1) * np.sum(values)) / (n * np.sum(values)))

        results.append({
            'hcpcs_code': code,
            'gini': round(gini, 4),
            'num_providers': n_prov,
        })

    high_gini = sum(1 for r in results if r['gini'] > 0.8)
    logger.info(f'Gini analysis: {len(results)} codes, {high_gini} highly concentrated (>0.8)')
    return results
