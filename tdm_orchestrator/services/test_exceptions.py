"""
Tests for TDM Orchestrator custom exceptions.

Covers:
- TDMOrchestratorError: Base exception with message and details
- SQL Exceptions: SqlExecutionError, DatabaseConnectionError, SqlSplitError
- Parsing Exceptions: VariableParsingError, VariableValidationError
- Export Exceptions: ExportError, ZipCreationError, ConfigGenerationError
- Orchestration Exceptions: OrchestrationError, StepExecutionError, RunnerExecutionError
"""

import pytest

from .exceptions import (
    TDMOrchestratorError,
    SqlExecutionError,
    DatabaseConnectionError,
    SqlSplitError,
    VariableParsingError,
    VariableValidationError,
    ExportError,
    ZipCreationError,
    ConfigGenerationError,
    OrchestrationError,
    StepExecutionError,
    RunnerExecutionError,
)


# =====================
# TDMOrchestratorError (Base Exception) Tests
# =====================

class TestTDMOrchestratorError:
    """Tests for TDMOrchestratorError base exception class."""

    def test_creates_instance_with_message_only(self):
        """Creates instance with only message parameter."""
        error = TDMOrchestratorError("Test error message")
        
        assert error.message == "Test error message"

    def test_default_details_is_empty_dict(self):
        """Default details is an empty dictionary when not provided."""
        error = TDMOrchestratorError("Test error")
        
        assert error.details == {}
        assert isinstance(error.details, dict)

    def test_creates_instance_with_message_and_details(self):
        """Creates instance with message and details parameters."""
        details = {"key": "value", "code": 123}
        error = TDMOrchestratorError("Test error", details=details)
        
        assert error.message == "Test error"
        assert error.details == {"key": "value", "code": 123}

    def test_inherits_from_exception(self):
        """Inherits from built-in Exception class."""
        error = TDMOrchestratorError("Test error")
        
        assert isinstance(error, Exception)

    def test_str_returns_message(self):
        """str() returns the error message."""
        error = TDMOrchestratorError("This is the error message")
        
        assert str(error) == "This is the error message"

    def test_can_be_raised_and_caught(self):
        """Can be raised and caught as exception."""
        with pytest.raises(TDMOrchestratorError) as exc_info:
            raise TDMOrchestratorError("Raised error")
        
        assert exc_info.value.message == "Raised error"

    def test_can_be_caught_as_exception(self):
        """Can be caught using base Exception type."""
        with pytest.raises(Exception):
            raise TDMOrchestratorError("Caught as Exception")

    def test_details_none_becomes_empty_dict(self):
        """Passing None as details results in empty dict."""
        error = TDMOrchestratorError("Test error", details=None)
        
        assert error.details == {}

    def test_empty_message(self):
        """Handles empty message string."""
        error = TDMOrchestratorError("")
        
        assert error.message == ""
        assert str(error) == ""

    def test_unicode_message(self):
        """Handles unicode characters in message."""
        error = TDMOrchestratorError("Erreur: données invalides 日本語 🎉")
        
        assert error.message == "Erreur: données invalides 日本語 🎉"

    def test_complex_details_structure(self):
        """Handles complex nested details structure."""
        complex_details = {
            "errors": [{"field": "name", "msg": "required"}],
            "context": {"user_id": 1, "action": "create"},
            "nested": {"level1": {"level2": "value"}}
        }
        error = TDMOrchestratorError("Complex error", details=complex_details)
        
        assert error.details == complex_details
        assert error.details["errors"][0]["field"] == "name"

    def test_details_is_mutable(self):
        """Details dictionary can be modified after creation."""
        error = TDMOrchestratorError("Test error", details={"key": "value"})
        error.details["new_key"] = "new_value"
        
        assert error.details["new_key"] == "new_value"

    def test_args_contains_message(self):
        """Exception args tuple contains the message."""
        error = TDMOrchestratorError("Error in args")
        
        assert error.args == ("Error in args",)


# =====================
# SqlExecutionError Tests
# =====================

