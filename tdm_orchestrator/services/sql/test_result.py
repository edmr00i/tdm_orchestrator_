"""
Tests for SqlExecutionResult - SQL execution result dataclass.

Covers:
- __init__: Dataclass instantiation with required/optional fields
- duration_seconds property: Conversion from ms to seconds
- has_errors property: Error detection logic
- to_dict method: Dictionary serialization
- success_result factory: Creates success result instances
- failure_result factory: Creates failure result instances
"""

import pytest

from .result import SqlExecutionResult


# =====================
# __init__ (Dataclass Instantiation) Tests
# =====================

class TestSqlExecutionResultInit:
    """Tests for SqlExecutionResult dataclass instantiation."""

    def test_creates_instance_with_required_fields_only(self):
        """Creates instance with only required fields (success, duration_ms, logs)."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs="Test logs"
        )
        
        assert result.success is True
        assert result.duration_ms == 100
        assert result.logs == "Test logs"

    def test_default_value_error_message_is_none(self):
        """Default value for error_message is None."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs="Test logs"
        )
        
        assert result.error_message is None

    def test_default_value_rows_affected_is_none(self):
        """Default value for rows_affected is None."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs="Test logs"
        )
        
        assert result.rows_affected is None

    def test_default_value_statements_executed_is_zero(self):
        """Default value for statements_executed is 0."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs="Test logs"
        )
        
        assert result.statements_executed == 0

    def test_default_value_statements_failed_is_zero(self):
        """Default value for statements_failed is 0."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs="Test logs"
        )
        
        assert result.statements_failed == 0

    def test_creates_instance_with_all_fields(self):
        """Creates instance with all fields explicitly set."""
        result = SqlExecutionResult(
            success=False,
            duration_ms=500,
            logs="Execution logs",
            error_message="Something went wrong",
            rows_affected=10,
            statements_executed=5,
            statements_failed=2
        )
        
        assert result.success is False
        assert result.duration_ms == 500
        assert result.logs == "Execution logs"
        assert result.error_message == "Something went wrong"
        assert result.rows_affected == 10
        assert result.statements_executed == 5
        assert result.statements_failed == 2

    def test_success_false_with_error_message(self):
        """Creates failure instance with error message."""
        result = SqlExecutionResult(
            success=False,
            duration_ms=200,
            logs="Error logs",
            error_message="Database connection failed"
        )
        
        assert result.success is False
        assert result.error_message == "Database connection failed"

    def test_empty_logs_string(self):
        """Handles empty logs string."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=50,
            logs=""
        )
        
        assert result.logs == ""

    def test_zero_duration(self):
        """Handles zero duration_ms."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=0,
            logs="Instant execution"
        )
        
        assert result.duration_ms == 0

    def test_large_duration_value(self):
        """Handles large duration_ms values."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=3600000,  # 1 hour in ms
            logs="Long execution"
        )
        
        assert result.duration_ms == 3600000

    def test_zero_rows_affected(self):
        """Handles zero rows_affected explicitly set."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs="SELECT query",
            rows_affected=0
        )
        
        assert result.rows_affected == 0

    def test_large_rows_affected(self):
        """Handles large rows_affected values."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=5000,
            logs="Bulk update",
            rows_affected=1000000
        )
        
        assert result.rows_affected == 1000000


# =====================
# duration_seconds Property Tests
# =====================

