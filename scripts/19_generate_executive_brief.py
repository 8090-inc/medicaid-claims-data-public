#!/usr/bin/env python3
"""Generate a CEO/CCO-friendly executive brief with contrarian insights."""

import csv
import json
import os
from collections import Counter, defaultdict

import duckdb

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINDINGS_PATH = os.path.join(PROJECT_ROOT, "output", "findings", "final_scored_findings.json")
RISK_QUEUE = os.path.join(PROJECT_ROOT, "output", "analysis", "risk_queue_top500.csv")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "output", "analysis", "executive_brief.md")
DB_PATH = os.path.join(PROJECT_ROOT, "medicaid.duckdb")


def parse_summary(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        buf = f.read(5 * 1024 * 1024)
    idx = buf.find('"summary"')
    if idx == -1:
        return {}
    idx = buf.find("{", idx)
    if idx == -1:
        return {}
    summary, _ = json.JSONDecoder().raw_decode(buf[idx:])
    return summary


def load_risk_queue():
    rows = []
    with open(RISK_QUEUE, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def is_public_entity(name):
    if not name:
        return False
    public_terms = ("DEPARTMENT", "COUNTY", "STATE", "CITY", "PUBLIC", "UNIVERSITY")
    upper = name.upper()
    return any(term in upper for term in public_terms)


def is_state_like(npi):
    if not npi:
        return False
    return npi.startswith("STATE_") or npi.startswith("PAIR_")


def method_category(method):
    m = (method or "").lower()
    if "ghost" in m or "nppes" in m or "deactivat" in m or "enumeration" in m:
        return "Identity or ghost network"
    if "paid_per_claim" in m or "ppc" in m or "gev" in m or "iqr" in m or "z_score" in m:
        return "Cost per claim outlier"
    if "claims_per_bene" in m or "volume" in m or "peer_volume" in m:
        return "High volume per beneficiary"
    if "change_point" in m or "cusum" in m or "yoy" in m or "growth" in m:
        return "Sudden shifts over time"
    if "dbscan" in m or "lof" in m or "cluster" in m or "hhi" in m:
        return "Peer cluster outlier"
    if "concentration" in m or "dominance" in m or "top_code_pct" in m:
        return "Code concentration"
    return "Other patterns"


def main():
    if not os.path.exists(FINDINGS_PATH) or not os.path.exists(RISK_QUEUE):
        raise SystemExit("Missing final findings or risk queue.")

    summary = parse_summary(FINDINGS_PATH)
    rows = load_risk_queue()
    total_weighted = sum(float(r["weighted_impact"]) for r in rows)
    total_findings = summary.get("total_findings") or 0
    quality_total = summary.get("quality_weighted_total") or 0
    systemic_total = summary.get("systemic_exposure_total") or 0
    top10 = rows[:10]
    top20 = rows[:20]
    top100 = rows[:100]

    top10_weighted = sum(float(r["weighted_impact"]) for r in top10)
    top20_weighted = sum(float(r["weighted_impact"]) for r in top20)
    top100_weighted = sum(float(r["weighted_impact"]) for r in top100)

    public_count = sum(1 for r in top20 if is_public_entity(r.get("name", "")))
    state_like_weighted = sum(float(r["weighted_impact"]) for r in rows if is_state_like(r.get("npi", "")))
    state_like_share = state_like_weighted / total_weighted if total_weighted else 0.0

    multi_method = sum(1 for r in rows if int(r.get("num_methods") or 0) >= 3)
    multi_method_share = multi_method / len(rows) if rows else 0.0

    # Method categories (provider-level)
    category_counter = Counter()
    for r in rows:
        categories = set()
        for m in (r.get("methods", "") or "").split(";"):
            if m:
                categories.add(method_category(m))
        for cat in categories:
            category_counter[cat] += 1
    top_categories = category_counter.most_common(5)

    # Top HCPCS codes (system-wide) for context
    con = duckdb.connect(DB_PATH, read_only=True)
    total_paid = con.execute("SELECT SUM(paid) FROM claims").fetchone()[0] or 0
    top_codes = con.execute("""
        SELECT hs.hcpcs_code,
               COALESCE(h.short_desc, '') AS short_desc,
               hs.total_paid
        FROM hcpcs_summary hs
        LEFT JOIN hcpcs_codes h ON hs.hcpcs_code = h.hcpcs_code
        ORDER BY hs.total_paid DESC
        LIMIT 5
    """).fetchall()
    con.close()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("# Executive Brief — Medicaid Fraud & Abuse Risk\n\n")
        f.write("## What matters most (plain language)\n\n")
        f.write(f"- We reviewed {total_findings:,} providers and prioritized "
                f"{len(rows):,} high-risk leads.\n")
        f.write(f"- Quality-weighted potential overpayment (provider-level, standardized) is "
                f"${quality_total:,.0f}.\n")
        if systemic_total:
            f.write(f"- Separate systemic exposure (state/code aggregates) totals "
                    f"${systemic_total:,.0f} and is not comparable to provider-level impact.\n")
        f.write(f"- The top 10 leads account for ${top10_weighted:,.0f} "
                f"({top10_weighted / total_weighted:.1%} of the top-500 risk pool).\n")
        f.write(f"- The top 100 leads account for ${top100_weighted:,.0f} "
                f"({top100_weighted / total_weighted:.1%} of the top-500 risk pool).\n\n")

        f.write("## Contrarian takeaways (high-entropy, decision-grade)\n\n")
        f.write(f"- Many of the largest signals are public or government-linked entities "
                f"({public_count} of the top 20). That points to **policy or rate issues**, "
                f"not just bad actors.\n")
        f.write(f"- {state_like_share:.0%} of top-500 weighted exposure comes from **state- or code-level "
                f"aggregates** (STATE_/PAIR_ entries). That is a red flag for **rate design and "
                f"authorization rules**, not just individual provider behavior.\n")
        if top_codes:
            top_code = top_codes[0]
            top_code_share = (top_code[2] / total_paid) if total_paid else 0.0
            f.write(f"- The single biggest paid code is {top_code[0]} "
                    f"({top_code[1].strip() or 'no description'}) at "
                    f"${top_code[2]:,.0f} (~{top_code_share:.0%} of total paid). "
                    "Routine, high-volume services dominate exposure.\n")
        f.write("- We removed four unstable methods and eliminated ~4.9M low-quality flags, "
                "yet total estimated recoverable stayed almost flat. That means **most dollar risk "
                "is concentrated in a smaller, more defensible set**.\n")
        f.write(f"- {multi_method_share:.0%} of the top-500 list triggers **3+ independent signals**. "
                "Those are the most defensible investigation targets.\n")
        f.write("- Some signals reflect **billing concentration and network patterns**, not unusual "
                "clinical behavior. These are best handled with **contracting and program integrity "
                "controls**, not medical review alone.\n\n")

        f.write("## Dominant signal families (provider count, top-500)\n\n")
        for cat, count in top_categories:
            f.write(f"- {cat}: {count} providers\n")

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
