"""
Tests for VariableParser - SQL variable parsing and substitution service.

Covers:
- __init__: Initialization with strict_mode and allowed_variables
- extract_variables: Variable extraction from SQL content
- validate_variable_name: Variable name validation against whitelist
- validate_variable_value: Variable value validation for dangerous patterns
- parse: SQL parsing with variable substitution
- get_missing_variables: Detection of missing required variables
- validate_sql_with_variables: Full validation without parsing
- Utility functions: extract_sql_variables, parse_sql_variables
"""

import re
import pytest
from unittest.mock import patch

from .variable_parser import (
    VariableParser,
    extract_sql_variables,
    parse_sql_variables,
)
from ..exceptions import VariableParsingError, VariableValidationError


# =====================
# Fixtures
# =====================

@pytest.fixture
def mock_variable_pattern():
    """Mock VARIABLE_PATTERN regex that matches ${VAR_NAME} format."""
    return re.compile(r'\$\{([A-Z_][A-Z0-9_]*)\}')


@pytest.fixture
def mock_allowed_variables():
    """Mock set of allowed variable names."""
    return {'SCHEMA', 'TABLE_NAME', 'USER_ID', 'DATABASE'}


@pytest.fixture
def mock_dangerous_patterns():
    """Mock list of dangerous value patterns."""
    return [r';\s*DROP', r';\s*DELETE', r'--', r'/\*']


@pytest.fixture
def parser_strict(mock_allowed_variables, mock_variable_pattern, mock_dangerous_patterns):
    """Create a strict mode parser with mocked constants."""
    with patch('tdm_orchestrator.services.parsers.variable_parser.VARIABLE_PATTERN', mock_variable_pattern), \
         patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', mock_allowed_variables), \
         patch('tdm_orchestrator.services.parsers.variable_parser.DANGEROUS_VARIABLE_VALUE_PATTERNS', mock_dangerous_patterns):
        return VariableParser(strict_mode=True)


@pytest.fixture
def parser_non_strict(mock_variable_pattern, mock_dangerous_patterns):
    """Create a non-strict mode parser with mocked constants."""
    with patch('tdm_orchestrator.services.parsers.variable_parser.VARIABLE_PATTERN', mock_variable_pattern), \
         patch('tdm_orchestrator.services.parsers.variable_parser.DANGEROUS_VARIABLE_VALUE_PATTERNS', mock_dangerous_patterns):
        return VariableParser(strict_mode=False)


# =====================
# __init__ Tests
# =====================

