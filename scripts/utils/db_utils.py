"""DuckDB connection and formatting utilities for Medicaid analysis."""

import os
import sys
import duckdb

# Import centralized config (with fallback for standalone execution)
try:
    _project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)
    from config.project_config import DB_PATH, DB_WRITE_THREADS, DB_WRITE_MEMORY_LIMIT
except ImportError:
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'medicaid.duckdb')
    DB_WRITE_THREADS = 16
    DB_WRITE_MEMORY_LIMIT = '96GB'


def get_connection(read_only=True):
    """Returns a DuckDB connection to medicaid.duckdb with appropriate settings."""
    con = duckdb.connect(DB_PATH, read_only=read_only)
    if not read_only:
        con.execute(f"SET threads TO {DB_WRITE_THREADS}")
        con.execute(f"SET memory_limit = '{DB_WRITE_MEMORY_LIMIT}'")
    return con


def format_dollars(amount):
    """Formats dollar amounts as $X.XB, $X.XM, $X.XK."""
    if amount is None:
        return "$0"
    neg = amount < 0
    amount = abs(amount)
    if amount >= 1e9:
        s = f"${amount / 1e9:.1f}B"
    elif amount >= 1e6:
        s = f"${amount / 1e6:.1f}M"
    elif amount >= 1e3:
        s = f"${amount / 1e3:.1f}K"
    else:
        s = f"${amount:,.0f}"
    return f"-{s}" if neg else s
