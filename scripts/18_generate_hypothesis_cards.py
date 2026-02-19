#!/usr/bin/env python3
"""Generate a card for every hypothesis using design spec styling."""

import csv
import json
import os
import re
from datetime import datetime
from textwrap import shorten, wrap

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "medicaid.duckdb")
FINDINGS_DIR = os.path.join(PROJECT_ROOT, "output", "findings")
HYPOTHESES_PATH = os.path.join(PROJECT_ROOT, "output", "hypotheses", "all_hypotheses_testable.json")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "cards", "hypotheses")
INDEX_PATH = os.path.join(PROJECT_ROOT, "output", "cards", "hypothesis_cards_index.csv")

CARD_SIZE = (833, 969)
CARD_DPI = 150

# Design-spec constants
PRIMARY = "#E8A317"
GRID = "#E8E8E8"
AXIS_LINE = "#CCCCCC"
TEXT_DARK = "#1A1A1A"
TEXT_MED = "#555555"
TEXT_LIGHT = "#888888"
TEXT_LINK = "#666666"
BORDER = "#E0E0E0"
BRAND = "#333333"
FONT_STACK = ["DejaVu Sans", "Arial", "Helvetica Neue", "sans-serif"]
PAD_LEFT_PX = 16
PAD_RIGHT_PX = 32
PAD_TOP_PX = 24
PAD_BOTTOM_PX = 20
TITLE_FONT_PX = 18
SUBTITLE_FONT_PX = 13
TITLE_LINE_HEIGHT = 1.3
SUBTITLE_LINE_HEIGHT = 1.4
TITLE_MARGIN_PX = 4
SUBTITLE_MARGIN_PX = 20
HEADER_BLOCK_PX = int(round(
    TITLE_FONT_PX * TITLE_LINE_HEIGHT
    + TITLE_MARGIN_PX
    + SUBTITLE_FONT_PX * SUBTITLE_LINE_HEIGHT
    + SUBTITLE_MARGIN_PX
))
LABEL_SPACE_PX = 120


def _figsize(px_size):
    return (px_size[0] / CARD_DPI, px_size[1] / CARD_DPI)


def _setup_fonts():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": FONT_STACK,
        "axes.titlesize": TITLE_FONT_PX,
        "axes.titleweight": 700,
        "axes.labelsize": 12,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "figure.dpi": CARD_DPI,
        "savefig.dpi": CARD_DPI,
    })


def _layout(width_px, height_px):
    left = PAD_LEFT_PX / width_px
    right = 1 - PAD_RIGHT_PX / width_px
    top = 1 - PAD_TOP_PX / height_px
    bottom = PAD_BOTTOM_PX / height_px
    return left, right, top, bottom


def _add_header(fig, title, subtitle, width_px, height_px):
    left, right, top, _ = _layout(width_px, height_px)
    title_y = top
    subtitle_y = top - (TITLE_FONT_PX * TITLE_LINE_HEIGHT + TITLE_MARGIN_PX) / height_px
    link_y = top + 2 / height_px
    fig.text(right, link_y, "↓ Image  ·  ↓ Data", fontsize=12, color=TEXT_LINK, ha="right", va="top")
    fig.text(left, title_y, title, fontsize=TITLE_FONT_PX, color=TEXT_DARK, ha="left",
             va="top", fontweight="700")
    fig.text(left, subtitle_y, subtitle, fontsize=SUBTITLE_FONT_PX, color=TEXT_MED,
             ha="left", va="top")


def _add_footer(fig, width_px, height_px):
    _, right, _, bottom = _layout(width_px, height_px)
    fig.text(right, bottom, "HHS // OPENDATA", fontsize=11, color=BRAND,
             ha="right", va="bottom", fontweight="bold")


def _style_axes(ax):
    ax.set_facecolor("#FFFFFF")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(AXIS_LINE)
    ax.tick_params(axis="y", length=0, colors=TEXT_LIGHT)
    ax.tick_params(axis="x", colors=TEXT_LIGHT)
    ax.grid(axis="x", color=GRID, linestyle="-", linewidth=1.0)
    ax.grid(axis="y", visible=False)
    ax.set_axisbelow(True)


