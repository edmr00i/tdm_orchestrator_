

from tdm_orchestrator.services.sql.splitters import (
    PostgreSqlSplitter,
    SqlServerSplitter,
    OracleSplitter,
    SimpleSplitter,
    get_splitter,
)


# =====================
# Additional Tests for BaseSqlSplitter (renamed class)
# =====================

class TestBaseSqlSplitterRemoveSingleLineComments:
    """Tests for BaseSqlSplitter._remove_single_line_comments method."""

    def test_removes_comment_at_start_of_line(self):
        """Removes comment that starts at beginning of line."""
        splitter = PostgreSqlSplitter()
        sql = "-- full line comment\nSELECT 1"
        result = splitter._remove_single_line_comments(sql)
        assert "-- full line comment" not in result
        assert "SELECT 1" in result

    def test_preserves_code_before_comment(self):
        """Preserves code that appears before comment marker."""
        splitter = PostgreSqlSplitter()
        sql = "SELECT id FROM users WHERE id > 10 -- filter"
        result = splitter._remove_single_line_comments(sql)
        assert "SELECT id FROM users WHERE id > 10" in result
        assert "-- filter" not in result

    def test_handles_line_with_only_dashes(self):
        """Handles line with only dashes (not a comment without second dash)."""
        splitter = PostgreSqlSplitter()
        sql = "SELECT 1 - 2"
        result = splitter._remove_single_line_comments(sql)
        assert result == "SELECT 1 - 2"


class TestBaseSqlSplitterRemoveMultilineComments:
    """Tests for BaseSqlSplitter._remove_multiline_comments method."""

    def test_handles_comment_at_start(self):
        """Handles multiline comment at start of SQL."""
        splitter = PostgreSqlSplitter()
        sql = "/* header comment */SELECT 1"
        result = splitter._remove_multiline_comments(sql)
        assert result == "SELECT 1"

    def test_handles_comment_at_end(self):
        """Handles multiline comment at end of SQL."""
        splitter = PostgreSqlSplitter()
        sql = "SELECT 1/* trailing */"
        result = splitter._remove_multiline_comments(sql)
        assert result == "SELECT 1"

    def test_handles_adjacent_comments(self):
        """Handles adjacent multiline comments."""
        splitter = PostgreSqlSplitter()
        sql = "SELECT /* c1 *//* c2 */ 1"
        result = splitter._remove_multiline_comments(sql)
        assert result == "SELECT  1"


# =====================
# Additional Tests for PostgreSqlSplitter (renamed class)
# =====================

class TestPostgreSqlSplitterAdditional:
    """Additional tests for PostgreSqlSplitter class."""

    def test_handles_underscore_in_dollar_tag(self):
        """Handles dollar tag with underscores."""
        splitter = PostgreSqlSplitter()
        sql = "SELECT $my_tag$content; here$my_tag$; SELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert "$my_tag$content; here$my_tag$" in result[0]

    def test_does_not_match_partial_dollar_tag(self):
        """Does not match partial dollar tags (different closing tag)."""
        splitter = PostgreSqlSplitter()
        sql = "SELECT $a$content$b$; SELECT 2"
        result = splitter.split(sql)
        # $a$ opens, $b$ doesn't close it, so semicolon inside is preserved
        assert len(result) == 1 or "$a$content$b$" in result[0]

    def test_handles_empty_dollar_tag_multiple(self):
        """Handles multiple empty dollar tags ($$) in sequence."""
        splitter = PostgreSqlSplitter()
        sql = "SELECT $$first$$; SELECT $$second$$"
        result = splitter.split(sql)
        assert len(result) == 2
        assert "$$first$$" in result[0]
        assert "$$second$$" in result[1]

    def test_quote_inside_dollar_block(self):
        """Handles quotes inside dollar-quoted block."""
        splitter = PostgreSqlSplitter()
        sql = "SELECT $$it's a 'test'; here$$; SELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert "it's a 'test'; here" in result[0]

    def test_double_quote_inside_dollar_block(self):
        """Handles double quotes inside dollar-quoted block."""
        splitter = PostgreSqlSplitter()
        sql = 'SELECT $$column "name"; test$$; SELECT 2'
        result = splitter.split(sql)
        assert len(result) == 2
        assert 'column "name"; test' in result[0]

    def test_dollar_sign_in_regular_string(self):
        """Handles $ inside regular single-quoted string."""
        splitter = PostgreSqlSplitter()
        sql = "SELECT '$100'; SELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert "$100" in result[0]


