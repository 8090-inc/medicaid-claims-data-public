"""DuckDB connection and formatting utilities for Medicaid analysis."""

import os
import duckdb

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'medicaid.duckdb')


def get_connection(read_only=True):
    """Returns a DuckDB connection to medicaid.duckdb with appropriate settings."""
    con = duckdb.connect(DB_PATH, read_only=read_only)
    if not read_only:
        con.execute("SET threads TO 16")
        con.execute("SET memory_limit = '96GB'")
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
