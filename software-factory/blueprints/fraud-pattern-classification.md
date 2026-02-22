---
title: "Fraud Pattern Classification"
feature_name: null
id: "01009f4c-e2b7-4e38-819d-767e8fee00e6"
---

## Feature Summary

Fraud Pattern Classification assigns detected fraud into 10 distinct pattern categories (Home Health outliers, Middleman billing, Impossible providers, Daily billing, Sudden starts/stops, Networks & circularity, State spending, Upcoding, Shared beneficiaries, Other patterns) based on detection method signatures and behavioral characteristics. The feature produces a taxonomy of fraud schemes with provider counts, financial exposures, and pattern descriptions to guide policy responses and investigation strategies.

## Component Blueprint Composition

This feature depends on findings and scoring from prior stages:

* **@Fraud Detection Execution** — Provides method flags and findings.
* **@Provider Validation Scores** — Provides composite risk scores.
* **@Financial Impact and Deduplication** — Provides deduplicated impact estimates.

## Feature-Specific Components

```component
name: FraudPatternTaxonomy
container: Pattern Classification
responsibilities:
	- Define 10 fraud pattern categories with classification rules
	- Pattern 1: Home Health & Personal Care Rate/Volume Outliers
	- Pattern 2: Middleman Billing Organizations
	- Pattern 3: Government Agencies as Outliers
	- Pattern 4: Providers That Cannot Exist (no NPPES, deactivated, LEIE)
	- Pattern 5: Billing Every Single Day
	- Pattern 6: Sudden Starts and Stops
	- Pattern 7: Billing Networks & Circular Billing
	- Pattern 8: State-Level Spending Differences
	- Pattern 9: Upcoding & Impossible Volumes
	- Pattern 10: Shared Beneficiary Counts
```

```component
name: ProviderPatternClassifier
container: Pattern Classification
responsibilities:
	- Apply classification rules to each flagged provider
	- Assign primary and secondary patterns based on detection signals, specialty, service type, temporal signature, network position
	- Save provider-to-pattern mapping to provider_fraud_patterns.csv with pattern_confidence scores
```

```component
name: PatternExposureCalculator
container: Pattern Classification
responsibilities:
	- For each pattern, aggregate total deduplicated quality-weighted impact
	- For systemic patterns (3, 8), include state/code aggregate exposures
	- Calculate provider counts per pattern and average impact per provider
	- Save to fraud_pattern_exposure.csv
```

```component
name: PatternSignatureAnalyzer
container: Pattern Classification
responsibilities:
	- Per pattern, calculate signature characteristics: dominant methods, confidence distribution, geographic concentration, specialty mix, service type distribution, temporal profile
	- Identify distinguishing features
	- Save to fraud_pattern_signatures.json
```

```component
name: FraudPatternReporter
container: Pattern Classification
responsibilities:
	- Generate fraud_pattern_summary_report.md with section per pattern
	- Include: definition, detection methods, provider count, exposure, geographic concentration, example providers, recommended interventions
	- Include pattern exposure ranking and overlap analysis
```

## System Contracts

### Key Contracts

* **Multi-Pattern Assignment**: Providers can belong to multiple patterns; primary = highest confidence.
* **Rule-Based Classification**: Deterministic rules based on methods, specialty, service type, behavior.
* **Systemic vs Individual**: Systemic patterns (3, 8) indicate rate policy issues; individual patterns indicate provider fraud.

### Integration Contracts

* **Input**: Findings from all detection methods, provider validation scores, financial impacts
* **Output**:
  * `output/analysis/provider_fraud_patterns.csv` — Pattern assignments
  * `output/analysis/fraud_pattern_exposure.csv` — Exposure by pattern
  * `output/analysis/fraud_pattern_signatures.json` — Pattern characteristics
  * `output/analysis/fraud_pattern_summary_report.md` — Detailed report
* **Downstream**: @Reporting and Visualization uses patterns for stakeholder communication

## Architecture Decision Records

### ADR-001: Rule-Based Over Learned Classification

**Context:** Fraud patterns are well-understood. Machine learning could discover patterns but introduces black-box interpretation.

**Decision:** Implement rule-based classification combining method signatures, specialty, and behavioral indicators.

**Consequences:**

* Benefits: Interpretability; auditable rules; domain-expert driven
* Trade-off: May miss novel patterns; requires manual rule maintenance
* Validation: Historical fraud cases should validate rule coverage

## Testing & Validation

### Acceptance Tests

* **Pattern Definition**: Verify all 10 fraud patterns defined with classification rules
* **Provider Classification**: Verify each flagged provider assigned primary and secondary patterns
* **Pattern Confidence**: Verify pattern_confidence scores assigned (0.6-0.99 range)
* **Exposure Calculation**: Verify total deduplicated quality-weighted impact aggregated per pattern
* **Systemic Pattern Handling**: Verify systemic patterns aggregate at state/code level separately
* **Report Generation**: Verify fraud_pattern_summary_report.md created with section per pattern

### Unit Tests

* **FraudPatternTaxonomy**: Test pattern definition completeness; test rule logic
* **ProviderPatternClassifier**: Test rule application; test pattern assignment accuracy
* **PatternExposureCalculator**: Test aggregation logic; test provider counting
* **PatternSignatureAnalyzer**: Test signature characteristic extraction
* **PatternReporter**: Test report generation; test ranking logic

### Integration Tests

* **End-to-End Classification**: Load findings -> classify providers -> aggregate exposures -> analyze signatures -> generate report
* **Rule Accuracy**: Manually apply classification rules to sample providers -> verify tool results match
* **Systemic vs Individual**: Verify systemic cases aggregated at state/code level
* **Report Quality**: Review pattern summary report; verify descriptions accurate and actionable

### Test Data Requirements

* **Diverse Findings**: Findings exhibiting all 10 fraud pattern types
* **Multi-Pattern Providers**: Providers flagged by multiple patterns
* **Systemic Cases**: State-level and code-level patterns
* **Geographic Variation**: Patterns distributed across states

### Success Criteria

* All flagged providers classified into 10-pattern taxonomy
* Pattern-to-provider mappings accurately reflect detection evidence
* Exposure aggregated correctly per pattern with deduplication
* Systemic patterns handled separately from individual provider fraud
* Pattern ranking by exposure enables policy responses
* Fraud pattern summary enables executive communication