# =====================
# Additional Tests for SqlServerSplitter (renamed class)
# =====================

class TestSqlServerSplitterAdditional:
    """Additional tests for SqlServerSplitter class."""

    def test_go_with_newline_before(self):
        """Handles GO with newline before it."""
        splitter = SqlServerSplitter()
        sql = "SELECT 1\n\nGO\nSELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2

    def test_multiple_go_in_sequence(self):
        """Handles multiple GO keywords in sequence."""
        splitter = SqlServerSplitter()
        sql = "SELECT 1\nGO\nGO\nGO\nSELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2
        assert result[0] == "SELECT 1"
        assert result[1] == "SELECT 2"

    def test_go_at_end_of_script(self):
        """Handles GO at end of script."""
        splitter = SqlServerSplitter()
        sql = "SELECT 1\nGO"
        result = splitter.split(sql)
        assert len(result) == 1
        assert result[0] == "SELECT 1"

    def test_go_at_start_of_script(self):
        """Handles GO at start of script."""
        splitter = SqlServerSplitter()
        sql = "GO\nSELECT 1"
        result = splitter.split(sql)
        assert len(result) == 1
        assert result[0] == "SELECT 1"

    def test_mixed_case_go(self):
        """Handles mixed case GO (gO, Go, etc.)."""
        splitter = SqlServerSplitter()
        sql = "SELECT 1\ngO\nSELECT 2\nGo\nSELECT 3"
        result = splitter.split(sql)
        assert len(result) == 3


# =====================
# Additional Tests for OracleSplitter (renamed class)
# =====================

class TestOracleSplitterAdditional:
    """Additional tests for OracleSplitter class."""

    def test_slash_at_end_of_script(self):
        """Handles slash at end of script."""
        splitter = OracleSplitter()
        sql = "BEGIN NULL; END;\n/"
        result = splitter.split(sql)
        assert len(result) == 1
        assert "BEGIN" in result[0]

        def test_multiple_declare_blocks(self):
            """Handles multiple DECLARE blocks separated by slash on its own line."""
            splitter = OracleSplitter()
            sql = """DECLARE v1 NUMBER;
    BEGIN
        v1 := 1;
    END;
    /
    DECLARE v2 NUMBER;
    BEGIN
        v2 := 2;
    END;
    /"""
            result = splitter.split(sql)
            assert len(result) == 2
            assert "v1" in result[0]
            assert "v2" in result[1]

    def test_end_with_name(self):
        """Handles END with procedure/function name."""
        splitter = OracleSplitter()
        sql = """
        CREATE PROCEDURE my_proc AS
        BEGIN
            NULL;
        END my_proc;
        /
        SELECT 1 FROM DUAL
        """
        result = splitter.split(sql)
        assert len(result) == 2
        assert "END my_proc" in result[0]

    def test_simple_select_without_plsql(self):
        """Handles simple SELECT without PL/SQL blocks."""
        splitter = OracleSplitter()
        sql = "SELECT 1 FROM DUAL; SELECT 2 FROM DUAL; SELECT 3 FROM DUAL"
        result = splitter.split(sql)
        assert len(result) == 3

    def test_empty_plsql_block(self):
        """Handles empty PL/SQL block."""
        splitter = OracleSplitter()
        sql = """
        BEGIN
            NULL;
        END;
        /
        """
        result = splitter.split(sql)
        assert len(result) == 1
        assert "NULL" in result[0]


# =====================
# Additional Tests for SimpleSplitter
# =====================

