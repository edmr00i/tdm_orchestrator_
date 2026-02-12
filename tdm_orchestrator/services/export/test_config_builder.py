# =====================
# Fixtures
# =====================
import pytest
from unittest.mock import MagicMock
from tdm_orchestrator.services.export.config_builder import ConfigBuilder

@pytest.fixture
def mock_application():
    """Create a mock application with basic attributes."""
    app = MagicMock()
    app.name = "test_application"
    app.reference = "APP_REF_001"
    return app


@pytest.fixture
def mock_runner(mock_application):
    """Create a mock runner with basic attributes."""
    runner = MagicMock()
    runner.name = "test_runner"
    runner.reference = "RUNNER_REF_001"
    runner.description = "Test runner description"
    runner.application = mock_application
    runner.stop_on_error = True
    runner.verbose_logging = False
    runner.get_pre_scripts.return_value = []
    runner.get_post_scripts.return_value = []
    return runner


@pytest.fixture
def mock_runner_no_description(mock_application):
    """Create a mock runner without description."""
    runner = MagicMock()
    runner.name = "runner_no_desc"
    runner.reference = "RUNNER_NO_DESC"
    runner.description = None
    runner.application = mock_application
    runner.stop_on_error = False
    runner.verbose_logging = True
    runner.get_pre_scripts.return_value = []
    runner.get_post_scripts.return_value = []
    return runner


@pytest.fixture
def mock_datasource():
    """Create a mock datasource."""
    ds = MagicMock()
    ds.name = "test_datasource"
    ds.reference = "DS_REF_001"
    return ds


@pytest.fixture
def mock_script(mock_datasource):
    """Create a mock script with datasource."""
    script = MagicMock()
    script.name = "test_script"
    script.reference = "SCRIPT_REF_001"
    script.description = "Test script description"
    script.script_type = "SQL"
    script.datasource = mock_datasource
    script.extract_variables.return_value = ["VAR1", "VAR2"]
    return script


@pytest.fixture
def mock_script_no_datasource():
    """Create a mock script without datasource."""
    script = MagicMock()
    script.name = "script_no_ds"
    script.reference = "SCRIPT_NO_DS"
    script.description = None
    script.script_type = "PL/SQL"
    script.datasource = None
    script.extract_variables.return_value = []
    return script


@pytest.fixture
def mock_step(mock_script):
    """Create a mock step with script."""
    step = MagicMock()
    step.script = mock_script
    step.order = 1
    return step


@pytest.fixture
def mock_step_no_datasource(mock_script_no_datasource):
    """Create a mock step without datasource."""
    step = MagicMock()
    step.script = mock_script_no_datasource
    step.order = 2
    return step


@pytest.fixture
def config_builder(mock_runner):
    """Create a ConfigBuilder instance."""
    return ConfigBuilder(mock_runner)


# =====================
# ConfigBuilder.__init__ Tests
# =====================

class TestConfigBuilderInit:
    """Tests for ConfigBuilder.__init__ method."""

    def test_stores_runner_reference(self, mock_runner):
        """Stores runner reference in instance."""
        builder = ConfigBuilder(mock_runner)
        
        assert builder.runner == mock_runner

    def test_accepts_any_runner_instance(self, mock_application):
        """Accepts any object with runner-like attributes."""
        custom_runner = MagicMock()
        custom_runner.name = "custom"
        custom_runner.reference = "CUSTOM_REF"
        custom_runner.application = mock_application
        
        builder = ConfigBuilder(custom_runner)
        
        assert builder.runner.name == "custom"


# =====================
# ConfigBuilder.build Tests
# =====================

