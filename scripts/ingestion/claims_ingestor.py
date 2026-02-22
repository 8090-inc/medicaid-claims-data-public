"""CSV to DuckDB ingestion with type casting and validation."""

import logging

logger = logging.getLogger('medicaid_fwa.ingestion')


def ingest_csv(con, csv_path):
    """Load the raw CSV into the claims table.

    Args:
        con: DuckDB connection (write mode).
        csv_path: Path to medicaid-provider-spending.csv.

    Returns:
        dict with row_count, total_paid, negative_paid_rows, zero_paid_rows.
    """
    logger.info(f'Ingesting CSV: {csv_path}')
    con.execute("DROP TABLE IF EXISTS claims")
    con.execute(f"""
        CREATE TABLE claims AS
        SELECT
            BILLING_PROVIDER_NPI_NUM::VARCHAR   AS billing_npi,
            SERVICING_PROVIDER_NPI_NUM::VARCHAR AS servicing_npi,
            HCPCS_CODE::VARCHAR                 AS hcpcs_code,
            CLAIM_FROM_MONTH::VARCHAR           AS claim_month,
            TOTAL_UNIQUE_BENEFICIARIES::INTEGER  AS beneficiaries,
            TOTAL_CLAIMS::INTEGER                AS claims,
            TOTAL_PAID::DOUBLE                   AS paid
        FROM read_csv_auto('{csv_path}',
            header=true,
            sample_size=100000,
            columns={{
                'BILLING_PROVIDER_NPI_NUM': 'VARCHAR',
                'SERVICING_PROVIDER_NPI_NUM': 'VARCHAR',
                'HCPCS_CODE': 'VARCHAR',
                'CLAIM_FROM_MONTH': 'VARCHAR',
                'TOTAL_UNIQUE_BENEFICIARIES': 'INTEGER',
                'TOTAL_CLAIMS': 'INTEGER',
                'TOTAL_PAID': 'DOUBLE'
            }}
        )
    """)

    row_count = con.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    total_paid = con.execute("SELECT SUM(paid) FROM claims").fetchone()[0]
    neg_paid = con.execute("SELECT COUNT(*) FROM claims WHERE paid < 0").fetchone()[0]
    zero_paid = con.execute("SELECT COUNT(*) FROM claims WHERE paid = 0").fetchone()[0]

    logger.info(f'Ingested {row_count:,} rows, total paid: ${total_paid:,.0f}')
    return {
        'row_count': row_count,
        'total_paid': total_paid,
        'negative_paid_rows': neg_paid,
        'zero_paid_rows': zero_paid,
    }