class TestDurationSecondsProperty:
    """Tests for duration_seconds computed property."""

    def test_converts_milliseconds_to_seconds(self):
        """Converts duration_ms to seconds correctly."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=1500,
            logs=""
        )
        
        assert result.duration_seconds == 1.5

    def test_zero_duration_returns_zero(self):
        """Returns 0.0 for zero duration."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=0,
            logs=""
        )
        
        assert result.duration_seconds == 0.0

    def test_rounds_to_two_decimal_places(self):
        """Rounds result to 2 decimal places."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=1234,
            logs=""
        )
        
        # 1234 / 1000 = 1.234, rounded to 1.23
        assert result.duration_seconds == 1.23

    def test_rounds_up_correctly(self):
        """Rounds up when third decimal >= 5."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=1235,
            logs=""
        )
        
        # 1235 / 1000 = 1.235, rounded to 1.24
        assert result.duration_seconds == 1.24

    def test_small_duration_less_than_10ms(self):
        """Handles small duration less than 10ms."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=5,
            logs=""
        )
        
        # 5 / 1000 = 0.005, rounded to 0.01
        assert result.duration_seconds == 0.01

    def test_very_small_duration_1ms(self):
        """Handles 1ms duration."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=1,
            logs=""
        )
        
        # 1 / 1000 = 0.001, rounded to 0.0
        assert result.duration_seconds == 0.0

    def test_large_duration_one_hour(self):
        """Handles large duration (1 hour)."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=3600000,
            logs=""
        )
        
        assert result.duration_seconds == 3600.0

    def test_exact_seconds_no_rounding_needed(self):
        """Handles exact second values (no rounding needed)."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=2000,
            logs=""
        )
        
        assert result.duration_seconds == 2.0

    def test_return_type_is_float(self):
        """Returns float type."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=1000,
            logs=""
        )
        
        assert isinstance(result.duration_seconds, float)


# =====================
# has_errors Property Tests
# =====================

class TestHasErrorsProperty:
    """Tests for has_errors computed property."""

    def test_returns_false_when_no_errors(self):
        """Returns False when statements_failed=0 and error_message=None."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs="",
            statements_failed=0,
            error_message=None
        )
        
        assert result.has_errors is False

    def test_returns_true_when_statements_failed_greater_than_zero(self):
        """Returns True when statements_failed > 0."""
        result = SqlExecutionResult(
            success=False,
            duration_ms=100,
            logs="",
            statements_failed=1
        )
        
        assert result.has_errors is True

    def test_returns_true_when_error_message_is_not_none(self):
        """Returns True when error_message is not None."""
        result = SqlExecutionResult(
            success=False,
            duration_ms=100,
            logs="",
            error_message="An error occurred"
        )
        
        assert result.has_errors is True

    def test_returns_true_when_both_conditions_met(self):
        """Returns True when both statements_failed > 0 and error_message is set."""
        result = SqlExecutionResult(
            success=False,
            duration_ms=100,
            logs="",
            statements_failed=3,
            error_message="Multiple errors"
        )
        
        assert result.has_errors is True

    def test_returns_false_with_success_true_and_no_failed(self):
        """Returns False for successful execution with no failures."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs="All good",
            statements_executed=5,
            statements_failed=0
        )
        
        assert result.has_errors is False

    def test_empty_string_error_message_is_truthy(self):
        """Empty string error_message is considered as having errors (not None)."""
        result = SqlExecutionResult(
            success=False,
            duration_ms=100,
            logs="",
            error_message=""
        )
        
        # Empty string is not None, so has_errors should be True
        assert result.has_errors is True

    def test_multiple_statements_failed(self):
        """Returns True when multiple statements failed."""
        result = SqlExecutionResult(
            success=False,
            duration_ms=100,
            logs="",
            statements_failed=10
        )
        
        assert result.has_errors is True

    def test_success_true_but_has_error_message(self):
        """Edge case: success=True but error_message set (inconsistent state)."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs="",
            error_message="Warning: something happened"
        )
        
        # has_errors should still return True because error_message is not None
        assert result.has_errors is True

    def test_success_false_but_no_error_indicators(self):
        """Edge case: success=False but no error indicators set."""
        result = SqlExecutionResult(
            success=False,
            duration_ms=100,
            logs="",
            statements_failed=0,
            error_message=None
        )
        
        # has_errors checks statements_failed and error_message, not success
        assert result.has_errors is False


# =====================
# to_dict Method Tests
# =====================

