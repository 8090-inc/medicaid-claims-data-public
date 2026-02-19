#!/usr/bin/env python3
"""Milestone 6: ML and Deep Learning anomaly detection.

Trains Isolation Forest, DBSCAN, LOF, K-means, XGBoost, Autoencoder, VAE, LSTM,
and Transformer models on provider feature vectors. Extracts top anomalies as findings.
"""

import json
import os
import sys
import time
import warnings
import numpy as np

warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.db_utils import get_connection, format_dollars

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINDINGS_DIR = os.path.join(PROJECT_ROOT, 'output', 'findings')
MODELS_DIR = os.path.join(PROJECT_ROOT, 'models')
HYPOTHESES_PATH = os.path.join(PROJECT_ROOT, 'output', 'hypotheses', 'all_hypotheses.json')
PRIOR_FINDINGS = os.path.join(FINDINGS_DIR, 'categories_1_to_5.json')


def load_feature_matrix(con):
    """Extract provider feature matrix from DuckDB."""
    print("Extracting provider feature matrix ...")
    rows = con.execute("""
        SELECT
            ps.billing_npi,
            ps.total_paid,
            ps.total_claims,
            ps.total_beneficiaries,
            ps.num_codes,
            ps.num_months,
            ps.avg_paid_per_claim,
            ps.avg_claims_per_bene,
            COALESCE(ps.total_paid / NULLIF(ps.total_beneficiaries, 0), 0) AS avg_paid_per_bene,
            -- max single month
            COALESCE(mm.max_month_paid, 0) AS max_single_month_paid,
            -- coefficient of variation
            COALESCE(mm.cv_monthly, 0) AS cv_monthly,
            -- percent from top code
            COALESCE(tc.top_code_pct, 0) AS pct_revenue_top_code,
            -- network features
            COALESCE(net.num_servicing, 0) AS num_servicing_npis,
            COALESCE(net.pct_self_billing, 0) AS pct_self_billing,
            -- temporal span
            ps.num_months AS months_active,
            -- growth (last year vs first year)
            COALESCE(gr.yoy_growth, 0) AS yoy_growth
        FROM provider_summary ps
        LEFT JOIN (
            SELECT billing_npi,
                   MAX(paid) AS max_month_paid,
                   CASE WHEN AVG(paid) > 0 THEN STDDEV(paid) / AVG(paid) ELSE 0 END AS cv_monthly
            FROM provider_monthly
            GROUP BY billing_npi
        ) mm ON ps.billing_npi = mm.billing_npi
        LEFT JOIN (
            SELECT billing_npi,
                   MAX(paid) * 100.0 / NULLIF(SUM(paid), 0) AS top_code_pct
            FROM provider_hcpcs
            GROUP BY billing_npi
        ) tc ON ps.billing_npi = tc.billing_npi
        LEFT JOIN (
            SELECT billing_npi,
                   COUNT(DISTINCT servicing_npi) AS num_servicing,
                   SUM(CASE WHEN billing_npi = servicing_npi THEN total_paid ELSE 0 END) * 100.0
                       / NULLIF(SUM(total_paid), 0) AS pct_self_billing
            FROM billing_servicing_network
            GROUP BY billing_npi
        ) net ON ps.billing_npi = net.billing_npi
        LEFT JOIN (
            SELECT billing_npi,
                   CASE WHEN SUM(CASE WHEN claim_month < '2020-01' THEN paid ELSE 0 END) > 0
                        THEN (SUM(CASE WHEN claim_month >= '2023-01' THEN paid ELSE 0 END)
                              / NULLIF(SUM(CASE WHEN claim_month < '2020-01' THEN paid ELSE 0 END), 0)) - 1
                        ELSE 0 END AS yoy_growth
            FROM provider_monthly
            GROUP BY billing_npi
        ) gr ON ps.billing_npi = gr.billing_npi
        WHERE ps.total_paid > 0 AND ps.total_claims > 0
    """).fetchall()

    npis = [r[0] for r in rows]
    features = np.array([[float(v) if v is not None else 0.0 for v in r[1:]] for r in rows], dtype=np.float64)

    # Replace inf/nan
    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

    feature_names = [
        'total_paid', 'total_claims', 'total_beneficiaries', 'num_codes',
        'num_months', 'avg_paid_per_claim', 'avg_claims_per_bene', 'avg_paid_per_bene',
        'max_single_month_paid', 'cv_monthly', 'pct_revenue_top_code',
        'num_servicing_npis', 'pct_self_billing', 'months_active', 'yoy_growth'
    ]

    print(f"  Feature matrix: {features.shape[0]} providers x {features.shape[1]} features")
    return npis, features, feature_names


def get_prior_flagged_npis():
    """Load NPIs already flagged by Categories 1-5."""
    flagged = set()
    if os.path.exists(PRIOR_FINDINGS):
        with open(PRIOR_FINDINGS) as f:
            findings = json.load(f)
        for finding in findings:
            for p in finding.get('flagged_providers', []):
                if isinstance(p, dict):
                    npi = p.get('npi', '')
                else:
                    npi = str(p)
                if npi:
                    flagged.add(npi)
    return flagged


def make_finding(hypothesis_id, npi, paid, score, method, evidence, confidence='medium'):
    return {
        'hypothesis_id': hypothesis_id,
        'flagged_providers': [{'npi': npi, 'amount': paid, 'score': float(score), 'evidence': evidence}],
        'total_impact': paid,
        'confidence': confidence,
        'method_name': method,
        'evidence': evidence,
    }


