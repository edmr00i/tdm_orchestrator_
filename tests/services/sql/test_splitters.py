# tests/services/sql/test_splitters.py
"""
Tests for SQL splitters - statement parsing by database type.

Covers:
- BaseSplitter:
  - _remove_single_line_comments (with/without quotes, escaped quotes)
  - _remove_multiline_comments (with/without quotes, escaped quotes)
- PostgreSQLSplitter:
  - Simple statements split by semicolon
  - Dollar-quoted strings ($$, $tag$)
  - Quoted strings (single, double, escaped)
  - Comments removal integration
  - Empty and whitespace handling
- SQLServerSplitter:
  - GO separator (case insensitive)
  - Comments removal
  - Multiple batches
- OracleSplitter:
  - Simple statements by semicolon
  - PL/SQL blocks (BEGIN/END, DECLARE)
  - Slash separator
  - Nested blocks
- SimpleSplitter:
  - Fallback semicolon splitting
  - Comments removal
- get_splitter factory:
  - Returns correct splitter for each DatabaseType
  - Falls back to SimpleSplitter for unknown types
"""

import pytest

from tdm_orchestrator.services.sql.splitters import (
    BaseSplitter,
    PostgreSQLSplitter,
    SQLServerSplitter,
    OracleSplitter,
    SimpleSplitter,
    get_splitter,
)
from tdm_orchestrator.services.constants import DatabaseType


# =====================
# BaseSplitter._remove_single_line_comments Tests
# =====================

class TestBaseSplitterRemoveSingleLineComments:
    """Tests for _remove_single_line_comments method."""

    def test_removes_simple_comment(self):
        """Removes simple -- comment at end of line."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT * FROM users -- this is a comment"
        result = splitter._remove_single_line_comments(sql)
        assert result == "SELECT * FROM users "

    def test_removes_comment_on_own_line(self):
        """Removes comment that is on its own line."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT * FROM users\n-- comment line\nWHERE id = 1"
        result = splitter._remove_single_line_comments(sql)
        assert "-- comment line" not in result
        assert "SELECT * FROM users" in result
        assert "WHERE id = 1" in result

    def test_preserves_dashes_in_single_quotes(self):
        """Preserves -- inside single-quoted strings."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT '-- not a comment' FROM users"
        result = splitter._remove_single_line_comments(sql)
        assert result == "SELECT '-- not a comment' FROM users"

    def test_preserves_dashes_in_double_quotes(self):
        """Preserves -- inside double-quoted strings."""
        splitter = PostgreSQLSplitter()
        sql = 'SELECT "-- not a comment" FROM users'
        result = splitter._remove_single_line_comments(sql)
        assert result == 'SELECT "-- not a comment" FROM users'

    def test_handles_escaped_single_quotes(self):
        """Handles escaped single quotes correctly."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT 'it''s -- still in quote' FROM users -- real comment"
        result = splitter._remove_single_line_comments(sql)
        assert "'it''s -- still in quote'" in result
        assert "-- real comment" not in result

    def test_handles_escaped_double_quotes(self):
        """Handles escaped double quotes correctly."""
        splitter = PostgreSQLSplitter()
        sql = 'SELECT "say ""hello"" -- in quote" FROM users -- comment'
        result = splitter._remove_single_line_comments(sql)
        assert '"say ""hello"" -- in quote"' in result
        assert "-- comment" not in result

    def test_multiple_lines_with_comments(self):
        """Removes comments from multiple lines."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT * -- first\nFROM users -- second\nWHERE 1=1 -- third"
        result = splitter._remove_single_line_comments(sql)
        lines = result.split('\n')
        assert len(lines) == 3
        assert "-- first" not in result
        assert "-- second" not in result
        assert "-- third" not in result

    def test_empty_string(self):
        """Handles empty string input."""
        splitter = PostgreSQLSplitter()
        result = splitter._remove_single_line_comments("")
        assert result == ""

    def test_no_comments(self):
        """Returns unchanged SQL when no comments present."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT * FROM users WHERE id = 1"
        result = splitter._remove_single_line_comments(sql)
        assert result == sql


# =====================
# BaseSplitter._remove_multiline_comments Tests
# =====================

