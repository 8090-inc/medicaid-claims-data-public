"""Statistical threshold configuration for detection methods.

All detection thresholds are configurable via config.yml under the
'thresholds' section. This module provides typed access with defaults.
"""

# ── Default thresholds (used when config.yml values are absent) ─────────

DEFAULTS = {
    # Z-score thresholds
    'z_score_high': 3.0,
    'z_score_medium': 2.5,
    'z_score_low': 2.0,

    # IQR multipliers
    'iqr_multiplier_high': 3.0,
    'iqr_multiplier_medium': 1.5,

    # Minimum sample sizes
    'min_claims': 10,
    'min_peers': 20,
    'min_excess_amount': 10000,

    # Confidence tier boundaries
    'confidence_high': 0.8,
    'confidence_medium': 0.5,
    'confidence_low': 0.2,

    # Temporal detection
    'cusum_threshold': 5.0,
    'spike_multiplier': 3.0,
    'sudden_start_min_months': 3,

    # Network detection
    'hub_min_connections': 10,
    'circular_min_cycle_length': 3,

    # Concentration detection
    'gini_high_threshold': 0.8,
    'hhi_high_threshold': 0.25,

    # Financial impact
    'prune_min_flagged': 50,
    'prune_holdout_rate_mult': 0.5,
    'prune_z_delta': -0.5,
}


class ThresholdManager:
    """Provides access to statistical thresholds with config overrides."""

    def __init__(self, config_overrides=None):
        """Initialize with optional overrides from config.yml.

        Args:
            config_overrides: dict from config.yml 'thresholds' section.
        """
        self._thresholds = dict(DEFAULTS)
        if config_overrides:
            self._thresholds.update(config_overrides)

    def get(self, name, default=None):
        """Get a threshold value by name.

        Args:
            name: Threshold name (e.g., 'z_score_high').
            default: Fallback if name not found.

        Returns:
            Threshold value (float/int).
        """
        return self._thresholds.get(name, default)

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        if name in self._thresholds:
            return self._thresholds[name]
        raise AttributeError(f'Unknown threshold: {name}')

    def as_dict(self):
        """Return all thresholds as a dictionary."""
        return dict(self._thresholds)
