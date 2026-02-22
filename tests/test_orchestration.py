"""Tests for pipeline orchestration: milestone manager, checkpoint, execution logger."""

import json
import os
import sys
import tempfile

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class TestMilestoneManager:
    """Tests for milestone_manager.py."""

    def test_milestones_count(self):
        from scripts.orchestration.milestone_manager import MILESTONES
        assert len(MILESTONES) == 26  # 24 milestones + 13b + 12b

    def test_milestone_sequence_full(self):
        from scripts.orchestration.milestone_manager import get_milestone_sequence
        seq = get_milestone_sequence()
        assert len(seq) == 26
        assert seq[0][0] == '00_data_quality.py'
        assert seq[-1][0] == '23_generate_provider_validation_scores.py'

    def test_start_from_filters(self):
        from scripts.orchestration.milestone_manager import get_milestone_sequence
        seq = get_milestone_sequence(start_from='03_eda.py')
        assert seq[0][0] == '03_eda.py'
        assert len(seq) < 26

    def test_skip_filters(self):
        from scripts.orchestration.milestone_manager import get_milestone_sequence
        seq = get_milestone_sequence(skip={'03_eda.py'})
        scripts = [s[0] for s in seq]
        assert '03_eda.py' not in scripts

    def test_start_from_by_number(self):
        from scripts.orchestration.milestone_manager import get_milestone_sequence
        seq = get_milestone_sequence(start_from='3')
        assert seq[0][0] == '03_eda.py'


class TestCheckpointManager:
    """Tests for CheckpointManager."""

    def test_save_and_load(self, temp_dir):
        from scripts.orchestration.milestone_manager import CheckpointManager
        path = os.path.join(temp_dir, 'checkpoints.json')
        cp = CheckpointManager(path)
        cp.mark_completed('01_setup_and_ingest.py', 5.0)
        assert cp.get_last_completed() == '01_setup_and_ingest.py'

        # Reload from disk
        cp2 = CheckpointManager(path)
        assert cp2.get_last_completed() == '01_setup_and_ingest.py'

    def test_resume_point(self, temp_dir):
        from scripts.orchestration.milestone_manager import CheckpointManager
        path = os.path.join(temp_dir, 'checkpoints.json')
        cp = CheckpointManager(path)
        cp.mark_completed('00_data_quality.py', 2.0)
        resume = cp.get_resume_point()
        assert resume == '01_setup_and_ingest.py'

    def test_reset(self, temp_dir):
        from scripts.orchestration.milestone_manager import CheckpointManager
        path = os.path.join(temp_dir, 'checkpoints.json')
        cp = CheckpointManager(path)
        cp.mark_completed('01_setup_and_ingest.py', 5.0)
        cp.reset()
        assert cp.get_last_completed() is None

    def test_is_completed(self, temp_dir):
        from scripts.orchestration.milestone_manager import CheckpointManager
        path = os.path.join(temp_dir, 'checkpoints.json')
        cp = CheckpointManager(path)
        cp.mark_completed('00_data_quality.py', 2.0)
        assert cp.is_completed('00_data_quality.py')
        assert not cp.is_completed('01_setup_and_ingest.py')


class TestExecutionLogger:
    """Tests for ExecutionLogger."""

    def test_results_tracking(self):
        from scripts.orchestration.execution_logger import ExecutionLogger
        el = ExecutionLogger(3)
        el.log_milestone_start('Test M1', 'test.py', 0)
        el.log_milestone_end('Test M1', True, 1.5)
        results = el.get_results()
        assert len(results) == 1
        assert results[0] == ('Test M1', True, 1.5)


class TestValidationManager:
    """Tests for validation_manager.py."""

    def test_validate_file_exists(self, temp_dir):
        from scripts.orchestration.validation_manager import validate_file_exists
        path = os.path.join(temp_dir, 'test.txt')
        ok, msg = validate_file_exists(path)
        assert not ok

        with open(path, 'w') as f:
            f.write('content')
        ok, msg = validate_file_exists(path)
        assert ok

    def test_validate_json_file(self, temp_dir):
        from scripts.orchestration.validation_manager import validate_json_file
        path = os.path.join(temp_dir, 'test.json')
        with open(path, 'w') as f:
            json.dump([{'id': 'H0001', 'score': 0.9}], f)
        ok, msg, data = validate_json_file(path, required_keys=['id'])
        assert ok
        assert len(data) == 1

    def test_validate_json_missing_keys(self, temp_dir):
        from scripts.orchestration.validation_manager import validate_json_file
        path = os.path.join(temp_dir, 'test.json')
        with open(path, 'w') as f:
            json.dump([{'id': 'H0001'}], f)
        ok, msg, data = validate_json_file(path, required_keys=['id', 'missing_key'])
        assert not ok

    def test_validate_database_tables(self, test_db_connection):
        from scripts.orchestration.validation_manager import validate_database_tables
        ok, missing = validate_database_tables(test_db_connection, ['claims', 'provider_summary'])
        assert ok
        assert len(missing) == 0

        ok, missing = validate_database_tables(test_db_connection, ['nonexistent_table'])
        assert not ok
        assert 'nonexistent_table' in missing


class TestMilestoneBase:
    """Tests for milestone_base.py."""

    def test_validate_inputs_missing(self, temp_dir):
        from scripts.orchestration.milestone_base import MilestoneBase
        mb = MilestoneBase()
        mb.required_inputs = [os.path.join(temp_dir, 'nonexistent')]
        ok, missing = mb.validate_inputs()
        assert not ok

    def test_validate_inputs_present(self, temp_dir):
        from scripts.orchestration.milestone_base import MilestoneBase
        path = os.path.join(temp_dir, 'exists.txt')
        with open(path, 'w') as f:
            f.write('data')
        mb = MilestoneBase()
        mb.required_inputs = [path]
        ok, missing = mb.validate_inputs()
        assert ok


class TestPerformanceManager:
    """Tests for performance_manager.py."""

    def test_tracker_checkpoint(self):
        from scripts.orchestration.performance_manager import PerformanceTracker
        pt = PerformanceTracker('test')
        pt.start()
        pt.checkpoint('loaded data', row_count=100)
        summary = pt.finish()
        assert summary['milestone'] == 'test'
        assert len(summary['checkpoints']) == 1
        assert summary['checkpoints'][0]['row_count'] == 100

    def test_progress_reporter(self, capsys):
        from scripts.orchestration.performance_manager import ProgressReporter
        pr = ProgressReporter(100, report_every=50)
        for _ in range(100):
            pr.update()
        assert pr.processed == 100
