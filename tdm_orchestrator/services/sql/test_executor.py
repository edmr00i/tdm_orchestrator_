import pytest
from unittest.mock import MagicMock
from tdm_orchestrator.services.sql.executor import SqlExecutor, SqlExecutionError

"""Tests for SqlExecutor class."""




# =====================
# Fixtures
# =====================

@pytest.fixture
def mock_datasource():
    """Creates a mock datasource for testing."""
    datasource = MagicMock()
    datasource.db_type = 'postgresql'
    return datasource


@pytest.fixture
def executor(mock_datasource, mocker):
    """Creates a SqlExecutor instance with mocked dependencies."""
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
    mocker.patch(
        'tdm_orchestrator.services.sql.executor.VariableParser',
        return_value=MagicMock()
    )
    
    return SqlExecutor(mock_datasource)


# =====================
# db_type Property Tests
# =====================

class TestDbTypeProperty:
    """Tests for SqlExecutor.db_type property."""

    def test_db_type_returns_connection_manager_db_type(self, executor):
        """db_type property returns the db_type from connection_manager."""
        assert executor.db_type == 'postgresql'

    def test_db_type_reflects_different_database_types(self, mock_datasource, mocker):
        """db_type reflects different database types from connection_manager."""
        mock_connection_manager = MagicMock()
        mock_connection_manager.db_type = 'oracle'
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.ConnectionManager',
            return_value=mock_connection_manager
        )
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.get_splitter',
            return_value=MagicMock()
        )
        
        exec_instance = SqlExecutor(mock_datasource)
        
        assert exec_instance.db_type == 'oracle'


# =====================
# _is_transaction_forbidden Tests
# =====================

class TestIsTransactionForbidden:
    """Tests for SqlExecutor._is_transaction_forbidden method."""

    def test_returns_false_for_regular_select(self, executor, mocker):
        """Returns False for regular SELECT statement."""
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            [r'\bCREATE\s+DATABASE\b', r'\bDROP\s+DATABASE\b']
        )
        
        result = executor._is_transaction_forbidden("SELECT * FROM users")
        
        assert result is False

    def test_returns_false_for_regular_insert(self, executor, mocker):
        """Returns False for regular INSERT statement."""
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            [r'\bCREATE\s+DATABASE\b', r'\bDROP\s+DATABASE\b']
        )
        
        result = executor._is_transaction_forbidden("INSERT INTO users VALUES (1, 'test')")
        
        assert result is False

    def test_returns_true_for_create_database(self, executor, mocker):
        """Returns True for CREATE DATABASE statement."""
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            [r'\bCREATE\s+DATABASE\b']
        )
        
        result = executor._is_transaction_forbidden("CREATE DATABASE testdb")
        
        assert result is True

    def test_returns_true_for_drop_database(self, executor, mocker):
        """Returns True for DROP DATABASE statement."""
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            [r'\bDROP\s+DATABASE\b']
        )
        
        result = executor._is_transaction_forbidden("DROP DATABASE testdb")
        
        assert result is True

    def test_case_insensitive_matching(self, executor, mocker):
        """Pattern matching is case insensitive."""
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            [r'\bCREATE\s+DATABASE\b']
        )
        
        result_upper = executor._is_transaction_forbidden("CREATE DATABASE testdb")
        result_lower = executor._is_transaction_forbidden("create database testdb")
        result_mixed = executor._is_transaction_forbidden("Create Database testdb")
        
        assert result_upper is True
        assert result_lower is True
        assert result_mixed is True

    def test_returns_false_when_no_patterns_defined(self, executor, mocker):
        """Returns False when TRANSACTION_FORBIDDEN_PATTERNS is empty."""
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            []
        )
        
        result = executor._is_transaction_forbidden("CREATE DATABASE testdb")
        
        assert result is False


# =====================
# _execute_autocommit Tests
# =====================

class TestExecuteAutocommit:
    """Tests for SqlExecutor._execute_autocommit method."""

    def test_executes_statement_with_autocommit(self, executor, mocker):
        """Executes statement using autocommit connection."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor._execute_autocommit("CREATE DATABASE testdb")
        
        executor.connection_manager.get_connection.assert_called_once_with(autocommit=True)
        mock_cursor.execute.assert_called_once_with("CREATE DATABASE testdb")
        mock_cursor.close.assert_called_once()

    def test_raises_sql_execution_error_on_failure(self, executor, mocker):
        """Raises SqlExecutionError when execution fails."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Database error")
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        with pytest.raises(SqlExecutionError) as exc_info:
            executor._execute_autocommit("INVALID SQL")
        
        assert "Erreur autocommit" in str(exc_info.value)
        assert "Database error" in str(exc_info.value)


