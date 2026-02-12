"""
Tests for ZipBuilder - ZIP file construction for runner export.

Covers:
- __init__: Initialization with runner
- _create_temp_directory: Temporary directory creation
- cleanup: Temp directory removal
- write_config_file: config.json creation
- write_script_files: SQL files writing
- _write_single_script: Individual script writing
- _get_script_filename: Filename generation
- _generate_sql_header: SQL header generation
- write_readme: README.md creation
- _generate_readme_content: README content generation
- create_zip: Final ZIP creation
"""

import json
import os
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, patch, mock_open
from zipfile import ZipFile

import pytest

from .zip_builder import ZipBuilder
from ..exceptions import ZipCreationError


# =====================
# Fixtures
# =====================

@pytest.fixture
def mock_runner():
    """Create a mock runner with basic attributes."""
    runner = MagicMock()
    runner.name = "test_runner"
    runner.reference = "TEST_REF_001"
    runner.get_pre_scripts.return_value = []
    runner.get_post_scripts.return_value = []
    return runner


@pytest.fixture
def mock_script():
    """Create a mock script."""
    script = MagicMock()
    script.name = "test_script"
    script.reference = "SCRIPT_REF"
    script.content = "SELECT * FROM users;"
    script.description = "Test script description"
    script.datasource = MagicMock()
    script.datasource.name = "test_datasource"
    script.extract_variables.return_value = ["VAR1", "VAR2"]
    return script


@pytest.fixture
def mock_script_no_datasource():
    """Create a mock script without datasource."""
    script = MagicMock()
    script.name = "script_no_ds"
    script.reference = "NO_DS_REF"
    script.content = "SELECT 1;"
    script.description = None
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
def sample_config():
    """Create a sample configuration dictionary."""
    return {
        'metadata': {
            'runner_name': 'test_runner',
            'runner_reference': 'TEST_REF',
            'application_name': 'test_app',
            'export_date': '2024-01-15 10:30:00',
            'runner_description': 'Test runner description',
        },
        'execution_settings': {
            'stop_on_error': True,
            'verbose_logging': False,
        },
        'pre_scripts': [
            {'order': 1, 'file': 'pre_001_script1.sql', 'name': 'script1'},
            {'order': 2, 'file': 'pre_002_script2.sql', 'name': 'script2'},
        ],
        'post_scripts': [
            {'order': 1, 'file': 'post_001_script3.sql', 'name': 'script3'},
        ],
        'required_variables': ['VAR1', 'VAR2', 'VAR3'],
    }


@pytest.fixture
def sample_config_empty():
    """Create a sample configuration with empty scripts and variables."""
    return {
        'metadata': {
            'runner_name': 'empty_runner',
            'runner_reference': 'EMPTY_REF',
            'application_name': 'empty_app',
            'export_date': '2024-01-15 10:30:00',
            'runner_description': 'Empty runner',
        },
        'execution_settings': {
            'stop_on_error': False,
            'verbose_logging': True,
        },
        'pre_scripts': [],
        'post_scripts': [],
        'required_variables': [],
    }


@pytest.fixture
def zip_builder(mock_runner):
    """Create a ZipBuilder instance."""
    return ZipBuilder(mock_runner)


@pytest.fixture
def zip_builder_with_temp_dir(mock_runner, tmp_path):
    """Create a ZipBuilder instance with temp_dir set."""
    builder = ZipBuilder(mock_runner)
    builder.temp_dir = str(tmp_path)
    return builder


# =====================
# __init__ Tests
# =====================

class TestZipBuilderInit:
    """Tests for ZipBuilder.__init__ method."""

    def test_stores_runner_reference(self, mock_runner):
        """Stores runner reference in instance."""
        builder = ZipBuilder(mock_runner)
        
        assert builder.runner == mock_runner

    def test_initializes_temp_dir_to_none(self, mock_runner):
        """Initializes temp_dir to None."""
        builder = ZipBuilder(mock_runner)
        
        assert builder.temp_dir is None


# =====================
# _create_temp_directory Tests
# =====================

class TestCreateTempDirectory:
    """Tests for ZipBuilder._create_temp_directory method."""

    def test_creates_directory_in_tempdir(self, zip_builder, mocker):
        """Creates directory in system temp directory."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mock_makedirs = mocker.patch('os.makedirs')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "20240115_103000"
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_reference',
            return_value="TEST_REF_001"
        )
        
        result = zip_builder._create_temp_directory()
        
        assert tempfile.gettempdir() in result
        mock_makedirs.assert_called_once()

    def test_uses_sanitized_runner_reference(self, zip_builder, mocker):
        """Uses sanitized runner reference in directory name."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch('os.makedirs')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "20240115"
        mock_sanitize = mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_reference',
            return_value="SANITIZED_REF"
        )
        
        result = zip_builder._create_temp_directory()
        
        mock_sanitize.assert_called_once_with(zip_builder.runner.reference)
        assert "SANITIZED_REF" in result

    def test_uses_timestamp_in_name(self, zip_builder, mocker):
        """Uses timestamp in directory name."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch('os.makedirs')
        mock_datetime = mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        )
        mock_datetime.now.return_value.strftime.return_value = "20240115_103045"
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_reference',
            return_value="REF"
        )
        
        result = zip_builder._create_temp_directory()
        
        assert "20240115_103045" in result

    def test_sets_temp_dir_attribute(self, zip_builder, mocker):
        """Sets temp_dir attribute on instance."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch('os.makedirs')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "20240115"
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_reference',
            return_value="REF"
        )
        
        result = zip_builder._create_temp_directory()
        
        assert zip_builder.temp_dir == result
        assert zip_builder.temp_dir is not None

    def test_returns_temp_dir_path(self, zip_builder, mocker):
        """Returns the temp_dir path."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch('os.makedirs')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "20240115"
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_reference',
            return_value="REF"
        )
        
        result = zip_builder._create_temp_directory()
        
        assert isinstance(result, str)
        assert "runner_export_REF_20240115" in result

    def test_creates_directory_with_exist_ok(self, zip_builder, mocker):
        """Calls makedirs with exist_ok=True."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mock_makedirs = mocker.patch('os.makedirs')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "20240115"
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_reference',
            return_value="REF"
        )
        
        zip_builder._create_temp_directory()
        
        mock_makedirs.assert_called_once()
        call_kwargs = mock_makedirs.call_args
        assert call_kwargs[1]['exist_ok'] is True

    def test_logs_info_message(self, zip_builder, mocker):
        """Logs info message with temp directory path."""
        mock_logger = mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.logger'
        )
        mocker.patch('os.makedirs')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "20240115"
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_reference',
            return_value="REF"
        )
        
        zip_builder._create_temp_directory()
        
        mock_logger.info.assert_called_once()
        assert "Répertoire temporaire" in mock_logger.info.call_args[0][0]


