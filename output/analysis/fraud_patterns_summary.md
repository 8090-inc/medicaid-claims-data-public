# Medicaid Spending: Suspicious Patterns in Provider Billing

**Data:** HHS Provider Spending, January 2018 through December 2024

---

## What This Analysis Covers

We looked at **$1.09 trillion** in Medicaid payments across **227 million** billing records over **7 years**. The data covers **617,503** providers and **10,881** procedure codes.

We found **$355 billion** in suspicious spending at the provider level, and another **$116 billion** in system-wide rate problems. These are upper-bound estimates — the most that could be at risk — not confirmed losses. A single provider can show up in more than one pattern, so the pattern totals add up to more than the overall total.

One important note: December 2024 data appears incomplete in many states. Providers that look like they suddenly stopped billing in late 2024 may just have late paperwork.

---

## The Ten Patterns We Found

### 1. Home Health and Personal Care — $55 billion, 19,922 providers

One billing code — T1019, for personal care in 15-minute blocks — accounts for $122.7 billion, or 11.2% of all Medicaid spending. These are services like bathing, dressing, and meal prep delivered in people's homes. They are hard to verify because nobody is watching to confirm the aide actually showed up.

The biggest outliers are large New York agencies: Premier Home Health ($260 million in suspicious spending on $1.5 billion billed), Concepts of Independence ($282 million), and Hamaspik of Kings County ($243 million). Each was flagged by 7 to 9 different detection methods, including signs of kickback payments and billing every day without breaks.

**What it means:** Some of this is real waste — high-volume services with little oversight. Some may be outright fraud — impossible daily hours and inflated rates. Personal care is structurally easy to abuse because verification is minimal.

### 2. Middleman Billing Organizations — $36.5 billion, 1,915 providers

Some companies don't deliver care themselves. They just submit bills on behalf of other providers. This is sometimes fine — insurance companies and fiscal agents do it routinely. It becomes suspicious when the middleman charges rates far above what others charge, or when it controls most of the billing for a particular service.

The biggest outlier is GuardianTrac LLC in Michigan ($1.24 billion in suspicious spending on $2.68 billion billed), which triggered 15 different detection methods. It bills through a large network of other providers. Other examples include Consumer Direct Care Network Virginia ($610 million) and NJ Dept of Health and Senior Services ($890 million).

**What it means:** Middleman billing is not automatically wrong, but middlemen who charge way more than their peers or dominate a service market need a closer look.

### 3. Government Agencies as Outliers — $53.5 billion, 20,205 providers

**This is the single most important finding in the entire analysis.**

Eleven of the top 20 flagged providers are government agencies — county departments, state agencies, or public institutions. These are not criminals stealing money. They are large public organizations whose billing looks very different from private-sector providers.

The biggest: LA County Dept of Mental Health ($4.99 billion in suspicious spending on $6.78 billion billed, flagged by 19 methods — more than any other provider). Tennessee's Dept of Intellectual and Developmental Disabilities totals $3.32 billion across two separate billing IDs. Alabama Dept of Mental Health: $1.93 billion. City of Chicago: $1.06 billion.

Massachusetts stands out: its Department of Developmental Services uses 8 or more separate billing IDs, each for a different regional office. Together they exceed $2.5 billion. Because each ID is compared to single-organization peers, each one looks like an outlier — but it is really one agency split into many pieces.

**What it means:** The problem here is how states set rates and structure billing for public agencies, not fraud by those agencies. The fix is program reform, not prosecution.

### 4. Providers That Cannot Exist — $0.9 billion (individual), $116.1 billion (system-wide)

407 providers billed Medicaid after their billing ID was shut down, or they have no name, specialty, or organization type on file. At the system level, 2,681 entries use fake or non-standard identifiers.

Three unregistered IDs stand out: one billed in 30 states in a single month ($2.1 billion total), another in 29 states ($1.1 billion), a third in 24 states ($826 million). Together: $4 billion. They might be clearinghouses or billing system glitches, but billing under IDs that are not in the national provider registry should not happen.

**What it means:** Billing under deactivated or unregistered IDs is a basic compliance failure. It may not all be fraud, but it should not exist.

### 5. Billing Every Single Day — $9.6 billion, 20 providers

Twenty providers billed Medicaid every calendar day — or nearly every day — across multiple years. The list includes LA County DMH, Tempus Unlimited, GuardianTrac, Freedom Care, and Premier Home Health, all of which also appear in other patterns.

**What it means:** A large organization with hundreds of employees could legitimately bill every day. This flag matters most when combined with other red flags like impossible volumes or inflated rates. On its own, it is a weak signal.

### 6. Sudden Starts and Stops — $91.8 billion, 2,433 providers

This is the biggest pattern by dollar amount. It catches providers that appeared out of nowhere with high billing, disappeared abruptly, or had sudden spikes or drops in their monthly totals. Examples: AOC TX LLC in Texas ($495 million), Arion Care Solutions in Arizona ($404 million), Coordinated Behavioral Care in New York ($284 million).

**Data warning:** December 2024 spending dropped 67% from November ($4.2 billion vs $12.9 billion). This almost certainly reflects late data, not real drops. Many late-2024 flags are probably false alarms. Also, the COVID comparison method can flag providers that legitimately changed their billing during the pandemic.

**What it means:** Some of these are genuinely suspicious new entrants that ramped up fast and may be worth investigating. Others are normal responses to COVID or policy changes. Each one needs its timeline checked before drawing conclusions.

