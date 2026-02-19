#!/usr/bin/env python3
"""Category 3: Peer Comparison Analysis.

Implements subcategories 3A-3F for detecting providers whose billing
patterns diverge significantly from their peers.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analyzers.base_analyzer import BaseAnalyzer


class PeerAnalyzer(BaseAnalyzer):
    """Detects providers deviating significantly from peer benchmarks."""

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
            '3A': self._paid_per_claim_vs_median,
            '3B': self._volume_vs_median,
            '3C': self._claims_per_bene_vs_median,
            '3D': self._state_peer_comparison,
            '3E': self._specialty_peer_comparison,
            '3F': self._size_tier_mismatch,
        }
        handler = dispatch.get(subcategory)
        if handler is None:
            print(f"  Unknown subcategory: {subcategory}")
            return []
        return handler(hypothesis, con)

    # ------------------------------------------------------------------
    # 3A: Paid per claim vs code-level median
    # ------------------------------------------------------------------
    def _paid_per_claim_vs_median(self, hypothesis, con):
        """Flag providers whose paid_per_claim for a given HCPCS code
        exceeds 2x the code-level median.

        Thresholds:
          - paid_per_claim > 2x median
          - claims >= 50
          - peer providers >= 30
        """
        findings = []
        params = hypothesis.get('parameters', {})
        hcpcs_code = params.get('hcpcs_code', None)
        multiplier = params.get('multiplier', 2.0)
        min_claims = params.get('min_claims', 50)
        min_peers = params.get('min_peers', 30)

        if hcpcs_code:
            codes_to_check = [(hcpcs_code,)]
        else:
            codes_to_check = self._safe_query(con, """
                SELECT hcpcs_code
                FROM hcpcs_summary
                WHERE num_providers >= ?
                ORDER BY total_paid DESC
                LIMIT 500
            """, [min_peers])

        for (code,) in codes_to_check:
            # Get code-level median from hcpcs_summary
            code_stats = self._safe_query(con, """
                SELECT
                    median_paid_per_claim,
                    num_providers
                FROM hcpcs_summary
                WHERE hcpcs_code = ?
            """, [code])

            if not code_stats or code_stats[0][0] is None:
                continue

            median_ppc, num_providers = code_stats[0]

            if num_providers < min_peers or median_ppc == 0:
                continue

            threshold = median_ppc * multiplier

            outliers = self._safe_query(con, """
                SELECT
                    ph.billing_npi,
                    ph.paid_per_claim,
                    ph.claims,
                    ph.paid,
                    ph.beneficiaries,
                    ph.paid_per_claim / ? AS ratio_to_median,
                    (ph.paid_per_claim - ?) * ph.claims AS excess
                FROM provider_hcpcs ph
                WHERE ph.hcpcs_code = ?
                  AND ph.claims >= ?
                  AND ph.paid_per_claim > ?
                ORDER BY ph.paid_per_claim DESC
                LIMIT 500
            """, [median_ppc, median_ppc, code, min_claims, threshold])

            for row in outliers:
                npi, ppc, claims_count, paid, bene, ratio, excess = row
                findings.append(self._make_finding(
                    hypothesis_id=hypothesis['id'],
                    providers=[npi],
                    total_impact=round(excess, 2),
                    confidence=min(0.95, 0.65 + 0.05 * min(ratio - multiplier, 6)),
                    method_name='paid_per_claim_vs_median',
                    evidence=(
                        f"HCPCS {code}: paid_per_claim=${ppc:.2f} vs "
                        f"median=${median_ppc:.2f} ({ratio:.1f}x), "
                        f"claims={claims_count}, bene={bene}, "
                        f"excess=${excess:,.0f}, peers={num_providers}"
                    ),
                ))

        return findings

    # ------------------------------------------------------------------
    # 3B: Volume (total claims) vs code-level median
    # ------------------------------------------------------------------
    def _volume_vs_median(self, hypothesis, con):
        """Flag providers whose total claims for a code exceed 10x the
        code-level median claim count.

        Thresholds:
          - claims > 10x median
          - months_active >= 12
          - total paid > $100K
        """
        findings = []
        params = hypothesis.get('parameters', {})
        hcpcs_code = params.get('hcpcs_code', None)
        volume_multiplier = params.get('volume_multiplier', 10.0)
        min_months = params.get('min_months', 12)
        min_total_paid = params.get('min_total_paid', 100000)

        if hcpcs_code:
            codes_to_check = [(hcpcs_code,)]
        else:
            codes_to_check = self._safe_query(con, """
                SELECT hcpcs_code
                FROM hcpcs_summary
                WHERE num_providers >= 30
                ORDER BY total_paid DESC
                LIMIT 500
            """)

        for (code,) in codes_to_check:
            # Compute median claims per provider for this code
            median_result = self._safe_query(con, """
                SELECT
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY claims) AS median_claims,
                    COUNT(*) AS num_providers
                FROM provider_hcpcs
                WHERE hcpcs_code = ?
            """, [code])

            if not median_result or median_result[0][0] is None:
                continue

            median_claims, num_providers = median_result[0]

            if median_claims == 0 or num_providers < 30:
                continue

            threshold = median_claims * volume_multiplier

            outliers = self._safe_query(con, """
                SELECT
                    ph.billing_npi,
                    ph.claims,
                    ph.paid,
                    ph.beneficiaries,
                    ph.months_active,
                    ph.claims / ? AS ratio_to_median
                FROM provider_hcpcs ph
                WHERE ph.hcpcs_code = ?
                  AND ph.months_active >= ?
                  AND ph.paid >= ?
                  AND ph.claims > ?
                ORDER BY ph.claims DESC
                LIMIT 500
            """, [median_claims, code, min_months, min_total_paid, threshold])

            for row in outliers:
                npi, claims_count, paid, bene, months, ratio = row
                findings.append(self._make_finding(
                    hypothesis_id=hypothesis['id'],
                    providers=[npi],
                    total_impact=round(paid, 2),
                    confidence=min(0.95, 0.65 + 0.03 * min(ratio - volume_multiplier, 10)),
                    method_name='volume_vs_median',
                    evidence=(
                        f"HCPCS {code}: claims={claims_count:,} vs "
                        f"median={median_claims:,.0f} ({ratio:.0f}x), "
                        f"paid=${paid:,.0f}, months={months}, "
                        f"peers={num_providers}"
                    ),
                ))

        return findings

    # ------------------------------------------------------------------
    # 3C: Claims per beneficiary vs code-level median
    # ------------------------------------------------------------------
    def _claims_per_bene_vs_median(self, hypothesis, con):
        """Flag providers whose claims_per_bene for a code exceeds 3x
        the code-level median and persists for 6+ months.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        hcpcs_code = params.get('hcpcs_code', None)
        cpb_multiplier = params.get('cpb_multiplier', 3.0)
        min_months = params.get('min_months', 6)

        if hcpcs_code:
            codes_to_check = [(hcpcs_code,)]
        else:
            codes_to_check = self._safe_query(con, """
                SELECT hcpcs_code
                FROM hcpcs_summary
                WHERE num_providers >= 30
                ORDER BY total_paid DESC
                LIMIT 500
            """)

        for (code,) in codes_to_check:
            median_result = self._safe_query(con, """
                SELECT
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY claims_per_bene) AS median_cpb,
                    COUNT(*) AS num_providers
                FROM provider_hcpcs
                WHERE hcpcs_code = ?
                  AND claims_per_bene IS NOT NULL
                  AND beneficiaries >= 5
            """, [code])

            if not median_result or median_result[0][0] is None:
                continue

            median_cpb, num_providers = median_result[0]

            if median_cpb == 0 or num_providers < 30:
                continue

            threshold = median_cpb * cpb_multiplier

            outliers = self._safe_query(con, """
                SELECT
                    ph.billing_npi,
                    ph.claims_per_bene,
                    ph.claims,
                    ph.beneficiaries,
                    ph.paid,
                    ph.months_active,
                    ph.claims_per_bene / ? AS ratio_to_median
                FROM provider_hcpcs ph
                WHERE ph.hcpcs_code = ?
                  AND ph.months_active >= ?
                  AND ph.claims_per_bene > ?
                  AND ph.beneficiaries >= 5
                ORDER BY ph.claims_per_bene DESC
                LIMIT 500
            """, [median_cpb, code, min_months, threshold])

            for row in outliers:
                npi, cpb, claims_count, bene, paid, months, ratio = row
                findings.append(self._make_finding(
                    hypothesis_id=hypothesis['id'],
                    providers=[npi],
                    total_impact=round(paid, 2),
                    confidence=min(0.95, 0.65 + 0.05 * min(ratio - cpb_multiplier, 6)),
                    method_name='claims_per_bene_vs_median',
                    evidence=(
                        f"HCPCS {code}: claims_per_bene={cpb:.2f} vs "
                        f"median={median_cpb:.2f} ({ratio:.1f}x), "
                        f"months={months}, bene={bene}, paid=${paid:,.0f}"
                    ),
                ))

        return findings

    # ------------------------------------------------------------------
    # 3D: State-level peer comparison
    # ------------------------------------------------------------------
    def _state_peer_comparison(self, hypothesis, con):
        """Join with providers table for state. Compare a provider's
        billing metrics to same-state peers for the same HCPCS code.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        hcpcs_code = params.get('hcpcs_code', None)
        multiplier = params.get('multiplier', 3.0)
        min_claims = params.get('min_claims', 20)
        min_state_peers = params.get('min_state_peers', 10)

        if hcpcs_code:
            codes_to_check = [(hcpcs_code,)]
        else:
            codes_to_check = self._safe_query(con, """
                SELECT hcpcs_code
                FROM hcpcs_summary
                WHERE num_providers >= 50
                ORDER BY total_paid DESC
                LIMIT 200
            """)

        for (code,) in codes_to_check:
            # Get state-level medians for this code
            state_medians = self._safe_query(con, """
                SELECT
                    p.state,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ph.paid_per_claim) AS state_median_ppc,
                    COUNT(*) AS state_peers
                FROM provider_hcpcs ph
                JOIN providers p ON ph.billing_npi = p.npi
                WHERE ph.hcpcs_code = ?
                  AND ph.claims >= ?
                  AND p.state IS NOT NULL AND p.state != ''
                GROUP BY p.state
                HAVING COUNT(*) >= ?
            """, [code, min_claims, min_state_peers])

            if not state_medians:
                continue

            for state, state_median, state_peers in state_medians:
                if state_median is None or state_median == 0:
                    continue

                threshold = state_median * multiplier

                outliers = self._safe_query(con, """
                    SELECT
                        ph.billing_npi,
                        ph.paid_per_claim,
                        ph.claims,
                        ph.paid,
                        ph.paid_per_claim / ? AS ratio_to_state_median,
                        (ph.paid_per_claim - ?) * ph.claims AS excess
                    FROM provider_hcpcs ph
                    JOIN providers p ON ph.billing_npi = p.npi
                    WHERE ph.hcpcs_code = ?
                      AND p.state = ?
                      AND ph.claims >= ?
                      AND ph.paid_per_claim > ?
                    ORDER BY ph.paid_per_claim DESC
                    LIMIT 100
                """, [state_median, state_median, code, state, min_claims, threshold])

                for row in outliers:
                    npi, ppc, claims_count, paid, ratio, excess = row
                    findings.append(self._make_finding(
                        hypothesis_id=hypothesis['id'],
                        providers=[npi],
                        total_impact=round(excess, 2),
                        confidence=min(0.95, 0.65 + 0.05 * min(ratio - multiplier, 6)),
                        method_name='state_peer_comparison',
                        evidence=(
                            f"HCPCS {code}, state {state}: "
                            f"paid_per_claim=${ppc:.2f} vs state median=${state_median:.2f} "
                            f"({ratio:.1f}x), claims={claims_count}, "
                            f"excess=${excess:,.0f}, state peers={state_peers}"
                        ),
                    ))

        return findings

    # ------------------------------------------------------------------
    # 3E: Specialty peer comparison
    # ------------------------------------------------------------------
    def _specialty_peer_comparison(self, hypothesis, con):
        """Compare a provider's total billing to same-specialty peers.
        Flag outliers within specialty groups.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        multiplier = params.get('multiplier', 5.0)
        min_specialty_peers = params.get('min_specialty_peers', 20)
        min_total_paid = params.get('min_total_paid', 100000)

        # Get specialty-level statistics
        specialty_stats = self._safe_query(con, """
            SELECT
                p.specialty,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ps.total_paid) AS median_paid,
                AVG(ps.total_paid) AS avg_paid,
                STDDEV(ps.total_paid) AS std_paid,
                COUNT(*) AS peer_count
            FROM provider_summary ps
            JOIN providers p ON ps.billing_npi = p.npi
            WHERE p.specialty IS NOT NULL AND p.specialty != '' AND p.specialty != 'Other'
            GROUP BY p.specialty
            HAVING COUNT(*) >= ?
        """, [min_specialty_peers])

        if not specialty_stats:
            return findings

        for specialty, median_paid, avg_paid, std_paid, peer_count in specialty_stats:
            if median_paid is None or median_paid == 0:
                continue

            threshold = median_paid * multiplier

            outliers = self._safe_query(con, """
                SELECT
                    ps.billing_npi,
                    ps.total_paid,
                    ps.total_claims,
                    ps.num_months,
                    ps.total_paid / ? AS ratio_to_median
                FROM provider_summary ps
                JOIN providers p ON ps.billing_npi = p.npi
                WHERE p.specialty = ?
                  AND ps.total_paid > ?
                  AND ps.total_paid >= ?
                ORDER BY ps.total_paid DESC
                LIMIT 100
            """, [median_paid, specialty, threshold, min_total_paid])

            for row in outliers:
                npi, total_paid, total_claims, num_months, ratio = row
                findings.append(self._make_finding(
                    hypothesis_id=hypothesis['id'],
                    providers=[npi],
                    total_impact=round(total_paid - median_paid, 2),
                    confidence=min(0.90, 0.6 + 0.03 * min(ratio - multiplier, 10)),
                    method_name='specialty_peer_comparison',
                    evidence=(
                        f"Specialty '{specialty}': total_paid=${total_paid:,.0f} vs "
                        f"median=${median_paid:,.0f} ({ratio:.1f}x), "
                        f"claims={total_claims:,}, months={num_months}, "
                        f"specialty peers={peer_count}"
                    ),
                ))

        return findings

    # ------------------------------------------------------------------
    # 3F: Size tier mismatch
    # ------------------------------------------------------------------
    def _size_tier_mismatch(self, hypothesis, con):
        """Detect size-tier mismatches: individual providers billing at
        organizational scale, or providers with high paid but unusually
        low claim counts (suggesting expensive phantom claims).
        """
        findings = []
        params = hypothesis.get('parameters', {})
        individual_paid_threshold = params.get('individual_paid_threshold', 5000000)
        high_paid_low_claims_ratio = params.get('high_paid_low_claims_ratio', 1000)
        min_total_paid = params.get('min_total_paid', 500000)

        # Find individual providers (entity_type=1) billing at org scale
        individual_outliers = self._safe_query(con, """
            SELECT
                ps.billing_npi,
                p.name,
                p.entity_type,
                p.specialty,
                ps.total_paid,
                ps.total_claims,
                ps.total_beneficiaries,
                ps.num_months,
                ps.total_paid / NULLIF(ps.total_claims, 0) AS avg_paid_per_claim
            FROM provider_summary ps
            JOIN providers p ON ps.billing_npi = p.npi
            WHERE p.entity_type = '1'
              AND ps.total_paid > ?
            ORDER BY ps.total_paid DESC
            LIMIT 500
        """, [individual_paid_threshold])

        for row in individual_outliers:
            npi, name, entity_type, specialty, total_paid, total_claims, bene, months, ppc = row
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(total_paid, 2),
                confidence=0.75,
                method_name='size_tier_individual_at_org_scale',
                evidence=(
                    f"Individual provider '{name}' ({specialty}): "
                    f"total_paid=${total_paid:,.0f} exceeds ${individual_paid_threshold:,.0f} threshold. "
                    f"claims={total_claims:,}, bene={bene:,}, months={months}"
                ),
            ))

        # Find providers with high paid per claim but very few claims
        # (suggests expensive phantom or upcoded claims)
        high_ppc_outliers = self._safe_query(con, """
            SELECT
                ps.billing_npi,
                ps.total_paid,
                ps.total_claims,
                ps.total_beneficiaries,
                ps.avg_paid_per_claim,
                ps.num_months
            FROM provider_summary ps
            WHERE ps.total_paid >= ?
              AND ps.avg_paid_per_claim > ?
              AND ps.total_claims < 1000
            ORDER BY ps.avg_paid_per_claim DESC
            LIMIT 500
        """, [min_total_paid, high_paid_low_claims_ratio])

        for row in high_ppc_outliers:
            npi, total_paid, total_claims, bene, ppc, months = row
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(total_paid, 2),
                confidence=min(0.90, 0.6 + 0.05 * min(ppc / max(high_paid_low_claims_ratio, 1), 6)),
                method_name='size_tier_high_paid_low_claims',
                evidence=(
                    f"High cost/low volume: avg_paid_per_claim=${ppc:,.2f}, "
                    f"total_claims={total_claims}, total_paid=${total_paid:,.0f}, "
                    f"bene={bene}, months={months}. "
                    f"Possible phantom or upcoded claims."
                ),
            ))

        return findings
