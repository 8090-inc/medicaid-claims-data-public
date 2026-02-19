"""LEIE (List of Excluded Individuals/Entities) download and parsing utilities.

Downloads the OIG exclusion database from exclusions.oig.hhs.gov and provides
lookup functions for cross-referencing billing/servicing NPIs.
"""

import csv
import io
import os
import zipfile
from datetime import datetime

import requests

LEIE_URL = 'https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv'
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEIE_DIR = os.path.join(PROJECT_ROOT, 'reference_data', 'leie')
LEIE_CSV_PATH = os.path.join(LEIE_DIR, 'UPDATED.csv')


def download_leie(force=False):
    """Download the LEIE CSV from OIG. Returns path to CSV file.

    Args:
        force: If True, re-download even if file exists.

    Returns:
        Path to the downloaded CSV file, or None if download fails.
    """
    os.makedirs(LEIE_DIR, exist_ok=True)

    if os.path.exists(LEIE_CSV_PATH) and not force:
        age_hours = (datetime.now().timestamp() - os.path.getmtime(LEIE_CSV_PATH)) / 3600
        if age_hours < 168:  # Less than 7 days old
            print(f"  LEIE file exists and is {age_hours:.0f}h old, using cached version")
            return LEIE_CSV_PATH

    print(f"  Downloading LEIE from {LEIE_URL} ...")
    try:
        resp = requests.get(LEIE_URL, timeout=120)
        resp.raise_for_status()

        # Check if it's a ZIP file
        if resp.content[:2] == b'PK':
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                csv_names = [n for n in zf.namelist() if n.endswith('.csv')]
                if csv_names:
                    with open(LEIE_CSV_PATH, 'wb') as f:
                        f.write(zf.read(csv_names[0]))
        else:
            with open(LEIE_CSV_PATH, 'wb') as f:
                f.write(resp.content)

        print(f"  LEIE downloaded to {LEIE_CSV_PATH} ({os.path.getsize(LEIE_CSV_PATH):,} bytes)")
        return LEIE_CSV_PATH

    except Exception as e:
        print(f"  WARNING: Failed to download LEIE: {e}")
        if os.path.exists(LEIE_CSV_PATH):
            print(f"  Using previously cached LEIE file")
            return LEIE_CSV_PATH
        return None


def parse_leie(csv_path=None):
    """Parse LEIE CSV into a list of exclusion records.

    Returns:
        List of dicts with keys: lastname, firstname, busname, npi, address, city, state,
        zip, excltype, excldate, reindate, waiverdate, waiverstate.
        Returns empty list if file not found.
    """
    csv_path = csv_path or LEIE_CSV_PATH
    if not os.path.exists(csv_path):
        print(f"  LEIE file not found at {csv_path}")
        return []

    records = []
    try:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = {
                    'lastname': (row.get('LASTNAME', '') or '').strip().upper(),
                    'firstname': (row.get('FIRSTNAME', '') or '').strip().upper(),
                    'busname': (row.get('BUSNAME', '') or '').strip().upper(),
                    'npi': (row.get('NPI', '') or '').strip(),
                    'address': (row.get('ADDRESS', '') or '').strip().upper(),
                    'city': (row.get('CITY', '') or '').strip().upper(),
                    'state': (row.get('STATE', '') or '').strip().upper(),
                    'zip': (row.get('ZIP', '') or '').strip(),
                    'excltype': (row.get('EXCLTYPE', '') or '').strip(),
                    'excldate': (row.get('EXCLDATE', '') or '').strip(),
                    'reindate': (row.get('REINDATE', '') or '').strip(),
                    'waiverdate': (row.get('WAIVERDATE', '') or '').strip(),
                    'waiverstate': (row.get('WAIVERSTATE', '') or '').strip(),
                }
                records.append(record)
    except Exception as e:
        print(f"  WARNING: Failed to parse LEIE: {e}")
        return []

    print(f"  Parsed {len(records)} LEIE exclusion records")
    return records


def build_leie_npi_set(records=None):
    """Build a set of NPIs from LEIE records (only currently excluded, no reinstatement).

    Args:
        records: List of LEIE records from parse_leie(). If None, downloads and parses.

    Returns:
        Set of NPI strings that are currently excluded.
    """
    if records is None:
        csv_path = download_leie()
        if not csv_path:
            return set()
        records = parse_leie(csv_path)

    excluded_npis = set()
    for r in records:
        npi = r.get('npi', '').strip()
        reindate = r.get('reindate', '').strip()
        # Only include if NPI is present and not reinstated
        if npi and len(npi) == 10 and not reindate:
            excluded_npis.add(npi)

    print(f"  {len(excluded_npis)} currently excluded NPIs with valid NPI numbers")
    return excluded_npis


def build_leie_name_address_index(records=None):
    """Build name+address lookup from LEIE records for fuzzy matching.

    Returns:
        Dict mapping (lastname, state) -> list of records for that name+state.
    """
    if records is None:
        csv_path = download_leie()
        if not csv_path:
            return {}
        records = parse_leie(csv_path)

    index = {}
    for r in records:
        if not r.get('reindate'):  # Currently excluded
            key = (r['lastname'], r['state'])
            index.setdefault(key, []).append(r)

    return index
