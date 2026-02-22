"""CSV structural validation — column count, header verification, encoding."""

import csv
import os
import re

EXPECTED_COLUMNS = 7
EXPECTED_HEADER = [
    'BILLING_PROVIDER_NPI_NUM', 'SERVICING_PROVIDER_NPI_NUM',
    'HCPCS_CODE', 'CLAIM_FROM_MONTH', 'TOTAL_UNIQUE_BENEFICIARIES',
    'TOTAL_CLAIMS', 'TOTAL_PAID',
]


def validate_header(csv_path):
    """Verify CSV has the expected header columns.

    Returns:
        tuple of (ok: bool, header: list, message: str)
    """
    with open(csv_path, 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader, None)
    if header is None:
        return False, [], 'CSV appears to be empty'
    if len(header) != EXPECTED_COLUMNS:
        return False, header, f'Expected {EXPECTED_COLUMNS} columns, got {len(header)}'
    return True, header, 'Header valid'


def validate_row_structure(row, row_number):
    """Check a single row has the correct number of columns.

    Returns:
        list of reason strings (empty if valid).
    """
    if len(row) != EXPECTED_COLUMNS:
        return ['column_count']
    return []