# =====================
# _parse_and_split Tests
# =====================

class TestParseAndSplit:
    """Tests for SqlExecutor._parse_and_split method."""

    def test_parses_variables_and_splits_sql(self, executor, mocker):
        """Parses variables and splits SQL content."""
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "SELECT 1; SELECT 2"
        executor.splitter.split.return_value = ["SELECT 1", "SELECT 2"]
        
        result = executor._parse_and_split("SELECT {{var}}", {"var": "1"})
        
        executor.variable_parser.parse.assert_called_once_with(
            "SELECT {{var}}", {"var": "1"}, strict_validation=False
        )
        executor.splitter.split.assert_called_once_with("SELECT 1; SELECT 2")
        assert result == ["SELECT 1", "SELECT 2"]

    def test_passes_strict_validation_flag(self, executor, mocker):
        """Passes strict validation flag to variable parser."""
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "SELECT 1"
        executor.splitter.split.return_value = ["SELECT 1"]
        
        executor._parse_and_split("SELECT 1", {}, strict=True)
        
        executor.variable_parser.parse.assert_called_once_with(
            "SELECT 1", {}, strict_validation=True
        )

    def test_handles_empty_variables(self, executor, mocker):
        """Handles empty variables dictionary."""
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "SELECT 1"
        executor.splitter.split.return_value = ["SELECT 1"]
        
        result = executor._parse_and_split("SELECT 1", {})
        
        executor.variable_parser.parse.assert_called_once_with(
            "SELECT 1", {}, strict_validation=False
        )
        assert result == ["SELECT 1"]

    def test_returns_empty_list_for_empty_sql(self, executor, mocker):
        """Returns empty list when SQL content produces no statements."""
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = ""
        executor.splitter.split.return_value = []
        
        result = executor._parse_and_split("", {})
        
        assert result == []


# =====================
# execute_dry_run Tests
# =====================

class TestExecuteDryRun:
    """Tests for SqlExecutor.execute_dry_run method."""

    def test_dry_run_success_with_valid_sql(self, executor, mocker):
        """Dry run succeeds with valid SQL statements."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "SELECT 1"
        executor.splitter.split.return_value = ["SELECT 1"]
        
        result = executor.execute_dry_run("SELECT 1")
        
        assert result.success is True
        assert result.statements_executed == 1
        mock_conn.rollback.assert_called_once()

    def test_dry_run_logs_variables_when_provided(self, executor, mocker):
        """Dry run logs variable names when variables are provided."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "SELECT 'value'"
        executor.splitter.split.return_value = ["SELECT 'value'"]
        
        result = executor.execute_dry_run("SELECT {{var}}", {"var": "value"})
        
        assert result.success is True
        assert "var" in result.logs

    def test_dry_run_returns_success_for_empty_statements(self, executor, mocker):
        """Dry run returns success when no statements to execute."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = ""
        executor.splitter.split.return_value = []
        
        result = executor.execute_dry_run("")
        
        assert result.success is True
        assert result.statements_executed == 0
        assert "Aucune instruction SQL" in result.logs

    def test_dry_run_truncates_long_statements_in_log(self, executor, mocker):
        """Dry run truncates statements longer than 100 chars in log preview."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        long_statement = "SELECT " + "x" * 200
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = long_statement
        executor.splitter.split.return_value = [long_statement]
        
        result = executor.execute_dry_run(long_statement)
        
        assert result.success is True
        assert "..." in result.logs

    def test_dry_run_failure_returns_error_result(self, executor, mocker):
        """Dry run returns failure result when statement execution fails."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Syntax error")
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "INVALID SQL"
        executor.splitter.split.return_value = ["INVALID SQL"]
        
        result = executor.execute_dry_run("INVALID SQL")
        
        assert result.success is False
        assert "Erreur instruction 1" in result.error_message
        assert result.statements_failed == 1

    def test_dry_run_closes_cursor_after_execution(self, executor, mocker):
        """Dry run closes cursor after all statements are executed."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "SELECT 1"
        executor.splitter.split.return_value = ["SELECT 1"]
        
        executor.execute_dry_run("SELECT 1")
        
        mock_cursor.close.assert_called_once()

    def test_dry_run_multiple_statements_success(self, executor, mocker):
        """Dry run executes multiple statements successfully."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "SELECT 1; SELECT 2; SELECT 3"
        executor.splitter.split.return_value = ["SELECT 1", "SELECT 2", "SELECT 3"]
        
        result = executor.execute_dry_run("SELECT 1; SELECT 2; SELECT 3")
        
        assert result.success is True
        assert result.statements_executed == 3
        assert mock_cursor.execute.call_count == 3

    def test_dry_run_clears_logs_at_start(self, executor, mocker):
        """Dry run clears _logs list at the start of execution."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        
        # Add some pre-existing logs
        executor._logs = ["Previous log entry"]
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = ""
        executor.splitter.split.return_value = []
        
        executor.execute_dry_run("")
        
        # Should not contain previous log entry
        assert "Previous log entry" not in '\n'.join(executor._logs)