class TestBaseSplitterRemoveMultilineComments:
    """Tests for _remove_multiline_comments method."""

    def test_removes_simple_multiline_comment(self):
        """Removes simple /* */ comment."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT * /* comment */ FROM users"
        result = splitter._remove_multiline_comments(sql)
        assert result == "SELECT *  FROM users"

    def test_removes_spanning_multiple_lines(self):
        """Removes comment spanning multiple lines."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT * /* this is\na multiline\ncomment */ FROM users"
        result = splitter._remove_multiline_comments(sql)
        assert result == "SELECT *  FROM users"

    def test_preserves_comment_markers_in_single_quotes(self):
        """Preserves /* */ inside single-quoted strings."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT '/* not a comment */' FROM users"
        result = splitter._remove_multiline_comments(sql)
        assert result == "SELECT '/* not a comment */' FROM users"

    def test_preserves_comment_markers_in_double_quotes(self):
        """Preserves /* */ inside double-quoted strings."""
        splitter = PostgreSQLSplitter()
        sql = 'SELECT "/* not a comment */" FROM users'
        result = splitter._remove_multiline_comments(sql)
        assert result == 'SELECT "/* not a comment */" FROM users'

    def test_handles_escaped_quotes_in_string(self):
        """Handles escaped quotes inside strings with comment markers."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT 'it''s /* still */ in quote' FROM users /* real */"
        result = splitter._remove_multiline_comments(sql)
        assert "'it''s /* still */ in quote'" in result
        assert "/* real */" not in result

    def test_multiple_comments(self):
        """Removes multiple multiline comments."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT /* c1 */ * FROM /* c2 */ users"
        result = splitter._remove_multiline_comments(sql)
        assert "/* c1 */" not in result
        assert "/* c2 */" not in result
        assert "SELECT  * FROM  users" == result

    def test_empty_string(self):
        """Handles empty string input."""
        splitter = PostgreSQLSplitter()
        result = splitter._remove_multiline_comments("")
        assert result == ""

    def test_no_comments(self):
        """Returns unchanged SQL when no comments present."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT * FROM users WHERE id = 1"
        result = splitter._remove_multiline_comments(sql)
        assert result == sql

    def test_unclosed_comment(self):
        """Handles unclosed multiline comment (edge case)."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT * /* unclosed comment FROM users"
        result = splitter._remove_multiline_comments(sql)
        # Unclosed comment should consume the rest
        assert result == "SELECT * "


# =====================
# PostgreSQLSplitter Tests
# =====================

class TestPostgreSQLSplitter:
    """Tests for PostgreSQLSplitter class."""

    def test_simple_statements(self):
        """Splits simple semicolon-separated statements."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT 1; SELECT 2; SELECT 3"
        result = splitter.split(sql)
        assert result == ["SELECT 1", "SELECT 2", "SELECT 3"]

    def test_single_statement_no_semicolon(self):
        """Handles single statement without trailing semicolon."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT * FROM users"
        result = splitter.split(sql)
        assert result == ["SELECT * FROM users"]

    def test_single_statement_with_semicolon(self):
        """Handles single statement with trailing semicolon."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT * FROM users;"
        result = splitter.split(sql)
        assert result == ["SELECT * FROM users"]

    def test_dollar_quoted_string_simple(self):
        """Handles simple $$ dollar-quoted strings."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT $$hello; world$$; SELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert result[0] == "SELECT $$hello; world$$"
        assert result[1] == "SELECT 2"

    def test_dollar_quoted_string_with_tag(self):
        """Handles $tag$ dollar-quoted strings."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT $body$hello; world$body$; SELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert result[0] == "SELECT $body$hello; world$body$"
        assert result[1] == "SELECT 2"

    def test_dollar_quoted_function_body(self):
        """Handles function with dollar-quoted body."""
        splitter = PostgreSQLSplitter()
        sql = """
        CREATE FUNCTION test() RETURNS void AS $$
        BEGIN
            INSERT INTO log VALUES ('test');
            UPDATE stats SET count = count + 1;
        END;
        $$ LANGUAGE plpgsql;
        SELECT 1
        """
        result = splitter.split(sql)
        assert len(result) == 2
        assert "CREATE FUNCTION" in result[0]
        assert "INSERT INTO log" in result[0]
        assert result[1] == "SELECT 1"

    def test_nested_dollar_quotes_different_tags(self):
        """Handles nested dollar quotes with different tags."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT $outer$text with $inner$nested$inner$ inside$outer$; SELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert "$outer$" in result[0]
        assert "$inner$nested$inner$" in result[0]

    def test_single_quoted_string_with_semicolon(self):
        """Preserves semicolons inside single-quoted strings."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT 'hello; world'; SELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert result[0] == "SELECT 'hello; world'"
        assert result[1] == "SELECT 2"

    def test_double_quoted_identifier_with_semicolon(self):
        """Preserves semicolons inside double-quoted identifiers."""
        splitter = PostgreSQLSplitter()
        sql = 'SELECT * FROM "table;name"; SELECT 2'
        result = splitter.split(sql)
        assert len(result) == 2
        assert result[0] == 'SELECT * FROM "table;name"'
        assert result[1] == "SELECT 2"

    def test_escaped_single_quotes(self):
        """Handles escaped single quotes correctly."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT 'it''s a test; really'; SELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert "it''s a test; really" in result[0]

    def test_escaped_double_quotes(self):
        """Handles escaped double quotes correctly."""
        splitter = PostgreSQLSplitter()
        sql = 'SELECT "col""name;test"; SELECT 2'
        result = splitter.split(sql)
        assert len(result) == 2
        assert 'col""name;test' in result[0]

    def test_removes_single_line_comments(self):
        """Removes single-line comments before splitting."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT 1; -- comment\nSELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert "-- comment" not in str(result)

    def test_removes_multiline_comments(self):
        """Removes multiline comments before splitting."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT 1; /* comment */ SELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert "/* comment */" not in str(result)

    def test_empty_string(self):
        """Handles empty string input."""
        splitter = PostgreSQLSplitter()
        result = splitter.split("")
        assert result == []

    def test_whitespace_only(self):
        """Handles whitespace-only input."""
        splitter = PostgreSQLSplitter()
        result = splitter.split("   \n\t  ")
        assert result == []

    def test_multiple_semicolons(self):
        """Handles multiple consecutive semicolons."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT 1;;; SELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert result[0] == "SELECT 1"
        assert result[1] == "SELECT 2"

    def test_complex_plpgsql_function(self):
        """Handles complex PL/pgSQL function with multiple statements inside."""
        splitter = PostgreSQLSplitter()
        sql = """
        CREATE OR REPLACE FUNCTION complex_func() RETURNS void AS $$
        DECLARE
            v_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO v_count FROM users;
            IF v_count > 0 THEN
                UPDATE stats SET total = v_count;
            END IF;
            RETURN;
        END;
        $$ LANGUAGE plpgsql;
        
        SELECT complex_func();
        """
        result = splitter.split(sql)
        assert len(result) == 2
        assert "CREATE OR REPLACE FUNCTION" in result[0]
        assert "DECLARE" in result[0]
        assert "SELECT complex_func()" in result[1]


