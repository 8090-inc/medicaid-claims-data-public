#!/usr/bin/env python3
"""Generate fraud heatmap PNG images (4 variants) from pipeline outputs."""

import json
import os
import shutil

import duckdb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINDINGS_PATH = os.path.join(PROJECT_ROOT, "output", "findings", "final_scored_findings.json")
PROFILE_PATH = os.path.join(PROJECT_ROOT, "output", "data_profile.json")
DB_PATH = os.path.join(PROJECT_ROOT, "medicaid.duckdb")
CHARTS_DIR = os.path.join(PROJECT_ROOT, "output", "charts")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")

# 8090 Design System colors
FACTORY_BLUE_DARK = '#0052CC'
FACTORY_BLUE_MED = '#4D94FF'
FACTORY_BLUE_LIGHT = '#B3D4FF'
FACTORY_BLUE_BG = '#EBF0FA'
GRAY_BG = '#F0F0F0'
DARK_TEXT = '#1A1A1A'
MUTED_TEXT = '#666666'
LIGHT_BORDER = '#D0D0D0'
WHITE = '#FFFFFF'

HOME_CARE_CODES = {"T1019", "T1020", "S5125", "S5126", "S5130", "S5131", "S5170", "S5175"}

PATTERNS = [
    ("Home Health & Personal Care", "home_personal"),
    ("Middleman Billing Organizations", "middleman"),
    ("Government Agencies as Outliers", "government"),
    ("Providers That Cannot Exist", "nonexistent"),
    ("Billing Every Single Day", "no_days_off"),
    ("Sudden Starts and Stops", "sudden"),
    ("Billing Networks & Circular Billing", "network"),
    ("State-Level Spending Differences", "state_level"),
    ("Upcoding & Impossible Volumes", "impossible"),
    ("Shared Beneficiary Counts", "shared_benes"),
]

PATTERN_DESCRIPTIONS = {
    "home_personal": "Coded as personal care or home health;\ncritically hard to verify outside of the home.",
    "middleman": "Billing organizations that don't deliver care;\nproviders but may not exist without delivering any\npatient services.",
    "government": "State agencies that look very different from\nprivate-sector peers. Not fraud — a rate and\nprogram design concern.",
    "nonexistent": "Billing under deactivated or unregistered\nidentifiers. Basic compliance failure that\nshould not exist.",
    "no_days_off": "Providers that billed Medicaid every calendar day\nacross multiple years without any breaks.",
    "sudden": "Providers that appeared or disappeared abruptly, with\nbilling anomaly, or had extreme\nchangepoints in their monthly totals.",
    "network": "Billing relationships where providers bill\nthrough each other or charge rates far above\npeers.",
    "state_level": "States paying more than double the national\naverage for specific services. A policy issue,\nnot provider-level fraud.",
    "impossible": "Billing for more expensive services than\ndelivered, or claiming more hours in a day than\nexist. Classic billing fraud indicator.",
    "shared_benes": "Provider pairs serving the exact same number of\npatients. May indicate shared ownership or\ncoordinated billing.",
}