# =====================
# execute Tests
# =====================

class TestExecute:
    """Tests for SqlExecutor.execute method."""

    def test_execute_delegates_to_dry_run_when_flag_set(self, executor, mocker):
        """Execute delegates to execute_dry_run when dry_run=True."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        
        mock_dry_run_result = MagicMock()
        mocker.patch.object(executor, 'execute_dry_run', return_value=mock_dry_run_result)
        
        result = executor.execute("SELECT 1", dry_run=True)
        
        executor.execute_dry_run.assert_called_once_with("SELECT 1", None, False)
        assert result == mock_dry_run_result

    def test_execute_success_with_single_statement(self, executor, mocker):
        """Execute succeeds with a single transactional statement."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            []
        )
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "INSERT INTO users VALUES (1)"
        executor.splitter.split.return_value = ["INSERT INTO users VALUES (1)"]
        
        result = executor.execute("INSERT INTO users VALUES (1)")
        
        assert result.success is True
        assert result.statements_executed == 1
        assert result.rows_affected == 1
        mock_conn.commit.assert_called_once()

    def test_execute_returns_success_for_empty_statements(self, executor, mocker):
        """Execute returns success when no statements to execute."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = ""
        executor.splitter.split.return_value = []
        
        result = executor.execute("")
        
        assert result.success is True
        assert result.statements_executed == 0
        assert result.rows_affected == 0

    def test_execute_handles_non_transactional_statements(self, executor, mocker):
        """Execute handles non-transactional statements with autocommit."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            [r'\bCREATE\s+DATABASE\b']
        )
        
        # Mock autocommit execution
        mock_autocommit_cursor = MagicMock()
        mock_autocommit_conn = MagicMock()
        mock_autocommit_conn.cursor.return_value = mock_autocommit_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_autocommit_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "CREATE DATABASE testdb"
        executor.splitter.split.return_value = ["CREATE DATABASE testdb"]
        
        result = executor.execute("CREATE DATABASE testdb")
        
        assert result.success is True
        assert result.statements_executed == 1

    def test_execute_separates_transactional_and_non_transactional(self, executor, mocker):
        """Execute separates transactional and non-transactional statements."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            [r'\bCREATE\s+DATABASE\b']
        )
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "SELECT 1; CREATE DATABASE testdb"
        executor.splitter.split.return_value = ["SELECT 1", "CREATE DATABASE testdb"]
        
        result = executor.execute("SELECT 1; CREATE DATABASE testdb")
        
        assert result.success is True
        assert result.statements_executed == 2
        assert "hors-transaction" in result.logs

    def test_execute_rollback_on_error_with_stop_on_error(self, executor, mocker):
        """Execute performs rollback when error occurs with stop_on_error=True."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            []
        )
        
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("SQL error")
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "INVALID SQL"
        executor.splitter.split.return_value = ["INVALID SQL"]
        
        result = executor.execute("INVALID SQL", stop_on_error=True)
        
        assert result.success is False
        mock_conn.rollback.assert_called_once()

    def test_execute_continues_on_error_with_stop_on_error_false(self, executor, mocker):
        """Execute continues execution when stop_on_error=False."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            []
        )
        
        mock_cursor = MagicMock()
        # First statement fails, second succeeds
        mock_cursor.execute.side_effect = [Exception("First error"), None]
        mock_cursor.rowcount = 1
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "INVALID; SELECT 1"
        executor.splitter.split.return_value = ["INVALID", "SELECT 1"]
        
        result = executor.execute("INVALID; SELECT 1", stop_on_error=False)
        
        # success is True because stop_on_error=False allows partial execution
        assert result.success is True
        assert result.statements_executed == 1
        assert result.statements_failed == 1

    def test_execute_rollback_when_auto_commit_false(self, executor, mocker):
        """Execute performs rollback when auto_commit=False."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            []
        )
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "INSERT INTO users VALUES (1)"
        executor.splitter.split.return_value = ["INSERT INTO users VALUES (1)"]
        
        result = executor.execute("INSERT INTO users VALUES (1)", auto_commit=False)
        
        assert result.success is True
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()

    def test_execute_accumulates_rows_affected(self, executor, mocker):
        """Execute accumulates rows_affected from multiple statements."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            []
        )
        
        mock_cursor = MagicMock()
        # Simulate different rowcounts for each execute
        mock_cursor.rowcount = 5
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "UPDATE t SET x=1; UPDATE t SET y=2"
        executor.splitter.split.return_value = ["UPDATE t SET x=1", "UPDATE t SET y=2"]
        
        result = executor.execute("UPDATE t SET x=1; UPDATE t SET y=2")
        
        assert result.success is True
        assert result.rows_affected == 10  # 5 + 5

    def test_execute_handles_zero_rowcount(self, executor, mocker):
        """Execute handles zero or negative rowcount gracefully."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            []
        )
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "SELECT 1"
        executor.splitter.split.return_value = ["SELECT 1"]
        
        result = executor.execute("SELECT 1")
        
        assert result.success is True
        assert result.rows_affected == 0

    def test_execute_handles_none_rowcount(self, executor, mocker):
        """Execute handles None rowcount gracefully."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            []
        )
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "SELECT 1"
        executor.splitter.split.return_value = ["SELECT 1"]
        
        result = executor.execute("SELECT 1")
        
        assert result.success is True
        assert result.rows_affected == 0

    def test_execute_failure_in_autocommit_statement(self, executor, mocker):
        """Execute handles failure in autocommit statement."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            [r'\bCREATE\s+DATABASE\b']
        )
        
        # Mock _execute_autocommit to raise
        mocker.patch.object(
            executor, '_execute_autocommit',
            side_effect=SqlExecutionError("Autocommit failed")
        )
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "CREATE DATABASE testdb"
        executor.splitter.split.return_value = ["CREATE DATABASE testdb"]
        
        result = executor.execute("CREATE DATABASE testdb", stop_on_error=True)
        
        assert result.success is False
        assert result.statements_failed == 1

    def test_execute_error_message_contains_all_errors(self, executor, mocker):
        """Execute error_message contains all accumulated errors when stop_on_error=False."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            []
        )
        
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = [Exception("Error 1"), Exception("Error 2")]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "BAD1; BAD2"
        executor.splitter.split.return_value = ["BAD1", "BAD2"]
        
        result = executor.execute("BAD1; BAD2", stop_on_error=False)
        
        assert result.statements_failed == 2
        assert "Error 1" in result.error_message
        assert "Error 2" in result.error_message

    def test_execute_clears_logs_at_start(self, executor, mocker):
        """Execute clears _logs list at the start of execution."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        
        # Add some pre-existing logs
        executor._logs = ["Previous log entry"]
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = ""
        executor.splitter.split.return_value = []
        
        executor.execute("")
        
        # Should not contain previous log entry
        assert "Previous log entry" not in '\n'.join(executor._logs)