def run_isolation_forest(npis, X, X_scaled, paid, feature_names, prior_flagged):
    """Category 6A: Isolation Forest anomaly detection."""
    from sklearn.ensemble import IsolationForest
    import joblib

    print("\n--- Isolation Forest ---")
    findings = []
    iso_model = None

    segments = [
        ('overall', np.ones(len(npis), dtype=bool), 'H0601', 10),
        ('home_health_high', paid > 100000, 'H0611', 10),
        ('behavioral_high', paid > 100000, 'H0621', 10),
        ('high_volume', paid > 1000000, 'H0631', 10),
    ]

    for seg_name, mask, base_id, n_findings in segments:
        if mask.sum() < 100:
            continue
        X_seg = X_scaled[mask]
        npis_seg = [npis[i] for i in range(len(npis)) if mask[i]]
        paid_seg = paid[mask]

        iso = IsolationForest(contamination=0.01, n_estimators=200, random_state=42, n_jobs=-1)
        scores = iso.fit_predict(X_seg)
        anomaly_scores = -iso.score_samples(X_seg)
        iso_model = iso

        # Get top anomalies
        anomaly_idx = np.where(scores == -1)[0]
        if len(anomaly_idx) == 0:
            continue
        top_idx = anomaly_idx[np.argsort(-anomaly_scores[anomaly_idx])[:n_findings]]

        for rank, idx in enumerate(top_idx):
            npi = npis_seg[idx]
            h_id = f"{base_id[:-2]}{rank+1:02d}" if rank < 9 else f"{base_id[:-2]}{rank+1:02d}"
            h_id = f"H{int(base_id[1:]) + rank:04d}"

            # Find which features are most anomalous
            feat_z = np.abs(X_seg[idx])
            top_feats = np.argsort(-feat_z)[:3]
            evidence = f"IsolationForest {seg_name}: anomaly_score={anomaly_scores[idx]:.3f}, " \
                       f"top_features=[{', '.join(feature_names[fi] for fi in top_feats)}]"

            confidence = 'high' if anomaly_scores[idx] > 0.7 and paid_seg[idx] > 500000 else 'medium'
            findings.append(make_finding(h_id, npi, float(paid_seg[idx]),
                                         float(anomaly_scores[idx]), 'isolation_forest', evidence, confidence))

    # Save model if at least one segment was fit
    if iso_model is not None:
        joblib.dump(iso_model, os.path.join(MODELS_DIR, 'isolation_forest.joblib'))
    print(f"  Isolation Forest: {len(findings)} findings")
    return findings


def run_dbscan(npis, X_scaled, paid, feature_names):
    """Category 6B: DBSCAN clustering."""
    from sklearn.cluster import DBSCAN

    print("\n--- DBSCAN ---")
    findings = []

    max_samples = 100000
    if len(npis) > max_samples:
        np.random.seed(42)
        high_paid_mask = paid > np.percentile(paid, 95)
        high_idx = np.where(high_paid_mask)[0]
        remaining = np.where(~high_paid_mask)[0]
        sample_remaining = np.random.choice(
            remaining,
            size=min(max_samples - len(high_idx), len(remaining)),
            replace=False,
        )
        subset_idx = np.concatenate([high_idx, sample_remaining])
    else:
        subset_idx = np.arange(len(npis))

    X_work = X_scaled[subset_idx]
    paid_work = paid[subset_idx]
    npis_work = [npis[i] for i in subset_idx]

    db = DBSCAN(eps=2.0, min_samples=10, n_jobs=-1)
    labels = db.fit_predict(X_work)

    noise_mask = labels == -1
    # Also find tiny clusters
    from collections import Counter
    cluster_counts = Counter(labels)
    small_clusters = {k for k, v in cluster_counts.items() if v <= 3 and k != -1}
    small_mask = np.array([labels[i] in small_clusters for i in range(len(labels))])

    anomaly_mask = noise_mask | small_mask
    anomaly_idx = np.where(anomaly_mask)[0]

    if len(anomaly_idx) > 0:
        top_idx = anomaly_idx[np.argsort(-paid_work[anomaly_idx])[:30]]
        for rank, idx in enumerate(top_idx):
            h_id = f"H{641 + rank:04d}"
            evidence = f"DBSCAN noise/small_cluster: cluster={labels[idx]}, total_paid={format_dollars(paid_work[idx])}"
            confidence = 'medium' if paid_work[idx] > 500000 else 'low'
            findings.append(make_finding(h_id, npis_work[idx], float(paid_work[idx]), 1.0,
                                         'dbscan', evidence, confidence))

    print(f"  DBSCAN: {len(findings)} findings, {noise_mask.sum()} noise points "
          f"(sample_size={len(subset_idx)})")
    return findings


def run_random_forest_importance(npis, X, X_scaled, paid, feature_names):
    """Category 6C: Random Forest feature importance."""
    from sklearn.ensemble import RandomForestClassifier
    import joblib

    print("\n--- Random Forest Feature Importance ---")
    findings = []

    # Create "extreme outlier" labels: top 0.1% on any metric
    n = len(npis)
    thresholds = np.percentile(X, 99.9, axis=0)
    extreme = np.any(X > thresholds, axis=1).astype(int)

    if extreme.sum() < 10 or extreme.sum() > n * 0.5:
        print("  Skipping RF: insufficient extreme cases")
        return findings

    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, max_depth=10)
    rf.fit(X_scaled, extreme)

    importances = rf.feature_importances_
    top_features = np.argsort(-importances)[:20]

    for rank, fi in enumerate(top_features):
        feat_name = feature_names[fi]
        # Find providers in extreme tail of this feature
        thresh = np.percentile(X[:, fi], 99.9)
        extreme_idx = np.where(X[:, fi] > thresh)[0]
        if len(extreme_idx) == 0:
            continue
        top_provider_idx = extreme_idx[np.argmax(paid[extreme_idx])]

        h_id = f"H{671 + rank:04d}"
        evidence = f"RF feature importance: {feat_name}={importances[fi]:.4f}, " \
                   f"provider value={X[top_provider_idx, fi]:.2f}, threshold={thresh:.2f}"
        findings.append(make_finding(h_id, npis[top_provider_idx], float(paid[top_provider_idx]),
                                     float(importances[fi]), 'random_forest', evidence))

    joblib.dump(rf, os.path.join(MODELS_DIR, 'random_forest.joblib'))
    print(f"  Random Forest: {len(findings)} findings")
    return findings


