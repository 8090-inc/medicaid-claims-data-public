"""Tests for database setup and schema validation."""

import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class TestDatabaseSetup:
    """Unit tests for scripts/utils/database_setup.py."""

    def test_create_schema(self):
        import duckdb
        from scripts.utils.database_setup import create_schema, validate_schema
        con = duckdb.connect(':memory:')
        create_schema(con)
        ok, missing = validate_schema(con)
        assert ok
        assert len(missing) == 0
        con.close()

    def test_validate_schema_missing(self):
        import duckdb
        from scripts.utils.database_setup import validate_schema
        con = duckdb.connect(':memory:')
        ok, missing = validate_schema(con)
        assert not ok
        assert len(missing) == 6
        con.close()

    def test_get_table_row_counts(self):
        import duckdb
        from scripts.utils.database_setup import create_schema, get_table_row_counts
        con = duckdb.connect(':memory:')
        create_schema(con)
        counts = get_table_row_counts(con)
        assert counts['claims'] == 0
        assert counts['provider_summary'] == 0
        con.close()

    def test_health_check_missing_db(self, temp_dir):
        from scripts.utils.database_setup import health_check
        result = health_check(os.path.join(temp_dir, 'nonexistent.duckdb'))
        assert not result['exists']


class TestDbUtils:
    """Tests for scripts/utils/db_utils.py."""

    def test_format_dollars_billions(self):
        from scripts.utils.db_utils import format_dollars
        assert format_dollars(1_500_000_000) == '$1.5B'

    def test_format_dollars_millions(self):
        from scripts.utils.db_utils import format_dollars
        assert format_dollars(2_300_000) == '$2.3M'

    def test_format_dollars_thousands(self):
        from scripts.utils.db_utils import format_dollars
        assert format_dollars(45_000) == '$45.0K'

    def test_format_dollars_small(self):
        from scripts.utils.db_utils import format_dollars
        assert format_dollars(500) == '$500'

    def test_format_dollars_none(self):
        from scripts.utils.db_utils import format_dollars
        assert format_dollars(None) == '$0'

    def test_format_dollars_negative(self):
        from scripts.utils.db_utils import format_dollars
        assert format_dollars(-1_000_000) == '-$1.0M'
