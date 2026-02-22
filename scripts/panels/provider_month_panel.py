"""Provider-month panel construction with covariates."""

import logging

logger = logging.getLogger('medicaid_fwa.panels')


def build_provider_month_panel(con):
    """Create provider_month_panel table with covariates.

    Args:
        con: DuckDB connection (write mode).

    Returns:
        Row count of the created panel.
    """
    logger.info('Creating provider_month_panel ...')
    con.execute("DROP TABLE IF EXISTS provider_month_panel")
    con.execute("""
        CREATE TABLE provider_month_panel AS
        WITH base AS (
            SELECT pm.billing_npi, pm.claim_month, pm.paid,
                   pm.claims, pm.beneficiaries, pm.num_codes
            FROM provider_monthly pm
        )
        SELECT
            b.billing_npi, b.claim_month,
            LEFT(b.claim_month, 4) AS year,
            RIGHT(b.claim_month, 2) AS month,
            b.paid, b.claims, b.beneficiaries, b.num_codes,
            b.paid / NULLIF(b.claims, 0) AS paid_per_claim,
            b.claims / NULLIF(b.beneficiaries, 0) AS claims_per_bene,
            b.paid / NULLIF(b.beneficiaries, 0) AS paid_per_bene,
            ps.total_paid AS provider_total_paid,
            ps.num_months AS provider_months,
            ps.num_codes AS provider_num_codes,
            COALESCE(p.state, '') AS state,
            COALESCE(p.specialty, '') AS specialty,
            COALESCE(p.entity_type, '') AS entity_type
        FROM base b
        LEFT JOIN provider_summary ps ON b.billing_npi = ps.billing_npi
        LEFT JOIN providers p ON b.billing_npi = p.npi
    """)
    count = con.execute("SELECT COUNT(*) FROM provider_month_panel").fetchone()[0]
    logger.info(f'  provider_month_panel: {count:,} rows')
    return count


def build_provider_code_month_panel(con):
    """Create provider_code_month_panel table.

    Args:
        con: DuckDB connection (write mode).

    Returns:
        Row count of the created panel.
    """
    logger.info('Creating provider_code_month_panel ...')
    con.execute("DROP TABLE IF EXISTS provider_code_month_panel")
    con.execute("""
        CREATE TABLE provider_code_month_panel AS
        SELECT
            c.billing_npi, c.hcpcs_code, c.claim_month,
            LEFT(c.claim_month, 4) AS year,
            RIGHT(c.claim_month, 2) AS month,
            c.paid, c.claims, c.beneficiaries,
            c.paid / NULLIF(c.claims, 0) AS paid_per_claim,
            c.claims / NULLIF(c.beneficiaries, 0) AS claims_per_bene,
            c.paid / NULLIF(c.beneficiaries, 0) AS paid_per_bene,
            COALESCE(p.state, '') AS state,
            COALESCE(p.specialty, '') AS specialty,
            COALESCE(p.entity_type, '') AS entity_type
        FROM claims c
        LEFT JOIN providers p ON c.billing_npi = p.npi
    """)
    count = con.execute("SELECT COUNT(*) FROM provider_code_month_panel").fetchone()[0]
    logger.info(f'  provider_code_month_panel: {count:,} rows')
    return count