class TestConfigBuilderBuild:
    """Tests for ConfigBuilder.build method."""

    def test_returns_dict(self, config_builder, mocker):
        """Returns a dictionary."""
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        
        result = config_builder.build()
        
        assert isinstance(result, dict)

    def test_contains_metadata_key(self, config_builder, mocker):
        """Contains metadata key in result."""
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        
        result = config_builder.build()
        
        assert 'metadata' in result

    def test_contains_execution_settings_key(self, config_builder, mocker):
        """Contains execution_settings key in result."""
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        
        result = config_builder.build()
        
        assert 'execution_settings' in result

    def test_contains_pre_scripts_key(self, config_builder, mocker):
        """Contains pre_scripts key in result."""
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        
        result = config_builder.build()
        
        assert 'pre_scripts' in result

    def test_contains_post_scripts_key(self, config_builder, mocker):
        """Contains post_scripts key in result."""
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        
        result = config_builder.build()
        
        assert 'post_scripts' in result

    def test_contains_anonymization_key(self, config_builder, mocker):
        """Contains anonymization key in result."""
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        
        result = config_builder.build()
        
        assert 'anonymization' in result

    def test_contains_required_variables_key(self, config_builder, mocker):
        """Contains required_variables key in result."""
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        
        result = config_builder.build()
        
        assert 'required_variables' in result

    def test_anonymization_has_engine_tdm_core(self, config_builder, mocker):
        """Anonymization engine is TDM_CORE."""
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        
        result = config_builder.build()
        
        assert result['anonymization']['engine'] == 'TDM_CORE'

    def test_anonymization_has_note(self, config_builder, mocker):
        """Anonymization has note field."""
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        
        result = config_builder.build()
        
        assert result['anonymization']['note'] == 'Gérée par le moteur TDM principal'

    def test_calls_get_pre_scripts(self, config_builder, mocker):
        """Calls runner.get_pre_scripts()."""
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        
        config_builder.build()
        
        config_builder.runner.get_pre_scripts.assert_called_once()

    def test_calls_get_post_scripts(self, config_builder, mocker):
        """Calls runner.get_post_scripts()."""
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        
        config_builder.build()
        
        config_builder.runner.get_post_scripts.assert_called_once()

    def test_logs_info_with_script_counts(self, config_builder, mocker):
        """Logs info message with script counts."""
        mock_logger = mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        
        config_builder.build()
        
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "0 PRE" in log_message
        assert "0 POST" in log_message

    def test_logs_correct_pre_count(self, mock_runner, mock_step, mocker):
        """Logs correct PRE scripts count."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        mock_logger = mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        mock_runner.get_pre_scripts.return_value = [mock_step, mock_step]
        mock_runner.get_post_scripts.return_value = []
        
        builder = ConfigBuilder(mock_runner)
        builder.build()
        
        log_message = mock_logger.info.call_args[0][0]
        assert "2 PRE" in log_message

    def test_logs_correct_post_count(self, mock_runner, mock_step, mocker):
        """Logs correct POST scripts count."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        mock_logger = mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        mock_runner.get_pre_scripts.return_value = []
        mock_runner.get_post_scripts.return_value = [mock_step, mock_step, mock_step]
        
        builder = ConfigBuilder(mock_runner)
        builder.build()
        
        log_message = mock_logger.info.call_args[0][0]
        assert "3 POST" in log_message


# =====================
# ConfigBuilder._build_metadata Tests
# =====================