# =====================
# cleanup Tests
# =====================

class TestCleanup:
    """Tests for ZipBuilder.cleanup method."""

    def test_removes_temp_dir_when_exists(self, zip_builder, mocker, tmp_path):
        """Removes temp_dir when it exists."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        zip_builder.temp_dir = str(tmp_path)
        
        # Create a file in the directory
        (tmp_path / "test.txt").write_text("test")
        
        zip_builder.cleanup()
        
        assert not tmp_path.exists()

    def test_does_nothing_when_temp_dir_is_none(self, zip_builder, mocker):
        """Does nothing when temp_dir is None."""
        mock_rmtree = mocker.patch('shutil.rmtree')
        zip_builder.temp_dir = None
        
        zip_builder.cleanup()
        
        mock_rmtree.assert_not_called()

    def test_does_nothing_when_temp_dir_not_exists(self, zip_builder, mocker):
        """Does nothing when temp_dir doesn't exist."""
        mock_rmtree = mocker.patch('shutil.rmtree')
        zip_builder.temp_dir = "/nonexistent/path/that/does/not/exist"
        
        zip_builder.cleanup()
        
        mock_rmtree.assert_not_called()

    def test_handles_exception_gracefully(self, zip_builder, mocker, tmp_path):
        """Handles exception during removal gracefully."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch('shutil.rmtree', side_effect=PermissionError("Access denied"))
        zip_builder.temp_dir = str(tmp_path)
        
        # Should not raise
        zip_builder.cleanup()

    def test_logs_warning_on_failure(self, zip_builder, mocker, tmp_path):
        """Logs warning on cleanup failure."""
        mock_logger = mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.logger'
        )
        mocker.patch('shutil.rmtree', side_effect=PermissionError("Access denied"))
        zip_builder.temp_dir = str(tmp_path)
        
        zip_builder.cleanup()
        
        mock_logger.warning.assert_called_once()
        assert "Échec nettoyage" in mock_logger.warning.call_args[0][0]

    def test_logs_info_on_success(self, zip_builder, mocker, tmp_path):
        """Logs info on successful cleanup."""
        mock_logger = mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.logger'
        )
        zip_builder.temp_dir = str(tmp_path)
        
        zip_builder.cleanup()
        
        mock_logger.info.assert_called_once()
        assert "Nettoyage" in mock_logger.info.call_args[0][0]


# =====================
# write_config_file Tests
# =====================

class TestWriteConfigFile:
    """Tests for ZipBuilder.write_config_file method."""

    def test_creates_temp_dir_if_not_exists(self, zip_builder, mocker, tmp_path):
        """Creates temp_dir if not already created."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        
        def set_temp_dir():
            zip_builder.temp_dir = str(tmp_path)
            return str(tmp_path)
        
        mock_create = mocker.patch.object(
            zip_builder, '_create_temp_directory', side_effect=set_temp_dir
        )
        zip_builder.temp_dir = None
        
        zip_builder.write_config_file({'key': 'value'})
        
        mock_create.assert_called_once()

    def test_skips_temp_dir_creation_if_exists(
        self, zip_builder_with_temp_dir, mocker
    ):
        """Skips temp_dir creation if already exists."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mock_create = mocker.patch.object(
            zip_builder_with_temp_dir, '_create_temp_directory'
        )
        
        zip_builder_with_temp_dir.write_config_file({'key': 'value'})
        
        mock_create.assert_not_called()

    def test_writes_config_json_with_correct_content(
        self, zip_builder_with_temp_dir, sample_config, mocker
    ):
        """Writes config.json with correct JSON content."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        
        zip_builder_with_temp_dir.write_config_file(sample_config)
        
        config_path = os.path.join(
            zip_builder_with_temp_dir.temp_dir, 'config.json'
        )
        with open(config_path, 'r', encoding='utf-8') as f:
            written_config = json.load(f)
        
        assert written_config == sample_config

    def test_returns_config_path(self, zip_builder_with_temp_dir, mocker):
        """Returns the path to config.json."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        
        result = zip_builder_with_temp_dir.write_config_file({'key': 'value'})
        
        expected_path = os.path.join(
            zip_builder_with_temp_dir.temp_dir, 'config.json'
        )
        assert result == expected_path

    def test_uses_utf8_encoding(self, zip_builder_with_temp_dir, mocker):
        """Uses UTF-8 encoding for writing."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        config_with_unicode = {'name': '日本語テスト', 'emoji': '🚀'}
        
        zip_builder_with_temp_dir.write_config_file(config_with_unicode)
        
        config_path = os.path.join(
            zip_builder_with_temp_dir.temp_dir, 'config.json'
        )
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert '日本語テスト' in content
        assert '🚀' in content

    def test_handles_unicode_in_config(self, zip_builder_with_temp_dir, mocker):
        """Handles unicode characters in config values."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        unicode_config = {
            'metadata': {
                'runner_name': 'Téléchargement données',
                'description': 'Script pour données françaises',
            }
        }
        
        zip_builder_with_temp_dir.write_config_file(unicode_config)
        
        config_path = os.path.join(
            zip_builder_with_temp_dir.temp_dir, 'config.json'
        )
        with open(config_path, 'r', encoding='utf-8') as f:
            written_config = json.load(f)
        
        assert written_config['metadata']['runner_name'] == 'Téléchargement données'

    def test_logs_info_message(self, zip_builder_with_temp_dir, mocker):
        """Logs info message when config is created."""
        mock_logger = mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.logger'
        )
        
        zip_builder_with_temp_dir.write_config_file({'key': 'value'})
        
        mock_logger.info.assert_called_once_with("config.json créé")

    def test_writes_with_indent(self, zip_builder_with_temp_dir, mocker):
        """Writes JSON with indentation for readability."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        
        zip_builder_with_temp_dir.write_config_file({'key': 'value'})
        
        config_path = os.path.join(
            zip_builder_with_temp_dir.temp_dir, 'config.json'
        )
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Indented JSON should have newlines
        assert '\n' in content