### 7. Billing Networks and Circular Billing — $16.1 billion, 852 providers

This pattern flags suspicious billing relationships: Provider A bills through Provider B, and Provider B bills through Provider A (circular billing). Or a provider sends more than 90% of its billing through a single partner. Or new, high-dollar relationships appear suddenly.

The most extreme case: Mains'l Florida Inc (registered in Minnesota, $900 million in suspicious spending). The rate it charges through its servicing partner is **$3,256 per claim** versus a peer median of **$40** — an 81 times markup.

**What it means:** These network patterns can indicate kickback schemes, shell companies, or billing setups designed to inflate payments. The 81x markup at Mains'l Florida is among the most extreme outliers in the entire dataset and should be investigated first.

### 8. State-Level Spending Differences — $77.5 billion (system-wide only)

Twenty combinations of state and procedure code where spending per patient is more than double the national average. The biggest: New York's personal care code T1019, where spending is $3,159 per patient versus the national median of $1,526 (2.1 times higher, $74.6 billion total). New Jersey's comprehensive community support code: $6.9 billion. New York's personal care per-day code: $3.5 billion.

**What it means:** These are state-level decisions about how much to pay for specific services. They need to be addressed between CMS and the states, not through provider-level enforcement.

### 9. Upcoding and Impossible Volumes — $3.4 billion, 36 providers

Upcoding means billing for a more expensive version of a service than what was actually delivered. Impossible volumes mean claiming more hours of service in a day than there are hours in a day, or more patient visits than one doctor could physically perform (more than 20 per day).

Examples: County of Orange, CA ($608 million), Scottish Rite Children's Medical Center, GA ($360 million), North Shore-LIJ Medical PC, NY ($274 million), and Cleveland Clinic Foundation, OH ($227 million, flagged by 16 methods).

**What it means:** Upcoding is one of the most common and well-documented forms of Medicaid fraud. But when major hospital systems show up on the list, the right next step is reviewing patient charts, not filing fraud charges.

### 10. Shared Beneficiary Counts — $2.4 billion, 19 providers

Provider pairs that serve the exact same number of patients. When two supposedly independent providers have identical patient counts, it can mean they share ownership, coordinate their billing, or are really the same organization under two names.

Top example: Community Assistance Resources & Extended Services Inc in New York ($738 million, 240,183 patients, flagged by 12 methods). Massachusetts state agencies also appear here.

**What it means:** Identical patient counts can be innocent (two billing IDs for the same agency) or suspicious (coordinated billing). Ownership records and network analysis are needed to tell the difference.

---

## Six Things That Matter Most

1. **Government agencies dominate the risk list.** Eleven of the top 20 flagged providers are public agencies. This is not a fraud wave — it is a systemic problem with how states set rates and structure billing for their own agencies.

2. **Splitting one agency across many billing IDs creates false outliers.** Massachusetts DDS uses 8+ billing IDs. Each piece looks abnormal when compared to single-entity peers, but together they are one agency.

3. **Multiple independent signals are the best indicator.** 90% of the top 500 providers triggered 3 or more different detection methods. A single flag is a screening lead. Three or more flags together are worth investigating.

4. **Known bad actors barely overlap with our findings.** The federal government maintains a list of 8,302 excluded providers. Fewer than 0.1% of our flagged providers appear on that list. Either the data has already been cleaned, or statistical methods catch a different kind of problem than exclusion lists do.

5. **Four detection methods were too unreliable to use.** One of them (ghost_provider_indicators) would have flagged 90% of all providers, which is useless. It was correctly removed.

6. **COVID makes everything harder to read.** Many of the time-based signals (sudden growth, billing spikes) pick up legitimate changes caused by the pandemic. Any finding from 2020-2021 needs to be read in the context of the public health emergency.

---

## How We Classified Providers

Each provider was sorted into patterns using fixed rules. A provider can land in more than one pattern.

| Pattern | How We Identified It |
|---|---|
| Home Health/Personal Care | Top billing code is a personal care or home health code, or specialty includes "Home Health," "In Home," or "Personal" |
| Middleman Billing | Flagged for hub-spoke networks, shared servicing, pure billing entities, or billing fan-out |
| Government Outliers | Name includes Department, County, State, City, Public, or University |
| Cannot Exist | Billing ID is non-standard, missing a name, or was used after deactivation |
| Every Day Billing | Flagged for no days off |
| Sudden Starts/Stops | Flagged for sudden appearance, disappearance, statistical change-points, or 2x+ year-over-year growth |
| Networks/Circular Billing | Flagged for circular billing, dense networks, ghost networks, or reciprocal billing |
| State Spending Differences | System-wide rate anomalies, state peer comparisons, or geographic monopolies |
| Upcoding/Impossible Volumes | Flagged for upcoding, impossible volumes, impossible units per day, or unbundling |
| Shared Beneficiary Counts | Flagged for identical patient counts, shared flagged patients, or patient overlap rings |

## How We Checked Our Work

- We held back data from January 2023 through December 2024 and tested whether flagged providers stayed flagged in the holdout period. Baseline holdout rate: 65.44%.
- The most reliable methods: addiction_high_per_bene, pharmacy_single_drug, pharmacy_rate_outlier, and ensemble_agreement.
- We cross-checked against the OIG's List of Excluded Individuals/Entities (8,302 entries).

---

*Everything described here is a statistical risk indicator, not proof of fraud. Every finding requires further investigation before any enforcement action.*