# =====================
# test_connection Tests
# =====================

class TestTestConnection:
    """Tests for SqlExecutor.test_connection method."""

    def test_delegates_to_connection_manager(self, executor):
        """test_connection delegates to connection_manager.test_connection."""
        executor.connection_manager.test_connection.return_value = (True, "Success")
        
        result = executor.test_connection()
        
        executor.connection_manager.test_connection.assert_called_once()
        assert result == (True, "Success")

    def test_returns_failure_from_connection_manager(self, executor):
        """test_connection returns failure result from connection_manager."""
        executor.connection_manager.test_connection.return_value = (False, "Connection refused")
        
        result = executor.test_connection()
        
        assert result == (False, "Connection refused")


# =====================
# __init__ Tests
# =====================

class TestSqlExecutorInit:
    """Tests for SqlExecutor.__init__ method."""

    def test_initializes_datasource(self, mock_datasource, mocker):
        """__init__ stores datasource reference."""
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
        
        exec_instance = SqlExecutor(mock_datasource)
        
        assert exec_instance.datasource == mock_datasource

    def test_initializes_connection_manager(self, mock_datasource, mocker):
        """__init__ creates ConnectionManager with datasource."""
        mock_connection_manager = MagicMock()
        mock_connection_manager.db_type = 'postgresql'
        mock_cm_class = mocker.patch(
            'tdm_orchestrator.services.sql.executor.ConnectionManager',
            return_value=mock_connection_manager
        )
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.get_splitter',
            return_value=MagicMock()
        )
        
        exec_instance = SqlExecutor(mock_datasource)
        
        mock_cm_class.assert_called_once_with(mock_datasource)
        assert exec_instance.connection_manager == mock_connection_manager

    def test_initializes_variable_parser_non_strict(self, mock_datasource, mocker):
        """__init__ creates VariableParser with strict_mode=False."""
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
        mock_vp_class = mocker.patch(
            'tdm_orchestrator.services.sql.executor.VariableParser',
            return_value=MagicMock()
        )
        
        SqlExecutor(mock_datasource)
        
        mock_vp_class.assert_called_once_with(strict_mode=False)

    def test_initializes_splitter_based_on_db_type(self, mock_datasource, mocker):
        """__init__ gets splitter based on connection_manager.db_type."""
        mock_connection_manager = MagicMock()
        mock_connection_manager.db_type = 'oracle'
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.ConnectionManager',
            return_value=mock_connection_manager
        )
        mock_splitter = MagicMock()
        mock_get_splitter = mocker.patch(
            'tdm_orchestrator.services.sql.executor.get_splitter',
            return_value=mock_splitter
        )
        
        exec_instance = SqlExecutor(mock_datasource)
        
        mock_get_splitter.assert_called_once_with('oracle')
        assert exec_instance.splitter == mock_splitter

    def test_initializes_empty_logs_list(self, mock_datasource, mocker):
        """__init__ initializes _logs as empty list."""
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
        
        exec_instance = SqlExecutor(mock_datasource)
        
        assert exec_instance._logs == []
        assert isinstance(exec_instance._logs, list)


