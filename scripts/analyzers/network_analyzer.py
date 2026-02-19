#!/usr/bin/env python3
"""Category 4: Network / Relationship Analysis.

Implements subcategories 4A-4G for detecting suspicious network structures
and relationships between billing and servicing providers.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analyzers.base_analyzer import BaseAnalyzer


class NetworkAnalyzer(BaseAnalyzer):
    """Detects suspicious network patterns in billing-servicing relationships."""

    def __init__(self):
        super().__init__()
        self._graph = None
        self._graph_loaded = False

    def execute(self, hypothesis, con):
        """Route to the appropriate subcategory method.

        Args:
            hypothesis: dict with keys including 'id', 'subcategory', 'parameters', etc.
            con: duckdb.DuckDBPyConnection (read-only)

        Returns:
            list of finding dicts
        """
        subcategory = hypothesis.get('subcategory', '')
        dispatch = {
            '4A': self._billing_fan_out,
            '4B': self._servicing_fan_in,
            '4C': self._reciprocal_billing,
            '4D': self._network_density,
            '4E': self._new_network_high_paid,
            '4F': self._billing_only_providers,
            '4G': self._ghost_provider_indicators,
        }
        handler = dispatch.get(subcategory)
        if handler is None:
            print(f"  Unknown subcategory: {subcategory}")
            return []
        return handler(hypothesis, con)

    def _ensure_graph(self, con):
        """Build the networkx DiGraph once from billing_servicing_network."""
        if self._graph_loaded:
            return self._graph

        try:
            import networkx as nx
        except ImportError:
            print("  networkx not available for network analysis")
            self._graph_loaded = True
            self._graph = None
            return None

        edges = self._safe_query(con, """
            SELECT
                billing_npi,
                servicing_npi,
                shared_codes,
                shared_months,
                total_paid,
                total_claims
            FROM billing_servicing_network
            WHERE billing_npi IS NOT NULL AND billing_npi != ''
              AND servicing_npi IS NOT NULL AND servicing_npi != ''
        """)

        if not edges:
            self._graph_loaded = True
            self._graph = None
            return None

        G = nx.DiGraph()
        for billing, servicing, codes, months, paid, claims in edges:
            G.add_edge(billing, servicing,
                        shared_codes=codes,
                        shared_months=months,
                        total_paid=paid,
                        total_claims=claims)

        self._graph = G
        self._graph_loaded = True
        print(f"  Network loaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G

    # ------------------------------------------------------------------
    # 4A: Billing NPI fan-out (many servicing NPIs)
    # ------------------------------------------------------------------
    def _billing_fan_out(self, hypothesis, con):
        """Count servicing NPIs per billing NPI. Flag billing providers
        that use an unusually large number of servicing providers.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        max_servicing = params.get('max_servicing', 50)
        min_total_paid = params.get('min_total_paid', 100000)

        rows = self._safe_query(con, """
            SELECT
                billing_npi,
                COUNT(DISTINCT servicing_npi) AS num_servicing,
                SUM(total_paid) AS total_paid,
                SUM(total_claims) AS total_claims,
                AVG(shared_months) AS avg_shared_months
            FROM billing_servicing_network
            GROUP BY billing_npi
            HAVING COUNT(DISTINCT servicing_npi) > ?
               AND SUM(total_paid) >= ?
            ORDER BY COUNT(DISTINCT servicing_npi) DESC
            LIMIT 1000
        """, [max_servicing, min_total_paid])

        for row in rows:
            npi, num_servicing, total_paid, total_claims, avg_months = row
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(total_paid, 2),
                confidence=min(0.90, 0.6 + 0.005 * min(num_servicing - max_servicing, 60)),
                method_name='billing_fan_out',
                evidence=(
                    f"Billing NPI uses {num_servicing} servicing providers "
                    f"(threshold={max_servicing}), total_paid=${total_paid:,.0f}, "
                    f"total_claims={total_claims:,}, "
                    f"avg_shared_months={avg_months:.1f}"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 4B: Servicing NPI fan-in (many billing NPIs)
    # ------------------------------------------------------------------
    def _servicing_fan_in(self, hypothesis, con):
        """Count billing NPIs per servicing NPI. Flag servicing providers
        being billed through an unusually large number of billing entities.
        Also check for rate differences across billers.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        max_billing = params.get('max_billing', 20)
        min_total_paid = params.get('min_total_paid', 100000)

        rows = self._safe_query(con, """
            SELECT
                servicing_npi,
                COUNT(DISTINCT billing_npi) AS num_billing,
                SUM(total_paid) AS total_paid,
                SUM(total_claims) AS total_claims,
                MIN(total_paid / NULLIF(total_claims, 0)) AS min_rate,
                MAX(total_paid / NULLIF(total_claims, 0)) AS max_rate,
                AVG(total_paid / NULLIF(total_claims, 0)) AS avg_rate
            FROM billing_servicing_network
            GROUP BY servicing_npi
            HAVING COUNT(DISTINCT billing_npi) > ?
               AND SUM(total_paid) >= ?
            ORDER BY COUNT(DISTINCT billing_npi) DESC
            LIMIT 1000
        """, [max_billing, min_total_paid])

        for row in rows:
            npi, num_billing, total_paid, total_claims, min_rate, max_rate, avg_rate = row
            rate_spread = max_rate / max(min_rate, 0.01) if min_rate and max_rate else 0
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(total_paid, 2),
                confidence=min(0.90, 0.6 + 0.01 * min(num_billing - max_billing, 30)),
                method_name='servicing_fan_in',
                evidence=(
                    f"Servicing NPI billed through {num_billing} billing providers "
                    f"(threshold={max_billing}), total_paid=${total_paid:,.0f}, "
                    f"rate range: ${min_rate:,.2f}-${max_rate:,.2f} "
                    f"(spread={rate_spread:.1f}x)"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 4C: Reciprocal billing (A bills through B and B bills through A)
    # ------------------------------------------------------------------
    def _reciprocal_billing(self, hypothesis, con):
        """Find pairs where A->B and B->A both exist in the
        billing_servicing_network, indicating potential collusion.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        min_pair_paid = params.get('min_pair_paid', 50000)

        rows = self._safe_query(con, """
            SELECT
                a.billing_npi AS npi_a,
                a.servicing_npi AS npi_b,
                a.total_paid AS a_to_b_paid,
                a.total_claims AS a_to_b_claims,
                b.total_paid AS b_to_a_paid,
                b.total_claims AS b_to_a_claims,
                a.total_paid + b.total_paid AS pair_total_paid
            FROM billing_servicing_network a
            JOIN billing_servicing_network b
                ON a.billing_npi = b.servicing_npi
                AND a.servicing_npi = b.billing_npi
            WHERE a.billing_npi < a.servicing_npi  -- avoid duplicates
              AND a.total_paid + b.total_paid >= ?
            ORDER BY pair_total_paid DESC
            LIMIT 500
        """, [min_pair_paid])

        for row in rows:
            npi_a, npi_b, a_to_b_paid, a_to_b_claims, b_to_a_paid, b_to_a_claims, pair_total = row
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi_a, npi_b],
                total_impact=round(pair_total, 2),
                confidence=0.80,
                method_name='reciprocal_billing',
                evidence=(
                    f"Reciprocal billing: {npi_a}->{npi_b}: "
                    f"${a_to_b_paid:,.0f} ({a_to_b_claims} claims), "
                    f"{npi_b}->{npi_a}: ${b_to_a_paid:,.0f} ({b_to_a_claims} claims). "
                    f"Total=${pair_total:,.0f}"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 4D: Network density / connected components
    # ------------------------------------------------------------------
    def _network_density(self, hypothesis, con):
        """Compute connected components and density of the billing-servicing
        network. Flag unusually dense clusters that may indicate fraud rings.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        min_component_size = params.get('min_component_size', 5)
        min_density = params.get('min_density', 0.3)
        min_component_paid = params.get('min_component_paid', 200000)

        try:
            import networkx as nx
        except ImportError:
            print("  networkx not available")
            return findings

        G = self._ensure_graph(con)
        if G is None:
            return findings

        # Get weakly connected components
        undirected = G.to_undirected()
        components = list(nx.connected_components(undirected))
        components = [c for c in components if len(c) >= min_component_size]

        print(f"  Found {len(components)} components with >= {min_component_size} nodes")

        for comp_nodes in sorted(components, key=len, reverse=True)[:500]:
            subgraph = G.subgraph(comp_nodes)
            n_nodes = subgraph.number_of_nodes()
            n_edges = subgraph.number_of_edges()

            # Density of the directed subgraph
            max_edges = n_nodes * (n_nodes - 1)
            density = n_edges / max_edges if max_edges > 0 else 0

            # Sum of paid in this component
            component_paid = sum(
                d.get('total_paid', 0)
                for _, _, d in subgraph.edges(data=True)
            )

            if density < min_density or component_paid < min_component_paid:
                continue

            providers_in_component = list(comp_nodes)

            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=providers_in_component[:50],  # Limit list size
                total_impact=round(component_paid, 2),
                confidence=min(0.90, 0.5 + 0.3 * density + 0.01 * min(n_nodes, 20)),
                method_name='network_density',
                evidence=(
                    f"Dense network cluster: {n_nodes} nodes, {n_edges} edges, "
                    f"density={density:.3f} (threshold={min_density}), "
                    f"total_paid=${component_paid:,.0f}"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 4E: New networks with high paid amounts
    # ------------------------------------------------------------------
    def _new_network_high_paid(self, hypothesis, con):
        """Filter billing-servicing edges by first shared month.
        Find new networks that quickly accumulate high paid amounts.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        min_paid = params.get('min_paid', 200000)
        max_shared_months = params.get('max_shared_months', 6)
        recency_months = params.get('recency_months', 24)

        # Find the latest month in the dataset
        max_month_result = self._safe_query(con, """
            SELECT MAX(claim_month) FROM provider_monthly
        """)
        if not max_month_result or max_month_result[0][0] is None:
            return findings
        dataset_max_month = max_month_result[0][0]

        # Compute the start date for "recent" edges
        recency_result = self._safe_query(con, f"""
            SELECT strftime(
                CAST('{dataset_max_month}-01' AS DATE) - INTERVAL '{recency_months}' MONTH,
                '%Y-%m'
            )
        """)
        if not recency_result or recency_result[0][0] is None:
            return findings
        recency_cutoff = recency_result[0][0]

        # We need to find the first month for each billing-servicing pair
        # from the raw claims table, since billing_servicing_network only
        # has aggregates
        rows = self._safe_query(con, """
            WITH edge_first_month AS (
                SELECT
                    billing_npi,
                    servicing_npi,
                    MIN(claim_month) AS first_month
                FROM claims
                WHERE servicing_npi IS NOT NULL AND servicing_npi != ''
                GROUP BY billing_npi, servicing_npi
            )
            SELECT
                bsn.billing_npi,
                bsn.servicing_npi,
                efm.first_month,
                bsn.shared_months,
                bsn.total_paid,
                bsn.total_claims,
                bsn.shared_codes
            FROM billing_servicing_network bsn
            JOIN edge_first_month efm
                ON bsn.billing_npi = efm.billing_npi
                AND bsn.servicing_npi = efm.servicing_npi
            WHERE efm.first_month >= ?
              AND bsn.shared_months <= ?
              AND bsn.total_paid >= ?
            ORDER BY bsn.total_paid DESC
            LIMIT 1000
        """, [recency_cutoff, max_shared_months, min_paid])

        for row in rows:
            billing, servicing, first_month, months, paid, claims, codes = row
            paid_per_month = paid / max(months, 1)
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[billing, servicing],
                total_impact=round(paid, 2),
                confidence=min(0.85, 0.6 + 0.05 * min(paid / max(min_paid, 1), 5)),
                method_name='new_network_high_paid',
                evidence=(
                    f"New relationship (started {first_month}): "
                    f"billing={billing}, servicing={servicing}, "
                    f"months={months}, paid=${paid:,.0f} "
                    f"(${paid_per_month:,.0f}/mo), "
                    f"claims={claims}, codes={codes}"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 4F: Billing-only providers (not found as servicing)
    # ------------------------------------------------------------------
    def _billing_only_providers(self, hypothesis, con):
        """Find billing NPIs that never appear as servicing NPIs.
        These may be shell companies that only pass through claims.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        min_total_paid = params.get('min_total_paid', 500000)
        min_servicing_count = params.get('min_servicing_count', 5)

        rows = self._safe_query(con, """
            WITH billing_npis AS (
                SELECT DISTINCT billing_npi
                FROM billing_servicing_network
            ),
            servicing_npis AS (
                SELECT DISTINCT servicing_npi
                FROM billing_servicing_network
            ),
            billing_only AS (
                SELECT b.billing_npi
                FROM billing_npis b
                LEFT JOIN servicing_npis s ON b.billing_npi = s.servicing_npi
                WHERE s.servicing_npi IS NULL
            )
            SELECT
                bo.billing_npi,
                ps.total_paid,
                ps.total_claims,
                ps.total_beneficiaries,
                ps.num_months,
                COUNT(DISTINCT bsn.servicing_npi) AS num_servicing_used
            FROM billing_only bo
            JOIN provider_summary ps ON bo.billing_npi = ps.billing_npi
            LEFT JOIN billing_servicing_network bsn ON bo.billing_npi = bsn.billing_npi
            WHERE ps.total_paid >= ?
            GROUP BY bo.billing_npi, ps.total_paid, ps.total_claims,
                     ps.total_beneficiaries, ps.num_months
            HAVING COUNT(DISTINCT bsn.servicing_npi) >= ?
            ORDER BY ps.total_paid DESC
            LIMIT 1000
        """, [min_total_paid, min_servicing_count])

        for row in rows:
            npi, total_paid, total_claims, bene, months, num_servicing = row
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(total_paid, 2),
                confidence=min(0.80, 0.55 + 0.02 * min(num_servicing, 12)),
                method_name='billing_only_provider',
                evidence=(
                    f"Billing-only NPI (never appears as servicing): "
                    f"total_paid=${total_paid:,.0f}, claims={total_claims:,}, "
                    f"bene={bene:,}, months={months}, "
                    f"uses {num_servicing} servicing providers"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 4G: Ghost provider indicators
    # ------------------------------------------------------------------
    def _ghost_provider_indicators(self, hypothesis, con):
        """Detect potential ghost providers based on multiple indicators:
        - Single billing entity (only one biller sends to this servicing NPI)
        - Short duration of activity
        - High paid amounts relative to duration
        - No record in NPPES providers table
        """
        findings = []
        params = hypothesis.get('parameters', {})
        min_paid = params.get('min_paid', 100000)
        max_duration_months = params.get('max_duration_months', 12)
        min_ghost_score = params.get('min_ghost_score', 3)

        # Find servicing NPIs with ghost indicators
        rows = self._safe_query(con, """
            WITH servicing_profile AS (
                SELECT
                    bsn.servicing_npi,
                    COUNT(DISTINCT bsn.billing_npi) AS num_billers,
                    SUM(bsn.total_paid) AS total_paid,
                    SUM(bsn.total_claims) AS total_claims,
                    MAX(bsn.shared_months) AS max_months,
                    MIN(bsn.shared_months) AS min_months
                FROM billing_servicing_network bsn
                GROUP BY bsn.servicing_npi
                HAVING SUM(bsn.total_paid) >= ?
            )
            SELECT
                sp.servicing_npi,
                sp.num_billers,
                sp.total_paid,
                sp.total_claims,
                sp.max_months,
                CASE WHEN p.npi IS NULL THEN 1 ELSE 0 END AS no_nppes_record,
                CASE WHEN sp.num_billers = 1 THEN 1 ELSE 0 END AS single_biller,
                CASE WHEN sp.max_months <= ? THEN 1 ELSE 0 END AS short_duration,
                CASE WHEN sp.total_paid / NULLIF(sp.max_months, 0) > 50000 THEN 1 ELSE 0 END AS high_monthly_rate,
                p.name,
                p.entity_type
            FROM servicing_profile sp
            LEFT JOIN providers p ON sp.servicing_npi = p.npi
        """, [min_paid, max_duration_months])

        for row in rows:
            (npi, num_billers, total_paid, total_claims, max_months,
             no_nppes, single_biller, short_duration, high_monthly,
             name, entity_type) = row

            # Compute ghost score (sum of indicator flags)
            ghost_score = no_nppes + single_biller + short_duration + high_monthly

            if ghost_score < min_ghost_score:
                continue

            indicators = []
            if no_nppes:
                indicators.append("no NPPES record")
            if single_biller:
                indicators.append(f"single biller (billers={num_billers})")
            if short_duration:
                indicators.append(f"short duration ({max_months} months)")
            if high_monthly:
                monthly_rate = total_paid / max(max_months, 1)
                indicators.append(f"high monthly rate (${monthly_rate:,.0f}/mo)")

            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(total_paid, 2),
                confidence=min(0.95, 0.5 + 0.1 * ghost_score),
                method_name='ghost_provider_indicators',
                evidence=(
                    f"Ghost score={ghost_score}/{4}: {', '.join(indicators)}. "
                    f"total_paid=${total_paid:,.0f}, claims={total_claims:,}, "
                    f"months={max_months}, "
                    f"name={'<missing>' if name is None else name}"
                ),
            ))

        return findings
