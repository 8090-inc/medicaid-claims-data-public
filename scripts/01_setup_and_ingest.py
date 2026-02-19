#!/usr/bin/env python3
"""Milestone 1: Environment setup and data ingestion into DuckDB.

Reads the 10.32 GB medicaid-provider-spending.csv into DuckDB,
creates indexes and 5 pre-aggregated summary tables, and exports a Parquet file.
"""

import os
import sys
import time
import json

import duckdb

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(PROJECT_ROOT, 'medicaid-provider-spending.csv')
DB_PATH = os.path.join(PROJECT_ROOT, 'medicaid.duckdb')
PARQUET_PATH = os.path.join(PROJECT_ROOT, 'claims.parquet')
QA_DIR = os.path.join(PROJECT_ROOT, 'output', 'qa')
INGEST_REPORT_PATH = os.path.join(QA_DIR, 'ingest_report.json')


def main():
    t0 = time.time()

    if not os.path.exists(CSV_PATH):
        print(f"ERROR: CSV file not found at {CSV_PATH}")
        sys.exit(1)

    print(f"Connecting to DuckDB at {DB_PATH} ...")
    con = duckdb.connect(DB_PATH)
    con.execute("SET threads TO 16")
    con.execute("SET memory_limit = '96GB'")

    # --- Step 1: Ingest CSV into claims table ---
    print("Ingesting CSV into claims table (this may take several minutes) ...")
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
        FROM read_csv_auto('{CSV_PATH}',
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
    null_months = con.execute("SELECT COUNT(*) FROM claims WHERE claim_month IS NULL").fetchone()[0]
    print(f"  Ingested {row_count:,} rows into medicaid.duckdb")
    print(f"  Total paid: ${total_paid:,.0f}")
    print(f"  Negative paid rows: {neg_paid:,}, zero paid rows: {zero_paid:,}")

    # --- Step 2: Create indexes ---
    print("Creating indexes ...")
    con.execute("CREATE INDEX IF NOT EXISTS idx_claims_billing_npi ON claims(billing_npi)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_claims_hcpcs ON claims(hcpcs_code)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_claims_month ON claims(claim_month)")
    print("  Indexes created.")

    # --- Step 3: Create pre-aggregated summary tables ---
    print("Creating provider_summary ...")
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
    ps_count = con.execute("SELECT COUNT(*) FROM provider_summary").fetchone()[0]
    print(f"  provider_summary: {ps_count:,} providers")

    print("Creating hcpcs_summary ...")
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
    hs_count = con.execute("SELECT COUNT(*) FROM hcpcs_summary").fetchone()[0]
    print(f"  hcpcs_summary: {hs_count:,} HCPCS codes")

    print("Creating provider_monthly ...")
    con.execute("DROP TABLE IF EXISTS provider_monthly")
    con.execute("""
        CREATE TABLE provider_monthly AS
        SELECT
            billing_npi,
            claim_month,
            SUM(beneficiaries)          AS beneficiaries,
            SUM(claims)                 AS claims,
            SUM(paid)                   AS paid,
            COUNT(DISTINCT hcpcs_code)  AS num_codes
        FROM claims
        GROUP BY billing_npi, claim_month
    """)
    pm_count = con.execute("SELECT COUNT(*) FROM provider_monthly").fetchone()[0]
    print(f"  provider_monthly: {pm_count:,} rows")

    print("Creating provider_hcpcs ...")
    con.execute("DROP TABLE IF EXISTS provider_hcpcs")
    con.execute("""
        CREATE TABLE provider_hcpcs AS
        SELECT
            billing_npi,
            hcpcs_code,
            SUM(beneficiaries)                              AS beneficiaries,
            SUM(claims)                                     AS claims,
            SUM(paid)                                       AS paid,
            SUM(paid) / NULLIF(SUM(claims), 0)              AS paid_per_claim,
            SUM(claims) / NULLIF(SUM(beneficiaries), 0)     AS claims_per_bene,
            COUNT(DISTINCT claim_month)                     AS months_active
        FROM claims
        WHERE claims > 0
        GROUP BY billing_npi, hcpcs_code
    """)
    ph_count = con.execute("SELECT COUNT(*) FROM provider_hcpcs").fetchone()[0]
    print(f"  provider_hcpcs: {ph_count:,} rows")

    print("Creating billing_servicing_network ...")
    con.execute("DROP TABLE IF EXISTS billing_servicing_network")
    con.execute("""
        CREATE TABLE billing_servicing_network AS
        SELECT
            billing_npi,
            servicing_npi,
            COUNT(DISTINCT hcpcs_code)   AS shared_codes,
            COUNT(DISTINCT claim_month)  AS shared_months,
            SUM(paid)                    AS total_paid,
            SUM(claims)                  AS total_claims
        FROM claims
        WHERE servicing_npi IS NOT NULL AND servicing_npi != ''
        GROUP BY billing_npi, servicing_npi
    """)
    bsn_count = con.execute("SELECT COUNT(*) FROM billing_servicing_network").fetchone()[0]
    print(f"  billing_servicing_network: {bsn_count:,} edges")

    print(f"Created 5 aggregate tables")

    # --- Step 4: Export Parquet ---
    print(f"Exporting Parquet to {PARQUET_PATH} ...")
    con.execute(f"COPY claims TO '{PARQUET_PATH}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    print(f"  Parquet exported.")

    # --- Step 5: Ingest report ---
    os.makedirs(QA_DIR, exist_ok=True)
    ingest_report = {
        'row_count': row_count,
        'total_paid': total_paid,
        'negative_paid_rows': neg_paid,
        'zero_paid_rows': zero_paid,
        'null_claim_month_rows': null_months,
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    with open(INGEST_REPORT_PATH, 'w') as f:
        json.dump(ingest_report, f, indent=2)
    print(f"Ingest report written to {INGEST_REPORT_PATH}")

    # --- Final verification ---
    tables = con.execute("SHOW TABLES").fetchall()
    print(f"\nAll tables: {[t[0] for t in tables]}")
    print(f"Total time: {time.time() - t0:.1f}s")

    con.close()
    print("\nMilestone 1 complete.")


if __name__ == '__main__':
    main()