# =====================
# write_script_files Tests
# =====================

class TestWriteScriptFiles:
    """Tests for ZipBuilder.write_script_files method."""

    def test_creates_temp_dir_if_not_exists(
        self, zip_builder, sample_config, mocker, tmp_path
    ):
        """Creates temp_dir if not already created."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mock_create = mocker.patch.object(
            zip_builder, '_create_temp_directory', return_value=str(tmp_path)
        )
        zip_builder.temp_dir = None
        
        zip_builder.write_script_files(sample_config)
        
        mock_create.assert_called_once()

    def test_writes_pre_scripts(
        self, zip_builder_with_temp_dir, mock_step, sample_config, mocker
    ):
        """Writes PRE scripts from runner."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='test_script'
        )
        zip_builder_with_temp_dir.runner.get_pre_scripts.return_value = [mock_step]
        zip_builder_with_temp_dir.runner.get_post_scripts.return_value = []
        
        zip_builder_with_temp_dir.write_script_files(sample_config)
        
        # Check file was created
        expected_file = os.path.join(
            zip_builder_with_temp_dir.temp_dir, 'pre_001_test_script.sql'
        )
        assert os.path.exists(expected_file)

    def test_writes_post_scripts(
        self, zip_builder_with_temp_dir, mock_step, sample_config, mocker
    ):
        """Writes POST scripts from runner."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='test_script'
        )
        zip_builder_with_temp_dir.runner.get_pre_scripts.return_value = []
        zip_builder_with_temp_dir.runner.get_post_scripts.return_value = [mock_step]
        
        zip_builder_with_temp_dir.write_script_files(sample_config)
        
        expected_file = os.path.join(
            zip_builder_with_temp_dir.temp_dir, 'post_001_test_script.sql'
        )
        assert os.path.exists(expected_file)

    def test_writes_correct_number_of_files(
        self, zip_builder_with_temp_dir, mock_step, sample_config, mocker
    ):
        """Writes correct number of script files."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='script'
        )
        
        step1 = MagicMock()
        step1.script = mock_step.script
        step1.order = 1
        step2 = MagicMock()
        step2.script = mock_step.script
        step2.order = 2
        step3 = MagicMock()
        step3.script = mock_step.script
        step3.order = 1
        
        zip_builder_with_temp_dir.runner.get_pre_scripts.return_value = [step1, step2]
        zip_builder_with_temp_dir.runner.get_post_scripts.return_value = [step3]
        
        zip_builder_with_temp_dir.write_script_files(sample_config)
        
        sql_files = [f for f in os.listdir(zip_builder_with_temp_dir.temp_dir) 
                     if f.endswith('.sql')]
        assert len(sql_files) == 3

    def test_logs_info_with_count(
        self, zip_builder_with_temp_dir, mock_step, sample_config, mocker
    ):
        """Logs info message with script count."""
        mock_logger = mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.logger'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='script'
        )
        zip_builder_with_temp_dir.runner.get_pre_scripts.return_value = [mock_step]
        zip_builder_with_temp_dir.runner.get_post_scripts.return_value = []
        
        zip_builder_with_temp_dir.write_script_files(sample_config)
        
        mock_logger.info.assert_called_once()
        assert "1 fichier(s) SQL créé(s)" in mock_logger.info.call_args[0][0]

    def test_handles_no_scripts(
        self, zip_builder_with_temp_dir, sample_config, mocker
    ):
        """Handles case with no scripts."""
        mock_logger = mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.logger'
        )
        zip_builder_with_temp_dir.runner.get_pre_scripts.return_value = []
        zip_builder_with_temp_dir.runner.get_post_scripts.return_value = []
        
        zip_builder_with_temp_dir.write_script_files(sample_config)
        
        mock_logger.info.assert_called_once()
        assert "0 fichier(s) SQL créé(s)" in mock_logger.info.call_args[0][0]