class TestBuildMetadata:
    """Tests for ConfigBuilder._build_metadata method."""

    def test_returns_dict(self, config_builder):
        """Returns a dictionary."""
        result = config_builder._build_metadata()
        
        assert isinstance(result, dict)

    def test_contains_runner_reference(self, config_builder):
        """Contains runner_reference from runner."""
        result = config_builder._build_metadata()
        
        assert result['runner_reference'] == 'RUNNER_REF_001'

    def test_contains_runner_name(self, config_builder):
        """Contains runner_name from runner."""
        result = config_builder._build_metadata()
        
        assert result['runner_name'] == 'test_runner'

    def test_contains_runner_description(self, config_builder):
        """Contains runner_description from runner."""
        result = config_builder._build_metadata()
        
        assert result['runner_description'] == 'Test runner description'

    def test_runner_description_empty_string_when_none(self, mock_runner_no_description):
        """Runner description is empty string when None."""
        builder = ConfigBuilder(mock_runner_no_description)
        
        result = builder._build_metadata()
        
        assert result['runner_description'] == ''

    def test_contains_application_name(self, config_builder):
        """Contains application_name from runner.application."""
        result = config_builder._build_metadata()
        
        assert result['application_name'] == 'test_application'

    def test_contains_application_reference(self, config_builder):
        """Contains application_reference from runner.application."""
        result = config_builder._build_metadata()
        
        assert result['application_reference'] == 'APP_REF_001'

    def test_contains_export_date_in_iso_format(self, config_builder, mocker):
        """Contains export_date in ISO format."""
        mock_datetime = mocker.patch(
            'tdm_orchestrator.services.export.config_builder.datetime'
        )
        mock_datetime.now.return_value.isoformat.return_value = '2024-01-15T10:30:00'
        
        result = config_builder._build_metadata()
        
        assert result['export_date'] == '2024-01-15T10:30:00'

    def test_contains_export_version(self, config_builder, mocker):
        """Contains export_version from constants."""
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.EXPORT_VERSION',
            '2.0.0'
        )
        
        result = config_builder._build_metadata()
        
        assert result['export_version'] == '2.0.0'

    def test_all_expected_keys_present(self, config_builder):
        """All expected metadata keys are present."""
        result = config_builder._build_metadata()
        
        expected_keys = {
            'runner_reference',
            'runner_name',
            'runner_description',
            'application_name',
            'application_reference',
            'export_date',
            'export_version',
        }
        assert set(result.keys()) == expected_keys


# =====================
# ConfigBuilder._build_execution_settings Tests
# =====================

class TestBuildExecutionSettings:
    """Tests for ConfigBuilder._build_execution_settings method."""

    def test_returns_dict(self, config_builder):
        """Returns a dictionary."""
        result = config_builder._build_execution_settings()
        
        assert isinstance(result, dict)

    def test_contains_stop_on_error_true(self, config_builder):
        """Contains stop_on_error set to True."""
        result = config_builder._build_execution_settings()
        
        assert result['stop_on_error'] is True

    def test_contains_stop_on_error_false(self, mock_runner_no_description):
        """Contains stop_on_error set to False."""
        builder = ConfigBuilder(mock_runner_no_description)
        
        result = builder._build_execution_settings()
        
        assert result['stop_on_error'] is False

    def test_contains_verbose_logging_false(self, config_builder):
        """Contains verbose_logging set to False."""
        result = config_builder._build_execution_settings()
        
        assert result['verbose_logging'] is False

    def test_contains_verbose_logging_true(self, mock_runner_no_description):
        """Contains verbose_logging set to True."""
        builder = ConfigBuilder(mock_runner_no_description)
        
        result = builder._build_execution_settings()
        
        assert result['verbose_logging'] is True

    def test_all_expected_keys_present(self, config_builder):
        """All expected execution settings keys are present."""
        result = config_builder._build_execution_settings()
        
        expected_keys = {'stop_on_error', 'verbose_logging'}
        assert set(result.keys()) == expected_keys


# =====================
# ConfigBuilder._build_scripts_config Tests
# =====================

