"""Pre-aggregated summary table creation for provider, HCPCS, and network data."""

import logging

logger = logging.getLogger('medicaid_fwa.ingestion')


def build_provider_summary(con):
    """Create provider_summary table aggregated by billing NPI."""
    logger.info('Building provider_summary ...')
    con.execute("DROP TABLE IF EXISTS provider_summary")
    con.execute("""
        CREATE TABLE provider_summary AS
        SELECT
            billing_npi,
            COUNT(DISTINCT hcpcs_code)  AS num_codes,
            COUNT(DISTINCT claim_month) AS num_months,
            SUM(beneficiaries)          AS total_beneficiaries,
            SUM(claims)                 AS total_claims,
            SUM(paid)                   AS total_paid,
            SUM(paid) / NULLIF(SUM(claims), 0)         AS avg_paid_per_claim,
            SUM(claims) / NULLIF(SUM(beneficiaries), 0) AS avg_claims_per_bene,
            MIN(claim_month)            AS first_month,
            MAX(claim_month)            AS last_month
        FROM claims
        GROUP BY billing_npi
    """)
    count = con.execute("SELECT COUNT(*) FROM provider_summary").fetchone()[0]
    logger.info(f'  provider_summary: {count:,} providers')
    return count


def build_hcpcs_summary(con):
    """Create hcpcs_summary table aggregated by HCPCS code."""
    logger.info('Building hcpcs_summary ...')
    con.execute("DROP TABLE IF EXISTS hcpcs_summary")
    con.execute("""
        CREATE TABLE hcpcs_summary AS
        SELECT
            hcpcs_code,
            COUNT(DISTINCT billing_npi)  AS num_providers,
            SUM(beneficiaries)           AS total_beneficiaries,
            SUM(claims)                  AS total_claims,
            SUM(paid)                    AS total_paid,
            SUM(paid) / NULLIF(SUM(claims), 0)              AS avg_paid_per_claim,
            STDDEV(paid / NULLIF(claims, 0))                 AS std_paid_per_claim,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY paid / NULLIF(claims, 0))  AS median_paid_per_claim,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY paid / NULLIF(claims, 0)) AS p95_paid_per_claim
        FROM claims
        WHERE claims > 0
        GROUP BY hcpcs_code
    """)
    count = con.execute("SELECT COUNT(*) FROM hcpcs_summary").fetchone()[0]
    logger.info(f'  hcpcs_summary: {count:,} codes')
    return count


def build_provider_monthly(con):
    """Create provider_monthly table."""
    logger.info('Building provider_monthly ...')
    con.execute("DROP TABLE IF EXISTS provider_monthly")
    con.execute("""
        CREATE TABLE provider_monthly AS
        SELECT
            billing_npi, claim_month,
            SUM(beneficiaries) AS beneficiaries, SUM(claims) AS claims,
            SUM(paid) AS paid, COUNT(DISTINCT hcpcs_code) AS num_codes
        FROM claims
        GROUP BY billing_npi, claim_month
    """)
    count = con.execute("SELECT COUNT(*) FROM provider_monthly").fetchone()[0]
    logger.info(f'  provider_monthly: {count:,} rows')
    return count


def build_provider_hcpcs(con):
    """Create provider_hcpcs table."""
    logger.info('Building provider_hcpcs ...')
    con.execute("DROP TABLE IF EXISTS provider_hcpcs")
    con.execute("""
        CREATE TABLE provider_hcpcs AS
        SELECT
            billing_npi, hcpcs_code,
            SUM(beneficiaries) AS beneficiaries, SUM(claims) AS claims,
            SUM(paid) AS paid,
            SUM(paid) / NULLIF(SUM(claims), 0) AS paid_per_claim,
            SUM(claims) / NULLIF(SUM(beneficiaries), 0) AS claims_per_bene,
            COUNT(DISTINCT claim_month) AS months_active
        FROM claims WHERE claims > 0
        GROUP BY billing_npi, hcpcs_code
    """)
    count = con.execute("SELECT COUNT(*) FROM provider_hcpcs").fetchone()[0]
    logger.info(f'  provider_hcpcs: {count:,} rows')
    return count


def build_network(con):
    """Create billing_servicing_network table."""
    logger.info('Building billing_servicing_network ...')
    con.execute("DROP TABLE IF EXISTS billing_servicing_network")
    con.execute("""
        CREATE TABLE billing_servicing_network AS
        SELECT
            billing_npi, servicing_npi,
            COUNT(DISTINCT hcpcs_code) AS shared_codes,
            COUNT(DISTINCT claim_month) AS shared_months,
            SUM(paid) AS total_paid, SUM(claims) AS total_claims
        FROM claims
        WHERE servicing_npi IS NOT NULL AND servicing_npi != ''
        GROUP BY billing_npi, servicing_npi
    """)
    count = con.execute("SELECT COUNT(*) FROM billing_servicing_network").fetchone()[0]
    logger.info(f'  billing_servicing_network: {count:,} edges')
    return count


def build_all_summaries(con):
    """Build all 5 pre-aggregated summary tables.

    Returns:
        dict of table_name -> row_count.
    """
    return {
        'provider_summary': build_provider_summary(con),
        'hcpcs_summary': build_hcpcs_summary(con),
        'provider_monthly': build_provider_monthly(con),
        'provider_hcpcs': build_provider_hcpcs(con),
        'billing_servicing_network': build_network(con),
    }
