---
title: "Executive Dashboard Cards"
type: "feature"
id: "5343ad67-91bd-4d79-9e57-59320c46cf8c"
---

## Overview

This feature generates 3 executive dashboard card images (monthly spending, top procedures, top providers) as PNG files matching HHS OpenData design specifications. Cards are sized for web display (833x547, 833x969 pixels) with precise padding, typography, and branding for use in executive briefings and web dashboards.

Runs as Milestone 17 and produces shareable visual assets.

## Terminology

* **Dashboard Card**: Self-contained visual data card with title, subtitle, chart, and footer branding following HHS design spec.
* **Card Dimensions**: Pixel-perfect sizing (833x547 for Card 1, 833x969 for Cards 2-3) at 150 DPI.
* **HHS Styling**: Monochromatic amber (#E8A317), specific fonts (DejaVu Sans), minimal borders, government branding.

## Requirements

### REQ-DASH-001: Card 1 - Monthly Spending Trend

**User Story:** As an executive, I want a monthly spending card, so that I can see temporal trends at a glance.

**Acceptance Criteria:**

* **AC-DASH-001.1:** The system shall generate `card1-full-monthly-spending.png` at 833x547 pixels showing monthly Medicaid spending from Jan 2018 - Dec 2024.
* **AC-DASH-001.2:** The card shall include title "Monthly Medicaid Provider Spending", subtitle "January 2018 - December 2024 | Total Fee-for-Service and Managed Care".
* **AC-DASH-001.3:** The chart shall use a line plot with amber color, y-axis in billions ($XXB format), and minimal gridlines.
* **AC-DASH-001.4:** The card shall include HHS footer branding and border.

### REQ-DASH-002: Card 2 - Top 20 Procedures

**User Story:** As a utilization analyst, I want a top procedures card, so that I can identify high-spending HCPCS codes.

**Acceptance Criteria:**

* **AC-DASH-002.1:** The system shall generate `card2-full-top-procedures.png` at 833x969 pixels showing top 20 HCPCS codes by total spending.
* **AC-DASH-002.2:** The card shall use horizontal bar chart with HCPCS code and short description as labels (truncated to 28 chars).
* **AC-DASH-002.3:** Bars shall display values in billions with proper formatting.
* **AC-DASH-002.4:** The card layout shall reserve 120px for y-axis labels and follow design spec padding.

### REQ-DASH-003: Card 3 - Top 20 Providers

**User Story:** As a fraud investigator, I want a top flagged providers card, so that I can see the highest-risk entities.

**Acceptance Criteria:**

* **AC-DASH-003.1:** The system shall generate `card3-full-top-providers.png` at 833x969 pixels showing top 20 flagged providers by estimated recoverable amount.
* **AC-DASH-003.2:** Provider labels shall include anonymized name and state: "Provider Name (ST)".
* **AC-DASH-003.3:** The card shall sort providers descending by quality-weighted impact.
* **AC-DASH-003.4:** All three cards shall follow identical typography, padding, and branding standards.

## Feature Behavior & Rules

Cards use matplotlib with precise figure sizing, DPI, and padding calculations. Text uses plain-language transformations for readability. Cards are saved with white background and 1px border. The design follows chart-design-spec.json specifications exactly. Cards are regenerated each run and can be embedded in web dashboards or presentations.
