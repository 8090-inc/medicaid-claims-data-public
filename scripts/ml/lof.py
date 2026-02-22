"""Local Outlier Factor (LOF) for detecting local density anomalies."""

import logging
import numpy as np

logger = logging.getLogger('medicaid_fwa.ml')


def run_lof(features, n_neighbors=20, contamination=0.05):
    """Run LOF on provider feature matrix.

    Args:
        features: numpy array of shape (n_providers, n_features).
        n_neighbors: Number of neighbors for LOF.
        contamination: Expected fraction of anomalies.

    Returns:
        dict with 'labels', 'scores', 'n_anomalies'.
    """
    from sklearn.neighbors import LocalOutlierFactor

    logger.info(f'Running LOF: {features.shape[0]} providers, k={n_neighbors}')
    model = LocalOutlierFactor(
        n_neighbors=n_neighbors,
        contamination=contamination,
        n_jobs=-1,
    )
    labels = model.fit_predict(features)
    scores = model.negative_outlier_factor_

    n_anomalies = int(np.sum(labels == -1))
    logger.info(f'  Detected {n_anomalies} anomalies')

    return {'labels': labels, 'scores': scores, 'n_anomalies': n_anomalies}
