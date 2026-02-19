"""Base analyzer class for hypothesis testing."""


class BaseAnalyzer:
    """Base class for all hypothesis analyzers."""

    def execute(self, hypothesis, con):
        """Execute a hypothesis against the DuckDB database.

        Args:
            hypothesis: dict with keys id, category, description, sql_template, parameters, etc.
            con: duckdb.DuckDBPyConnection (read-only)

        Returns:
            list of finding dicts with keys:
                hypothesis_id, flagged_providers, total_impact, confidence, method_name, evidence
        """
        raise NotImplementedError

    def _safe_query(self, con, sql, params=None):
        """Execute a query safely, returning empty list on error."""
        try:
            if params:
                return con.execute(sql, params).fetchall()
            return con.execute(sql).fetchall()
        except Exception as e:
            print(f"    Query error: {e}")
            return []

    def _make_finding(self, hypothesis_id, providers, total_impact, confidence, method_name, evidence=""):
        """Create a standardized finding dict."""
        return {
            'hypothesis_id': hypothesis_id,
            'flagged_providers': providers,
            'total_impact': total_impact,
            'confidence': confidence,
            'method_name': method_name,
            'evidence': evidence,
        }
