#!/usr/bin/env python3
"""Holdout + placebo calibration report for method stability.

Produces output/analysis/calibration_report.md and method_calibration.csv.
"""

import csv
import os
import time

import duckdb

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "medicaid.duckdb")
FINDINGS_DIR = os.path.join(PROJECT_ROOT, "output", "findings")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "analysis")
POSITIVE_CONTROLS_DIR = os.path.join(PROJECT_ROOT, "reference_data", "positive_controls")
POSITIVE_CONTROL_FILES = {
    "UPDATED.csv": "LEIE",
    "leie.csv": "LEIE",
    "leie_exclusions.csv": "LEIE",
    "sam_exclusions.csv": "SAM",
    "licensure_actions.csv": "LICENSURE",
}


def existing_findings_files():
    files = [
        "categories_1_to_5.json",
        "categories_6_and_7.json",
        "category_8.json",
        "categories_9_and_10.json",
    ]
    return [os.path.join(FINDINGS_DIR, f) for f in files if os.path.exists(os.path.join(FINDINGS_DIR, f))]


def read_positive_control_npis():
    npis_by_source = {}
    if not os.path.isdir(POSITIVE_CONTROLS_DIR):
        return npis_by_source
    for fname, label in POSITIVE_CONTROL_FILES.items():
        path = os.path.join(POSITIVE_CONTROLS_DIR, fname)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                continue
            npi_col = None
            for col in reader.fieldnames:
                if "npi" in col.lower():
                    npi_col = col
                    break
            if not npi_col:
                continue
            npis = set()
            for row in reader:
                npi = (row.get(npi_col, "") or "").strip()
                if len(npi) == 10 and npi.isdigit():
                    npis.add(npi)
            if npis:
                npis_by_source[label] = npis
    return npis_by_source


