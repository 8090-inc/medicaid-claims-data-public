"""Data profiling and quality metrics."""

import logging

logger = logging.getLogger('medicaid_fwa.preparation')


def profile_table(con, table_name):
    """Generate a data profile for a DuckDB table.

    Args:
        con: DuckDB connection (read-only).
        table_name: Name of the table to profile.

    Returns:
        dict with row count, column stats, etc.
    """
    logger.info(f'Profiling table: {table_name}')
    row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    columns = con.execute(f"DESCRIBE {table_name}").fetchall()
    col_info = []
    for col in columns:
        col_name, col_type = col[0], col[1]
        null_count = con.execute(
            f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL"
        ).fetchone()[0]
        col_info.append({
            'name': col_name,
            'type': col_type,
            'null_count': null_count,
            'null_pct': round(null_count / row_count * 100, 2) if row_count > 0 else 0,
        })

    return {
        'table': table_name,
        'row_count': row_count,
        'column_count': len(columns),
        'columns': col_info,
    }


def assess_data_quality_score(profile):
    """Compute a data quality score from a table profile.

    Args:
        profile: Output from profile_table().

    Returns:
        float quality score between 0.0 and 1.0.
    """
    if profile['row_count'] == 0:
        return 0.0

    total_cells = profile['row_count'] * profile['column_count']
    null_cells = sum(c['null_count'] for c in profile['columns'])
    completeness = 1.0 - (null_cells / total_cells) if total_cells > 0 else 0.0

    return round(completeness, 4)
