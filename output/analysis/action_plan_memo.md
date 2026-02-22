# CEO Action Plan — Medicaid Fraud, Waste, and Abuse

## Executive Summary

- Provider‑level exposure totals about $355,781,963,848.
- A separate $116,147,010,551 reflects state/code rate issues; treat as policy work, not enforcement.
- The top 10 providers account for $17,697,096,555 (5.0% of provider exposure).
- The top 100 providers account for $51,131,158,301 (14.4% of provider exposure).
- Most high‑risk providers show multiple independent red flags (top 500: 484).
- 11 of the top 20 are public entities; focus on policy and rate fixes there.

## Immediate Actions (Next 30 Days)

1) Investigate the top 50 provider‑level findings in the priority queue.
   Start with cases that show multiple red flags or impossible billing patterns.
2) Separate enforcement from policy work: do not treat state/code entries as providers.
3) Require documentation for the top 20 highest‑impact providers with multiple red flags.
4) Verify December 2024 submissions before acting on late‑year drops.

## Policy and Program Integrity Actions

- Use the systemic queue to review rate design and authorization rules.
- Prioritize personal care and community support services for stronger controls.
- Require extra oversight for billing‑only or middleman structures.

## Where the Risk Concentrates

- Public agencies with outlier billing: 20115 providers
- Network or middleman billing: 2690 providers
- Sudden starts or stops: 2433 providers
- Implausible volume or upcoding: 36 providers
- Billing every day: 20 providers
- Billing after deactivation: 20 providers

## Deliverables

- Priority queue (validated + sorted): `/Users/rohitkelapure/projects/medicaid-claims-data/output/analysis/priority_queue_with_notes.csv`
- Top 50 priority list: `/Users/rohitkelapure/projects/medicaid-claims-data/output/analysis/top50_priority_list.md`
- Top 100 priority list: `/Users/rohitkelapure/projects/medicaid-claims-data/output/analysis/top100_priority_list.md`
- Top 200 priority list: `/Users/rohitkelapure/projects/medicaid-claims-data/output/analysis/top200_priority_list.md`
- Provider/systemic risk queues in `output/analysis/` (top100/top500 each).
- Fraud pattern summary: `output/analysis/fraud_patterns.md`

## Validation Status

Positive-control validation requires SAM/LEIE/licensure NPIs in `reference_data/positive_controls/`.
Once loaded, run `python3 scripts/23_generate_provider_validation_scores.py` to generate validation scores.