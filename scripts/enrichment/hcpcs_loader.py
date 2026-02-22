"""HCPCS code description loading and management."""

import csv
import json
import logging
import os

from config.project_config import HCPCS_DIR

logger = logging.getLogger('medicaid_fwa.enrichment')


def load_hcpcs_descriptions(hcpcs_dir=None):
    """Load HCPCS code descriptions from reference data.

    Args:
        hcpcs_dir: Directory containing HCPCS description files.

    Returns:
        dict mapping hcpcs_code -> description string.
    """
    hcpcs_dir = hcpcs_dir or HCPCS_DIR
    descriptions = {}

    if not os.path.isdir(hcpcs_dir):
        logger.warning(f'HCPCS directory not found: {hcpcs_dir}')
        return descriptions

    for fname in os.listdir(hcpcs_dir):
        fpath = os.path.join(hcpcs_dir, fname)
        if fname.endswith('.json'):
            with open(fpath) as f:
                data = json.load(f)
            if isinstance(data, dict):
                descriptions.update(data)
            elif isinstance(data, list):
                for item in data:
                    if 'code' in item and 'description' in item:
                        descriptions[item['code']] = item['description']
        elif fname.endswith('.csv'):
            with open(fpath) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = row.get('code') or row.get('HCPCS')
                    desc = row.get('description') or row.get('DESCRIPTION')
                    if code and desc:
                        descriptions[code] = desc

    logger.info(f'Loaded {len(descriptions)} HCPCS descriptions')
    return descriptions


def create_hcpcs_table(con, descriptions):
    """Create hcpcs_descriptions table in DuckDB.

    Args:
        con: DuckDB connection (write mode).
        descriptions: dict mapping code -> description.
    """
    con.execute("DROP TABLE IF EXISTS hcpcs_descriptions")
    con.execute("CREATE TABLE hcpcs_descriptions (hcpcs_code VARCHAR, description VARCHAR)")
    for code, desc in descriptions.items():
        con.execute("INSERT INTO hcpcs_descriptions VALUES (?, ?)", [code, desc])
    logger.info(f'Created hcpcs_descriptions table: {len(descriptions)} codes')
