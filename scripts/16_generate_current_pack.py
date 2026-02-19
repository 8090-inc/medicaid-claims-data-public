#!/usr/bin/env python3
"""Generate a current analysis pack from final_scored_findings.json.

Outputs:
  - output/analysis/risk_queue_top100.csv
  - output/analysis/risk_queue_top500.csv
  - output/analysis/risk_queue_providers_top100.csv
  - output/analysis/risk_queue_providers_top500.csv
  - output/analysis/risk_queue_systemic_top100.csv
  - output/analysis/risk_queue_systemic_top500.csv
  - output/analysis/current_analysis_pack.md
"""

import csv
import heapq
import json
import os


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINDINGS_PATH = os.path.join(PROJECT_ROOT, "output", "findings", "final_scored_findings.json")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "analysis")


def parse_summary(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        buf = f.read(5 * 1024 * 1024)
    idx = buf.find('"summary"')
    if idx == -1:
        return {}
    idx = buf.find("{", idx)
    if idx == -1:
        return {}
    decoder = json.JSONDecoder()
    summary, _ = decoder.raw_decode(buf[idx:])
    return summary


def stream_findings(path, on_item):
    decoder = json.JSONDecoder()
    buf = ""
    in_array = False
    chunk_size = 1024 * 1024
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            buf += chunk
            if not in_array:
                pos = buf.find('"findings"')
                if pos == -1:
                    buf = buf[-2048:]
                    continue
                start = buf.find("[", pos)
                if start == -1:
                    continue
                buf = buf[start + 1 :]
                in_array = True

            idx = 0
            while True:
                while idx < len(buf) and buf[idx] in " \r\n\t,":
                    idx += 1
                if idx < len(buf) and buf[idx] == "]":
                    return
                if idx >= len(buf):
                    break
                try:
                    obj, end = decoder.raw_decode(buf[idx:])
                except json.JSONDecodeError:
                    break
                on_item(obj)
                idx += end
            buf = buf[idx:]


def push_top(heap, item, key, limit):
    tie = item.get("npi", "")
    entry = (key, tie, item)
    if len(heap) < limit:
        heapq.heappush(heap, entry)
        return
    if key > heap[0][0]:
        heapq.heapreplace(heap, entry)


def write_csv(path, rows):
    fieldnames = [
        "npi",
        "name",
        "state",
        "confidence",
        "total_impact",
        "systemic_impact_raw",
        "weighted_impact",
        "score",
        "weighted_score",
        "num_methods",
        "primary_method",
        "methods",
        "hypothesis_ids",
        "state_quality_weight",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def is_systemic_entry(npi):
    if not npi:
        return False
    if npi.startswith("STATE_") or npi.startswith("PAIR_"):
        return True
    # Treat non-10-digit identifiers as systemic placeholders
    return not (len(npi) == 10 and npi.isdigit())


def main():
    if not os.path.exists(FINDINGS_PATH):
        raise SystemExit(f"Missing findings: {FINDINGS_PATH}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    summary = parse_summary(FINDINGS_PATH)

    top100 = []
    top500 = []
    top100_providers = []
    top500_providers = []
    top100_systemic = []
    top500_systemic = []
    state_counts = {}
    state_weighted = {}
    method_counts = {}
    method_weighted = {}

    def handle_item(item):
        npi = item.get("npi", "")
        name = item.get("name", "")
        state = (item.get("state") or "").strip().upper()
        conf = item.get("confidence", "")
        total_impact = float(item.get("total_impact", 0) or 0)
        systemic_impact_raw = float(item.get("systemic_impact_raw", 0) or 0)
        weighted_impact = float(item.get("weighted_impact", total_impact) or 0)
        score = float(item.get("score", 0) or 0)
        weighted_score = float(item.get("weighted_score", score) or 0)
        num_methods = int(item.get("num_methods", 0) or 0)
        primary_method = item.get("primary_method", "")
        methods = item.get("methods", []) or []
        hyp_ids = item.get("hypothesis_ids", []) or []
        weight = float(item.get("state_quality_weight", 1.0) or 1.0)

        record = {
            "npi": npi,
            "name": name,
            "state": state,
            "confidence": conf,
            "total_impact": round(total_impact, 2),
            "systemic_impact_raw": round(systemic_impact_raw, 2),
            "weighted_impact": round(weighted_impact, 2),
            "score": round(score, 4),
            "weighted_score": round(weighted_score, 4),
            "num_methods": num_methods,
            "primary_method": primary_method,
            "methods": ";".join(methods),
            "hypothesis_ids": ";".join(hyp_ids),
            "state_quality_weight": round(weight, 4),
        }

        push_top(top100, record, weighted_impact, 100)
        push_top(top500, record, weighted_impact, 500)

        if is_systemic_entry(npi):
            key = systemic_impact_raw if systemic_impact_raw > 0 else weighted_impact
            push_top(top100_systemic, record, key, 100)
            push_top(top500_systemic, record, key, 500)
        else:
            push_top(top100_providers, record, weighted_impact, 100)
            push_top(top500_providers, record, weighted_impact, 500)

        if state:
            state_counts[state] = state_counts.get(state, 0) + 1
            state_weighted[state] = state_weighted.get(state, 0) + weighted_impact

        for method in methods:
            method_counts[method] = method_counts.get(method, 0) + 1
            method_weighted[method] = method_weighted.get(method, 0) + weighted_impact

    stream_findings(FINDINGS_PATH, handle_item)

    top100_rows = [row for _, _, row in sorted(top100, key=lambda x: -x[0])]
    top500_rows = [row for _, _, row in sorted(top500, key=lambda x: -x[0])]
    top100_provider_rows = [row for _, _, row in sorted(top100_providers, key=lambda x: -x[0])]
    top500_provider_rows = [row for _, _, row in sorted(top500_providers, key=lambda x: -x[0])]
    top100_systemic_rows = [row for _, _, row in sorted(top100_systemic, key=lambda x: -x[0])]
    top500_systemic_rows = [row for _, _, row in sorted(top500_systemic, key=lambda x: -x[0])]

    write_csv(os.path.join(OUTPUT_DIR, "risk_queue_top100.csv"), top100_rows)
    write_csv(os.path.join(OUTPUT_DIR, "risk_queue_top500.csv"), top500_rows)
    write_csv(os.path.join(OUTPUT_DIR, "risk_queue_providers_top100.csv"), top100_provider_rows)
    write_csv(os.path.join(OUTPUT_DIR, "risk_queue_providers_top500.csv"), top500_provider_rows)
    write_csv(os.path.join(OUTPUT_DIR, "risk_queue_systemic_top100.csv"), top100_systemic_rows)
    write_csv(os.path.join(OUTPUT_DIR, "risk_queue_systemic_top500.csv"), top500_systemic_rows)

    top_states = sorted(state_weighted.items(), key=lambda x: -x[1])[:10]
    top_methods = sorted(method_weighted.items(), key=lambda x: -x[1])[:10]

    report_path = os.path.join(OUTPUT_DIR, "current_analysis_pack.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Current Analysis Pack\n\n")
        if summary:
            f.write("## Summary\n\n")
            f.write(f"- Total findings: {summary.get('total_findings', '')}\n")
            f.write(f"- High confidence: {summary.get('high_confidence', '')}\n")
            f.write(f"- Medium confidence: {summary.get('medium_confidence', '')}\n")
            f.write(f"- Low confidence: {summary.get('low_confidence', '')}\n")
        f.write(f"- Total estimated recoverable (standardized, provider-level): ${summary.get('total_estimated_recoverable', 0):,.0f}\n")
        if summary.get("systemic_exposure_total") is not None:
            f.write(f"- Systemic exposure (state/code aggregates): ${summary.get('systemic_exposure_total', 0):,.0f}\n")
            if summary.get("quality_weighted_total") is not None:
                f.write(f"- Quality-weighted recoverable: ${summary.get('quality_weighted_total', 0):,.0f}\n")
            if summary.get("pruned_methods_count"):
                f.write(f"- Pruned methods: {summary.get('pruned_methods_count')}\n")
                if summary.get("pruned_methods_path"):
                    f.write(f"- Pruned methods file: {summary.get('pruned_methods_path')}\n")
            if summary.get("quality_weights_applied") is not None:
                f.write(f"- Quality weights applied: {summary.get('quality_weights_applied')}\n")
            f.write("\n")

        f.write("## Top 10 States by Weighted Impact\n\n")
        for state, impact in top_states:
            f.write(f"- {state}: ${impact:,.0f}\n")
        f.write("\n")

        f.write("## Top 10 Methods by Weighted Impact (multi-method providers counted per method)\n\n")
        for method, impact in top_methods:
            f.write(f"- {method}: ${impact:,.0f}\n")
        f.write("\n")

        f.write("## Top 20 Risk Queue (weighted impact)\n\n")
        for row in top100_rows[:20]:
            f.write(f"- {row['npi']} {row['name']} ({row['state']}): "
                    f"${row['weighted_impact']:,.0f} ({row['confidence']})\n")
        f.write("\n")

        f.write("## Top 20 Provider-Level Risk Queue (weighted impact)\n\n")
        for row in top100_provider_rows[:20]:
            f.write(f"- {row['npi']} {row['name']} ({row['state']}): "
                    f"${row['weighted_impact']:,.0f} ({row['confidence']})\n")
        f.write("\n")

        f.write("## Top 20 Systemic / Rate-Level Risk Queue (weighted impact)\n\n")
        for row in top100_systemic_rows[:20]:
            f.write(f"- {row['npi']} {row['name']} ({row['state']}): "
                    f"${row['weighted_impact']:,.0f} ({row['confidence']})\n")
        f.write("\n")

        f.write("## Outputs\n\n")
        f.write("- risk_queue_top100.csv\n")
        f.write("- risk_queue_top500.csv\n")
        f.write("- risk_queue_providers_top100.csv\n")
        f.write("- risk_queue_providers_top500.csv\n")
        f.write("- risk_queue_systemic_top100.csv\n")
        f.write("- risk_queue_systemic_top500.csv\n")

    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
