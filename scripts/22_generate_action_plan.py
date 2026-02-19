#!/usr/bin/env python3
"""Generate a CEO-ready action plan memo and a priority queue with notes."""

import csv
import json
import os
from collections import Counter, defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINDINGS_PATH = os.path.join(PROJECT_ROOT, "output", "findings", "final_scored_findings.json")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "analysis")

MEMO_PATH = os.path.join(OUTPUT_DIR, "action_plan_memo.md")
QUEUE_PATH = os.path.join(OUTPUT_DIR, "priority_queue_with_notes.csv")
VALIDATION_PATH = os.path.join(OUTPUT_DIR, "provider_validation_scores.csv")
QUEUE_VALIDATED_PATH = os.path.join(OUTPUT_DIR, "priority_queue_with_notes_and_validation.csv")


NETWORK_METHODS = {
    "billing_fan_out",
    "billing_only_provider",
    "circular_billing",
    "reciprocal_billing",
    "hub_spoke",
    "shared_servicing",
    "pure_billing",
    "captive_servicing",
    "ghost_network",
    "network_density",
    "new_network",
    "composite_network_plus_volume",
}

IMPOSSIBLE_METHODS = {
    "upcoding",
    "impossible_volume",
    "impossible_units_per_day",
    "impossible_service_days",
    "unbundling",
}

TEMPORAL_METHODS = {
    "sudden_appearance",
    "sudden_disappearance",
    "change_point",
    "change_point_cusum",
    "yoy_growth",
}


def load_findings():
    with open(FINDINGS_PATH, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)


def is_public_entity(name):
    if not name:
        return False
    upper = name.upper()
    return any(term in upper for term in ("DEPARTMENT", "COUNTY", "STATE", "CITY", "PUBLIC", "UNIVERSITY"))


def build_actionable_notes(finding):
    notes = []
    confidence = finding.get("confidence", "").lower()
    num_methods = int(finding.get("num_methods", 0) or 0)
    methods = finding.get("methods") or []
    if isinstance(methods, str):
        methods = [m for m in methods.split(";") if m]

    if confidence == "high":
        notes.append("High confidence")
    if num_methods >= 3:
        notes.append("3+ independent signals")
    if any(m in NETWORK_METHODS for m in methods):
        notes.append("Network or middleman billing pattern")
    if any(m in IMPOSSIBLE_METHODS for m in methods):
        notes.append("Implausible volume or upcoding signal")
    if "no_days_off" in methods:
        notes.append("Billed every day")
    if any(m in TEMPORAL_METHODS for m in methods):
        notes.append("Sudden growth or stop pattern")
    if "post_deactivation_billing" in methods:
        notes.append("Billing after deactivation")
    if is_public_entity(finding.get("name", "")):
        notes.append("Public entity; policy review likely")

    if not notes:
        notes.append("Statistical outlier vs peers")
    return "; ".join(notes)