# =====================
# Integration-like Tests
# =====================

class TestSqlExecutorIntegration:
    """Integration-like tests for SqlExecutor."""

    def test_full_execution_flow_with_variables(self, executor, mocker):
        """Tests full execution flow with variable substitution."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            []
        )
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "INSERT INTO users (name) VALUES ('John')"
        executor.splitter.split.return_value = ["INSERT INTO users (name) VALUES ('John')"]
        
        result = executor.execute(
            "INSERT INTO users (name) VALUES ('{{name}}')",
            variables={"name": "John"}
        )
        
        assert result.success is True
        executor.variable_parser.parse.assert_called_once()

    def test_mixed_transactional_and_autocommit_execution(self, executor, mocker):
        """Tests execution with both transactional and autocommit statements."""
        mocker.patch('tdm_orchestrator.services.sql.executor.logger')
        mocker.patch(
            'tdm_orchestrator.services.sql.executor.TRANSACTION_FORBIDDEN_PATTERNS',
            [r'\bCREATE\s+DATABASE\b']
        )
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        executor.connection_manager.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        executor.connection_manager.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        
        # Mock _execute_autocommit
        mocker.patch.object(executor, '_execute_autocommit')
        
        executor.variable_parser = MagicMock()
        executor.variable_parser.parse.return_value = "SELECT 1; CREATE DATABASE testdb; INSERT INTO t VALUES (1)"
        executor.splitter.split.return_value = [
            "SELECT 1",
            "CREATE DATABASE testdb",
            "INSERT INTO t VALUES (1)"
        ]
        
        result = executor.execute("SELECT 1; CREATE DATABASE testdb; INSERT INTO t VALUES (1)")
        
        assert result.success is True
        assert result.statements_executed == 3
        # 2 transactional + 1 autocommit
        assert mock_cursor.execute.call_count == 2
        executor._execute_autocommit.assert_called_once_with("CREATE DATABASE testdb")