def run_xgboost(npis, X_scaled, paid, prior_flagged):
    """Category 6D: XGBoost semi-supervised scoring."""
    import xgboost as xgb
    import joblib

    print("\n--- XGBoost Semi-supervised ---")
    findings = []

    # Create pseudo-labels
    positive = np.array([1 if npis[i] in prior_flagged else 0 for i in range(len(npis))])
    if positive.sum() < 10:
        print("  Skipping XGBoost: too few prior findings")
        return findings

    # Add negative samples
    neg_mask = positive == 0
    neg_indices = np.where(neg_mask)[0]
    sample_size = min(int(positive.sum() * 5), len(neg_indices))
    np.random.seed(42)
    neg_sample = np.random.choice(neg_indices, size=sample_size, replace=False)
    neg_labels = np.zeros(sample_size)

    pos_indices = np.where(positive == 1)[0]
    train_idx = np.concatenate([pos_indices, neg_sample])
    train_labels = np.concatenate([np.ones(len(pos_indices)), neg_labels])

    model = xgb.XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.1,
        eval_metric='logloss', random_state=42, n_jobs=-1
    )
    model.fit(X_scaled[train_idx], train_labels)

    # Score all providers
    proba = model.predict_proba(X_scaled)[:, 1]

    # Find new high-probability anomalies not in prior findings
    novel_mask = np.array([npis[i] not in prior_flagged for i in range(len(npis))])
    high_prob_mask = proba > 0.8
    paid_mask = paid > 100000
    candidate_mask = novel_mask & high_prob_mask & paid_mask
    candidate_idx = np.where(candidate_mask)[0]

    if len(candidate_idx) > 0:
        top_idx = candidate_idx[np.argsort(-proba[candidate_idx])[:30]]
        for rank, idx in enumerate(top_idx):
            h_id = f"H{691 + rank:04d}"
            evidence = f"XGBoost semi-supervised: probability={proba[idx]:.3f}, " \
                       f"total_paid={format_dollars(paid[idx])}, novel finding"
            confidence = 'high' if proba[idx] > 0.95 else 'medium'
            findings.append(make_finding(h_id, npis[idx], float(paid[idx]),
                                         float(proba[idx]), 'xgboost', evidence, confidence))

    joblib.dump(model, os.path.join(MODELS_DIR, 'xgboost.joblib'))
    print(f"  XGBoost: {len(findings)} novel findings")
    return findings


def run_kmeans(npis, X_scaled, paid, feature_names):
    """Category 6E: K-means outliers."""
    from sklearn.cluster import KMeans

    print("\n--- K-Means ---")
    findings = []

    km = KMeans(n_clusters=20, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    distances = np.min(km.transform(X_scaled), axis=1)

    # Per-cluster mean distance
    for c in range(20):
        cluster_mask = labels == c
        if cluster_mask.sum() < 5:
            continue
        mean_dist = distances[cluster_mask].mean()
        outlier_mask = cluster_mask & (distances > 3 * mean_dist)
        outlier_idx = np.where(outlier_mask)[0]
        if len(outlier_idx) == 0:
            continue
        top_idx = outlier_idx[np.argsort(-paid[outlier_idx])[:3]]
        for idx in top_idx:
            if len(findings) >= 15:
                break
            h_id = f"H{721 + len(findings):04d}"
            evidence = f"K-means cluster {c}: distance={distances[idx]:.2f}, " \
                       f"mean_cluster_distance={mean_dist:.2f}, ratio={distances[idx]/mean_dist:.1f}x"
            findings.append(make_finding(h_id, npis[idx], float(paid[idx]),
                                         float(distances[idx]), 'kmeans', evidence))

    print(f"  K-Means: {len(findings)} findings")
    return findings


def run_lof(npis, X_scaled, paid):
    """Category 6F: Local Outlier Factor."""
    from sklearn.neighbors import LocalOutlierFactor

    print("\n--- Local Outlier Factor ---")
    findings = []

    # LOF on a subsample if too large
    max_samples = 100000
    if len(npis) > max_samples:
        np.random.seed(42)
        # Include all high-paid providers plus random sample
        high_paid_mask = paid > np.percentile(paid, 95)
        high_idx = np.where(high_paid_mask)[0]
        remaining = np.where(~high_paid_mask)[0]
        sample_remaining = np.random.choice(remaining, size=min(max_samples - len(high_idx), len(remaining)), replace=False)
        subset_idx = np.concatenate([high_idx, sample_remaining])
    else:
        subset_idx = np.arange(len(npis))

    lof = LocalOutlierFactor(n_neighbors=20, contamination=0.01, n_jobs=-1)
    labels = lof.fit_predict(X_scaled[subset_idx])
    scores = -lof.negative_outlier_factor_

    # Top anomalies by score * paid
    anomaly_mask = labels == -1
    anomaly_idx = np.where(anomaly_mask)[0]
    if len(anomaly_idx) > 0:
        combined_score = scores[anomaly_idx] * paid[subset_idx[anomaly_idx]]
        top_local = anomaly_idx[np.argsort(-combined_score)[:15]]
        for rank, li in enumerate(top_local):
            idx = subset_idx[li]
            h_id = f"H{736 + rank:04d}"
            evidence = f"LOF score={scores[li]:.2f}, total_paid={format_dollars(paid[idx])}"
            confidence = 'medium' if scores[li] > 3.0 else 'low'
            findings.append(make_finding(h_id, npis[idx], float(paid[idx]),
                                         float(scores[li]), 'lof', evidence, confidence))

    print(f"  LOF: {len(findings)} findings")
    return findings


def run_autoencoder(npis, X_scaled, paid, feature_names):
    """Category 7A: Autoencoder reconstruction error."""
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    print("\n--- Autoencoder ---")
    findings = []

    input_dim = X_scaled.shape[1]
    X_tensor = torch.FloatTensor(X_scaled)

    class Autoencoder(nn.Module):
        def __init__(self, d):
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Linear(d, 64), nn.ReLU(),
                nn.Linear(64, 32), nn.ReLU(),
                nn.Linear(32, 8), nn.ReLU(),
            )
            self.decoder = nn.Sequential(
                nn.Linear(8, 32), nn.ReLU(),
                nn.Linear(32, 64), nn.ReLU(),
                nn.Linear(64, d),
            )
        def forward(self, x):
            return self.decoder(self.encoder(x))

    model = Autoencoder(input_dim)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss(reduction='none')

    dataset = TensorDataset(X_tensor)
    loader = DataLoader(dataset, batch_size=2048, shuffle=True)

    model.train()
    for epoch in range(100):
        for batch in loader:
            x = batch[0]
            pred = model(x)
            loss = criterion(pred, x).mean()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        if (epoch + 1) % 25 == 0:
            print(f"    Epoch {epoch+1}/100, loss={loss.item():.6f}")

    model.eval()
    with torch.no_grad():
        recon = model(X_tensor)
        errors = criterion(recon, X_tensor).mean(dim=1).numpy()

    threshold = np.percentile(errors, 99)

    segments = [
        ('overall', np.ones(len(npis), dtype=bool), 751, 10),
        ('home_health', paid > 100000, 761, 10),
        ('behavioral', paid > 50000, 771, 10),
    ]

    for seg_name, mask, base_h, n_findings in segments:
        seg_idx = np.where(mask & (errors > threshold))[0]
        if len(seg_idx) == 0:
            continue
        top_idx = seg_idx[np.argsort(-errors[seg_idx])[:n_findings]]
        for rank, idx in enumerate(top_idx):
            h_id = f"H{base_h + rank:04d}"
            # Find which features have highest reconstruction error
            with torch.no_grad():
                feat_errors = criterion(recon[idx:idx+1], X_tensor[idx:idx+1])[0].numpy()
            top_feats = np.argsort(-feat_errors)[:3]
            evidence = f"Autoencoder {seg_name}: recon_error={errors[idx]:.4f}, " \
                       f"threshold={threshold:.4f}, " \
                       f"anomalous_features=[{', '.join(feature_names[fi] for fi in top_feats)}]"
            confidence = 'high' if errors[idx] > threshold * 2 and paid[idx] > 500000 else 'medium'
            findings.append(make_finding(h_id, npis[idx], float(paid[idx]),
                                         float(errors[idx]), 'autoencoder', evidence, confidence))

    torch.save(model.state_dict(), os.path.join(MODELS_DIR, 'autoencoder.pt'))
    print(f"  Autoencoder: {len(findings)} findings")
    return findings, errors


