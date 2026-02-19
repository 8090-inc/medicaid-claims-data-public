#!/usr/bin/env python3
"""Milestone 2: Reference data enrichment.

Downloads NPPES provider registry and creates HCPCS code descriptions table.
Joins with claims data so findings include provider names, specialties, and states.
"""

import os
import sys
import time
import zipfile
import glob
import csv
import io
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.db_utils import get_connection

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NPPES_DIR = os.path.join(PROJECT_ROOT, 'reference_data', 'nppes')
HCPCS_DIR = os.path.join(PROJECT_ROOT, 'reference_data', 'hcpcs')

# Top 200 taxonomy code to specialty mappings
TAXONOMY_MAP = {
    '101Y00000X': 'Counselor',
    '101YA0400X': 'Addiction Counselor',
    '101YM0800X': 'Mental Health Counselor',
    '101YP1600X': 'Pastoral Counselor',
    '101YP2500X': 'Professional Counselor',
    '101YS0200X': 'School Counselor',
    '102L00000X': 'Psychoanalyst',
    '103T00000X': 'Psychologist',
    '103TA0400X': 'Addiction Psychologist',
    '103TC0700X': 'Clinical Psychologist',
    '103TC2200X': 'Clinical Child Psychologist',
    '104100000X': 'Social Worker',
    '1041C0700X': 'Clinical Social Worker',
    '106H00000X': 'Marriage & Family Therapist',
    '111N00000X': 'Chiropractor',
    '122300000X': 'Dentist',
    '133V00000X': 'Dietitian/Nutritionist',
    '136A00000X': 'Diet Technician',
    '146D00000X': 'Personal Emergency Response',
    '146L00000X': 'Emergency Medical Technician',
    '146M00000X': 'Paramedic',
    '152W00000X': 'Optometrist',
    '156F00000X': 'Technician/Technologist',
    '163W00000X': 'Registered Nurse',
    '163WA0400X': 'Addiction Nurse',
    '163WG0100X': 'Gastroenterology Nurse',
    '163WP0808X': 'Psychiatric Nurse',
    '163WP0809X': 'Psych/Mental Health Nurse',
    '163WP2201X': 'Ambulatory Care Nurse',
    '164W00000X': 'Licensed Practical Nurse',
    '167G00000X': 'Psychiatric Technician',
    '170100000X': 'PhD Medical Genetics',
    '171000000X': 'Military Health',
    '171100000X': 'Acupuncturist',
    '171M00000X': 'Case Manager/Care Coordinator',
    '172A00000X': 'Driver',
    '174400000X': 'Specialist',
    '174M00000X': 'Veterinarian',
    '175F00000X': 'Naturopath',
    '175L00000X': 'Homeopath',
    '175M00000X': 'Midwife',
    '176B00000X': 'Midwife',
    '176P00000X': 'Funeral Director',
    '183500000X': 'Pharmacist',
    '1835P1300X': 'Pharmacotherapy Pharmacist',
    '193200000X': 'Multi-Specialty Group',
    '193400000X': 'Single Specialty Group',
    '202C00000X': 'Independent Medical Examiner',
    '204C00000X': 'Neuromusculoskeletal Medicine',
    '204D00000X': 'Neuromusculoskeletal Sports Med',
    '204E00000X': 'Oral & Maxillofacial Surgery',
    '207K00000X': 'Allergy & Immunology',
    '207L00000X': 'Anesthesiology',
    '207N00000X': 'Dermatology',
    '207P00000X': 'Emergency Medicine',
    '207Q00000X': 'Family Medicine',
    '207R00000X': 'Internal Medicine',
    '207RC0000X': 'Cardiovascular Disease',
    '207RE0101X': 'Endocrinology',
    '207RG0100X': 'Gastroenterology',
    '207RH0000X': 'Hematology',
    '207RI0001X': 'Clinical & Lab Immunology',
    '207RI0008X': 'Hepatology',
    '207RI0011X': 'Interventional Cardiology',
    '207RI0200X': 'Infectious Disease',
    '207RN0300X': 'Nephrology',
    '207RP1001X': 'Pulmonary Disease',
    '207RR0500X': 'Rheumatology',
    '207RS0010X': 'Sports Medicine',
    '207RS0012X': 'Sleep Medicine',
    '207T00000X': 'Neurological Surgery',
    '207U00000X': 'Nuclear Medicine',
    '207V00000X': 'Obstetrics & Gynecology',
    '207VB0002X': 'Bariatric Medicine',
    '207W00000X': 'Ophthalmology',
    '207X00000X': 'Orthopaedic Surgery',
    '207Y00000X': 'Otolaryngology',
    '208000000X': 'Pediatrics',
    '2080A0000X': 'Adolescent Medicine',
    '2080P0006X': 'Developmental Pediatrics',
    '2080P0008X': 'Neurodevelopmental Pediatrics',
    '208100000X': 'Physical Med & Rehabilitation',
    '208200000X': 'Plastic Surgery',
    '208600000X': 'Surgery',
    '2086S0102X': 'Surgical Critical Care',
    '2086S0105X': 'Hand Surgery',
    '2086S0120X': 'Pediatric Surgery',
    '2086S0122X': 'Plastic Surgery within Head & Neck',
    '2086S0127X': 'Trauma Surgery',
    '2086S0129X': 'Vascular Surgery',
    '208800000X': 'Urology',
    '208C00000X': 'Colon & Rectal Surgery',
    '208D00000X': 'General Practice',
    '208G00000X': 'Thoracic Surgery',
    '208M00000X': 'Hospitalist',
    '208VP0000X': 'Pain Medicine',
    '208VP0014X': 'Interventional Pain Medicine',
    '209800000X': 'Legal Medicine',
    '211D00000X': 'Podiatric Assistant',
    '213E00000X': 'Podiatrist',
    '221700000X': 'Art Therapist',
    '222Z00000X': 'Occupational Therapy Assistant',
    '224P00000X': 'Pharmacy Technician',
    '224Z00000X': 'Occupational Therapy Assistant',
    '225000000X': 'Orthotic Fitter',
    '225100000X': 'Physical Therapist',
    '2251C2600X': 'Cardiopulmonary PT',
    '2251E1300X': 'Electrophysiology PT',
    '2251G0304X': 'Geriatric PT',
    '2251H1200X': 'Hand PT',
    '2251H1300X': 'Human Factors PT',
    '2251N0400X': 'Neurology PT',
    '2251P0200X': 'Pediatric PT',
    '2251S0007X': 'Sports PT',
    '225200000X': 'Physical Therapy Assistant',
    '225400000X': 'Rehabilitation Practitioner',
    '225500000X': 'Respiratory/Developmental/Rehab',
    '225600000X': 'Dance Therapist',
    '225700000X': 'Massage Therapist',
    '225800000X': 'Recreation Therapist',
    '225A00000X': 'Music Therapist',
    '225B00000X': 'Pulmonary Function Technologist',
    '225C00000X': 'Rehabilitation Counselor',
    '225CA2400X': 'Assistive Technology Practitioner',
    '225CA2500X': 'Assistive Technology Supplier',
    '225X00000X': 'Occupational Therapist',
    '225XE1200X': 'Ergonomics OT',
    '225XH1200X': 'Hand OT',
    '225XH1300X': 'Human Factors OT',
    '225XN1300X': 'Neurorehab OT',
    '225XP0200X': 'Pediatric OT',
    '226300000X': 'Kinesiotherapist',
    '227800000X': 'Respiratory Therapist',
    '227900000X': 'Respiratory Therapy Technician',
    '229N00000X': 'Anaplastologist',
    '231H00000X': 'Audiologist',
    '235500000X': 'Speech-Language Pathologist',
    '235Z00000X': 'Speech-Language Pathology Asst',
    '237600000X': 'Audiologist-Hearing Aid Fitter',
    '237700000X': 'Hearing Instrument Specialist',
    '242T00000X': 'Perfusionist',
    '243U00000X': 'Radiology Practitioner Asst',
    '246Q00000X': 'Pathology Technician',
    '246R00000X': 'Radiology Technician',
    '246W00000X': 'Cardiology Technician',
    '246X00000X': 'Cardiovascular Technologist',
    '246Y00000X': 'Health Information Technician',
    '246Z00000X': 'Other Technician',
    '247000000X': 'Health Info Management Tech',
    '247100000X': 'Radiologic Technologist',
    '247200000X': 'Diagnostic Technologist',
    '251300000X': 'Local Education Agency (LEA)',
    '251B00000X': 'Case Management Agency',
    '251C00000X': 'Day Training/Habilitation',
    '251E00000X': 'Home Health Agency',
    '251F00000X': 'Home Infusion',
    '251G00000X': 'Hospice',
    '251J00000X': 'Nursing Facility',
    '251K00000X': 'Nursing Home',
    '251S00000X': 'Community/Behavioral Health',
    '251V00000X': 'Voluntary/Non-Profit',
    '251X00000X': 'Supports Brokerage',
    '252Y00000X': 'Early Intervention Provider',
    '253J00000X': 'Foster Care Agency',
    '253Z00000X': 'In Home Supportive Care',
    '261Q00000X': 'Clinic/Center',
    '261QA0600X': 'Adult Day Care',
    '261QA1903X': 'Ambulatory Surgical',
    '261QB0400X': 'Birthing Center',
    '261QC0050X': 'Critical Access Hospital',
    '261QC1500X': 'Community Health Center',
    '261QC1800X': 'Corporate Health',
    '261QD0000X': 'Dental Clinic',
    '261QD1600X': 'Developmental Disabilities',
    '261QE0002X': 'Emergency Care',
    '261QE0700X': 'End-Stage Renal Disease',
    '261QF0050X': 'Family Planning',
    '261QF0400X': 'Federally Qualified Health Ctr',
    '261QH0100X': 'Health Service',
    '261QM0801X': 'Mental Health Center',
    '261QM0850X': 'Adult Mental Health',
    '261QM0855X': 'Adolescent/Children MH',
    '261QM1000X': 'Migrant Health Center',
    '261QP2300X': 'Primary Care',
    '261QR0200X': 'Radiology Center',
    '261QR0400X': 'Rehabilitation Center',
    '261QR0405X': 'Rehab Substance Use Disorder',
    '261QR0800X': 'Recovery Care',
    '261QR1300X': 'Rural Health',
    '261QS0112X': 'Oral Surgery',
    '261QS0132X': 'Ophthalmologic Surgery',
    '261QS1000X': 'Student Health',
    '261QU0200X': 'Urgent Care',
    '261QX0100X': 'Occupational Medicine',
    '273R00000X': 'Psychiatric Hospital',
    '273Y00000X': 'Rehabilitation Hospital',
    '275N00000X': 'Medicare-Medicaid Hospital',
    '276400000X': 'Rehab Hosp',
    '281P00000X': 'Chronic Disease Hospital',
    '282N00000X': 'General Acute Care Hospital',
    '282NC0060X': 'Critical Access',
    '283Q00000X': 'Psychiatric Hospital',
    '283X00000X': 'Rehab Hospital',
    '284300000X': 'Special Hospital',
    '286500000X': 'Military Hospital',
    '287300000X': 'Christian Science Sanitorium',
    '291900000X': 'Military Clinical Lab',
    '291U00000X': 'Clinical Lab',
    '292200000X': 'Dental Lab',
    '293D00000X': 'Physiological Lab',
    '302F00000X': 'Exclusive Provider Organization',
    '302R00000X': 'HMO',
    '305R00000X': 'Preferred Provider Organization',
    '305S00000X': 'POS',
    '310400000X': 'Assisted Living Facility',
    '310500000X': 'Intermediate Care (MR)',
    '311500000X': 'Alzheimer Center',
    '311Z00000X': 'Custodial Care Facility',
    '313M00000X': 'Nursing Facility',
    '314000000X': 'Skilled Nursing Facility',
    '315D00000X': 'Hospice Inpatient',
    '315P00000X': 'Intermediate Care (MR)',
    '317400000X': 'Christian Science Facility',
    '320600000X': 'Intellectual Disabilities ICF',
    '320700000X': 'Mentally Retarded ICF',
    '320800000X': 'MR ICF',
    '320900000X': 'ID/MR Community',
    '322D00000X': 'Residential Treatment (Psych)',
    '323P00000X': 'Psychiatric Residential',
    '324500000X': 'Substance Abuse Rehab',
    '331L00000X': 'Blood Bank',
    '332000000X': 'Military/VA Pharmacy',
    '332100000X': 'DOD Pharmacy',
    '332800000X': 'Indian Health Service Pharmacy',
    '332900000X': 'Non-Pharmacy Dispensing Site',
    '332B00000X': 'DME Supplier',
    '332BN1400X': 'Customized DME',
    '332BP3500X': 'Parenteral & Enteral DME',
    '332G00000X': 'Eye Bank',
    '332H00000X': 'Eyewear Supplier',
    '332S00000X': 'Hearing Aid Equipment',
    '332U00000X': 'Home Delivered Meals',
    '333300000X': 'Emergency Response (Vehicle)',
    '333600000X': 'Pharmacy',
    '335E00000X': 'Prosthetic/Orthotic Supplier',
    '335G00000X': 'Medical Foods Supplier',
    '335U00000X': 'Organ Procurement Organization',
    '335V00000X': 'Portable X-Ray Supplier',
    '341600000X': 'Ambulance',
    '341800000X': 'Military Transport',
    '343800000X': 'Secured Transport',
    '343900000X': 'Non-Emergency Transport',
    '344600000X': 'Taxi',
    '344800000X': 'Air Transport',
    '347B00000X': 'Bus Transport',
    '347C00000X': 'Private Vehicle',
    '347D00000X': 'Train Transport',
    '347E00000X': 'Transportation Broker',
    '363A00000X': 'Physician Assistant',
    '363AM0700X': 'Medical PA',
    '363AS0400X': 'Surgical PA',
    '363L00000X': 'Nurse Practitioner',
    '363LA2100X': 'Acute Care NP',
    '363LA2200X': 'Adult Health NP',
    '363LC0200X': 'Critical Care NP',
    '363LC1500X': 'Community Health NP',
    '363LF0000X': 'Family NP',
    '363LG0600X': 'Gerontology NP',
    '363LN0000X': 'Neonatal NP',
    '363LN0005X': 'Critical Care Neonatal NP',
    '363LP0200X': 'Pediatric NP',
    '363LP0222X': 'Critical Care Pediatric NP',
    '363LP0808X': 'Psychiatric NP',
    '363LP1700X': 'Perinatal NP',
    '363LP2300X': 'Primary Care NP',
    '363LS0200X': 'School NP',
    '363LW0102X': "Women's Health NP",
    '363LX0001X': 'Obstetric-Gynecology NP',
    '364S00000X': 'Clinical Nurse Specialist',
    '367500000X': 'Nurse Anesthetist (CRNA)',
    '367A00000X': 'Advanced Practice Midwife',
    '367H00000X': 'Anesthesiologist Assistant',
    '372500000X': 'Chore Provider',
    '372600000X': 'Day Training Provider',
    '373H00000X': 'Day Training/Habilitation Spec',
    '374700000X': 'Technician',
    '374J00000X': 'Doula',
    '374K00000X': 'Religious Counselor',
    '374T00000X': 'Peer Specialist',
    '374U00000X': 'Health Educator',
    '376G00000X': 'Nursing Home Administrator',
    '376J00000X': 'Homemaker',
    '376K00000X': 'Nurse/Home Health Aide',
    '385H00000X': 'Respite Care',
    '385HR2050X': 'Respite Camp',
    '385HR2055X': 'Respite Child',
    '385HR2060X': 'Respite In-Home',
    '390200000X': 'Student',
}