# Static qualitative risk assessments
RISK_ASSESSMENTS = {
    "home_personal":  {"fraud": "High", "waste": "High", "policy": "Med"},
    "middleman":      {"fraud": "High", "waste": "High", "policy": "Med"},
    "government":     {"fraud": "—",    "waste": "Med",  "policy": "High"},
    "nonexistent":    {"fraud": "High", "waste": "Low",  "policy": "Low"},
    "no_days_off":    {"fraud": "Med",  "waste": "Med",  "policy": "—"},
    "sudden":         {"fraud": "High", "waste": "Med",  "policy": "Med"},
    "network":        {"fraud": "High", "waste": "Med",  "policy": "Low"},
    "state_level":    {"fraud": "Low",  "waste": "—",    "policy": "High"},
    "impossible":     {"fraud": "High", "waste": "High", "policy": "—"},
    "shared_benes":   {"fraud": "Med",  "waste": "Low",  "policy": "Low"},
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


def classify_findings(findings, code_lookup):
    """Classify findings into patterns, return per-pattern counts and totals."""
    provider_counts = {key: 0 for _, key in PATTERNS}
    provider_totals = {key: 0.0 for _, key in PATTERNS}
    systemic_counts = {key: 0 for _, key in PATTERNS}
    systemic_totals = {key: 0.0 for _, key in PATTERNS}

    for f in findings:
        npi = f.get("npi", "")
        name = f.get("name", "")
        specialty = (f.get("specialty") or "").upper()
        methods = normalize_methods(f.get("methods", []))
        total_impact = float(f.get("total_impact", 0) or 0)
        systemic_raw = float(f.get("systemic_impact_raw", 0) or 0)
        top_code = code_lookup.get(npi, "")
        is_sys = is_systemic_npi(npi)

        matches = set()

        if top_code in HOME_CARE_CODES or "HOME HEALTH" in specialty or "IN HOME" in specialty or "PERSONAL" in specialty:
            matches.add("home_personal")
        if any(m in methods for m in ("hub_spoke", "shared_servicing", "pure_billing",
                                      "captive_servicing", "billing_only_provider", "billing_fan_out")):
            matches.add("middleman")
        if is_public_entity(name):
            matches.add("government")
        if is_sys or not name or "post_deactivation_billing" in methods:
            matches.add("nonexistent")
        if "no_days_off" in methods:
            matches.add("no_days_off")
        if any(m in methods for m in ("sudden_appearance", "sudden_disappearance", "change_point_cusum", "change_point", "yoy_growth")):
            matches.add("sudden")
        if any(m in methods for m in ("circular_billing", "network_density", "ghost_network", "new_network",
                                      "hub_spoke", "composite_network_plus_volume", "reciprocal_billing")):
            matches.add("network")
        if is_sys and any(m in methods for m in ("state_peer_comparison", "state_spending_anomaly",
                                                 "geographic_monopoly", "peer_concentration")):
            matches.add("state_level")
        if any(m in methods for m in ("upcoding", "impossible_volume", "impossible_units_per_day", "impossible_service_days", "unbundling")):
            matches.add("impossible")
        if any(m in methods for m in ("shared_bene_count", "shared_flagged_benes", "bene_overlap_ring", "bene_network_spread")):
            matches.add("shared_benes")

        for key in matches:
            if is_sys:
                systemic_counts[key] += 1
                systemic_totals[key] += systemic_raw
            else:
                provider_counts[key] += 1
                provider_totals[key] += total_impact

    return provider_counts, provider_totals, systemic_counts, systemic_totals


def format_dollars_short(amount):
    if amount >= 1e9:
        return f"${amount/1e9:.1f}B"
    elif amount >= 1e6:
        return f"${amount/1e6:.1f}M"
    elif amount >= 1e3:
        return f"${amount/1e3:.1f}K"
    return f"${amount:,.0f}"


def blue_intensity(val, vmin, vmax):
    """Map a value to a blue color on gradient from light to dark."""
    if vmax == vmin:
        return FACTORY_BLUE_MED
    norm = (val - vmin) / (vmax - vmin)
    norm = max(0, min(1, norm))
    # Interpolate from light (#EBF0FA) to dark (#0052CC)
    r = int(0xEB + (0x00 - 0xEB) * norm)
    g = int(0xF0 + (0x52 - 0xF0) * norm)
    b = int(0xFA + (0xCC - 0xFA) * norm)
    return f'#{r:02X}{g:02X}{b:02X}'


def risk_color(level):
    if level == "High":
        return FACTORY_BLUE_DARK
    elif level == "Med":
        return FACTORY_BLUE_MED
    elif level == "Low":
        return FACTORY_BLUE_LIGHT
    return GRAY_BG


def risk_text_color(level):
    if level in ("High", "Med"):
        return WHITE
    return DARK_TEXT


def get_combined_counts(p_counts, p_totals, s_counts, s_totals):
    """Get display counts and totals per pattern (provider-level preferred, systemic for state_level)."""
    rows = []
    for idx, (label, key) in enumerate(PATTERNS):
        if key == "state_level":
            count = s_counts[key]
            total = s_totals[key]
        elif key == "nonexistent":
            # Show provider-level count + total for display, note systemic separately
            count = p_counts[key]
            total = p_totals[key]
        else:
            count = p_counts[key]
            total = p_totals[key]
        rows.append({
            "idx": idx + 1,
            "label": label,
            "key": key,
            "providers": count,
            "exposure": total,
            "exposure_str": format_dollars_short(total),
            "description": PATTERN_DESCRIPTIONS[key],
            "risk": RISK_ASSESSMENTS[key],
        })
    return rows


def draw_rounded_rect(ax, x, y, w, h, color, radius=0.005):
    """Draw a filled rounded rectangle."""
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
                                    facecolor=color, edgecolor='none', transform=ax.transAxes)
    ax.add_patch(rect)


