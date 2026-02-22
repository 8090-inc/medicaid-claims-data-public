"""DuckDB schema creation and health check utilities.

Extracted from 01_setup_and_ingest.py for reuse in testing and validation.
"""

import logging
import os

import duckdb

from config.project_config import DB_PATH, DB_WRITE_THREADS, DB_WRITE_MEMORY_LIMIT

logger = logging.getLogger('medicaid_fwa.database')

# Production schema — 6 tables
SCHEMA_TABLES = {
    'claims': """
        CREATE TABLE IF NOT EXISTS claims (
            billing_npi VARCHAR,
            servicing_npi VARCHAR,
            hcpcs_code VARCHAR,
            claim_month VARCHAR,
            beneficiaries INTEGER,
            claims INTEGER,
            paid DOUBLE
        )
    """,
    'provider_summary': """
        CREATE TABLE IF NOT EXISTS provider_summary (
            billing_npi VARCHAR,
            total_paid DOUBLE,
            total_claims INTEGER,
            total_beneficiaries INTEGER,
            avg_paid_per_claim DOUBLE,
            avg_claims_per_bene DOUBLE,
            num_codes INTEGER,
            num_months INTEGER
        )
    """,
    'hcpcs_summary': """
        CREATE TABLE IF NOT EXISTS hcpcs_summary (
            hcpcs_code VARCHAR,
            avg_paid_per_claim DOUBLE,
            stddev_paid_per_claim DOUBLE,
            median_paid_per_claim DOUBLE,
            p95_paid_per_claim DOUBLE,
            num_providers INTEGER,
            total_paid DOUBLE
        )
    """,
    'provider_hcpcs': """
        CREATE TABLE IF NOT EXISTS provider_hcpcs (
            billing_npi VARCHAR,
            hcpcs_code VARCHAR,
            claims INTEGER,
            paid DOUBLE,
            paid_per_claim DOUBLE,
            beneficiaries INTEGER
        )
    """,
    'provider_monthly': """
        CREATE TABLE IF NOT EXISTS provider_monthly (
            billing_npi VARCHAR,
            claim_month VARCHAR,
            claims INTEGER,
            paid DOUBLE,
            beneficiaries INTEGER
        )
    """,
    'billing_servicing_network': """
        CREATE TABLE IF NOT EXISTS billing_servicing_network (
            billing_npi VARCHAR,
            servicing_npi VARCHAR,
            claims INTEGER,
            paid DOUBLE
        )
    """,
}


def create_schema(con):
    """Create all 6 pipeline tables if they don't exist.

    Args:
        con: DuckDB connection (write mode).
    """
    for table_name, ddl in SCHEMA_TABLES.items():
        con.execute(ddl)
        logger.info(f'Ensured table: {table_name}')


def validate_schema(con):
    """Verify all expected tables exist in the database.

    Args:
        con: DuckDB connection.

    Returns:
        tuple of (ok: bool, missing: list of table names)
    """
    existing = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    expected = set(SCHEMA_TABLES.keys())
    missing = expected - existing
    return len(missing) == 0, list(missing)


def get_table_row_counts(con):
    """Get row counts for all pipeline tables.

    Args:
        con: DuckDB connection.

    Returns:
        dict mapping table_name -> row_count
    """
    counts = {}
    existing = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    for table in SCHEMA_TABLES:
        if table in existing:
            count = con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            counts[table] = count
    return counts


def health_check(db_path=None):
    """Run a health check on the DuckDB database.

    Returns:
        dict with health status.
    """
    path = db_path or DB_PATH
    result = {
        'exists': os.path.exists(path),
        'path': path,
        'size_gb': None,
        'schema_valid': False,
        'table_counts': {},
    }
    if not result['exists']:
        return result

    result['size_gb'] = round(os.path.getsize(path) / (1024 ** 3), 2)
    try:
        con = duckdb.connect(path, read_only=True)
        ok, missing = validate_schema(con)
        result['schema_valid'] = ok
        result['missing_tables'] = missing
        result['table_counts'] = get_table_row_counts(con)
        con.close()
    except Exception as e:
        result['error'] = str(e)
    return result