# Top 100 HCPCS codes by spending (publicly available from CMS)
HCPCS_DESCRIPTIONS = {
    'T1019': 'Personal Care Services (15 min)',
    'T1015': 'Clinic Visit/Encounter',
    '99213': 'Office Visit, Est Patient (Low)',
    '99214': 'Office Visit, Est Patient (Moderate)',
    'H0015': 'Alcohol/Drug Intensive Outpatient',
    'T2003': 'Non-Emergency Transport',
    'T1005': 'Respite Care (15 min)',
    '99215': 'Office Visit, Est Patient (High)',
    'T2025': 'Waiver Services NOS',
    '99212': 'Office Visit, Est Patient (Straightforward)',
    'T1020': 'Personal Care Services (per diem)',
    'H2015': 'Comprehensive Community Support',
    'H2016': 'Comprehensive Community Support (per hr)',
    '99203': 'Office Visit, New Patient (Low)',
    '99204': 'Office Visit, New Patient (Moderate)',
    '99202': 'Office Visit, New Patient (Straightforward)',
    '99211': 'Office Visit, Est Patient (Minimal)',
    'T2024': 'Service Plan Development',
    '97110': 'Therapeutic Exercise',
    '97530': 'Therapeutic Activities',
    '92507': 'Speech/Language Treatment',
    '97140': 'Manual Therapy',
    '97116': 'Gait Training',
    '97161': 'PT Evaluation (Low Complexity)',
    '97163': 'PT Evaluation (High Complexity)',
    '97162': 'PT Evaluation (Moderate)',
    '90834': 'Psychotherapy 45 min',
    '90837': 'Psychotherapy 60 min',
    '90832': 'Psychotherapy 30 min',
    '90847': 'Family Psychotherapy w/Patient',
    '90846': 'Family Psychotherapy w/o Patient',
    '90853': 'Group Psychotherapy',
    '90791': 'Psychiatric Diagnostic Evaluation',
    '90792': 'Psych Diagnostic Eval w/Medical',
    'H0031': 'Mental Health Assessment',
    'H0032': 'Mental Health Plan Development',
    'H0036': 'Community Psychiatric Support (15 min)',
    'H0020': 'Alcohol/Drug Services Behavioral',
    'H0004': 'Behavioral Health Counseling',
    'H0005': 'Alcohol/Drug Group Counseling',
    'H0001': 'Alcohol/Drug Assessment',
    'H0035': 'Mental Health Partial Hospitalization',
    'H0033': 'Oral Medication Admin (per 15 min)',
    'H0034': 'Medication Training',
    'H0038': 'Self-Help/Peer Services (per 15 min)',
    'H0039': 'Assertive Community Treatment',
    'H0040': 'Assertive Community Treatment per diem',
    'H0046': 'Mental Health Services NOS',
    'H2012': 'Behavioral Health Day Treatment (per hr)',
    'H2014': 'Skills Training & Development',
    'H2017': 'Psychosocial Rehab (per 15 min)',
    'H2019': 'Therapeutic Behavioral Svcs (15 min)',
    'H2023': 'Supported Employment (15 min)',
    'S5150': 'Unskilled Respite (15 min)',
    'S5151': 'Unskilled Respite (per diem)',
    'S5125': 'Attendant Care (15 min)',
    'S5130': 'Homemaker (15 min)',
    'S5135': 'Companion (15 min)',
    'S5170': 'Home Delivered Meals',
    'T1017': 'Targeted Case Management',
    'T1016': 'Case Management (per 15 min)',
    'T2028': 'Specialized Supply',
    'T2001': 'Non-Emergency Transport (per trip)',
    'T2002': 'Non-Emergency Transport (per mile)',
    'T2033': 'Residential Setting (per diem)',
    'T2020': 'Day Habilitation (15 min)',
    'T2021': 'Day Habilitation (per diem)',
    'A0428': 'BLS Ambulance Non-Emergency',
    'A0425': 'Ground Mileage',
    'A0426': 'ALS Ambulance Non-Emergency',
    'A0427': 'ALS Ambulance Emergency',
    'A0429': 'BLS Ambulance Emergency',
    'J7192': 'Factor VIII (per IU)',
    'J7195': 'Factor IX (per IU)',
    'J2794': 'Injection, Risperidone Long Acting',
    'J0885': 'Injection, Epoetin Alfa',
    'J1745': 'Injection, Infliximab',
    'J3490': 'Unclassified Drugs',
    'J7306': 'Levonorgestrel IUD',
    'J7307': 'Etonogestrel Implant',
    '99223': 'Initial Hospital Care (High)',
    '99222': 'Initial Hospital Care (Moderate)',
    '99232': 'Subsequent Hospital Care (Moderate)',
    '99233': 'Subsequent Hospital Care (High)',
    '99231': 'Subsequent Hospital Care (Low)',
    '99238': 'Hospital Discharge Day Mgmt 30 min',
    '99239': 'Hospital Discharge Day Mgmt 60+ min',
    '99281': 'ED Visit (Straightforward)',
    '99282': 'ED Visit (Low)',
    '99283': 'ED Visit (Moderate)',
    '99284': 'ED Visit (Moderate/High)',
    '99285': 'ED Visit (High)',
    '99291': 'Critical Care First 30-74 min',
    '99205': 'Office Visit, New Patient (High)',
    '85025': 'CBC with Differential',
    '80053': 'Comprehensive Metabolic Panel',
    '80048': 'Basic Metabolic Panel',
    '87491': 'Chlamydia Test (DNA Probe)',
    '36415': 'Venipuncture',
    '96372': 'Therapeutic Injection, SC/IM',
    'E1390': 'Oxygen Concentrator',
    'E0260': 'Hospital Bed Semi-Electric',
    'K0823': 'Power Wheelchair Group 2',
}


