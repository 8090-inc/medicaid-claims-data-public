"""Holdout dataset partitioning for validation."""

import logging
import random

logger = logging.getLogger('medicaid_fwa.validation')


def create_holdout_partition(con, holdout_fraction=0.2, seed=42):
    """Partition providers into training and holdout sets.

    Args:
        con: DuckDB connection (read-only).
        holdout_fraction: Fraction of providers to hold out.
        seed: Random seed for reproducibility.

    Returns:
        dict with 'train_npis' and 'holdout_npis' lists.
    """
    rows = con.execute("""
        SELECT billing_npi FROM provider_summary
        ORDER BY billing_npi
    """).fetchall()

    all_npis = [r[0] for r in rows]
    random.seed(seed)
    random.shuffle(all_npis)

    split_idx = int(len(all_npis) * (1 - holdout_fraction))
    train = all_npis[:split_idx]
    holdout = all_npis[split_idx:]

    logger.info(f'Holdout partition: {len(train)} train, {len(holdout)} holdout '
                f'({holdout_fraction:.0%})')
    return {'train_npis': train, 'holdout_npis': holdout}


def partition_findings_by_holdout(findings, holdout_npis):
    """Split findings into train and holdout subsets.

    Args:
        findings: List of finding dicts.
        holdout_npis: Set or list of holdout NPI strings.

    Returns:
        dict with 'train_findings' and 'holdout_findings' lists.
    """
    holdout_set = set(holdout_npis)
    train = []
    holdout = []

    for f in findings:
        providers = f.get('flagged_providers', [])
        if any(p in holdout_set for p in providers):
            holdout.append(f)
        else:
            train.append(f)

    logger.info(f'Findings split: {len(train)} train, {len(holdout)} holdout')
    return {'train_findings': train, 'holdout_findings': holdout}