# =====================
# _write_single_script Tests
# =====================

class TestWriteSingleScript:
    """Tests for ZipBuilder._write_single_script method."""

    def test_writes_file_with_header_and_content(
        self, zip_builder_with_temp_dir, mock_step, mocker
    ):
        """Writes file containing header and script content."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='test_script'
        )
        
        zip_builder_with_temp_dir._write_single_script(mock_step, 'pre')
        
        expected_file = os.path.join(
            zip_builder_with_temp_dir.temp_dir, 'pre_001_test_script.sql'
        )
        with open(expected_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "SELECT * FROM users;" in content
        assert "-- Script :" in content

    def test_uses_correct_filename_format(
        self, zip_builder_with_temp_dir, mock_step, mocker
    ):
        """Uses correct filename format."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='my_script'
        )
        mock_step.order = 5
        
        zip_builder_with_temp_dir._write_single_script(mock_step, 'post')
        
        expected_file = os.path.join(
            zip_builder_with_temp_dir.temp_dir, 'post_005_my_script.sql'
        )
        assert os.path.exists(expected_file)

    def test_writes_with_utf8_encoding(
        self, zip_builder_with_temp_dir, mock_step, mocker
    ):
        """Writes file with UTF-8 encoding."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='script'
        )
        mock_step.script.content = "SELECT '日本語データ' FROM テーブル;"
        
        zip_builder_with_temp_dir._write_single_script(mock_step, 'pre')
        
        expected_file = os.path.join(
            zip_builder_with_temp_dir.temp_dir, 'pre_001_script.sql'
        )
        with open(expected_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert '日本語データ' in content

    def test_logs_debug_message(
        self, zip_builder_with_temp_dir, mock_step, mocker
    ):
        """Logs debug message with filename."""
        mock_logger = mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.logger'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='script'
        )
        
        zip_builder_with_temp_dir._write_single_script(mock_step, 'pre')
        
        mock_logger.debug.assert_called_once()
        assert "Script écrit" in mock_logger.debug.call_args[0][0]


# =====================
# _get_script_filename Tests
# =====================

class TestGetScriptFilename:
    """Tests for ZipBuilder._get_script_filename method."""

    def test_returns_correct_format(self, zip_builder, mock_script, mocker):
        """Returns correct filename format: {type}_{order:03d}_{name}.sql"""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='my_script'
        )
        
        result = zip_builder._get_script_filename(mock_script, 1, 'pre')
        
        assert result == 'pre_001_my_script.sql'

    def test_pads_order_with_zeros(self, zip_builder, mock_script, mocker):
        """Pads order number with leading zeros."""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='script'
        )
        
        result = zip_builder._get_script_filename(mock_script, 5, 'post')
        
        assert result == 'post_005_script.sql'

    def test_handles_large_order_numbers(self, zip_builder, mock_script, mocker):
        """Handles order numbers larger than 999."""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='script'
        )
        
        result = zip_builder._get_script_filename(mock_script, 1234, 'pre')
        
        assert result == 'pre_1234_script.sql'

    def test_sanitizes_script_name(self, zip_builder, mock_script, mocker):
        """Sanitizes script name using sanitize_filename."""
        mock_sanitize = mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='sanitized_name'
        )
        
        result = zip_builder._get_script_filename(mock_script, 1, 'pre')
        
        mock_sanitize.assert_called_once_with(mock_script.name)
        assert 'sanitized_name' in result

    def test_handles_special_characters_via_sanitize(
        self, zip_builder, mock_script, mocker
    ):
        """Handles special characters through sanitize_filename."""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='script_with_spaces'
        )
        mock_script.name = "script with spaces & special!"
        
        result = zip_builder._get_script_filename(mock_script, 1, 'pre')
        
        assert result == 'pre_001_script_with_spaces.sql'


# =====================
# _generate_sql_header Tests
# =====================

class TestGenerateSqlHeader:
    """Tests for ZipBuilder._generate_sql_header method."""

    def test_contains_script_name(self, zip_builder, mock_script, mocker):
        """Header contains script name."""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "2024-01-15"
        
        result = zip_builder._generate_sql_header(mock_script, 1, 'PRE')
        
        assert f"Script : {mock_script.name}" in result

    def test_contains_script_reference(self, zip_builder, mock_script, mocker):
        """Header contains script reference."""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "2024-01-15"
        
        result = zip_builder._generate_sql_header(mock_script, 1, 'PRE')
        
        assert f"Référence : {mock_script.reference}" in result

    def test_contains_step_type_and_order(self, zip_builder, mock_script, mocker):
        """Header contains step type and order."""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "2024-01-15"
        
        result = zip_builder._generate_sql_header(mock_script, 5, 'POST')
        
        assert "Type : POST-Processing (Ordre: 5)" in result

    def test_contains_description(self, zip_builder, mock_script, mocker):
        """Header contains script description."""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "2024-01-15"
        mock_script.description = "My custom description"
        
        result = zip_builder._generate_sql_header(mock_script, 1, 'PRE')
        
        assert "Description : My custom description" in result

    def test_uses_default_description_when_none(
        self, zip_builder, mock_script_no_datasource, mocker
    ):
        """Uses 'Aucune description' when description is None."""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "2024-01-15"
        
        result = zip_builder._generate_sql_header(mock_script_no_datasource, 1, 'PRE')
        
        assert "Description : Aucune description" in result

    def test_contains_datasource_name(self, zip_builder, mock_script, mocker):
        """Header contains datasource name."""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "2024-01-15"
        
        result = zip_builder._generate_sql_header(mock_script, 1, 'PRE')
        
        assert "Source de données : test_datasource" in result

    def test_uses_default_datasource_when_none(
        self, zip_builder, mock_script_no_datasource, mocker
    ):
        """Uses 'Non spécifiée' when datasource is None."""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "2024-01-15"
        
        result = zip_builder._generate_sql_header(mock_script_no_datasource, 1, 'PRE')
        
        assert "Source de données : Non spécifiée" in result

    def test_contains_variables(self, zip_builder, mock_script, mocker):
        """Header contains required variables."""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "2024-01-15"
        
        result = zip_builder._generate_sql_header(mock_script, 1, 'PRE')
        
        assert "Variables requises : VAR1, VAR2" in result

    def test_uses_aucune_when_no_variables(
        self, zip_builder, mock_script_no_datasource, mocker
    ):
        """Uses 'Aucune' when no variables."""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "2024-01-15"
        
        result = zip_builder._generate_sql_header(mock_script_no_datasource, 1, 'PRE')
        
        assert "Variables requises : Aucune" in result

    def test_contains_export_date(self, zip_builder, mock_script, mocker):
        """Header contains export date."""
        mock_datetime = mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        )
        mock_datetime.now.return_value.strftime.return_value = "2024-01-15 10:30:00"
        
        result = zip_builder._generate_sql_header(mock_script, 1, 'PRE')
        
        assert "Date d'export : 2024-01-15 10:30:00" in result

    def test_header_format_has_sql_comments(self, zip_builder, mock_script, mocker):
        """Header uses SQL comment format."""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "2024-01-15"
        
        result = zip_builder._generate_sql_header(mock_script, 1, 'PRE')
        
        assert result.startswith("--")
        assert "-- ==" in result


# =====================
# write_readme Tests
# =====================

class TestWriteReadme:
    """Tests for ZipBuilder.write_readme method."""

    def test_creates_temp_dir_if_not_exists(
        self, zip_builder, sample_config, mocker, tmp_path
    ):
        """Creates temp_dir if not already created."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        
        def set_temp_dir():
            zip_builder.temp_dir = str(tmp_path)
            return str(tmp_path)
        
        mock_create = mocker.patch.object(
            zip_builder, '_create_temp_directory', side_effect=set_temp_dir
        )
        zip_builder.temp_dir = None
        
        zip_builder.write_readme(sample_config)
        
        mock_create.assert_called_once()

    def test_writes_readme_md(
        self, zip_builder_with_temp_dir, sample_config, mocker
    ):
        """Writes README.md file."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        
        zip_builder_with_temp_dir.write_readme(sample_config)
        
        readme_path = os.path.join(
            zip_builder_with_temp_dir.temp_dir, 'README.md'
        )
        assert os.path.exists(readme_path)

    def test_readme_contains_runner_name(
        self, zip_builder_with_temp_dir, sample_config, mocker
    ):
        """README contains runner name."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        
        zip_builder_with_temp_dir.write_readme(sample_config)
        
        readme_path = os.path.join(
            zip_builder_with_temp_dir.temp_dir, 'README.md'
        )
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'test_runner' in content

    def test_logs_info_message(
        self, zip_builder_with_temp_dir, sample_config, mocker
    ):
        """Logs info message when README is created."""
        mock_logger = mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.logger'
        )
        
        zip_builder_with_temp_dir.write_readme(sample_config)
        
        mock_logger.info.assert_called_once_with("README.md créé")


