#!/usr/bin/env python3
"""Longitudinal, multivariate analysis over provider-month panels.

Outputs summary tables and a narrative report in output/analysis.
"""

import os
import time

import duckdb

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "medicaid.duckdb")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "analysis")


def copy_query(con, query, out_path):
    con.execute(f"COPY ({query}) TO '{out_path}' (HEADER, DELIMITER ',')")


def main():
    t0 = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    con = duckdb.connect(DB_PATH, read_only=True)

    time_range = con.execute("""
        SELECT MIN(claim_month), MAX(claim_month), COUNT(DISTINCT claim_month)
        FROM claims
    """).fetchone()

    totals = con.execute("""
        SELECT SUM(paid), SUM(claims), SUM(beneficiaries)
        FROM claims
    """).fetchone()

    # Monthly totals
    copy_query(
        con,
        """
        SELECT claim_month,
               SUM(paid) AS total_paid,
               SUM(claims) AS total_claims,
               SUM(beneficiaries) AS total_beneficiaries
        FROM claims
        GROUP BY claim_month
        ORDER BY claim_month
        """,
        os.path.join(OUTPUT_DIR, "monthly_totals.csv"),
    )

    # State-month totals
    copy_query(
        con,
        """
        SELECT state, claim_month,
               SUM(paid) AS total_paid,
               SUM(claims) AS total_claims,
               SUM(beneficiaries) AS total_beneficiaries,
               COUNT(DISTINCT billing_npi) AS num_providers
        FROM provider_month_panel
        WHERE state IS NOT NULL AND state != ''
        GROUP BY state, claim_month
        ORDER BY total_paid DESC
        """,
        os.path.join(OUTPUT_DIR, "state_monthly_totals.csv"),
    )

    # Specialty-month totals
    copy_query(
        con,
        """
        SELECT specialty, claim_month,
               SUM(paid) AS total_paid,
               SUM(claims) AS total_claims,
               SUM(beneficiaries) AS total_beneficiaries,
               COUNT(DISTINCT billing_npi) AS num_providers
        FROM provider_month_panel
        WHERE specialty IS NOT NULL AND specialty != ''
        GROUP BY specialty, claim_month
        ORDER BY total_paid DESC
        """,
        os.path.join(OUTPUT_DIR, "specialty_monthly_totals.csv"),
    )

    # Top codes and code-month totals
    copy_query(
        con,
        """
        WITH top_codes AS (
            SELECT hcpcs_code
            FROM hcpcs_summary
            ORDER BY total_paid DESC
            LIMIT 200
        )
        SELECT pcm.hcpcs_code, pcm.claim_month,
               SUM(pcm.paid) AS total_paid,
               SUM(pcm.claims) AS total_claims,
               SUM(pcm.beneficiaries) AS total_beneficiaries
        FROM provider_code_month_panel pcm
        INNER JOIN top_codes tc ON pcm.hcpcs_code = tc.hcpcs_code
        GROUP BY pcm.hcpcs_code, pcm.claim_month
        ORDER BY total_paid DESC
        """,
        os.path.join(OUTPUT_DIR, "code_monthly_totals_top200.csv"),
    )

    # Multivariate residuals: paid-per-claim vs peers (state + specialty + code + month)
    copy_query(
        con,
        """
        WITH top_codes AS (
            SELECT hcpcs_code
            FROM hcpcs_summary
            ORDER BY total_paid DESC
            LIMIT 200
        ),
        base AS (
            SELECT
                billing_npi,
                hcpcs_code,
                claim_month,
                state,
                specialty,
                paid,
                claims,
                paid_per_claim
            FROM provider_code_month_panel
            WHERE claims >= 10
              AND paid > 0
              AND state IS NOT NULL AND state != ''
              AND specialty IS NOT NULL AND specialty != ''
              AND hcpcs_code IN (SELECT hcpcs_code FROM top_codes)
        ),
        peers AS (
            SELECT
                hcpcs_code,
                state,
                specialty,
                claim_month,
                QUANTILE_CONT(paid_per_claim, 0.5) AS median_ppc,
                AVG(paid_per_claim) AS mean_ppc,
                STDDEV(paid_per_claim) AS sd_ppc,
                COUNT(*) AS peers
            FROM base
            GROUP BY hcpcs_code, state, specialty, claim_month
            HAVING COUNT(*) >= 20
        ),
        scored AS (
            SELECT
                b.billing_npi,
                b.hcpcs_code,
                b.claim_month,
                b.state,
                b.specialty,
                b.paid,
                b.claims,
                b.paid_per_claim,
                p.median_ppc,
                p.peers,
                (b.paid_per_claim - p.median_ppc) AS ppc_delta,
                (b.paid_per_claim - p.median_ppc) * b.claims AS excess_paid,
                CASE WHEN p.sd_ppc > 0 THEN (b.paid_per_claim - p.mean_ppc) / p.sd_ppc ELSE NULL END AS z_ppc
            FROM base b
            INNER JOIN peers p
                ON b.hcpcs_code = p.hcpcs_code
               AND b.state = p.state
               AND b.specialty = p.specialty
               AND b.claim_month = p.claim_month
            WHERE b.paid_per_claim > p.median_ppc
        )
        SELECT *
        FROM scored
        ORDER BY excess_paid DESC
        LIMIT 500
        """,
        os.path.join(OUTPUT_DIR, "ppc_residuals_top500.csv"),
    )

    # Growth anomalies: 2024 vs 2023 by provider (state + specialty peers)
    copy_query(
        con,
        """
        WITH yearly AS (
            SELECT
                billing_npi,
                state,
                specialty,
                year,
                SUM(paid) AS paid
            FROM provider_month_panel
            WHERE year IN ('2023', '2024')
            GROUP BY billing_npi, state, specialty, year
        ),
        pvt AS (
            SELECT
                billing_npi,
                state,
                specialty,
                SUM(CASE WHEN year = '2023' THEN paid ELSE 0 END) AS paid_2023,
                SUM(CASE WHEN year = '2024' THEN paid ELSE 0 END) AS paid_2024
            FROM yearly
            GROUP BY billing_npi, state, specialty
        ),
        growth AS (
            SELECT
                billing_npi,
                state,
                specialty,
                paid_2023,
                paid_2024,
                CASE WHEN paid_2023 > 0 THEN paid_2024 / paid_2023 - 1 ELSE NULL END AS growth
            FROM pvt
            WHERE paid_2023 > 0 AND paid_2024 > 0
        ),
        stats AS (
            SELECT
                state,
                specialty,
                AVG(growth) AS mean_growth,
                STDDEV(growth) AS sd_growth,
                COUNT(*) AS peers
            FROM growth
            GROUP BY state, specialty
            HAVING COUNT(*) >= 50
        ),
        scored AS (
            SELECT
                g.*,
                s.peers,
                CASE WHEN s.sd_growth > 0 THEN (g.growth - s.mean_growth) / s.sd_growth ELSE NULL END AS z_growth
            FROM growth g
            INNER JOIN stats s ON g.state = s.state AND g.specialty = s.specialty
        )
        SELECT *
        FROM scored
        WHERE growth > 1 AND z_growth > 3
        ORDER BY z_growth DESC
        LIMIT 500
        """,
        os.path.join(OUTPUT_DIR, "growth_anomalies_top500.csv"),
    )

    # Multivariate risk index
    copy_query(
        con,
        """
        WITH top_code_pct AS (
            SELECT
                billing_npi,
                MAX(paid) * 1.0 / NULLIF(SUM(paid), 0) AS top_code_pct
            FROM provider_hcpcs
            GROUP BY billing_npi
        ),
        monthly_cv AS (
            SELECT
                billing_npi,
                CASE WHEN AVG(paid) > 0 THEN STDDEV(paid) / AVG(paid) ELSE 0 END AS cv_monthly
            FROM provider_monthly
            GROUP BY billing_npi
        ),
        yoy_growth AS (
            SELECT
                billing_npi,
                CASE
                    WHEN SUM(CASE WHEN SUBSTR(claim_month, 1, 4) = '2023' THEN paid ELSE 0 END) > 0
                    THEN SUM(CASE WHEN SUBSTR(claim_month, 1, 4) = '2024' THEN paid ELSE 0 END)
                         / NULLIF(SUM(CASE WHEN SUBSTR(claim_month, 1, 4) = '2023' THEN paid ELSE 0 END), 0) - 1
                    ELSE NULL
                END AS yoy_growth
            FROM provider_monthly
            GROUP BY billing_npi
        ),
        base AS (
            SELECT
                ps.billing_npi,
                p.state,
                p.specialty,
                ps.total_paid,
                ps.avg_paid_per_claim,
                ps.avg_claims_per_bene,
                COALESCE(tc.top_code_pct, 0) AS top_code_pct,
                COALESCE(cv.cv_monthly, 0) AS cv_monthly,
                COALESCE(gr.yoy_growth, 0) AS yoy_growth
            FROM provider_summary ps
            LEFT JOIN providers p ON ps.billing_npi = p.npi
            LEFT JOIN top_code_pct tc ON ps.billing_npi = tc.billing_npi
            LEFT JOIN monthly_cv cv ON ps.billing_npi = cv.billing_npi
            LEFT JOIN yoy_growth gr ON ps.billing_npi = gr.billing_npi
            WHERE ps.total_paid > 0
        ),
        stats AS (
            SELECT
                state,
                specialty,
                AVG(avg_paid_per_claim) AS mean_ppc,
                STDDEV(avg_paid_per_claim) AS sd_ppc,
                AVG(avg_claims_per_bene) AS mean_cpb,
                STDDEV(avg_claims_per_bene) AS sd_cpb,
                AVG(top_code_pct) AS mean_top,
                STDDEV(top_code_pct) AS sd_top,
                AVG(cv_monthly) AS mean_cv,
                STDDEV(cv_monthly) AS sd_cv,
                AVG(yoy_growth) AS mean_growth,
                STDDEV(yoy_growth) AS sd_growth,
                COUNT(*) AS peers
            FROM base
            WHERE state IS NOT NULL AND state != ''
              AND specialty IS NOT NULL AND specialty != ''
            GROUP BY state, specialty
            HAVING COUNT(*) >= 50
        ),
        scored AS (
            SELECT
                b.*,
                s.peers,
                (b.avg_paid_per_claim - s.mean_ppc) / NULLIF(s.sd_ppc, 0) AS z_ppc,
                (b.avg_claims_per_bene - s.mean_cpb) / NULLIF(s.sd_cpb, 0) AS z_cpb,
                (b.top_code_pct - s.mean_top) / NULLIF(s.sd_top, 0) AS z_top,
                (b.cv_monthly - s.mean_cv) / NULLIF(s.sd_cv, 0) AS z_cv,
                (b.yoy_growth - s.mean_growth) / NULLIF(s.sd_growth, 0) AS z_growth
            FROM base b
            INNER JOIN stats s ON b.state = s.state AND b.specialty = s.specialty
        )
        SELECT
            billing_npi,
            state,
            specialty,
            total_paid,
            avg_paid_per_claim,
            avg_claims_per_bene,
            top_code_pct,
            cv_monthly,
            yoy_growth,
            z_ppc,
            z_cpb,
            z_top,
            z_cv,
            z_growth,
            GREATEST(z_ppc, 0) + GREATEST(z_cpb, 0) + GREATEST(z_top, 0) + GREATEST(z_cv, 0) + GREATEST(z_growth, 0) AS risk_index
        FROM scored
        ORDER BY risk_index DESC
        LIMIT 500
        """,
        os.path.join(OUTPUT_DIR, "multivariate_risk_top500.csv"),
    )

    # Report
    top_states = con.execute("""
        SELECT state, SUM(paid) AS total_paid
        FROM provider_month_panel
        WHERE state IS NOT NULL AND state != ''
        GROUP BY state
        ORDER BY total_paid DESC
        LIMIT 10
    """).fetchall()

    top_specialties = con.execute("""
        SELECT specialty, SUM(paid) AS total_paid
        FROM provider_month_panel
        WHERE specialty IS NOT NULL AND specialty != ''
        GROUP BY specialty
        ORDER BY total_paid DESC
        LIMIT 10
    """).fetchall()

    top_codes = con.execute("""
        SELECT hcpcs_code, total_paid
        FROM hcpcs_summary
        ORDER BY total_paid DESC
        LIMIT 10
    """).fetchall()

    report_path = os.path.join(OUTPUT_DIR, "longitudinal_multivariate_report.md")
    with open(report_path, "w") as f:
        f.write("# Longitudinal Multivariate Analysis\n\n")
        f.write(f"- Time range: {time_range[0]} to {time_range[1]} ({time_range[2]} months)\n")
        f.write(f"- Total paid: ${totals[0]:,.0f}\n")
        f.write(f"- Total claims: {totals[1]:,.0f}\n")
        f.write(f"- Total beneficiaries: {totals[2]:,.0f}\n\n")

        f.write("## Top 10 States by Total Paid\n\n")
        for state, paid in top_states:
            f.write(f"- {state}: ${paid:,.0f}\n")
        f.write("\n")

        f.write("## Top 10 Specialties by Total Paid\n\n")
        for specialty, paid in top_specialties:
            f.write(f"- {specialty}: ${paid:,.0f}\n")
        f.write("\n")

        f.write("## Top 10 HCPCS Codes by Total Paid\n\n")
        for code, paid in top_codes:
            f.write(f"- {code}: ${paid:,.0f}\n")
        f.write("\n")

        f.write("## Output Tables\n\n")
        f.write("- monthly_totals.csv\n")
        f.write("- state_monthly_totals.csv\n")
        f.write("- specialty_monthly_totals.csv\n")
        f.write("- code_monthly_totals_top200.csv\n")
        f.write("- ppc_residuals_top500.csv\n")
        f.write("- growth_anomalies_top500.csv\n")
        f.write("- multivariate_risk_top500.csv\n")

    con.close()
    print(f"Wrote analysis outputs to {OUTPUT_DIR}")
    print(f"Done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