class TestSqlExecutionError:
    """Tests for SqlExecutionError exception class."""

    def test_inherits_from_tdm_orchestrator_error(self):
        """Inherits from TDMOrchestratorError."""
        error = SqlExecutionError("SQL error")
        
        assert isinstance(error, TDMOrchestratorError)

    def test_creates_instance_with_message(self):
        """Creates instance with message."""
        error = SqlExecutionError("Query failed")
        
        assert error.message == "Query failed"

    def test_creates_instance_with_message_and_details(self):
        """Creates instance with message and details."""
        error = SqlExecutionError(
            "Query failed",
            details={"query": "SELECT * FROM users", "line": 5}
        )
        
        assert error.message == "Query failed"
        assert error.details["query"] == "SELECT * FROM users"
        assert error.details["line"] == 5

    def test_default_details_is_empty_dict(self):
        """Default details is empty dict."""
        error = SqlExecutionError("SQL error")
        
        assert error.details == {}

    def test_can_be_raised_and_caught(self):
        """Can be raised and caught."""
        with pytest.raises(SqlExecutionError) as exc_info:
            raise SqlExecutionError("Execution failed")
        
        assert exc_info.value.message == "Execution failed"

    def test_can_be_caught_as_base_class(self):
        """Can be caught as TDMOrchestratorError."""
        with pytest.raises(TDMOrchestratorError):
            raise SqlExecutionError("SQL error caught as base")


# =====================
# DatabaseConnectionError Tests
# =====================

class TestDatabaseConnectionError:
    """Tests for DatabaseConnectionError exception class."""

    def test_inherits_from_tdm_orchestrator_error(self):
        """Inherits from TDMOrchestratorError."""
        error = DatabaseConnectionError("Connection failed")
        
        assert isinstance(error, TDMOrchestratorError)

    def test_creates_instance_with_message(self):
        """Creates instance with message."""
        error = DatabaseConnectionError("Cannot connect to database")
        
        assert error.message == "Cannot connect to database"

    def test_creates_instance_with_message_and_details(self):
        """Creates instance with message and details."""
        error = DatabaseConnectionError(
            "Connection refused",
            details={"host": "localhost", "port": 5432, "database": "testdb"}
        )
        
        assert error.message == "Connection refused"
        assert error.details["host"] == "localhost"
        assert error.details["port"] == 5432

    def test_default_details_is_empty_dict(self):
        """Default details is empty dict."""
        error = DatabaseConnectionError("Connection error")
        
        assert error.details == {}

    def test_can_be_raised_and_caught(self):
        """Can be raised and caught."""
        with pytest.raises(DatabaseConnectionError) as exc_info:
            raise DatabaseConnectionError("Timeout")
        
        assert exc_info.value.message == "Timeout"

    def test_can_be_caught_as_base_class(self):
        """Can be caught as TDMOrchestratorError."""
        with pytest.raises(TDMOrchestratorError):
            raise DatabaseConnectionError("Connection error caught as base")


# =====================
# SqlSplitError Tests
# =====================

class TestSqlSplitError:
    """Tests for SqlSplitError exception class."""

    def test_inherits_from_tdm_orchestrator_error(self):
        """Inherits from TDMOrchestratorError."""
        error = SqlSplitError("Split error")
        
        assert isinstance(error, TDMOrchestratorError)

    def test_creates_instance_with_message(self):
        """Creates instance with message."""
        error = SqlSplitError("Cannot split SQL content")
        
        assert error.message == "Cannot split SQL content"

    def test_creates_instance_with_message_and_details(self):
        """Creates instance with message and details."""
        error = SqlSplitError(
            "Unclosed string literal",
            details={"position": 42, "content": "SELECT 'unclosed"}
        )
        
        assert error.message == "Unclosed string literal"
        assert error.details["position"] == 42

    def test_default_details_is_empty_dict(self):
        """Default details is empty dict."""
        error = SqlSplitError("Split error")
        
        assert error.details == {}

    def test_can_be_raised_and_caught(self):
        """Can be raised and caught."""
        with pytest.raises(SqlSplitError) as exc_info:
            raise SqlSplitError("Parse error")
        
        assert exc_info.value.message == "Parse error"


# =====================
# VariableParsingError Tests
# =====================