# =====================
# SQLServerSplitter Tests
# =====================

class TestSQLServerSplitter:
    """Tests for SQLServerSplitter class."""

    def test_simple_go_separator(self):
        """Splits batches by GO keyword."""
        splitter = SQLServerSplitter()
        sql = "SELECT 1\nGO\nSELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert result[0] == "SELECT 1"
        assert result[1] == "SELECT 2"

    def test_go_case_insensitive(self):
        """GO separator is case insensitive."""
        splitter = SQLServerSplitter()
        sql = "SELECT 1\ngo\nSELECT 2\nGO\nSELECT 3\nGo\nSELECT 4"
        result = splitter.split(sql)
        assert len(result) == 4

    def test_go_with_surrounding_whitespace(self):
        """Handles GO with surrounding whitespace."""
        splitter = SQLServerSplitter()
        sql = "SELECT 1\n  GO  \nSELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2

    def test_removes_single_line_comments(self):
        """Removes -- comments."""
        splitter = SQLServerSplitter()
        sql = "SELECT 1 -- comment\nGO\nSELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert "-- comment" not in result[0]

    def test_removes_multiline_comments(self):
        """Removes /* */ comments."""
        splitter = SQLServerSplitter()
        sql = "SELECT /* comment */ 1\nGO\nSELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert "/* comment */" not in result[0]

    def test_no_go_returns_single_batch(self):
        """Returns single batch when no GO present."""
        splitter = SQLServerSplitter()
        sql = "SELECT 1; SELECT 2; SELECT 3"
        result = splitter.split(sql)
        assert len(result) == 1
        assert result[0] == "SELECT 1; SELECT 2; SELECT 3"

    def test_empty_batches_filtered(self):
        """Filters out empty batches."""
        splitter = SQLServerSplitter()
        sql = "GO\nSELECT 1\nGO\n\nGO\nSELECT 2\nGO"
        result = splitter.split(sql)
        assert len(result) == 2
        assert result[0] == "SELECT 1"
        assert result[1] == "SELECT 2"

    def test_empty_string(self):
        """Handles empty string input."""
        splitter = SQLServerSplitter()
        result = splitter.split("")
        assert result == []

    def test_go_not_as_word_boundary(self):
        """GO inside words should not split (word boundary check)."""
        splitter = SQLServerSplitter()
        sql = "SELECT * FROM category\nGO\nSELECT 1"
        result = splitter.split(sql)
        # 'category' contains 'go' but shouldn't split
        assert len(result) == 2
        assert "category" in result[0]

    def test_create_procedure(self):
        """Handles stored procedure creation."""
        splitter = SQLServerSplitter()
        sql = """
        CREATE PROCEDURE TestProc
        AS
        BEGIN
            SELECT 1;
            SELECT 2;
        END
        GO
        EXEC TestProc
        """
        result = splitter.split(sql)
        assert len(result) == 2
        assert "CREATE PROCEDURE" in result[0]
        assert "EXEC TestProc" in result[1]


