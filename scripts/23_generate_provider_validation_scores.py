#!/usr/bin/env python3
"""Generate provider-level validation scores using positive controls and method stability."""

import csv
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINDINGS_PATH = os.path.join(PROJECT_ROOT, "output", "findings", "final_scored_findings.json")
CALIBRATION_PATH = os.path.join(PROJECT_ROOT, "output", "analysis", "method_calibration.csv")
POSITIVE_CONTROLS_DIR = os.path.join(PROJECT_ROOT, "reference_data", "positive_controls")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "output", "analysis", "provider_validation_scores.csv")


def load_findings():
    with open(FINDINGS_PATH, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)


def load_method_calibration():
    scores = {}
    if not os.path.exists(CALIBRATION_PATH):
        return scores
    with open(CALIBRATION_PATH, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            method = row.get("method_name")
            if not method:
                continue
            try:
                z_delta = float(row.get("holdout_z_delta") or 0)
            except ValueError:
                z_delta = 0.0
            scores[method] = z_delta
    # Normalize to 0..1
    if not scores:
        return scores
    values = list(scores.values())
    vmin, vmax = min(values), max(values)
    if vmin == vmax:
        return {k: 1.0 for k in scores}
    return {k: (v - vmin) / (vmax - vmin) for k, v in scores.items()}


def load_positive_controls():
    npis_by_source = {}
    if not os.path.isdir(POSITIVE_CONTROLS_DIR):
        return npis_by_source
    for fname in os.listdir(POSITIVE_CONTROLS_DIR):
        if not fname.endswith(".csv"):
            continue
        path = os.path.join(POSITIVE_CONTROLS_DIR, fname)
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
                label = os.path.splitext(fname)[0].upper()
                npis_by_source[label] = npis
    return npis_by_source


def main():
    if not os.path.exists(FINDINGS_PATH):
        raise SystemExit(f"Missing findings: {FINDINGS_PATH}")

    data = load_findings()
    findings = [f for f in data.get("findings", []) if f.get("impact_standardized")]
    method_scores = load_method_calibration()
    controls = load_positive_controls()
    controls_loaded = bool(controls)

    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "npi",
            "name",
            "state",
            "validation_score",
            "method_stability_score",
            "positive_control_hit",
            "positive_control_sources",
            "controls_loaded",
        ])

        for finding in findings:
            npi = finding.get("npi", "")
            name = finding.get("name", "")
            state = finding.get("state", "")
            methods = finding.get("methods") or []
            if isinstance(methods, str):
                methods = [m for m in methods.split(";") if m]

            # Method stability score: average normalized z_delta
            if methods and method_scores:
                vals = [method_scores.get(m, 0.0) for m in methods]
                stability = sum(vals) / len(vals)
            else:
                stability = 0.0

            hit = False
            sources = []
            for label, npis in controls.items():
                if npi in npis:
                    hit = True
                    sources.append(label)

            # Validation score: combine stability + positive control hit
            if controls_loaded:
                validation_score = 0.7 * stability + 0.3 * (1.0 if hit else 0.0)
            else:
                validation_score = stability

            writer.writerow([
                npi,
                name,
                state,
                f"{validation_score:.4f}",
                f"{stability:.4f}",
                "yes" if hit else "no",
                ";".join(sources),
                "yes" if controls_loaded else "no",
            ])

    print(f"Wrote {OUTPUT_PATH}")
    if not controls_loaded:
        print("Positive controls not found. Validation scores are stability-only.")


if __name__ == "__main__":
    main()