class TestToDictMethod:
    """Tests for to_dict serialization method."""

    def test_returns_dictionary(self):
        """Returns a dictionary type."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs=""
        )
        
        output = result.to_dict()
        
        assert isinstance(output, dict)

    def test_contains_all_expected_keys(self):
        """Contains all expected keys."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs=""
        )
        
        output = result.to_dict()
        
        expected_keys = {
            'success',
            'duration_ms',
            'duration_seconds',
            'logs',
            'error_message',
            'rows_affected',
            'statements_executed',
            'statements_failed'
        }
        assert set(output.keys()) == expected_keys

    def test_success_value_matches(self):
        """success value matches instance attribute."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs=""
        )
        
        output = result.to_dict()
        
        assert output['success'] is True

    def test_duration_ms_value_matches(self):
        """duration_ms value matches instance attribute."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=1500,
            logs=""
        )
        
        output = result.to_dict()
        
        assert output['duration_ms'] == 1500

    def test_duration_seconds_is_computed(self):
        """duration_seconds is computed property value."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=1500,
            logs=""
        )
        
        output = result.to_dict()
        
        assert output['duration_seconds'] == 1.5

    def test_logs_value_matches(self):
        """logs value matches instance attribute."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs="Detailed execution logs"
        )
        
        output = result.to_dict()
        
        assert output['logs'] == "Detailed execution logs"

    def test_error_message_none_serialized(self):
        """error_message None is serialized correctly."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs=""
        )
        
        output = result.to_dict()
        
        assert output['error_message'] is None

    def test_error_message_string_serialized(self):
        """error_message string is serialized correctly."""
        result = SqlExecutionResult(
            success=False,
            duration_ms=100,
            logs="",
            error_message="Connection failed"
        )
        
        output = result.to_dict()
        
        assert output['error_message'] == "Connection failed"

    def test_rows_affected_none_serialized(self):
        """rows_affected None is serialized correctly."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs=""
        )
        
        output = result.to_dict()
        
        assert output['rows_affected'] is None

    def test_rows_affected_integer_serialized(self):
        """rows_affected integer is serialized correctly."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs="",
            rows_affected=42
        )
        
        output = result.to_dict()
        
        assert output['rows_affected'] == 42

    def test_statements_executed_serialized(self):
        """statements_executed is serialized correctly."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs="",
            statements_executed=5
        )
        
        output = result.to_dict()
        
        assert output['statements_executed'] == 5

    def test_statements_failed_serialized(self):
        """statements_failed is serialized correctly."""
        result = SqlExecutionResult(
            success=False,
            duration_ms=100,
            logs="",
            statements_failed=2
        )
        
        output = result.to_dict()
        
        assert output['statements_failed'] == 2

    def test_all_fields_serialized_together(self):
        """All fields are serialized correctly together."""
        result = SqlExecutionResult(
            success=False,
            duration_ms=2500,
            logs="Execution log content",
            error_message="Error occurred",
            rows_affected=100,
            statements_executed=8,
            statements_failed=2
        )
        
        output = result.to_dict()
        
        assert output == {
            'success': False,
            'duration_ms': 2500,
            'duration_seconds': 2.5,
            'logs': "Execution log content",
            'error_message': "Error occurred",
            'rows_affected': 100,
            'statements_executed': 8,
            'statements_failed': 2
        }

    def test_multiline_logs_serialized(self):
        """Multiline logs are serialized correctly."""
        multiline_logs = "Line 1\nLine 2\nLine 3"
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs=multiline_logs
        )
        
        output = result.to_dict()
        
        assert output['logs'] == multiline_logs
        assert '\n' in output['logs']

    def test_unicode_in_logs_serialized(self):
        """Unicode characters in logs are serialized correctly."""
        unicode_logs = "Exécution réussie 🎉 日本語"
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs=unicode_logs
        )
        
        output = result.to_dict()
        
        assert output['logs'] == unicode_logs


# =====================
# success_result Factory Method Tests
# =====================