# =====================
# _generate_readme_content Tests
# =====================

class TestGenerateReadmeContent:
    """Tests for ZipBuilder._generate_readme_content method."""

    def test_contains_runner_name_in_title(self, zip_builder, sample_config):
        """Contains runner name in title."""
        result = zip_builder._generate_readme_content(sample_config)
        
        assert "# Runner Export: test_runner" in result

    def test_contains_runner_reference(self, zip_builder, sample_config):
        """Contains runner reference."""
        result = zip_builder._generate_readme_content(sample_config)
        
        assert "**Référence** : TEST_REF" in result

    def test_contains_application_name(self, zip_builder, sample_config):
        """Contains application name."""
        result = zip_builder._generate_readme_content(sample_config)
        
        assert "**Application** : test_app" in result

    def test_contains_export_date(self, zip_builder, sample_config):
        """Contains export date."""
        result = zip_builder._generate_readme_content(sample_config)
        
        assert "**Date d'export** : 2024-01-15 10:30:00" in result

    def test_contains_description(self, zip_builder, sample_config):
        """Contains runner description."""
        result = zip_builder._generate_readme_content(sample_config)
        
        assert "Test runner description" in result

    def test_contains_stop_on_error_yes(self, zip_builder, sample_config):
        """Contains stop_on_error setting (Oui)."""
        result = zip_builder._generate_readme_content(sample_config)
        
        assert "**Arrêt sur erreur** : Oui" in result

    def test_contains_stop_on_error_non(self, zip_builder, sample_config_empty):
        """Contains stop_on_error setting (Non)."""
        result = zip_builder._generate_readme_content(sample_config_empty)
        
        assert "**Arrêt sur erreur** : Non" in result

    def test_contains_verbose_logging_non(self, zip_builder, sample_config):
        """Contains verbose_logging setting (Non)."""
        result = zip_builder._generate_readme_content(sample_config)
        
        assert "**Logs verbeux** : Non" in result

    def test_contains_verbose_logging_oui(self, zip_builder, sample_config_empty):
        """Contains verbose_logging setting (Oui)."""
        result = zip_builder._generate_readme_content(sample_config_empty)
        
        assert "**Logs verbeux** : Oui" in result

    def test_lists_pre_scripts(self, zip_builder, sample_config):
        """Lists pre scripts with order and filename."""
        result = zip_builder._generate_readme_content(sample_config)
        
        assert "Pré-traitement (2 script(s))" in result
        assert "**1.** `pre_001_script1.sql`" in result
        assert "**2.** `pre_002_script2.sql`" in result

    def test_lists_post_scripts(self, zip_builder, sample_config):
        """Lists post scripts with order and filename."""
        result = zip_builder._generate_readme_content(sample_config)
        
        assert "Post-traitement (1 script(s))" in result
        assert "**1.** `post_001_script3.sql`" in result

    def test_lists_required_variables(self, zip_builder, sample_config):
        """Lists required variables."""
        result = zip_builder._generate_readme_content(sample_config)
        
        assert "## 🔧 Variables requises" in result
        assert "- `${VAR1}`" in result
        assert "- `${VAR2}`" in result
        assert "- `${VAR3}`" in result

    def test_handles_empty_scripts_lists(self, zip_builder, sample_config_empty):
        """Handles empty scripts lists."""
        result = zip_builder._generate_readme_content(sample_config_empty)
        
        assert "Pré-traitement (0 script(s))" in result
        assert "Post-traitement (0 script(s))" in result

    def test_handles_empty_variables(self, zip_builder, sample_config_empty):
        """Does not show variables section when empty."""
        result = zip_builder._generate_readme_content(sample_config_empty)
        
        assert "## 🔧 Variables requises" not in result

    def test_contains_footer(self, zip_builder, sample_config):
        """Contains footer with generator name."""
        result = zip_builder._generate_readme_content(sample_config)
        
        assert "*Généré par TDM SQL Orchestrator*" in result


