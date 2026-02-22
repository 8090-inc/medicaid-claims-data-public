"""Tests for foundation components: config, logging, directories, constants."""

import os
import sys
import tempfile

import pytest
import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ── Configuration Tests ─────────────────────────────────────────────────

class TestProjectConfig:
    """Unit tests for config/project_config.py."""

    def test_project_root_exists(self):
        from config.project_config import PROJECT_ROOT
        assert os.path.isdir(PROJECT_ROOT)

    def test_scripts_dir_exists(self):
        from config.project_config import SCRIPTS_DIR
        assert os.path.isdir(SCRIPTS_DIR)

    def test_output_subdirs_defined(self):
        from config.project_config import OUTPUT_SUBDIRS
        assert len(OUTPUT_SUBDIRS) >= 6

    def test_db_path_is_absolute(self):
        from config.project_config import DB_PATH
        assert os.path.isabs(DB_PATH)

    def test_all_path_constants_are_strings(self):
        from config import project_config
        path_attrs = [a for a in dir(project_config) if a.endswith('_DIR') or a.endswith('_PATH')]
        for attr in path_attrs:
            value = getattr(project_config, attr)
            assert isinstance(value, str), f'{attr} should be a string'


class TestConfigManager:
    """Unit tests for config/manager.py."""

    def test_load_valid_config(self, sample_config):
        from config.manager import ConfigManager
        cm = ConfigManager(sample_config)
        assert cm.pipeline['name'] == 'test'

    def test_missing_config_raises(self, temp_dir):
        from config.manager import ConfigManager, ConfigurationError
        with pytest.raises(ConfigurationError):
            ConfigManager(os.path.join(temp_dir, 'nonexistent.yml'))

    def test_missing_section_raises(self, temp_dir):
        from config.manager import ConfigManager, ConfigurationError
        bad_config = os.path.join(temp_dir, 'bad.yml')
        with open(bad_config, 'w') as f:
            yaml.dump({'pipeline': {}}, f)
        with pytest.raises(ConfigurationError):
            ConfigManager(bad_config)

    def test_dot_path_access(self, sample_config):
        from config.manager import ConfigManager
        cm = ConfigManager(sample_config)
        assert cm.get('database.threads') == 1

    def test_dot_path_default(self, sample_config):
        from config.manager import ConfigManager
        cm = ConfigManager(sample_config)
        assert cm.get('nonexistent.key', 'fallback') == 'fallback'

    def test_as_dict(self, sample_config):
        from config.manager import ConfigManager
        cm = ConfigManager(sample_config)
        d = cm.as_dict()
        assert 'pipeline' in d
        assert 'database' in d


# ── Constants Tests ─────────────────────────────────────────────────────

class TestConstants:
    """Unit tests for utils/constants.py."""

    def test_top_30_codes_count(self):
        from utils.constants import TOP_30_CODES
        assert len(TOP_30_CODES) == 30

    def test_top_20_is_subset(self):
        from utils.constants import TOP_20_CODES, TOP_30_CODES
        assert TOP_20_CODES == TOP_30_CODES[:20]

    def test_hcpcs_categories_count(self):
        from utils.constants import HCPCS_CATEGORIES
        assert len(HCPCS_CATEGORIES) == 10

    def test_em_families_keys(self):
        from utils.constants import EM_FAMILIES
        assert 'office_established' in EM_FAMILIES
        assert 'office_new' in EM_FAMILIES
        assert 'ed_visit' in EM_FAMILIES
        assert 'hospital_initial' in EM_FAMILIES
        assert 'hospital_subsequent' in EM_FAMILIES

    def test_physical_limits_structure(self):
        from utils.constants import PHYSICAL_LIMITS
        for code, info in PHYSICAL_LIMITS.items():
            assert 'unit_minutes' in info
            assert 'max_units_per_bene_per_month' in info
            assert 'desc' in info

    def test_specialties_not_empty(self):
        from utils.constants import SPECIALTIES
        assert len(SPECIALTIES) >= 20

    def test_confidence_tiers(self):
        from utils.constants import CONFIDENCE_TIERS
        assert CONFIDENCE_TIERS['high']['min_score'] > CONFIDENCE_TIERS['medium']['min_score']
        assert CONFIDENCE_TIERS['medium']['min_score'] > CONFIDENCE_TIERS['low']['min_score']

    def test_design_8090_tokens(self):
        from utils.constants import DESIGN_8090
        assert DESIGN_8090['brand_blue'] == '#0052CC'
        assert DESIGN_8090['font_sans'] == 'IBM Plex Sans'


