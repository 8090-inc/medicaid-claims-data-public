"""Hypothesis parameter management and customization.

Provides default parameters for hypothesis generation and allows
overrides via config.yml without modifying pipeline code.
"""

DEFAULTS = {
    # Per-code hypothesis parameters
    'z_threshold': 3.0,
    'min_claims': 10,
    'min_peers': 20,
    'min_excess': 10000,

    # Hypothesis batch sizes
    'batch_size': 50,
    'total_hypotheses': 1000,

    # Category weights for prioritization
    'category_weights': {
        '1': 1.0,   # Statistical outliers
        '2': 0.9,   # Temporal anomalies
        '3': 0.85,  # Peer comparison
        '4': 0.8,   # Network analysis
        '5': 0.75,  # Concentration
        '6': 1.0,   # ML/DL
        '7': 1.0,   # Domain rules
        '8': 0.95,  # Cross-reference
        '9': 0.9,   # Financial impact
        '10': 0.85, # Composite
    },

    # Parallel execution
    'max_workers': 10,
    'timeout_per_hypothesis': 300,  # seconds
}


class HypothesisParameterManager:
    """Manages hypothesis generation and testing parameters."""

    def __init__(self, config_overrides=None):
        """Initialize with optional overrides from config.yml.

        Args:
            config_overrides: dict from config.yml 'hypotheses' section.
        """
        self._params = dict(DEFAULTS)
        if config_overrides:
            for key, value in config_overrides.items():
                if key in self._params and isinstance(self._params[key], dict) and isinstance(value, dict):
                    self._params[key].update(value)
                else:
                    self._params[key] = value

    def get(self, name, default=None):
        """Get a parameter value by name."""
        return self._params.get(name, default)

    def get_category_weight(self, category):
        """Get the weight for a hypothesis category."""
        weights = self._params.get('category_weights', {})
        return weights.get(str(category), 1.0)

    def as_dict(self):
        """Return all parameters as a dictionary."""
        return dict(self._params)