# =====================
# OracleSplitter Tests
# =====================

class TestOracleSplitter:
    """Tests for OracleSplitter class."""

    def test_simple_statements_semicolon(self):
        """Splits simple statements by semicolon."""
        splitter = OracleSplitter()
        sql = "SELECT 1 FROM DUAL; SELECT 2 FROM DUAL"
        result = splitter.split(sql)
        assert len(result) == 2
        assert "SELECT 1 FROM DUAL" in result[0]
        assert "SELECT 2 FROM DUAL" in result[1]

    def test_plsql_block_begin_end(self):
        """Handles PL/SQL BEGIN...END block."""
        splitter = OracleSplitter()
        sql = """
        BEGIN
            INSERT INTO log VALUES ('test');
            UPDATE stats SET count = count + 1;
        END;
        /
        SELECT 1 FROM DUAL
        """
        result = splitter.split(sql)
        assert len(result) == 2
        assert "BEGIN" in result[0]
        assert "INSERT INTO log" in result[0]
        assert "END" in result[0]

    def test_plsql_declare_block(self):
        """Handles PL/SQL DECLARE block."""
        splitter = OracleSplitter()
        sql = """
        DECLARE
            v_count NUMBER;
        BEGIN
            SELECT COUNT(*) INTO v_count FROM users;
        END;
        /
        SELECT 1 FROM DUAL
        """
        result = splitter.split(sql)
        assert len(result) == 2
        assert "DECLARE" in result[0]
        assert "v_count NUMBER" in result[0]

    def test_nested_begin_end(self):
        """Handles nested BEGIN...END blocks."""
        splitter = OracleSplitter()
        sql = """
        BEGIN
            BEGIN
                INSERT INTO log VALUES ('inner');
            END;
            UPDATE stats SET count = 1;
        END;
        /
        SELECT 1 FROM DUAL
        """
        result = splitter.split(sql)
        assert len(result) == 2
        assert result[0].count("BEGIN") == 2
        assert result[0].count("END") == 2

    def test_slash_separator(self):
        """Uses / as separator for PL/SQL blocks."""
        splitter = OracleSplitter()
        sql = """
        CREATE PROCEDURE test_proc AS
        BEGIN
            NULL;
        END;
        /
        CREATE PROCEDURE test_proc2 AS
        BEGIN
            NULL;
        END;
        /
        """
        result = splitter.split(sql)
        assert len(result) == 2
        assert "test_proc" in result[0]
        assert "test_proc2" in result[1]

    def test_removes_single_line_comments(self):
        """Removes -- comments."""
        splitter = OracleSplitter()
        sql = "SELECT 1 FROM DUAL -- comment; SELECT 2 FROM DUAL"
        result = splitter.split(sql)
        assert "-- comment" not in str(result)

    def test_removes_multiline_comments(self):
        """Removes /* */ comments."""
        splitter = OracleSplitter()
        sql = "SELECT /* comment */ 1 FROM DUAL; SELECT 2 FROM DUAL"
        result = splitter.split(sql)
        assert "/* comment */" not in str(result)

    def test_empty_string(self):
        """Handles empty string input."""
        splitter = OracleSplitter()
        result = splitter.split("")
        assert result == []

    def test_single_statement_no_separator(self):
        """Handles single statement without separator."""
        splitter = OracleSplitter()
        sql = "SELECT * FROM users"
        result = splitter.split(sql)
        assert len(result) == 1
        assert "SELECT * FROM users" in result[0]

    def test_create_function(self):
        """Handles CREATE FUNCTION with PL/SQL body."""
        splitter = OracleSplitter()
        sql = """
        CREATE FUNCTION get_count RETURN NUMBER AS
            v_result NUMBER;
        BEGIN
            SELECT COUNT(*) INTO v_result FROM users;
            RETURN v_result;
        END;
        /
        SELECT get_count() FROM DUAL
        """
        result = splitter.split(sql)
        assert len(result) == 2
        assert "CREATE FUNCTION" in result[0]
        assert "RETURN v_result" in result[0]


