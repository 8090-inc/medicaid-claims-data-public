#!/usr/bin/env python3
"""Category 5: Market Concentration Analysis.

Implements subcategories 5A-5E for detecting market dominance,
monopolistic patterns, and revenue concentration anomalies.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analyzers.base_analyzer import BaseAnalyzer


class ConcentrationAnalyzer(BaseAnalyzer):
    """Detects market concentration and monopolistic billing patterns."""

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
            '5A': self._provider_share_per_code,
            '5B': self._code_concentration_per_provider,
            '5C': self._hhi_per_code,
            '5D': self._state_level_share,
            '5E': self._temporal_revenue_concentration,
        }
        handler = dispatch.get(subcategory)
        if handler is None:
            print(f"  Unknown subcategory: {subcategory}")
            return []
        return handler(hypothesis, con)

    # ------------------------------------------------------------------
    # 5A: Provider share per HCPCS code
    # ------------------------------------------------------------------
    def _provider_share_per_code(self, hypothesis, con):
        """For each HCPCS code, compute the share of total paid
        attributable to each provider. Flag providers with dominant
        shares: > 30%, > 50%, > 80%.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        share_threshold_low = params.get('share_threshold_low', 0.30)
        share_threshold_med = params.get('share_threshold_med', 0.50)
        share_threshold_high = params.get('share_threshold_high', 0.80)
        min_code_total = params.get('min_code_total', 100000)
        min_providers = params.get('min_providers', 5)

        # Get codes with enough spending and providers
        codes = self._safe_query(con, """
            SELECT hcpcs_code, total_paid, num_providers
            FROM hcpcs_summary
            WHERE total_paid >= ?
              AND num_providers >= ?
            ORDER BY total_paid DESC
            LIMIT 1000
        """, [min_code_total, min_providers])

        for code, code_total, num_providers in codes:
            # Find dominant providers for this code
            top_providers = self._safe_query(con, """
                SELECT
                    billing_npi,
                    paid,
                    claims,
                    beneficiaries,
                    paid / ? AS share
                FROM provider_hcpcs
                WHERE hcpcs_code = ?
                  AND paid / ? >= ?
                ORDER BY paid DESC
                LIMIT 50
            """, [code_total, code, code_total, share_threshold_low])

            for row in top_providers:
                npi, paid, claims_count, bene, share = row
                if share is None:
                    continue

                # Determine severity
                if share >= share_threshold_high:
                    severity = 'dominant (>80%)'
                    confidence_base = 0.90
                elif share >= share_threshold_med:
                    severity = 'majority (>50%)'
                    confidence_base = 0.80
                else:
                    severity = 'significant (>30%)'
                    confidence_base = 0.70

                findings.append(self._make_finding(
                    hypothesis_id=hypothesis['id'],
                    providers=[npi],
                    total_impact=round(paid, 2),
                    confidence=min(0.95, confidence_base + 0.1 * share),
                    method_name='provider_share_per_code',
                    evidence=(
                        f"HCPCS {code}: provider holds {share:.1%} of "
                        f"${code_total:,.0f} total ({severity}). "
                        f"Provider paid=${paid:,.0f}, claims={claims_count:,}, "
                        f"bene={bene:,}, code providers={num_providers}"
                    ),
                ))

        return findings

    # ------------------------------------------------------------------
    # 5B: Code concentration per provider (top-code reliance)
    # ------------------------------------------------------------------
    def _code_concentration_per_provider(self, hypothesis, con):
        """For each provider, compute the percentage of total paid from
        their top HCPCS code. Flag if > 90% of revenue from a single
        code and total > $1M.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        top_code_share_threshold = params.get('top_code_share_threshold', 0.90)
        min_total_paid = params.get('min_total_paid', 1000000)

        rows = self._safe_query(con, """
            WITH provider_top_code AS (
                SELECT
                    ph.billing_npi,
                    ph.hcpcs_code,
                    ph.paid AS code_paid,
                    ps.total_paid AS provider_total,
                    ph.paid / NULLIF(ps.total_paid, 0) AS code_share,
                    ROW_NUMBER() OVER (
                        PARTITION BY ph.billing_npi ORDER BY ph.paid DESC
                    ) AS rank_num
                FROM provider_hcpcs ph
                JOIN provider_summary ps ON ph.billing_npi = ps.billing_npi
                WHERE ps.total_paid >= ?
            )
            SELECT
                billing_npi,
                hcpcs_code,
                code_paid,
                provider_total,
                code_share
            FROM provider_top_code
            WHERE rank_num = 1
              AND code_share >= ?
            ORDER BY provider_total DESC
            LIMIT 1000
        """, [min_total_paid, top_code_share_threshold])

        for row in rows:
            npi, code, code_paid, provider_total, share = row
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(provider_total, 2),
                confidence=min(0.90, 0.65 + 0.2 * share),
                method_name='code_concentration_per_provider',
                evidence=(
                    f"Provider derives {share:.1%} of ${provider_total:,.0f} "
                    f"from single code {code} (${code_paid:,.0f}). "
                    f"Extreme code concentration."
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 5C: HHI (Herfindahl-Hirschman Index) per HCPCS code
    # ------------------------------------------------------------------
    def _hhi_per_code(self, hypothesis, con):
        """Compute the HHI for each HCPCS code based on provider shares.
        HHI > 2500 indicates a highly concentrated market.

        HHI = sum of (share_i * 100)^2 for all providers i
        """
        findings = []
        params = hypothesis.get('parameters', {})
        hhi_threshold = params.get('hhi_threshold', 2500)
        min_code_total = params.get('min_code_total', 500000)
        min_providers = params.get('min_providers', 3)

        rows = self._safe_query(con, """
            WITH code_shares AS (
                SELECT
                    ph.hcpcs_code,
                    ph.billing_npi,
                    ph.paid,
                    hs.total_paid AS code_total,
                    hs.num_providers,
                    (ph.paid / NULLIF(hs.total_paid, 0) * 100) AS market_share_pct
                FROM provider_hcpcs ph
                JOIN hcpcs_summary hs ON ph.hcpcs_code = hs.hcpcs_code
                WHERE hs.total_paid >= ?
                  AND hs.num_providers >= ?
            ),
            hhi_calc AS (
                SELECT
                    hcpcs_code,
                    SUM(market_share_pct * market_share_pct) AS hhi,
                    MAX(code_total) AS code_total,
                    MAX(num_providers) AS num_providers,
                    MAX(market_share_pct) AS top_share_pct,
                    FIRST(billing_npi ORDER BY paid DESC) AS top_provider
                FROM code_shares
                GROUP BY hcpcs_code
                HAVING SUM(market_share_pct * market_share_pct) > ?
            )
            SELECT
                hcpcs_code,
                hhi,
                code_total,
                num_providers,
                top_share_pct,
                top_provider
            FROM hhi_calc
            ORDER BY hhi DESC
            LIMIT 500
        """, [min_code_total, min_providers, hhi_threshold])

        for row in rows:
            code, hhi, code_total, num_providers, top_share, top_provider = row
            # Categorize HHI
            if hhi >= 5000:
                concentration = 'extremely concentrated'
            elif hhi >= 2500:
                concentration = 'highly concentrated'
            else:
                concentration = 'moderately concentrated'

            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[top_provider] if top_provider else [],
                total_impact=round(code_total, 2),
                confidence=min(0.90, 0.6 + 0.1 * min(hhi / 2500, 3)),
                method_name='hhi_per_code',
                evidence=(
                    f"HCPCS {code}: HHI={hhi:,.0f} ({concentration}), "
                    f"code_total=${code_total:,.0f}, providers={num_providers}, "
                    f"top provider share={top_share:.1f}%, "
                    f"top provider={top_provider}"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 5D: State-level market share
    # ------------------------------------------------------------------
    def _state_level_share(self, hypothesis, con):
        """Join providers table for state. Compute each provider's share
        of total state-level Medicaid spending. Flag dominant providers.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        share_threshold = params.get('share_threshold', 0.10)
        min_state_total = params.get('min_state_total', 10000000)

        rows = self._safe_query(con, """
            WITH state_totals AS (
                SELECT
                    p.state,
                    SUM(ps.total_paid) AS state_total,
                    COUNT(*) AS state_providers
                FROM provider_summary ps
                JOIN providers p ON ps.billing_npi = p.npi
                WHERE p.state IS NOT NULL AND p.state != ''
                GROUP BY p.state
                HAVING SUM(ps.total_paid) >= ?
            ),
            provider_shares AS (
                SELECT
                    ps.billing_npi,
                    p.state,
                    p.name,
                    ps.total_paid,
                    st.state_total,
                    st.state_providers,
                    ps.total_paid / NULLIF(st.state_total, 0) AS state_share
                FROM provider_summary ps
                JOIN providers p ON ps.billing_npi = p.npi
                JOIN state_totals st ON p.state = st.state
            )
            SELECT
                billing_npi,
                state,
                name,
                total_paid,
                state_total,
                state_providers,
                state_share
            FROM provider_shares
            WHERE state_share >= ?
            ORDER BY state_share DESC
            LIMIT 1000
        """, [min_state_total, share_threshold])

        for row in rows:
            npi, state, name, total_paid, state_total, state_providers, share = row
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(total_paid, 2),
                confidence=min(0.90, 0.6 + 0.3 * share),
                method_name='state_level_share',
                evidence=(
                    f"State {state}: '{name}' holds {share:.1%} of "
                    f"${state_total:,.0f} state total. "
                    f"Provider paid=${total_paid:,.0f}, "
                    f"state providers={state_providers}"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 5E: Temporal revenue concentration
    # ------------------------------------------------------------------
    def _temporal_revenue_concentration(self, hypothesis, con):
        """For each provider, compute the share of annual revenue
        attributable to each month. Flag providers where > 40% of
        annual revenue is concentrated in 1-2 months.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        month_share_threshold = params.get('month_share_threshold', 0.40)
        min_annual_paid = params.get('min_annual_paid', 200000)
        min_months_active = params.get('min_months_active', 6)

        # For each provider-year, find the top month's share
        rows = self._safe_query(con, """
            WITH annual_totals AS (
                SELECT
                    billing_npi,
                    LEFT(claim_month, 4) AS year,
                    SUM(paid) AS annual_paid,
                    COUNT(*) AS months_in_year
                FROM provider_monthly
                GROUP BY billing_npi, LEFT(claim_month, 4)
                HAVING SUM(paid) >= ?
                   AND COUNT(*) >= ?
            ),
            monthly_shares AS (
                SELECT
                    pm.billing_npi,
                    LEFT(pm.claim_month, 4) AS year,
                    pm.claim_month,
                    pm.paid,
                    at.annual_paid,
                    pm.paid / NULLIF(at.annual_paid, 0) AS month_share,
                    ROW_NUMBER() OVER (
                        PARTITION BY pm.billing_npi, LEFT(pm.claim_month, 4)
                        ORDER BY pm.paid DESC
                    ) AS rank_num
                FROM provider_monthly pm
                JOIN annual_totals at
                    ON pm.billing_npi = at.billing_npi
                    AND LEFT(pm.claim_month, 4) = at.year
            )
            SELECT
                billing_npi,
                year,
                claim_month AS top_month,
                paid AS top_month_paid,
                annual_paid,
                month_share
            FROM monthly_shares
            WHERE rank_num = 1
              AND month_share >= ?
            ORDER BY annual_paid DESC
            LIMIT 1000
        """, [min_annual_paid, min_months_active, month_share_threshold])

        for row in rows:
            npi, year, top_month, top_paid, annual_paid, share = row
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(top_paid, 2),
                confidence=min(0.85, 0.6 + 0.3 * share),
                method_name='temporal_revenue_concentration',
                evidence=(
                    f"Year {year}: {top_month} accounts for {share:.1%} of "
                    f"${annual_paid:,.0f} annual revenue "
                    f"(${top_paid:,.0f} in one month). "
                    f"Abnormal temporal concentration."
                ),
            ))

        # Also check for top-2 months concentration
        rows_top2 = self._safe_query(con, """
            WITH annual_totals AS (
                SELECT
                    billing_npi,
                    LEFT(claim_month, 4) AS year,
                    SUM(paid) AS annual_paid,
                    COUNT(*) AS months_in_year
                FROM provider_monthly
                GROUP BY billing_npi, LEFT(claim_month, 4)
                HAVING SUM(paid) >= ?
                   AND COUNT(*) >= ?
            ),
            monthly_ranked AS (
                SELECT
                    pm.billing_npi,
                    LEFT(pm.claim_month, 4) AS year,
                    pm.claim_month,
                    pm.paid,
                    at.annual_paid,
                    ROW_NUMBER() OVER (
                        PARTITION BY pm.billing_npi, LEFT(pm.claim_month, 4)
                        ORDER BY pm.paid DESC
                    ) AS rank_num
                FROM provider_monthly pm
                JOIN annual_totals at
                    ON pm.billing_npi = at.billing_npi
                    AND LEFT(pm.claim_month, 4) = at.year
            ),
            top2_sum AS (
                SELECT
                    billing_npi,
                    year,
                    annual_paid,
                    SUM(paid) AS top2_paid,
                    SUM(paid) / NULLIF(annual_paid, 0) AS top2_share,
                    STRING_AGG(claim_month, ', ' ORDER BY paid DESC) AS top2_months
                FROM monthly_ranked
                WHERE rank_num <= 2
                GROUP BY billing_npi, year, annual_paid
            )
            SELECT
                billing_npi,
                year,
                top2_months,
                top2_paid,
                annual_paid,
                top2_share
            FROM top2_sum
            WHERE top2_share >= 0.60
            ORDER BY annual_paid DESC
            LIMIT 500
        """, [min_annual_paid, min_months_active])

        for row in rows_top2:
            npi, year, top2_months, top2_paid, annual_paid, share = row
            # Avoid duplicating findings already captured in top-1 check
            if share < 0.60:
                continue
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(top2_paid, 2),
                confidence=min(0.85, 0.55 + 0.3 * share),
                method_name='temporal_revenue_concentration_top2',
                evidence=(
                    f"Year {year}: top 2 months ({top2_months}) account for "
                    f"{share:.1%} of ${annual_paid:,.0f} annual revenue "
                    f"(${top2_paid:,.0f}). Extreme temporal concentration."
                ),
            ))

        return findings