def categorize_hcpcs(code):
    """Assign category to an HCPCS code based on prefix."""
    if not code:
        return 'Other'
    c = code.upper()
    if c.startswith('T'):
        return 'Home Health'
    if c.startswith('H'):
        return 'Behavioral Health'
    if c.startswith('S'):
        return 'Temp/Waiver'
    if c.startswith('J'):
        return 'Pharmacy'
    if c.startswith(('A04', 'A0')):
        return 'Transportation'
    if c.startswith(('A', 'E', 'K', 'L')):
        return 'DME'
    if c.startswith('9921') or c.startswith('9920') or c.startswith('9922') or c.startswith('9923') or c.startswith('9928'):
        return 'E&M'
    if c.startswith(('908', '909')):
        return 'Behavioral Health'
    if c.startswith(('8', '87', '86', '85', '84', '83', '82', '81', '80')):
        return 'Lab'
    if c.startswith('97'):
        return 'Therapy'
    return 'Other'


def download_nppes(con):
    """Download NPPES data and load into DuckDB."""
    import datetime

    # Try current month first, then try recent months
    months_to_try = []
    now = datetime.datetime.now()
    for offset in range(0, 6):
        d = now - datetime.timedelta(days=30 * offset)
        months_to_try.append(d.strftime('%B_%Y'))

    nppes_zip = os.path.join(NPPES_DIR, 'nppes.zip')
    nppes_csv = None

    # Check if already downloaded/extracted
    existing = glob.glob(os.path.join(NPPES_DIR, 'npidata_pfile_*.csv'))
    if existing:
        nppes_csv = existing[0]
        print(f"  Using existing NPPES file: {nppes_csv}")
    else:
        # Check for local zip already placed in NPPES_DIR
        local_zips = glob.glob(os.path.join(NPPES_DIR, 'NPPES_Data_Dissemination_*.zip'))
        if local_zips:
            local_zips.sort(key=os.path.getmtime, reverse=True)
            local_zip = local_zips[0]
            print(f"  Using local NPPES zip: {local_zip}")
            try:
                with zipfile.ZipFile(local_zip, 'r') as zf:
                    for name in zf.namelist():
                        if name.startswith('npidata_pfile_') and name.endswith('.csv'):
                            zf.extract(name, NPPES_DIR)
                            nppes_csv = os.path.join(NPPES_DIR, name)
                            break
            except Exception as e:
                print(f"  Failed to extract local zip: {e}")

        if nppes_csv:
            load_nppes_from_csv(con, nppes_csv)
            return

        for month_year in months_to_try:
            url = f'https://download.cms.gov/nppes/NPPES_Data_Dissemination_{month_year}.zip'
            print(f"  Trying NPPES download: {url}")
            try:
                resp = requests.get(url, stream=True, timeout=30)
                if resp.status_code == 200:
                    print(f"  Downloading NPPES ({month_year}) ...")
                    with open(nppes_zip, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=8 * 1024 * 1024):
                            f.write(chunk)
                    print(f"  Extracting NPPES zip ...")
                    with zipfile.ZipFile(nppes_zip, 'r') as zf:
                        for name in zf.namelist():
                            if name.startswith('npidata_pfile_') and name.endswith('.csv'):
                                zf.extract(name, NPPES_DIR)
                                nppes_csv = os.path.join(NPPES_DIR, name)
                                break
                    if os.path.exists(nppes_zip):
                        os.remove(nppes_zip)
                    break
            except Exception as e:
                print(f"  Failed: {e}")
                continue

    if nppes_csv and os.path.exists(nppes_csv):
        load_nppes_from_csv(con, nppes_csv)
    else:
        print("  NPPES download failed - loading from NPPES API for top providers")
        load_nppes_from_api(con)