def draw_cell(ax, x, y, w, h, color, text='', text_color=DARK_TEXT, fontsize=8, bold=False):
    """Draw a colored cell with centered text."""
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0",
                                    facecolor=color, edgecolor=LIGHT_BORDER, linewidth=0.5,
                                    transform=ax.transAxes)
    ax.add_patch(rect)
    if text:
        weight = 'bold' if bold else 'normal'
        ax.text(x + w/2, y + h/2, text, transform=ax.transAxes,
                ha='center', va='center', fontsize=fontsize, color=text_color, fontweight=weight)


def generate_aligned(rows, profile, findings_data):
    """Generate fraud_heatmap_aligned.png — single-section layout with descriptions."""
    fig = plt.figure(figsize=(12, 11), facecolor=WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    total_paid = profile.get("total_paid", 0)
    total_rows = profile.get("total_rows", 0)
    total_impact = findings_data.get("summary", {}).get("total_estimated_recoverable", 0)
    systemic_total = findings_data.get("summary", {}).get("systemic_exposure_total", 0)

    # Title
    ax.text(0.03, 0.97, "Medicaid Fraud, Waste, and Abuse Pattern Heat Map",
            fontsize=16, fontweight='bold', color=DARK_TEXT, va='top', transform=ax.transAxes)
    ax.text(0.03, 0.945,
            f"Health and Human Services Provider Spending Dataset  ·  {total_rows/1e6:.0f}M+ entries across {total_rows/1e6:.0f}M records  ·  Jan 2018 – Dec 2024",
            fontsize=8, color=MUTED_TEXT, va='top', transform=ax.transAxes)
    ax.text(0.03, 0.93,
            f"Provider-level exposure: {format_dollars_short(total_impact)}  ·  Systemic exposure: {format_dollars_short(systemic_total)}",
            fontsize=8, color=MUTED_TEXT, va='top', transform=ax.transAxes)

    # Legend
    ax.text(0.03, 0.91, "SCALE:", fontsize=6, color=MUTED_TEXT, va='top', fontweight='bold')
    legend_colors = [FACTORY_BLUE_BG, FACTORY_BLUE_LIGHT, FACTORY_BLUE_MED, FACTORY_BLUE_DARK]
    legend_labels = ["Low", "", "", "High"]
    for i, (c, l) in enumerate(zip(legend_colors, legend_labels)):
        lx = 0.065 + i * 0.025
        draw_cell(ax, lx, 0.905, 0.02, 0.012, c)
    ax.text(0.065, 0.90, "Low", fontsize=5, color=MUTED_TEXT, va='top')
    ax.text(0.14, 0.90, "High", fontsize=5, color=MUTED_TEXT, va='top')

    # Column headers
    header_y = 0.875
    col_x = {"pattern": 0.03, "providers": 0.42, "exposure": 0.52, "fraud": 0.64, "waste": 0.73, "policy": 0.82}
    col_w = {"providers": 0.08, "exposure": 0.10, "fraud": 0.08, "waste": 0.08, "policy": 0.08}

    ax.text(col_x["pattern"], header_y, "PATTERN", fontsize=7, color=MUTED_TEXT, fontweight='bold', va='center')
    ax.text(col_x["providers"] + col_w["providers"]/2, header_y, "PROVIDERS", fontsize=7, color=MUTED_TEXT, fontweight='bold', va='center', ha='center')
    ax.text(col_x["exposure"] + col_w["exposure"]/2, header_y, "EXPOSURE", fontsize=7, color=MUTED_TEXT, fontweight='bold', va='center', ha='center')
    ax.text(col_x["fraud"] + col_w["fraud"]/2, header_y, "FRAUD", fontsize=7, color=MUTED_TEXT, fontweight='bold', va='center', ha='center')
    ax.text(col_x["waste"] + col_w["waste"]/2, header_y, "WASTE", fontsize=7, color=MUTED_TEXT, fontweight='bold', va='center', ha='center')
    ax.text(col_x["policy"] + col_w["policy"]/2, header_y, "POLICY", fontsize=7, color=MUTED_TEXT, fontweight='bold', va='center', ha='center')

    # Separator line
    ax.plot([0.03, 0.97], [0.86, 0.86], color=LIGHT_BORDER, linewidth=0.5, transform=ax.transAxes)

    # Compute intensity ranges for heatmap cells
    all_providers = [r["providers"] for r in rows]
    all_exposure = [r["exposure"] for r in rows]
    prov_min, prov_max = min(all_providers), max(all_providers)
    exp_min, exp_max = min(all_exposure), max(all_exposure)

    # Draw rows
    row_height = 0.072
    start_y = 0.845

    for i, row in enumerate(rows):
        y = start_y - i * row_height

        # Circled number
        circle = mpatches.Circle((0.045, y - row_height/2 + 0.005), 0.012,
                                  facecolor=FACTORY_BLUE_DARK, edgecolor='none', transform=ax.transAxes)
        ax.add_patch(circle)
        ax.text(0.045, y - row_height/2 + 0.005, str(row["idx"]),
                fontsize=8, color=WHITE, ha='center', va='center', fontweight='bold', transform=ax.transAxes)

        # Pattern name and description
        ax.text(0.07, y - 0.005, row["label"],
                fontsize=9, color=DARK_TEXT, fontweight='bold', va='top', transform=ax.transAxes)
        ax.text(0.07, y - 0.02, row["description"],
                fontsize=6, color=MUTED_TEXT, va='top', transform=ax.transAxes, linespacing=1.3)

        cell_y = y - row_height + 0.01
        cell_h = row_height - 0.015

        # Provider count cell
        prov_color = blue_intensity(row["providers"], prov_min, prov_max)
        draw_cell(ax, col_x["providers"], cell_y, col_w["providers"], cell_h, prov_color,
                  f'{row["providers"]:,}', risk_text_color("High") if row["providers"] > prov_max * 0.4 else DARK_TEXT, fontsize=9, bold=True)

        # Exposure cell
        exp_color = blue_intensity(row["exposure"], exp_min, exp_max)
        draw_cell(ax, col_x["exposure"], cell_y, col_w["exposure"], cell_h, exp_color,
                  row["exposure_str"], risk_text_color("High") if row["exposure"] > exp_max * 0.4 else DARK_TEXT, fontsize=9, bold=True)

        # Risk cells
        for risk_key, cx in [("fraud", col_x["fraud"]), ("waste", col_x["waste"]), ("policy", col_x["policy"])]:
            level = row["risk"][risk_key]
            rc = risk_color(level)
            tc = risk_text_color(level)
            draw_cell(ax, cx, cell_y, col_w[risk_key], cell_h, rc, level, tc, fontsize=8, bold=True)

        # Row separator
        sep_y = y - row_height + 0.005
        ax.plot([0.03, 0.97], [sep_y, sep_y], color=LIGHT_BORDER, linewidth=0.3, transform=ax.transAxes)

    # Legend text at bottom
    legend_y = start_y - len(rows) * row_height - 0.02
    ax.text(0.03, legend_y,
            "Reading the heat map: Blue intensity columns are normalized independently — the darkest cell is the highest value in\n"
            "that column. Risk columns range from blue (Highest risk) to pale (Lower risk) to flat based on how strongly (2 ways) Fraud, Waste,\n"
            "or policy/systemic issues. Most patterns are a mix.",
            fontsize=6, color=MUTED_TEXT, va='top', transform=ax.transAxes, linespacing=1.4)

    # Footer
    ax.text(0.03, 0.01, "Source: fraud_patterns.md  ·  All values are statistical risk indicators, not findings of fraud.  ·  8090 Design System.",
            fontsize=6, color=MUTED_TEXT, va='bottom', transform=ax.transAxes)

    os.makedirs(CHARTS_DIR, exist_ok=True)
    path = os.path.join(CHARTS_DIR, "fraud_heatmap_aligned.png")
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=WHITE, pad_inches=0.2)
    plt.close(fig)
    print(f"  Saved: {path}")
    return path