class TestSuccessResultFactory:
    """Tests for success_result class method (factory)."""

    def test_creates_instance_with_success_true(self):
        """Creates instance with success=True."""
        result = SqlExecutionResult.success_result(
            duration_ms=100,
            logs="Success"
        )
        
        assert result.success is True

    def test_sets_duration_ms(self):
        """Sets duration_ms from parameter."""
        result = SqlExecutionResult.success_result(
            duration_ms=500,
            logs=""
        )
        
        assert result.duration_ms == 500

    def test_sets_logs(self):
        """Sets logs from parameter."""
        result = SqlExecutionResult.success_result(
            duration_ms=100,
            logs="Execution completed successfully"
        )
        
        assert result.logs == "Execution completed successfully"

    def test_sets_statements_executed(self):
        """Sets statements_executed from parameter."""
        result = SqlExecutionResult.success_result(
            duration_ms=100,
            logs="",
            statements_executed=10
        )
        
        assert result.statements_executed == 10

    def test_sets_rows_affected(self):
        """Sets rows_affected from parameter."""
        result = SqlExecutionResult.success_result(
            duration_ms=100,
            logs="",
            rows_affected=50
        )
        
        assert result.rows_affected == 50

    def test_default_statements_executed_is_zero(self):
        """Default statements_executed is 0."""
        result = SqlExecutionResult.success_result(
            duration_ms=100,
            logs=""
        )
        
        assert result.statements_executed == 0

    def test_default_rows_affected_is_none(self):
        """Default rows_affected is None."""
        result = SqlExecutionResult.success_result(
            duration_ms=100,
            logs=""
        )
        
        assert result.rows_affected is None

    def test_error_message_is_none(self):
        """error_message is always None for success result."""
        result = SqlExecutionResult.success_result(
            duration_ms=100,
            logs="",
            statements_executed=5,
            rows_affected=10
        )
        
        assert result.error_message is None

    def test_statements_failed_is_zero(self):
        """statements_failed is always 0 for success result."""
        result = SqlExecutionResult.success_result(
            duration_ms=100,
            logs=""
        )
        
        assert result.statements_failed == 0

    def test_returns_sql_execution_result_instance(self):
        """Returns SqlExecutionResult instance."""
        result = SqlExecutionResult.success_result(
            duration_ms=100,
            logs=""
        )
        
        assert isinstance(result, SqlExecutionResult)

    def test_has_errors_is_false(self):
        """has_errors property returns False for success result."""
        result = SqlExecutionResult.success_result(
            duration_ms=100,
            logs=""
        )
        
        assert result.has_errors is False

    def test_with_all_optional_parameters(self):
        """Creates success result with all optional parameters."""
        result = SqlExecutionResult.success_result(
            duration_ms=1000,
            logs="Complete logs",
            statements_executed=20,
            rows_affected=500
        )
        
        assert result.success is True
        assert result.duration_ms == 1000
        assert result.logs == "Complete logs"
        assert result.statements_executed == 20
        assert result.rows_affected == 500
        assert result.error_message is None
        assert result.statements_failed == 0


# =====================
# failure_result Factory Method Tests
# =====================

