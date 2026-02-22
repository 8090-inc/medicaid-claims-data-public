"""Data format transformations and normalization."""

import logging

logger = logging.getLogger('medicaid_fwa.preparation')


def normalize_npi_format(con):
    """Ensure NPI columns are zero-padded 10-digit strings.

    Args:
        con: DuckDB connection (write mode).

    Returns:
        Number of NPIs reformatted.
    """
    logger.info('Normalizing NPI format ...')
    reformatted = con.execute("""
        SELECT COUNT(*) FROM claims WHERE LENGTH(billing_npi) != 10
    """).fetchone()[0]
    if reformatted > 0:
        con.execute("""
            UPDATE claims
            SET billing_npi = LPAD(billing_npi, 10, '0')
            WHERE LENGTH(billing_npi) != 10
        """)
        logger.info(f'  Reformatted {reformatted:,} NPIs')
    return reformatted


def add_derived_columns(con):
    """Add commonly used derived columns to claims table.

    Args:
        con: DuckDB connection (write mode).
    """
    logger.info('Adding derived columns ...')
    # paid_per_claim is computed in aggregations, not stored in raw claims
    # This is a no-op for the current schema but available for future use
    pass
