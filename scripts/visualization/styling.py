"""Chart styling utilities — HHS OpenData and 8090 design system integration.

Re-exports from scripts/utils/chart_utils.py and adds 8090 design tokens
for use in report generation.
"""

# Re-export HHS chart utilities for convenient access
from scripts.utils.chart_utils import (
    setup_hhs_style,
    add_hhs_border,
    add_hhs_branding,
    get_title_font,
    get_mono_font,
    dollar_formatter,
    create_horizontal_bar_chart,
    create_line_chart,
    create_scatter_chart,
    HHS_AMBER, HHS_DARK, HHS_MUTED, HHS_BG, HHS_PAGE_BG,
    HHS_RED, HHS_GREEN, HHS_GRID, HHS_BORDER,
)

from utils.constants import DESIGN_8090, HHS_COLORS

# 8090 Design System tokens for HTML/report generation
BRAND_BLUE = DESIGN_8090['brand_blue']
BG_CANVAS = DESIGN_8090['bg_canvas']
TEXT_HEADLINE = DESIGN_8090['text_headline']
TEXT_BODY = DESIGN_8090['text_body']
TEXT_SECONDARY = DESIGN_8090['text_secondary']
FONT_SANS = DESIGN_8090['font_sans']
FONT_MONO = DESIGN_8090['font_mono']
