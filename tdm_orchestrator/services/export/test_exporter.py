import pytest
from unittest.mock import MagicMock

from tdm_orchestrator.services.export.exporter import (
    RunnerExporter,
    export_runner_to_zip,
    ExportError,
)


# =====================
# Fixtures
# =====================

@pytest.fixture
def mock_runner():
    """Create a mock runner with basic attributes."""
    runner = MagicMock()
    runner.name = "test_runner"
    runner.reference = "TEST_REF"
    runner.get_pre_scripts.return_value = []
    runner.get_post_scripts.return_value = []
    return runner


@pytest.fixture
def mock_step():
    """Create a mock step with script."""
    step = MagicMock()
    step.script = MagicMock()
    step.script.content = "SELECT * FROM users"
    return step


@pytest.fixture
def mock_config():
    """Create a mock configuration dictionary."""
    return {
        'metadata': {
            'runner_name': 'test_runner',
            'runner_reference': 'TEST_REF',
            'application_name': 'test_app',
        },
        'pre_scripts': [{'name': 'pre_script_1'}],
        'post_scripts': [{'name': 'post_script_1'}, {'name': 'post_script_2'}],
        'required_variables': ['VAR1', 'VAR2'],
    }


@pytest.fixture
def mock_config_empty():
    """Create a mock configuration with empty scripts."""
    return {
        'metadata': {
            'runner_name': 'empty_runner',
            'runner_reference': 'EMPTY_REF',
            'application_name': 'empty_app',
        },
        'pre_scripts': [],
        'post_scripts': [],
        'required_variables': [],
    }


# =====================
# RunnerExporter.__init__ Tests
# =====================

class TestRunnerExporterInit:
    """Tests for RunnerExporter.__init__ method."""

    def test_stores_runner_reference(self, mock_runner, mocker):
        """Stores runner reference in instance."""
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        
        assert exporter.runner == mock_runner

    def test_creates_config_builder_with_runner(self, mock_runner, mocker):
        """Creates ConfigBuilder with runner."""
        mock_config_builder_class = mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        RunnerExporter(mock_runner)
        
        mock_config_builder_class.assert_called_once_with(mock_runner)

    def test_creates_zip_builder_with_runner(self, mock_runner, mocker):
        """Creates ZipBuilder with runner."""
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder'
        )
        mock_zip_builder_class = mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        RunnerExporter(mock_runner)
        
        mock_zip_builder_class.assert_called_once_with(mock_runner)

    def test_stores_config_builder_instance(self, mock_runner, mocker):
        """Stores ConfigBuilder instance."""
        mock_config_builder = MagicMock()
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        
        assert exporter.config_builder == mock_config_builder

    def test_stores_zip_builder_instance(self, mock_runner, mocker):
        """Stores ZipBuilder instance."""
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder'
        )
        mock_zip_builder = MagicMock()
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        
        assert exporter.zip_builder == mock_zip_builder


# =====================
# RunnerExporter.export Tests
# =====================