def run_vae(npis, X_scaled, paid, feature_names, ae_errors):
    """Category 7B: Variational Autoencoder."""
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    print("\n--- VAE ---")
    findings = []

    input_dim = X_scaled.shape[1]
    X_tensor = torch.FloatTensor(X_scaled)

    class VAE(nn.Module):
        def __init__(self, d):
            super().__init__()
            self.encoder = nn.Sequential(nn.Linear(d, 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU())
            self.fc_mu = nn.Linear(32, 8)
            self.fc_logvar = nn.Linear(32, 8)
            self.decoder = nn.Sequential(
                nn.Linear(8, 32), nn.ReLU(), nn.Linear(32, 64), nn.ReLU(), nn.Linear(64, d)
            )

        def encode(self, x):
            h = self.encoder(x)
            return self.fc_mu(h), self.fc_logvar(h)

        def reparameterize(self, mu, logvar):
            std = torch.exp(0.5 * logvar)
            eps = torch.randn_like(std)
            return mu + eps * std

        def forward(self, x):
            mu, logvar = self.encode(x)
            z = self.reparameterize(mu, logvar)
            return self.decoder(z), mu, logvar

    model = VAE(input_dim)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    dataset = TensorDataset(X_tensor)
    loader = DataLoader(dataset, batch_size=2048, shuffle=True)

    model.train()
    for epoch in range(100):
        for batch in loader:
            x = batch[0]
            recon, mu, logvar = model(x)
            recon_loss = nn.functional.mse_loss(recon, x, reduction='mean')
            kl_loss = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())
            loss = recon_loss + 0.1 * kl_loss
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        recon, mu, logvar = model(X_tensor)
        recon_errors = nn.functional.mse_loss(recon, X_tensor, reduction='none').mean(dim=1).numpy()
        kl_errors = -0.5 * (1 + logvar - mu.pow(2) - logvar.exp()).mean(dim=1).numpy()
        total_scores = recon_errors + 0.1 * kl_errors

    # Flag top anomalies not already in autoencoder top
    ae_threshold = np.percentile(ae_errors, 99)
    novel_mask = ae_errors < ae_threshold  # Not already flagged by AE
    vae_threshold = np.percentile(total_scores, 99)
    candidate_mask = novel_mask & (total_scores > vae_threshold) & (paid > 100000)
    candidate_idx = np.where(candidate_mask)[0]

    if len(candidate_idx) > 0:
        top_idx = candidate_idx[np.argsort(-total_scores[candidate_idx])[:20]]
        for rank, idx in enumerate(top_idx):
            h_id = f"H{781 + rank:04d}"
            evidence = f"VAE: total_score={total_scores[idx]:.4f}, " \
                       f"recon={recon_errors[idx]:.4f}, kl={kl_errors[idx]:.4f}"
            findings.append(make_finding(h_id, npis[idx], float(paid[idx]),
                                         float(total_scores[idx]), 'vae', evidence))

    torch.save(model.state_dict(), os.path.join(MODELS_DIR, 'vae.pt'))
    print(f"  VAE: {len(findings)} findings")
    return findings