def generate_two_section(rows, profile, findings_data, filename, title):
    """Generate the two-section layout (final and v1 variants)."""
    fig = plt.figure(figsize=(12, 13), facecolor=WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    total_paid = profile.get("total_paid", 0)
    total_rows = profile.get("total_rows", 0)
    total_impact = findings_data.get("summary", {}).get("total_estimated_recoverable", 0)
    systemic_total = findings_data.get("summary", {}).get("systemic_exposure_total", 0)

    # Title
    ax.text(0.03, 0.975, title,
            fontsize=16, fontweight='bold', color=DARK_TEXT, va='top')
    ax.text(0.03, 0.955,
            f"HHS Provider Spending Dataset  ·  {total_rows/1e6:.0f}M+ entries across {total_rows/1e6:.0f}M records  ·  Jan 2018 – Dec 2024",
            fontsize=8, color=MUTED_TEXT, va='top')
    ax.text(0.03, 0.94,
            f"Provider-level exposure: {format_dollars_short(total_impact)}  ·  Systemic exposure: {format_dollars_short(systemic_total)}",
            fontsize=8, color=MUTED_TEXT, va='top')

    # --- Section 1: Pattern Intensity Matrix ---
    sec1_top = 0.915
    ax.text(0.03, sec1_top, "1  PATTERN INTENSITY MATRIX", fontsize=10, fontweight='bold', color=FACTORY_BLUE_DARK, va='top')

    # Column headers for section 1
    hdr_y = sec1_top - 0.025
    s1_cols = {"pattern": 0.03, "flagged": 0.35, "exposure": 0.47, "pct_paid": 0.59, "per_provider": 0.71, "concentration": 0.83}
    s1_widths = {"flagged": 0.10, "exposure": 0.10, "pct_paid": 0.10, "per_provider": 0.10, "concentration": 0.10}
    headers = [("PATTERN", "pattern"), ("FLAGGED\nPROVIDERS", "flagged"), ("ESTIMATED\nEXPOSURE", "exposure"),
               ("% OF TOTAL\nPAID", "pct_paid"), ("PER PROVIDER\nAVG", "per_provider"), ("CONCENTRATION", "concentration")]

    for label, key in headers:
        if key == "pattern":
            ax.text(s1_cols[key], hdr_y, label, fontsize=6.5, color=MUTED_TEXT, fontweight='bold', va='center')
        else:
            ax.text(s1_cols[key] + s1_widths[key]/2, hdr_y, label, fontsize=6.5, color=MUTED_TEXT,
                    fontweight='bold', va='center', ha='center', linespacing=1.2)

    ax.plot([0.03, 0.97], [hdr_y - 0.015, hdr_y - 0.015], color=LIGHT_BORDER, linewidth=0.5)

    # Compute derived metrics
    total_paid_val = profile.get("total_paid", 1)
    for row in rows:
        row["pct_paid"] = (row["exposure"] / total_paid_val * 100) if total_paid_val else 0
        row["per_provider"] = (row["exposure"] / row["providers"]) if row["providers"] > 0 else 0

    all_prov = [r["providers"] for r in rows]
    all_exp = [r["exposure"] for r in rows]
    all_pct = [r["pct_paid"] for r in rows]
    all_per = [r["per_provider"] for r in rows]

    row_h = 0.033
    s1_start = hdr_y - 0.025

    for i, row in enumerate(rows):
        y = s1_start - i * row_h
        # Pattern name
        suffix = "  (system-wide)" if row["key"] == "state_level" else ""
        ax.text(s1_cols["pattern"], y, f'{row["label"]}{suffix}', fontsize=7.5, color=DARK_TEXT, va='center')

        # Heatmap cells
        prov_c = blue_intensity(row["providers"], min(all_prov), max(all_prov))
        exp_c = blue_intensity(row["exposure"], min(all_exp), max(all_exp))
        pct_c = blue_intensity(row["pct_paid"], min(all_pct), max(all_pct))
        per_c = blue_intensity(row["per_provider"], min(all_per), max(all_per))

        # Concentration = simple high/med/low based on provider count relative
        conc_val = row["providers"] / max(all_prov) if max(all_prov) > 0 else 0

        for col_key, val_str, color in [
            ("flagged", f'{row["providers"]:,}', prov_c),
            ("exposure", row["exposure_str"], exp_c),
            ("pct_paid", f'{row["pct_paid"]:.1f}%', pct_c),
            ("per_provider", format_dollars_short(row["per_provider"]), per_c),
            ("concentration", "", blue_intensity(conc_val, 0, 1)),
        ]:
            is_dark = blue_intensity == FACTORY_BLUE_DARK  # check if dark enough for white text
            draw_cell(ax, s1_cols[col_key], y - row_h/2 + 0.003, s1_widths[col_key], row_h - 0.005, color,
                      val_str, DARK_TEXT if row[{
                          "flagged": "providers", "exposure": "exposure", "pct_paid": "pct_paid",
                          "per_provider": "per_provider", "concentration": "providers"
                      }.get(col_key, "providers")] < max(all_prov) * 0.6 else WHITE, fontsize=7.5, bold=True)

        ax.plot([0.03, 0.97], [y - row_h/2 + 0.001, y - row_h/2 + 0.001], color=LIGHT_BORDER, linewidth=0.2)

    # Legend for section 1
    s1_legend_y = s1_start - len(rows) * row_h - 0.01
    ax.text(0.03, s1_legend_y,
            "Reading the heat map: Each column is normalized independently. The darkest cell in each column has the highest value. If a pattern has a provider count\n"
            "high on one metric and low on another — for example, Pattern 5 (Every Day Billing) has only 20 providers but $480M exposure per provider.",
            fontsize=5.5, color=MUTED_TEXT, va='top', linespacing=1.3)

    # --- Section 2: Risk Pattern Assessment ---
    sec2_top = s1_legend_y - 0.035
    ax.text(0.03, sec2_top, "2  RISK PATTERN ASSESSMENT", fontsize=10, fontweight='bold', color=FACTORY_BLUE_DARK, va='top')

    # Legend for risk colors
    leg_y = sec2_top - 0.02
    for i, (label, color) in enumerate([("HIGH RISK/CORRELATION", FACTORY_BLUE_DARK),
                                         ("MODERATE RISK", FACTORY_BLUE_MED),
                                         ("LOW RISK", FACTORY_BLUE_LIGHT),
                                         ("NOT APPLICABLE", GRAY_BG)]):
        lx = 0.03 + i * 0.18
        draw_cell(ax, lx, leg_y - 0.005, 0.015, 0.01, color)
        tc = WHITE if color in (FACTORY_BLUE_DARK, FACTORY_BLUE_MED) else DARK_TEXT
        ax.text(lx + 0.02, leg_y, label, fontsize=6, color=MUTED_TEXT, va='center')

    # Risk table headers
    risk_hdr_y = leg_y - 0.025
    r_cols = {"pattern": 0.03, "fraud": 0.55, "waste": 0.68, "policy": 0.81}
    r_widths = {"fraud": 0.11, "waste": 0.11, "policy": 0.11}

    ax.text(r_cols["pattern"], risk_hdr_y, "PATTERN", fontsize=6.5, color=MUTED_TEXT, fontweight='bold', va='center')
    for key in ("fraud", "waste", "policy"):
        ax.text(r_cols[key] + r_widths[key]/2, risk_hdr_y, key.upper(), fontsize=6.5, color=MUTED_TEXT,
                fontweight='bold', va='center', ha='center')

    ax.plot([0.03, 0.97], [risk_hdr_y - 0.012, risk_hdr_y - 0.012], color=LIGHT_BORDER, linewidth=0.5)

    r_row_h = 0.028
    r_start = risk_hdr_y - 0.022

    for i, row in enumerate(rows):
        y = r_start - i * r_row_h
        ax.text(r_cols["pattern"], y, row["label"], fontsize=7.5, color=DARK_TEXT, va='center')

        for rk in ("fraud", "waste", "policy"):
            level = row["risk"][rk]
            rc = risk_color(level)
            tc = risk_text_color(level)
            draw_cell(ax, r_cols[rk], y - r_row_h/2 + 0.003, r_widths[rk], r_row_h - 0.005, rc, level, tc, fontsize=7.5, bold=True)

        ax.plot([0.03, 0.97], [y - r_row_h/2 + 0.001, y - r_row_h/2 + 0.001], color=LIGHT_BORDER, linewidth=0.2)

    # Assessment note
    note_y = r_start - len(rows) * r_row_h - 0.01
    ax.text(0.03, note_y,
            "Matrix assessment is derived from the qualitative descriptions in the analysis. Each cell rates the category that pattern maps to each risk type. Most\n"
            "patterns are a mix: Home Health scores high on both Fraud and Waste; Government Agencies score almost entirely as policy issues.",
            fontsize=5.5, color=MUTED_TEXT, va='top', linespacing=1.3)

    # Footer
    ax.text(0.03, 0.01, "Source: fraud_patterns.md  ·  All values are statistical risk indicators, not findings of fraud.  ·  8090 Design System.",
            fontsize=6, color=MUTED_TEXT, va='bottom')

    path = os.path.join(CHARTS_DIR, filename)
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=WHITE, pad_inches=0.2)
    plt.close(fig)
    print(f"  Saved: {path}")
    return path