class TestVariableParsingError:
    """Tests for VariableParsingError exception class."""

    def test_inherits_from_tdm_orchestrator_error(self):
        """Inherits from TDMOrchestratorError."""
        error = VariableParsingError("Parsing error")
        
        assert isinstance(error, TDMOrchestratorError)

    def test_creates_instance_with_message(self):
        """Creates instance with message."""
        error = VariableParsingError("Cannot parse variable")
        
        assert error.message == "Cannot parse variable"

    def test_creates_instance_with_message_and_details(self):
        """Creates instance with message and details."""
        error = VariableParsingError(
            "Invalid variable syntax",
            details={"variable": "{{invalid", "expected": "{{name}}"}
        )
        
        assert error.message == "Invalid variable syntax"
        assert error.details["variable"] == "{{invalid"

    def test_default_details_is_empty_dict(self):
        """Default details is empty dict."""
        error = VariableParsingError("Parsing error")
        
        assert error.details == {}

    def test_can_be_raised_and_caught(self):
        """Can be raised and caught."""
        with pytest.raises(VariableParsingError) as exc_info:
            raise VariableParsingError("Variable not found")
        
        assert exc_info.value.message == "Variable not found"

    def test_can_be_caught_as_base_class(self):
        """Can be caught as TDMOrchestratorError."""
        with pytest.raises(TDMOrchestratorError):
            raise VariableParsingError("Parsing error caught as base")


# =====================
# VariableValidationError Tests
# =====================

class TestVariableValidationError:
    """Tests for VariableValidationError exception class."""

    def test_inherits_from_variable_parsing_error(self):
        """Inherits from VariableParsingError."""
        error = VariableValidationError("Validation error")
        
        assert isinstance(error, VariableParsingError)

    def test_inherits_from_tdm_orchestrator_error(self):
        """Also inherits from TDMOrchestratorError (via VariableParsingError)."""
        error = VariableValidationError("Validation error")
        
        assert isinstance(error, TDMOrchestratorError)

    def test_creates_instance_with_message(self):
        """Creates instance with message."""
        error = VariableValidationError("Invalid variable name")
        
        assert error.message == "Invalid variable name"

    def test_creates_instance_with_message_and_details(self):
        """Creates instance with message and details."""
        error = VariableValidationError(
            "Variable name contains invalid characters",
            details={"name": "my-var", "invalid_chars": ["-"]}
        )
        
        assert error.message == "Variable name contains invalid characters"
        assert error.details["name"] == "my-var"

    def test_can_be_caught_as_variable_parsing_error(self):
        """Can be caught as VariableParsingError."""
        with pytest.raises(VariableParsingError):
            raise VariableValidationError("Validation caught as parsing")

    def test_can_be_raised_and_caught(self):
        """Can be raised and caught."""
        with pytest.raises(VariableValidationError) as exc_info:
            raise VariableValidationError("Invalid format")
        
        assert exc_info.value.message == "Invalid format"


# =====================
# ExportError Tests
# =====================

class TestExportError:
    """Tests for ExportError exception class."""

    def test_inherits_from_tdm_orchestrator_error(self):
        """Inherits from TDMOrchestratorError."""
        error = ExportError("Export failed")
        
        assert isinstance(error, TDMOrchestratorError)

    def test_creates_instance_with_message(self):
        """Creates instance with message."""
        error = ExportError("Cannot export data")
        
        assert error.message == "Cannot export data"

    def test_creates_instance_with_message_and_details(self):
        """Creates instance with message and details."""
        error = ExportError(
            "Export failed",
            details={"format": "csv", "records": 1000}
        )
        
        assert error.message == "Export failed"
        assert error.details["format"] == "csv"

    def test_default_details_is_empty_dict(self):
        """Default details is empty dict."""
        error = ExportError("Export error")
        
        assert error.details == {}

    def test_can_be_raised_and_caught(self):
        """Can be raised and caught."""
        with pytest.raises(ExportError) as exc_info:
            raise ExportError("Output error")
        
        assert exc_info.value.message == "Output error"


# =====================
# ZipCreationError Tests
# =====================

