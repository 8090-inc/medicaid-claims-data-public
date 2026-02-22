"""YAML-based configuration manager with validation.

Loads config.yml and provides typed access to all pipeline settings.
Supports environment-specific overrides.
"""

import os
import yaml

from config.project_config import CONFIG_DIR, PROJECT_ROOT

DEFAULT_CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config.yml')


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required fields."""


class ConfigManager:
    """Loads, validates, and provides access to pipeline configuration."""

    REQUIRED_SECTIONS = ['pipeline', 'database', 'output', 'detection']

    def __init__(self, config_path=None):
        self._config_path = config_path or DEFAULT_CONFIG_PATH
        self._config = {}
        self.load()

    def load(self):
        """Load configuration from YAML file."""
        if not os.path.exists(self._config_path):
            raise ConfigurationError(f'Configuration file not found: {self._config_path}')
        with open(self._config_path) as f:
            self._config = yaml.safe_load(f) or {}
        self._validate()

    def _validate(self):
        """Validate that all required sections are present."""
        missing = [s for s in self.REQUIRED_SECTIONS if s not in self._config]
        if missing:
            raise ConfigurationError(
                f'Missing required config sections: {", ".join(missing)}. '
                f'Check {self._config_path}'
            )

    def get(self, key_path, default=None):
        """Get a config value using dot-separated path.

        Args:
            key_path: Dot-separated key path (e.g., 'database.threads').
            default: Default value if key not found.

        Returns:
            The configuration value, or default if not found.
        """
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_section(self, section):
        """Get an entire configuration section.

        Args:
            section: Top-level section name.

        Returns:
            dict of section values, or empty dict if not found.
        """
        return self._config.get(section, {})

    @property
    def pipeline(self):
        return self._config.get('pipeline', {})

    @property
    def database(self):
        return self._config.get('database', {})

    @property
    def output(self):
        return self._config.get('output', {})

    @property
    def detection(self):
        return self._config.get('detection', {})

    @property
    def thresholds(self):
        return self._config.get('thresholds', {})

    @property
    def logging_config(self):
        return self._config.get('logging', {})

    def as_dict(self):
        """Return the full configuration as a dictionary."""
        return dict(self._config)


# Module-level singleton for convenience
_instance = None


def get_config(config_path=None):
    """Get the global ConfigManager singleton.

    Args:
        config_path: Optional path to config.yml (used on first call).

    Returns:
        ConfigManager instance.
    """
    global _instance
    if _instance is None:
        _instance = ConfigManager(config_path)
    return _instance


def reload_config(config_path=None):
    """Force reload the configuration (e.g., after editing config.yml)."""
    global _instance
    _instance = ConfigManager(config_path)
    return _instance