class TestBuildScriptsConfig:
    """Tests for ConfigBuilder._build_scripts_config method."""

    def test_returns_list(self, config_builder):
        """Returns a list."""
        result = config_builder._build_scripts_config([], 'pre')
        
        assert isinstance(result, list)

    def test_returns_empty_list_for_no_steps(self, config_builder):
        """Returns empty list when no steps provided."""
        result = config_builder._build_scripts_config([], 'pre')
        
        assert result == []

    def test_returns_correct_count(self, config_builder, mock_step, mocker):
        """Returns correct number of script configs."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        steps = [mock_step, mock_step, mock_step]
        
        result = config_builder._build_scripts_config(steps, 'pre')
        
        assert len(result) == 3

    def test_contains_order(self, config_builder, mock_step, mocker):
        """Contains order from step."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        mock_step.order = 5
        
        result = config_builder._build_scripts_config([mock_step], 'pre')
        
        assert result[0]['order'] == 5

    def test_contains_script_reference(self, config_builder, mock_step, mocker):
        """Contains script_reference from script."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._build_scripts_config([mock_step], 'pre')
        
        assert result[0]['script_reference'] == 'SCRIPT_REF_001'

    def test_contains_script_name(self, config_builder, mock_step, mocker):
        """Contains script_name from script."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._build_scripts_config([mock_step], 'pre')
        
        assert result[0]['script_name'] == 'test_script'

    def test_contains_script_description(self, config_builder, mock_step, mocker):
        """Contains script_description from script."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._build_scripts_config([mock_step], 'pre')
        
        assert result[0]['script_description'] == 'Test script description'

    def test_script_description_empty_when_none(
        self, config_builder, mock_step_no_datasource, mocker
    ):
        """Script description is empty string when None."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._build_scripts_config([mock_step_no_datasource], 'pre')
        
        assert result[0]['script_description'] == ''

    def test_contains_script_type(self, config_builder, mock_step, mocker):
        """Contains script_type from script."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._build_scripts_config([mock_step], 'pre')
        
        assert result[0]['script_type'] == 'SQL'

    def test_contains_datasource_name(self, config_builder, mock_step, mocker):
        """Contains datasource_name when datasource exists."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._build_scripts_config([mock_step], 'pre')
        
        assert result[0]['datasource_name'] == 'test_datasource'

    def test_datasource_name_none_when_no_datasource(
        self, config_builder, mock_step_no_datasource, mocker
    ):
        """Datasource_name is None when no datasource."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._build_scripts_config([mock_step_no_datasource], 'pre')
        
        assert result[0]['datasource_name'] is None

    def test_contains_datasource_reference(self, config_builder, mock_step, mocker):
        """Contains datasource_reference when datasource exists."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._build_scripts_config([mock_step], 'pre')
        
        assert result[0]['datasource_reference'] == 'DS_REF_001'

    def test_datasource_reference_none_when_no_datasource(
        self, config_builder, mock_step_no_datasource, mocker
    ):
        """Datasource_reference is None when no datasource."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._build_scripts_config([mock_step_no_datasource], 'pre')
        
        assert result[0]['datasource_reference'] is None

    def test_contains_file_with_pre_prefix(self, config_builder, mock_step, mocker):
        """Contains file with 'pre' prefix."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='test_script'
        )
        mock_step.order = 1
        
        result = config_builder._build_scripts_config([mock_step], 'pre')
        
        assert result[0]['file'] == 'pre_001_test_script.sql'

    def test_contains_file_with_post_prefix(self, config_builder, mock_step, mocker):
        """Contains file with 'post' prefix."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='test_script'
        )
        mock_step.order = 1
        
        result = config_builder._build_scripts_config([mock_step], 'post')
        
        assert result[0]['file'] == 'post_001_test_script.sql'

    def test_contains_variables_list(self, config_builder, mock_step, mocker):
        """Contains variables list from script.extract_variables()."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._build_scripts_config([mock_step], 'pre')
        
        assert result[0]['variables'] == ['VAR1', 'VAR2']

    def test_empty_variables_when_none(
        self, config_builder, mock_step_no_datasource, mocker
    ):
        """Contains empty variables list when no variables."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._build_scripts_config([mock_step_no_datasource], 'pre')
        
        assert result[0]['variables'] == []

    def test_all_expected_keys_present(self, config_builder, mock_step, mocker):
        """All expected script config keys are present."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._build_scripts_config([mock_step], 'pre')
        
        expected_keys = {
            'order',
            'script_reference',
            'script_name',
            'script_description',
            'script_type',
            'datasource_name',
            'datasource_reference',
            'file',
            'variables',
        }
        assert set(result[0].keys()) == expected_keys


# =====================
# ConfigBuilder._get_script_filename Tests
# =====================