# =====================
# create_zip Tests
# =====================

class TestCreateZip:
    """Tests for ZipBuilder.create_zip method."""

    def test_raises_error_when_no_temp_dir(self, zip_builder):
        """Raises ZipCreationError when temp_dir is None."""
        zip_builder.temp_dir = None
        
        with pytest.raises(ZipCreationError) as exc_info:
            zip_builder.create_zip()
        
        assert "Aucun fichier à compresser" in str(exc_info.value)

    def test_creates_zip_at_output_path(
        self, zip_builder_with_temp_dir, mocker, tmp_path
    ):
        """Creates ZIP at specified output_path."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        output_path = str(tmp_path / "output.zip")
        
        # Create a file in temp_dir
        test_file = os.path.join(zip_builder_with_temp_dir.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        result = zip_builder_with_temp_dir.create_zip(output_path)
        
        assert result == output_path
        assert os.path.exists(output_path)

    def test_generates_default_path_when_none(
        self, zip_builder_with_temp_dir, mocker
    ):
        """Generates default path in temp directory when output_path is None."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "20240115_103000"
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='TEST_REF_001'
        )
        
        # Create a file in temp_dir
        test_file = os.path.join(zip_builder_with_temp_dir.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        result = zip_builder_with_temp_dir.create_zip()
        
        assert tempfile.gettempdir() in result
        assert "runner_TEST_REF_001_20240115_103000.zip" in result
        # Cleanup
        if os.path.exists(result):
            os.remove(result)

    def test_contains_all_files_from_temp_dir(
        self, zip_builder_with_temp_dir, mocker, tmp_path
    ):
        """ZIP contains all files from temp_dir."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        output_path = str(tmp_path / "output.zip")
        
        # Create multiple files
        for name in ["file1.txt", "file2.sql", "config.json"]:
            filepath = os.path.join(zip_builder_with_temp_dir.temp_dir, name)
            with open(filepath, 'w') as f:
                f.write(f"content of {name}")
        
        zip_builder_with_temp_dir.create_zip(output_path)
        
        with ZipFile(output_path, 'r') as zipf:
            names = zipf.namelist()
        
        assert "file1.txt" in names
        assert "file2.sql" in names
        assert "config.json" in names

    def test_returns_zip_path(
        self, zip_builder_with_temp_dir, mocker, tmp_path
    ):
        """Returns the path to created ZIP."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        output_path = str(tmp_path / "my_export.zip")
        
        test_file = os.path.join(zip_builder_with_temp_dir.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        result = zip_builder_with_temp_dir.create_zip(output_path)
        
        assert result == output_path

    def test_raises_error_on_write_failure(
        self, zip_builder_with_temp_dir, mocker
    ):
        """Raises ZipCreationError when ZIP creation fails."""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.ZipFile',
            side_effect=IOError("Disk full")
        )
        
        test_file = os.path.join(zip_builder_with_temp_dir.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        with pytest.raises(ZipCreationError) as exc_info:
            zip_builder_with_temp_dir.create_zip("/some/path.zip")
        
        assert "Erreur création ZIP" in str(exc_info.value)
        assert "Disk full" in str(exc_info.value)

    def test_logs_info_with_size(
        self, zip_builder_with_temp_dir, mocker, tmp_path
    ):
        """Logs info message with ZIP path and size."""
        mock_logger = mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.logger'
        )
        output_path = str(tmp_path / "output.zip")
        
        test_file = os.path.join(zip_builder_with_temp_dir.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        zip_builder_with_temp_dir.create_zip(output_path)
        
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "ZIP créé" in log_message
        assert output_path in log_message
        assert "octets" in log_message

    def test_uses_deflate_compression(
        self, zip_builder_with_temp_dir, mocker, tmp_path
    ):
        """Uses ZIP_DEFLATED compression."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        output_path = str(tmp_path / "output.zip")
        
        test_file = os.path.join(zip_builder_with_temp_dir.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content " * 100)  # Repeated content compresses well
        
        zip_builder_with_temp_dir.create_zip(output_path)
        
        with ZipFile(output_path, 'r') as zipf:
            info = zipf.getinfo("test.txt")
            # ZIP_DEFLATED = 8
            assert info.compress_type == 8

    def test_preserves_relative_paths(
        self, mock_runner, mocker
    ):
        """Preserves relative paths in ZIP (no absolute paths)."""
        import tempfile
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        
        # Create separate directories for temp_dir and output
        with tempfile.TemporaryDirectory() as temp_dir, \
             tempfile.TemporaryDirectory() as output_dir:
            builder = ZipBuilder(mock_runner)
            builder.temp_dir = temp_dir
            output_path = os.path.join(output_dir, "output.zip")
            
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test")
            
            builder.create_zip(output_path)
            
            with ZipFile(output_path, 'r') as zipf:
                names = zipf.namelist()
            
            # Should be relative path, not absolute
            assert names == ["test.txt"]


# =====================
# Integration Tests
# =====================

class TestZipBuilderIntegration:
    """Integration tests for ZipBuilder."""

    def test_full_workflow(self, mock_runner, mock_step, sample_config, tmp_path, mocker):
        """Tests complete workflow: create temp, write files, create zip, cleanup."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='script'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_reference',
            return_value='REF'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "2024-01-15"
        
        mock_runner.get_pre_scripts.return_value = [mock_step]
        mock_runner.get_post_scripts.return_value = []
        
        builder = ZipBuilder(mock_runner)
        output_path = str(tmp_path / "export.zip")
        
        # Write files
        builder.write_config_file(sample_config)
        builder.write_script_files(sample_config)
        builder.write_readme(sample_config)
        
        # Create ZIP
        result = builder.create_zip(output_path)
        
        # Verify
        assert os.path.exists(result)
        with ZipFile(result, 'r') as zipf:
            names = zipf.namelist()
            assert 'config.json' in names
            assert 'README.md' in names
            assert any('.sql' in name for name in names)
        
        # Cleanup
        temp_dir = builder.temp_dir
        builder.cleanup()
        assert not os.path.exists(temp_dir)

    def test_multiple_scripts_export(
        self, mock_runner, mock_script, sample_config, tmp_path, mocker
    ):
        """Tests export with multiple PRE and POST scripts."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='script'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_reference',
            return_value='REF'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "2024-01-15"
        
        # Create multiple steps
        steps_pre = []
        steps_post = []
        for i in range(3):
            step = MagicMock()
            step.script = mock_script
            step.order = i + 1
            steps_pre.append(step)
        for i in range(2):
            step = MagicMock()
            step.script = mock_script
            step.order = i + 1
            steps_post.append(step)
        
        mock_runner.get_pre_scripts.return_value = steps_pre
        mock_runner.get_post_scripts.return_value = steps_post
        
        builder = ZipBuilder(mock_runner)
        output_path = str(tmp_path / "export.zip")
        
        builder.write_config_file(sample_config)
        builder.write_script_files(sample_config)
        builder.write_readme(sample_config)
        result = builder.create_zip(output_path)
        
        with ZipFile(result, 'r') as zipf:
            sql_files = [n for n in zipf.namelist() if n.endswith('.sql')]
        
        assert len(sql_files) == 5  # 3 pre + 2 post
        
        builder.cleanup()


# =====================
# Edge Cases
# =====================

class TestZipBuilderEdgeCases:
    """Edge case tests for ZipBuilder."""

    def test_runner_with_special_characters_in_reference(self, mocker, tmp_path):
        """Handles runner reference with special characters."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_reference',
            return_value='REF_SPECIAL'
        )
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.datetime'
        ).now.return_value.strftime.return_value = "20240115"
        
        runner = MagicMock()
        runner.reference = "REF/WITH\\SPECIAL<>CHARS"
        runner.get_pre_scripts.return_value = []
        runner.get_post_scripts.return_value = []
        
        builder = ZipBuilder(runner)
        builder._create_temp_directory()
        
        assert "REF_SPECIAL" in builder.temp_dir
        
        builder.cleanup()

    def test_script_with_unicode_content(
        self, zip_builder_with_temp_dir, mocker
    ):
        """Handles script with unicode content."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='unicode_script'
        )
        
        script = MagicMock()
        script.name = "日本語スクリプト"
        script.reference = "UNICODE_REF"
        script.content = "SELECT * FROM テーブル WHERE 列 = '値';"
        script.description = "スクリプトの説明"
        script.datasource = MagicMock()
        script.datasource.name = "データソース"
        script.extract_variables.return_value = []
        
        step = MagicMock()
        step.script = script
        step.order = 1
        
        zip_builder_with_temp_dir._write_single_script(step, 'pre')
        
        filepath = os.path.join(
            zip_builder_with_temp_dir.temp_dir, 'pre_001_unicode_script.sql'
        )
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'テーブル' in content
        assert 'スクリプトの説明' in content

    def test_empty_script_content(
        self, zip_builder_with_temp_dir, mocker
    ):
        """Handles script with empty content."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='empty_script'
        )
        
        script = MagicMock()
        script.name = "empty_script"
        script.reference = "EMPTY"
        script.content = ""
        script.description = None
        script.datasource = None
        script.extract_variables.return_value = []
        
        step = MagicMock()
        step.script = script
        step.order = 1
        
        zip_builder_with_temp_dir._write_single_script(step, 'pre')
        
        filepath = os.path.join(
            zip_builder_with_temp_dir.temp_dir, 'pre_001_empty_script.sql'
        )
        assert os.path.exists(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # Should have header but no content after it
        assert "-- Script :" in content

    def test_very_long_script_name(self, zip_builder, mocker):
        """Handles very long script name."""
        mocker.patch(
            'tdm_orchestrator.services.export.zip_builder.sanitize_filename',
            return_value='x' * 200
        )
        
        script = MagicMock()
        script.name = 'a' * 500
        
        result = zip_builder._get_script_filename(script, 1, 'pre')
        
        assert result == 'pre_001_' + 'x' * 200 + '.sql'

    def test_cleanup_when_directory_already_removed(
        self, zip_builder, mocker
    ):
        """Handles cleanup when directory was already removed."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        
        zip_builder.temp_dir = "/nonexistent/already/removed/path"
        
        # Should not raise
        zip_builder.cleanup()

    def test_config_with_deeply_nested_structure(
        self, zip_builder_with_temp_dir, mocker
    ):
        """Handles config with deeply nested structure."""
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        
        nested_config = {
            'level1': {
                'level2': {
                    'level3': {
                        'level4': {
                            'value': 'deeply nested'
                        }
                    }
                }
            }
        }
        
        zip_builder_with_temp_dir.write_config_file(nested_config)
        
        config_path = os.path.join(
            zip_builder_with_temp_dir.temp_dir, 'config.json'
        )
        with open(config_path, 'r', encoding='utf-8') as f:
            written = json.load(f)
        
        assert written['level1']['level2']['level3']['level4']['value'] == 'deeply nested'

    def test_zip_with_empty_temp_directory(
        self, mock_runner, mocker
    ):
        """Creates ZIP even when temp directory is empty."""
        import tempfile
        mocker.patch('tdm_orchestrator.services.export.zip_builder.logger')
        
        # Create separate directories for temp_dir and output
        with tempfile.TemporaryDirectory() as temp_dir, \
             tempfile.TemporaryDirectory() as output_dir:
            builder = ZipBuilder(mock_runner)
            builder.temp_dir = temp_dir
            output_path = os.path.join(output_dir, "empty.zip")
            
            result = builder.create_zip(output_path)
            
            assert os.path.exists(result)
            with ZipFile(result, 'r') as zipf:
                assert zipf.namelist() == []


# =====================
# Summary of Covered Cases
# =====================
# __init__:
# - Stores runner reference
# - Initializes temp_dir to None
#
# _create_temp_directory:
# - Creates directory in tempdir
# - Uses sanitized runner reference
# - Uses timestamp in name
# - Sets temp_dir attribute
# - Returns temp_dir path
# - Creates with exist_ok=True
# - Logs info message
#
# cleanup:
# - Removes temp_dir when exists
# - Does nothing when temp_dir is None
# - Does nothing when temp_dir doesn't exist
# - Handles exception gracefully
# - Logs warning on failure
# - Logs info on success
#
# write_config_file:
# - Creates temp_dir if not exists
# - Skips creation if exists
# - Writes correct JSON content
# - Returns config path
# - Uses UTF-8 encoding
# - Handles unicode
# - Logs info message
# - Writes with indent
#
# write_script_files:
# - Creates temp_dir if not exists
# - Writes PRE scripts
# - Writes POST scripts
# - Writes correct number of files
# - Logs info with count
# - Handles no scripts
#
# _write_single_script:
# - Writes file with header and content
# - Uses correct filename format
# - Writes with UTF-8 encoding
# - Logs debug message
#
# _get_script_filename:
# - Returns correct format
# - Pads order with zeros
# - Handles large order numbers
# - Sanitizes script name
# - Handles special characters
#
# _generate_sql_header:
# - Contains script name and reference
# - Contains step type and order
# - Contains description or default
# - Contains datasource name or default
# - Contains variables or "Aucune"
# - Contains export date
# - Uses SQL comment format
#
# write_readme:
# - Creates temp_dir if not exists
# - Writes README.md
# - Contains runner name
# - Logs info message
#
# _generate_readme_content:
# - Contains runner name in title
# - Contains runner reference
# - Contains application name
# - Contains export date
# - Contains description
# - Contains stop_on_error setting
# - Contains verbose_logging setting
# - Lists pre scripts
# - Lists post scripts
# - Lists required variables
# - Handles empty scripts lists
# - Handles empty variables
# - Contains footer
#
# create_zip:
# - Raises error when no temp_dir
# - Creates ZIP at output_path
# - Generates default path when None
# - Contains all files from temp_dir
# - Returns ZIP path
# - Raises error on write failure
# - Logs info with size
# - Uses DEFLATE compression
# - Preserves relative paths
#
# Integration:
# - Full workflow
# - Multiple scripts export
#
# Edge cases:
# - Special characters in reference
# - Unicode content
# - Empty script content
# - Very long script name
# - Cleanup already removed directory
# - Deeply nested config
# - Empty temp directory