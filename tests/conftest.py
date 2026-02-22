"""Shared pytest fixtures for the Medicaid FWA Analytics test suite."""

import os
import sys
import tempfile

import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture
def project_root():
    """Return the project root directory path."""
    return PROJECT_ROOT


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_config(temp_dir):
    """Create a minimal config.yml in a temporary directory."""
    import yaml
    config = {
        'pipeline': {'name': 'test', 'version': '1.0.0', 'halt_on_failure': True},
        'database': {'path': ':memory:', 'threads': 1, 'memory_limit': '256MB'},
        'output': {'base_dir': os.path.join(temp_dir, 'output')},
        'detection': {'methods': {'z_score': True}},
        'thresholds': {'z_score_high': 3.0},
    }
    config_path = os.path.join(temp_dir, 'config.yml')
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    return config_path


@pytest.fixture
def test_db_connection():
    """Provide an in-memory DuckDB connection for testing."""
    import duckdb
    con = duckdb.connect(':memory:')
    # Create minimal schema matching production tables
    con.execute("""
        CREATE TABLE claims (
            billing_npi VARCHAR,
            servicing_npi VARCHAR,
            hcpcs_code VARCHAR,
            claim_month VARCHAR,
            beneficiaries INTEGER,
            claims INTEGER,
            paid DOUBLE
        )
    """)
    con.execute("""
        CREATE TABLE provider_summary (
            billing_npi VARCHAR,
            total_paid DOUBLE,
            total_claims INTEGER,
            total_beneficiaries INTEGER,
            avg_paid_per_claim DOUBLE,
            avg_claims_per_bene DOUBLE,
            num_codes INTEGER,
            num_months INTEGER
        )
    """)
    con.execute("""
        CREATE TABLE hcpcs_summary (
            hcpcs_code VARCHAR,
            avg_paid_per_claim DOUBLE,
            stddev_paid_per_claim DOUBLE,
            median_paid_per_claim DOUBLE,
            p95_paid_per_claim DOUBLE,
            num_providers INTEGER,
            total_paid DOUBLE
        )
    """)
    con.execute("""
        CREATE TABLE provider_hcpcs (
            billing_npi VARCHAR,
            hcpcs_code VARCHAR,
            claims INTEGER,
            paid DOUBLE,
            paid_per_claim DOUBLE,
            beneficiaries INTEGER
        )
    """)
    con.execute("""
        CREATE TABLE provider_monthly (
            billing_npi VARCHAR,
            claim_month VARCHAR,
            claims INTEGER,
            paid DOUBLE,
            beneficiaries INTEGER
        )
    """)
    con.execute("""
        CREATE TABLE billing_servicing_network (
            billing_npi VARCHAR,
            servicing_npi VARCHAR,
            claims INTEGER,
            paid DOUBLE
        )
    """)
    yield con
    con.close()
