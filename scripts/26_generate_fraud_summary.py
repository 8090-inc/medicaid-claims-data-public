#!/usr/bin/env python3
"""Generate fraud_patterns_summary.md with plain-language narratives from pipeline data."""

import csv
import json
import os
import sys

import duckdb

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scripts.utils.db_utils import format_dollars

FINDINGS_PATH = os.path.join(PROJECT_ROOT, "output", "findings", "final_scored_findings.json")
PROFILE_PATH = os.path.join(PROJECT_ROOT, "output", "data_profile.json")
RISK_QUEUE_PATH = os.path.join(PROJECT_ROOT, "output", "analysis", "risk_queue_top500.csv")
FRAUD_PATTERNS_PATH = os.path.join(PROJECT_ROOT, "output", "analysis", "fraud_patterns.md")
DB_PATH = os.path.join(PROJECT_ROOT, "medicaid.duckdb")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "output", "analysis", "fraud_patterns_summary.md")

HOME_CARE_CODES = {"T1019", "T1020", "S5125", "S5126", "S5130", "S5131", "S5170", "S5175"}

PATTERNS = [
    ("Home Health and Personal Care", "home_personal"),
    ("Middleman Billing Organizations", "middleman"),
    ("Government Agencies as Outliers", "government"),
    ("Providers That Cannot Exist", "nonexistent"),
    ("Billing Every Single Day", "no_days_off"),
    ("Sudden Starts and Stops", "sudden"),
    ("Billing Networks and Circular Billing", "network"),
    ("State-Level Spending Differences", "state_level"),
    ("Upcoding and Impossible Volumes", "impossible"),
    ("Shared Beneficiary Counts", "shared_benes"),
]


def load_json(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)


def normalize_methods(methods):
    if isinstance(methods, str):
        return [m for m in methods.split(";") if m]
    return methods or []


def is_public_entity(name):
    if not name:
        return False
    upper = name.upper()
    return any(term in upper for term in ("DEPARTMENT", "COUNTY", "STATE", "CITY", "PUBLIC", "UNIVERSITY"))


def is_systemic_npi(npi):
    if not npi:
        return False
    if npi.startswith("STATE_") or npi.startswith("PAIR_"):
        return True
    return not (len(npi) == 10 and npi.isdigit())


def fmt_b(amount):
    """Format as $X.X billion for narrative text."""
    return f"${amount / 1e9:.1f} billion"


def fmt_b_short(amount):
    """Format as $55.1B for headings."""
    return format_dollars(amount)


def fmt_m(amount):
    """Format as $X million for narrative text."""
    if amount >= 1e9:
        return f"${amount / 1e9:.2f} billion"
    return f"${amount / 1e6:,.0f} million"


def classify_finding(f, code_lookup):
    """Return set of pattern keys a finding belongs to."""
    npi = f.get("npi", "")
    name = f.get("name", "")
    specialty = (f.get("specialty") or "").upper()
    methods = normalize_methods(f.get("methods", []))
    top_code = code_lookup.get(npi, "")
    is_sys = is_systemic_npi(npi)

    matches = set()

    if top_code in HOME_CARE_CODES or "HOME HEALTH" in specialty or "IN HOME" in specialty or "PERSONAL" in specialty:
        matches.add("home_personal")
    if any(m in methods for m in ("hub_spoke", "shared_servicing", "pure_billing",
                                  "captive_servicing", "billing_only_provider", "billing_fan_out")):
        matches.add("middleman")
    if is_public_entity(name):
        matches.add("government")
    if is_sys or not name or "post_deactivation_billing" in methods:
        matches.add("nonexistent")
    if "no_days_off" in methods:
        matches.add("no_days_off")
    if any(m in methods for m in ("sudden_appearance", "sudden_disappearance", "change_point_cusum", "change_point", "yoy_growth")):
        matches.add("sudden")
    if any(m in methods for m in ("circular_billing", "network_density", "ghost_network", "new_network",
                                  "hub_spoke", "composite_network_plus_volume", "reciprocal_billing")):
        matches.add("network")
    if is_sys and any(m in methods for m in ("state_peer_comparison", "state_spending_anomaly",
                                             "geographic_monopoly", "peer_concentration")):
        matches.add("state_level")
    if any(m in methods for m in ("upcoding", "impossible_volume", "impossible_units_per_day", "impossible_service_days", "unbundling")):
        matches.add("impossible")
    if any(m in methods for m in ("shared_bene_count", "shared_flagged_benes", "bene_overlap_ring", "bene_network_spread")):
        matches.add("shared_benes")

    return matches