def main():
    t0 = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    findings_files = existing_findings_files()
    if not findings_files:
        raise SystemExit("No findings files found for calibration.")

    con = duckdb.connect(DB_PATH, read_only=True)

    con.execute("""
        CREATE TEMP TABLE method_npi AS
        SELECT NULL::VARCHAR AS method_name, NULL::VARCHAR AS npi
        WHERE 1=0
    """)

    # Extract method -> NPI map per file to avoid type conflicts
    for path in findings_files:
        col_type = con.execute(
            f"DESCRIBE SELECT flagged_providers FROM read_json_auto('{path}')"
        ).fetchone()[1]
        if 'STRUCT' in col_type:
            con.execute(f"""
                INSERT INTO method_npi
                SELECT DISTINCT
                    method_name,
                    fp.npi AS npi
                FROM read_json_auto('{path}'), UNNEST(flagged_providers) AS t(fp)
                WHERE fp.npi IS NOT NULL AND fp.npi != ''
            """)
        else:
            con.execute(f"""
                INSERT INTO method_npi
                SELECT DISTINCT
                    method_name,
                    CAST(fp AS VARCHAR) AS npi
                FROM read_json_auto('{path}'), UNNEST(flagged_providers) AS t(fp)
                WHERE fp IS NOT NULL AND fp != ''
            """)

    # Holdout providers
    con.execute("""
        CREATE TEMP TABLE holdout_providers AS
        SELECT DISTINCT billing_npi
        FROM provider_month_panel
        WHERE claim_month >= '2023-01'
    """)

    con.execute("""
        CREATE TEMP TABLE all_providers AS
        SELECT DISTINCT billing_npi
        FROM provider_summary
    """)

    baseline_holdout = con.execute("""
        SELECT
            COUNT(*)::DOUBLE / NULLIF((SELECT COUNT(*) FROM all_providers), 0)
        FROM holdout_providers
    """).fetchone()[0] or 0.0

    # Z-scores for paid_per_claim by state+specialty+month
    con.execute("""
        CREATE TEMP TABLE z_scores AS
        WITH base AS (
            SELECT
                billing_npi,
                claim_month,
                state,
                specialty,
                paid_per_claim,
                claims
            FROM provider_month_panel
            WHERE claims >= 10
              AND paid_per_claim IS NOT NULL
              AND state IS NOT NULL AND state != ''
              AND specialty IS NOT NULL AND specialty != ''
        ),
        peers AS (
            SELECT
                state,
                specialty,
                claim_month,
                AVG(paid_per_claim) AS mean_ppc,
                STDDEV(paid_per_claim) AS sd_ppc,
                COUNT(*) AS peers
            FROM base
            GROUP BY state, specialty, claim_month
            HAVING COUNT(*) >= 50
        )
        SELECT
            b.billing_npi,
            b.claim_month,
            CASE WHEN p.sd_ppc > 0 THEN (b.paid_per_claim - p.mean_ppc) / p.sd_ppc ELSE NULL END AS z_ppc
        FROM base b
        INNER JOIN peers p
            ON b.state = p.state AND b.specialty = p.specialty AND b.claim_month = p.claim_month
    """)

    # Method-level calibration
    con.execute("""
        CREATE TEMP TABLE method_calibration AS
        WITH counts AS (
            SELECT method_name, COUNT(DISTINCT npi) AS flagged_npis
            FROM method_npi
            GROUP BY method_name
        ),
        holdout AS (
            SELECT m.method_name,
                   COUNT(DISTINCT m.npi) AS holdout_npis
            FROM method_npi m
            INNER JOIN holdout_providers h ON m.npi = h.billing_npi
            GROUP BY m.method_name
        ),
        ztrain AS (
            SELECT m.method_name, AVG(z.z_ppc) AS train_z_mean
            FROM method_npi m
            INNER JOIN z_scores z ON m.npi = z.billing_npi
            WHERE z.claim_month <= '2022-12'
            GROUP BY m.method_name
        ),
        zhold AS (
            SELECT m.method_name, AVG(z.z_ppc) AS holdout_z_mean
            FROM method_npi m
            INNER JOIN z_scores z ON m.npi = z.billing_npi
            WHERE z.claim_month >= '2023-01'
            GROUP BY m.method_name
        )
        SELECT
            c.method_name,
            c.flagged_npis,
            COALESCE(h.holdout_npis, 0) AS holdout_npis,
            COALESCE(h.holdout_npis, 0) * 1.0 / NULLIF(c.flagged_npis, 0) AS holdout_rate,
            ? AS baseline_holdout_rate,
            zt.train_z_mean,
            zh.holdout_z_mean,
            zh.holdout_z_mean - zt.train_z_mean AS holdout_z_delta
        FROM counts c
        LEFT JOIN holdout h ON c.method_name = h.method_name
        LEFT JOIN ztrain zt ON c.method_name = zt.method_name
        LEFT JOIN zhold zh ON c.method_name = zh.method_name
    """, [baseline_holdout])

    # Positive controls (SAM / licensure) overlap
    npis_by_source = read_positive_control_npis()
    if npis_by_source:
        con.execute("""
            CREATE TEMP TABLE positive_controls (
                npi VARCHAR,
                source VARCHAR
            )
        """)
        for source, npis in npis_by_source.items():
            con.executemany(
                "INSERT INTO positive_controls VALUES (?, ?)",
                [(npi, source) for npi in npis],
            )

        con.execute("""
            CREATE TEMP TABLE method_positive_overlap AS
            WITH counts AS (
                SELECT method_name, COUNT(DISTINCT npi) AS flagged_npis
                FROM method_npi
                GROUP BY method_name
            )
            SELECT
                m.method_name,
                p.source,
                COUNT(DISTINCT m.npi) AS overlap_npis,
                COUNT(DISTINCT m.npi) * 1.0 / NULLIF(c.flagged_npis, 0) AS overlap_rate,
                c.flagged_npis
            FROM method_npi m
            INNER JOIN positive_controls p ON m.npi = p.npi
            INNER JOIN counts c ON m.method_name = c.method_name
            GROUP BY m.method_name, p.source, c.flagged_npis
        """)

        overlap_path = os.path.join(OUTPUT_DIR, "positive_control_overlaps.csv")
        con.execute(f"""
            COPY (
                SELECT * FROM method_positive_overlap
                ORDER BY overlap_rate DESC, overlap_npis DESC
            ) TO '{overlap_path}' (HEADER, DELIMITER ',')
        """)

    csv_path = os.path.join(OUTPUT_DIR, "method_calibration.csv")
    con.execute(f"""
        COPY (
            SELECT * FROM method_calibration
            ORDER BY holdout_rate DESC, flagged_npis DESC
        ) TO '{csv_path}' (HEADER, DELIMITER ',')
    """)

    top_unstable = con.execute("""
        SELECT method_name, holdout_rate, baseline_holdout_rate, holdout_z_delta, flagged_npis
        FROM method_calibration
        ORDER BY holdout_z_delta ASC
        LIMIT 15
    """).fetchall()

    top_stable = con.execute("""
        SELECT method_name, holdout_rate, baseline_holdout_rate, holdout_z_delta, flagged_npis
        FROM method_calibration
        ORDER BY holdout_z_delta DESC
        LIMIT 15
    """).fetchall()

    md_path = os.path.join(OUTPUT_DIR, "calibration_report.md")
    with open(md_path, "w") as f:
        f.write("# Calibration Report (Holdout + Placebo)\n\n")
        f.write(f"- Holdout window: 2023-01 to 2024-12\n")
        f.write(f"- Baseline holdout rate (all providers): {baseline_holdout:.2%}\n\n")

        f.write("## Most Unstable Methods (lowest holdout z-score delta)\n\n")
        for method, rate, baseline, delta, count in top_unstable:
            f.write(f"- {method}: holdout_rate={rate:.2%}, baseline={baseline:.2%}, "
                    f"z_delta={delta:.2f}, flagged={count}\n")
        f.write("\n")

        f.write("## Most Stable Methods (highest holdout z-score delta)\n\n")
        for method, rate, baseline, delta, count in top_stable:
            f.write(f"- {method}: holdout_rate={rate:.2%}, baseline={baseline:.2%}, "
                    f"z_delta={delta:.2f}, flagged={count}\n")

        if npis_by_source:
            f.write("\n## Positive Control Overlaps\n\n")
            for source in sorted(npis_by_source):
                total = len(npis_by_source[source])
                f.write(f"- {source}: {total} NPIs loaded\n")
            f.write("  See positive_control_overlaps.csv for per-method overlap rates.\n")

    con.close()
    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"Done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