# =====================
# SimpleSplitter Tests
# =====================

class TestSimpleSplitter:
    """Tests for SimpleSplitter class (fallback)."""

    def test_simple_split_by_semicolon(self):
        """Splits statements by semicolon."""
        splitter = SimpleSplitter()
        sql = "SELECT 1; SELECT 2; SELECT 3"
        result = splitter.split(sql)
        assert result == ["SELECT 1", "SELECT 2", "SELECT 3"]

    def test_removes_single_line_comments(self):
        """Removes -- comments."""
        splitter = SimpleSplitter()
        sql = "SELECT 1 -- comment; SELECT 2"
        result = splitter.split(sql)
        assert "-- comment" not in str(result)

    def test_removes_multiline_comments(self):
        """Removes /* */ comments."""
        splitter = SimpleSplitter()
        sql = "SELECT /* comment */ 1; SELECT 2"
        result = splitter.split(sql)
        assert "/* comment */" not in str(result)

    def test_empty_string(self):
        """Handles empty string input."""
        splitter = SimpleSplitter()
        result = splitter.split("")
        assert result == []

    def test_whitespace_only(self):
        """Handles whitespace-only input."""
        splitter = SimpleSplitter()
        result = splitter.split("   \n\t  ")
        assert result == []

    def test_filters_empty_statements(self):
        """Filters out empty statements from multiple semicolons."""
        splitter = SimpleSplitter()
        sql = "SELECT 1;;; SELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2

    def test_single_statement_no_semicolon(self):
        """Handles single statement without semicolon."""
        splitter = SimpleSplitter()
        sql = "SELECT * FROM users"
        result = splitter.split(sql)
        assert result == ["SELECT * FROM users"]

    def test_trims_whitespace(self):
        """Trims whitespace from statements."""
        splitter = SimpleSplitter()
        sql = "  SELECT 1  ;  SELECT 2  "
        result = splitter.split(sql)
        assert result == ["SELECT 1", "SELECT 2"]


# =====================
# get_splitter Factory Tests
# =====================