def run_lstm(con, npis_all, paid_all):
    """Category 7C: LSTM temporal anomaly detection."""
    import torch
    import torch.nn as nn

    print("\n--- LSTM Temporal ---")
    findings = []

    # Get monthly time series for high-value providers
    high_value_npis = [npis_all[i] for i in range(len(npis_all)) if paid_all[i] > 200000]
    if len(high_value_npis) > 20000:
        np.random.seed(42)
        high_value_npis = list(np.random.choice(high_value_npis, 20000, replace=False))

    if len(high_value_npis) == 0:
        return findings

    # Build monthly series
    npi_set = set(high_value_npis)
    rows = con.execute("""
        SELECT billing_npi, claim_month, paid
        FROM provider_monthly
        WHERE billing_npi IN (SELECT UNNEST(?::VARCHAR[]))
        ORDER BY billing_npi, claim_month
    """, [high_value_npis]).fetchall()

    # Create time series dict
    from collections import defaultdict
    series = defaultdict(dict)
    all_months = sorted(set(r[1] for r in rows))
    month_idx = {m: i for i, m in enumerate(all_months)}

    for npi, month, p in rows:
        series[npi][month_idx.get(month, 0)] = p

    n_months = len(all_months)
    npis_with_data = []
    ts_data = []
    for npi in high_value_npis:
        if npi in series and len(series[npi]) >= 24:
            ts = np.zeros(n_months)
            for mi, val in series[npi].items():
                ts[mi] = val
            ts_data.append(ts)
            npis_with_data.append(npi)

    if len(ts_data) < 100:
        print("  LSTM: insufficient time series data")
        return findings

    ts_array = np.array(ts_data)
    # Normalize per provider
    means = ts_array.mean(axis=1, keepdims=True)
    stds = ts_array.std(axis=1, keepdims=True)
    stds[stds < 1] = 1
    ts_norm = (ts_array - means) / stds

    class LSTMPredictor(nn.Module):
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(1, 32, batch_first=True, num_layers=2)
            self.fc = nn.Linear(32, 1)

        def forward(self, x):
            out, _ = self.lstm(x)
            return self.fc(out[:, -1, :])

    # Train on all series to predict next month
    X_seq = torch.FloatTensor(ts_norm[:, :-1]).unsqueeze(-1)
    y_seq = torch.FloatTensor(ts_norm[:, -1])

    model = LSTMPredictor()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    model.train()
    batch_size = min(512, len(X_seq))
    for epoch in range(50):
        perm = torch.randperm(len(X_seq))
        for i in range(0, len(X_seq), batch_size):
            idx = perm[i:i+batch_size]
            pred = model(X_seq[idx]).squeeze()
            loss = nn.functional.mse_loss(pred, y_seq[idx])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    # Compute prediction errors for all providers
    model.eval()
    with torch.no_grad():
        all_errors = []
        for i in range(0, len(X_seq), 1000):
            pred = model(X_seq[i:i+1000]).squeeze()
            err = (pred - y_seq[i:i+1000]).abs().numpy()
            all_errors.extend(err.tolist() if err.ndim > 0 else [err.item()])

    all_errors = np.array(all_errors)
    mean_error = all_errors.mean()
    threshold = 3 * mean_error

    anomaly_idx = np.where(all_errors > threshold)[0]
    if len(anomaly_idx) > 0:
        top_idx = anomaly_idx[np.argsort(-all_errors[anomaly_idx])[:15]]
        for rank, idx in enumerate(top_idx):
            npi = npis_with_data[idx]
            total = ts_array[idx].sum()
            h_id = f"H{801 + rank:04d}"
            evidence = f"LSTM prediction error={all_errors[idx]:.3f}, " \
                       f"mean_error={mean_error:.3f}, ratio={all_errors[idx]/mean_error:.1f}x"
            findings.append(make_finding(h_id, npi, float(total),
                                         float(all_errors[idx]), 'lstm', evidence))

    torch.save(model.state_dict(), os.path.join(MODELS_DIR, 'lstm.pt'))
    print(f"  LSTM: {len(findings)} findings")
    return findings


def run_transformer(con, npis_all, paid_all):
    """Category 7D: Transformer attention anomaly detection."""
    import torch
    import torch.nn as nn

    print("\n--- Transformer Attention ---")
    findings = []

    # Use high-value providers
    high_value_mask = paid_all > 500000
    high_npis = [npis_all[i] for i in range(len(npis_all)) if high_value_mask[i]]

    if len(high_npis) > 10000:
        np.random.seed(42)
        high_npis = list(np.random.choice(high_npis, 10000, replace=False))

    if len(high_npis) < 50:
        return findings

    rows = con.execute("""
        SELECT billing_npi, claim_month, paid
        FROM provider_monthly
        WHERE billing_npi IN (SELECT UNNEST(?::VARCHAR[]))
        ORDER BY billing_npi, claim_month
    """, [high_npis]).fetchall()

    from collections import defaultdict
    series = defaultdict(dict)
    all_months = sorted(set(r[1] for r in rows))
    month_idx = {m: i for i, m in enumerate(all_months)}

    for npi, month, p in rows:
        series[npi][month_idx.get(month, 0)] = p

    n_months = len(all_months)
    npis_with_data = []
    ts_data = []
    for npi in high_npis:
        if npi in series and len(series[npi]) >= 12:
            ts = np.zeros(n_months)
            for mi, val in series[npi].items():
                ts[mi] = val
            ts_data.append(ts)
            npis_with_data.append(npi)

    if len(ts_data) < 50:
        return findings

    ts_array = np.array(ts_data)
    means = ts_array.mean(axis=1, keepdims=True)
    stds = ts_array.std(axis=1, keepdims=True)
    stds[stds < 1] = 1
    ts_norm = (ts_array - means) / stds

    class SimpleTransformer(nn.Module):
        def __init__(self, seq_len):
            super().__init__()
            self.pos_enc = nn.Parameter(torch.randn(1, seq_len, 32))
            self.proj = nn.Linear(1, 32)
            self.attn = nn.MultiheadAttention(32, 4, batch_first=True)
            self.fc = nn.Linear(32, 1)

        def forward(self, x):
            h = self.proj(x) + self.pos_enc
            attn_out, attn_weights = self.attn(h, h, h)
            return self.fc(attn_out), attn_weights

    X_t = torch.FloatTensor(ts_norm).unsqueeze(-1)
    model = SimpleTransformer(n_months)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    model.train()
    for epoch in range(50):
        pred, _ = model(X_t)
        loss = nn.functional.mse_loss(pred.squeeze(), torch.FloatTensor(ts_norm))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        _, attn_weights = model(X_t)  # [N, n_months, n_months]

    # Check attention concentration
    attn_np = attn_weights.numpy()
    uniform = 1.0 / n_months
    max_attn = attn_np.max(axis=-1).mean(axis=-1)  # max attention per query, averaged
    concentration = max_attn / uniform

    threshold = 3.0
    anomaly_mask = concentration > threshold
    anomaly_idx = np.where(anomaly_mask)[0]

    if len(anomaly_idx) > 0:
        top_idx = anomaly_idx[np.argsort(-concentration[anomaly_idx])[:15]]
        for rank, idx in enumerate(top_idx):
            npi = npis_with_data[idx]
            total = ts_array[idx].sum()
            h_id = f"H{816 + rank:04d}"
            evidence = f"Transformer attention concentration={concentration[idx]:.2f}x uniform, " \
                       f"threshold={threshold:.1f}x"
            findings.append(make_finding(h_id, npi, float(total),
                                         float(concentration[idx]), 'transformer', evidence))

    torch.save(model.state_dict(), os.path.join(MODELS_DIR, 'transformer.pt'))
    print(f"  Transformer: {len(findings)} findings")
    return findings