class TestZipCreationError:
    """Tests for ZipCreationError exception class."""

    def test_inherits_from_export_error(self):
        """Inherits from ExportError."""
        error = ZipCreationError("ZIP creation failed")
        
        assert isinstance(error, ExportError)

    def test_inherits_from_tdm_orchestrator_error(self):
        """Also inherits from TDMOrchestratorError (via ExportError)."""
        error = ZipCreationError("ZIP error")
        
        assert isinstance(error, TDMOrchestratorError)

    def test_creates_instance_with_message(self):
        """Creates instance with message."""
        error = ZipCreationError("Cannot create ZIP file")
        
        assert error.message == "Cannot create ZIP file"

    def test_creates_instance_with_message_and_details(self):
        """Creates instance with message and details."""
        error = ZipCreationError(
            "Disk full",
            details={"path": "/tmp/export.zip", "size_needed": 1024}
        )
        
        assert error.message == "Disk full"
        assert error.details["path"] == "/tmp/export.zip"

    def test_can_be_caught_as_export_error(self):
        """Can be caught as ExportError."""
        with pytest.raises(ExportError):
            raise ZipCreationError("ZIP caught as export")

    def test_can_be_raised_and_caught(self):
        """Can be raised and caught."""
        with pytest.raises(ZipCreationError) as exc_info:
            raise ZipCreationError("Compression failed")
        
        assert exc_info.value.message == "Compression failed"


# =====================
# ConfigGenerationError Tests
# =====================

class TestConfigGenerationError:
    """Tests for ConfigGenerationError exception class."""

    def test_inherits_from_export_error(self):
        """Inherits from ExportError."""
        error = ConfigGenerationError("Config generation failed")
        
        assert isinstance(error, ExportError)

    def test_inherits_from_tdm_orchestrator_error(self):
        """Also inherits from TDMOrchestratorError (via ExportError)."""
        error = ConfigGenerationError("Config error")
        
        assert isinstance(error, TDMOrchestratorError)

    def test_creates_instance_with_message(self):
        """Creates instance with message."""
        error = ConfigGenerationError("Cannot generate configuration")
        
        assert error.message == "Cannot generate configuration"

    def test_creates_instance_with_message_and_details(self):
        """Creates instance with message and details."""
        error = ConfigGenerationError(
            "Invalid template",
            details={"template": "config.yaml.j2", "error": "Missing variable"}
        )
        
        assert error.message == "Invalid template"
        assert error.details["template"] == "config.yaml.j2"

    def test_can_be_caught_as_export_error(self):
        """Can be caught as ExportError."""
        with pytest.raises(ExportError):
            raise ConfigGenerationError("Config caught as export")

    def test_can_be_raised_and_caught(self):
        """Can be raised and caught."""
        with pytest.raises(ConfigGenerationError) as exc_info:
            raise ConfigGenerationError("Template error")
        
        assert exc_info.value.message == "Template error"


# =====================
# OrchestrationError Tests
# =====================

class TestOrchestrationError:
    """Tests for OrchestrationError exception class."""

    def test_inherits_from_tdm_orchestrator_error(self):
        """Inherits from TDMOrchestratorError."""
        error = OrchestrationError("Orchestration failed")
        
        assert isinstance(error, TDMOrchestratorError)

    def test_creates_instance_with_message(self):
        """Creates instance with message."""
        error = OrchestrationError("Workflow failed")
        
        assert error.message == "Workflow failed"

    def test_creates_instance_with_message_and_details(self):
        """Creates instance with message and details."""
        error = OrchestrationError(
            "Pipeline error",
            details={"pipeline_id": 123, "stage": "validation"}
        )
        
        assert error.message == "Pipeline error"
        assert error.details["pipeline_id"] == 123

    def test_default_details_is_empty_dict(self):
        """Default details is empty dict."""
        error = OrchestrationError("Orchestration error")
        
        assert error.details == {}

    def test_can_be_raised_and_caught(self):
        """Can be raised and caught."""
        with pytest.raises(OrchestrationError) as exc_info:
            raise OrchestrationError("Step failed")
        
        assert exc_info.value.message == "Step failed"


# =====================
# StepExecutionError Tests
# =====================