def load_nppes_from_csv(con, nppes_csv):
    """Load NPPES CSV into DuckDB, filtering to relevant NPIs."""
    print(f"  Loading NPPES from {nppes_csv} ...")

    # Get all unique NPIs from claims
    con.execute("DROP TABLE IF EXISTS providers")
    con.execute(f"""
        CREATE TABLE providers AS
        WITH claim_npis AS (
            SELECT DISTINCT billing_npi AS npi FROM claims
            UNION
            SELECT DISTINCT servicing_npi AS npi FROM claims
            WHERE servicing_npi IS NOT NULL AND servicing_npi != ''
        ),
        nppes_raw AS (
            SELECT
                "NPI"::VARCHAR AS npi,
                "Entity Type Code"::VARCHAR AS entity_type,
                "Provider Organization Name (Legal Business Name)"::VARCHAR AS org_name,
                "Provider Last Name (Legal Name)"::VARCHAR AS last_name,
                "Provider First Name"::VARCHAR AS first_name,
                "NPI Deactivation Date"::VARCHAR AS deactivation_date,
                "NPI Reactivation Date"::VARCHAR AS reactivation_date,
                "NPI Deactivation Reason Code"::VARCHAR AS deactivation_reason,
                "Provider Business Practice Location Address State Name"::VARCHAR AS state,
                "Provider Business Practice Location Address City Name"::VARCHAR AS city,
                "Provider First Line Business Practice Location Address"::VARCHAR AS addr1,
                "Provider Second Line Business Practice Location Address"::VARCHAR AS addr2,
                "Provider Business Practice Location Address Postal Code"::VARCHAR AS zip,
                "Provider First Line Business Mailing Address"::VARCHAR AS mail_addr1,
                "Provider Second Line Business Mailing Address"::VARCHAR AS mail_addr2,
                "Provider Business Mailing Address City Name"::VARCHAR AS mail_city,
                "Provider Business Mailing Address State Name"::VARCHAR AS mail_state,
                "Provider Business Mailing Address Postal Code"::VARCHAR AS mail_zip,
                "Healthcare Provider Taxonomy Code_1"::VARCHAR AS taxonomy
            FROM read_csv_auto('{nppes_csv}',
                header=true,
                sample_size=10000,
                ignore_errors=true,
                all_varchar=true,
                null_padding=true
            )
        )
        SELECT
            n.npi,
            n.entity_type,
            CASE
                WHEN n.entity_type = '2' THEN COALESCE(n.org_name, 'Organization')
                ELSE COALESCE(n.last_name || ', ' || n.first_name, 'Individual')
            END AS name,
            n.deactivation_date,
            n.reactivation_date,
            n.deactivation_reason,
            n.state,
            n.city,
            TRIM(COALESCE(n.addr1, '') || ' ' || COALESCE(n.addr2, '')) AS address,
            n.zip,
            TRIM(COALESCE(n.mail_addr1, '') || ' ' || COALESCE(n.mail_addr2, '')) AS mailing_address,
            n.mail_city,
            n.mail_state,
            n.mail_zip,
            n.taxonomy,
            '' AS specialty
        FROM nppes_raw n
        INNER JOIN claim_npis c ON n.npi = c.npi
    """)

    provider_count = con.execute("SELECT COUNT(*) FROM providers").fetchone()[0]
    print(f"  Loaded {provider_count:,} providers from NPPES bulk file")

    # Update specialty from taxonomy map
    _update_specialties(con)


