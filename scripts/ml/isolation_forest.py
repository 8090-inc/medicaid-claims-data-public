"""Isolation Forest anomaly detection for provider billing patterns."""

import logging
import numpy as np

logger = logging.getLogger('medicaid_fwa.ml')


def run_isolation_forest(features, contamination=0.05, n_estimators=200, random_state=42):
    """Run Isolation Forest on provider feature matrix.

    Args:
        features: numpy array of shape (n_providers, n_features).
        contamination: Expected fraction of anomalies.
        n_estimators: Number of trees.
        random_state: Random seed.

    Returns:
        dict with 'labels' (-1 for anomaly, 1 for normal), 'scores' (anomaly scores).
    """
    from sklearn.ensemble import IsolationForest

    logger.info(f'Running Isolation Forest: {features.shape[0]} providers, {features.shape[1]} features')
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    labels = model.fit_predict(features)
    scores = model.decision_function(features)

    n_anomalies = int(np.sum(labels == -1))
    logger.info(f'  Detected {n_anomalies} anomalies ({n_anomalies / len(labels) * 100:.1f}%)')

    return {'labels': labels, 'scores': scores, 'n_anomalies': n_anomalies}