class TestGetScriptFilename:
    """Tests for ConfigBuilder._get_script_filename method."""

    def test_returns_string(self, config_builder, mock_script, mocker):
        """Returns a string."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._get_script_filename(mock_script, 1, 'pre')
        
        assert isinstance(result, str)

    def test_format_pre_prefix(self, config_builder, mock_script, mocker):
        """Uses 'pre' prefix correctly."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='my_script'
        )
        
        result = config_builder._get_script_filename(mock_script, 1, 'pre')
        
        assert result.startswith('pre_')

    def test_format_post_prefix(self, config_builder, mock_script, mocker):
        """Uses 'post' prefix correctly."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='my_script'
        )
        
        result = config_builder._get_script_filename(mock_script, 1, 'post')
        
        assert result.startswith('post_')

    def test_pads_order_with_zeros(self, config_builder, mock_script, mocker):
        """Pads order number with leading zeros (3 digits)."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._get_script_filename(mock_script, 5, 'pre')
        
        assert result == 'pre_005_script.sql'

    def test_handles_large_order_number(self, config_builder, mock_script, mocker):
        """Handles order numbers larger than 999."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._get_script_filename(mock_script, 1234, 'pre')
        
        assert result == 'pre_1234_script.sql'

    def test_ends_with_sql_extension(self, config_builder, mock_script, mocker):
        """Ends with .sql extension."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._get_script_filename(mock_script, 1, 'pre')
        
        assert result.endswith('.sql')

    def test_calls_sanitize_filename(self, config_builder, mock_script, mocker):
        """Calls sanitize_filename with script name."""
        mock_sanitize = mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='sanitized_name'
        )
        
        config_builder._get_script_filename(mock_script, 1, 'pre')
        
        mock_sanitize.assert_called_once_with('test_script')

    def test_uses_sanitized_name(self, config_builder, mock_script, mocker):
        """Uses sanitized name in filename."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='clean_name'
        )
        
        result = config_builder._get_script_filename(mock_script, 1, 'pre')
        
        assert 'clean_name' in result


# =====================
# ConfigBuilder._collect_variables Tests
# =====================

class TestCollectVariables:
    """Tests for ConfigBuilder._collect_variables method."""

    def test_returns_list(self, config_builder):
        """Returns a list."""
        config = {'pre_scripts': [], 'post_scripts': []}
        
        result = config_builder._collect_variables(config)
        
        assert isinstance(result, list)

    def test_returns_empty_list_for_no_scripts(self, config_builder):
        """Returns empty list when no scripts."""
        config = {'pre_scripts': [], 'post_scripts': []}
        
        result = config_builder._collect_variables(config)
        
        assert result == []

    def test_collects_from_pre_scripts(self, config_builder):
        """Collects variables from pre_scripts."""
        config = {
            'pre_scripts': [
                {'variables': ['VAR1', 'VAR2']},
            ],
            'post_scripts': [],
        }
        
        result = config_builder._collect_variables(config)
        
        assert 'VAR1' in result
        assert 'VAR2' in result

    def test_collects_from_post_scripts(self, config_builder):
        """Collects variables from post_scripts."""
        config = {
            'pre_scripts': [],
            'post_scripts': [
                {'variables': ['VAR3', 'VAR4']},
            ],
        }
        
        result = config_builder._collect_variables(config)
        
        assert 'VAR3' in result
        assert 'VAR4' in result

    def test_collects_from_both_pre_and_post(self, config_builder):
        """Collects variables from both pre and post scripts."""
        config = {
            'pre_scripts': [
                {'variables': ['VAR1']},
            ],
            'post_scripts': [
                {'variables': ['VAR2']},
            ],
        }
        
        result = config_builder._collect_variables(config)
        
        assert 'VAR1' in result
        assert 'VAR2' in result

    def test_removes_duplicates(self, config_builder):
        """Removes duplicate variables."""
        config = {
            'pre_scripts': [
                {'variables': ['VAR1', 'VAR2']},
            ],
            'post_scripts': [
                {'variables': ['VAR2', 'VAR3']},
            ],
        }
        
        result = config_builder._collect_variables(config)
        
        assert result.count('VAR2') == 1

    def test_returns_sorted_list(self, config_builder):
        """Returns variables sorted alphabetically."""
        config = {
            'pre_scripts': [
                {'variables': ['ZEBRA', 'APPLE']},
            ],
            'post_scripts': [
                {'variables': ['MANGO']},
            ],
        }
        
        result = config_builder._collect_variables(config)
        
        assert result == ['APPLE', 'MANGO', 'ZEBRA']

    def test_handles_multiple_scripts(self, config_builder):
        """Handles multiple scripts in each category."""
        config = {
            'pre_scripts': [
                {'variables': ['A', 'B']},
                {'variables': ['C', 'D']},
            ],
            'post_scripts': [
                {'variables': ['E', 'F']},
                {'variables': ['G', 'A']},  # 'A' is duplicate
            ],
        }
        
        result = config_builder._collect_variables(config)
        
        assert len(result) == 7  # A, B, C, D, E, F, G (no duplicates)
        assert result == ['A', 'B', 'C', 'D', 'E', 'F', 'G']

    def test_handles_empty_variables_list(self, config_builder):
        """Handles scripts with empty variables list."""
        config = {
            'pre_scripts': [
                {'variables': []},
            ],
            'post_scripts': [
                {'variables': ['VAR1']},
            ],
        }
        
        result = config_builder._collect_variables(config)
        
        assert result == ['VAR1']


# =====================
# Integration Tests
# =====================

class TestConfigBuilderIntegration:
    """Integration tests for ConfigBuilder."""

    def test_full_build_workflow(self, mock_runner, mock_step, mocker):
        """Tests complete build workflow with scripts."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='test_script'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.EXPORT_VERSION',
            '1.0.0'
        )
        mock_datetime = mocker.patch(
            'tdm_orchestrator.services.export.config_builder.datetime'
        )
        mock_datetime.now.return_value.isoformat.return_value = '2024-01-15T10:00:00'
        
        step2 = MagicMock()
        step2.order = 1
        step2.script = MagicMock()
        step2.script.name = "post_script"
        step2.script.reference = "POST_REF"
        step2.script.description = "Post description"
        step2.script.script_type = "SQL"
        step2.script.datasource = None
        step2.script.extract_variables.return_value = ['VAR3']
        
        mock_runner.get_pre_scripts.return_value = [mock_step]
        mock_runner.get_post_scripts.return_value = [step2]
        
        builder = ConfigBuilder(mock_runner)
        result = builder.build()
        
        # Verify structure
        assert len(result['pre_scripts']) == 1
        assert len(result['post_scripts']) == 1
        assert result['metadata']['runner_name'] == 'test_runner'
        assert result['execution_settings']['stop_on_error'] is True
        assert 'VAR1' in result['required_variables']
        assert 'VAR2' in result['required_variables']
        assert 'VAR3' in result['required_variables']

    def test_build_with_no_scripts(self, mock_runner, mocker):
        """Tests build with no scripts."""
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        mock_runner.get_pre_scripts.return_value = []
        mock_runner.get_post_scripts.return_value = []
        
        builder = ConfigBuilder(mock_runner)
        result = builder.build()
        
        assert result['pre_scripts'] == []
        assert result['post_scripts'] == []
        assert result['required_variables'] == []

    def test_build_preserves_order(self, mock_runner, mocker):
        """Tests that scripts preserve their order."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        
        steps = []
        for i in [3, 1, 2]:  # Intentionally out of order
            step = MagicMock()
            step.order = i
            step.script = MagicMock()
            step.script.name = f"script_{i}"
            step.script.reference = f"REF_{i}"
            step.script.description = None
            step.script.script_type = "SQL"
            step.script.datasource = None
            step.script.extract_variables.return_value = []
            steps.append(step)
        
        mock_runner.get_pre_scripts.return_value = steps
        mock_runner.get_post_scripts.return_value = []
        
        builder = ConfigBuilder(mock_runner)
        result = builder.build()
        
        # Order should match input order (3, 1, 2)
        assert result['pre_scripts'][0]['order'] == 3
        assert result['pre_scripts'][1]['order'] == 1
        assert result['pre_scripts'][2]['order'] == 2


# =====================
# Edge Cases
# =====================

class TestConfigBuilderEdgeCases:
    """Edge case tests for ConfigBuilder."""

    def test_runner_with_unicode_name(self, mock_application, mocker):
        """Handles runner with unicode name."""
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        
        runner = MagicMock()
        runner.name = "日本語ランナー"
        runner.reference = "JP_RUNNER"
        runner.description = "日本語の説明"
        runner.application = mock_application
        runner.stop_on_error = True
        runner.verbose_logging = False
        runner.get_pre_scripts.return_value = []
        runner.get_post_scripts.return_value = []
        
        builder = ConfigBuilder(runner)
        result = builder.build()
        
        assert result['metadata']['runner_name'] == '日本語ランナー'
        assert result['metadata']['runner_description'] == '日本語の説明'

    def test_script_with_empty_description(self, config_builder, mocker):
        """Handles script with empty string description."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        step = MagicMock()
        step.order = 1
        step.script = MagicMock()
        step.script.name = "script"
        step.script.reference = "REF"
        step.script.description = ""  # Empty string, not None
        step.script.script_type = "SQL"
        step.script.datasource = None
        step.script.extract_variables.return_value = []
        
        result = config_builder._build_scripts_config([step], 'pre')
        
        assert result[0]['script_description'] == ''

    def test_very_large_order_number(self, config_builder, mock_script, mocker):
        """Handles very large order numbers."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._get_script_filename(mock_script, 99999, 'pre')
        
        assert result == 'pre_99999_script.sql'

    def test_order_zero(self, config_builder, mock_script, mocker):
        """Handles order number of 0."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.sanitize_filename',
            return_value='script'
        )
        
        result = config_builder._get_script_filename(mock_script, 0, 'pre')
        
        assert result == 'pre_000_script.sql'

    def test_many_variables_sorted(self, config_builder):
        """Tests sorting with many variables."""
        config = {
            'pre_scripts': [
                {'variables': ['Z', 'M', 'A', 'B']},
            ],
            'post_scripts': [
                {'variables': ['X', 'C', 'Y', 'D']},
            ],
        }
        
        result = config_builder._collect_variables(config)
        
        assert result == ['A', 'B', 'C', 'D', 'M', 'X', 'Y', 'Z']

    def test_application_with_special_characters(self, mock_runner, mocker):
        """Handles application with special characters."""
        mocker.patch(
            'tdm_orchestrator.services.export.config_builder.logger'
        )
        
        mock_runner.application.name = "App & Co. <Test>"
        mock_runner.application.reference = "APP/REF\\001"
        
        builder = ConfigBuilder(mock_runner)
        result = builder.build()
        
        assert result['metadata']['application_name'] == "App & Co. <Test>"
        assert result['metadata']['application_reference'] == "APP/REF\\001"