class TestFailureResultFactory:
    """Tests for failure_result class method (factory)."""

    def test_creates_instance_with_success_false(self):
        """Creates instance with success=False."""
        result = SqlExecutionResult.failure_result(
            duration_ms=100,
            logs="",
            error_message="Error"
        )
        
        assert result.success is False

    def test_sets_duration_ms(self):
        """Sets duration_ms from parameter."""
        result = SqlExecutionResult.failure_result(
            duration_ms=750,
            logs="",
            error_message="Error"
        )
        
        assert result.duration_ms == 750

    def test_sets_logs(self):
        """Sets logs from parameter."""
        result = SqlExecutionResult.failure_result(
            duration_ms=100,
            logs="Error logs here",
            error_message="Error"
        )
        
        assert result.logs == "Error logs here"

    def test_sets_error_message(self):
        """Sets error_message from parameter."""
        result = SqlExecutionResult.failure_result(
            duration_ms=100,
            logs="",
            error_message="Database connection refused"
        )
        
        assert result.error_message == "Database connection refused"

    def test_sets_statements_executed(self):
        """Sets statements_executed from parameter."""
        result = SqlExecutionResult.failure_result(
            duration_ms=100,
            logs="",
            error_message="Error",
            statements_executed=3
        )
        
        assert result.statements_executed == 3

    def test_sets_statements_failed(self):
        """Sets statements_failed from parameter."""
        result = SqlExecutionResult.failure_result(
            duration_ms=100,
            logs="",
            error_message="Error",
            statements_failed=2
        )
        
        assert result.statements_failed == 2

    def test_default_statements_executed_is_zero(self):
        """Default statements_executed is 0."""
        result = SqlExecutionResult.failure_result(
            duration_ms=100,
            logs="",
            error_message="Error"
        )
        
        assert result.statements_executed == 0

    def test_default_statements_failed_is_zero(self):
        """Default statements_failed is 0."""
        result = SqlExecutionResult.failure_result(
            duration_ms=100,
            logs="",
            error_message="Error"
        )
        
        assert result.statements_failed == 0

    def test_rows_affected_is_none(self):
        """rows_affected is always None for failure result."""
        result = SqlExecutionResult.failure_result(
            duration_ms=100,
            logs="",
            error_message="Error",
            statements_executed=5,
            statements_failed=2
        )
        
        assert result.rows_affected is None

    def test_returns_sql_execution_result_instance(self):
        """Returns SqlExecutionResult instance."""
        result = SqlExecutionResult.failure_result(
            duration_ms=100,
            logs="",
            error_message="Error"
        )
        
        assert isinstance(result, SqlExecutionResult)

    def test_has_errors_is_true_due_to_error_message(self):
        """has_errors property returns True due to error_message."""
        result = SqlExecutionResult.failure_result(
            duration_ms=100,
            logs="",
            error_message="Something went wrong"
        )
        
        assert result.has_errors is True

    def test_has_errors_is_true_due_to_statements_failed(self):
        """has_errors property returns True due to statements_failed > 0."""
        result = SqlExecutionResult.failure_result(
            duration_ms=100,
            logs="",
            error_message="Error",
            statements_failed=5
        )
        
        assert result.has_errors is True

    def test_with_all_optional_parameters(self):
        """Creates failure result with all optional parameters."""
        result = SqlExecutionResult.failure_result(
            duration_ms=2000,
            logs="Detailed error logs",
            error_message="Critical failure",
            statements_executed=3,
            statements_failed=7
        )
        
        assert result.success is False
        assert result.duration_ms == 2000
        assert result.logs == "Detailed error logs"
        assert result.error_message == "Critical failure"
        assert result.statements_executed == 3
        assert result.statements_failed == 7
        assert result.rows_affected is None

    def test_empty_error_message_string(self):
        """Handles empty error_message string."""
        result = SqlExecutionResult.failure_result(
            duration_ms=100,
            logs="",
            error_message=""
        )
        
        assert result.error_message == ""
        assert result.has_errors is True


# =====================
# Integration Tests
# =====================