class TestStepExecutionError:
    """Tests for StepExecutionError exception class."""

    def test_inherits_from_orchestration_error(self):
        """Inherits from OrchestrationError."""
        error = StepExecutionError("Step failed")
        
        assert isinstance(error, OrchestrationError)

    def test_inherits_from_tdm_orchestrator_error(self):
        """Also inherits from TDMOrchestratorError (via OrchestrationError)."""
        error = StepExecutionError("Step error")
        
        assert isinstance(error, TDMOrchestratorError)

    def test_creates_instance_with_message_only(self):
        """Creates instance with only message."""
        error = StepExecutionError("Step execution failed")
        
        assert error.message == "Step execution failed"

    def test_default_step_name_is_none(self):
        """Default step_name is None."""
        error = StepExecutionError("Step error")
        
        assert error.step_name is None

    def test_default_step_order_is_none(self):
        """Default step_order is None."""
        error = StepExecutionError("Step error")
        
        assert error.step_order is None

    def test_creates_instance_with_step_name(self):
        """Creates instance with step_name parameter."""
        error = StepExecutionError("Step failed", step_name="data_validation")
        
        assert error.message == "Step failed"
        assert error.step_name == "data_validation"

    def test_creates_instance_with_step_order(self):
        """Creates instance with step_order parameter."""
        error = StepExecutionError("Step failed", step_order=3)
        
        assert error.message == "Step failed"
        assert error.step_order == 3

    def test_creates_instance_with_all_parameters(self):
        """Creates instance with all parameters."""
        error = StepExecutionError(
            "Validation step failed",
            step_name="validate_data",
            step_order=2,
            details={"input_file": "data.csv"}
        )
        
        assert error.message == "Validation step failed"
        assert error.step_name == "validate_data"
        assert error.step_order == 2
        assert error.details["input_file"] == "data.csv"

    def test_can_be_caught_as_orchestration_error(self):
        """Can be caught as OrchestrationError."""
        with pytest.raises(OrchestrationError):
            raise StepExecutionError("Step caught as orchestration")

    def test_can_be_raised_and_caught(self):
        """Can be raised and caught."""
        with pytest.raises(StepExecutionError) as exc_info:
            raise StepExecutionError("Step failed", step_name="test_step", step_order=1)
        
        assert exc_info.value.message == "Step failed"
        assert exc_info.value.step_name == "test_step"
        assert exc_info.value.step_order == 1

    def test_step_order_can_be_zero(self):
        """step_order can be zero (first step)."""
        error = StepExecutionError("First step failed", step_order=0)
        
        assert error.step_order == 0

    def test_step_name_empty_string(self):
        """step_name can be empty string."""
        error = StepExecutionError("Step error", step_name="")
        
        assert error.step_name == ""


# =====================
# RunnerExecutionError Tests
# =====================