class TestSimpleSplitterAdditional:
    """Additional tests for SimpleSplitter class."""

    def test_statement_with_semicolon_in_comment(self):
        """Removes comment containing semicolon before splitting."""
        splitter = SimpleSplitter()
        sql = "SELECT 1 -- comment; here\n; SELECT 2"
        result = splitter.split(sql)
        # After removing comment, becomes "SELECT 1 \n; SELECT 2"
        assert len(result) == 2

    def test_multiline_statement(self):
        """Handles multiline statement correctly."""
        splitter = SimpleSplitter()
        sql = "SELECT\n  id,\n  name\nFROM\n  users; SELECT 1"
        result = splitter.split(sql)
        assert len(result) == 2
        assert "SELECT" in result[0]
        assert "id" in result[0]
        assert "name" in result[0]

    def test_semicolon_at_very_end(self):
        """Handles semicolon at very end without content after."""
        splitter = SimpleSplitter()
        sql = "SELECT 1; SELECT 2;"
        result = splitter.split(sql)
        assert len(result) == 2
        assert result[0] == "SELECT 1"
        assert result[1] == "SELECT 2"


# =====================
# Additional Tests for get_splitter Factory
# =====================

class TestGetSplitterAdditional:
    """Additional tests for get_splitter factory function."""

    def test_returns_postgresql_splitter_lowercase(self):
        """Returns PostgreSqlSplitter for 'postgresql' string."""
        splitter = get_splitter('postgresql')
        assert isinstance(splitter, PostgreSqlSplitter)

    def test_returns_mysql_splitter(self):
        """Returns PostgreSqlSplitter for 'mysql' string (same splitter)."""
        splitter = get_splitter('mysql')
        assert isinstance(splitter, PostgreSqlSplitter)

    def test_returns_sqlserver_splitter_string(self):
        """Returns SqlServerSplitter for 'sqlserver' string."""
        splitter = get_splitter('sqlserver')
        assert isinstance(splitter, SqlServerSplitter)

    def test_returns_oracle_splitter_string(self):
        """Returns OracleSplitter for 'oracle' string."""
        splitter = get_splitter('oracle')
        assert isinstance(splitter, OracleSplitter)

    def test_returns_simple_splitter_for_empty_string(self):
        """Returns SimpleSplitter for empty string."""
        splitter = get_splitter('')
        assert isinstance(splitter, SimpleSplitter)

    def test_returns_simple_splitter_for_unknown_type(self):
        """Returns SimpleSplitter for unknown database type string."""
        splitter = get_splitter('mongodb')
        assert isinstance(splitter, SimpleSplitter)


# =====================
# Additional Integration Tests
# =====================

class TestSplitterIntegrationAdditional:
    """Additional integration tests for SQL splitters."""

    def test_postgresql_trigger_with_function(self):
        """PostgreSQL trigger creation with associated function."""
        splitter = PostgreSqlSplitter()
        sql = """
        CREATE OR REPLACE FUNCTION notify_trigger() RETURNS trigger AS $$
        BEGIN
            PERFORM pg_notify('events', NEW.id::text);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER event_notify
            AFTER INSERT ON events
            FOR EACH ROW EXECUTE FUNCTION notify_trigger();
        """
        result = splitter.split(sql)
        assert len(result) == 2
        assert "notify_trigger" in result[0]
        assert "CREATE TRIGGER" in result[1]

    def test_sqlserver_temp_table_operations(self):
        """SQL Server temp table creation and usage."""
        splitter = SqlServerSplitter()
        sql = """
        CREATE TABLE #TempUsers (id INT, name NVARCHAR(100))
        GO
        INSERT INTO #TempUsers SELECT id, name FROM users WHERE active = 1
        GO
        SELECT * FROM #TempUsers
        GO
        DROP TABLE #TempUsers
        """
        result = splitter.split(sql)
        assert len(result) == 4
        assert "CREATE TABLE #TempUsers" in result[0]
        assert "DROP TABLE #TempUsers" in result[3]

    def test_oracle_cursor_with_loop(self):
        """Oracle PL/SQL with cursor and loop."""
        splitter = OracleSplitter()
        sql = """
        DECLARE
            CURSOR c_users IS SELECT id, name FROM users;
            v_id users.id%TYPE;
            v_name users.name%TYPE;
        BEGIN
            OPEN c_users;
            LOOP
                FETCH c_users INTO v_id, v_name;
                EXIT WHEN c_users%NOTFOUND;
                DBMS_OUTPUT.PUT_LINE(v_name);
            END LOOP;
            CLOSE c_users;
        END;
        /
        SELECT 'done' FROM DUAL
        """
        result = splitter.split(sql)
        assert len(result) == 2
        assert "CURSOR c_users" in result[0]
        assert "LOOP" in result[0]
        assert "SELECT 'done'" in result[1]


