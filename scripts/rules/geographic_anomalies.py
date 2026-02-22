"""Geographic anomaly detection — state-level billing pattern outliers."""

import logging

logger = logging.getLogger('medicaid_fwa.rules')


def detect_geographic_outliers(con, z_threshold=3.0):
    """Detect providers whose billing patterns are outliers within their state.

    Args:
        con: DuckDB connection (read-only).
        z_threshold: Z-score threshold for flagging.

    Returns:
        list of finding dicts.
    """
    logger.info(f'Detecting geographic outliers (z > {z_threshold}) ...')
    findings = []

    rows = con.execute(f"""
        WITH state_stats AS (
            SELECT
                p.state,
                AVG(ps.avg_paid_per_claim) AS state_avg_ppc,
                STDDEV(ps.avg_paid_per_claim) AS state_std_ppc,
                COUNT(*) AS providers_in_state
            FROM provider_summary ps
            LEFT JOIN providers p ON ps.billing_npi = p.npi
            WHERE p.state IS NOT NULL AND p.state != ''
            GROUP BY p.state
            HAVING COUNT(*) >= 20 AND STDDEV(ps.avg_paid_per_claim) > 0
        )
        SELECT
            ps.billing_npi, p.state,
            ps.avg_paid_per_claim, ps.total_paid,
            ss.state_avg_ppc, ss.state_std_ppc,
            (ps.avg_paid_per_claim - ss.state_avg_ppc) / ss.state_std_ppc AS z_score
        FROM provider_summary ps
        LEFT JOIN providers p ON ps.billing_npi = p.npi
        JOIN state_stats ss ON p.state = ss.state
        WHERE (ps.avg_paid_per_claim - ss.state_avg_ppc) / ss.state_std_ppc > {z_threshold}
        ORDER BY z_score DESC
        LIMIT 500
    """).fetchall()

    for row in rows:
        findings.append({
            'hypothesis_id': 'H_GEO',
            'flagged_providers': [row[0]],
            'total_impact': row[3],
            'confidence': min(0.5 + row[6] * 0.1, 0.95),
            'method_name': 'geographic_outlier',
            'evidence': f'State {row[1]}: z={row[6]:.2f}, paid/claim ${row[2]:,.0f} vs state avg ${row[4]:,.0f}',
        })

    logger.info(f'  Found {len(findings)} geographic outliers')
    return findings
