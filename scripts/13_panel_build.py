#!/usr/bin/env python3
"""Milestone 13: Longitudinal panel build.

Creates provider-month and provider-code-month panels with covariates.
"""

import os
import time

import duckdb


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, 'medicaid.duckdb')


def main():
    t0 = time.time()
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"DuckDB not found at {DB_PATH}. Run 01_setup_and_ingest.py first.")

    con = duckdb.connect(DB_PATH)
    con.execute("SET threads TO 16")
    con.execute("SET memory_limit = '96GB'")

    print("Creating provider_month_panel ...")
    con.execute("DROP TABLE IF EXISTS provider_month_panel")
    con.execute("""
        CREATE TABLE provider_month_panel AS
        WITH base AS (
            SELECT
                pm.billing_npi,
                pm.claim_month,
                pm.paid,
                pm.claims,
                pm.beneficiaries,
                pm.num_codes
            FROM provider_monthly pm
        )
        SELECT
            b.billing_npi,
            b.claim_month,
            LEFT(b.claim_month, 4) AS year,
            RIGHT(b.claim_month, 2) AS month,
            b.paid,
            b.claims,
            b.beneficiaries,
            b.num_codes,
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

    print("Creating provider_code_month_panel ...")
    con.execute("DROP TABLE IF EXISTS provider_code_month_panel")
    con.execute("""
        CREATE TABLE provider_code_month_panel AS
        SELECT
            c.billing_npi,
            c.hcpcs_code,
            c.claim_month,
            LEFT(c.claim_month, 4) AS year,
            RIGHT(c.claim_month, 2) AS month,
            c.paid,
            c.claims,
            c.beneficiaries,
            c.paid / NULLIF(c.claims, 0) AS paid_per_claim,
            c.claims / NULLIF(c.beneficiaries, 0) AS claims_per_bene,
            c.paid / NULLIF(c.beneficiaries, 0) AS paid_per_bene,
            COALESCE(p.state, '') AS state,
            COALESCE(p.specialty, '') AS specialty,
            COALESCE(p.entity_type, '') AS entity_type
        FROM claims c
        LEFT JOIN providers p ON c.billing_npi = p.npi
    """)

    pm_count = con.execute("SELECT COUNT(*) FROM provider_month_panel").fetchone()[0]
    pcm_count = con.execute("SELECT COUNT(*) FROM provider_code_month_panel").fetchone()[0]
    print(f"  provider_month_panel rows: {pm_count:,}")
    print(f"  provider_code_month_panel rows: {pcm_count:,}")

    con.close()
    print(f"Panel build complete in {time.time() - t0:.1f}s")


if __name__ == '__main__':
    main()
