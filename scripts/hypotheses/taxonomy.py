"""Hypothesis category and subcategory definitions.

Defines the 10-category taxonomy for fraud hypotheses.
"""

CATEGORIES = {
    '1': {
        'name': 'Statistical Outlier Detection',
        'subcategories': {
            '1A': 'Paid-per-claim Z-score outliers',
            '1B': 'IQR-based outliers',
            '1C': 'Generalized Extreme Value (GEV) outliers',
            '1D': "Benford's Law digit distribution anomalies",
            '1E': 'Modified Z-score outliers',
            '1F': 'Percentile rank extremes',
        },
    },
    '2': {
        'name': 'Temporal Anomaly Detection',
        'subcategories': {
            '2A': 'Sudden activity start/stop patterns',
            '2B': 'Billing spike detection',
            '2C': 'Seasonal anomaly detection',
            '2D': 'CUSUM structural break detection',
            '2E': 'Trend divergence from peers',
        },
    },
    '3': {
        'name': 'Peer Comparison Analysis',
        'subcategories': {
            '3A': 'Peer group deviation (same specialty)',
            '3B': 'Code-specialty mismatch detection',
            '3C': 'Geographic outlier detection',
            '3D': 'Volume outlier vs. peer median',
        },
    },
    '4': {
        'name': 'Network Analysis',
        'subcategories': {
            '4A': 'Circular billing detection',
            '4B': 'Hub-and-spoke topology detection',
            '4C': 'Middleman/pass-through detection',
            '4D': 'Network centrality anomalies',
        },
    },
    '5': {
        'name': 'Concentration Analysis',
        'subcategories': {
            '5A': 'Gini coefficient (revenue concentration)',
            '5B': 'Lorenz curve analysis',
            '5C': 'Herfindahl-Hirschman Index (HHI)',
        },
    },
    '6': {
        'name': 'ML/DL Anomaly Detection',
        'subcategories': {
            '6A': 'Isolation Forest',
            '6B': 'Random Forest feature importance',
            '6C': 'XGBoost anomaly scoring',
            '6D': 'DBSCAN clustering',
            '6E': 'K-Means clustering',
            '6F': 'Local Outlier Factor (LOF)',
            '6G': 'Autoencoder reconstruction error',
            '6H': 'Variational Autoencoder (VAE)',
            '6I': 'LSTM temporal anomaly',
            '6J': 'Transformer attention anomaly',
        },
    },
    '7': {
        'name': 'Cross-Reference Validation',
        'subcategories': {
            '7A': 'LEIE exclusion list matching',
            '7B': 'NPPES deactivation check',
        },
    },
    '8': {
        'name': 'Domain-Specific Rules',
        'subcategories': {
            '8A': 'Impossible service volumes',
            '8B': 'E&M upcoding detection',
            '8C': 'Unbundling detection',
            '8D': 'Phantom billing (after deactivation)',
            '8E': 'Duplicate billing detection',
        },
    },
    '9': {
        'name': 'Financial Impact Assessment',
        'subcategories': {
            '9A': 'Excess payment calculation',
            '9B': 'Deduplication and consolidation',
        },
    },
    '10': {
        'name': 'Composite Scoring',
        'subcategories': {
            '10A': 'Multi-method composite risk score',
        },
    },
}


def get_category_name(category_id):
    """Get the name for a category ID."""
    cat = CATEGORIES.get(str(category_id))
    return cat['name'] if cat else f'Category {category_id}'


def get_subcategory_description(category_id, subcategory_id):
    """Get the description for a subcategory."""
    cat = CATEGORIES.get(str(category_id))
    if cat:
        return cat['subcategories'].get(subcategory_id, subcategory_id)
    return subcategory_id