def _billions_formatter(x, _):
    return f"${x/1e9:.1f}B" if x >= 0 else f"-${abs(x)/1e9:.1f}B"


def _wrap_label(text, width=18, max_lines=2):
    lines = wrap(text, width=width)
    if len(lines) <= max_lines:
        return "\n".join(lines)
    kept = lines[:max_lines]
    kept[-1] = shorten(kept[-1], width=width, placeholder="...")
    return "\n".join(kept)


def _plain_language(text, code=None, code_desc=None):
    if not text:
        return "Outlier pattern flagged"
    out = re.sub(r"^Providers with ", "", text, flags=re.IGNORECASE)
    repl = {
        "z-score": "far above peers",
        "z score": "far above peers",
        "zscore": "far above peers",
        "GEV": "rare extreme",
        "IQR": "outside typical range",
        "yoy": "year-over-year",
        "YoY": "year-over-year",
        "HCPCS": "procedure code",
        "paid_per_claim": "paid per claim",
        "paid_per_bene": "paid per beneficiary",
        "claims_per_bene": "claims per beneficiary",
        "GEV extreme value analysis": "rare extreme outlier check",
        "peer_rate": "rate above peers",
        "peer_volume": "volume above peers",
        "change_point": "sudden shift",
        "ghost_network": "likely shell network",
        "duplicate": "duplicate billing",
        "circular_billing": "billing loop",
    }
    for k, v in repl.items():
        out = out.replace(k, v)
    out = re.sub(r"z-?score\s*[>≥]\s*[\d\.]+", "far above peers", out, flags=re.IGNORECASE)
    out = re.sub(r"paid-per-claim", "paid per claim", out, flags=re.IGNORECASE)
    out = re.sub(r"paid-per-bene", "paid per beneficiary", out, flags=re.IGNORECASE)
    out = re.sub(r"claims-per-bene", "claims per beneficiary", out, flags=re.IGNORECASE)
    if code and code_desc:
        short_desc = shorten(code_desc, width=32, placeholder="...")
        out = out.replace(code, f"{code} ({short_desc})")
    out = re.sub(r"\s+", " ", out).strip()
    return out


def _load_hypotheses():
    with open(HYPOTHESES_PATH, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)


def _build_hyp_provider_table(con):
    con.execute("CREATE TEMP TABLE hyp_provider (hypothesis_id VARCHAR, npi VARCHAR, amount DOUBLE)")
    files = [
        "categories_1_to_5.json",
        "categories_6_and_7.json",
        "category_8.json",
        "categories_9_and_10.json",
    ]
    for fname in files:
        path = os.path.join(FINDINGS_DIR, fname)
        if not os.path.exists(path):
            continue
        col_type = con.execute(
            f"DESCRIBE SELECT flagged_providers FROM read_json_auto('{path}')"
        ).fetchone()[1]
        if "STRUCT" in col_type:
            con.execute(f"""
                INSERT INTO hyp_provider
                SELECT
                    hypothesis_id,
                    fp.npi AS npi,
                    COALESCE(fp.amount, 0) AS amount
                FROM read_json_auto('{path}'), UNNEST(flagged_providers) AS t(fp)
                WHERE fp.npi IS NOT NULL AND fp.npi != ''
            """)
        else:
            con.execute(f"""
                INSERT INTO hyp_provider
                SELECT
                    hypothesis_id,
                    CAST(fp AS VARCHAR) AS npi,
                    total_impact AS amount
                FROM read_json_auto('{path}'), UNNEST(flagged_providers) AS t(fp)
                WHERE fp IS NOT NULL AND fp != ''
            """)
    con.execute("""
        CREATE TEMP TABLE hyp_provider_agg AS
        SELECT hypothesis_id, npi, SUM(amount) AS amount
        FROM hyp_provider
        GROUP BY hypothesis_id, npi
    """)


def _load_code_lookup(con):
    rows = con.execute("""
        SELECT hcpcs_code, short_desc
        FROM hcpcs_codes
        WHERE hcpcs_code IS NOT NULL AND short_desc IS NOT NULL
    """).fetchall()
    return {code: desc for code, desc in rows if code and desc}