class TestVariableParserInit:
    """Tests for VariableParser.__init__ method."""

    def test_default_strict_mode_is_true(self, mock_allowed_variables):
        """Default strict_mode is True."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', mock_allowed_variables):
            parser = VariableParser()
        
        assert parser.strict_mode is True

    def test_default_allowed_variables_uses_constant(self, mock_allowed_variables):
        """Default allowed_variables uses ALLOWED_VARIABLE_NAMES constant."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', mock_allowed_variables):
            parser = VariableParser()
        
        assert parser.allowed_variables == mock_allowed_variables

    def test_custom_strict_mode_false(self, mock_allowed_variables):
        """Custom strict_mode=False is set correctly."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', mock_allowed_variables):
            parser = VariableParser(strict_mode=False)
        
        assert parser.strict_mode is False

    def test_custom_allowed_variables(self):
        """Custom allowed_variables set is used."""
        custom_vars = {'VAR1', 'VAR2', 'VAR3'}
        parser = VariableParser(allowed_variables=custom_vars)
        
        assert parser.allowed_variables == custom_vars

    def test_none_allowed_variables_uses_default(self, mock_allowed_variables):
        """None for allowed_variables uses ALLOWED_VARIABLE_NAMES."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', mock_allowed_variables):
            parser = VariableParser(allowed_variables=None)
        
        assert parser.allowed_variables == mock_allowed_variables

    def test_empty_allowed_variables_set(self, mock_variable_pattern, mock_dangerous_patterns, mock_allowed_variables):
        """Empty allowed_variables set falls back to default (empty set is falsy)."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.VARIABLE_PATTERN', mock_variable_pattern), \
             patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', mock_allowed_variables), \
             patch('tdm_orchestrator.services.parsers.variable_parser.DANGEROUS_VARIABLE_VALUE_PATTERNS', mock_dangerous_patterns):
            # Empty set is falsy, so it falls back to ALLOWED_VARIABLE_NAMES
            parser = VariableParser(allowed_variables=set(), strict_mode=False)
            assert parser.allowed_variables == mock_allowed_variables


# =====================
# extract_variables Tests
# =====================

class TestExtractVariables:
    """Tests for VariableParser.extract_variables method."""

    def test_empty_string_returns_empty_list(self, parser_non_strict):
        """Empty string returns empty list."""
        result = parser_non_strict.extract_variables("")
        
        assert result == []

    def test_none_returns_empty_list(self, parser_non_strict):
        """None content returns empty list."""
        result = parser_non_strict.extract_variables(None)
        
        assert result == []

    def test_no_variables_returns_empty_list(self, parser_non_strict):
        """SQL without variables returns empty list."""
        sql = "SELECT * FROM users WHERE id = 1"
        result = parser_non_strict.extract_variables(sql)
        
        assert result == []

    def test_single_variable_extraction(self, parser_non_strict):
        """Extracts single variable correctly."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        result = parser_non_strict.extract_variables(sql)
        
        assert result == ['SCHEMA']

    def test_multiple_variables_extraction(self, parser_non_strict):
        """Extracts multiple different variables."""
        sql = "SELECT * FROM ${SCHEMA}.${TABLE_NAME} WHERE id = ${USER_ID}"
        result = parser_non_strict.extract_variables(sql)
        
        assert result == ['SCHEMA', 'TABLE_NAME', 'USER_ID']

    def test_duplicate_variables_deduplicated(self, parser_non_strict):
        """Duplicate variables are removed, preserving first occurrence order."""
        sql = "SELECT ${SCHEMA}.a, ${USER_ID}, ${SCHEMA}.b FROM ${USER_ID}"
        result = parser_non_strict.extract_variables(sql)
        
        assert result == ['SCHEMA', 'USER_ID']

    def test_preserves_order_of_first_occurrence(self, parser_non_strict):
        """Order is preserved based on first occurrence."""
        sql = "${SCHEMA} ${USER_ID} ${DATABASE} ${USER_ID} ${SCHEMA}"
        result = parser_non_strict.extract_variables(sql)
        
        assert result == ['SCHEMA', 'USER_ID', 'DATABASE']

    def test_variable_in_string_literal(self, parser_non_strict):
        """Variables inside SQL are still extracted (pattern doesn't distinguish)."""
        sql = "SELECT '${SCHEMA}' FROM dual"
        result = parser_non_strict.extract_variables(sql)
        
        assert result == ['SCHEMA']

    def test_multiline_sql(self, parser_non_strict):
        """Handles multiline SQL content."""
        sql = """
        SELECT *
        FROM ${SCHEMA}.users
        WHERE id = ${USER_ID}
        """
        result = parser_non_strict.extract_variables(sql)
        
        assert result == ['SCHEMA', 'USER_ID']

    def test_whitespace_only_returns_empty(self, parser_non_strict):
        """Whitespace-only content returns empty list."""
        result = parser_non_strict.extract_variables("   \n\t  ")
        
        assert result == []


# =====================
# validate_variable_name Tests
# =====================