def generate_merged(rows, profile, findings_data):
    """Generate fraud_heatmap_merged.png — combined single table with all data + descriptions."""
    fig = plt.figure(figsize=(12, 12), facecolor=WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    total_paid = profile.get("total_paid", 0)
    total_rows = profile.get("total_rows", 0)
    total_impact = findings_data.get("summary", {}).get("total_estimated_recoverable", 0)
    systemic_total = findings_data.get("summary", {}).get("systemic_exposure_total", 0)

    # Title
    ax.text(0.03, 0.975, "Medicaid Fraud, Waste, and Abuse Pattern Heat Map",
            fontsize=16, fontweight='bold', color=DARK_TEXT, va='top')
    ax.text(0.03, 0.955,
            f"Health and Human Services Provider Spending Dataset  ·  {total_rows/1e6:.0f}M+ entries across {total_rows/1e6:.0f}M records  ·  Jan 2018 – Dec 2024",
            fontsize=8, color=MUTED_TEXT, va='top')
    ax.text(0.03, 0.94,
            f"Provider-level exposure: {format_dollars_short(total_impact)}  ·  Systemic exposure: {format_dollars_short(systemic_total)}",
            fontsize=8, color=MUTED_TEXT, va='top')

    # Scale legend
    ax.text(0.03, 0.925, "SCALE:", fontsize=6, color=MUTED_TEXT, fontweight='bold', va='top')
    for i, c in enumerate([FACTORY_BLUE_BG, FACTORY_BLUE_LIGHT, FACTORY_BLUE_MED, FACTORY_BLUE_DARK]):
        draw_cell(ax, 0.065 + i * 0.025, 0.918, 0.02, 0.012, c)
    ax.text(0.065, 0.913, "Low", fontsize=5, color=MUTED_TEXT, va='top')
    ax.text(0.14, 0.913, "High", fontsize=5, color=MUTED_TEXT, va='top')

    # Column headers
    hdr_y = 0.895
    m_cols = {"pattern": 0.03, "providers": 0.36, "exposure": 0.45, "fraud": 0.57, "waste": 0.66, "policy": 0.75}
    m_widths = {"providers": 0.08, "exposure": 0.10, "fraud": 0.08, "waste": 0.08, "policy": 0.08}

    ax.text(m_cols["pattern"], hdr_y, "PATTERN", fontsize=7, color=MUTED_TEXT, fontweight='bold', va='center')
    for key, label in [("providers", "PROVIDERS"), ("exposure", "EXPOSURE"),
                        ("fraud", "FRAUD"), ("waste", "WASTE"), ("policy", "POLICY")]:
        ax.text(m_cols[key] + m_widths[key]/2, hdr_y, label, fontsize=7, color=MUTED_TEXT,
                fontweight='bold', va='center', ha='center')

    ax.plot([0.03, 0.97], [hdr_y - 0.012, hdr_y - 0.012], color=LIGHT_BORDER, linewidth=0.5)

    all_prov = [r["providers"] for r in rows]
    all_exp = [r["exposure"] for r in rows]
    prov_min, prov_max = min(all_prov), max(all_prov)
    exp_min, exp_max = min(all_exp), max(all_exp)

    row_h = 0.072
    start_y = 0.87

    for i, row in enumerate(rows):
        y = start_y - i * row_h
        cell_y = y - row_h + 0.01
        cell_h = row_h - 0.015

        # Circled number
        circle = mpatches.Circle((0.045, y - row_h/2 + 0.005), 0.012,
                                  facecolor=FACTORY_BLUE_DARK, edgecolor='none', transform=ax.transAxes)
        ax.add_patch(circle)
        ax.text(0.045, y - row_h/2 + 0.005, str(row["idx"]),
                fontsize=8, color=WHITE, ha='center', va='center', fontweight='bold')

        # Pattern name + description
        ax.text(0.07, y - 0.005, row["label"],
                fontsize=9, color=DARK_TEXT, fontweight='bold', va='top')
        ax.text(0.07, y - 0.02, row["description"],
                fontsize=6, color=MUTED_TEXT, va='top', linespacing=1.3)

        # Provider count cell
        prov_c = blue_intensity(row["providers"], prov_min, prov_max)
        draw_cell(ax, m_cols["providers"], cell_y, m_widths["providers"], cell_h, prov_c,
                  f'{row["providers"]:,}', WHITE if row["providers"] > prov_max * 0.4 else DARK_TEXT, fontsize=9, bold=True)

        # Exposure cell
        exp_c = blue_intensity(row["exposure"], exp_min, exp_max)
        draw_cell(ax, m_cols["exposure"], cell_y, m_widths["exposure"], cell_h, exp_c,
                  row["exposure_str"], WHITE if row["exposure"] > exp_max * 0.4 else DARK_TEXT, fontsize=9, bold=True)

        # Risk cells
        for rk, cx in [("fraud", m_cols["fraud"]), ("waste", m_cols["waste"]), ("policy", m_cols["policy"])]:
            level = row["risk"][rk]
            rc = risk_color(level)
            tc = risk_text_color(level)
            draw_cell(ax, cx, cell_y, m_widths[rk], cell_h, rc, level, tc, fontsize=8, bold=True)

        sep_y = y - row_h + 0.005
        ax.plot([0.03, 0.97], [sep_y, sep_y], color=LIGHT_BORDER, linewidth=0.3)

    # Legend
    legend_y = start_y - len(rows) * row_h - 0.02
    ax.text(0.03, legend_y,
            "Reading the heat map: Blue intensity columns are normalized independently — the darkest cell is the highest value in\n"
            "that column. Risk columns range from blue (Highest risk) to pale (Lower risk) to flat based on how strongly (2 ways) Fraud, Waste,\n"
            "or policy/systemic issues. Most patterns are a mix.",
            fontsize=6, color=MUTED_TEXT, va='top', linespacing=1.4)

    # Footer
    ax.text(0.03, 0.01, "Source: fraud_patterns.md  ·  All values are statistical risk indicators, not findings of fraud.  ·  8090 Design System.",
            fontsize=6, color=MUTED_TEXT, va='bottom')

    path = os.path.join(CHARTS_DIR, "fraud_heatmap_merged.png")
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=WHITE, pad_inches=0.2)
    plt.close(fig)
    print(f"  Saved: {path}")
    return path


