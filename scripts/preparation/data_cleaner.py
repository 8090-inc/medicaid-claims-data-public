"""Data cleaning — missing values, duplicates, outlier handling."""

import logging

logger = logging.getLogger('medicaid_fwa.preparation')


def remove_duplicate_claims(con):
    """Identify and remove exact duplicate claim rows.

    Args:
        con: DuckDB connection (write mode).

    Returns:
        Number of duplicates removed.
    """
    logger.info('Checking for duplicate claims ...')
    before = con.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    con.execute("""
        CREATE OR REPLACE TABLE claims AS
        SELECT DISTINCT * FROM claims
    """)
    after = con.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    removed = before - after
    if removed > 0:
        logger.info(f'  Removed {removed:,} duplicate rows')
    else:
        logger.info('  No duplicates found')
    return removed


def handle_missing_values(con):
    """Report on and optionally handle missing values.

    Args:
        con: DuckDB connection (read-only).

    Returns:
        dict of column -> null count.
    """
    logger.info('Checking missing values ...')
    columns = ['billing_npi', 'servicing_npi', 'hcpcs_code',
               'claim_month', 'beneficiaries', 'claims', 'paid']
    null_counts = {}
    for col in columns:
        count = con.execute(
            f"SELECT COUNT(*) FROM claims WHERE {col} IS NULL OR CAST({col} AS VARCHAR) = ''"
        ).fetchone()[0]
        null_counts[col] = count
        if count > 0:
            logger.info(f'  {col}: {count:,} null/empty values')
    return null_counts