class TestValidateVariableName:
    """Tests for VariableParser.validate_variable_name method."""

    def test_returns_true_in_non_strict_mode(self, parser_non_strict):
        """Returns True for any variable in non-strict mode."""
        result = parser_non_strict.validate_variable_name("ANY_VARIABLE")
        
        assert result is True

    def test_returns_true_in_non_strict_for_unknown_variable(self, parser_non_strict):
        """Returns True for unknown variable in non-strict mode."""
        result = parser_non_strict.validate_variable_name("UNKNOWN_VAR")
        
        assert result is True

    def test_returns_true_for_allowed_variable_strict_mode(self, parser_strict):
        """Returns True for allowed variable in strict mode."""
        result = parser_strict.validate_variable_name("SCHEMA")
        
        assert result is True

    def test_returns_true_for_all_allowed_variables(self, parser_strict, mock_allowed_variables):
        """Returns True for all variables in allowed set."""
        for var in mock_allowed_variables:
            result = parser_strict.validate_variable_name(var)
            assert result is True

    def test_raises_error_for_non_allowed_variable_strict_mode(self, parser_strict):
        """Raises VariableValidationError for non-allowed variable in strict mode."""
        with pytest.raises(VariableValidationError) as exc_info:
            parser_strict.validate_variable_name("FORBIDDEN_VAR")
        
        assert "FORBIDDEN_VAR" in str(exc_info.value)
        assert "non autorisée" in str(exc_info.value)

    def test_error_message_contains_allowed_list(self, parser_strict):
        """Error message contains list of allowed variables."""
        with pytest.raises(VariableValidationError) as exc_info:
            parser_strict.validate_variable_name("BAD_VAR")
        
        assert "Autorisées" in str(exc_info.value)

    def test_empty_variable_name_not_allowed(self, mock_allowed_variables, mock_variable_pattern, mock_dangerous_patterns):
        """Empty variable name is not in allowed set."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.VARIABLE_PATTERN', mock_variable_pattern), \
             patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', mock_allowed_variables), \
             patch('tdm_orchestrator.services.parsers.variable_parser.DANGEROUS_VARIABLE_VALUE_PATTERNS', mock_dangerous_patterns):
            parser = VariableParser(strict_mode=True)
            
            with pytest.raises(VariableValidationError):
                parser.validate_variable_name("")


# =====================
# validate_variable_value Tests
# =====================

class TestValidateVariableValue:
    """Tests for VariableParser.validate_variable_value method."""

    def test_returns_safe_string_value(self, parser_strict):
        """Returns the value for a safe string."""
        result = parser_strict.validate_variable_value("production")
        
        assert result == "production"

    def test_converts_integer_to_string(self, parser_strict):
        """Converts integer to string."""
        result = parser_strict.validate_variable_value(123)
        
        assert result == "123"
        assert isinstance(result, str)

    def test_converts_float_to_string(self, parser_strict):
        """Converts float to string."""
        result = parser_strict.validate_variable_value(3.14)
        
        assert result == "3.14"
        assert isinstance(result, str)

    def test_converts_none_to_string(self, parser_strict):
        """Converts None to string 'None'."""
        result = parser_strict.validate_variable_value(None)
        
        assert result == "None"

    def test_raises_error_for_drop_injection(self, parser_strict):
        """Raises VariableValidationError for DROP injection attempt."""
        with pytest.raises(VariableValidationError) as exc_info:
            parser_strict.validate_variable_value("value; DROP TABLE users")
        
        assert "dangereuse" in str(exc_info.value)

    def test_raises_error_for_delete_injection(self, parser_strict):
        """Raises VariableValidationError for DELETE injection attempt."""
        with pytest.raises(VariableValidationError) as exc_info:
            parser_strict.validate_variable_value("value; DELETE FROM users")
        
        assert "dangereuse" in str(exc_info.value)

    def test_raises_error_for_sql_comment_double_dash(self, parser_strict):
        """Raises VariableValidationError for -- comment injection."""
        with pytest.raises(VariableValidationError) as exc_info:
            parser_strict.validate_variable_value("value -- comment")
        
        assert "dangereuse" in str(exc_info.value)

    def test_raises_error_for_sql_comment_block(self, parser_strict):
        """Raises VariableValidationError for /* */ comment injection."""
        with pytest.raises(VariableValidationError) as exc_info:
            parser_strict.validate_variable_value("value /* comment */")
        
        assert "dangereuse" in str(exc_info.value)

    def test_safe_value_with_spaces(self, parser_strict):
        """Safe value with spaces is accepted."""
        result = parser_strict.validate_variable_value("hello world")
        
        assert result == "hello world"

    def test_safe_value_with_special_chars(self, parser_strict):
        """Safe value with special characters (non-dangerous) is accepted."""
        result = parser_strict.validate_variable_value("user@domain.com")
        
        assert result == "user@domain.com"

    def test_case_insensitive_danger_detection(self, parser_strict):
        """Dangerous patterns are detected case-insensitively."""
        with pytest.raises(VariableValidationError):
            parser_strict.validate_variable_value("value; drop TABLE")


# =====================
# parse Tests
# =====================

class TestParse:
    """Tests for VariableParser.parse method."""

    def test_empty_content_returns_empty(self, parser_non_strict):
        """Empty content returns empty string."""
        result = parser_non_strict.parse("", {})
        
        assert result == ""

    def test_none_content_returns_none(self, parser_non_strict):
        """None content returns None."""
        result = parser_non_strict.parse(None, {})
        
        assert result is None

    def test_no_variables_needed_returns_unchanged(self, parser_non_strict):
        """SQL without variables returns unchanged."""
        sql = "SELECT * FROM users WHERE id = 1"
        result = parser_non_strict.parse(sql, {})
        
        assert result == sql

    def test_single_variable_substitution(self, parser_non_strict):
        """Single variable is substituted correctly."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        result = parser_non_strict.parse(sql, {"SCHEMA": "production"})
        
        assert result == "SELECT * FROM production.users"

    def test_multiple_variable_substitution(self, parser_non_strict):
        """Multiple variables are substituted correctly."""
        sql = "SELECT * FROM ${SCHEMA}.${TABLE_NAME}"
        result = parser_non_strict.parse(sql, {"SCHEMA": "prod", "TABLE_NAME": "users"})
        
        assert result == "SELECT * FROM prod.users"

    def test_same_variable_multiple_occurrences(self, parser_non_strict):
        """Same variable appearing multiple times is substituted everywhere."""
        sql = "SELECT ${SCHEMA}.a, ${SCHEMA}.b FROM ${SCHEMA}.c"
        result = parser_non_strict.parse(sql, {"SCHEMA": "test"})
        
        assert result == "SELECT test.a, test.b FROM test.c"

    def test_raises_error_when_variable_missing(self, parser_non_strict):
        """Raises VariableParsingError when required variable is missing."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        
        with pytest.raises(VariableParsingError) as exc_info:
            parser_non_strict.parse(sql, {"OTHER": "value"})
        
        assert "manquantes" in str(exc_info.value)
        assert "SCHEMA" in str(exc_info.value)

    def test_raises_error_when_no_variables_provided_but_needed(self, parser_non_strict):
        """Raises VariableParsingError when variables needed but none provided."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        
        with pytest.raises(VariableParsingError) as exc_info:
            parser_non_strict.parse(sql, {})
        
        assert "non fournies" in str(exc_info.value)

    def test_raises_error_when_variables_none_but_needed(self, parser_non_strict):
        """Raises VariableParsingError when variables is None but needed."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        
        with pytest.raises(VariableParsingError) as exc_info:
            parser_non_strict.parse(sql, None)
        
        assert "non fournies" in str(exc_info.value)

    def test_empty_variables_dict_no_variables_needed(self, parser_non_strict):
        """Empty variables dict is OK when no variables needed."""
        sql = "SELECT * FROM users"
        result = parser_non_strict.parse(sql, {})
        
        assert result == sql

    def test_extra_variables_ignored(self, parser_non_strict):
        """Extra variables not in SQL are ignored."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        result = parser_non_strict.parse(sql, {"SCHEMA": "prod", "EXTRA": "ignored"})
        
        assert result == "SELECT * FROM prod.users"

    def test_strict_validation_true_validates_names(self, parser_strict):
        """strict_validation=True validates variable names."""
        sql = "SELECT * FROM ${FORBIDDEN_VAR}.users"
        
        with pytest.raises(VariableValidationError) as exc_info:
            parser_strict.parse(sql, {"FORBIDDEN_VAR": "value"}, strict_validation=True)
        
        assert "non autorisée" in str(exc_info.value)

    def test_strict_validation_true_validates_values(self, parser_strict):
        """strict_validation=True validates variable values."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        
        with pytest.raises(VariableValidationError) as exc_info:
            parser_strict.parse(sql, {"SCHEMA": "val; DROP TABLE"}, strict_validation=True)
        
        assert "dangereuse" in str(exc_info.value)

    def test_strict_validation_false_skips_validation(self, parser_strict):
        """strict_validation=False skips name and value validation."""
        sql = "SELECT * FROM ${FORBIDDEN_VAR}.users"
        result = parser_strict.parse(sql, {"FORBIDDEN_VAR": "value"}, strict_validation=False)
        
        assert result == "SELECT * FROM value.users"

    def test_variable_value_with_special_chars(self, parser_non_strict):
        """Variable value with allowed special characters works."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        result = parser_non_strict.parse(sql, {"SCHEMA": "my_schema_123"})
        
        assert result == "SELECT * FROM my_schema_123.users"

    def test_multiline_sql_parsing(self, parser_non_strict):
        """Multiline SQL is parsed correctly."""
        sql = """
        SELECT *
        FROM ${SCHEMA}.users
        WHERE name = '${USER_ID}'
        """
        result = parser_non_strict.parse(sql, {"SCHEMA": "prod", "USER_ID": "123"})
        
        assert "prod.users" in result
        assert "'123'" in result


