#!/usr/bin/env python3
"""Generate HHS-style card images for the current fraud/abuse analysis."""

import csv
import os
from datetime import datetime
from textwrap import shorten, wrap

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Design-spec constants (chart-design-spec.json)
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


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "medicaid.duckdb")
OUTPUT_DIR = PROJECT_ROOT
ANALYSIS_DIR = os.path.join(PROJECT_ROOT, "output", "analysis")
RISK_QUEUE = os.path.join(ANALYSIS_DIR, "risk_queue_top500.csv")

CARD1 = os.path.join(OUTPUT_DIR, "card1-full-monthly-spending.png")
CARD2 = os.path.join(OUTPUT_DIR, "card2-full-top-procedures.png")
CARD3 = os.path.join(OUTPUT_DIR, "card3-full-top-providers.png")

CARD1_SIZE = (833, 547)
CARD23_SIZE = (833, 969)
CARD_DPI = 150
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
FOOTNOTE_PAD_PX = 14
LABEL_SPACE_PX = 120


def _figsize(px_size):
    return (px_size[0] / CARD_DPI, px_size[1] / CARD_DPI)


def _billions_formatter(x, _):
    return f"${x/1e9:.1f}B" if x >= 0 else f"-${abs(x)/1e9:.1f}B"


def _fy_formatter(x, _):
    dt = mdates.num2date(x)
    fy = dt.year + 1 if dt.month >= 10 else dt.year
    return f"FY{str(fy)[-2:]}"


def _setup_fonts():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": FONT_STACK,
        "axes.titlesize": 18,
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
    fig.text(right, link_y, "↓ Image  ·  ↓ Data",
             fontsize=12, color=TEXT_LINK, ha="right", va="top")
    fig.text(left, title_y, title, fontsize=TITLE_FONT_PX, color=TEXT_DARK,
             ha="left", va="top", fontweight="700")
    fig.text(left, subtitle_y, subtitle, fontsize=SUBTITLE_FONT_PX, color=TEXT_MED,
             ha="left", va="top")


def _add_branding(fig, width_px, height_px):
    _, right, _, bottom = _layout(width_px, height_px)
    fig.text(right, bottom, "HHS // OPENDATA", fontsize=11, color=BRAND,
             ha="right", va="bottom", fontweight="bold")


def _add_footer(fig, text_left, width_px, height_px):
    left, _, _, bottom = _layout(width_px, height_px)
    if text_left:
        fig.text(left, bottom, text_left, fontsize=11, color=TEXT_LIGHT, va="bottom")
    _add_branding(fig, width_px, height_px)


def _style_axes_line(ax):
    ax.set_facecolor("#FFFFFF")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(AXIS_LINE)
    ax.tick_params(axis="y", length=0, colors=TEXT_LIGHT)
    ax.tick_params(axis="x", colors=TEXT_LIGHT)
    ax.grid(axis="y", color=GRID, linestyle="-", linewidth=1.0)
    ax.grid(axis="x", visible=False)
    ax.set_axisbelow(True)


def _style_axes_bar(ax):
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


def _truncate_label(text, width=30):
    return shorten(text, width=width, placeholder="...")


def _wrap_label(text, width=18, max_lines=2):
    lines = wrap(text, width=width)
    if len(lines) <= max_lines:
        return "\n".join(lines)
    kept = lines[:max_lines]
    kept[-1] = shorten(kept[-1], width=width, placeholder="...")
    return "\n".join(kept)


def _ellipsis_label(text, width=28):
    return shorten(text, width=width, placeholder="...")


def _load_top_providers(limit=500):
    rows = []
    with open(RISK_QUEUE, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            if len(rows) >= limit:
                break
    return rows


def _query_monthly_spend(con, npis):
    con.execute("CREATE TEMP TABLE top_providers (npi VARCHAR)")
    con.executemany("INSERT INTO top_providers VALUES (?)", [(n,) for n in npis])
    rows = con.execute("""
        SELECT claim_month, SUM(paid) AS total_paid
        FROM claims c
        INNER JOIN top_providers t ON c.billing_npi = t.npi
        GROUP BY claim_month
        ORDER BY claim_month
    """).fetchall()
    return rows


def _query_top_codes(con):
    rows = con.execute(f"""
        WITH top_providers AS (
            SELECT DISTINCT npi FROM read_csv_auto('{RISK_QUEUE}')
        ),
        code_totals AS (
            SELECT
                ph.hcpcs_code,
                SUM(ph.paid) AS total_paid
            FROM provider_hcpcs ph
            INNER JOIN top_providers tp ON ph.billing_npi = tp.npi
            GROUP BY ph.hcpcs_code
        )
        SELECT ct.hcpcs_code,
               COALESCE(h.short_desc, ct.hcpcs_code) AS short_desc,
               ct.total_paid
        FROM code_totals ct
        LEFT JOIN hcpcs_codes h ON ct.hcpcs_code = h.hcpcs_code
        ORDER BY ct.total_paid DESC
        LIMIT 20
    """).fetchall()
    return rows


def generate_card1(top_rows):
    _setup_fonts()
    width_px, height_px = CARD1_SIZE
    dates = [datetime.strptime(r[0], "%Y-%m") for r in top_rows]
    values = [r[1] for r in top_rows]

    fig = plt.figure(figsize=_figsize(CARD1_SIZE), dpi=CARD_DPI, facecolor="#FFFFFF")
    _add_header(fig,
                "Monthly Spending Trend",
                "Total payments by month for top flagged providers, 2018–2024",
                width_px, height_px)

    left, right, top, bottom = _layout(width_px, height_px)
    ax_left = left
    ax_right = right
    ax_top = top - HEADER_BLOCK_PX / height_px
    ax_bottom = bottom + FOOTNOTE_PAD_PX / height_px
    ax = fig.add_axes([ax_left, ax_bottom, ax_right - ax_left, ax_top - ax_bottom])
    _style_axes_line(ax)
    ax.yaxis.set_major_formatter(_billions_formatter)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(5))
    ax.set_ylim(bottom=0)

    ax.plot(dates, values, color=PRIMARY, linewidth=2, zorder=3)

    min_idx = min(range(len(values)), key=values.__getitem__)
    # Reference line at FY20/FY21 boundary (Oct 2020)
    ax.axvline(datetime(2020, 10, 1), color="#999999", linewidth=1.0, zorder=1)
    ax.scatter([dates[min_idx]], [values[min_idx]], color=PRIMARY, s=14, zorder=4)

    ax.annotate(
        f"{dates[min_idx].strftime('%b %y')}\n${values[min_idx]:,.0f}",
        xy=(dates[min_idx], values[min_idx]),
        xytext=(0.02, 0.78),
        textcoords="axes fraction",
        fontsize=11,
        color="#FFFFFF",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#333333", edgecolor="none"),
    )

    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=10))
    ax.xaxis.set_major_formatter(_fy_formatter)
    ax.set_xlim(min(dates), max(dates))

    _add_footer(fig, "Federal fiscal years run October – September.", width_px, height_px)
    fig.patch.set_edgecolor(BORDER)
    fig.patch.set_linewidth(1.0)
    fig.savefig(CARD1, facecolor=fig.get_facecolor(), edgecolor=fig.get_edgecolor())
    plt.close(fig)