def _fetch_top(con, hyp_id):
    rows = con.execute("""
        SELECT
            hpa.npi,
            COALESCE(p.name, hpa.npi) AS name,
            COALESCE(p.state, '') AS state,
            hpa.amount
        FROM hyp_provider_agg hpa
        LEFT JOIN providers p ON hpa.npi = p.npi
        WHERE hpa.hypothesis_id = ?
        ORDER BY hpa.amount DESC
        LIMIT 20
    """, [hyp_id]).fetchall()
    stats = con.execute("""
        SELECT COUNT(DISTINCT npi) AS providers, COALESCE(SUM(amount), 0) AS total
        FROM hyp_provider_agg
        WHERE hypothesis_id = ?
    """, [hyp_id]).fetchone()
    return rows, stats


def _render_card(title, subtitle, rows, output_path, width_px, height_px):
    _setup_fonts()
    fig = plt.figure(figsize=_figsize(CARD_SIZE), dpi=CARD_DPI, facecolor="#FFFFFF")
    _add_header(fig, title, subtitle, width_px, height_px)

    left, right, top, bottom = _layout(width_px, height_px)
    ax_left = left + LABEL_SPACE_PX / width_px
    ax_right = right
    ax_top = top - HEADER_BLOCK_PX / height_px
    ax_bottom = bottom + 8 / height_px
    ax = fig.add_axes([ax_left, ax_bottom, ax_right - ax_left, ax_top - ax_bottom])
    _style_axes(ax)
    ax.xaxis.set_major_formatter(_billions_formatter)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(4))
    ax.set_xlim(left=0)

    if rows:
        labels = [shorten(r[1], width=28, placeholder="...") for r in rows][::-1]
        values = [r[3] for r in rows][::-1]
        ax.barh(range(len(values)), values, color=PRIMARY, edgecolor="none", height=0.7)
        ax.set_yticks(range(len(values)))
        ax.set_yticklabels(labels, fontsize=11, color="#444444")
        ax.tick_params(axis="y", pad=6)
        ax.invert_yaxis()
    else:
        ax.text(0.5, 0.5, "No findings in current data",
                ha="center", va="center", fontsize=12, color=TEXT_LIGHT, transform=ax.transAxes)
        ax.set_yticks([])
        ax.set_xticks([])

    _add_footer(fig, width_px, height_px)
    fig.patch.set_edgecolor(BORDER)
    fig.patch.set_linewidth(1.0)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor=fig.get_edgecolor())
    plt.close(fig)


def main():
    if not os.path.exists(HYPOTHESES_PATH):
        raise SystemExit(f"Missing hypotheses: {HYPOTHESES_PATH}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)

    hypotheses = _load_hypotheses()
    con = duckdb.connect(DB_PATH, read_only=True)
    _build_hyp_provider_table(con)
    code_lookup = _load_code_lookup(con)
    width_px, height_px = CARD_SIZE

    with open(INDEX_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hypothesis_id", "title", "subtitle", "card_path", "providers", "total_impact"])
        for hyp in hypotheses:
            hyp_id = hyp.get("id")
            if not hyp_id:
                continue
            params = hyp.get("parameters") or {}
            code = params.get("hcpcs_code")
            code_desc = code_lookup.get(code) if code else None
            desc = _plain_language(hyp.get("description", ""), code=code, code_desc=code_desc)
            title = shorten(f"{hyp_id} — {desc}", width=90, placeholder="...")
            rows, stats = _fetch_top(con, hyp_id)
            providers = stats[0] if stats else 0
            total = stats[1] if stats else 0
            subtitle = f"Top 20 flagged providers · {providers} total · ${total:,.0f} estimated exposure"
            subtitle = shorten(subtitle, width=110, placeholder="...")
            output_path = os.path.join(OUTPUT_DIR, f"{hyp_id}.png")
            _render_card(title, subtitle, rows, output_path, width_px, height_px)
            writer.writerow([hyp_id, title, subtitle, output_path, providers, total])

    con.close()
    print(f"Wrote {INDEX_PATH}")


if __name__ == "__main__":
    main()