def main():
    if not os.path.exists(FINDINGS_PATH):
        raise SystemExit(f"Missing findings: {FINDINGS_PATH}")
    if not os.path.exists(PROFILE_PATH):
        raise SystemExit(f"Missing profile: {PROFILE_PATH}")

    print("Loading data...")
    findings_data = load_json(FINDINGS_PATH)
    profile = load_json(PROFILE_PATH)
    findings = findings_data.get("findings", [])

    # Build HCPCS code lookup
    npis = [f["npi"] for f in findings if f.get("npi") and not is_systemic_npi(f.get("npi"))]
    code_lookup = {}
    if npis:
        con = duckdb.connect(DB_PATH, read_only=True)
        rows_db = con.execute("""
            SELECT billing_npi, hcpcs_code
            FROM (
                SELECT billing_npi, hcpcs_code,
                       ROW_NUMBER() OVER (PARTITION BY billing_npi ORDER BY paid DESC) AS rn
                FROM provider_hcpcs
                WHERE billing_npi IN (SELECT UNNEST(?::VARCHAR[]))
            ) t WHERE rn = 1
        """, [npis]).fetchall()
        con.close()
        code_lookup = {r[0]: r[1] for r in rows_db}

    # Classify findings
    p_counts, p_totals, s_counts, s_totals = classify_findings(findings, code_lookup)
    rows = get_combined_counts(p_counts, p_totals, s_counts, s_totals)

    print("Generating heatmaps...")
    paths = []
    paths.append(generate_aligned(rows, profile, findings_data))
    paths.append(generate_two_section(rows, profile, findings_data, "fraud_heatmap_final.png", "Medicaid Fraud, Waste, and Abuse Pattern Heat Map"))
    paths.append(generate_two_section(rows, profile, findings_data, "fraud_heatmap_v1.png", "Medicaid FWA Pattern Heat Map"))
    paths.append(generate_merged(rows, profile, findings_data))

    # Copy to images/ directory
    os.makedirs(IMAGES_DIR, exist_ok=True)
    for p in paths:
        dest = os.path.join(IMAGES_DIR, os.path.basename(p))
        shutil.copy2(p, dest)
        print(f"  Copied: {dest}")

    print(f"\nDone. Generated {len(paths)} heatmaps.")


if __name__ == "__main__":
    main()
