#!/usr/bin/env python3
"""Category 2: Temporal Pattern Analysis.

Implements subcategories 2A-2H for detecting time-based anomalies
in provider billing behavior.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analyzers.base_analyzer import BaseAnalyzer


class TemporalAnalyzer(BaseAnalyzer):
    """Detects temporal anomalies in provider billing patterns."""

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
            '2A': self._month_over_month_spike,
            '2B': self._ramp_up,
            '2C': self._abrupt_stop,
            '2D': self._yoy_growth,
            '2E': self._seasonality_anomaly,
            '2F': self._covid_comparison,
            '2G': self._december_spike,
            '2H': self._change_point_detection,
        }
        handler = dispatch.get(subcategory)
        if handler is None:
            print(f"  Unknown subcategory: {subcategory}")
            return []
        return handler(hypothesis, con)

    # ------------------------------------------------------------------
    # 2A: Month-over-month spike detection
    # ------------------------------------------------------------------
    def _month_over_month_spike(self, hypothesis, con):
        """Compare consecutive months using a LAG window function.
        Flag providers where the ratio of current month to previous month
        exceeds a threshold and both months exceed a minimum paid amount.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        ratio_threshold = params.get('ratio_threshold', 3.0)
        min_monthly_paid = params.get('min_monthly_paid', 10000)

        rows = self._safe_query(con, """
            WITH monthly_lag AS (
                SELECT
                    billing_npi,
                    claim_month,
                    paid,
                    LAG(paid) OVER (PARTITION BY billing_npi ORDER BY claim_month) AS prev_paid,
                    LAG(claim_month) OVER (PARTITION BY billing_npi ORDER BY claim_month) AS prev_month
                FROM provider_monthly
            )
            SELECT
                billing_npi,
                claim_month,
                paid,
                prev_paid,
                prev_month,
                paid / NULLIF(prev_paid, 0) AS ratio
            FROM monthly_lag
            WHERE prev_paid IS NOT NULL
              AND prev_paid > ?
              AND paid > ?
              AND paid / NULLIF(prev_paid, 0) > ?
            ORDER BY ratio DESC
            LIMIT 2000
        """, [min_monthly_paid, min_monthly_paid, ratio_threshold])

        for row in rows:
            npi, month, paid, prev_paid, prev_month, ratio = row
            spike_amount = paid - prev_paid
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(spike_amount, 2),
                confidence=min(0.95, 0.6 + 0.05 * min(ratio - ratio_threshold, 7)),
                method_name='month_over_month_spike',
                evidence=(
                    f"Month {month}: ${paid:,.0f} vs prev {prev_month}: "
                    f"${prev_paid:,.0f} (ratio={ratio:.1f}x, "
                    f"increase=${spike_amount:,.0f})"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 2B: Ramp-up / first-month anomaly
    # ------------------------------------------------------------------
    def _ramp_up(self, hypothesis, con):
        """Check the first month of billing in provider_summary.
        Flag providers whose first-month paid exceeds a threshold,
        indicating unusually high initial billing.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        first_month_threshold = params.get('first_month_threshold', 50000)
        min_total_paid = params.get('min_total_paid', 100000)

        rows = self._safe_query(con, """
            SELECT
                ps.billing_npi,
                ps.first_month,
                ps.total_paid,
                ps.total_claims,
                ps.num_months,
                pm.paid AS first_month_paid,
                pm.claims AS first_month_claims
            FROM provider_summary ps
            JOIN provider_monthly pm
                ON ps.billing_npi = pm.billing_npi
                AND ps.first_month = pm.claim_month
            WHERE pm.paid > ?
              AND ps.total_paid > ?
            ORDER BY pm.paid DESC
            LIMIT 1000
        """, [first_month_threshold, min_total_paid])

        for row in rows:
            npi, first_month, total_paid, total_claims, num_months, fm_paid, fm_claims = row
            # Compare first month to average monthly for the provider
            avg_monthly = total_paid / max(num_months, 1)
            if avg_monthly > 0 and fm_paid > avg_monthly * 2:
                ratio = fm_paid / avg_monthly
                findings.append(self._make_finding(
                    hypothesis_id=hypothesis['id'],
                    providers=[npi],
                    total_impact=round(fm_paid, 2),
                    confidence=min(0.90, 0.6 + 0.05 * min(ratio - 1, 6)),
                    method_name='ramp_up',
                    evidence=(
                        f"First month {first_month}: ${fm_paid:,.0f} "
                        f"(claims={fm_claims}), avg monthly=${avg_monthly:,.0f}, "
                        f"ratio={ratio:.1f}x, total months={num_months}"
                    ),
                ))

        return findings

    # ------------------------------------------------------------------
    # 2C: Abrupt stop detection
    # ------------------------------------------------------------------
    def _abrupt_stop(self, hypothesis, con):
        """Flag providers who were active for 12+ months with significant
        average billing, then abruptly stopped (last_month well before
        the most recent month in the dataset).
        """
        findings = []
        params = hypothesis.get('parameters', {})
        min_months_active = params.get('min_months_active', 12)
        min_avg_monthly = params.get('min_avg_monthly', 20000)
        months_before_end = params.get('months_before_end', 6)

        # Find the maximum month in the dataset
        max_month_result = self._safe_query(con, """
            SELECT MAX(claim_month) FROM provider_monthly
        """)
        if not max_month_result or max_month_result[0][0] is None:
            return findings
        dataset_max_month = max_month_result[0][0]

        # Compute the cutoff month: months_before_end months before dataset end
        cutoff_result = self._safe_query(con, f"""
            SELECT strftime(
                CAST('{dataset_max_month}-01' AS DATE) - INTERVAL '{months_before_end}' MONTH,
                '%Y-%m'
            )
        """)
        if not cutoff_result or cutoff_result[0][0] is None:
            return findings
        cutoff_month = cutoff_result[0][0]

        rows = self._safe_query(con, """
            SELECT
                billing_npi,
                num_months,
                total_paid,
                total_claims,
                first_month,
                last_month,
                total_paid / NULLIF(num_months, 0) AS avg_monthly
            FROM provider_summary
            WHERE num_months >= ?
              AND total_paid / NULLIF(num_months, 0) >= ?
              AND last_month < ?
            ORDER BY total_paid DESC
            LIMIT 1000
        """, [min_months_active, min_avg_monthly, cutoff_month])

        for row in rows:
            npi, num_months, total_paid, total_claims, first_month, last_month, avg_monthly = row
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(total_paid, 2),
                confidence=min(0.85, 0.6 + 0.02 * num_months),
                method_name='abrupt_stop',
                evidence=(
                    f"Active {first_month} to {last_month} ({num_months} months), "
                    f"avg monthly=${avg_monthly:,.0f}, total=${total_paid:,.0f}. "
                    f"Stopped {months_before_end}+ months before dataset end ({dataset_max_month})"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 2D: Year-over-year growth
    # ------------------------------------------------------------------
    def _yoy_growth(self, hypothesis, con):
        """Compare total paid by year for each provider. Flag if
        year-over-year growth exceeds a threshold.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        growth_threshold = params.get('growth_threshold', 2.0)
        min_base_year = params.get('min_base_year', 50000)
        min_total_paid = params.get('min_total_paid', 100000)

        rows = self._safe_query(con, """
            WITH yearly AS (
                SELECT
                    billing_npi,
                    LEFT(claim_month, 4) AS year,
                    SUM(paid) AS year_paid
                FROM provider_monthly
                GROUP BY billing_npi, LEFT(claim_month, 4)
            ),
            yoy AS (
                SELECT
                    y1.billing_npi,
                    y1.year AS base_year,
                    y2.year AS growth_year,
                    y1.year_paid AS base_paid,
                    y2.year_paid AS growth_paid,
                    y2.year_paid / NULLIF(y1.year_paid, 0) AS growth_ratio,
                    y2.year_paid - y1.year_paid AS growth_amount
                FROM yearly y1
                JOIN yearly y2
                    ON y1.billing_npi = y2.billing_npi
                    AND CAST(y2.year AS INTEGER) = CAST(y1.year AS INTEGER) + 1
                WHERE y1.year_paid > ?
            )
            SELECT
                yoy.billing_npi,
                yoy.base_year,
                yoy.growth_year,
                yoy.base_paid,
                yoy.growth_paid,
                yoy.growth_ratio,
                yoy.growth_amount,
                ps.total_paid
            FROM yoy
            JOIN provider_summary ps ON yoy.billing_npi = ps.billing_npi
            WHERE yoy.growth_ratio > ?
              AND ps.total_paid > ?
            ORDER BY yoy.growth_amount DESC
            LIMIT 2000
        """, [min_base_year, growth_threshold, min_total_paid])

        for row in rows:
            npi, base_yr, growth_yr, base_paid, growth_paid, ratio, amount, total_paid = row
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(amount, 2),
                confidence=min(0.95, 0.6 + 0.05 * min(ratio - growth_threshold, 7)),
                method_name='yoy_growth',
                evidence=(
                    f"{base_yr}: ${base_paid:,.0f} -> {growth_yr}: ${growth_paid:,.0f} "
                    f"(growth={ratio:.1f}x, increase=${amount:,.0f}, "
                    f"total lifetime=${total_paid:,.0f})"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 2E: Seasonality anomaly / artificial smoothing
    # ------------------------------------------------------------------
    def _seasonality_anomaly(self, hypothesis, con):
        """Compute monthly coefficients of variation (CV) per provider.
        Flag if CV is extremely low (artificial smoothing suggesting
        fabricated data) or if the pattern violates expected seasonality.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        max_cv_for_flag = params.get('max_cv_for_flag', 0.05)
        min_months = params.get('min_months', 12)
        min_total_paid = params.get('min_total_paid', 200000)

        # Get providers with enough history
        rows = self._safe_query(con, """
            WITH monthly_stats AS (
                SELECT
                    billing_npi,
                    COUNT(*) AS num_months,
                    AVG(paid) AS avg_paid,
                    STDDEV(paid) AS std_paid,
                    SUM(paid) AS total_paid
                FROM provider_monthly
                GROUP BY billing_npi
                HAVING COUNT(*) >= ?
                   AND AVG(paid) > 0
                   AND SUM(paid) >= ?
            )
            SELECT
                billing_npi,
                num_months,
                avg_paid,
                std_paid,
                total_paid,
                std_paid / NULLIF(avg_paid, 0) AS cv
            FROM monthly_stats
            WHERE std_paid / NULLIF(avg_paid, 0) < ?
              AND std_paid / NULLIF(avg_paid, 0) IS NOT NULL
            ORDER BY total_paid DESC
            LIMIT 1000
        """, [min_months, min_total_paid, max_cv_for_flag])

        for row in rows:
            npi, num_months, avg_paid, std_paid, total_paid, cv = row
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(total_paid, 2),
                confidence=min(0.90, 0.7 + 0.1 * (max_cv_for_flag - cv) / max(max_cv_for_flag, 0.001)),
                method_name='seasonality_anomaly_low_cv',
                evidence=(
                    f"CV={cv:.4f} (threshold={max_cv_for_flag}), "
                    f"avg_monthly=${avg_paid:,.0f}, std=${std_paid:,.0f}, "
                    f"months={num_months}, total=${total_paid:,.0f}. "
                    f"Suspiciously uniform billing pattern."
                ),
            ))

        # Also detect high-seasonality anomaly: single month dominates
        params_high_cv = hypothesis.get('parameters', {})
        max_month_share = params_high_cv.get('max_month_share', 0.60)

        high_season_rows = self._safe_query(con, """
            WITH monthly_totals AS (
                SELECT
                    billing_npi,
                    claim_month,
                    paid,
                    SUM(paid) OVER (PARTITION BY billing_npi) AS annual_total,
                    COUNT(*) OVER (PARTITION BY billing_npi) AS num_months
                FROM provider_monthly
            )
            SELECT
                billing_npi,
                claim_month,
                paid,
                annual_total,
                paid / NULLIF(annual_total, 0) AS month_share,
                num_months
            FROM monthly_totals
            WHERE num_months >= ?
              AND annual_total >= ?
              AND paid / NULLIF(annual_total, 0) > ?
            ORDER BY paid DESC
            LIMIT 1000
        """, [min_months, min_total_paid, max_month_share])

        for row in high_season_rows:
            npi, month, paid, annual_total, share, num_months = row
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(paid, 2),
                confidence=min(0.85, 0.6 + 0.2 * share),
                method_name='seasonality_anomaly_concentration',
                evidence=(
                    f"Month {month}: ${paid:,.0f} = {share:.1%} of "
                    f"total ${annual_total:,.0f} over {num_months} months. "
                    f"Abnormal concentration."
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 2F: COVID period comparison
    # ------------------------------------------------------------------
    def _covid_comparison(self, hypothesis, con):
        """Compare COVID period (2020-03 to 2021-12) vs pre-COVID (2019)
        billing totals. Flag providers with significant increases during
        COVID that may indicate opportunistic fraud.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        growth_threshold = params.get('growth_threshold', 3.0)
        min_pre_covid = params.get('min_pre_covid', 50000)

        rows = self._safe_query(con, """
            WITH pre_covid AS (
                SELECT
                    billing_npi,
                    SUM(paid) AS pre_paid,
                    SUM(claims) AS pre_claims,
                    COUNT(DISTINCT claim_month) AS pre_months
                FROM provider_monthly
                WHERE claim_month >= '2019-01' AND claim_month <= '2019-12'
                GROUP BY billing_npi
                HAVING SUM(paid) > ?
            ),
            covid AS (
                SELECT
                    billing_npi,
                    SUM(paid) AS covid_paid,
                    SUM(claims) AS covid_claims,
                    COUNT(DISTINCT claim_month) AS covid_months
                FROM provider_monthly
                WHERE claim_month >= '2020-03' AND claim_month <= '2021-12'
                GROUP BY billing_npi
            )
            SELECT
                pre.billing_npi,
                pre.pre_paid,
                pre.pre_months,
                covid.covid_paid,
                covid.covid_months,
                -- Annualize for fair comparison
                (covid.covid_paid / NULLIF(covid.covid_months, 0)) /
                NULLIF(pre.pre_paid / NULLIF(pre.pre_months, 0), 0) AS monthly_ratio,
                covid.covid_paid - pre.pre_paid AS absolute_increase
            FROM pre_covid pre
            JOIN covid ON pre.billing_npi = covid.billing_npi
            WHERE covid.covid_months >= 6
              AND (covid.covid_paid / NULLIF(covid.covid_months, 0)) /
                  NULLIF(pre.pre_paid / NULLIF(pre.pre_months, 0), 0) > ?
            ORDER BY absolute_increase DESC
            LIMIT 1000
        """, [min_pre_covid, growth_threshold])

        for row in rows:
            npi, pre_paid, pre_months, covid_paid, covid_months, ratio, increase = row
            pre_monthly = pre_paid / max(pre_months, 1)
            covid_monthly = covid_paid / max(covid_months, 1)
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(increase, 2),
                confidence=min(0.90, 0.6 + 0.05 * min(ratio - growth_threshold, 6)),
                method_name='covid_comparison',
                evidence=(
                    f"Pre-COVID (2019): ${pre_paid:,.0f} over {pre_months} months "
                    f"(${pre_monthly:,.0f}/mo). "
                    f"COVID (2020-03 to 2021-12): ${covid_paid:,.0f} over {covid_months} months "
                    f"(${covid_monthly:,.0f}/mo). "
                    f"Monthly ratio={ratio:.1f}x, increase=${increase:,.0f}"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 2G: December billing spike
    # ------------------------------------------------------------------
    def _december_spike(self, hypothesis, con):
        """Compare December billing to the provider's monthly average.
        Year-end spikes may indicate rushed billing to meet targets or
        fraudulent end-of-year submissions.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        dec_ratio_threshold = params.get('dec_ratio_threshold', 2.5)
        min_avg_monthly = params.get('min_avg_monthly', 10000)
        min_dec_paid = params.get('min_dec_paid', 30000)

        rows = self._safe_query(con, """
            WITH provider_avg AS (
                SELECT
                    billing_npi,
                    AVG(paid) AS avg_monthly,
                    COUNT(*) AS num_months
                FROM provider_monthly
                GROUP BY billing_npi
                HAVING COUNT(*) >= 6
                   AND AVG(paid) >= ?
            ),
            dec_months AS (
                SELECT
                    billing_npi,
                    claim_month,
                    paid
                FROM provider_monthly
                WHERE claim_month LIKE '%-12'
                  AND paid >= ?
            )
            SELECT
                d.billing_npi,
                d.claim_month,
                d.paid AS dec_paid,
                pa.avg_monthly,
                pa.num_months,
                d.paid / NULLIF(pa.avg_monthly, 0) AS dec_ratio
            FROM dec_months d
            JOIN provider_avg pa ON d.billing_npi = pa.billing_npi
            WHERE d.paid / NULLIF(pa.avg_monthly, 0) > ?
            ORDER BY d.paid DESC
            LIMIT 1000
        """, [min_avg_monthly, min_dec_paid, dec_ratio_threshold])

        for row in rows:
            npi, month, dec_paid, avg_monthly, num_months, ratio = row
            excess = dec_paid - avg_monthly
            findings.append(self._make_finding(
                hypothesis_id=hypothesis['id'],
                providers=[npi],
                total_impact=round(excess, 2),
                confidence=min(0.85, 0.6 + 0.05 * min(ratio - dec_ratio_threshold, 5)),
                method_name='december_spike',
                evidence=(
                    f"December {month}: ${dec_paid:,.0f} vs avg monthly "
                    f"${avg_monthly:,.0f} (ratio={ratio:.1f}x, "
                    f"excess=${excess:,.0f}, months={num_months})"
                ),
            ))

        return findings

    # ------------------------------------------------------------------
    # 2H: Change-point detection (CUSUM)
    # ------------------------------------------------------------------
    def _change_point_detection(self, hypothesis, con):
        """Detect change points in provider monthly billing series using
        either the ruptures library (if available) or a manual CUSUM
        algorithm. A change point indicates a structural shift in billing
        behavior.
        """
        findings = []
        params = hypothesis.get('parameters', {})
        min_months = params.get('min_months', 18)
        min_total_paid = params.get('min_total_paid', 200000)
        cusum_threshold = params.get('cusum_threshold', 5.0)
        max_providers = params.get('max_providers', 2000)

        # Select candidate providers
        providers = self._safe_query(con, """
            SELECT billing_npi, total_paid, num_months
            FROM provider_summary
            WHERE num_months >= ?
              AND total_paid >= ?
            ORDER BY total_paid DESC
            LIMIT ?
        """, [min_months, min_total_paid, max_providers])

        use_ruptures = False
        try:
            import ruptures
            use_ruptures = True
        except ImportError:
            pass

        try:
            import numpy as np
        except ImportError:
            print("  numpy not available for change-point detection")
            return findings

        for prov_npi, prov_total_paid, prov_num_months in providers:
            monthly_data = self._safe_query(con, """
                SELECT claim_month, paid
                FROM provider_monthly
                WHERE billing_npi = ?
                ORDER BY claim_month
            """, [prov_npi])

            if not monthly_data or len(monthly_data) < min_months:
                continue

            months = [r[0] for r in monthly_data]
            paid_series = np.array([r[1] for r in monthly_data], dtype=float)

            if np.std(paid_series) == 0:
                continue

            change_points = []

            if use_ruptures:
                # Use ruptures for Pelt change-point detection
                try:
                    model = ruptures.Pelt(model="rbf", min_size=3).fit(paid_series)
                    result = model.predict(pen=10)
                    # result contains change point indices (1-indexed, last is len)
                    change_points = [idx for idx in result if idx < len(paid_series)]
                except Exception:
                    # Fall through to CUSUM
                    use_ruptures = False

            if not use_ruptures or not change_points:
                # Manual CUSUM algorithm
                mean_val = np.mean(paid_series)
                std_val = np.std(paid_series)
                if std_val == 0:
                    continue

                normalized = (paid_series - mean_val) / std_val
                cusum_pos = np.zeros(len(normalized))
                cusum_neg = np.zeros(len(normalized))

                for i in range(1, len(normalized)):
                    cusum_pos[i] = max(0, cusum_pos[i - 1] + normalized[i] - 0.5)
                    cusum_neg[i] = max(0, cusum_neg[i - 1] - normalized[i] - 0.5)

                # Find points where CUSUM exceeds threshold
                for i in range(1, len(cusum_pos)):
                    if (cusum_pos[i] > cusum_threshold and cusum_pos[i - 1] <= cusum_threshold):
                        change_points.append(i)
                    if (cusum_neg[i] > cusum_threshold and cusum_neg[i - 1] <= cusum_threshold):
                        change_points.append(i)

            if not change_points:
                continue

            # Analyze each change point
            for cp_idx in change_points:
                if cp_idx <= 2 or cp_idx >= len(paid_series) - 1:
                    continue

                before_mean = np.mean(paid_series[:cp_idx])
                after_mean = np.mean(paid_series[cp_idx:])

                if before_mean == 0:
                    continue

                shift_ratio = after_mean / before_mean
                shift_amount = (after_mean - before_mean) * (len(paid_series) - cp_idx)

                # Only flag significant shifts
                if abs(shift_ratio - 1.0) < 0.5:
                    continue

                cp_month = months[min(cp_idx, len(months) - 1)]
                method_used = 'ruptures_pelt' if use_ruptures else 'cusum'

                findings.append(self._make_finding(
                    hypothesis_id=hypothesis['id'],
                    providers=[prov_npi],
                    total_impact=round(abs(shift_amount), 2),
                    confidence=min(0.85, 0.6 + 0.05 * min(abs(shift_ratio - 1.0) * 2, 5)),
                    method_name=f'change_point_{method_used}',
                    evidence=(
                        f"Change point at {cp_month} (index {cp_idx}): "
                        f"before avg=${before_mean:,.0f}, after avg=${after_mean:,.0f}, "
                        f"shift_ratio={shift_ratio:.2f}x, "
                        f"estimated impact=${abs(shift_amount):,.0f}, "
                        f"method={method_used}"
                    ),
                ))

                # Only report the most significant change point per provider
                break

        return findings