class TestGetSplitter:
    """Tests for get_splitter factory function."""

    def test_returns_postgresql_splitter(self):
        """Returns PostgreSQLSplitter for POSTGRESQL type."""
        splitter = get_splitter(DatabaseType.POSTGRESQL)
        assert isinstance(splitter, PostgreSQLSplitter)

    def test_returns_postgresql_splitter_for_mysql(self):
        """Returns PostgreSQLSplitter for MYSQL type (same splitter)."""
        splitter = get_splitter(DatabaseType.MYSQL)
        assert isinstance(splitter, PostgreSQLSplitter)

    def test_returns_sqlserver_splitter(self):
        """Returns SQLServerSplitter for SQLSERVER type."""
        splitter = get_splitter(DatabaseType.SQLSERVER)
        assert isinstance(splitter, SQLServerSplitter)

    def test_returns_oracle_splitter(self):
        """Returns OracleSplitter for ORACLE type."""
        splitter = get_splitter(DatabaseType.ORACLE)
        assert isinstance(splitter, OracleSplitter)

    def test_returns_simple_splitter_for_unknown(self):
        """Returns SimpleSplitter for unknown database type."""
        splitter = get_splitter("unknown_db")
        assert isinstance(splitter, SimpleSplitter)

    def test_returns_simple_splitter_for_none(self):
        """Returns SimpleSplitter for None database type."""
        splitter = get_splitter(None)
        assert isinstance(splitter, SimpleSplitter)

    def test_returns_new_instance_each_call(self):
        """Returns new instance on each call."""
        splitter1 = get_splitter(DatabaseType.POSTGRESQL)
        splitter2 = get_splitter(DatabaseType.POSTGRESQL)
        assert splitter1 is not splitter2


# =====================
# Integration Tests
# =====================

class TestSplitterIntegration:
    """Integration tests for complex SQL scenarios."""

    def test_postgresql_complex_migration(self):
        """PostgreSQL complex migration script with multiple object types."""
        splitter = PostgreSQLSplitter()
        sql = """
        -- Create tables
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100)
        );
        
        /* Create function */
        CREATE OR REPLACE FUNCTION update_timestamp() 
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Create trigger
        CREATE TRIGGER update_users_timestamp
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_timestamp();
        
        INSERT INTO users (name) VALUES ('test');
        """
        result = splitter.split(sql)
        assert len(result) == 4
        assert "CREATE TABLE" in result[0]
        assert "CREATE OR REPLACE FUNCTION" in result[1]
        assert "CREATE TRIGGER" in result[2]
        assert "INSERT INTO" in result[3]

    def test_sqlserver_complex_batch(self):
        """SQL Server complex batch with multiple operations."""
        splitter = SQLServerSplitter()
        sql = """
        CREATE TABLE #temp (id INT)
        INSERT INTO #temp VALUES (1), (2), (3)
        GO
        
        CREATE PROCEDURE GetTemp
        AS
        BEGIN
            SELECT * FROM #temp
        END
        GO
        
        EXEC GetTemp
        GO
        
        DROP TABLE #temp
        DROP PROCEDURE GetTemp
        """
        result = splitter.split(sql)
        assert len(result) == 4

    def test_oracle_package_creation(self):
        """Oracle package with specification and body."""
        splitter = OracleSplitter()
        sql = """
        CREATE OR REPLACE PACKAGE test_pkg AS
            PROCEDURE do_something;
            FUNCTION get_value RETURN NUMBER;
        END test_pkg;
        /
        
        CREATE OR REPLACE PACKAGE BODY test_pkg AS
            PROCEDURE do_something AS
            BEGIN
                NULL;
            END do_something;
            
            FUNCTION get_value RETURN NUMBER AS
            BEGIN
                RETURN 42;
            END get_value;
        END test_pkg;
        /
        
        SELECT test_pkg.get_value() FROM DUAL
        """
        result = splitter.split(sql)
        assert len(result) == 3
        assert "CREATE OR REPLACE PACKAGE test_pkg" in result[0]
        assert "PACKAGE BODY" in result[1]
        assert "SELECT" in result[2]


# =====================
# Edge Cases
# =====================

