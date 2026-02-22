"""Peer comparison analysis — extracted from PeerAnalyzer."""

import logging

logger = logging.getLogger('medicaid_fwa.analysis')


def compute_peer_benchmarks(con, metric='paid_per_claim', min_peers=20):
    """Compute peer group benchmarks per HCPCS code.

    Args:
        con: DuckDB connection (read-only).
        metric: 'paid_per_claim', 'claims_per_bene', or 'paid_per_bene'.
        min_peers: Minimum providers billing a code for peer comparison.

    Returns:
        dict mapping hcpcs_code -> benchmark dict with median, mean, std, p95.
    """
    if metric == 'paid_per_claim':
        col = 'avg_paid_per_claim'
    elif metric == 'claims_per_bene':
        col = 'total_claims * 1.0 / NULLIF(total_beneficiaries, 0)'
    else:
        col = 'total_paid * 1.0 / NULLIF(total_beneficiaries, 0)'

    rows = con.execute(f"""
        SELECT
            hcpcs_code,
            MEDIAN({col}) AS median_val,
            AVG({col}) AS mean_val,
            STDDEV({col}) AS std_val,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {col}) AS p95_val,
            COUNT(*) AS peer_count
        FROM provider_hcpcs
        GROUP BY hcpcs_code
        HAVING COUNT(*) >= {min_peers}
    """).fetchall()

    benchmarks = {}
    for code, median, mean, std, p95, peers in rows:
        benchmarks[code] = {
            'median': median,
            'mean': mean,
            'std': std or 0,
            'p95': p95,
            'peer_count': peers,
        }

    logger.info(f'Computed {metric} benchmarks for {len(benchmarks)} HCPCS codes')
    return benchmarks


def find_peer_outliers(con, benchmarks, multiplier=2.0, min_claims=50):
    """Find providers exceeding peer benchmarks.

    Args:
        con: DuckDB connection (read-only).
        benchmarks: dict from compute_peer_benchmarks.
        multiplier: Threshold multiplier above median.
        min_claims: Minimum claims for inclusion.

    Returns:
        list of outlier dicts with npi, code, value, median, ratio.
    """
    outliers = []
    for code, bench in benchmarks.items():
        median = bench['median']
        if not median or median <= 0:
            continue

        rows = con.execute("""
            SELECT billing_npi, avg_paid_per_claim, total_claims
            FROM provider_hcpcs
            WHERE hcpcs_code = ? AND total_claims >= ?
                AND avg_paid_per_claim > ? * ?
            ORDER BY avg_paid_per_claim DESC
        """, [code, min_claims, median, multiplier]).fetchall()

        for npi, value, claims in rows:
            outliers.append({
                'npi': npi,
                'hcpcs_code': code,
                'value': value,
                'median': median,
                'ratio': value / median,
                'claims': claims,
            })

    logger.info(f'Found {len(outliers)} peer comparison outliers '
                f'(>{multiplier}x median, >={min_claims} claims)')
    return outliers