class TestRunnerExecutionError:
    """Tests for RunnerExecutionError exception class."""

    def test_inherits_from_orchestration_error(self):
        """Inherits from OrchestrationError."""
        error = RunnerExecutionError("Runner failed")
        
        assert isinstance(error, OrchestrationError)

    def test_inherits_from_tdm_orchestrator_error(self):
        """Also inherits from TDMOrchestratorError (via OrchestrationError)."""
        error = RunnerExecutionError("Runner error")
        
        assert isinstance(error, TDMOrchestratorError)

    def test_creates_instance_with_message_only(self):
        """Creates instance with only message."""
        error = RunnerExecutionError("Runner execution failed")
        
        assert error.message == "Runner execution failed"

    def test_default_runner_id_is_none(self):
        """Default runner_id is None."""
        error = RunnerExecutionError("Runner error")
        
        assert error.runner_id is None

    def test_default_runner_name_is_none(self):
        """Default runner_name is None."""
        error = RunnerExecutionError("Runner error")
        
        assert error.runner_name is None

    def test_creates_instance_with_runner_id(self):
        """Creates instance with runner_id parameter."""
        error = RunnerExecutionError("Runner failed", runner_id=42)
        
        assert error.message == "Runner failed"
        assert error.runner_id == 42

    def test_creates_instance_with_runner_name(self):
        """Creates instance with runner_name parameter."""
        error = RunnerExecutionError("Runner failed", runner_name="main_runner")
        
        assert error.message == "Runner failed"
        assert error.runner_name == "main_runner"

    def test_creates_instance_with_all_parameters(self):
        """Creates instance with all parameters."""
        error = RunnerExecutionError(
            "Runner timeout",
            runner_id=123,
            runner_name="batch_processor",
            details={"timeout_seconds": 300}
        )
        
        assert error.message == "Runner timeout"
        assert error.runner_id == 123
        assert error.runner_name == "batch_processor"
        assert error.details["timeout_seconds"] == 300

    def test_can_be_caught_as_orchestration_error(self):
        """Can be caught as OrchestrationError."""
        with pytest.raises(OrchestrationError):
            raise RunnerExecutionError("Runner caught as orchestration")

    def test_can_be_raised_and_caught(self):
        """Can be raised and caught."""
        with pytest.raises(RunnerExecutionError) as exc_info:
            raise RunnerExecutionError("Runner failed", runner_id=1, runner_name="test")
        
        assert exc_info.value.message == "Runner failed"
        assert exc_info.value.runner_id == 1
        assert exc_info.value.runner_name == "test"

    def test_runner_id_can_be_zero(self):
        """runner_id can be zero."""
        error = RunnerExecutionError("Runner error", runner_id=0)
        
        assert error.runner_id == 0

    def test_runner_name_empty_string(self):
        """runner_name can be empty string."""
        error = RunnerExecutionError("Runner error", runner_name="")
        
        assert error.runner_name == ""


# =====================
# Inheritance Hierarchy Tests
# =====================

class TestExceptionHierarchy:
    """Tests verifying the exception inheritance hierarchy."""

    def test_all_sql_exceptions_inherit_from_base(self):
        """All SQL exceptions inherit from TDMOrchestratorError."""
        sql_exceptions = [
            SqlExecutionError("test"),
            DatabaseConnectionError("test"),
            SqlSplitError("test"),
        ]
        
        for exc in sql_exceptions:
            assert isinstance(exc, TDMOrchestratorError)

    def test_all_parsing_exceptions_inherit_from_base(self):
        """All parsing exceptions inherit from TDMOrchestratorError."""
        parsing_exceptions = [
            VariableParsingError("test"),
            VariableValidationError("test"),
        ]
        
        for exc in parsing_exceptions:
            assert isinstance(exc, TDMOrchestratorError)

    def test_variable_validation_inherits_from_variable_parsing(self):
        """VariableValidationError inherits from VariableParsingError."""
        error = VariableValidationError("test")
        
        assert isinstance(error, VariableParsingError)

    def test_all_export_exceptions_inherit_from_base(self):
        """All export exceptions inherit from TDMOrchestratorError."""
        export_exceptions = [
            ExportError("test"),
            ZipCreationError("test"),
            ConfigGenerationError("test"),
        ]
        
        for exc in export_exceptions:
            assert isinstance(exc, TDMOrchestratorError)

    def test_zip_and_config_inherit_from_export(self):
        """ZipCreationError and ConfigGenerationError inherit from ExportError."""
        assert isinstance(ZipCreationError("test"), ExportError)
        assert isinstance(ConfigGenerationError("test"), ExportError)

    def test_all_orchestration_exceptions_inherit_from_base(self):
        """All orchestration exceptions inherit from TDMOrchestratorError."""
        orchestration_exceptions = [
            OrchestrationError("test"),
            StepExecutionError("test"),
            RunnerExecutionError("test"),
        ]
        
        for exc in orchestration_exceptions:
            assert isinstance(exc, TDMOrchestratorError)

    def test_step_and_runner_inherit_from_orchestration(self):
        """StepExecutionError and RunnerExecutionError inherit from OrchestrationError."""
        assert isinstance(StepExecutionError("test"), OrchestrationError)
        assert isinstance(RunnerExecutionError("test"), OrchestrationError)


# =====================
# Edge Cases
# =====================

