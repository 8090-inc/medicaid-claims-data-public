#!/usr/bin/env python3
"""Build state quality weights from DQ Atlas measure_allStates export."""

import csv
import json
import os
from collections import defaultdict


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DQ_DIR = os.path.join(PROJECT_ROOT, "reference_data", "dq_atlas")
INPUT_PATH = os.path.join(DQ_DIR, "measure_allStates.csv")
OUTPUT_PATH = os.path.join(DQ_DIR, "state_quality_weights.csv")


LEVEL_WEIGHTS = {
    "Low concern": 1.0,
    "Medium concern": 0.85,
    "High concern": 0.7,
    "Unclassified": 0.6,
}

EXCLUDED_LEVELS = {"Excluded", "Unusable"}


def main():
    if not os.path.exists(INPUT_PATH):
        raise SystemExit(f"Missing DQ Atlas export: {INPUT_PATH}")

    scores = defaultdict(list)
    counts = defaultdict(lambda: defaultdict(int))

    with open(INPUT_PATH, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            payload = row.get("payload", "")
            if not payload:
                continue
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue
            for rec in data.get("data", []) or []:
                state = (rec.get("stateAbbreviation", "") or "").strip().upper()
                level = (rec.get("concernLevelDisplay", "") or "").strip()
                if not state or not level:
                    continue
                if level in EXCLUDED_LEVELS:
                    counts[state][level] += 1
                    continue
                weight = LEVEL_WEIGHTS.get(level)
                if weight is None:
                    continue
                scores[state].append(weight)
                counts[state][level] += 1

    if not scores:
        raise SystemExit("No state quality data found in payloads.")

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "state",
            "weight",
            "measures",
            "low_count",
            "medium_count",
            "high_count",
            "unclassified_count",
            "excluded_count",
            "unusable_count",
        ])
        for state in sorted(counts):
            vals = scores.get(state, [])
            avg = sum(vals) / len(vals) if vals else 0.5
            c = counts[state]
            writer.writerow([
                state,
                f"{avg:.4f}",
                len(vals),
                c.get("Low concern", 0),
                c.get("Medium concern", 0),
                c.get("High concern", 0),
                c.get("Unclassified", 0),
                c.get("Excluded", 0),
                c.get("Unusable", 0),
            ])

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
