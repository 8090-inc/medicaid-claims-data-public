#!/usr/bin/env python3
"""Category 1: Statistical Outlier Detection.

Implements subcategories 1A-1F for detecting statistically anomalous
billing patterns across Medicaid providers.
"""

import os
import sys
import math
import collections

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analyzers.base_analyzer import BaseAnalyzer


class StatisticalAnalyzer(BaseAnalyzer):
    """Detects statistical outliers in provider billing data."""

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
            '1A': self._zscore_paid_per_claim,
            '1B': self._zscore_claims_per_bene,
            '1C': self._zscore_paid_per_bene,
            '1D': self._iqr_outlier,
            '1E': self._gev_extreme_value,
            '1F': self._benfords_law,
        }
        handler = dispatch.get(subcategory)
        if handler is None:
            print(f"  Unknown subcategory: {subcategory}")
            return []
        return handler(hypothesis, con)

    # ------------------------------------------------------------------
    # 1A: Z-score on paid_per_claim per HCPCS code
    # ------------------------------------------------------------------
    def _zscore_paid_per_claim(self, hypothesis, con):
        """Flag providers whose avg paid_per_claim for a given HCPCS code
        is more than 3 standard deviations above the code-level mean.

        Thresholds:
          - z-score > 3
          - provider must have >= 10 claims for that code
          - peer group (providers billing the code) >= 20
          - excess dollar amount > $10,000
        """
        findings = []
        params = hypothesis.get('parameters', {})
        hcpcs_code = params.get('hcpcs_code', None)
        z_threshold = params.get('z_threshold', 3.0)
        min_claims = params.get('min_claims', 10)
        min_peers = params.get('min_peers', 20)
        min_excess = params.get('min_excess', 10000)

        # If a specific code is provided, only check that code; otherwise scan top codes
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
            # Get code-level statistics from provider_hcpcs
            stats = self._safe_query(con, """
                SELECT
                    AVG(paid_per_claim) AS mean_ppc,
                    STDDEV(paid_per_claim) AS std_ppc,
                    COUNT(*) AS num_providers
                FROM provider_hcpcs
                WHERE hcpcs_code = ?
                  AND claims >= ?
            """, [code, min_claims])

            if not stats or stats[0][0] is None or stats[0][1] is None:
                continue

            mean_ppc, std_ppc, num_providers = stats[0]

            if num_providers < min_peers or std_ppc == 0:
                continue

            # Find outlier providers
            outliers = self._safe_query(con, """
                SELECT
                    billing_npi,
                    paid_per_claim,
                    claims,
                    paid,
                    (paid_per_claim - ?) / ? AS z_score,
                    (paid_per_claim - ?) * claims AS excess_amount
                FROM provider_hcpcs
                WHERE hcpcs_code = ?
                  AND claims >= ?
                  AND (paid_per_claim - ?) / ? > ?
                ORDER BY z_score DESC
            """, [mean_ppc, std_ppc, mean_ppc, code, min_claims,
                  mean_ppc, std_ppc, z_threshold])

            for row in outliers:
                npi, ppc, claims_count, paid, z_score, excess = row
                if excess is None or excess < min_excess:
                    continue
                findings.append(self._make_finding(
                    hypothesis_id=hypothesis['id'],
                    providers=[npi],
                    total_impact=round(excess, 2),
                    confidence=min(0.99, 0.7 + 0.05 * (z_score - z_threshold)),
                    method_name='zscore_paid_per_claim',
                    evidence=(
                        f"HCPCS {code}: provider paid_per_claim=${ppc:.2f} vs "
                        f"mean=${mean_ppc:.2f} (z={z_score:.2f}, "
                        f"claims={claims_count}, peers={num_providers}, "
                        f"excess=${excess:,.0f})"
                    ),
                ))

        return findings

    # ------------------------------------------------------------------
    # 1B: Z-score on claims_per_bene per HCPCS code
    # ------------------------------------------------------------------
    def _zscore_claims_per_bene(self, hypothesis, con):
        """Flag providers whose claims_per_bene for a given HCPCS code
        is more than 3 standard deviations above the code-level mean.

        Thresholds:
          - z-score > 3
          - beneficiaries >= 12
          - ratio > 2x the code-level median
        """
        findings = []
        params = hypothesis.get('parameters', {})
        hcpcs_code = params.get('hcpcs_code', None)
        z_threshold = params.get('z_threshold', 3.0)
        min_bene = params.get('min_bene', 12)
        median_multiplier = params.get('median_multiplier', 2.0)

        if hcpcs_code:
            codes_to_check = [(hcpcs_code,)]
        else:
            codes_to_check = self._safe_query(con, """
                SELECT hcpcs_code
                FROM hcpcs_summary
                WHERE num_providers >= 20
                ORDER BY total_paid DESC
                LIMIT 500
            """)

        for (code,) in codes_to_check:
            stats = self._safe_query(con, """
                SELECT
                    AVG(claims_per_bene) AS mean_cpb,
                    STDDEV(claims_per_bene) AS std_cpb,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY claims_per_bene) AS median_cpb,
                    COUNT(*) AS num_providers
                FROM provider_hcpcs
                WHERE hcpcs_code = ?
                  AND beneficiaries >= ?
                  AND claims_per_bene IS NOT NULL
            """, [code, min_bene])

            if not stats or stats[0][0] is None or stats[0][1] is None:
                continue

            mean_cpb, std_cpb, median_cpb, num_providers = stats[0]

            if num_providers < 20 or std_cpb == 0 or median_cpb is None or median_cpb == 0:
                continue

            outliers = self._safe_query(con, """
                SELECT
                    billing_npi,
                    claims_per_bene,
                    beneficiaries,
                    claims,
                    paid,
                    (claims_per_bene - ?) / ? AS z_score
                FROM provider_hcpcs
                WHERE hcpcs_code = ?
                  AND beneficiaries >= ?
                  AND claims_per_bene IS NOT NULL
                  AND (claims_per_bene - ?) / ? > ?
                  AND claims_per_bene > ? * ?
                ORDER BY z_score DESC
            """, [mean_cpb, std_cpb, code, min_bene,
                  mean_cpb, std_cpb, z_threshold,
                  median_cpb, median_multiplier])

            for row in outliers:
                npi, cpb, bene, claims_count, paid, z_score = row
                findings.append(self._make_finding(
                    hypothesis_id=hypothesis['id'],
                    providers=[npi],
                    total_impact=round(paid, 2),
                    confidence=min(0.99, 0.7 + 0.05 * (z_score - z_threshold)),
                    method_name='zscore_claims_per_bene',
                    evidence=(
                        f"HCPCS {code}: provider claims_per_bene={cpb:.2f} vs "
                        f"mean={mean_cpb:.2f}, median={median_cpb:.2f} "
                        f"(z={z_score:.2f}, bene={bene}, ratio={cpb/median_cpb:.1f}x)"
                    ),
                ))

        return findings

    # ------------------------------------------------------------------
    # 1C: Z-score on paid_per_bene
    # ------------------------------------------------------------------
    def _zscore_paid_per_bene(self, hypothesis, con):
        """Flag providers whose paid_per_bene is more than 3 standard
        deviations above the provider-level mean.

        Thresholds:
          - z-score > 3
          - excess > $500 per beneficiary
        """
        findings = []
        params = hypothesis.get('parameters', {})
        z_threshold = params.get('z_threshold', 3.0)
        min_excess_per_bene = params.get('min_excess_per_bene', 500)
        min_bene = params.get('min_bene', 10)

        stats = self._safe_query(con, """
            SELECT
                AVG(total_paid / NULLIF(total_beneficiaries, 0)) AS mean_ppb,
                STDDEV(total_paid / NULLIF(total_beneficiaries, 0)) AS std_ppb
            FROM provider_summary
            WHERE total_beneficiaries >= ?
        """, [min_bene])

        if not stats or stats[0][0] is None or stats[0][1] is None:
            return findings

        mean_ppb, std_ppb = stats[0]

        if std_ppb == 0:
            return findings

        outliers = self._safe_query(con, """
            SELECT
                billing_npi,
                total_paid,
                total_beneficiaries,
                total_paid / NULLIF(total_beneficiaries, 0) AS paid_per_bene,
                (total_paid / NULLIF(total_beneficiaries, 0) - ?) / ? AS z_score,
                (total_paid / NULLIF(total_beneficiaries, 0) - ?) * total_beneficiaries AS excess
            FROM provider_summary
            WHERE total_beneficiaries >= ?
              AND (total_paid / NULLIF(total_beneficiaries, 0) - ?) / ? > ?
            ORDER BY z_score DESC
            LIMIT 1000
        """, [mean_ppb, std_ppb, mean_ppb, min_bene,
              mean_ppb, std_ppb, z_threshold])

        for row in outliers:
            npi, total_paid, total_bene, ppb, z_score, excess = row
            if ppb is None:
                continue
            excess_per_bene = ppb - mean_ppb
            if excess_per_bene < min_excess_per_bene:
                continue
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(excess, 2),
                confidence=min(0.99, 0.7 + 0.05 * (z_score - z_threshold)),
                method_name='zscore_paid_per_bene',
                evidence=(
                    f"Provider paid_per_bene=${ppb:,.2f} vs mean=${mean_ppb:,.2f} "
                    f"(z={z_score:.2f}, bene={total_bene}, "
                    f"excess_per_bene=${excess_per_bene:,.0f}, "
                    f"total_excess=${excess:,.0f})"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 1D: IQR-based outlier detection
    # ------------------------------------------------------------------
    def _iqr_outlier(self, hypothesis, con):
        """Flag providers whose specified metric exceeds Q3 + 3*IQR
        from the provider_summary distribution.

        Thresholds:
          - value > Q3 + 3*IQR
          - num_months >= 6
          - total impact > $50,000
        """
        findings = []
        params = hypothesis.get('parameters', {})
        metric = params.get('metric', 'total_paid')
        min_months = params.get('min_months', 6)
        min_impact = params.get('min_impact', params.get('min_amount', 50000))
        iqr_multiplier = params.get('iqr_multiplier', 3.0)

        # Validate metric name to prevent SQL injection
        allowed_metrics = [
            'total_paid', 'total_claims', 'total_beneficiaries',
            'avg_paid_per_claim', 'avg_claims_per_bene', 'num_codes',
            'num_months',
        ]
        if metric not in allowed_metrics:
            print(f"  Invalid metric: {metric}")
            return findings

        # Compute Q1 and Q3 from provider_summary
        quartiles = self._safe_query(con, f"""
            SELECT
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {metric}) AS q1,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {metric}) AS q3
            FROM provider_summary
            WHERE num_months >= ?
              AND {metric} IS NOT NULL
        """, [min_months])

        if not quartiles or quartiles[0][0] is None or quartiles[0][1] is None:
            return findings

        q1, q3 = quartiles[0]
        iqr = q3 - q1

        if iqr == 0:
            return findings

        upper_fence = q3 + iqr_multiplier * iqr

        outliers = self._safe_query(con, f"""
            SELECT
                billing_npi,
                {metric} AS metric_value,
                total_paid,
                num_months,
                total_claims
            FROM provider_summary
            WHERE num_months >= ?
              AND {metric} > ?
            ORDER BY {metric} DESC
            LIMIT 1000
        """, [min_months, upper_fence])

        for row in outliers:
            npi, metric_value, total_paid, num_months, total_claims = row
            # For non-dollar metrics, use total_paid as impact
            impact = total_paid if metric != 'total_paid' else metric_value
            if impact < min_impact:
                continue
            excess_over_fence = metric_value - upper_fence
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(impact, 2),
                confidence=min(0.99, 0.75 + 0.01 * min(excess_over_fence / max(iqr, 1), 25)),
                method_name='iqr_outlier',
                evidence=(
                    f"Metric '{metric}'={metric_value:,.2f}, "
                    f"Q1={q1:,.2f}, Q3={q3:,.2f}, IQR={iqr:,.2f}, "
                    f"upper_fence={upper_fence:,.2f}, "
                    f"months={num_months}, total_paid=${total_paid:,.0f}"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 1E: Generalized Extreme Value (GEV) distribution analysis
    # ------------------------------------------------------------------
    def _gev_extreme_value(self, hypothesis, con):
        """Fit a GEV distribution to provider-level metric values for
        a given HCPCS category, then flag providers exceeding the 99th
        percentile return level.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        category = params.get('category', None)
        metric = params.get('metric', 'paid_per_claim')
        percentile_threshold = params.get('percentile_threshold', params.get('p_threshold', 0.99))
        min_claims = params.get('min_claims', 10)

        try:
            from scipy.stats import genextreme
            import numpy as np
        except ImportError:
            print("  scipy not available for GEV analysis")
            return findings

        # Get HCPCS codes in the requested category
        if category:
            codes_result = self._safe_query(con, """
                SELECT hcpcs_code FROM hcpcs_codes WHERE category = ?
            """, [category])
            if not codes_result:
                return findings
            code_list = [r[0] for r in codes_result]
            code_filter = "AND hcpcs_code IN (" + ",".join(f"'{c}'" for c in code_list) + ")"
        else:
            code_filter = ""

        # Validate metric
        allowed_metrics = ['paid_per_claim', 'claims_per_bene', 'paid', 'total_paid']
        if metric not in allowed_metrics:
            print(f"  Invalid metric for GEV: {metric}")
            return findings

        # Get the distribution of provider-level metric values
        data_rows = self._safe_query(con, f"""
            SELECT
                billing_npi,
                SUM(paid) / NULLIF(SUM(claims), 0) AS paid_per_claim,
                SUM(claims) / NULLIF(SUM(beneficiaries), 0) AS claims_per_bene,
                SUM(paid) AS paid,
                SUM(claims) AS total_claims
            FROM provider_hcpcs
            WHERE claims >= ? {code_filter}
            GROUP BY billing_npi
            HAVING SUM(claims) >= ?
        """, [min_claims, min_claims])

        if not data_rows or len(data_rows) < 30:
            return findings

        metric_idx = {'paid_per_claim': 1, 'claims_per_bene': 2, 'paid': 3, 'total_paid': 3}[metric]
        npis = [r[0] for r in data_rows]
        values = np.array([r[metric_idx] for r in data_rows if r[metric_idx] is not None], dtype=float)
        npi_values = [(r[0], r[metric_idx], r[3], r[4]) for r in data_rows if r[metric_idx] is not None]

        if len(values) < 30:
            return findings

        # Remove extreme outliers before fitting (top 0.1% could distort the fit)
        clip_threshold = np.percentile(values, 99.9)
        fit_values = values[values <= clip_threshold]

        if len(fit_values) < 30:
            return findings

        try:
            shape, loc, scale = genextreme.fit(fit_values)
            return_level = genextreme.ppf(percentile_threshold, shape, loc=loc, scale=scale)
        except Exception as e:
            print(f"  GEV fit failed: {e}")
            return findings

        # Flag providers exceeding the return level
        for npi, val, paid, total_claims in npi_values:
            if val is None or val <= return_level:
                continue
            excess = (val - return_level) * total_claims if metric == 'paid_per_claim' else val - return_level
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(abs(excess), 2),
                confidence=0.85,
                method_name='gev_extreme_value',
                evidence=(
                    f"Category '{category or 'all'}', metric '{metric}': "
                    f"value={val:,.2f}, GEV 99th pctile return level={return_level:,.2f}, "
                    f"GEV params(shape={shape:.4f}, loc={loc:.2f}, scale={scale:.2f}), "
                    f"claims={total_claims}"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 1F: Benford's Law and round-number detection
    # ------------------------------------------------------------------
    def _benfords_law(self, hypothesis, con):
        """Test whether the first-digit distribution of a provider's
        billing amounts follows Benford's Law using a chi-squared test.
        Also detect excessive round-number billing.

        Benford's expected first-digit frequencies:
            d: log10(1 + 1/d) for d in 1..9
        """
        findings = []
        params = hypothesis.get('parameters', {})
        min_line_items = params.get('min_line_items', 100)
        chi2_threshold = params.get('chi2_threshold', 30.0)
        round_pct_threshold = params.get('round_pct_threshold', 0.50)

        try:
            from scipy.stats import chi2
            import numpy as np
        except ImportError:
            print("  scipy not available for Benford's Law")
            return findings

        # Benford's expected proportions for digits 1-9
        expected_proportions = np.array([
            math.log10(1 + 1.0 / d) for d in range(1, 10)
        ])

        # Get providers with enough line items
        providers = self._safe_query(con, """
            SELECT billing_npi, total_claims, total_paid
            FROM provider_summary
            WHERE total_claims >= ?
            ORDER BY total_paid DESC
            LIMIT 5000
        """, [min_line_items])

        for prov_npi, total_claims, total_paid in providers:
            # Get individual paid amounts for this provider
            amounts = self._safe_query(con, """
                SELECT paid
                FROM provider_hcpcs
                WHERE billing_npi = ?
                  AND paid > 0
            """, [prov_npi])

            if not amounts or len(amounts) < min_line_items:
                continue

            paid_values = [r[0] for r in amounts if r[0] is not None and r[0] > 0]
            if len(paid_values) < min_line_items:
                continue

            # --- Benford's Law chi-squared test ---
            first_digits = collections.Counter()
            for val in paid_values:
                # Extract first significant digit
                s = f"{val:.2f}".lstrip('0').lstrip('.')
                if s and s[0].isdigit() and s[0] != '0':
                    first_digits[int(s[0])] += 1

            total_digits = sum(first_digits.values())
            if total_digits < min_line_items:
                continue

            observed = np.array([first_digits.get(d, 0) for d in range(1, 10)], dtype=float)
            expected = expected_proportions * total_digits

            # Avoid division by zero
            mask = expected > 0
            if not mask.all():
                continue

            chi2_stat = np.sum((observed[mask] - expected[mask]) ** 2 / expected[mask])
            # Degrees of freedom = 8 (9 categories - 1)
            p_value = 1.0 - chi2.cdf(chi2_stat, df=8)

            benford_flagged = chi2_stat > chi2_threshold

            # --- Round-number detection ---
            round_count = 0
            for val in paid_values:
                # Check if amount is a round number (ends in 00, 000, or is whole dollar)
                if val == int(val) and val % 100 == 0:
                    round_count += 1
                elif val == int(val) and val % 10 == 0:
                    round_count += 1

            round_pct = round_count / len(paid_values) if paid_values else 0
            round_flagged = round_pct > round_pct_threshold

            if benford_flagged or round_flagged:
                flags = []
                if benford_flagged:
                    flags.append(f"Benford chi2={chi2_stat:.1f} (p={p_value:.4f})")
                if round_flagged:
                    flags.append(f"round_numbers={round_pct:.1%}")

                findings.append(self._make_finding(
                    hypothesis_id=hypothesis['id'],
                    providers=[prov_npi],
                    total_impact=round(total_paid, 2),
                    confidence=min(0.95, 0.6 + 0.1 * int(benford_flagged) + 0.15 * int(round_flagged)),
                    method_name='benfords_law',
                    evidence=(
                        f"Total items={total_digits}, total_paid=${total_paid:,.0f}. "
                        f"Flags: {'; '.join(flags)}. "
                        f"First-digit distribution: {dict(first_digits)}"
                    ),
                ))

        return findings