# =====================
# get_missing_variables Tests
# =====================

class TestGetMissingVariables:
    """Tests for VariableParser.get_missing_variables method."""

    def test_returns_empty_when_all_provided(self, parser_non_strict):
        """Returns empty list when all required variables are provided."""
        sql = "SELECT * FROM ${SCHEMA}.${TABLE_NAME}"
        result = parser_non_strict.get_missing_variables(sql, {"SCHEMA": "a", "TABLE_NAME": "b"})
        
        assert result == []

    def test_returns_missing_variables(self, parser_non_strict):
        """Returns list of missing variables."""
        sql = "SELECT * FROM ${SCHEMA}.${TABLE_NAME}"
        result = parser_non_strict.get_missing_variables(sql, {"SCHEMA": "a"})
        
        assert result == ["TABLE_NAME"]

    def test_returns_all_missing_when_none_provided(self, parser_non_strict):
        """Returns all variables when none are provided."""
        sql = "SELECT * FROM ${SCHEMA}.${TABLE_NAME}"
        result = parser_non_strict.get_missing_variables(sql, {})
        
        assert result == ["SCHEMA", "TABLE_NAME"]

    def test_returns_empty_when_no_variables_needed(self, parser_non_strict):
        """Returns empty when SQL has no variables."""
        sql = "SELECT * FROM users"
        result = parser_non_strict.get_missing_variables(sql, {"EXTRA": "value"})
        
        assert result == []

    def test_handles_empty_sql(self, parser_non_strict):
        """Handles empty SQL content."""
        result = parser_non_strict.get_missing_variables("", {"VAR": "value"})
        
        assert result == []

    def test_preserves_order_of_missing(self, parser_non_strict):
        """Missing variables are returned in order of appearance."""
        sql = "${SCHEMA} ${USER_ID} ${DATABASE}"
        result = parser_non_strict.get_missing_variables(sql, {})
        
        assert result == ['SCHEMA', 'USER_ID', 'DATABASE']