def load_nppes_from_api(con):
    """Fallback: load top providers via NPPES API."""
    print("  Loading top 10,000 providers from NPPES API ...")

    # Get top NPIs by spending
    top_npis = con.execute("""
        SELECT billing_npi, total_paid
        FROM provider_summary
        ORDER BY total_paid DESC
        LIMIT 10000
    """).fetchall()

    records = []
    batch_size = 100
    for i in range(0, len(top_npis), batch_size):
        batch = top_npis[i:i + batch_size]
        for npi, paid in batch:
            try:
                url = f'https://npiregistry.cms.hhs.gov/api/?number={npi}&version=2.1'
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('result_count', 0) > 0:
                        r = data['results'][0]
                        basic = r.get('basic', {})
                        entity = r.get('enumeration_type', '')
                        is_org = entity == 'NPI-2'
                        if is_org:
                            name = basic.get('organization_name', 'Organization')
                        else:
                            name = f"{basic.get('last_name', '')}, {basic.get('first_name', '')}"
                        loc_addr = {}
                        mail_addr = {}
                        for a in r.get('addresses', []) or []:
                            if a.get('address_purpose') == 'LOCATION' and not loc_addr:
                                loc_addr = a
                            if a.get('address_purpose') == 'MAILING' and not mail_addr:
                                mail_addr = a
                        if not loc_addr:
                            loc_addr = r.get('addresses', [{}])[0] if r.get('addresses') else {}
                        tax = r.get('taxonomies', [{}])[0] if r.get('taxonomies') else {}
                        addr_line = " ".join(
                            [loc_addr.get('address_1', ''), loc_addr.get('address_2', '')]
                        ).strip()
                        mail_line = " ".join(
                            [mail_addr.get('address_1', ''), mail_addr.get('address_2', '')]
                        ).strip()
                        records.append({
                            'npi': npi,
                            'entity_type': '2' if is_org else '1',
                            'name': name,
                            'deactivation_date': basic.get('deactivation_date', ''),
                            'reactivation_date': basic.get('reactivation_date', ''),
                            'deactivation_reason': basic.get('deactivation_reason_code', ''),
                            'state': loc_addr.get('state', ''),
                            'city': loc_addr.get('city', ''),
                            'address': addr_line,
                            'zip': loc_addr.get('postal_code', ''),
                            'mailing_address': mail_line,
                            'mail_city': mail_addr.get('city', ''),
                            'mail_state': mail_addr.get('state', ''),
                            'mail_zip': mail_addr.get('postal_code', ''),
                            'taxonomy': tax.get('code', ''),
                        })
            except Exception:
                pass
        if i % 1000 == 0 and i > 0:
            print(f"    Fetched {i} of {len(top_npis)} ...")

    # Create table from records
    con.execute("DROP TABLE IF EXISTS providers")
    con.execute("""
        CREATE TABLE providers (
            npi VARCHAR, entity_type VARCHAR, name VARCHAR,
            deactivation_date VARCHAR, reactivation_date VARCHAR, deactivation_reason VARCHAR,
            state VARCHAR, city VARCHAR, address VARCHAR, zip VARCHAR,
            mailing_address VARCHAR, mail_city VARCHAR, mail_state VARCHAR, mail_zip VARCHAR,
            taxonomy VARCHAR, specialty VARCHAR
        )
    """)
    for r in records:
        con.execute(
            "INSERT INTO providers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '')",
            [
                r['npi'],
                r['entity_type'],
                r['name'],
                r.get('deactivation_date', ''),
                r.get('reactivation_date', ''),
                r.get('deactivation_reason', ''),
                r['state'],
                r['city'],
                r.get('address', ''),
                r.get('zip', ''),
                r.get('mailing_address', ''),
                r.get('mail_city', ''),
                r.get('mail_state', ''),
                r.get('mail_zip', ''),
                r['taxonomy'],
            ]
        )
    print(f"  Loaded {len(records)} providers from API")
    _update_specialties(con)


