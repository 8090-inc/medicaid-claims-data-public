"""Milestone dependency graph, ordering, and checkpoint management.

Defines the 24-milestone execution sequence with dependencies,
manages checkpoint save/restore for pipeline resumption.
"""

import json
import os
import time

from config.project_config import CHECKPOINT_PATH

# Milestone registry: (script_name, description, milestone_number)
# Execution order differs from script numbering — this is the canonical order.
MILESTONES = [
    ('00_data_quality.py', 'Milestone 0: CSV Data Quality Scan', 0),
    ('01_setup_and_ingest.py', 'Milestone 1: Data Ingestion', 1),
    ('02_enrich_references.py', 'Milestone 2: Reference Data Enrichment', 2),
    ('03_eda.py', 'Milestone 3: Exploratory Data Analysis', 3),
    ('04_generate_hypotheses.py', 'Milestone 4: Hypothesis Generation', 4),
    ('12_feasibility_matrix.py', 'Milestone 12: Hypothesis Feasibility Matrix', 12),
    ('05_run_hypotheses_1_to_5.py', 'Milestone 5: Parallel Hypothesis Testing (Cat 1-5)', 5),
    ('06_run_ml_hypotheses.py', 'Milestone 6: ML/DL Anomaly Detection', 6),
    ('07_run_domain_rules.py', 'Milestone 7: Domain-Specific Rules', 7),
    ('08_run_crossref_composite.py', 'Milestone 8: Cross-Reference & Composite', 8),
    ('15_build_dq_atlas_weights.py', 'Milestone 15: Build DQ Atlas State Weights', 15),
    ('09_financial_impact.py', 'Milestone 9: Financial Impact & Deduplication', 9),
    ('16_generate_current_pack.py', 'Milestone 16: Current Risk Queue Pack', 16),
    ('10_generate_charts.py', 'Milestone 10: Chart Generation', 10),
    ('11_generate_report.py', 'Milestone 11: Report Assembly', 11),
    ('13_panel_build.py', 'Milestone 13: Longitudinal Panel Build', 13),
    ('13_longitudinal_multivariate_analysis.py', 'Milestone 13b: Longitudinal Multivariate Analysis', 131),
    ('14_validation_calibration.py', 'Milestone 14: Validation & Calibration', 14),
    ('12_validate_hypotheses.py', 'Milestone 12b: Hypothesis Validation Summary', 121),
    ('18_generate_hypothesis_cards.py', 'Milestone 18: Hypothesis Cards', 18),
    ('17_generate_cards.py', 'Milestone 17: Executive Dashboard Cards', 17),
    ('19_generate_executive_brief.py', 'Milestone 19: Executive Brief', 19),
    ('20_generate_merged_cards.py', 'Milestone 20: Merged Aggregate + Hypothesis Cards', 20),
    ('21_generate_fraud_patterns.py', 'Milestone 21: Fraud Pattern Summary', 21),
    ('22_generate_action_plan.py', 'Milestone 22: Action Plan Memo + Priority Queue', 22),
    ('23_generate_provider_validation_scores.py', 'Milestone 23: Provider Validation Scores', 23),
]


def get_milestone_sequence(start_from=None, skip=None):
    """Return the milestone execution list, optionally filtered.

    Args:
        start_from: Script name or milestone number to resume from.
        skip: Set of script names or milestone numbers to skip.

    Returns:
        List of (script_name, description, milestone_number) tuples.
    """
    skip = skip or set()
    sequence = []
    started = start_from is None

    for script_name, description, milestone_num in MILESTONES:
        if not started:
            if str(start_from) in (script_name, str(milestone_num), description):
                started = True
            else:
                continue
        if script_name in skip or str(milestone_num) in skip:
            continue
        sequence.append((script_name, description, milestone_num))

    return sequence


class CheckpointManager:
    """Manages pipeline execution checkpoints for resume capability."""

    def __init__(self, checkpoint_path=None):
        self._path = checkpoint_path or CHECKPOINT_PATH
        self._data = self._load()

    def _load(self):
        """Load checkpoint data from disk."""
        if os.path.exists(self._path):
            with open(self._path) as f:
                return json.load(f)
        return {'completed': [], 'last_completed': None, 'started_at': None}

    def save(self):
        """Persist checkpoint data to disk."""
        with open(self._path, 'w') as f:
            json.dump(self._data, f, indent=2)

    def mark_completed(self, script_name, elapsed):
        """Record a milestone as completed."""
        self._data['completed'].append({
            'script': script_name,
            'completed_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'elapsed_seconds': round(elapsed, 1),
        })
        self._data['last_completed'] = script_name
        self.save()

    def get_last_completed(self):
        """Return the script name of the last completed milestone, or None."""
        return self._data.get('last_completed')

    def get_resume_point(self):
        """Determine the script to resume from (the one after last completed).

        Returns:
            Script name to resume from, or None if no checkpoint exists.
        """
        last = self.get_last_completed()
        if last is None:
            return None
        for i, (script_name, _, _) in enumerate(MILESTONES):
            if script_name == last and i + 1 < len(MILESTONES):
                return MILESTONES[i + 1][0]
        return None

    def is_completed(self, script_name):
        """Check if a milestone was already completed in this checkpoint."""
        return any(c['script'] == script_name for c in self._data.get('completed', []))

    def reset(self):
        """Clear all checkpoints for a fresh run."""
        self._data = {'completed': [], 'last_completed': None, 'started_at': None}
        self.save()

    def mark_pipeline_start(self):
        """Record pipeline start time."""
        self._data['started_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        self.save()