# ---------------------------------------------------------------------------
# Gap Analysis: Novel/Research-Frontier ML Methods (H1086-H1100)
# ---------------------------------------------------------------------------


def run_zipf_analysis(con, npis, paid):
    """6G: Zipf's Law deviation analysis on billing distributions (H1086-H1087)."""
    from scipy import stats

    print("\n--- Zipf's Law Analysis ---")
    findings = []

    # H1086: Overall billing distribution vs Zipf's Law
    # Sort providers by paid descending, check if log-rank vs log-paid is linear
    sorted_idx = np.argsort(-paid)
    ranks = np.arange(1, len(sorted_idx) + 1)
    sorted_paid = paid[sorted_idx]

    # Only use positive values
    pos_mask = sorted_paid > 0
    if pos_mask.sum() > 100:
        log_ranks = np.log10(ranks[pos_mask])
        log_paid = np.log10(sorted_paid[pos_mask])

        slope, intercept, r_value, p_value, std_err = stats.linregress(log_ranks, log_paid)

        # Find providers that deviate most from Zipf expectation
        expected_log_paid = slope * log_ranks + intercept
        residuals = log_paid - expected_log_paid
        # Providers above the line are billing MORE than Zipf predicts
        excess_idx = np.where(residuals > 2 * residuals.std())[0]

        if len(excess_idx) > 0:
            providers_flagged = []
            for i in excess_idx[:15]:
                orig_idx = sorted_idx[pos_mask][i]
                npi = npis[orig_idx]
                evidence = f"Zipf deviation: rank={ranks[pos_mask][i]}, " \
                           f"actual={format_dollars(sorted_paid[pos_mask][i])}, " \
                           f"expected={format_dollars(10**expected_log_paid[i])}, " \
                           f"residual={residuals[i]:.2f}σ (Zipf R²={r_value**2:.3f})"
                providers_flagged.append(make_finding(
                    f"H1086", npi, float(sorted_paid[pos_mask][i]),
                    float(residuals[i]), 'zipf_billing', evidence))

            if providers_flagged:
                findings.extend(providers_flagged[:10])

    # H1087: Referral concentration Zipf analysis
    ref_rows = con.execute("""
        SELECT servicing_npi, SUM(total_paid) AS total_referred
        FROM billing_servicing_network
        WHERE billing_npi != servicing_npi
        GROUP BY servicing_npi
        HAVING SUM(total_paid) > 10000
        ORDER BY SUM(total_paid) DESC
    """).fetchall()

    if len(ref_rows) > 100:
        ref_paid = np.array([r[1] for r in ref_rows], dtype=np.float64)
        ref_npis = [r[0] for r in ref_rows]
        ref_ranks = np.arange(1, len(ref_paid) + 1)

        log_rr = np.log10(ref_ranks)
        log_rp = np.log10(np.maximum(ref_paid, 1))

        slope_r, intercept_r, r_val_r, _, _ = stats.linregress(log_rr, log_rp)
        expected_r = slope_r * log_rr + intercept_r
        residuals_r = log_rp - expected_r

        excess_r = np.where(residuals_r > 2 * residuals_r.std())[0]
        for i in excess_r[:10]:
            npi = ref_npis[i]
            findings.append(make_finding(
                'H1087', npi, float(ref_paid[i]),
                float(residuals_r[i]), 'zipf_referral',
                f"Referral Zipf deviation: rank={ref_ranks[i]}, "
                f"received={format_dollars(ref_paid[i])}, "
                f"residual={residuals_r[i]:.2f}σ"))

    print(f"  Zipf analysis: {len(findings)} findings")
    return findings


def run_association_rules(con):
    """6G: Association rule mining for unusual code combinations (H1088)."""
    print("\n--- Association Rule Mining ---")
    findings = []

    # Find providers billing unusual code combinations
    rows = con.execute("""
        WITH provider_codes AS (
            SELECT billing_npi, hcpcs_code, SUM(paid) AS code_paid
            FROM claims
            GROUP BY billing_npi, hcpcs_code
            HAVING SUM(paid) > 1000
        ),
        code_pairs AS (
            SELECT
                a.billing_npi,
                a.hcpcs_code AS code_a,
                b.hcpcs_code AS code_b,
                a.code_paid + b.code_paid AS pair_paid
            FROM provider_codes a
            INNER JOIN provider_codes b
                ON a.billing_npi = b.billing_npi AND a.hcpcs_code < b.hcpcs_code
        ),
        pair_counts AS (
            SELECT code_a, code_b,
                   COUNT(*) AS pair_count,
                   SUM(pair_paid) AS pair_total
            FROM code_pairs
            GROUP BY code_a, code_b
        ),
        code_a_counts AS (
            SELECT hcpcs_code, COUNT(DISTINCT billing_npi) AS code_count
            FROM provider_codes
            GROUP BY hcpcs_code
        ),
        -- Find rare pairs: pairs that occur with few providers relative to either code's prevalence
        rare_pairs AS (
            SELECT pc.code_a, pc.code_b, pc.pair_count, pc.pair_total,
                   ca.code_count AS count_a, cb.code_count AS count_b,
                   pc.pair_count * 1.0 / LEAST(ca.code_count, cb.code_count) AS support
            FROM pair_counts pc
            INNER JOIN code_a_counts ca ON pc.code_a = ca.hcpcs_code
            INNER JOIN code_a_counts cb ON pc.code_b = cb.hcpcs_code
            WHERE pc.pair_count BETWEEN 2 AND 10
              AND LEAST(ca.code_count, cb.code_count) > 100
              AND pc.pair_total > 500000
        )
        SELECT code_a, code_b, pair_count, pair_total, count_a, count_b, support
        FROM rare_pairs
        ORDER BY pair_total DESC
        LIMIT 20
    """).fetchall()

    if rows:
        for rank, r in enumerate(rows[:10]):
            code_a, code_b, count, total, ca, cb, support = r
            findings.append(make_finding(
                'H1088', f"PAIR_{code_a}_{code_b}", float(total),
                float(1 - support), 'association_rules',
                f"Unusual code pair: {code_a}+{code_b}, {count} providers "
                f"({code_a} in {ca} providers, {code_b} in {cb}), "
                f"support={support:.4f}, total={format_dollars(total)}"))

    print(f"  Association rules: {len(findings)} findings")
    return findings