def _update_specialties(con):
    """Update specialty column from taxonomy code map."""
    for tax_code, specialty in TAXONOMY_MAP.items():
        con.execute(
            "UPDATE providers SET specialty = ? WHERE taxonomy = ?",
            [specialty, tax_code]
        )
    # Set remaining to category-level specialty
    con.execute("UPDATE providers SET specialty = 'Other' WHERE specialty = '' OR specialty IS NULL")
    sample = con.execute("SELECT npi, name, state, specialty FROM providers LIMIT 5").fetchall()
    print(f"  Sample providers: {sample}")


def create_hcpcs_table(con):
    """Create HCPCS code descriptions table."""
    print("Creating hcpcs_codes table ...")
    con.execute("DROP TABLE IF EXISTS hcpcs_codes")
    con.execute("""
        CREATE TABLE hcpcs_codes (
            hcpcs_code VARCHAR PRIMARY KEY,
            short_desc VARCHAR,
            category VARCHAR
        )
    """)

    loaded_external = False
    external_path = None
    if os.path.isdir(HCPCS_DIR):
        # Prefer the largest extracted file in the HCPCS folder
        candidates = []
        for ext in ('.csv', '.tsv', '.txt'):
            candidates.extend(glob.glob(os.path.join(HCPCS_DIR, f'*{ext}')))
        if candidates:
            candidates.sort(key=os.path.getsize, reverse=True)
            external_path = candidates[0]
        else:
            # If a zip is present, extract and re-scan
            zips = glob.glob(os.path.join(HCPCS_DIR, '*.zip'))
            if zips:
                zips.sort(key=os.path.getmtime, reverse=True)
                zip_path = zips[0]
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zf:
                        zf.extractall(HCPCS_DIR)
                    candidates = []
                    for ext in ('.csv', '.tsv', '.txt'):
                        candidates.extend(glob.glob(os.path.join(HCPCS_DIR, f'*{ext}')))
                    if candidates:
                        candidates.sort(key=os.path.getsize, reverse=True)
                        external_path = candidates[0]
                except Exception as e:
                    print(f"  Failed to extract HCPCS zip: {e}")

    if external_path and os.path.exists(external_path):
        print(f"  Loading HCPCS from {external_path} ...")
        try:
            rel = f"""
                read_csv_auto('{external_path}',
                    header=true,
                    sample_size=100000,
                    ignore_errors=true,
                    all_varchar=true,
                    null_padding=true,
                    strict_mode=false
                )
            """
            cols = con.execute(f"DESCRIBE SELECT * FROM {rel}").fetchall()
            col_names = [c[0] for c in cols]
            lower_map = {c.lower(): c for c in col_names}

            def pick_col(needles):
                for n in needles:
                    for c in col_names:
                        if n in c.lower():
                            return c
                return None

            code_col = pick_col(['hcpcs code', 'hcpcs_code', 'hcpcs', 'procedure code', 'code'])
            desc_col = pick_col(['short description', 'short desc', 'description', 'long description', 'long desc'])

            if code_col:
                code_q = f'"{code_col.replace("\"", "\"\"")}"'
                desc_q = f'"{desc_col.replace("\"", "\"\"")}"' if desc_col else None
                desc_expr = f"COALESCE(NULLIF(TRIM({desc_q}), ''), 'Code ' || TRIM({code_q}))" if desc_q else f"'Code ' || TRIM({code_q})"

                con.execute(f"""
                    INSERT INTO hcpcs_codes
                    SELECT DISTINCT
                        TRIM({code_q}) AS hcpcs_code,
                        {desc_expr} AS short_desc,
                        CASE
                            WHEN {code_q} LIKE 'T%' THEN 'Home Health'
                            WHEN {code_q} LIKE 'H%' THEN 'Behavioral Health'
                            WHEN {code_q} LIKE 'J%' THEN 'Pharmacy'
                            WHEN {code_q} LIKE 'S%' THEN 'Temp/Waiver'
                            WHEN {code_q} LIKE 'A04%' THEN 'Transportation'
                            WHEN {code_q} LIKE 'A%' OR {code_q} LIKE 'E%' OR {code_q} LIKE 'K%' OR {code_q} LIKE 'L%' THEN 'DME'
                            WHEN {code_q} LIKE '97%' THEN 'Therapy'
                            WHEN {code_q} LIKE '992%' OR {code_q} LIKE '990%' THEN 'E&M'
                            WHEN {code_q} LIKE '8%' THEN 'Lab'
                            ELSE 'Other'
                        END AS category
                    FROM {rel}
                    WHERE {code_q} IS NOT NULL AND TRIM({code_q}) != ''
                """)
                loaded_external = True
            else:
                if external_path.lower().endswith('.txt'):
                    print("  Parsing fixed-width HCPCS text file ...")
                    try:
                        rows = []
                        with open(external_path, 'r', errors='ignore') as f:
                            for line in f:
                                s = line.lstrip().rstrip('\n')
                                if len(s) < 10:
                                    continue
                                code = s[:5].strip()
                                if not code:
                                    continue
                                remainder = s[5:]
                                start = None
                                for i, ch in enumerate(remainder):
                                    if ch.isalpha():
                                        start = i
                                        break
                                if start is None:
                                    continue
                                short_desc = remainder[start:start + 60].strip()
                                if not short_desc:
                                    short_desc = f"Code {code}"
                                rows.append((code, short_desc, categorize_hcpcs(code)))
                        if rows:
                            con.executemany("INSERT OR IGNORE INTO hcpcs_codes VALUES (?, ?, ?)", rows)
                            loaded_external = True
                    except Exception as e:
                        print(f"  Fixed-width parse failed: {e}")
                if not loaded_external:
                    print("  Could not detect HCPCS code column in external file; falling back to built-in list.")
        except Exception as e:
            print(f"  Failed to load external HCPCS file: {e}")

    if not loaded_external:
        for code, desc in HCPCS_DESCRIPTIONS.items():
            cat = categorize_hcpcs(code)
            con.execute("INSERT INTO hcpcs_codes VALUES (?, ?, ?)", [code, desc, cat])

    # Also add entries for any top codes in the data not in our dictionary
    con.execute("""
        INSERT OR IGNORE INTO hcpcs_codes
        SELECT
            hs.hcpcs_code,
            'Code ' || hs.hcpcs_code AS short_desc,
            CASE
                WHEN hs.hcpcs_code LIKE 'T%' THEN 'Home Health'
                WHEN hs.hcpcs_code LIKE 'H%' THEN 'Behavioral Health'
                WHEN hs.hcpcs_code LIKE 'J%' THEN 'Pharmacy'
                WHEN hs.hcpcs_code LIKE 'S%' THEN 'Temp/Waiver'
                WHEN hs.hcpcs_code LIKE 'A04%' THEN 'Transportation'
                WHEN hs.hcpcs_code LIKE 'A%' OR hs.hcpcs_code LIKE 'E%' OR hs.hcpcs_code LIKE 'K%' THEN 'DME'
                WHEN hs.hcpcs_code LIKE '97%' THEN 'Therapy'
                WHEN hs.hcpcs_code LIKE '992%' OR hs.hcpcs_code LIKE '990%' THEN 'E&M'
                WHEN hs.hcpcs_code LIKE '8%' THEN 'Lab'
                ELSE 'Other'
            END AS category
        FROM hcpcs_summary hs
        WHERE hs.hcpcs_code NOT IN (SELECT hcpcs_code FROM hcpcs_codes)
        ORDER BY hs.total_paid DESC
        LIMIT 500
    """)

    hcpcs_count = con.execute("SELECT COUNT(*) FROM hcpcs_codes").fetchone()[0]
    print(f"  Loaded {hcpcs_count} HCPCS code descriptions")


def main():
    t0 = time.time()
    con = get_connection(read_only=False)

    download_nppes(con)
    create_hcpcs_table(con)

    # Verification
    prov_count = con.execute("SELECT COUNT(*) FROM providers").fetchone()[0]
    print(f"\nProviders table: {prov_count:,} rows")

    try:
        sample = con.execute("""
            SELECT p.name, p.state, p.specialty
            FROM providers p WHERE p.npi = '1417262056'
        """).fetchone()
        if sample:
            print(f"  Public Partnerships LLC check: {sample}")
    except Exception:
        pass

    try:
        desc = con.execute("SELECT short_desc FROM hcpcs_codes WHERE hcpcs_code = 'T1019'").fetchone()
        if desc:
            print(f"  T1019 description: {desc[0]}")
    except Exception:
        pass

    con.close()
    print(f"\nMilestone 2 complete. Time: {time.time() - t0:.1f}s")


if __name__ == '__main__':
    main()
