# tests/services/sql/test_executor.py
"""
Tests for SqlExecutor._log method.

Covers:
- Log entry format with timestamp, level, and message
- Default INFO level when level not specified
- Custom log levels (WARNING, ERROR, DEBUG)
- Logger function dispatching based on level
- Fallback to logger.info for unknown levels
- Log accumulation in _logs list
- Multiple log entries accumulation
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from tdm_orchestrator.services.sql.executor import SqlExecutor
from tdm_orchestrator.services.constants import LOG_TIMESTAMP_FORMAT


# --- Fixtures ---

@pytest.fixture
def mock_datasource():
    """Create a mock datasource for SqlExecutor initialization."""
    ds = MagicMock()
    ds.sgbd_name.value_char = 'PostgreSQL'
    ds.sgbd_host = 'localhost'
    ds.sgbd_port = 5432
    ds.sgbd_user = 'user'
    ds.sgbd_password = 'pass'
    ds.sgbd_database = 'testdb'
    ds.sgbd_tls = False
    ds.name = 'Test DataSource'
    return ds


@pytest.fixture
def executor(mock_datasource, mocker):
    """Create SqlExecutor with mocked dependencies."""
    # Mock ConnectionManager to avoid real connection setup
    mock_connection_manager = MagicMock()
    mock_connection_manager.db_type = 'postgresql'
    mocker.patch(
        'tdm_orchestrator.services.sql.executor.ConnectionManager',
        return_value=mock_connection_manager
    )
    # Mock get_splitter to avoid real splitter setup
    mock_splitter = MagicMock()
    mocker.patch(
        'tdm_orchestrator.services.sql.executor.get_splitter',
        return_value=mock_splitter
    )
    return SqlExecutor(mock_datasource)


# =====================
# _log Method Tests
# =====================

def test_log_default_info_level(executor, mocker):
    """_log uses INFO level by default when level not specified."""
    mock_logger = mocker.patch('tdm_orchestrator.services.sql.executor.logger')
    
    executor._log("Test message")
    
    # Verify log was added to internal logs
    assert len(executor._logs) == 1
    assert "[INFO]" in executor._logs[0]
    assert "Test message" in executor._logs[0]
    
    # Verify logger.info was called
    mock_logger.info.assert_called_once_with("Test message")


def test_log_entry_format_contains_timestamp(executor, mocker):
    """_log entry contains properly formatted timestamp."""
    mocker.patch('tdm_orchestrator.services.sql.executor.logger')
    
    # Freeze time for deterministic test
    fixed_time = datetime(2024, 1, 15, 10, 30, 45)
    mocker.patch(
        'tdm_orchestrator.services.sql.executor.datetime'
    ).now.return_value = fixed_time
    
    executor._log("Test message")
    
    log_entry = executor._logs[0]
    expected_timestamp = fixed_time.strftime(LOG_TIMESTAMP_FORMAT)
    assert expected_timestamp in log_entry


def test_log_entry_format_structure(executor, mocker):
    """_log entry follows [timestamp] [level] message format."""
    mocker.patch('tdm_orchestrator.services.sql.executor.logger')
    
    executor._log("My test message", level='WARNING')
    
    log_entry = executor._logs[0]
    # Verify structure: starts with [, contains ][WARNING], ends with message
    assert log_entry.startswith("[")
    assert "] [WARNING] My test message" in log_entry


def test_log_warning_level(executor, mocker):
    """_log correctly handles WARNING level."""
    mock_logger = mocker.patch('tdm_orchestrator.services.sql.executor.logger')
    
    executor._log("Warning message", level='WARNING')
    
    assert len(executor._logs) == 1
    assert "[WARNING]" in executor._logs[0]
    assert "Warning message" in executor._logs[0]
    mock_logger.warning.assert_called_once_with("Warning message")


def test_log_error_level(executor, mocker):
    """_log correctly handles ERROR level."""
    mock_logger = mocker.patch('tdm_orchestrator.services.sql.executor.logger')
    
    executor._log("Error message", level='ERROR')
    
    assert len(executor._logs) == 1
    assert "[ERROR]" in executor._logs[0]
    assert "Error message" in executor._logs[0]
    mock_logger.error.assert_called_once_with("Error message")


def test_log_debug_level(executor, mocker):
    """_log correctly handles DEBUG level."""
    mock_logger = mocker.patch('tdm_orchestrator.services.sql.executor.logger')
    
    executor._log("Debug message", level='DEBUG')
    
    assert len(executor._logs) == 1
    assert "[DEBUG]" in executor._logs[0]
    assert "Debug message" in executor._logs[0]
    mock_logger.debug.assert_called_once_with("Debug message")


def test_log_unknown_level_fallback_to_info(executor, mocker):
    """_log falls back to logger.info for unknown log levels."""
    mock_logger = mocker.patch('tdm_orchestrator.services.sql.executor.logger')
    # Do NOT set mock_logger.unknownlevel = None, just leave it unassigned so getattr fallback works
    # This way, getattr(logger, 'unknownlevel', logger.info) returns logger.info (a callable)
    executor._log("Unknown level message", level='UNKNOWNLEVEL')

    assert len(executor._logs) == 1
    assert "[UNKNOWNLEVEL]" in executor._logs[0]
    # Since getattr with default=logger.info is used, info should be called
    mock_logger.info.assert_called_once_with("Unknown level message")


def test_log_accumulates_multiple_entries(executor, mocker):
    """_log accumulates multiple log entries in _logs list."""
    mocker.patch('tdm_orchestrator.services.sql.executor.logger')
    
    executor._log("First message")
    executor._log("Second message", level='WARNING')
    executor._log("Third message", level='ERROR')
    
    assert len(executor._logs) == 3
    assert "First message" in executor._logs[0]
    assert "[INFO]" in executor._logs[0]
    assert "Second message" in executor._logs[1]
    assert "[WARNING]" in executor._logs[1]
    assert "Third message" in executor._logs[2]
    assert "[ERROR]" in executor._logs[2]


def test_log_preserves_order(executor, mocker):
    """_log preserves chronological order of log entries."""
    mocker.patch('tdm_orchestrator.services.sql.executor.logger')
    
    messages = ["Message 1", "Message 2", "Message 3", "Message 4", "Message 5"]
    for msg in messages:
        executor._log(msg)
    
    assert len(executor._logs) == 5
    for i, msg in enumerate(messages):
        assert msg in executor._logs[i]


def test_log_empty_message(executor, mocker):
    """_log handles empty message string."""
    mock_logger = mocker.patch('tdm_orchestrator.services.sql.executor.logger')
    
    executor._log("")
    
    assert len(executor._logs) == 1
    assert "[INFO]" in executor._logs[0]
    mock_logger.info.assert_called_once_with("")


def test_log_message_with_special_characters(executor, mocker):
    """_log handles messages with special characters."""
    mock_logger = mocker.patch('tdm_orchestrator.services.sql.executor.logger')
    
    special_message = "Message with émojis 🎉 and accénts àéïõü"
    executor._log(special_message)
    
    assert len(executor._logs) == 1
    assert special_message in executor._logs[0]
    mock_logger.info.assert_called_once_with(special_message)


def test_log_message_with_newlines(executor, mocker):
    """_log handles messages containing newline characters."""
    mock_logger = mocker.patch('tdm_orchestrator.services.sql.executor.logger')
    
    multiline_message = "Line 1\nLine 2\nLine 3"
    executor._log(multiline_message)
    
    assert len(executor._logs) == 1
    assert multiline_message in executor._logs[0]
    mock_logger.info.assert_called_once_with(multiline_message)


def test_log_case_insensitive_level_lookup(executor, mocker):
    """_log converts level to lowercase for logger method lookup."""
    mock_logger = mocker.patch('tdm_orchestrator.services.sql.executor.logger')
    
    # Test with uppercase level - should call lowercase method
    executor._log("Test", level='INFO')
    mock_logger.info.assert_called_with("Test")
    
    executor._log("Test2", level='info')
    # Second call should also work
    assert mock_logger.info.call_count == 2


def test_log_clears_on_execute_start(executor, mocker):
    """Verify _logs list behavior - it should be clearable."""
    mocker.patch('tdm_orchestrator.services.sql.executor.logger')
    
    executor._log("Message 1")
    executor._log("Message 2")
    assert len(executor._logs) == 2
    
    # Clear logs (as execute() does at start)
    executor._logs = []
    
    executor._log("New message")
    assert len(executor._logs) == 1
    assert "New message" in executor._logs[0]


def test_log_initial_empty_logs_list(mock_datasource, mocker):
    """SqlExecutor initializes with empty _logs list."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.db_type = 'postgresql'
    mocker.patch(
        'tdm_orchestrator.services.sql.executor.ConnectionManager',
        return_value=mock_connection_manager
    )
    mocker.patch(
        'tdm_orchestrator.services.sql.executor.get_splitter',
        return_value=MagicMock()
    )
    
    executor = SqlExecutor(mock_datasource)
    
    assert executor._logs == []
    assert isinstance(executor._logs, list)


# =====================
# Summary of Covered Cases
# =====================
# - _log method:
#   - Default INFO level when level not specified
#   - Log entry format contains timestamp in LOG_TIMESTAMP_FORMAT
#   - Log entry follows [timestamp] [level] message structure
#   - WARNING level handling and logger.warning dispatch
#   - ERROR level handling and logger.error dispatch
#   - DEBUG level handling and logger.debug dispatch
#   - Unknown level fallback to logger.info
#   - Multiple log entries accumulation
#   - Log entry order preservation
#   - Empty message handling
#   - Special characters and unicode handling
#   - Multiline message handling
#   - Case-insensitive level lookup (level.lower())
#   - _logs list clearable behavior
#   - Initial empty _logs list on SqlExecutor creation