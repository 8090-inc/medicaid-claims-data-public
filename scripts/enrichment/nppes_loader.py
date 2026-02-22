"""NPPES provider registry download, parsing, and filtering."""

import csv
import glob
import io
import logging
import os
import zipfile

import requests

from config.project_config import NPPES_DIR

logger = logging.getLogger('medicaid_fwa.enrichment')

NPPES_URL = 'https://download.cms.gov/nppes/NPPES_Data_Dissemination_January_2025.zip'


def download_nppes(url=None, target_dir=None):
    """Download the NPPES data dissemination ZIP file.

    Args:
        url: URL to download from (default: latest NPPES release).
        target_dir: Directory to save to (default: reference_data/nppes/).
    """
    url = url or NPPES_URL
    target_dir = target_dir or NPPES_DIR
    os.makedirs(target_dir, exist_ok=True)

    zip_path = os.path.join(target_dir, 'nppes_data.zip')
    if os.path.exists(zip_path):
        logger.info(f'NPPES ZIP already exists: {zip_path}')
        return zip_path

    logger.info(f'Downloading NPPES from {url} ...')
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(zip_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    logger.info(f'Downloaded: {zip_path}')
    return zip_path


def find_nppes_csv(nppes_dir=None):
    """Find the main NPPES CSV file in the extracted directory.

    Returns:
        Path to the CSV file, or None if not found.
    """
    nppes_dir = nppes_dir or NPPES_DIR
    patterns = [
        os.path.join(nppes_dir, 'npidata_pfile_*.csv'),
        os.path.join(nppes_dir, '**', 'npidata_pfile_*.csv'),
    ]
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            return matches[0]
    return None


def parse_nppes_for_claims(con, nppes_csv_path):
    """Parse NPPES CSV and create providers table in DuckDB.

    Extracts NPI, name, state, specialty, entity type for providers
    that appear in the claims data.

    Args:
        con: DuckDB connection (write mode).
        nppes_csv_path: Path to the NPPES CSV file.
    """
    logger.info(f'Parsing NPPES: {nppes_csv_path}')
    con.execute("DROP TABLE IF EXISTS providers")
    con.execute("""
        CREATE TABLE providers AS
        SELECT
            NPI::VARCHAR AS npi,
            COALESCE(
                CASE WHEN "Entity Type Code" = '1'
                    THEN "Provider Last Name (Legal Name)" || ', ' || "Provider First Name"
                    ELSE "Provider Organization Name (Legal Business Name)"
                END, ''
            ) AS name,
            COALESCE("Provider Business Practice Location Address State Name", '') AS state,
            '' AS specialty,
            CASE WHEN "Entity Type Code" = '1' THEN 'individual' ELSE 'organization' END AS entity_type
        FROM read_csv_auto(?, header=true, sample_size=10000)
        WHERE NPI IN (SELECT DISTINCT billing_npi FROM claims)
    """, [nppes_csv_path])
    count = con.execute("SELECT COUNT(*) FROM providers").fetchone()[0]
    logger.info(f'  Loaded {count:,} providers from NPPES')
    return count