def generate_card2(top_codes):
    _setup_fonts()
    width_px, height_px = CARD23_SIZE
    labels = [_wrap_label(r[1], width=20) for r in top_codes][::-1]
    values = [r[2] for r in top_codes][::-1]

    fig = plt.figure(figsize=_figsize(CARD23_SIZE), dpi=CARD_DPI, facecolor="#FFFFFF")
    _add_header(fig,
                "Highest-cost HCPCS procedure codes (flagged providers)",
                "Top 20 by total paid, 2018–2024",
                width_px, height_px)
    left, right, top, bottom = _layout(width_px, height_px)
    ax_left = left + LABEL_SPACE_PX / width_px
    ax_right = right
    ax_top = top - HEADER_BLOCK_PX / height_px
    ax_bottom = bottom + 8 / height_px
    ax = fig.add_axes([ax_left, ax_bottom, ax_right - ax_left, ax_top - ax_bottom])
    _style_axes_bar(ax)

    ax.barh(range(len(values)), values, color=PRIMARY, edgecolor="none", height=0.7)
    ax.set_yticks(range(len(values)))
    ax.set_yticklabels(labels, fontsize=11, color="#444444")
    ax.tick_params(axis="y", pad=6)
    ax.xaxis.set_major_formatter(_billions_formatter)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(4))
    ax.set_xlim(left=0)
    ax.invert_yaxis()

    for label in ax.get_yticklabels():
        label.set_ha("right")
    _add_footer(fig, "", width_px, height_px)
    fig.patch.set_edgecolor(BORDER)
    fig.patch.set_linewidth(1.0)
    fig.savefig(CARD2, facecolor=fig.get_facecolor(), edgecolor=fig.get_edgecolor())
    plt.close(fig)


def generate_card3(top_providers):
    _setup_fonts()
    width_px, height_px = CARD23_SIZE
    top20 = top_providers[:20][::-1]
    labels = [_ellipsis_label(r["name"], width=28) for r in top20]
    values = [float(r["weighted_impact"]) for r in top20]

    fig = plt.figure(figsize=_figsize(CARD23_SIZE), dpi=CARD_DPI, facecolor="#FFFFFF")
    _add_header(fig,
                "Top 20 providers by weighted impact (flagged)",
                "Quality-weighted impact, 2018–2024",
                width_px, height_px)
    left, right, top, bottom = _layout(width_px, height_px)
    ax_left = left + LABEL_SPACE_PX / width_px
    ax_right = right
    ax_top = top - HEADER_BLOCK_PX / height_px
    ax_bottom = bottom + 8 / height_px
    ax = fig.add_axes([ax_left, ax_bottom, ax_right - ax_left, ax_top - ax_bottom])
    _style_axes_bar(ax)

    ax.barh(range(len(values)), values, color=PRIMARY, edgecolor="none", height=0.7)
    ax.set_yticks(range(len(values)))
    ax.set_yticklabels(labels, fontsize=11, color="#444444")
    ax.tick_params(axis="y", pad=6)
    ax.xaxis.set_major_formatter(_billions_formatter)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(4))
    ax.set_xlim(left=0)
    ax.invert_yaxis()

    for label in ax.get_yticklabels():
        label.set_ha("right")
    _add_footer(fig, "", width_px, height_px)
    fig.patch.set_edgecolor(BORDER)
    fig.patch.set_linewidth(1.0)
    fig.savefig(CARD3, facecolor=fig.get_facecolor(), edgecolor=fig.get_edgecolor())
    plt.close(fig)


def main():
    if not os.path.exists(RISK_QUEUE):
        raise SystemExit(f"Missing risk queue: {RISK_QUEUE}")

    top_providers = _load_top_providers(500)
    npis = [r["npi"] for r in top_providers if r.get("npi")]

    con = duckdb.connect(DB_PATH, read_only=True)
    monthly = _query_monthly_spend(con, npis)
    codes = _query_top_codes(con)
    con.close()

    generate_card1(monthly)
    generate_card2(codes)
    generate_card3(top_providers)

    print(f"Wrote {CARD1}")
    print(f"Wrote {CARD2}")
    print(f"Wrote {CARD3}")


if __name__ == "__main__":
    main()
