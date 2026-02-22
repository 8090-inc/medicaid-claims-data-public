"""Sampling utilities for development and testing."""

import logging
import os

logger = logging.getLogger('medicaid_fwa.preparation')


def create_dev_sample(con, sample_fraction=0.01, output_path=None):
    """Create a small sample database for development/testing.

    Args:
        con: DuckDB connection (read-only, source).
        sample_fraction: Fraction of providers to include (default 1%).
        output_path: Path for the sample database.

    Returns:
        dict with sample statistics.
    """
    import duckdb

    output_path = output_path or 'medicaid_sample.duckdb'
    logger.info(f'Creating {sample_fraction*100:.0f}% sample at {output_path}')

    sample_con = duckdb.connect(output_path)

    # Sample providers
    sample_con.execute(f"""
        ATTACH '{con.execute("SELECT current_database()").fetchone()[0]}' AS source (READ_ONLY);
        CREATE TABLE sample_npis AS
        SELECT billing_npi FROM source.provider_summary
        USING SAMPLE {sample_fraction * 100} PERCENT (bernoulli)
    """)

    sample_count = sample_con.execute("SELECT COUNT(*) FROM sample_npis").fetchone()[0]
    logger.info(f'  Sampled {sample_count:,} providers')

    sample_con.close()
    return {'sample_providers': sample_count, 'output_path': output_path}
