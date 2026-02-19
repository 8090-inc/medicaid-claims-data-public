#!/usr/bin/env python3
"""Generate a merged card set: aggregate cards + ranked hypothesis cards.

Outputs cards to output/cards/merged and writes merged_cards_index.csv.
"""

import csv
import json
import math
import os
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MERGED_DIR = os.path.join(PROJECT_ROOT, "output", "cards", "merged")
INDEX_PATH = os.path.join(MERGED_DIR, "merged_cards_index.csv")

HYP_CARD_INDEX = os.path.join(PROJECT_ROOT, "output", "cards", "hypothesis_cards_index.csv")
VALIDATION_CSV = os.path.join(PROJECT_ROOT, "output", "analysis", "hypothesis_validation_summary.csv")

CARD1 = os.path.join(PROJECT_ROOT, "card1-full-monthly-spending.png")
CARD2 = os.path.join(PROJECT_ROOT, "card2-full-top-procedures.png")
CARD3 = os.path.join(PROJECT_ROOT, "card3-full-top-providers.png")

WEIGHTS = {
    "impact": 0.50,
    "validation": 0.30,
    "novelty": 0.20,
}


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def load_hypothesis_cards():
    cards = {}
    if not os.path.exists(HYP_CARD_INDEX):
        return cards
    with open(HYP_CARD_INDEX, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            hyp_id = row.get("hypothesis_id")
            if not hyp_id:
                continue
            cards[hyp_id] = {
                "card_path": row.get("card_path"),
                "providers": int(row.get("providers") or 0),
                "total_impact": _safe_float(row.get("total_impact")),
                "title": row.get("title") or "",
                "subtitle": row.get("subtitle") or "",
            }
    return cards


def load_validation():
    rows = []
    if not os.path.exists(VALIDATION_CSV):
        return rows
    with open(VALIDATION_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            hyp_id = row.get("hypothesis_id")
            if not hyp_id:
                continue
            row["num_findings"] = int(row.get("num_findings") or 0)
            row["total_impact"] = _safe_float(row.get("total_impact"))
            rows.append(row)
    return rows


def normalize(values):
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if math.isclose(vmin, vmax):
        return [1.0 for _ in values]
    return [(v - vmin) / (vmax - vmin) for v in values]


def main():
    os.makedirs(MERGED_DIR, exist_ok=True)

    hyp_cards = load_hypothesis_cards()
    validation_rows = load_validation()

    if not validation_rows:
        raise SystemExit("Missing hypothesis validation summary; run scripts/12_validate_hypotheses.py first.")

    # Method frequency for novelty (rarer method = higher novelty)
    method_counts = {}
    for row in validation_rows:
        method = row.get("method") or "unknown"
        method_counts[method] = method_counts.get(method, 0) + 1

    # Prepare scoring inputs for supported hypotheses only
    supported = []
    for row in validation_rows:
        if (row.get("validation_status") or "").lower() != "supported":
            continue
        hyp_id = row.get("hypothesis_id")
        card_info = hyp_cards.get(hyp_id)
        if not card_info:
            continue
        total_impact = row.get("total_impact", 0.0)
        if total_impact <= 0:
            total_impact = card_info.get("total_impact", 0.0)
        supported.append({
            "hypothesis_id": hyp_id,
            "method": row.get("method") or "unknown",
            "num_findings": row.get("num_findings", 0),
            "total_impact": total_impact,
            "card_path": card_info.get("card_path"),
            "providers": card_info.get("providers", 0),
            "title": card_info.get("title", ""),
            "subtitle": card_info.get("subtitle", ""),
        })

    impact_vals = [math.log1p(s["total_impact"]) for s in supported]
    validation_vals = [math.log1p(s["num_findings"]) for s in supported]
    novelty_vals = [
        1.0 - (method_counts.get(s["method"], 1) / max(method_counts.values()))
        for s in supported
    ]

    impact_norm = normalize(impact_vals)
    validation_norm = normalize(validation_vals)
    novelty_norm = normalize(novelty_vals)

    for idx, s in enumerate(supported):
        s["score_impact"] = impact_norm[idx]
        s["score_validation"] = validation_norm[idx]
        s["score_novelty"] = novelty_norm[idx]
        s["score_total"] = (
            WEIGHTS["impact"] * s["score_impact"]
            + WEIGHTS["validation"] * s["score_validation"]
            + WEIGHTS["novelty"] * s["score_novelty"]
        )

    supported.sort(key=lambda x: x["score_total"], reverse=True)

    # Copy aggregate cards first
    aggregate_cards = [
        (0, "aggregate", "Monthly Spending Trend", CARD1),
        (1, "aggregate", "Top Procedures (flagged providers)", CARD2),
        (2, "aggregate", "Top Providers (flagged)", CARD3),
    ]

    with open(INDEX_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rank",
            "type",
            "title",
            "score_total",
            "score_impact",
            "score_validation",
            "score_novelty",
            "hypothesis_id",
            "method",
            "num_findings",
            "total_impact",
            "providers",
            "card_path",
            "source_card_path",
        ])

        for rank, card_type, title, src in aggregate_cards:
            if os.path.exists(src):
                dest_name = f"{rank:03d}_aggregate.png"
                dest_path = os.path.join(MERGED_DIR, dest_name)
                shutil.copyfile(src, dest_path)
                writer.writerow([
                    rank,
                    card_type,
                    title,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    dest_path,
                    src,
                ])

        # Hypothesis cards, ranked
        offset = len(aggregate_cards)
        for idx, s in enumerate(supported, start=offset):
            src = s["card_path"]
            if not src or not os.path.exists(src):
                continue
            dest_name = f"{idx:03d}_{s['hypothesis_id']}.png"
            dest_path = os.path.join(MERGED_DIR, dest_name)
            shutil.copyfile(src, dest_path)
            writer.writerow([
                idx,
                "hypothesis",
                s["title"],
                f"{s['score_total']:.4f}",
                f"{s['score_impact']:.4f}",
                f"{s['score_validation']:.4f}",
                f"{s['score_novelty']:.4f}",
                s["hypothesis_id"],
                s["method"],
                s["num_findings"],
                f"{s['total_impact']:.0f}",
                s["providers"],
                dest_path,
                src,
            ])

    print(f"Wrote merged cards to {MERGED_DIR}")
    print(f"Wrote index to {INDEX_PATH}")


if __name__ == "__main__":
    main()