class TestSqlExecutionResultIntegration:
    """Integration tests combining multiple features."""

    def test_success_result_to_dict_integration(self):
        """success_result followed by to_dict produces expected output."""
        result = SqlExecutionResult.success_result(
            duration_ms=1500,
            logs="Execution complete",
            statements_executed=10,
            rows_affected=100
        )
        
        output = result.to_dict()
        
        assert output['success'] is True
        assert output['duration_ms'] == 1500
        assert output['duration_seconds'] == 1.5
        assert output['logs'] == "Execution complete"
        assert output['error_message'] is None
        assert output['rows_affected'] == 100
        assert output['statements_executed'] == 10
        assert output['statements_failed'] == 0

    def test_failure_result_to_dict_integration(self):
        """failure_result followed by to_dict produces expected output."""
        result = SqlExecutionResult.failure_result(
            duration_ms=500,
            logs="Error during execution",
            error_message="Syntax error at line 5",
            statements_executed=4,
            statements_failed=1
        )
        
        output = result.to_dict()
        
        assert output['success'] is False
        assert output['duration_ms'] == 500
        assert output['duration_seconds'] == 0.5
        assert output['logs'] == "Error during execution"
        assert output['error_message'] == "Syntax error at line 5"
        assert output['rows_affected'] is None
        assert output['statements_executed'] == 4
        assert output['statements_failed'] == 1

    def test_duration_seconds_consistency_in_to_dict(self):
        """duration_seconds in to_dict matches property value."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=1234,
            logs=""
        )
        
        output = result.to_dict()
        
        assert output['duration_seconds'] == result.duration_seconds

    def test_has_errors_consistency_with_factory_methods(self):
        """has_errors is consistent with factory method outcomes."""
        success = SqlExecutionResult.success_result(
            duration_ms=100,
            logs=""
        )
        failure = SqlExecutionResult.failure_result(
            duration_ms=100,
            logs="",
            error_message="Error",
            statements_failed=1
        )
        
        assert success.has_errors is False
        assert failure.has_errors is True


# =====================
# Edge Cases
# =====================

class TestSqlExecutionResultEdgeCases:
    """Edge case tests for SqlExecutionResult."""

    def test_very_long_logs_string(self):
        """Handles very long logs string."""
        long_logs = "x" * 100000
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs=long_logs
        )
        
        assert len(result.logs) == 100000
        assert result.to_dict()['logs'] == long_logs

    def test_very_long_error_message(self):
        """Handles very long error message."""
        long_error = "Error: " + "x" * 10000
        result = SqlExecutionResult.failure_result(
            duration_ms=100,
            logs="",
            error_message=long_error
        )
        
        assert result.error_message == long_error

    def test_special_characters_in_logs(self):
        """Handles special characters in logs."""
        special_logs = "Line1\tTab\nLine2\rCarriage\0Null"
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs=special_logs
        )
        
        assert result.logs == special_logs

    def test_special_characters_in_error_message(self):
        """Handles special characters in error message."""
        special_error = "Error:\n\tDetails here"
        result = SqlExecutionResult.failure_result(
            duration_ms=100,
            logs="",
            error_message=special_error
        )
        
        assert result.error_message == special_error

    def test_negative_rows_affected_edge_case(self):
        """Handles negative rows_affected (unusual but possible)."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=100,
            logs="",
            rows_affected=-1
        )
        
        assert result.rows_affected == -1

    def test_max_int_duration(self):
        """Handles maximum integer duration value."""
        import sys
        max_int = sys.maxsize
        result = SqlExecutionResult(
            success=True,
            duration_ms=max_int,
            logs=""
        )
        
        assert result.duration_ms == max_int
        # duration_seconds should still compute (may lose precision)
        assert isinstance(result.duration_seconds, float)

    def test_zero_values_everywhere(self):
        """Handles all numeric values as zero."""
        result = SqlExecutionResult(
            success=True,
            duration_ms=0,
            logs="",
            rows_affected=0,
            statements_executed=0,
            statements_failed=0
        )
        
        assert result.duration_ms == 0
        assert result.duration_seconds == 0.0
        assert result.rows_affected == 0
        assert result.statements_executed == 0
        assert result.statements_failed == 0
        assert result.has_errors is False


# =====================
# Summary of Covered Cases
# =====================
# - __init__ (Dataclass Instantiation):
#   - Required fields only
#   - All fields explicitly set
#   - Default values for optional fields
#   - Empty logs string
#   - Zero/large duration values
#   - Zero/large rows_affected values
#
# - duration_seconds property:
#   - Milliseconds to seconds conversion
#   - Zero duration
#   - Rounding to 2 decimal places
#   - Rounding up/down
#   - Small/large durations
#   - Return type is float
#
# - has_errors property:
#   - Returns False when no errors
#   - Returns True when statements_failed > 0
#   - Returns True when error_message is not None
#   - Returns True when both conditions met
#   - Empty string error_message
#   - Inconsistent states (success=True but error set)
#
# - to_dict method:
#   - Returns dictionary type
#   - Contains all expected keys
#   - Values match instance attributes
#   - Computed duration_seconds included
#   - None values serialized correctly
#   - Multiline/unicode logs
#
# - success_result factory:
#   - Creates instance with success=True
#   - Sets all provided parameters
#   - Default values for optional parameters
#   - error_message always None
#   - statements_failed always 0
#
# - failure_result factory:
#   - Creates instance with success=False
#   - Sets error_message
#   - Sets statements_failed
#   - Default values for optional parameters
#   - rows_affected always None
#
# - Integration tests:
#   - Factory methods with to_dict
#   - Property consistency
#
# - Edge cases:
#   - Very long strings
#   - Special characters
#   - Negative values
#   - Maximum integer values
#   - All zeros