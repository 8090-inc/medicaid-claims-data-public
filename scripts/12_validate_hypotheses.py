#!/usr/bin/env python3
"""Validate hypotheses by summarizing findings per hypothesis.

Produces CSV and Markdown summaries in output/analysis.
"""

import os
import time

import duckdb

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINDINGS_PATH = os.path.join(PROJECT_ROOT, "output", "findings", "all_hypotheses.json")
HYPOTHESES_PATH = os.path.join(PROJECT_ROOT, "output", "hypotheses", "all_hypotheses_testable.json")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "analysis")


def main():
    t0 = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(FINDINGS_PATH):
        raise SystemExit(f"Missing findings file: {FINDINGS_PATH}")
    if not os.path.exists(HYPOTHESES_PATH):
        raise SystemExit(f"Missing hypotheses file: {HYPOTHESES_PATH}")

    con = duckdb.connect()

    con.execute("""
        CREATE TEMP TABLE finding_summary AS
        SELECT
            hypothesis_id,
            COUNT(*) AS num_findings,
            SUM(total_impact) AS total_impact,
            AVG(total_impact) AS avg_impact
        FROM read_json_auto(?)
        GROUP BY hypothesis_id
    """, [FINDINGS_PATH])

    con.execute("""
        CREATE TEMP TABLE hypotheses AS
        SELECT
            id AS hypothesis_id,
            category,
            subcategory,
            description,
            method,
            acceptance_criteria
        FROM read_json_auto(?)
    """, [HYPOTHESES_PATH])

    con.execute("""
        CREATE TEMP TABLE hypothesis_validation AS
        SELECT
            h.hypothesis_id,
            h.category,
            h.subcategory,
            h.method,
            h.description,
            h.acceptance_criteria,
            COALESCE(f.num_findings, 0) AS num_findings,
            COALESCE(f.total_impact, 0) AS total_impact,
            COALESCE(f.avg_impact, 0) AS avg_impact,
            CASE WHEN COALESCE(f.num_findings, 0) > 0 THEN 'supported' ELSE 'not_supported' END AS validation_status
        FROM hypotheses h
        LEFT JOIN finding_summary f ON h.hypothesis_id = f.hypothesis_id
    """)

    csv_path = os.path.join(OUTPUT_DIR, "hypothesis_validation_summary.csv")
    con.execute(f"""
        COPY (
            SELECT * FROM hypothesis_validation
            ORDER BY num_findings DESC, total_impact DESC
        ) TO '{csv_path}' (HEADER, DELIMITER ',')
    """)

    # Build a concise markdown summary
    totals = con.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN validation_status = 'supported' THEN 1 ELSE 0 END) AS supported,
            SUM(CASE WHEN validation_status = 'not_supported' THEN 1 ELSE 0 END) AS not_supported
        FROM hypothesis_validation
    """).fetchone()

    top_by_impact = con.execute("""
        SELECT hypothesis_id, description, total_impact, num_findings
        FROM hypothesis_validation
        ORDER BY total_impact DESC
        LIMIT 20
    """).fetchall()

    top_by_count = con.execute("""
        SELECT hypothesis_id, description, num_findings, total_impact
        FROM hypothesis_validation
        ORDER BY num_findings DESC
        LIMIT 20
    """).fetchall()

    by_method = con.execute("""
        SELECT method,
               COUNT(*) AS hypotheses,
               SUM(num_findings) AS total_findings,
               SUM(total_impact) AS total_impact
        FROM hypothesis_validation
        GROUP BY method
        ORDER BY total_impact DESC
    """).fetchall()

    ghost_summary = con.execute("""
        SELECT
            COUNT(DISTINCT hypothesis_id) AS hyp_count,
            SUM(num_findings) AS total_findings,
            SUM(total_impact) AS total_impact
        FROM hypothesis_validation
        WHERE method = 'ghost_network'
    """).fetchone()

    md_path = os.path.join(OUTPUT_DIR, "hypothesis_validation_summary.md")
    with open(md_path, "w") as f:
        f.write("# Hypothesis Validation Summary\n\n")
        f.write(f"- Total hypotheses: {totals[0]}\n")
        f.write(f"- Supported (>=1 finding): {totals[1]}\n")
        f.write(f"- Not supported (0 findings): {totals[2]}\n\n")

        f.write("## Top 20 by Total Estimated Impact\n\n")
        for hyp_id, desc, impact, count in top_by_impact:
            f.write(f"- {hyp_id}: ${impact:,.0f} across {count} findings — {desc}\n")
        f.write("\n")

        f.write("## Top 20 by Finding Count\n\n")
        for hyp_id, desc, count, impact in top_by_count:
            f.write(f"- {hyp_id}: {count} findings, ${impact:,.0f} — {desc}\n")
        f.write("\n")

        f.write("## Totals by Method\n\n")
        for method, hyp_count, total_findings, total_impact in by_method:
            f.write(f"- {method}: {hyp_count} hypotheses, {total_findings} findings, ${total_impact:,.0f}\n")

        f.write("\n## Ghost Network (Collapsed View)\n\n")
        if ghost_summary and ghost_summary[0]:
            f.write(f"- Composite ghost_network: {ghost_summary[0]} hypotheses, "
                    f"{ghost_summary[1]} findings, ${ghost_summary[2]:,.0f}\n")
        else:
            f.write("- No ghost_network hypotheses found.\n")

    con.close()
    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"Done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
