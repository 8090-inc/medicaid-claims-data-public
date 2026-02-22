"""DuckDB index creation for the claims table."""

import logging

logger = logging.getLogger('medicaid_fwa.ingestion')


def create_indexes(con):
    """Create performance indexes on the claims table.

    Args:
        con: DuckDB connection (write mode).
    """
    logger.info('Creating indexes ...')
    con.execute("CREATE INDEX IF NOT EXISTS idx_claims_billing_npi ON claims(billing_npi)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_claims_hcpcs ON claims(hcpcs_code)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_claims_month ON claims(claim_month)")
    logger.info('  Indexes created.')