# =====================

class TestValidateSqlWithVariables:
    """Tests for VariableParser.validate_sql_with_variables method."""

    def test_valid_sql_returns_valid_true(self, parser_non_strict):
        """Valid SQL with all variables returns valid=True."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        result = parser_non_strict.validate_sql_with_variables(sql, {"SCHEMA": "prod"})
        
        assert result['valid'] is True
        assert result['errors'] == []

    def test_returns_required_variables(self, parser_non_strict):
        """Returns list of required variables."""
        sql = "SELECT * FROM ${SCHEMA}.${TABLE_NAME}"
        result = parser_non_strict.validate_sql_with_variables(sql, {"SCHEMA": "a", "TABLE_NAME": "b"})
        
        assert result['required_variables'] == ["SCHEMA", "TABLE_NAME"]

    def test_returns_provided_variables(self, parser_non_strict):
        """Returns list of provided variables."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        result = parser_non_strict.validate_sql_with_variables(sql, {"SCHEMA": "a", "EXTRA": "b"})
        
        assert "SCHEMA" in result['provided_variables']
        assert "EXTRA" in result['provided_variables']

    def test_missing_variables_returns_valid_false(self, parser_non_strict):
        """Missing variables returns valid=False."""
        sql = "SELECT * FROM ${SCHEMA}.${TABLE_NAME}"
        result = parser_non_strict.validate_sql_with_variables(sql, {"SCHEMA": "prod"})
        
        assert result['valid'] is False
        assert result['missing_variables'] == ["TABLE_NAME"]
        assert len(result['errors']) > 0

    def test_missing_variables_in_errors(self, parser_non_strict):
        """Missing variables are listed in errors."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        result = parser_non_strict.validate_sql_with_variables(sql, {})
        
        assert result['valid'] is False
        assert any("manquantes" in error for error in result['errors'])

    def test_dangerous_value_returns_valid_false(self, parser_strict):
        """Dangerous variable value returns valid=False."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        result = parser_strict.validate_sql_with_variables(sql, {"SCHEMA": "val; DROP TABLE"})
        
        assert result['valid'] is False
        assert any("dangereuse" in error for error in result['errors'])

    def test_non_allowed_variable_strict_mode_returns_valid_false(self, parser_strict):
        """Non-allowed variable in strict mode returns valid=False."""
        sql = "SELECT * FROM ${FORBIDDEN_VAR}.users"
        result = parser_strict.validate_sql_with_variables(sql, {"FORBIDDEN_VAR": "value"})
        
        assert result['valid'] is False
        assert any("non autorisée" in error for error in result['errors'])

    def test_extra_variables_produce_warnings(self, parser_non_strict):
        """Extra unused variables produce warnings."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        result = parser_non_strict.validate_sql_with_variables(sql, {"SCHEMA": "prod", "EXTRA": "unused"})
        
        assert len(result['warnings']) > 0
        assert any("non utilisées" in warning for warning in result['warnings'])

    def test_no_warnings_when_all_used(self, parser_non_strict):
        """No warnings when all provided variables are used."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        result = parser_non_strict.validate_sql_with_variables(sql, {"SCHEMA": "prod"})
        
        assert result['warnings'] == []

    def test_empty_sql_is_valid(self, parser_non_strict):
        """Empty SQL is considered valid."""
        result = parser_non_strict.validate_sql_with_variables("", {})
        
        assert result['valid'] is True
        assert result['required_variables'] == []

    def test_multiple_errors_accumulated(self, parser_strict):
        """Multiple errors are accumulated."""
        sql = "SELECT * FROM ${FORBIDDEN1}.${FORBIDDEN2}"
        result = parser_strict.validate_sql_with_variables(
            sql, 
            {"FORBIDDEN1": "val; DROP", "FORBIDDEN2": "val--"}
        )
        
        assert result['valid'] is False
        assert len(result['errors']) >= 2

    def test_handles_exception_gracefully(self, parser_non_strict):
        """Handles unexpected exceptions gracefully."""
        with patch.object(parser_non_strict, 'extract_variables', side_effect=Exception("Unexpected error")):
            result = parser_non_strict.validate_sql_with_variables("SELECT 1", {})
        
        assert result['valid'] is False
        assert any("Unexpected error" in error for error in result['errors'])