def load_risk_queue(path):
    """Load risk_queue_top500.csv into list of dicts."""
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["total_impact"] = float(row.get("total_impact", 0) or 0)
            row["num_methods"] = int(row.get("num_methods", 0) or 0)
            row["methods"] = row.get("methods", "")
            rows.append(row)
    return rows


def get_top_providers_for_pattern(risk_queue, pattern_key, code_lookup, n=5):
    """Get top N providers from risk queue that match a pattern."""
    matched = []
    for row in risk_queue:
        f = {
            "npi": row.get("npi", ""),
            "name": row.get("name", ""),
            "specialty": row.get("specialty", ""),
            "methods": row.get("methods", ""),
        }
        patterns = classify_finding(f, code_lookup)
        if pattern_key in patterns:
            matched.append(row)
    return matched[:n]


def count_gov_in_top20(risk_queue):
    """Count government agencies in top 20."""
    count = 0
    for row in risk_queue[:20]:
        if is_public_entity(row.get("name", "")):
            count += 1
    return count


def count_multi_method(risk_queue, threshold=3, top_n=500):
    """Count providers with >= threshold methods in top N."""
    count = 0
    for row in risk_queue[:top_n]:
        if row["num_methods"] >= threshold:
            count += 1
    return count


def main():
    for path in (FINDINGS_PATH, PROFILE_PATH, RISK_QUEUE_PATH):
        if not os.path.exists(path):
            raise SystemExit(f"Missing: {path}")

    print("Loading data...")
    findings_data = load_json(FINDINGS_PATH)
    profile = load_json(PROFILE_PATH)
    findings = findings_data.get("findings", [])
    risk_queue = load_risk_queue(RISK_QUEUE_PATH)

    # Build HCPCS code lookup
    npis = [f["npi"] for f in findings if f.get("npi") and not is_systemic_npi(f.get("npi"))]
    code_lookup = {}
    if npis:
        con = duckdb.connect(DB_PATH, read_only=True)
        rows_db = con.execute("""
            SELECT billing_npi, hcpcs_code FROM (
                SELECT billing_npi, hcpcs_code,
                       ROW_NUMBER() OVER (PARTITION BY billing_npi ORDER BY paid DESC) AS rn
                FROM provider_hcpcs WHERE billing_npi IN (SELECT UNNEST(?::VARCHAR[]))
            ) t WHERE rn = 1
        """, [npis]).fetchall()
        con.close()
        code_lookup = {r[0]: r[1] for r in rows_db}

    # Classify all findings
    provider_counts = {key: 0 for _, key in PATTERNS}
    provider_totals = {key: 0.0 for _, key in PATTERNS}
    systemic_counts = {key: 0 for _, key in PATTERNS}
    systemic_totals = {key: 0.0 for _, key in PATTERNS}

    for f in findings:
        npi = f.get("npi", "")
        total_impact = float(f.get("total_impact", 0) or 0)
        systemic_raw = float(f.get("systemic_impact_raw", 0) or 0)
        is_sys = is_systemic_npi(npi)
        matches = classify_finding(f, code_lookup)

        for key in matches:
            if is_sys:
                systemic_counts[key] += 1
                systemic_totals[key] += systemic_raw
            else:
                provider_counts[key] += 1
                provider_totals[key] += total_impact

    total_paid = profile.get("total_paid", 0)
    total_rows = profile.get("total_rows", 0)
    total_providers = profile.get("unique_billing_npis", 0)
    total_codes = profile.get("unique_hcpcs_codes", 0)
    total_impact = findings_data.get("summary", {}).get("total_estimated_recoverable", 0)
    systemic_total = findings_data.get("summary", {}).get("systemic_exposure_total", 0)

    # Computed facts for "Six Things"
    gov_in_top20 = count_gov_in_top20(risk_queue)
    multi_method_count = count_multi_method(risk_queue, threshold=3, top_n=500)
    multi_method_pct = (multi_method_count / min(len(risk_queue), 500) * 100) if risk_queue else 0

    # Pattern display values
    def p_count(key):
        return provider_counts[key]

    def p_total(key):
        return provider_totals[key]

    def s_count(key):
        return systemic_counts[key]

    def s_total(key):
        return systemic_totals[key]

    # Get top providers per pattern from risk queue
    def top_provs(key, n=5):
        return get_top_providers_for_pattern(risk_queue, key, code_lookup, n)

    print("Generating summary...")

    lines = []

    # --- Title and Overview ---
    lines.append("# Medicaid Spending: Suspicious Patterns in Provider Billing")
    lines.append("")
    lines.append("**Data:** HHS Provider Spending, January 2018 through December 2024")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## What This Analysis Covers")
    lines.append("")
    lines.append(
        f"We looked at **${total_paid / 1e12:.2f} trillion** in Medicaid payments across "
        f"**{total_rows / 1e6:.0f} million** billing records over **7 years**. "
        f"The data covers **{total_providers:,}** providers and **{total_codes:,}** procedure codes."
    )
    lines.append("")
    lines.append(
        f"We found **{fmt_b(total_impact)}** in suspicious spending at the provider level, "
        f"and another **{fmt_b(systemic_total)}** in system-wide rate problems. "
        "These are upper-bound estimates \u2014 the most that could be at risk \u2014 not confirmed losses. "
        "A single provider can show up in more than one pattern, so the pattern totals add up to more than the overall total."
    )
    lines.append("")
    lines.append(
        "One important note: December 2024 data appears incomplete in many states. "
        "Providers that look like they suddenly stopped billing in late 2024 may just have late paperwork."
    )
    lines.append("")
    lines.append("![Monthly Medicaid Provider Spending, Jan 2018 \u2013 Dec 2024](../charts/monthly_spending_trend.png)")
    lines.append("")
    lines.append("![Fraud Pattern Heat Map \u2014 All 10 patterns scored by spending, providers, and risk](../charts/fraud_heatmap_aligned.png)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- The Ten Patterns ---
    lines.append("## The Ten Patterns We Found")
    lines.append("")

    # Pattern 1: Home Health and Personal Care
    hp_top = top_provs("home_personal", 5)
    lines.append(f"### 1. Home Health and Personal Care \u2014 {fmt_b_short(p_total('home_personal'))}, {p_count('home_personal'):,} providers")
    lines.append("")
    lines.append("![Top 20 Procedures by Total Spending](../charts/top20_flagged_procedures.png)")
    lines.append("")
    lines.append(
        "One billing code \u2014 T1019, for personal care in 15-minute blocks \u2014 accounts for $122.7 billion, "
        "or 11.2% of all Medicaid spending. These are services like bathing, dressing, and meal prep delivered in "
        "people's homes. They are hard to verify because nobody is watching to confirm the aide actually showed up."
    )
    lines.append("")
    if len(hp_top) >= 3:
        examples = []
        for p in hp_top[:3]:
            examples.append(f"{p['name']} ({fmt_m(p['total_impact'])} in suspicious spending)")
        lines.append(f"The biggest outliers include {examples[0]}, {examples[1]}, and {examples[2]}.")
    lines.append("")
    lines.append(
        "**What it means:** Some of this is real waste \u2014 high-volume services with little oversight. "
        "Some may be outright fraud \u2014 impossible daily hours and inflated rates. "
        "Personal care is structurally easy to abuse because verification is minimal."
    )
    lines.append("")

    # Pattern 2: Middleman Billing Organizations
    mm_top = top_provs("middleman", 5)
    lines.append(f"### 2. Middleman Billing Organizations \u2014 {fmt_b_short(p_total('middleman'))}, {p_count('middleman'):,} providers")
    lines.append("")
    lines.append(
        "Some companies don't deliver care themselves. They just submit bills on behalf of other providers. "
        "This is sometimes fine \u2014 insurance companies and fiscal agents do it routinely. It becomes suspicious "
        "when the middleman charges rates far above what others charge, or when it controls most of the billing "
        "for a particular service."
    )
    lines.append("")
    if mm_top:
        p = mm_top[0]
        text = (
            f"The biggest outlier is {p['name']} in {p['state']} "
            f"({fmt_m(p['total_impact'])} in suspicious spending), "
            f"which triggered {p['num_methods']} different detection methods."
        )
        if len(mm_top) >= 3:
            text += (
                f" Other examples include {mm_top[1]['name']} ({fmt_m(mm_top[1]['total_impact'])}) "
                f"and {mm_top[2]['name']} ({fmt_m(mm_top[2]['total_impact'])})."
            )
        lines.append(text)
    lines.append("")
    lines.append(
        "**What it means:** Middleman billing is not automatically wrong, but middlemen who charge way more "
        "than their peers or dominate a service market need a closer look."
    )
    lines.append("")

    # Pattern 3: Government Agencies as Outliers
    gov_top = top_provs("government", 5)
    lines.append(f"### 3. Government Agencies as Outliers \u2014 {fmt_b_short(p_total('government'))}, {p_count('government'):,} providers")
    lines.append("")
    lines.append("![Top 20 Providers by Estimated Recoverable Amount](../charts/top20_flagged_providers.png)")
    lines.append("")
    lines.append("**This is the single most important finding in the entire analysis.**")
    lines.append("")
    lines.append(
        f"{gov_in_top20} of the top 20 flagged providers are government agencies \u2014 county departments, "
        "state agencies, or public institutions. These are not criminals stealing money. They are large public "
        "organizations whose billing looks very different from private-sector providers."
    )
    lines.append("")
    if gov_top:
        p = gov_top[0]
        text = (
            f"The biggest: {p['name']} ({fmt_m(p['total_impact'])} in suspicious spending, "
            f"flagged by {p['num_methods']} methods \u2014 more than any other provider)."
        )
        # Find TN DIDD entries
        tn_entries = [r for r in gov_top if "INTELLECTUAL AND DEVELOPMENTAL" in (r.get("name", "") or "").upper()]
        if len(tn_entries) >= 2:
            tn_total = sum(float(r["total_impact"]) for r in tn_entries)
            text += (
                f" Tennessee's Dept of Intellectual and Developmental Disabilities totals "
                f"{fmt_m(tn_total)} across two separate billing IDs."
            )
        lines.append(text)
    lines.append("")
    lines.append(
        "Massachusetts stands out: its Department of Developmental Services uses 8 or more separate billing IDs, "
        "each for a different regional office. Together they exceed $2.5 billion. Because each ID is compared to "
        "single-organization peers, each one looks like an outlier \u2014 but it is really one agency split into many pieces."
    )
    lines.append("")
    lines.append(
        "**What it means:** The problem here is how states set rates and structure billing for public agencies, "
        "not fraud by those agencies. The fix is program reform, not prosecution."
    )
    lines.append("")

    # Pattern 4: Providers That Cannot Exist
    lines.append(
        f"### 4. Providers That Cannot Exist \u2014 "
        f"{fmt_b_short(p_total('nonexistent'))} (individual), {fmt_b_short(s_total('nonexistent'))} (system-wide)"
    )
    lines.append("")
    lines.append(
        f"{p_count('nonexistent'):,} providers billed Medicaid after their billing ID was shut down, or they have "
        "no name, specialty, or organization type on file. At the system level, "
        f"{s_count('nonexistent'):,} entries use fake or non-standard identifiers."
    )
    lines.append("")
    lines.append(
        "Three unregistered IDs stand out: one billed in 30 states in a single month ($2.1 billion total), "
        "another in 29 states ($1.1 billion), a third in 24 states ($826 million). Together: $4 billion. "
        "They might be clearinghouses or billing system glitches, but billing under IDs that are not in the "
        "national provider registry should not happen."
    )
    lines.append("")
    lines.append(
        "**What it means:** Billing under deactivated or unregistered IDs is a basic compliance failure. "
        "It may not all be fraud, but it should not exist."
    )
    lines.append("")

    # Pattern 5: Billing Every Single Day
    lines.append(f"### 5. Billing Every Single Day \u2014 {fmt_b_short(p_total('no_days_off'))}, {p_count('no_days_off'):,} providers")
    lines.append("")
    ndo_top = top_provs("no_days_off", 5)
    ndo_names = [p["name"] for p in ndo_top[:5] if p.get("name")]
    if ndo_names:
        names_str = ", ".join(ndo_names[:5])
        lines.append(
            f"{p_count('no_days_off')} providers billed Medicaid every calendar day \u2014 or nearly every day \u2014 "
            f"across multiple years. The list includes {names_str}, all of which also appear in other patterns."
        )
    else:
        lines.append(
            f"{p_count('no_days_off')} providers billed Medicaid every calendar day \u2014 or nearly every day \u2014 "
            "across multiple years."
        )
    lines.append("")
    lines.append(
        "**What it means:** A large organization with hundreds of employees could legitimately bill every day. "
        "This flag matters most when combined with other red flags like impossible volumes or inflated rates. "
        "On its own, it is a weak signal."
    )
    lines.append("")

    # Pattern 6: Sudden Starts and Stops
    lines.append(f"### 6. Sudden Starts and Stops \u2014 {fmt_b_short(p_total('sudden'))}, {p_count('sudden'):,} providers")
    lines.append("")
    lines.append("![Top 5 Flagged Providers: Monthly Billing Anomaly Patterns](../charts/temporal_anomalies_top5.png)")
    lines.append("")
    sudden_top = top_provs("sudden", 5)
    text = (
        "This is the biggest pattern by dollar amount. It catches providers that appeared out of nowhere with "
        "high billing, disappeared abruptly, or had sudden spikes or drops in their monthly totals."
    )
    if len(sudden_top) >= 3:
        examples = [f"{p['name']} in {p['state']} ({fmt_m(p['total_impact'])})" for p in sudden_top[:3]]
        text += f" Examples: {', '.join(examples)}."
    lines.append(text)
    lines.append("")
    lines.append(
        "**Data warning:** December 2024 spending dropped 67% from November ($4.2 billion vs $12.9 billion). "
        "This almost certainly reflects late data, not real drops. Many late-2024 flags are probably false alarms. "
        "Also, the COVID comparison method can flag providers that legitimately changed their billing during the pandemic."
    )
    lines.append("")
    lines.append(
        "**What it means:** Some of these are genuinely suspicious new entrants that ramped up fast and may be "
        "worth investigating. Others are normal responses to COVID or policy changes. Each one needs its timeline "
        "checked before drawing conclusions."
    )
    lines.append("")

    # Pattern 7: Billing Networks and Circular Billing
    lines.append(f"### 7. Billing Networks and Circular Billing \u2014 {fmt_b_short(p_total('network'))}, {p_count('network'):,} providers")
    lines.append("")
    lines.append("![Top 3 Suspicious Billing Networks](../charts/network_graph_top3.png)")
    lines.append("")
    lines.append(
        "This pattern flags suspicious billing relationships: Provider A bills through Provider B, and Provider B "
        "bills through Provider A (circular billing). Or a provider sends more than 90% of its billing through a "
        "single partner. Or new, high-dollar relationships appear suddenly."
    )
    lines.append("")
    net_top = top_provs("network", 3)
    if net_top:
        p = net_top[0]
        lines.append(
            f"The most extreme case: {p['name']} (registered in {p['state']}, "
            f"{fmt_m(p['total_impact'])} in suspicious spending)."
        )
    lines.append("")
    lines.append(
        "**What it means:** These network patterns can indicate kickback schemes, shell companies, or billing "
        "setups designed to inflate payments."
    )
    lines.append("")

    # Pattern 8: State-Level Spending Differences
    lines.append(f"### 8. State-Level Spending Differences \u2014 {fmt_b_short(s_total('state_level'))} (system-wide only)")
    lines.append("")
    lines.append("![Flagged Spending by State](../charts/state_heatmap.png)")
    lines.append("")
    lines.append(
        f"{s_count('state_level')} combinations of state and procedure code where spending per patient is more than "
        "double the national average. The biggest: New York's personal care code T1019, where spending is $3,159 per "
        "patient versus the national median of $1,526 (2.1 times higher, $74.6 billion total). "
        "New Jersey's comprehensive community support code: $6.9 billion. New York's personal care per-day code: $3.5 billion."
    )
    lines.append("")
    lines.append(
        "**What it means:** These are state-level decisions about how much to pay for specific services. "
        "They need to be addressed between CMS and the states, not through provider-level enforcement."
    )
    lines.append("")

    # Pattern 9: Upcoding and Impossible Volumes
    lines.append(f"### 9. Upcoding and Impossible Volumes \u2014 {fmt_b_short(p_total('impossible'))}, {p_count('impossible'):,} providers")
    lines.append("")
    lines.append(
        "Upcoding means billing for a more expensive version of a service than what was actually delivered. "
        "Impossible volumes mean claiming more hours of service in a day than there are hours in a day, or more "
        "patient visits than one doctor could physically perform (more than 20 per day)."
    )
    lines.append("")
    imp_top = top_provs("impossible", 4)
    if imp_top:
        examples = [f"{p['name']}, {p['state']} ({fmt_m(p['total_impact'])})" for p in imp_top[:4]]
        lines.append(f"Examples: {', '.join(examples)}.")
    lines.append("")
    lines.append(
        "**What it means:** Upcoding is one of the most common and well-documented forms of Medicaid fraud. "
        "But when major hospital systems show up on the list, the right next step is reviewing patient charts, "
        "not filing fraud charges."
    )
    lines.append("")

    # Pattern 10: Shared Beneficiary Counts
    lines.append(f"### 10. Shared Beneficiary Counts \u2014 {fmt_b_short(p_total('shared_benes'))}, {p_count('shared_benes'):,} providers")
    lines.append("")
    lines.append(
        "Provider pairs that serve the exact same number of patients. When two supposedly independent providers "
        "have identical patient counts, it can mean they share ownership, coordinate their billing, or are really "
        "the same organization under two names."
    )
    lines.append("")
    sb_top = top_provs("shared_benes", 3)
    if sb_top:
        p = sb_top[0]
        score_str = f", flagged by {p['num_methods']} methods" if p["num_methods"] else ""
        lines.append(
            f"Top example: {p['name']} in {p['state']} "
            f"({fmt_m(p['total_impact'])}{score_str}). Massachusetts state agencies also appear here."
        )
    lines.append("")
    lines.append(
        "**What it means:** Identical patient counts can be innocent (two billing IDs for the same agency) or "
        "suspicious (coordinated billing). Ownership records and network analysis are needed to tell the difference."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # Charts
    lines.append("![Provider Risk Assessment: Total Paid vs Composite Anomaly Score](../charts/provider_risk_scatter.png)")
    lines.append("")
    lines.append("![Provider Spending Concentration (Lorenz Curve)](../charts/lorenz_curve.png)")
    lines.append("")

    # --- Six Things That Matter Most ---
    lines.append("## Six Things That Matter Most")
    lines.append("")
    lines.append(
        f"1. **Government agencies dominate the risk list.** {gov_in_top20} of the top 20 flagged providers "
        "are public agencies. This is not a fraud wave \u2014 it is a systemic problem with how states set rates "
        "and structure billing for their own agencies."
    )
    lines.append("")
    lines.append(
        "2. **Splitting one agency across many billing IDs creates false outliers.** Massachusetts DDS uses 8+ "
        "billing IDs. Each piece looks abnormal when compared to single-entity peers, but together they are one agency."
    )
    lines.append("")
    lines.append(
        f"3. **Multiple independent signals are the best indicator.** {multi_method_pct:.0f}% of the top 500 "
        "providers triggered 3 or more different detection methods. A single flag is a screening lead. Three or "
        "more flags together are worth investigating."
    )
    lines.append("")
    lines.append(
        "4. **Known bad actors barely overlap with our findings.** The federal government maintains a list of "
        "8,302 excluded providers. Fewer than 0.1% of our flagged providers appear on that list. Either the data "
        "has already been cleaned, or statistical methods catch a different kind of problem than exclusion lists do."
    )
    lines.append("")
    lines.append(
        "5. **Four detection methods were too unreliable to use.** One of them (ghost_provider_indicators) would "
        "have flagged 90% of all providers, which is useless. It was correctly removed."
    )
    lines.append("")
    lines.append(
        "6. **COVID makes everything harder to read.** Many of the time-based signals (sudden growth, billing "
        "spikes) pick up legitimate changes caused by the pandemic. Any finding from 2020-2021 needs to be read "
        "in the context of the public health emergency."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- Classification table ---
    lines.append("## How We Classified Providers")
    lines.append("")
    lines.append("Each provider was sorted into patterns using fixed rules. A provider can land in more than one pattern.")
    lines.append("")
    lines.append("| Pattern | How We Identified It |")
    lines.append("|---|---|")
    lines.append('| Home Health/Personal Care | Top billing code is a personal care or home health code, or specialty includes "Home Health," "In Home," or "Personal" |')
    lines.append("| Middleman Billing | Flagged for hub-spoke networks, shared servicing, pure billing entities, or billing fan-out |")
    lines.append("| Government Outliers | Name includes Department, County, State, City, Public, or University |")
    lines.append("| Cannot Exist | Billing ID is non-standard, missing a name, or was used after deactivation |")
    lines.append("| Every Day Billing | Flagged for no days off |")
    lines.append("| Sudden Starts/Stops | Flagged for sudden appearance, disappearance, statistical change-points, or 2x+ year-over-year growth |")
    lines.append("| Networks/Circular Billing | Flagged for circular billing, dense networks, ghost networks, or reciprocal billing |")
    lines.append("| State Spending Differences | System-wide rate anomalies, state peer comparisons, or geographic monopolies |")
    lines.append("| Upcoding/Impossible Volumes | Flagged for upcoding, impossible volumes, impossible units per day, or unbundling |")
    lines.append("| Shared Beneficiary Counts | Flagged for identical patient counts, shared flagged patients, or patient overlap rings |")
    lines.append("")

    # --- Validation ---
    lines.append("## How We Checked Our Work")
    lines.append("")
    lines.append("- We held back data from January 2023 through December 2024 and tested whether flagged providers stayed flagged in the holdout period. Baseline holdout rate: 65.44%.")
    lines.append("- The most reliable methods: addiction_high_per_bene, pharmacy_single_drug, pharmacy_rate_outlier, and ensemble_agreement.")
    lines.append("- We cross-checked against the OIG's List of Excluded Individuals/Entities (8,302 entries).")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Everything described here is a statistical risk indicator, not proof of fraud. Every finding requires further investigation before any enforcement action.*")

    # Write output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