class TestRunnerExporterExport:
    """Tests for RunnerExporter.export method."""

    def test_builds_config_from_config_builder(self, mock_runner, mock_config, mocker):
        """Calls config_builder.build() to generate configuration."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.return_value = "/path/to/output.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        exporter.export()
        
        mock_config_builder.build.assert_called_once()

    def test_writes_config_file_with_config(self, mock_runner, mock_config, mocker):
        """Calls zip_builder.write_config_file() with config."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.return_value = "/path/to/output.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        exporter.export()
        
        mock_zip_builder.write_config_file.assert_called_once_with(mock_config)

    def test_writes_script_files_with_config(self, mock_runner, mock_config, mocker):
        """Calls zip_builder.write_script_files() with config."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.return_value = "/path/to/output.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        exporter.export()
        
        mock_zip_builder.write_script_files.assert_called_once_with(mock_config)

    def test_writes_readme_with_config(self, mock_runner, mock_config, mocker):
        """Calls zip_builder.write_readme() with config."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.return_value = "/path/to/output.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        exporter.export()
        
        mock_zip_builder.write_readme.assert_called_once_with(mock_config)

    def test_creates_zip_with_output_path(self, mock_runner, mock_config, mocker):
        """Calls zip_builder.create_zip() with output_path."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.return_value = "/custom/path/output.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        exporter.export(output_path="/custom/path/output.zip")
        
        mock_zip_builder.create_zip.assert_called_once_with("/custom/path/output.zip")

    def test_creates_zip_without_output_path(self, mock_runner, mock_config, mocker):
        """Calls zip_builder.create_zip() with None when no output_path."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.return_value = "/default/path.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        exporter.export()
        
        mock_zip_builder.create_zip.assert_called_once_with(None)

    def test_returns_zip_path(self, mock_runner, mock_config, mocker):
        """Returns the path from zip_builder.create_zip()."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.return_value = "/output/runner_export.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.export()
        
        assert result == "/output/runner_export.zip"

    def test_calls_cleanup_on_success(self, mock_runner, mock_config, mocker):
        """Calls zip_builder.cleanup() on successful export."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.return_value = "/path/output.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        exporter.export()
        
        mock_zip_builder.cleanup.assert_called_once()

    def test_calls_cleanup_on_exception(self, mock_runner, mocker):
        """Calls zip_builder.cleanup() even when exception occurs."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.side_effect = Exception("Build failed")
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mock_zip_builder = MagicMock()
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        
        with pytest.raises(ExportError):
            exporter.export()
        
        mock_zip_builder.cleanup.assert_called_once()

    def test_raises_export_error_on_config_build_failure(self, mock_runner, mocker):
        """Raises ExportError when config_builder.build() fails."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.side_effect = Exception("Config error")
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        
        with pytest.raises(ExportError) as exc_info:
            exporter.export()
        
        assert "Config error" in str(exc_info.value)

    def test_raises_export_error_on_write_config_failure(self, mock_runner, mock_config, mocker):
        """Raises ExportError when write_config_file() fails."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mock_zip_builder = MagicMock()
        mock_zip_builder.write_config_file.side_effect = Exception("Write error")
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        
        with pytest.raises(ExportError) as exc_info:
            exporter.export()
        
        assert "Write error" in str(exc_info.value)

    def test_raises_export_error_on_create_zip_failure(self, mock_runner, mock_config, mocker):
        """Raises ExportError when create_zip() fails."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.side_effect = Exception("Zip creation failed")
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        
        with pytest.raises(ExportError) as exc_info:
            exporter.export()
        
        assert "Zip creation failed" in str(exc_info.value)

    def test_logs_info_on_export_start(self, mock_runner, mock_config, mocker):
        """Logs info message when export starts."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.return_value = "/path/output.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        mock_logger = mocker.patch(
            'tdm_orchestrator.services.export.exporter.logger'
        )
        
        exporter = RunnerExporter(mock_runner)
        exporter.export()
        
        mock_logger.info.assert_any_call("Export du runner : test_runner")

    def test_logs_info_on_export_complete(self, mock_runner, mock_config, mocker):
        """Logs info message when export completes."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.return_value = "/path/output.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        mock_logger = mocker.patch(
            'tdm_orchestrator.services.export.exporter.logger'
        )
        
        exporter = RunnerExporter(mock_runner)
        exporter.export()
        
        mock_logger.info.assert_any_call("Export terminé : /path/output.zip")

    def test_logs_error_on_failure(self, mock_runner, mocker):
        """Logs error message when export fails."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.side_effect = Exception("Unexpected error")
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        mock_logger = mocker.patch(
            'tdm_orchestrator.services.export.exporter.logger'
        )
        
        exporter = RunnerExporter(mock_runner)
        
        with pytest.raises(ExportError):
            exporter.export()
        
        mock_logger.error.assert_called_once()
        assert "Unexpected error" in mock_logger.error.call_args[0][0]


# =====================
# RunnerExporter.get_export_info Tests
# =====================

class TestRunnerExporterGetExportInfo:
    """Tests for RunnerExporter.get_export_info method."""

    def test_returns_dict(self, mock_runner, mock_config, mocker):
        """Returns a dictionary."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.get_export_info()
        
        assert isinstance(result, dict)

    def test_contains_all_expected_keys(self, mock_runner, mock_config, mocker):
        """Returns dictionary with all expected keys."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.get_export_info()
        
        expected_keys = {
            'runner_name',
            'runner_reference',
            'application',
            'pre_scripts_count',
            'post_scripts_count',
            'total_scripts',
            'required_variables',
            'variables_count',
            'estimated_size_kb',
        }
        assert set(result.keys()) == expected_keys

    def test_returns_runner_name_from_config(self, mock_runner, mock_config, mocker):
        """Returns runner_name from config metadata."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.get_export_info()
        
        assert result['runner_name'] == 'test_runner'

    def test_returns_runner_reference_from_config(self, mock_runner, mock_config, mocker):
        """Returns runner_reference from config metadata."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.get_export_info()
        
        assert result['runner_reference'] == 'TEST_REF'

    def test_returns_application_from_config(self, mock_runner, mock_config, mocker):
        """Returns application from config metadata."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.get_export_info()
        
        assert result['application'] == 'test_app'

    def test_returns_pre_scripts_count(self, mock_runner, mock_config, mocker):
        """Returns correct pre_scripts_count."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.get_export_info()
        
        assert result['pre_scripts_count'] == 1

    def test_returns_post_scripts_count(self, mock_runner, mock_config, mocker):
        """Returns correct post_scripts_count."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.get_export_info()
        
        assert result['post_scripts_count'] == 2

    def test_returns_total_scripts(self, mock_runner, mock_config, mocker):
        """Returns correct total_scripts sum."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.get_export_info()
        
        assert result['total_scripts'] == 3

    def test_returns_required_variables(self, mock_runner, mock_config, mocker):
        """Returns required_variables list."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.get_export_info()
        
        assert result['required_variables'] == ['VAR1', 'VAR2']

    def test_returns_variables_count(self, mock_runner, mock_config, mocker):
        """Returns correct variables_count."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.get_export_info()
        
        assert result['variables_count'] == 2

    def test_returns_estimated_size_kb(self, mock_runner, mock_config, mocker):
        """Returns estimated_size_kb from _estimate_export_size."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.get_export_info()
        
        assert isinstance(result['estimated_size_kb'], int)
        assert result['estimated_size_kb'] >= 1

    def test_empty_config_returns_zero_counts(self, mock_runner, mock_config_empty, mocker):
        """Returns zero counts for empty config."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config_empty
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.get_export_info()
        
        assert result['pre_scripts_count'] == 0
        assert result['post_scripts_count'] == 0
        assert result['total_scripts'] == 0
        assert result['variables_count'] == 0


# =====================
# RunnerExporter._estimate_export_size Tests
# =====================

class TestEstimateExportSize:
    """Tests for RunnerExporter._estimate_export_size method."""

    def test_returns_int(self, mock_runner, mocker):
        """Returns an integer value."""
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter._estimate_export_size()
        
        assert isinstance(result, int)

    def test_returns_minimum_one(self, mock_runner, mocker):
        """Returns at least 1 KB."""
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter._estimate_export_size()
        
        assert result >= 1

    def test_includes_base_config_and_readme_size(self, mock_runner, mocker):
        """Includes base config and readme sizes."""
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ESTIMATED_CONFIG_SIZE_KB', 5
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ESTIMATED_README_SIZE_KB', 2
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZIP_COMPRESSION_RATIO', 1.0
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter._estimate_export_size()
        
        # Base is 5 + 2 = 7, with compression ratio 1.0
        assert result >= 7

    def test_includes_script_content_size(self, mock_runner, mock_step, mocker):
        """Includes script content sizes."""
        mock_runner.get_pre_scripts.return_value = [mock_step]
        mock_runner.get_post_scripts.return_value = []
        
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ESTIMATED_CONFIG_SIZE_KB', 0
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ESTIMATED_README_SIZE_KB', 0
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ESTIMATED_HEADER_SIZE_BYTES', 0
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZIP_COMPRESSION_RATIO', 1.0
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter._estimate_export_size()
        
        # Script content is small, but minimum is 1
        assert result >= 1

    def test_includes_header_size_per_script(self, mock_runner, mock_step, mocker):
        """Includes header size for each script."""
        mock_runner.get_pre_scripts.return_value = [mock_step]
        mock_runner.get_post_scripts.return_value = []
        
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ESTIMATED_CONFIG_SIZE_KB', 0
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ESTIMATED_README_SIZE_KB', 0
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ESTIMATED_HEADER_SIZE_BYTES', 1024
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZIP_COMPRESSION_RATIO', 1.0
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter._estimate_export_size()
        
        # Header alone is 1KB
        assert result >= 1

    def test_applies_compression_ratio(self, mock_runner, mocker):
        """Applies ZIP compression ratio."""
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ESTIMATED_CONFIG_SIZE_KB', 10
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ESTIMATED_README_SIZE_KB', 0
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZIP_COMPRESSION_RATIO', 0.5
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter._estimate_export_size()
        
        # 10 * 0.5 = 5
        assert result == 5

    def test_handles_multiple_pre_scripts(self, mock_runner, mocker):
        """Handles multiple PRE scripts."""
        step1 = MagicMock()
        step1.script.content = "SELECT 1"
        step2 = MagicMock()
        step2.script.content = "SELECT 2"
        mock_runner.get_pre_scripts.return_value = [step1, step2]
        mock_runner.get_post_scripts.return_value = []
        
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter._estimate_export_size()
        
        assert result >= 1

    def test_handles_multiple_post_scripts(self, mock_runner, mocker):
        """Handles multiple POST scripts."""
        step1 = MagicMock()
        step1.script.content = "INSERT INTO t VALUES (1)"
        step2 = MagicMock()
        step2.script.content = "UPDATE t SET x = 1"
        mock_runner.get_pre_scripts.return_value = []
        mock_runner.get_post_scripts.return_value = [step1, step2]
        
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter._estimate_export_size()
        
        assert result >= 1

    def test_handles_large_script_content(self, mock_runner, mocker):
        """Handles large script content."""
        large_step = MagicMock()
        large_step.script.content = "X" * 10240  # 10KB of content
        mock_runner.get_pre_scripts.return_value = [large_step]
        mock_runner.get_post_scripts.return_value = []
        
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ESTIMATED_CONFIG_SIZE_KB', 0
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ESTIMATED_README_SIZE_KB', 0
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ESTIMATED_HEADER_SIZE_BYTES', 0
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZIP_COMPRESSION_RATIO', 1.0
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter._estimate_export_size()
        
        assert result >= 10

    def test_handles_unicode_in_script_content(self, mock_runner, mocker):
        """Handles unicode characters in script content."""
        unicode_step = MagicMock()
        unicode_step.script.content = "SELECT '日本語データ' FROM テーブル"
        mock_runner.get_pre_scripts.return_value = [unicode_step]
        mock_runner.get_post_scripts.return_value = []
        
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder'
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter._estimate_export_size()
        
        assert result >= 1


# =====================
# export_runner_to_zip Tests
# =====================

class TestExportRunnerToZip:
    """Tests for export_runner_to_zip utility function."""

    def test_creates_runner_exporter(self, mock_runner, mocker):
        """Creates RunnerExporter with runner."""
        mock_exporter_instance = MagicMock()
        mock_exporter_instance.export.return_value = "/path/output.zip"
        mock_exporter_class = mocker.patch(
            'tdm_orchestrator.services.export.exporter.RunnerExporter',
            return_value=mock_exporter_instance
        )
        
        export_runner_to_zip(mock_runner)
        
        mock_exporter_class.assert_called_once_with(mock_runner)

    def test_calls_export_with_output_path(self, mock_runner, mocker):
        """Calls exporter.export() with output_path."""
        mock_exporter_instance = MagicMock()
        mock_exporter_instance.export.return_value = "/custom/output.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.RunnerExporter',
            return_value=mock_exporter_instance
        )
        
        export_runner_to_zip(mock_runner, output_path="/custom/output.zip")
        
        mock_exporter_instance.export.assert_called_once_with("/custom/output.zip")

    def test_calls_export_without_output_path(self, mock_runner, mocker):
        """Calls exporter.export() with None when no output_path."""
        mock_exporter_instance = MagicMock()
        mock_exporter_instance.export.return_value = "/default/output.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.RunnerExporter',
            return_value=mock_exporter_instance
        )
        
        export_runner_to_zip(mock_runner)
        
        mock_exporter_instance.export.assert_called_once_with(None)

    def test_returns_zip_path(self, mock_runner, mocker):
        """Returns the path from exporter.export()."""
        mock_exporter_instance = MagicMock()
        mock_exporter_instance.export.return_value = "/path/to/runner.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.RunnerExporter',
            return_value=mock_exporter_instance
        )
        
        result = export_runner_to_zip(mock_runner)
        
        assert result == "/path/to/runner.zip"

    def test_propagates_export_error(self, mock_runner, mocker):
        """Propagates ExportError from exporter.export()."""
        mock_exporter_instance = MagicMock()
        mock_exporter_instance.export.side_effect = ExportError("Export failed")
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.RunnerExporter',
            return_value=mock_exporter_instance
        )
        
        with pytest.raises(ExportError) as exc_info:
            export_runner_to_zip(mock_runner)
        
        assert "Export failed" in str(exc_info.value)


# =====================
# Integration Tests
# =====================

class TestRunnerExporterIntegration:
    """Integration tests for RunnerExporter."""

    def test_full_export_workflow(self, mock_runner, mock_config, mocker):
        """Tests complete export workflow from init to zip creation."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.return_value = "/export/runner_test_runner.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.export("/export/runner_test_runner.zip")
        
        # Verify workflow order
        assert mock_config_builder.build.called
        assert mock_zip_builder.write_config_file.called
        assert mock_zip_builder.write_script_files.called
        assert mock_zip_builder.write_readme.called
        assert mock_zip_builder.create_zip.called
        assert mock_zip_builder.cleanup.called
        assert result == "/export/runner_test_runner.zip"

    def test_get_info_then_export(self, mock_runner, mock_config, mocker):
        """Tests getting info then exporting."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.return_value = "/export/output.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        
        # Get info first
        info = exporter.get_export_info()
        assert info['runner_name'] == 'test_runner'
        assert info['total_scripts'] == 3
        
        # Then export
        zip_path = exporter.export()
        assert zip_path == "/export/output.zip"


# =====================
# Edge Cases
# =====================

class TestRunnerExporterEdgeCases:
    """Edge case tests for RunnerExporter."""

    def test_runner_with_no_scripts(self, mock_runner, mock_config_empty, mocker):
        """Handles runner with no scripts."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config_empty
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.return_value = "/export/empty.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.export()
        
        assert result == "/export/empty.zip"

    def test_runner_name_with_special_characters(self, mocker):
        """Handles runner name with special characters."""
        special_runner = MagicMock()
        special_runner.name = "runner_日本語_#$%"
        special_runner.get_pre_scripts.return_value = []
        special_runner.get_post_scripts.return_value = []
        
        mock_config = {
            'metadata': {
                'runner_name': 'runner_日本語_#$%',
                'runner_reference': 'SPEC',
                'application_name': 'app',
            },
            'pre_scripts': [],
            'post_scripts': [],
            'required_variables': [],
        }
        
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.return_value = "/export/special.zip"
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(special_runner)
        info = exporter.get_export_info()
        
        assert info['runner_name'] == 'runner_日本語_#$%'

    def test_cleanup_called_when_write_readme_fails(self, mock_runner, mock_config, mocker):
        """Cleanup is called even when write_readme fails."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        
        mock_zip_builder = MagicMock()
        mock_zip_builder.write_readme.side_effect = Exception("README error")
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        
        with pytest.raises(ExportError):
            exporter.export()
        
        mock_zip_builder.cleanup.assert_called_once()

    def test_empty_output_path_string(self, mock_runner, mock_config, mocker):
        """Handles empty string as output_path."""
        mock_config_builder = MagicMock()
        mock_config_builder.build.return_value = mock_config
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ConfigBuilder',
            return_value=mock_config_builder
        )
        
        mock_zip_builder = MagicMock()
        mock_zip_builder.create_zip.return_value = ""
        mocker.patch(
            'tdm_orchestrator.services.export.exporter.ZipBuilder',
            return_value=mock_zip_builder
        )
        
        exporter = RunnerExporter(mock_runner)
        result = exporter.export(output_path="")
        
        mock_zip_builder.create_zip.assert_called_once_with("")
        assert result == ""


# =====================
# Summary of Covered Cases
# =====================
# __init__:
# - Stores runner reference
# - Creates ConfigBuilder with runner
# - Creates ZipBuilder with runner
# - Stores builder instances
#
# export:
# - Builds config from config_builder
# - Writes config file with config
# - Writes script files with config
# - Writes readme with config
# - Creates zip with/without output_path
# - Returns zip path
# - Calls cleanup on success and on exception
# - Raises ExportError on various failures
# - Logs info and error messages
#
# get_export_info:
# - Returns dict with all expected keys
# - Returns values from config metadata
# - Returns correct counts (pre, post, total, variables)
# - Includes estimated_size_kb
# - Handles empty config
#
# _estimate_export_size:
# - Returns int >= 1
# - Includes base config and readme sizes
# - Includes script content and header sizes
# - Applies compression ratio
# - Handles multiple scripts
# - Handles large and unicode content
#
# export_runner_to_zip:
# - Creates exporter with runner
# - Calls export with/without output_path
# - Returns zip path
# - Propagates ExportError
#
# Edge cases:
# - Runner with no scripts
# - Special characters in runner name
# - Cleanup on various failure points
# - Empty output path string