# =====================
# extract_sql_variables Utility Function Tests
# =====================

class TestExtractSqlVariablesUtility:
    """Tests for extract_sql_variables utility function."""

    def test_extracts_variables_from_sql(self, mock_variable_pattern):
        """Extracts variables from SQL content."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.VARIABLE_PATTERN', mock_variable_pattern), \
             patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', set()):
            result = extract_sql_variables("SELECT * FROM ${SCHEMA}.users")
        
        assert result == ['SCHEMA']

    def test_uses_non_strict_mode(self, mock_variable_pattern):
        """Uses non-strict mode internally."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.VARIABLE_PATTERN', mock_variable_pattern), \
             patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', set()):
            # Should not raise even with unknown variables
            result = extract_sql_variables("SELECT * FROM ${ANY_VAR}.users")
        
        assert result == ['ANY_VAR']

    def test_empty_string_returns_empty_list(self, mock_variable_pattern):
        """Empty string returns empty list."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.VARIABLE_PATTERN', mock_variable_pattern), \
             patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', set()):
            result = extract_sql_variables("")
        
        assert result == []

    def test_multiple_variables(self, mock_variable_pattern):
        """Extracts multiple variables."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.VARIABLE_PATTERN', mock_variable_pattern), \
             patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', set()):
            result = extract_sql_variables("${VAR1} ${VAR2} ${VAR3}")
        
        assert result == ['VAR1', 'VAR2', 'VAR3']


# =====================
# parse_sql_variables Utility Function Tests
# =====================

