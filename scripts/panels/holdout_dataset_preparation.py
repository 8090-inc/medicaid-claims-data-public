"""Holdout dataset preparation for validation and calibration."""

import logging

logger = logging.getLogger('medicaid_fwa.panels')


def create_holdout_split(con, holdout_fraction=0.2, seed=42):
    """Create a holdout split of providers for validation.

    Assigns a random fraction of providers to a holdout set.

    Args:
        con: DuckDB connection (write mode).
        holdout_fraction: Fraction of providers in holdout (default 0.2).
        seed: Random seed for reproducibility.

    Returns:
        dict with train_count and holdout_count.
    """
    logger.info(f'Creating holdout split (fraction={holdout_fraction}, seed={seed}) ...')
    con.execute("DROP TABLE IF EXISTS holdout_assignment")
    con.execute(f"""
        CREATE TABLE holdout_assignment AS
        SELECT
            billing_npi,
            CASE WHEN HASH(billing_npi || '{seed}') % 100 < {int(holdout_fraction * 100)}
                 THEN 'holdout' ELSE 'train' END AS split
        FROM provider_summary
    """)
    train = con.execute("SELECT COUNT(*) FROM holdout_assignment WHERE split = 'train'").fetchone()[0]
    holdout = con.execute("SELECT COUNT(*) FROM holdout_assignment WHERE split = 'holdout'").fetchone()[0]
    logger.info(f'  Train: {train:,}, Holdout: {holdout:,}')
    return {'train_count': train, 'holdout_count': holdout}