class TestExceptionEdgeCases:
    """Edge case tests for all exceptions."""

    def test_multiline_message(self):
        """Handles multiline error message."""
        multiline_msg = "Line 1\nLine 2\nLine 3"
        error = TDMOrchestratorError(multiline_msg)
        
        assert error.message == multiline_msg
        assert "\n" in str(error)

    def test_very_long_message(self):
        """Handles very long error message."""
        long_msg = "x" * 10000
        error = TDMOrchestratorError(long_msg)
        
        assert len(error.message) == 10000

    def test_special_characters_in_message(self):
        """Handles special characters in message."""
        special_msg = "Error: <tag>&amp;'\"\\n\\t"
        error = TDMOrchestratorError(special_msg)
        
        assert error.message == special_msg

    def test_details_with_none_values(self):
        """Handles details dict with None values."""
        error = TDMOrchestratorError(
            "Error",
            details={"key1": None, "key2": "value"}
        )
        
        assert error.details["key1"] is None
        assert error.details["key2"] == "value"

    def test_details_with_list_values(self):
        """Handles details dict with list values."""
        error = TDMOrchestratorError(
            "Error",
            details={"items": [1, 2, 3], "names": ["a", "b"]}
        )
        
        assert error.details["items"] == [1, 2, 3]
        assert error.details["names"] == ["a", "b"]

    def test_chained_exception(self):
        """Handles exception chaining with __cause__."""
        original = ValueError("Original error")
        try:
            raise TDMOrchestratorError("Wrapped error") from original
        except TDMOrchestratorError as e:
            assert e.__cause__ == original

    def test_step_error_with_negative_order(self):
        """StepExecutionError handles negative step_order."""
        error = StepExecutionError("Error", step_order=-1)
        
        assert error.step_order == -1

    def test_runner_error_with_negative_id(self):
        """RunnerExecutionError handles negative runner_id."""
        error = RunnerExecutionError("Error", runner_id=-1)
        
        assert error.runner_id == -1

    def test_exception_repr(self):
        """Exception has meaningful repr."""
        error = TDMOrchestratorError("Test message")
        
        # Should not raise an error
        repr_str = repr(error)
        assert isinstance(repr_str, str)

    def test_exception_equality_by_identity(self):
        """Two exception instances are not equal (identity comparison)."""
        error1 = TDMOrchestratorError("Same message")
        error2 = TDMOrchestratorError("Same message")
        
        assert error1 is not error2


# =====================
# Summary of Covered Cases
# =====================
# - TDMOrchestratorError (Base):
#   - Message only initialization
#   - Message and details initialization
#   - Default details is empty dict
#   - None details becomes empty dict
#   - Inheritance from Exception
#   - str() returns message
#   - Can be raised and caught
#   - Empty/unicode/complex messages
#   - Complex/mutable details
#
# - SQL Exceptions (SqlExecutionError, DatabaseConnectionError, SqlSplitError):
#   - Inherit from TDMOrchestratorError
#   - Message and details support
#   - Can be raised and caught
#
# - Parsing Exceptions (VariableParsingError, VariableValidationError):
#   - VariableParsingError inherits from TDMOrchestratorError
#   - VariableValidationError inherits from VariableParsingError
#   - Can be caught at parent level
#
# - Export Exceptions (ExportError, ZipCreationError, ConfigGenerationError):
#   - ExportError inherits from TDMOrchestratorError
#   - ZipCreationError/ConfigGenerationError inherit from ExportError
#   - Can be caught at parent level
#
# - Orchestration Exceptions (OrchestrationError, StepExecutionError, RunnerExecutionError):
#   - OrchestrationError inherits from TDMOrchestratorError
#   - StepExecutionError with step_name/step_order
#   - RunnerExecutionError with runner_id/runner_name
#   - Default None for optional attributes
#   - All combinations of parameters
#
# - Inheritance Hierarchy:
#   - All exceptions ultimately inherit from TDMOrchestratorError
#   - Correct parent class for each exception
#
# - Edge Cases:
#   - Multiline/long/special character messages
#   - Complex details structures
#   - Exception chaining
#   - Negative values for numeric attributes
#   - Zero values for numeric attributes
#   - Empty strings for string attributes