class TestParseSqlVariablesUtility:
    """Tests for parse_sql_variables utility function."""

    def test_parses_variables_in_sql(self, mock_variable_pattern, mock_allowed_variables, mock_dangerous_patterns):
        """Parses and substitutes variables in SQL."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.VARIABLE_PATTERN', mock_variable_pattern), \
             patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', mock_allowed_variables), \
             patch('tdm_orchestrator.services.parsers.variable_parser.DANGEROUS_VARIABLE_VALUE_PATTERNS', mock_dangerous_patterns):
            result = parse_sql_variables(
                "SELECT * FROM ${SCHEMA}.users",
                {"SCHEMA": "production"},
                strict=True
            )
        
        assert result == "SELECT * FROM production.users"

    def test_strict_false_skips_validation(self, mock_variable_pattern, mock_dangerous_patterns):
        """strict=False skips variable validation."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.VARIABLE_PATTERN', mock_variable_pattern), \
             patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', set()), \
             patch('tdm_orchestrator.services.parsers.variable_parser.DANGEROUS_VARIABLE_VALUE_PATTERNS', mock_dangerous_patterns):
            # Should not raise for unknown variable when strict=False
            result = parse_sql_variables(
                "SELECT * FROM ${UNKNOWN_VAR}.users",
                {"UNKNOWN_VAR": "value"},
                strict=False
            )
        
        assert result == "SELECT * FROM value.users"

    def test_strict_true_validates_names(self, mock_variable_pattern, mock_allowed_variables, mock_dangerous_patterns):
        """strict=True validates variable names against whitelist."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.VARIABLE_PATTERN', mock_variable_pattern), \
             patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', mock_allowed_variables), \
             patch('tdm_orchestrator.services.parsers.variable_parser.DANGEROUS_VARIABLE_VALUE_PATTERNS', mock_dangerous_patterns):
            with pytest.raises(VariableValidationError):
                parse_sql_variables(
                    "SELECT * FROM ${FORBIDDEN}.users",
                    {"FORBIDDEN": "value"},
                    strict=True
                )

    def test_raises_for_missing_variables(self, mock_variable_pattern, mock_allowed_variables, mock_dangerous_patterns):
        """Raises VariableParsingError for missing variables."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.VARIABLE_PATTERN', mock_variable_pattern), \
             patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', mock_allowed_variables), \
             patch('tdm_orchestrator.services.parsers.variable_parser.DANGEROUS_VARIABLE_VALUE_PATTERNS', mock_dangerous_patterns):
            with pytest.raises(VariableParsingError):
                parse_sql_variables(
                    "SELECT * FROM ${SCHEMA}.users",
                    {},
                    strict=True
                )


# =====================
# Integration Tests
# =====================

class TestVariableParserIntegration:
    """Integration tests for VariableParser."""

    def test_full_workflow_extract_validate_parse(self, mock_variable_pattern, mock_allowed_variables, mock_dangerous_patterns):
        """Full workflow: extract, validate, parse."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.VARIABLE_PATTERN', mock_variable_pattern), \
             patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', mock_allowed_variables), \
             patch('tdm_orchestrator.services.parsers.variable_parser.DANGEROUS_VARIABLE_VALUE_PATTERNS', mock_dangerous_patterns):
            parser = VariableParser(strict_mode=True)
            sql = "SELECT * FROM ${SCHEMA}.${TABLE_NAME} WHERE id = ${USER_ID}"
            
            # Extract
            variables = parser.extract_variables(sql)
            assert variables == ['SCHEMA', 'TABLE_NAME', 'USER_ID']
            
            # Validate
            validation = parser.validate_sql_with_variables(
                sql, 
                {"SCHEMA": "prod", "TABLE_NAME": "users", "USER_ID": "123"}
            )
            assert validation['valid'] is True
            
            # Parse
            result = parser.parse(
                sql, 
                {"SCHEMA": "prod", "TABLE_NAME": "users", "USER_ID": "123"}
            )
            assert result == "SELECT * FROM prod.users WHERE id = 123"

    def test_validation_before_parse_catches_errors(self, mock_variable_pattern, mock_allowed_variables, mock_dangerous_patterns):
        """Validation before parse catches errors early."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.VARIABLE_PATTERN', mock_variable_pattern), \
             patch('tdm_orchestrator.services.parsers.variable_parser.ALLOWED_VARIABLE_NAMES', mock_allowed_variables), \
             patch('tdm_orchestrator.services.parsers.variable_parser.DANGEROUS_VARIABLE_VALUE_PATTERNS', mock_dangerous_patterns):
            parser = VariableParser(strict_mode=True)
            sql = "SELECT * FROM ${SCHEMA}.users"
            
            # Validate first - catches dangerous value
            validation = parser.validate_sql_with_variables(sql, {"SCHEMA": "val; DROP TABLE"})
            assert validation['valid'] is False
            
            # Parse would also raise
            with pytest.raises(VariableValidationError):
                parser.parse(sql, {"SCHEMA": "val; DROP TABLE"})


# =====================
# Edge Cases
# =====================