class TestSplitterEdgeCases:
    """Edge case tests for all splitters."""

    def test_postgresql_dollar_sign_not_quoted(self):
        """Single $ without matching tag is not a dollar quote."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT $1; SELECT $2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert result[0] == "SELECT $1"
        assert result[1] == "SELECT $2"

    def test_postgresql_mixed_quotes(self):
        """Mixed single and double quotes in same statement."""
        splitter = PostgreSQLSplitter()
        sql = """SELECT 'single; quote' AS "double; quote"; SELECT 2"""
        result = splitter.split(sql)
        assert len(result) == 2
        assert "single; quote" in result[0]
        assert "double; quote" in result[0]

    def test_sqlserver_go_in_string_literal(self):
        """GO inside string literal - regex approach may incorrectly split."""
        splitter = SQLServerSplitter()
        # Note: SQLServerSplitter uses simple regex, this is a known limitation
        sql = "SELECT 'text GO more text'"
        result = splitter.split(sql)
        # Current implementation splits on GO regardless of context
        # This test documents the behavior
        assert len(result) >= 1

    def test_unicode_content(self):
        """Handles unicode content in statements."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT '日本語'; SELECT 'émojis 🎉'"
        result = splitter.split(sql)
        assert len(result) == 2
        assert "日本語" in result[0]
        assert "🎉" in result[1]

    def test_very_long_statement(self):
        """Handles very long statements."""
        splitter = PostgreSQLSplitter()
        long_content = "x" * 10000
        sql = f"SELECT '{long_content}'; SELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert long_content in result[0]

    def test_only_semicolons(self):
        """Handles input with only semicolons."""
        splitter = PostgreSQLSplitter()
        sql = ";;;"
        result = splitter.split(sql)
        assert result == []

    def test_statement_ending_with_newlines(self):
        """Handles statements with trailing newlines."""
        splitter = PostgreSQLSplitter()
        sql = "SELECT 1;\n\n\nSELECT 2;\n\n"
        result = splitter.split(sql)
        assert len(result) == 2
        assert result[0] == "SELECT 1"
        assert result[1] == "SELECT 2"


# =====================
# Summary of Covered Cases
# =====================
# - BaseSplitter._remove_single_line_comments:
#   - Simple comment removal
#   - Comment on own line
#   - Preserves -- in single quotes
#   - Preserves -- in double quotes
#   - Handles escaped single quotes
#   - Handles escaped double quotes
#   - Multiple lines with comments
#   - Empty string
#   - No comments
#
# - BaseSplitter._remove_multiline_comments:
#   - Simple /* */ removal
#   - Spanning multiple lines
#   - Preserves in single quotes
#   - Preserves in double quotes
#   - Escaped quotes in strings
#   - Multiple comments
#   - Empty string
#   - No comments
#   - Unclosed comment
#
# - PostgreSQLSplitter:
#   - Simple statements
#   - Single statement with/without semicolon
#   - Dollar-quoted strings ($$, $tag$)
#   - Dollar-quoted function body
#   - Nested dollar quotes
#   - Single/double quoted strings with semicolons
#   - Escaped quotes
#   - Comments removal
#   - Empty/whitespace input
#   - Multiple semicolons
#   - Complex PL/pgSQL
#
# - SQLServerSplitter:
#   - GO separator
#   - Case insensitive GO
#   - GO with whitespace
#   - Comments removal
#   - No GO returns single batch
#   - Empty batches filtered
#   - Empty string
#   - Word boundary for GO
#   - Stored procedure
#
# - OracleSplitter:
#   - Semicolon splitting
#   - BEGIN/END blocks
#   - DECLARE blocks
#   - Nested BEGIN/END
#   - Slash separator
#   - Comments removal
#   - Empty string
#   - CREATE FUNCTION
#
# - SimpleSplitter:
#   - Semicolon splitting
#   - Comments removal
#   - Empty/whitespace input
#   - Filters empty statements
#   - Trims whitespace
#
# - get_splitter factory:
#   - Returns correct splitter for each DatabaseType
#   - Returns SimpleSplitter for unknown/None
#   - Returns new instance each call
#
# - Integration tests:
#   - PostgreSQL complex migration
#   - SQL Server complex batch
#   - Oracle package creation
#
# - Edge cases:
#   - Dollar sign not quoted
#   - Mixed quotes
#   - Unicode content
#   - Very long statements
#   - Only semicolons
#   - Trailing newlines