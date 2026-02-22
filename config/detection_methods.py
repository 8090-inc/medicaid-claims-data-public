"""Detection method enable/disable configuration.

Controls which detection methods are active in the pipeline.
Methods can be toggled via config.yml without code changes.
"""

# All detection methods with their default enabled state
METHOD_REGISTRY = {
    # Statistical (Category 1)
    'z_score': {'enabled': True, 'category': '1', 'subcategory': '1A'},
    'iqr_outlier': {'enabled': True, 'category': '1', 'subcategory': '1B'},
    'gev_extreme_value': {'enabled': True, 'category': '1', 'subcategory': '1C'},
    'benfords_law': {'enabled': True, 'category': '1', 'subcategory': '1D'},
    'modified_z_score': {'enabled': True, 'category': '1', 'subcategory': '1E'},
    'percentile_rank': {'enabled': True, 'category': '1', 'subcategory': '1F'},

    # Temporal (Category 2)
    'sudden_start_stop': {'enabled': True, 'category': '2', 'subcategory': '2A'},
    'billing_spike': {'enabled': True, 'category': '2', 'subcategory': '2B'},
    'seasonal_anomaly': {'enabled': True, 'category': '2', 'subcategory': '2C'},
    'cusum_break': {'enabled': True, 'category': '2', 'subcategory': '2D'},
    'trend_divergence': {'enabled': True, 'category': '2', 'subcategory': '2E'},

    # Peer Comparison (Category 3)
    'peer_deviation': {'enabled': True, 'category': '3', 'subcategory': '3A'},
    'code_specialty_mismatch': {'enabled': True, 'category': '3', 'subcategory': '3B'},
    'geographic_outlier': {'enabled': True, 'category': '3', 'subcategory': '3C'},
    'volume_outlier': {'enabled': True, 'category': '3', 'subcategory': '3D'},

    # Network (Category 4)
    'circular_billing': {'enabled': True, 'category': '4', 'subcategory': '4A'},
    'hub_and_spoke': {'enabled': True, 'category': '4', 'subcategory': '4B'},
    'middleman_detection': {'enabled': True, 'category': '4', 'subcategory': '4C'},
    'network_anomaly': {'enabled': True, 'category': '4', 'subcategory': '4D'},

    # Concentration (Category 5)
    'gini_coefficient': {'enabled': True, 'category': '5', 'subcategory': '5A'},
    'lorenz_curve': {'enabled': True, 'category': '5', 'subcategory': '5B'},
    'herfindahl_index': {'enabled': True, 'category': '5', 'subcategory': '5C'},

    # ML/DL (Category 6)
    'isolation_forest': {'enabled': True, 'category': '6', 'subcategory': '6A'},
    'random_forest': {'enabled': True, 'category': '6', 'subcategory': '6B'},
    'xgboost': {'enabled': True, 'category': '6', 'subcategory': '6C'},
    'dbscan': {'enabled': True, 'category': '6', 'subcategory': '6D'},
    'kmeans': {'enabled': True, 'category': '6', 'subcategory': '6E'},
    'lof': {'enabled': True, 'category': '6', 'subcategory': '6F'},
    'autoencoder': {'enabled': True, 'category': '6', 'subcategory': '6G'},
    'vae': {'enabled': True, 'category': '6', 'subcategory': '6H'},
    'lstm': {'enabled': True, 'category': '6', 'subcategory': '6I'},
    'transformer': {'enabled': True, 'category': '6', 'subcategory': '6J'},

    # Domain Rules (Category 7/8)
    'impossible_volumes': {'enabled': True, 'category': '8', 'subcategory': '8A'},
    'upcoding': {'enabled': True, 'category': '8', 'subcategory': '8B'},
    'unbundling': {'enabled': True, 'category': '8', 'subcategory': '8C'},
    'phantom_billing': {'enabled': True, 'category': '8', 'subcategory': '8D'},
    'duplicate_billing': {'enabled': True, 'category': '8', 'subcategory': '8E'},

    # Cross-Reference (Category 9/10)
    'leie_exclusion': {'enabled': True, 'category': '9', 'subcategory': '9A'},
    'nppes_deactivation': {'enabled': True, 'category': '9', 'subcategory': '9B'},
    'composite_scoring': {'enabled': True, 'category': '10', 'subcategory': '10A'},
}


class DetectionMethodManager:
    """Manages which detection methods are active."""

    def __init__(self, config_overrides=None):
        """Initialize with optional overrides from config.yml.

        Args:
            config_overrides: dict mapping method_name -> bool (enabled/disabled).
        """
        self._methods = {k: dict(v) for k, v in METHOD_REGISTRY.items()}
        if config_overrides:
            for method_name, enabled in config_overrides.items():
                if method_name in self._methods:
                    self._methods[method_name]['enabled'] = bool(enabled)

    def is_enabled(self, method_name):
        """Check if a detection method is enabled."""
        method = self._methods.get(method_name)
        return method['enabled'] if method else False

    def get_enabled_methods(self, category=None):
        """Get list of enabled method names, optionally filtered by category."""
        return [
            name for name, info in self._methods.items()
            if info['enabled'] and (category is None or info['category'] == str(category))
        ]

    def get_disabled_methods(self):
        """Get list of disabled method names."""
        return [name for name, info in self._methods.items() if not info['enabled']]

    def enable(self, method_name):
        """Enable a detection method."""
        if method_name in self._methods:
            self._methods[method_name]['enabled'] = True

    def disable(self, method_name):
        """Disable a detection method."""
        if method_name in self._methods:
            self._methods[method_name]['enabled'] = False

    def as_dict(self):
        """Return all methods and their status."""
        return {name: info['enabled'] for name, info in self._methods.items()}
