#!/usr/bin/env python3
"""Generate fraud_patterns.md with reproducible pattern counts and capped impact."""

import json
import os

import duckdb

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINDINGS_PATH = os.path.join(PROJECT_ROOT, "output", "findings", "final_scored_findings.json")
PROFILE_PATH = os.path.join(PROJECT_ROOT, "output", "data_profile.json")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "output", "analysis", "fraud_patterns.md")
DB_PATH = os.path.join(PROJECT_ROOT, "medicaid.duckdb")


HOME_CARE_CODES = {
    "T1019", "T1020", "S5125", "S5126", "S5130", "S5131", "S5170", "S5175"
}


def load_json(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)


def normalize_methods(methods):
    if isinstance(methods, str):
        return [m for m in methods.split(";") if m]
    return methods or []


def is_public_entity(name):
    if not name:
        return False
    upper = name.upper()
    return any(term in upper for term in ("DEPARTMENT", "COUNTY", "STATE", "CITY", "PUBLIC", "UNIVERSITY"))


def is_systemic_npi(npi):
    if not npi:
        return False
    if npi.startswith("STATE_") or npi.startswith("PAIR_"):
        return True
    return not (len(npi) == 10 and npi.isdigit())


def main():
    if not os.path.exists(FINDINGS_PATH):
        raise SystemExit(f"Missing findings: {FINDINGS_PATH}")
    if not os.path.exists(PROFILE_PATH):
        raise SystemExit(f"Missing profile: {PROFILE_PATH}")

    findings_data = load_json(FINDINGS_PATH)
    profile = load_json(PROFILE_PATH)
    findings = findings_data.get("findings", [])

    # Build top HCPCS code per provider for category tagging
    npis = [f["npi"] for f in findings if f.get("npi") and not is_systemic_npi(f.get("npi"))]
    code_lookup = {}
    if npis:
        con = duckdb.connect(DB_PATH, read_only=True)
        rows = con.execute("""
            SELECT billing_npi, hcpcs_code
            FROM (
                SELECT
                    billing_npi,
                    hcpcs_code,
                    ROW_NUMBER() OVER (PARTITION BY billing_npi ORDER BY paid DESC) AS rn
                FROM provider_hcpcs
                WHERE billing_npi IN (SELECT UNNEST(?::VARCHAR[]))
            ) t
            WHERE rn = 1
        """, [npis]).fetchall()
        con.close()
        code_lookup = {row[0]: row[1] for row in rows}

    patterns = [
        ("Home Health and Personal Care", "home_personal"),
        ("Middleman Billing Organizations", "middleman"),
        ("Government Agencies as Outliers", "government"),
        ("Providers That Cannot Exist", "nonexistent"),
        ("Billing Every Single Day", "no_days_off"),
        ("Sudden Starts and Stops", "sudden"),
        ("Billing Networks and Circular Billing", "network"),
        ("State-Level Spending Differences", "state_level"),
        ("Upcoding and Impossible Volumes", "impossible"),
        ("Shared Beneficiary Counts", "shared_benes"),
    ]

    counts = {key: 0 for _, key in patterns}
    totals = {key: 0.0 for _, key in patterns}

    provider_counts = {key: 0 for _, key in patterns}
    provider_totals = {key: 0.0 for _, key in patterns}
    systemic_counts = {key: 0 for _, key in patterns}
    systemic_totals = {key: 0.0 for _, key in patterns}

    # Method-based membership rules
    for f in findings:
        npi = f.get("npi", "")
        name = f.get("name", "")
        specialty = (f.get("specialty") or "").upper()
        methods = normalize_methods(f.get("methods", []))
        total_impact = float(f.get("total_impact", 0) or 0)
        systemic_raw = float(f.get("systemic_impact_raw", 0) or 0)
        top_code = code_lookup.get(npi, "")

        is_systemic = is_systemic_npi(npi)

        matches = set()

        # Pattern 1: home health & personal care
        if top_code in HOME_CARE_CODES or "HOME HEALTH" in specialty or "IN HOME" in specialty or "PERSONAL" in specialty:
            matches.add("home_personal")

        # Pattern 2: middleman billing organizations
        if any(m in methods for m in ("hub_spoke", "shared_servicing", "pure_billing",
                                      "captive_servicing", "billing_only_provider", "billing_fan_out")):
            matches.add("middleman")

        # Pattern 3: government agencies as outliers
        if is_public_entity(name):
            matches.add("government")

        # Pattern 4: providers that cannot exist
        if is_systemic or not name or "post_deactivation_billing" in methods:
            matches.add("nonexistent")

        # Pattern 5: billing every day
        if "no_days_off" in methods:
            matches.add("no_days_off")

        # Pattern 6: sudden starts/stops
        if any(m in methods for m in ("sudden_appearance", "sudden_disappearance", "change_point_cusum", "change_point", "yoy_growth")):
            matches.add("sudden")

        # Pattern 7: billing networks and circular billing
        if any(m in methods for m in ("circular_billing", "network_density", "ghost_network", "new_network",
                                      "hub_spoke", "composite_network_plus_volume", "reciprocal_billing")):
            matches.add("network")

        # Pattern 8: state-level spending differences
        if is_systemic and any(m in methods for m in ("state_peer_comparison", "state_spending_anomaly",
                                                     "geographic_monopoly", "peer_concentration")):
            matches.add("state_level")

        # Pattern 9: upcoding and impossible volumes
        if any(m in methods for m in ("upcoding", "impossible_volume", "impossible_units_per_day", "impossible_service_days", "unbundling")):
            matches.add("impossible")

        # Pattern 10: shared beneficiary counts
        if any(m in methods for m in ("shared_bene_count", "shared_flagged_benes", "bene_overlap_ring", "bene_network_spread")):
            matches.add("shared_benes")

        for key in matches:
            if is_systemic:
                systemic_counts[key] += 1
                systemic_totals[key] += systemic_raw
            else:
                provider_counts[key] += 1
                provider_totals[key] += total_impact

    total_paid = profile.get("total_paid", 0)
    total_rows = profile.get("total_rows", 0)
    total_impact = findings_data.get("summary", {}).get("total_estimated_recoverable", 0)
    systemic_total = findings_data.get("summary", {}).get("systemic_exposure_total", 0)

    lines = []
    lines.append("# Fraud, Waste, and Abuse Patterns in Medicaid Provider Spending")
    lines.append("")
    lines.append("**HHS Provider Spending Dataset, January 2018 through December 2024**")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(
        f"We analyzed ${total_paid:,.0f} in Medicaid provider spending across "
        f"{total_rows:,.0f} billing records from January 2018 through December 2024."
    )
    lines.append(
        "Provider-level pattern totals use a standardized impact formula: excess above peer median paid-per-claim, "
        "capped at total paid per provider. These are exposure ceilings, not guaranteed recoveries."
    )
    lines.append(
        f"Provider-level standardized exposure totals ${total_impact:,.0f}. "
        f"Systemic rate/code exposure totals ${systemic_total:,.0f} and is reported separately."
    )
    lines.append(
        "December 2024 data may be incomplete in some states; late submissions can depress recent-month totals."
    )
    lines.append("")
    lines.append("## Provider-Level Patterns (Standardized Impact)")
    lines.append("")
    lines.append("| #  | Pattern                                | Providers | Estimated Impact |")
    lines.append("| -- | -------------------------------------- | --------- | ---------------- |")
    for idx, (label, key) in enumerate(patterns, start=1):
        if label == "State-Level Spending Differences":
            continue
        lines.append(f"| {idx}  | {label:36} | {provider_counts[key]:9d} | ${provider_totals[key]/1e9:,.1f}B           |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Systemic Rate/Code Patterns (Reported Separately)")
    lines.append("")
    lines.append("| #  | Pattern                                | Providers | Estimated Exposure |")
    lines.append("| -- | -------------------------------------- | --------- | ------------------ |")
    # Only report systemic-relevant patterns
    for idx, (label, key) in enumerate(patterns, start=1):
        if label not in ("State-Level Spending Differences", "Providers That Cannot Exist", "Shared Beneficiary Counts"):
            continue
        lines.append(f"| {idx}  | {label:36} | {systemic_counts[key]:9d} | ${systemic_totals[key]/1e9:,.1f}B             |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Methodology (Reproducible Mapping)")
    lines.append("")
    lines.append("- **Home Health and Personal Care**: providers whose top paid code is T1019/T1020/S5125/S5126/S5130/S5131/S5170/S5175,")
    lines.append("  or specialties containing 'Home Health', 'In Home', or 'Personal'.")
    lines.append("- **Middleman Billing Organizations**: methods include hub_spoke, shared_servicing, pure_billing, captive_servicing,")
    lines.append("  billing_only_provider, billing_fan_out.")
    lines.append("- **Government Agencies as Outliers**: provider name contains Department/County/State/City/Public/University.")
    lines.append("- **Providers That Cannot Exist**: identifiers are STATE_/PAIR_ or non-10-digit NPIs or missing names,")
    lines.append("  plus post_deactivation_billing.")
    lines.append("- **Billing Every Single Day**: method includes no_days_off.")
    lines.append("- **Sudden Starts and Stops**: methods include sudden_appearance, sudden_disappearance, change_point(_cusum), yoy_growth.")
    lines.append("- **Billing Networks and Circular Billing**: methods include circular_billing, network_density, ghost_network, new_network,")
    lines.append("  hub_spoke, composite_network_plus_volume, reciprocal_billing.")
    lines.append("- **State-Level Spending Differences**: systemic identifiers with state_spending_anomaly, state_peer_comparison,")
    lines.append("  geographic_monopoly, or peer_concentration. Reported separately as systemic exposure.")
    lines.append("- **Upcoding and Impossible Volumes**: methods include upcoding, impossible_volume, impossible_units_per_day, impossible_service_days, unbundling.")
    lines.append("- **Shared Beneficiary Counts**: methods include shared_bene_count, shared_flagged_benes, bene_overlap_ring, bene_network_spread.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "*All patterns described above come from statistical analysis of the HHS Provider Spending dataset. "
        "They are risk indicators, not findings of fraud. Each one requires further investigation before enforcement action.*"
    )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