class TestVariableParserEdgeCases:
    """Edge case tests for VariableParser."""

    def test_variable_at_start_of_sql(self, parser_non_strict):
        """Variable at the very start of SQL."""
        sql = "${SCHEMA}.users"
        result = parser_non_strict.parse(sql, {"SCHEMA": "prod"})
        
        assert result == "prod.users"

    def test_variable_at_end_of_sql(self, parser_non_strict):
        """Variable at the very end of SQL."""
        sql = "SELECT * FROM ${TABLE_NAME}"
        result = parser_non_strict.parse(sql, {"TABLE_NAME": "users"})
        
        assert result == "SELECT * FROM users"

    def test_adjacent_variables(self, parser_non_strict):
        """Two variables adjacent to each other."""
        sql = "${SCHEMA}${TABLE_NAME}"
        result = parser_non_strict.parse(sql, {"SCHEMA": "hello", "TABLE_NAME": "world"})
        
        assert result == "helloworld"

    def test_unicode_in_variable_value(self, parser_non_strict):
        sql = "SELECT * FROM ${SCHEMA}.users WHERE name = '${NAME}'"
        result = parser_non_strict.parse(sql, {"SCHEMA": "schéma", "NAME": "日本語"})
        
        assert "schéma" in result
        assert "日本語" in result

    def test_very_long_variable_value(self, parser_non_strict):
        """Very long variable value."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        long_value = "x" * 10000
        result = parser_non_strict.parse(sql, {"SCHEMA": long_value})
        
        assert result == f"SELECT * FROM {long_value}.users"

    def test_sql_with_only_variables(self, mock_variable_pattern, mock_dangerous_patterns):
        """SQL containing only variables."""
        with patch('tdm_orchestrator.services.parsers.variable_parser.VARIABLE_PATTERN', mock_variable_pattern), \
             patch('tdm_orchestrator.services.parsers.variable_parser.DANGEROUS_VARIABLE_VALUE_PATTERNS', mock_dangerous_patterns):
            sql = "${VAR1}${VAR2}${VAR3}"
            result = parse_sql_variables(sql, {"VAR1": "A", "VAR2": "B", "VAR3": "C"}, strict=False)
            
            assert result == "ABC"
    
    def test_very_long_variable_value(self, parser_non_strict):
        """Very long variable value."""
        sql = "SELECT * FROM ${SCHEMA}.users"
        long_value = "x" * 10000
        result = parser_non_strict.parse(sql, {"SCHEMA": long_value})
        
        assert result == f"SELECT * FROM {long_value}.users"

#   - Empty allowed_variables set
#
# - extract_variables:
#   - Empty string returns empty list
#   - None returns empty list
#   - No variables returns empty list
#   - Single variable extraction
#   - Multiple variables extraction
#   - Duplicate variables deduplicated
#   - Order preserved
#   - Multiline SQL
#   - Whitespace-only content
#
# - validate_variable_name:
#   - Returns True in non-strict mode
#   - Returns True for allowed variable strict mode
#   - Raises error for non-allowed variable
#   - Error message contains allowed list
#   - Empty variable name not allowed
#
# - validate_variable_value:
#   - Returns safe string value
#   - Converts non-string to string
#   - Raises error for DROP injection
#   - Raises error for DELETE injection
#   - Raises error for -- comment
#   - Raises error for /* */ comment
#   - Safe value with spaces/special chars
#   - Case insensitive danger detection
#
# - parse:
#   - Empty content returns empty
#   - None content returns None
#   - No variables needed unchanged
#   - Single/multiple variable substitution
#   - Same variable multiple occurrences
#   - Raises error for missing variables
#   - Raises error when none provided but needed
#   - Empty dict OK when no variables needed
#   - Extra variables ignored
#   - strict_validation validates names/values
#   - strict_validation=False skips validation
#   - Multiline SQL parsing
#
# - get_missing_variables:
#   - Empty when all provided
#   - Returns missing variables
#   - All missing when none provided
#   - Empty when no variables needed
#   - Preserves order
#
# - validate_sql_with_variables:
#   - Valid SQL returns valid=True
#   - Returns required/provided/missing variables
#   - Missing variables returns valid=False
#   - Dangerous value returns valid=False
#   - Non-allowed variable strict mode
#   - Extra variables produce warnings
#   - Multiple errors accumulated
#   - Handles exceptions gracefully
#
# - Utility functions:
#   - extract_sql_variables uses non-strict mode
#   - parse_sql_variables with strict flag
#
# - Integration:
#   - Full workflow extract-validate-parse
#   - Validation catches errors before parse
#
#   - Edge cases:
#   - Variable at start/end of SQL
#   - Adjacent variables
#   - Empty string value
#   - Newlines/unicode in value
#   - Very long value
#   - SQL with only variables
#   - Case sensitivity
#   - Dollar sign in value not expanded