def run_cosine_similarity(npis, X_scaled, paid, feature_names, prior_flagged):
    """6G: Billing pattern cosine similarity to known fraud profiles (H1089)."""
    from sklearn.metrics.pairwise import cosine_similarity as cs

    print("\n--- Cosine Similarity ---")
    findings = []

    # Build average "fraud profile" from prior flagged providers
    flagged_mask = np.array([npis[i] in prior_flagged for i in range(len(npis))])
    if flagged_mask.sum() < 10:
        print("  Insufficient flagged providers for similarity analysis")
        return findings

    fraud_centroid = X_scaled[flagged_mask].mean(axis=0).reshape(1, -1)

    # Compute cosine similarity of all providers to the fraud centroid
    similarities = cs(X_scaled, fraud_centroid).flatten()

    # Find high-similarity providers NOT already flagged
    novel_mask = ~flagged_mask & (paid > 100000)
    novel_high = np.where(novel_mask & (similarities > 0.9))[0]

    if len(novel_high) > 0:
        top_idx = novel_high[np.argsort(-similarities[novel_high])[:15]]
        for rank, idx in enumerate(top_idx):
            findings.append(make_finding(
                'H1089', npis[idx], float(paid[idx]),
                float(similarities[idx]), 'cosine_similarity_fraud',
                f"Cosine similarity to fraud profile: {similarities[idx]:.3f}, "
                f"total_paid={format_dollars(paid[idx])}, novel finding"))

    print(f"  Cosine similarity: {len(findings)} findings")
    return findings


def run_entropy_analysis(npis, features, paid, feature_names):
    """6G: Entropy analysis on billing distributions (H1090)."""
    from scipy.stats import entropy as scipy_entropy

    print("\n--- Entropy Analysis ---")
    findings = []

    # For each provider, compute entropy of their feature distribution
    # (normalized to sum to 1 for positive features)
    pos_features = np.maximum(features, 0)
    row_sums = pos_features.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    normed = pos_features / row_sums

    entropies = np.array([scipy_entropy(row + 1e-10) for row in normed])

    # Flag providers with extremely low entropy (too uniform or too concentrated)
    p1 = np.percentile(entropies, 1)
    low_entropy_mask = (entropies < p1) & (paid > 500000)
    low_idx = np.where(low_entropy_mask)[0]

    if len(low_idx) > 0:
        top_idx = low_idx[np.argsort(-paid[low_idx])[:15]]
        for rank, idx in enumerate(top_idx):
            findings.append(make_finding(
                'H1090', npis[idx], float(paid[idx]),
                float(1 / max(entropies[idx], 0.001)), 'low_entropy_billing',
                f"Low billing entropy: {entropies[idx]:.4f} (1st pct={p1:.4f}), "
                f"total_paid={format_dollars(paid[idx])}"))

    print(f"  Entropy analysis: {len(findings)} findings")
    return findings


def run_neighborhood_risk(con, npis, paid, prior_flagged):
    """6G: Provider neighborhood risk score (H1100)."""
    print("\n--- Neighborhood Risk Propagation ---")
    findings = []

    # Build adjacency from billing_servicing_network
    rows = con.execute("""
        SELECT billing_npi, servicing_npi, total_paid
        FROM billing_servicing_network
        WHERE billing_npi != servicing_npi AND total_paid > 10000
    """).fetchall()

    if len(rows) < 100:
        print("  Insufficient network data for risk propagation")
        return findings

    # Build risk scores
    npi_set = set(npis)
    npi_to_idx = {npi: i for i, npi in enumerate(npis)}

    # Initial risk: 1.0 for flagged, 0.0 for others
    risk = np.zeros(len(npis))
    for npi in prior_flagged:
        if npi in npi_to_idx:
            risk[npi_to_idx[npi]] = 1.0

    # Build neighbor lists
    neighbors = {i: [] for i in range(len(npis))}
    for b_npi, s_npi, edge_paid in rows:
        b_idx = npi_to_idx.get(b_npi)
        s_idx = npi_to_idx.get(s_npi)
        if b_idx is not None and s_idx is not None:
            neighbors[b_idx].append((s_idx, edge_paid))
            neighbors[s_idx].append((b_idx, edge_paid))

    # Propagate risk (1 iteration)
    new_risk = risk.copy()
    for i in range(len(npis)):
        if neighbors[i]:
            total_weight = sum(w for _, w in neighbors[i])
            if total_weight > 0:
                neighbor_risk = sum(risk[j] * w for j, w in neighbors[i]) / total_weight
                new_risk[i] = 0.5 * risk[i] + 0.5 * neighbor_risk

    risk = new_risk

    # Find novel high-risk providers
    novel_mask = np.array([npis[i] not in prior_flagged for i in range(len(npis))])
    high_risk_mask = novel_mask & (risk > 0.5) & (paid > 100000)
    high_idx = np.where(high_risk_mask)[0]

    if len(high_idx) > 0:
        top_idx = high_idx[np.argsort(-risk[high_idx] * paid[high_idx])[:15]]
        for rank, idx in enumerate(top_idx):
            num_flagged_neighbors = sum(1 for j, _ in neighbors[idx] if risk[j] > 0.5)
            findings.append(make_finding(
                'H1100', npis[idx], float(paid[idx]),
                float(risk[idx]), 'neighborhood_risk',
                f"Neighborhood risk score={risk[idx]:.3f}, "
                f"{num_flagged_neighbors} high-risk neighbors, "
                f"total_paid={format_dollars(paid[idx])}"))

    print(f"  Neighborhood risk: {len(findings)} findings")
    return findings