# ── Directory Manager Tests ─────────────────────────────────────────────

class TestDirectoryManager:
    """Unit tests for utils/directory_manager.py."""

    def test_ensure_directory(self, temp_dir):
        from utils.directory_manager import ensure_directory
        new_dir = os.path.join(temp_dir, 'test_subdir')
        ensure_directory(new_dir)
        assert os.path.isdir(new_dir)

    def test_get_relative_path(self):
        from utils.directory_manager import get_relative_path
        from config.project_config import PROJECT_ROOT
        abs_path = os.path.join(PROJECT_ROOT, 'output', 'charts')
        rel_path = get_relative_path(abs_path)
        assert rel_path == os.path.join('output', 'charts')


# ── Threshold Manager Tests ─────────────────────────────────────────────

class TestThresholdManager:
    """Unit tests for config/thresholds.py."""

    def test_defaults_loaded(self):
        from config.thresholds import ThresholdManager
        tm = ThresholdManager()
        assert tm.get('z_score_high') == 3.0

    def test_override(self):
        from config.thresholds import ThresholdManager
        tm = ThresholdManager({'z_score_high': 4.0})
        assert tm.get('z_score_high') == 4.0

    def test_attribute_access(self):
        from config.thresholds import ThresholdManager
        tm = ThresholdManager()
        assert tm.z_score_high == 3.0

    def test_unknown_attribute_raises(self):
        from config.thresholds import ThresholdManager
        tm = ThresholdManager()
        with pytest.raises(AttributeError):
            _ = tm.nonexistent_threshold


# ── Logging Tests ───────────────────────────────────────────────────────

class TestLogging:
    """Unit tests for config/logging_config.py."""

    def test_setup_logging_returns_logger(self):
        from config.logging_config import setup_logging
        logger = setup_logging(console=True, file_logging=False)
        assert logger.name == 'medicaid_fwa'

    def test_get_logger(self):
        from config.logging_config import get_logger, setup_logging
        setup_logging(console=False, file_logging=False)
        logger = get_logger('test_module')
        assert 'medicaid_fwa.test_module' == logger.name


# ── Error Classifier Tests ──────────────────────────────────────────────

class TestErrorClassifier:
    """Unit tests for scripts/orchestration/error_classifier.py."""

    def test_memory_error_is_critical(self):
        from scripts.orchestration.error_classifier import classify_error, ErrorSeverity
        assert classify_error(MemoryError()) == ErrorSeverity.CRITICAL

    def test_os_error_is_critical(self):
        from scripts.orchestration.error_classifier import classify_error, ErrorSeverity
        assert classify_error(OSError('disk full')) == ErrorSeverity.CRITICAL

    def test_value_error_is_error(self):
        from scripts.orchestration.error_classifier import classify_error, ErrorSeverity
        assert classify_error(ValueError('bad value')) == ErrorSeverity.ERROR

    def test_skipping_message_is_warning(self):
        from scripts.orchestration.error_classifier import classify_error, ErrorSeverity
        assert classify_error(RuntimeError('skipping this step')) == ErrorSeverity.WARNING

    def test_format_error_context(self):
        from scripts.orchestration.error_classifier import format_error_context
        ctx = format_error_context(ValueError('test'), milestone='M01', script='01_ingest.py')
        assert ctx['milestone'] == 'M01'
        assert ctx['error_type'] == 'ValueError'


# ── Detection Methods Tests ─────────────────────────────────────────────

class TestDetectionMethodManager:
    """Unit tests for config/detection_methods.py."""

    def test_all_methods_enabled_by_default(self):
        from config.detection_methods import DetectionMethodManager
        dm = DetectionMethodManager()
        assert dm.is_enabled('z_score')
        assert dm.is_enabled('isolation_forest')

    def test_disable_method(self):
        from config.detection_methods import DetectionMethodManager
        dm = DetectionMethodManager({'z_score': False})
        assert not dm.is_enabled('z_score')

    def test_get_enabled_by_category(self):
        from config.detection_methods import DetectionMethodManager
        dm = DetectionMethodManager()
        cat1 = dm.get_enabled_methods(category='1')
        assert 'z_score' in cat1