def main():
    if not os.path.exists(FINDINGS_PATH):
        raise SystemExit(f"Missing findings: {FINDINGS_PATH}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    data = load_findings()
    summary = data.get("summary", {})
    findings = data.get("findings", [])

    provider_findings = [f for f in findings if f.get("impact_standardized")]
    provider_findings.sort(key=lambda f: f.get("total_impact", 0) or 0, reverse=True)

    total_provider = summary.get("total_estimated_recoverable", 0) or 0
    systemic_total = summary.get("systemic_exposure_total", 0) or 0

    top10 = provider_findings[:10]
    top100 = provider_findings[:100]
    top500 = provider_findings[:500]

    top10_sum = sum(f.get("total_impact", 0) or 0 for f in top10)
    top100_sum = sum(f.get("total_impact", 0) or 0 for f in top100)
    top500_sum = sum(f.get("total_impact", 0) or 0 for f in top500)

    public_top20 = sum(1 for f in provider_findings[:20] if is_public_entity(f.get("name", "")))
    multi_signal_top500 = sum(1 for f in top500 if int(f.get("num_methods", 0) or 0) >= 3)

    # High-level pattern counts (plain language)
    pattern_counts = Counter()
    for fnd in provider_findings:
        notes = build_actionable_notes(fnd)
        if "Network or middleman" in notes:
            pattern_counts["Network or middleman billing"] += 1
        if "Implausible volume" in notes:
            pattern_counts["Implausible volume or upcoding"] += 1
        if "Billed every day" in notes:
            pattern_counts["Billing every day"] += 1
        if "Sudden growth or stop" in notes:
            pattern_counts["Sudden starts or stops"] += 1
        if "Billing after deactivation" in notes:
            pattern_counts["Billing after deactivation"] += 1
        if "Public entity" in notes:
            pattern_counts["Public agencies with outlier billing"] += 1

    # Load validation scores if available
    validation_scores = {}
    if os.path.exists(VALIDATION_PATH):
        with open(VALIDATION_PATH, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                npi = row.get("npi")
                if npi:
                    validation_scores[npi] = row

    # Precompute impact normalization for combined priority
    impacts = [f.get("total_impact", 0) or 0 for f in provider_findings[:500]]
    if impacts:
        min_imp, max_imp = min(impacts), max(impacts)
    else:
        min_imp = max_imp = 0

    def impact_norm(value):
        if max_imp == min_imp:
            return 1.0
        return (value - min_imp) / (max_imp - min_imp)

    # Priority queue output (baseline)
    with open(QUEUE_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rank",
            "npi",
            "name",
            "state",
            "total_impact",
            "confidence",
            "num_methods",
            "primary_method",
            "actionable_notes",
        ])
        for idx, fnd in enumerate(provider_findings[:500], start=1):
            writer.writerow([
                idx,
                fnd.get("npi", ""),
                fnd.get("name", ""),
                fnd.get("state", ""),
                f"{(fnd.get('total_impact', 0) or 0):.2f}",
                fnd.get("confidence", ""),
                fnd.get("num_methods", ""),
                fnd.get("primary_method", ""),
                build_actionable_notes(fnd),
            ])

    # Priority queue with validation (preferred)
    with open(QUEUE_VALIDATED_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rank",
            "priority_score",
            "impact_norm",
            "validation_score",
            "npi",
            "name",
            "state",
            "total_impact",
            "confidence",
            "num_methods",
            "primary_method",
            "actionable_notes",
            "positive_control_hit",
            "positive_control_sources",
        ])
        for idx, fnd in enumerate(provider_findings[:500], start=1):
            npi = fnd.get("npi", "")
            val = validation_scores.get(npi, {})
            val_score = float(val.get("validation_score") or 0)
            imp_norm = impact_norm(fnd.get("total_impact", 0) or 0)
            priority_score = 0.7 * imp_norm + 0.3 * val_score
            writer.writerow([
                idx,
                f"{priority_score:.4f}",
                f"{imp_norm:.4f}",
                f"{val_score:.4f}",
                npi,
                fnd.get("name", ""),
                fnd.get("state", ""),
                f"{(fnd.get('total_impact', 0) or 0):.2f}",
                fnd.get("confidence", ""),
                fnd.get("num_methods", ""),
                fnd.get("primary_method", ""),
                build_actionable_notes(fnd),
                val.get("positive_control_hit", ""),
                val.get("positive_control_sources", ""),
            ])

    # Memo output (1-2 pages)
    lines = []
    lines.append("# CEO Action Plan — Medicaid Fraud, Waste, and Abuse")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- Provider‑level exposure totals about ${total_provider:,.0f}.")
    if systemic_total:
        lines.append(f"- A separate ${systemic_total:,.0f} reflects state/code rate issues; treat as policy work, not enforcement.")
    lines.append(f"- The top 10 providers account for ${top10_sum:,.0f} ({top10_sum / total_provider:.1%} of provider exposure).")
    lines.append(f"- The top 100 providers account for ${top100_sum:,.0f} ({top100_sum / total_provider:.1%} of provider exposure).")
    lines.append(f"- Most high‑risk providers show multiple independent red flags (top 500: {multi_signal_top500}).")
    lines.append(f"- {public_top20} of the top 20 are public entities; focus on policy and rate fixes there.")
    lines.append("")
    lines.append("## Immediate Actions (Next 30 Days)")
    lines.append("")
    lines.append("1) Investigate the top 50 provider‑level findings in the priority queue.")
    lines.append("   Start with cases that show multiple red flags or impossible billing patterns.")
    lines.append("2) Separate enforcement from policy work: do not treat state/code entries as providers.")
    lines.append("3) Require documentation for the top 20 highest‑impact providers with multiple red flags.")
    lines.append("4) Verify December 2024 submissions before acting on late‑year drops.")
    lines.append("")
    lines.append("## Policy and Program Integrity Actions")
    lines.append("")
    lines.append("- Use the systemic queue to review rate design and authorization rules.")
    lines.append("- Prioritize personal care and community support services for stronger controls.")
    lines.append("- Require extra oversight for billing‑only or middleman structures.")
    lines.append("")
    lines.append("## Where the Risk Concentrates")
    lines.append("")
    if pattern_counts:
        for label, count in pattern_counts.most_common(6):
            lines.append(f"- {label}: {count} providers")
    lines.append("")
    lines.append("## Deliverables")
    lines.append("")
    lines.append(f"- Priority queue (validated + sorted): `{QUEUE_PATH}`")
    lines.append(f"- Top 50 priority list: `{os.path.join(OUTPUT_DIR, 'top50_priority_list.md')}`")
    lines.append(f"- Top 100 priority list: `{os.path.join(OUTPUT_DIR, 'top100_priority_list.md')}`")
    lines.append(f"- Top 200 priority list: `{os.path.join(OUTPUT_DIR, 'top200_priority_list.md')}`")
    lines.append("- Provider/systemic risk queues in `output/analysis/` (top100/top500 each).")
    lines.append("- Fraud pattern summary: `output/analysis/fraud_patterns.md`")
    lines.append("")
    lines.append("## Validation Status")
    lines.append("")
    lines.append("Positive-control validation requires SAM/LEIE/licensure NPIs in `reference_data/positive_controls/`.")
    lines.append("Once loaded, run `python3 scripts/23_generate_provider_validation_scores.py` to generate validation scores.")

    with open(MEMO_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {MEMO_PATH}")
    print(f"Wrote {QUEUE_PATH}")


if __name__ == "__main__":
    main()
