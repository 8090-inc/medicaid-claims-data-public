"""Environment-specific configuration (dev / staging / production)."""

import os

ENVIRONMENTS = {
    'development': {
        'database': {
            'threads': 4,
            'memory_limit': '8GB',
        },
        'pipeline': {
            'max_workers': 4,
            'log_level': 'DEBUG',
        },
    },
    'staging': {
        'database': {
            'threads': 8,
            'memory_limit': '32GB',
        },
        'pipeline': {
            'max_workers': 8,
            'log_level': 'INFO',
        },
    },
    'production': {
        'database': {
            'threads': 16,
            'memory_limit': '96GB',
        },
        'pipeline': {
            'max_workers': 10,
            'log_level': 'WARNING',
        },
    },
}


def get_environment():
    """Determine the current environment from MEDICAID_ENV or default to development."""
    return os.environ.get('MEDICAID_ENV', 'development')


def get_environment_config():
    """Get configuration overrides for the current environment."""
    env = get_environment()
    return ENVIRONMENTS.get(env, ENVIRONMENTS['development'])
