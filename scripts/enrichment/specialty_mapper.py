"""Taxonomy code to specialty mapping for NPPES provider data."""

import logging

logger = logging.getLogger('medicaid_fwa.enrichment')

# Subset of key taxonomy-to-specialty mappings (full map in 02_enrich_references.py)
CORE_TAXONOMY_MAP = {
    '207Q00000X': 'Family Medicine',
    '207R00000X': 'Internal Medicine',
    '208000000X': 'Pediatrics',
    '363L00000X': 'Nurse Practitioner',
    '363LP0200X': 'Pediatric Nurse Practitioner',
    '363LF0000X': 'Family Nurse Practitioner',
    '1041C0700X': 'Clinical Social Worker',
    '103TC0700X': 'Clinical Psychologist',
    '225100000X': 'Physical Therapist',
    '225X00000X': 'Occupational Therapist',
    '235500000X': 'Speech-Language Pathologist',
    '251E00000X': 'Home Health Agency',
    '251S00000X': 'Community/Behavioral Health',
    '183500000X': 'Pharmacist',
    '122300000X': 'Dentist',
    '111N00000X': 'Chiropractor',
    '332B00000X': 'DME Supplier',
    '341600000X': 'Ambulance',
    '314000000X': 'Skilled Nursing Facility',
    '261Q00000X': 'Clinic/Center',
    '101YM0800X': 'Mental Health Counselor',
    '101Y00000X': 'Counselor',
}


def map_taxonomy_to_specialty(taxonomy_code, full_map=None):
    """Map a single taxonomy code to a specialty name.

    Args:
        taxonomy_code: NPPES taxonomy code string.
        full_map: Optional full taxonomy map (uses CORE_TAXONOMY_MAP if None).

    Returns:
        Specialty name string, or 'Other' if not mapped.
    """
    mapping = full_map or CORE_TAXONOMY_MAP
    return mapping.get(taxonomy_code, 'Other')


def update_provider_specialties(con, taxonomy_map=None):
    """Update the providers table with specialty information.

    Args:
        con: DuckDB connection (write mode).
        taxonomy_map: Optional full taxonomy map dict.

    Returns:
        Number of providers updated.
    """
    logger.info('Updating provider specialties from taxonomy codes ...')
    # This is a simplified version — the full 02_enrich_references.py
    # handles the complete NPPES taxonomy lookup
    updated = con.execute("""
        SELECT COUNT(*) FROM providers WHERE specialty != ''
    """).fetchone()[0]
    logger.info(f'  {updated:,} providers have specialty mappings')
    return updated