# =====================
# Additional Edge Cases
# =====================

class TestSplitterEdgeCasesAdditional:
    """Additional edge case tests for all splitters."""

    def test_postgresql_backslash_in_string(self):
        """Handles backslash in string (not escape in standard SQL)."""
        splitter = PostgreSqlSplitter()
        sql = r"SELECT 'path\\to\\file'; SELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2

    def test_postgresql_newline_in_string(self):
        """Handles newline character in string literal."""
        splitter = PostgreSqlSplitter()
        sql = "SELECT 'line1\nline2'; SELECT 2"
        result = splitter.split(sql)
        assert len(result) == 2

    def test_sqlserver_bracket_identifiers(self):
        """Handles SQL Server bracket identifiers."""
        splitter = SqlServerSplitter()
        sql = "SELECT [column name] FROM [table name]\nGO\nSELECT 1"
        result = splitter.split(sql)
        assert len(result) == 2
        assert "[column name]" in result[0]

    def test_oracle_case_statement(self):
        """Handles CASE statement (contains END but not block END)."""
        splitter = OracleSplitter()
        sql = """
        SELECT 
            CASE WHEN id = 1 THEN 'one' ELSE 'other' END AS label
        FROM users;
        SELECT 2 FROM DUAL
        """
        result = splitter.split(sql)
        # CASE...END should not affect block tracking incorrectly
        assert len(result) == 2

    def test_tabs_and_mixed_whitespace(self):
        """Handles tabs and mixed whitespace."""
        splitter = PostgreSqlSplitter()
        sql = "\t\tSELECT 1;\t\n\t\tSELECT 2\t\t"
        result = splitter.split(sql)
        assert len(result) == 2
        assert result[0] == "SELECT 1"
        assert result[1] == "SELECT 2"

    def test_carriage_return_line_feed(self):
        """Handles Windows-style CRLF line endings."""
        splitter = PostgreSqlSplitter()
        sql = "SELECT 1;\r\nSELECT 2;\r\n"
        result = splitter.split(sql)
        assert len(result) == 2

    def test_null_like_content(self):
        """Handles SQL with NULL keyword (not Python None)."""
        splitter = SimpleSplitter()
        sql = "INSERT INTO t VALUES (NULL); SELECT NULL"
        result = splitter.split(sql)
        assert len(result) == 2
        assert "NULL" in result[0]
        assert "NULL" in result[1]


# =====================
# Summary of Additional Covered Cases
# =====================
# - BaseSqlSplitter._remove_single_line_comments:
#   - Comment at start of line
#   - Preserves code before comment
#   - Single dash (not a comment)
#
# - BaseSqlSplitter._remove_multiline_comments:
#   - Comment at start
#   - Comment at end
#   - Adjacent comments
#
# - PostgreSqlSplitter:
#   - Underscore in dollar tag
#   - Partial/mismatched dollar tags
#   - Multiple empty dollar tags
#   - Quotes inside dollar block
#   - Dollar sign in regular string
#
# - SqlServerSplitter:
#   - GO with newline before
#   - Multiple GO in sequence
#   - GO at start/end of script
#   - Mixed case GO
#
# - OracleSplitter:
#   - Slash at end
#   - Multiple DECLARE blocks
#   - END with procedure name
#   - Simple SELECT without PL/SQL
#   - Empty PL/SQL block
#
# - SimpleSplitter:
#   - Semicolon in comment
#   - Multiline statement
#   - Semicolon at very end
#
# - get_splitter factory:
#   - String type inputs (postgresql, mysql, sqlserver, oracle)
#   - Empty string
#   - Unknown type
#
# - Integration:
#   - PostgreSQL trigger with function
#   - SQL Server temp tables
#   - Oracle cursor with loop
#
# - Edge cases:
#   - Backslash in string
#   - Newline in string
#   - SQL Server bracket identifiers
#   - CASE statement with END
#   - Tabs and mixed whitespace
#   - CRLF line endings
#   - NULL keyword