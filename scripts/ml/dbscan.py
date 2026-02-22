"""DBSCAN clustering for identifying anomalous provider groups."""

import logging
import numpy as np

logger = logging.getLogger('medicaid_fwa.ml')


def run_dbscan(features, eps=0.5, min_samples=10):
    """Run DBSCAN clustering on provider feature matrix.

    Args:
        features: numpy array of shape (n_providers, n_features).
        eps: Maximum distance between neighbors.
        min_samples: Minimum samples in a neighborhood.

    Returns:
        dict with 'labels' (cluster IDs, -1 for noise), 'n_clusters', 'n_noise'.
    """
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler

    logger.info(f'Running DBSCAN: {features.shape[0]} providers')
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    model = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=-1)
    labels = model.fit_predict(scaled)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = int(np.sum(labels == -1))
    logger.info(f'  {n_clusters} clusters, {n_noise} noise points')

    return {'labels': labels, 'n_clusters': n_clusters, 'n_noise': n_noise}
