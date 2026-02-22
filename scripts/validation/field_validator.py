"""Per-field validation for CSV records — NPI, dates, numerics."""

import re

MONTH_RE = re.compile(r'^\d{4}-\d{2}$')


def validate_npi(npi_value, allow_empty=False):
    """Validate a 10-digit NPI number.

    Returns:
        True if valid, False otherwise.
    """
    if not npi_value:
        return allow_empty
    return npi_value.isdigit() and len(npi_value) == 10


def validate_hcpcs(hcpcs_value):
    """Validate HCPCS code is non-empty."""
    return bool(hcpcs_value)


def validate_claim_month(month_value):
    """Validate YYYY-MM format and valid month range.

    Returns:
        True if valid.
    """
    if not MONTH_RE.match(month_value):
        return False
    mo = int(month_value[5:7])
    return 1 <= mo <= 12


def validate_integer(value, allow_negative=False):
    """Validate integer field.

    Returns:
        tuple of (valid: bool, parsed_value: int or None)
    """
    try:
        v = int(value)
        if not allow_negative and v < 0:
            return False, None
        return True, v
    except (ValueError, TypeError):
        return False, None


def validate_float(value):
    """Validate float/decimal field.

    Returns:
        tuple of (valid: bool, parsed_value: float or None)
    """
    try:
        return True, float(value)
    except (ValueError, TypeError):
        return False, None


def validate_row_fields(row):
    """Validate all fields in a 7-column claims row.

    Args:
        row: List of 7 string values.

    Returns:
        list of reason strings (empty if all valid).
    """
    billing_npi, servicing_npi, hcpcs, claim_month, bene, claims, paid = row
    reasons = []

    if not validate_npi(billing_npi):
        reasons.append('billing_npi')
    if servicing_npi and not validate_npi(servicing_npi, allow_empty=True):
        reasons.append('servicing_npi')
    if not validate_hcpcs(hcpcs):
        reasons.append('hcpcs')
    if not validate_claim_month(claim_month):
        reasons.append('claim_month')

    bene_ok, _ = validate_integer(bene)
    if not bene_ok:
        reasons.append('beneficiaries')

    claims_ok, _ = validate_integer(claims)
    if not claims_ok:
        reasons.append('claims')

    paid_ok, _ = validate_float(paid)
    if not paid_ok:
        reasons.append('paid')

    return reasons
