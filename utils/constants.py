"""Project-wide constants — single source of truth.

Consolidates TOP_30_CODES, HCPCS_CATEGORIES, SPECIALTIES, EM_FAMILIES,
TIMED_CODES, PHYSICAL_LIMITS, and financial pruning thresholds that were
previously duplicated across 04_generate_hypotheses.py, 07_run_domain_rules.py,
and 09_financial_impact.py.
"""

# ── Top HCPCS codes by spending ─────────────────────────────────────────
TOP_30_CODES = [
    'T1019', 'T1015', '99213', '99214', 'H0015', 'T2003', 'T1005', '99215',
    'T2025', '99212', 'T1020', 'H2015', 'H2016', '99203', '99204', '99202',
    '99211', 'T2024', '97110', '97530', '92507', '97140', '97116', '90834',
    '90837', '90832', 'H0031', 'H0036', 'H0004', 'T1017',
]

TOP_20_CODES = TOP_30_CODES[:20]

# ── HCPCS categories ────────────────────────────────────────────────────
HCPCS_CATEGORIES = [
    'Home Health', 'Behavioral Health', 'E&M', 'DME', 'Lab',
    'Pharmacy', 'Therapy', 'Transportation', 'Temp/Waiver', 'Other',
]

# ── IQR metrics (provider_summary columns) ──────────────────────────────
IQR_METRICS = [
    'total_paid', 'total_claims', 'total_beneficiaries', 'avg_paid_per_claim',
    'avg_claims_per_bene', 'num_codes', 'num_months',
]

# ── Specialties for peer comparison ─────────────────────────────────────
SPECIALTIES = [
    'Family Medicine', 'Internal Medicine', 'Pediatrics', 'Nurse Practitioner',
    'Clinical Social Worker', 'Psychologist', 'Physical Therapist',
    'Occupational Therapist', 'Speech-Language Pathologist', 'Home Health Agency',
    'Community/Behavioral Health', 'Pharmacist', 'Dentist', 'Chiropractor',
    'DME Supplier', 'Ambulance', 'Skilled Nursing Facility', 'Clinic/Center',
    'Counselor', 'Mental Health Counselor',
]

# ── E&M level families (superset from 04 + 07) ─────────────────────────
EM_FAMILIES = {
    'office_established': ['99211', '99212', '99213', '99214', '99215'],
    'office_new': ['99201', '99202', '99203', '99204', '99205'],
    'ed_visit': ['99281', '99282', '99283', '99284', '99285'],
    'hospital_initial': ['99221', '99222', '99223'],
    'hospital_subsequent': ['99231', '99232', '99233'],
}

# ── Timed service codes with physical limits ────────────────────────────
# (code, unit_minutes, max_units_per_bene_per_month)
TIMED_CODES = [
    ('T1019', 15, 480), ('T1020', 1440, 31), ('T1005', 15, 480),
    ('S5125', 15, 480), ('S5130', 15, 480), ('S5150', 15, 480),
    ('H0015', 15, 192), ('H2015', 15, 480), ('H2016', 60, 120),
    ('H0036', 15, 480), ('T1016', 15, 192), ('T1017', 15, 192),
    ('H2017', 15, 480), ('T2020', 15, 480), ('H2019', 15, 480),
]

# ── Physical limits for domain rule detection ───────────────────────────
PHYSICAL_LIMITS = {
    'T1019': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Personal Care 15min'},
    'T1020': {'unit_minutes': 1440, 'max_units_per_bene_per_month': 31, 'desc': 'Personal Care per diem'},
    'T1005': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Respite Care 15min'},
    'S5125': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Attendant Care 15min'},
    'S5130': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Homemaker 15min'},
    'S5150': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Unskilled Respite 15min'},
    'H0015': {'unit_minutes': 15, 'max_units_per_bene_per_month': 192, 'desc': 'Intensive Outpatient'},
    'H2015': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Community Support 15min'},
    'H2016': {'unit_minutes': 60, 'max_units_per_bene_per_month': 120, 'desc': 'Community Support per hr'},
    'H0036': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Psychiatric Support 15min'},
    'T1016': {'unit_minutes': 15, 'max_units_per_bene_per_month': 192, 'desc': 'Case Management 15min'},
    'T1017': {'unit_minutes': 15, 'max_units_per_bene_per_month': 192, 'desc': 'Targeted Case Mgmt 15min'},
    'H2017': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Psychosocial Rehab 15min'},
    'T2020': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Day Habilitation 15min'},
    'H2019': {'unit_minutes': 15, 'max_units_per_bene_per_month': 480, 'desc': 'Therapeutic Behavioral 15min'},
}

# ── Financial impact pruning thresholds ─────────────────────────────────
PRUNE_MIN_FLAGGED = 50
PRUNE_HOLDOUT_RATE_MULT = 0.5
PRUNE_Z_DELTA = -0.5

# ── Confidence tiers ────────────────────────────────────────────────────
CONFIDENCE_TIERS = {
    'high': {'min_score': 0.8, 'label': 'High'},
    'medium': {'min_score': 0.5, 'label': 'Medium'},
    'low': {'min_score': 0.2, 'label': 'Low'},
}

# ── Findings file names ────────────────────────────────────────────────
FINDINGS_FILES = [
    'categories_1_to_5.json',
    'categories_6_and_7.json',
    'category_8.json',
    'categories_9_and_10.json',
]

# ── 8090 Design System tokens (for reports and visualizations) ──────────
DESIGN_8090 = {
    'brand_blue': '#0052CC',
    'bg_canvas': '#f8fafc',       # slate-50
    'surface': '#ffffff',
    'surface_alt': '#f1f5f9',     # slate-100
    'border': '#e2e8f0',          # slate-200
    'text_secondary': '#64748b',  # slate-500
    'text_body': '#334155',       # slate-700
    'text_headline': '#020617',   # slate-950
    'text_muted': '#94a3b8',      # slate-400
    'error': '#ef4444',           # red-500
    'font_sans': 'IBM Plex Sans',
    'font_mono': 'Geist Mono',
}

# ── HHS OpenData design constants (for matplotlib charts) ───────────────
HHS_COLORS = {
    'amber': '#F59F0A',
    'dark': '#221E1C',
    'muted': '#78716D',
    'bg': '#FFFFFF',
    'page_bg': '#F8F7F2',
    'red': '#B91C1C',
    'green': '#15803D',
    'grid': '#E5E2DC',
    'border': '#221E1C',
}