# =====================
# Summary of Covered Cases
# =====================
# __init__:
# - Stores runner reference
# - Accepts any runner-like object
#
# build:
# - Returns dict with all expected keys
# - Contains metadata, execution_settings, pre_scripts, post_scripts
# - Contains anonymization with TDM_CORE engine
# - Contains required_variables
# - Calls get_pre_scripts and get_post_scripts
# - Logs info with correct script counts
#
# _build_metadata:
# - Returns dict with all expected keys
# - Contains runner reference, name, description
# - Handles None description as empty string
# - Contains application name and reference
# - Contains export_date in ISO format
# - Contains export_version
#
# _build_execution_settings:
# - Returns dict with stop_on_error and verbose_logging
# - Handles True/False values correctly
#
# _build_scripts_config:
# - Returns list of script configs
# - Handles empty steps list
# - Contains all expected script config keys
# - Handles datasource presence/absence
# - Handles description presence/absence
# - Uses correct file naming
# - Collects variables from scripts
#
# _get_script_filename:
# - Returns correctly formatted string
# - Uses pre/post prefix
# - Pads order with zeros
# - Handles large order numbers
# - Ends with .sql
# - Calls sanitize_filename
#
# _collect_variables:
# - Returns sorted list of unique variables
# - Collects from pre and post scripts
# - Removes duplicates
# - Handles empty variables lists
# - Handles multiple scripts
#
# Integration:
# - Full workflow with scripts
# - Build with no scripts
# - Preserves script order
#
# Edge cases:
# - Unicode names and descriptions
# - Empty string description
# - Very large order numbers
# - Order zero
# - Many variables sorting
# - Special characters in application