def main():
    t0 = time.time()
    os.makedirs(FINDINGS_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)

    os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

    all_findings = []
    prior_flagged = set()
    con = None
    try:
        con = get_connection(read_only=True)

        # Load feature matrix
        npis, features, feature_names = load_feature_matrix(con)
        if len(npis) == 0:
            print("No providers available for ML feature extraction. Writing empty findings.")
            output_path = os.path.join(FINDINGS_DIR, 'categories_6_and_7.json')
            with open(output_path, 'w') as f:
                json.dump([], f, indent=2, default=str)
            return
        paid = features[:, 0]  # total_paid is first feature

        # Standardize
        try:
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(features)
        except Exception as e:
            print(f"  [SKIP] StandardScaler failed or sklearn missing: {e}")
            output_path = os.path.join(FINDINGS_DIR, 'categories_6_and_7.json')
            with open(output_path, 'w') as f:
                json.dump([], f, indent=2, default=str)
            return

        import joblib
        joblib.dump(scaler, os.path.join(MODELS_DIR, 'scaler.joblib'))

        # Load prior flagged NPIs
        prior_flagged = get_prior_flagged_npis()
        print(f"Prior flagged NPIs: {len(prior_flagged)}")

        # Category 6A: Isolation Forest
        try:
            findings = run_isolation_forest(npis, features, X_scaled, paid, feature_names, prior_flagged)
            all_findings.extend(findings)
        except Exception as e:
            print(f"  [SKIP] Isolation Forest failed: {e}")

        # Category 6B: DBSCAN
        try:
            findings = run_dbscan(npis, X_scaled, paid, feature_names)
            all_findings.extend(findings)
        except Exception as e:
            print(f"  [SKIP] DBSCAN failed: {e}")

        # Category 6C: Random Forest
        try:
            findings = run_random_forest_importance(npis, features, X_scaled, paid, feature_names)
            all_findings.extend(findings)
        except Exception as e:
            print(f"  [SKIP] Random Forest failed: {e}")

        # Category 6D: XGBoost
        try:
            findings = run_xgboost(npis, X_scaled, paid, prior_flagged)
            all_findings.extend(findings)
        except Exception as e:
            print(f"  [SKIP] XGBoost failed: {e}")

        # Category 6E: K-Means
        try:
            findings = run_kmeans(npis, X_scaled, paid, feature_names)
            all_findings.extend(findings)
        except Exception as e:
            print(f"  [SKIP] KMeans failed: {e}")

        # Category 6F: LOF
        try:
            findings = run_lof(npis, X_scaled, paid)
            all_findings.extend(findings)
        except Exception as e:
            print(f"  [SKIP] LOF failed: {e}")

        # Category 7A-7D: Deep learning models (skip for very large cohorts)
        run_torch_models = len(npis) <= 200000
        if not run_torch_models:
            ae_errors = None
            print(f"  [SKIP] Deep models: provider count {len(npis)} exceeds 200000")
        else:
            # Category 7A: Autoencoder
            try:
                ae_findings, ae_errors = run_autoencoder(npis, X_scaled, paid, feature_names)
                all_findings.extend(ae_findings)
            except Exception as e:
                ae_errors = None
                print(f"  [SKIP] Autoencoder failed: {e}")

            # Category 7B: VAE
            try:
                if ae_errors is not None:
                    findings = run_vae(npis, X_scaled, paid, feature_names, ae_errors)
                    all_findings.extend(findings)
            except Exception as e:
                print(f"  [SKIP] VAE failed: {e}")

            # Category 7C: LSTM
            try:
                findings = run_lstm(con, npis, paid)
                all_findings.extend(findings)
            except Exception as e:
                print(f"  [SKIP] LSTM failed: {e}")

            # Category 7D: Transformer
            try:
                findings = run_transformer(con, npis, paid)
                all_findings.extend(findings)
            except Exception as e:
                print(f"  [SKIP] Transformer failed: {e}")

        # Gap Analysis: Novel ML methods (H1086-H1100)
        try:
            findings = run_zipf_analysis(con, npis, paid)
            all_findings.extend(findings)
        except Exception as e:
            print(f"  [SKIP] Zipf analysis failed: {e}")

        try:
            findings = run_association_rules(con)
            all_findings.extend(findings)
        except Exception as e:
            print(f"  [SKIP] Association rules failed: {e}")

        try:
            findings = run_cosine_similarity(npis, X_scaled, paid, feature_names, prior_flagged)
            all_findings.extend(findings)
        except Exception as e:
            print(f"  [SKIP] Cosine similarity failed: {e}")

        try:
            findings = run_entropy_analysis(npis, features, paid, feature_names)
            all_findings.extend(findings)
        except Exception as e:
            print(f"  [SKIP] Entropy analysis failed: {e}")

        try:
            findings = run_neighborhood_risk(con, npis, paid, prior_flagged)
            all_findings.extend(findings)
        except Exception as e:
            print(f"  [SKIP] Neighborhood risk failed: {e}")
    finally:
        # Save findings even if an intermediate step fails
        output_path = os.path.join(FINDINGS_DIR, 'categories_6_and_7.json')
        with open(output_path, 'w') as f:
            json.dump(all_findings, f, indent=2, default=str)

        # Count novel findings
        novel_npis = set()
        for finding in all_findings:
            for p in finding.get('flagged_providers', []):
                if p['npi'] not in prior_flagged:
                    novel_npis.add(p['npi'])

        print(f"\nTotal ML/DL findings: {len(all_findings)}")
        print(f"Novel providers (not in Categories 1-5): {len(novel_npis)}")
        print(f"Findings written to {output_path}")

        if con is not None:
            con.close()
        print(f"\nMilestone 6 complete. Time: {time.time() - t0:.1f}s")


if __name__ == '__main__':
    main()
