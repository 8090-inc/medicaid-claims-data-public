"""HHS OpenData chart design system for Medicaid analysis."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import os

# HHS OpenData design constants
HHS_AMBER = '#F59F0A'
HHS_DARK = '#221E1C'
HHS_MUTED = '#78716D'
HHS_BG = '#FFFFFF'
HHS_PAGE_BG = '#F8F7F2'
HHS_RED = '#B91C1C'
HHS_GREEN = '#15803D'
HHS_GRID = '#E5E2DC'
HHS_BORDER = '#221E1C'

# Font fallbacks
TITLE_FONT = 'Inter'
MONO_FONT = 'JetBrains Mono'
FALLBACK_FONTS = ['Helvetica Neue', 'Arial', 'sans-serif']
MONO_FALLBACKS = ['Consolas', 'Courier New', 'monospace']


def _get_font(preferred, fallbacks):
    """Return the first available font from the list."""
    import matplotlib.font_manager as fm
    available = {f.name for f in fm.fontManager.ttflist}
    if preferred in available:
        return preferred
    for f in fallbacks:
        if f in available:
            return f
    return fallbacks[-1]


def get_title_font():
    return _get_font(TITLE_FONT, FALLBACK_FONTS)


def get_mono_font():
    return _get_font(MONO_FONT, MONO_FALLBACKS)


def setup_hhs_style():
    """Configures matplotlib rcParams to match HHS OpenData design."""
    title_font = get_title_font()
    plt.rcParams.update({
        'figure.facecolor': HHS_BG,
        'axes.facecolor': HHS_BG,
        'axes.edgecolor': HHS_DARK,
        'axes.labelcolor': HHS_MUTED,
        'axes.labelsize': 11,
        'axes.titlesize': 14,
        'axes.titleweight': 600,
        'axes.grid': True,
        'grid.color': HHS_GRID,
        'grid.linestyle': '--',
        'grid.linewidth': 0.5,
        'xtick.color': HHS_MUTED,
        'ytick.color': HHS_MUTED,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'text.color': HHS_DARK,
        'font.family': 'sans-serif',
        'font.sans-serif': [title_font] + FALLBACK_FONTS,
        'figure.dpi': 150,
        'savefig.dpi': 150,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.3,
    })


def add_hhs_border(fig):
    """Add 2px solid dark border around the figure (card style)."""
    fig.patch.set_edgecolor(HHS_BORDER)
    fig.patch.set_linewidth(2)


def add_hhs_branding(fig):
    """Adds 'HHS // OPENDATA' branding to bottom-right of figure."""
    mono = get_mono_font()
    fig.text(0.97, 0.02, 'HHS // OPENDATA', fontsize=9, fontfamily=mono,
             color=HHS_MUTED, ha='right', va='bottom', alpha=0.7)


def _dollar_formatter(x, pos):
    """Axis tick formatter for dollar amounts."""
    if abs(x) >= 1e9:
        return f'${x/1e9:.1f}B'
    elif abs(x) >= 1e6:
        return f'${x/1e6:.0f}M'
    elif abs(x) >= 1e3:
        return f'${x/1e3:.0f}K'
    else:
        return f'${x:,.0f}'


def dollar_formatter():
    return mticker.FuncFormatter(_dollar_formatter)


def create_horizontal_bar_chart(data, labels, title, subtitle, output_path,
                                 color=HHS_AMBER, figsize=(10, 8), value_labels=True):
    """Creates an HHS-styled horizontal bar chart and saves as PNG."""
    setup_hhs_style()
    mono = get_mono_font()

    fig, ax = plt.subplots(figsize=figsize)

    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, data, color=color, height=0.6, edgecolor='none')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(dollar_formatter())
    ax.set_axisbelow(True)
    ax.grid(axis='x', linestyle='--', linewidth=0.5, color=HHS_GRID)
    ax.grid(axis='y', visible=False)

    ax.set_title(title, fontsize=14, fontweight=600, color=HHS_DARK, loc='left', pad=20)
    fig.text(0.125, 0.92, subtitle, fontsize=11, fontfamily=mono, color=HHS_MUTED)

    if value_labels:
        for bar, val in zip(bars, data):
            ax.text(bar.get_width() + max(data) * 0.01, bar.get_y() + bar.get_height() / 2,
                    _dollar_formatter(val, None), va='center', fontsize=9, color=HHS_MUTED)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(left=False)

    add_hhs_border(fig)
    add_hhs_branding(fig)
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor=fig.get_edgecolor())
    plt.close(fig)
    print(f"  Chart saved: {output_path}")


def create_line_chart(x, y, title, subtitle, output_path, color=HHS_AMBER,
                      figsize=(12, 5), ylabel='', markers=None, marker_color=HHS_RED,
                      reference_line=None, ref_label=None):
    """Creates an HHS-styled line chart and saves as PNG."""
    setup_hhs_style()
    mono = get_mono_font()

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(x, y, color=color, linewidth=2, zorder=5)

    if markers is not None:
        mx = [x[i] for i in markers]
        my = [y[i] for i in markers]
        ax.scatter(mx, my, color=marker_color, s=60, zorder=6, edgecolors='white', linewidth=1)

    if reference_line is not None:
        ax.plot(x, reference_line, color=HHS_MUTED, linewidth=1, linestyle='--',
                label=ref_label or 'Reference', zorder=4)
        ax.legend(fontsize=9, frameon=False)

    ax.yaxis.set_major_formatter(dollar_formatter())
    ax.set_ylim(bottom=0)
    ax.set_axisbelow(True)
    ax.grid(axis='y', linestyle='--', linewidth=0.5, color=HHS_GRID)
    ax.grid(axis='x', visible=False)

    if ylabel:
        ax.set_ylabel(ylabel, fontsize=11, color=HHS_MUTED)

    ax.set_title(title, fontsize=14, fontweight=600, color=HHS_DARK, loc='left', pad=20)
    fig.text(0.125, 0.92, subtitle, fontsize=11, fontfamily=mono, color=HHS_MUTED)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Thin x-axis labels for readability
    if len(x) > 20:
        step = max(1, len(x) // 7)  # aim for ~7 labels
        tick_indices = list(range(0, len(x), step))
        ax.set_xticks(tick_indices)
        tick_labels = []
        for i in tick_indices:
            lbl = str(x[i])
            # Simplify YYYY-MM or YYYY-MM-DD to just YYYY for yearly+ intervals
            if step >= 10 and len(lbl) >= 7:
                tick_labels.append(lbl[:4])
            else:
                tick_labels.append(lbl)
        ax.set_xticklabels(tick_labels, rotation=0, ha='center')

    add_hhs_border(fig)
    add_hhs_branding(fig)
    plt.tight_layout(rect=[0, 0, 1, 0.88])
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor=fig.get_edgecolor())
    plt.close(fig)
    print(f"  Chart saved: {output_path}")


def create_scatter_chart(x, y, title, subtitle, output_path, colors=None,
                         figsize=(10, 7), xlabel='', ylabel='', log_x=False):
    """Creates an HHS-styled scatter plot."""
    setup_hhs_style()
    mono = get_mono_font()

    fig, ax = plt.subplots(figsize=figsize)

    if colors is None:
        colors = [HHS_AMBER] * len(x)

    ax.scatter(x, y, c=colors, s=30, alpha=0.7, edgecolors='white', linewidth=0.5, zorder=5)

    if log_x:
        ax.set_xscale('log')
    ax.xaxis.set_major_formatter(dollar_formatter())

    ax.set_xlabel(xlabel, fontsize=11, color=HHS_MUTED)
    ax.set_ylabel(ylabel, fontsize=11, color=HHS_MUTED)

    ax.set_title(title, fontsize=14, fontweight=600, color=HHS_DARK, loc='left', pad=20)
    fig.text(0.125, 0.92, subtitle, fontsize=11, fontfamily=mono, color=HHS_MUTED)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_axisbelow(True)

    add_hhs_border(fig)
    add_hhs_branding(fig)
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor=fig.get_edgecolor())
    plt.close(fig)
    print(f"  Chart saved: {output_path}")
