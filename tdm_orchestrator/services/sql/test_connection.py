"""
Tests for ConnectionManager - database connection handling.

Covers:
- __init__ and _detect_db_type: DB type detection from datasource
- get_connection_params: Parameter preparation for each DB type
- _create_connection: Connection creation with mocked drivers
- get_connection: Context manager behavior
- test_connection: Connection testing
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from .connection import ConnectionManager
from ..exceptions import DatabaseConnectionError


# =====================
# Fixtures
# =====================

@pytest.fixture
def mock_datasource():
    """Creates a mock datasource with all required attributes."""
    datasource = MagicMock()
    datasource.name = "test_datasource"
    datasource.sgbd_host = "localhost"
    datasource.sgbd_port = 5432
    datasource.sgbd_user = "test_user"
    datasource.sgbd_password = "test_password"
    datasource.sgbd_database = "test_db"
    datasource.sgbd_sid = "test_sid"
    datasource.sgbd_driver = None
    datasource.sgbd_tls = False
    datasource.sgbd_name = MagicMock()
    datasource.sgbd_name.value_char = "postgresql"
    return datasource


@pytest.fixture
def mock_constants():
    """Patches constants used by ConnectionManager."""
    with patch.multiple(
        'tdm_orchestrator.services.sql.connection',
        SUPPORTED_DATABASES={'postgresql': 'psycopg2', 'oracle': 'cx_Oracle', 'sqlserver': 'pyodbc', 'mysql': 'MySQLdb'},
        DATABASE_ALIASES={'postgres': 'postgresql', 'mssql': 'sqlserver', 'mariadb': 'mysql'},
        DEFAULT_PORTS={'postgresql': 5432, 'oracle': 1521, 'sqlserver': 1433, 'mysql': 3306}
    ):
        yield


# =====================
# _detect_db_type Tests
# =====================

class TestDetectDbType:
    """Tests for _detect_db_type method."""

    def test_detect_postgresql_direct(self, mock_datasource, mock_constants):
        """Detects postgresql from direct name match."""
        mock_datasource.sgbd_name.value_char = "postgresql"
        manager = ConnectionManager(mock_datasource)
        assert manager.db_type == "postgresql"

    def test_detect_oracle_direct(self, mock_datasource, mock_constants):
        """Detects oracle from direct name match."""
        mock_datasource.sgbd_name.value_char = "oracle"
        manager = ConnectionManager(mock_datasource)
        assert manager.db_type == "oracle"

    def test_detect_sqlserver_direct(self, mock_datasource, mock_constants):
        """Detects sqlserver from direct name match."""
        mock_datasource.sgbd_name.value_char = "sqlserver"
        manager = ConnectionManager(mock_datasource)
        assert manager.db_type == "sqlserver"

    def test_detect_mysql_direct(self, mock_datasource, mock_constants):
        """Detects mysql from direct name match."""
        mock_datasource.sgbd_name.value_char = "mysql"
        manager = ConnectionManager(mock_datasource)
        assert manager.db_type == "mysql"

    def test_detect_via_postgres_alias(self, mock_datasource, mock_constants):
        """Detects postgresql via 'postgres' alias."""
        mock_datasource.sgbd_name.value_char = "postgres"
        manager = ConnectionManager(mock_datasource)
        assert manager.db_type == "postgresql"

    def test_detect_via_mssql_alias(self, mock_datasource, mock_constants):
        """Detects sqlserver via 'mssql' alias."""
        mock_datasource.sgbd_name.value_char = "mssql"
        manager = ConnectionManager(mock_datasource)
        assert manager.db_type == "sqlserver"

    def test_detect_via_mariadb_alias(self, mock_datasource, mock_constants):
        """Detects mysql via 'mariadb' alias."""
        mock_datasource.sgbd_name.value_char = "mariadb"
        manager = ConnectionManager(mock_datasource)
        assert manager.db_type == "mysql"

    def test_detect_case_insensitive(self, mock_datasource, mock_constants):
        """Detects db type case-insensitively."""
        mock_datasource.sgbd_name.value_char = "POSTGRESQL"
        manager = ConnectionManager(mock_datasource)
        assert manager.db_type == "postgresql"

    def test_raises_exception_for_unsupported_db(self, mock_datasource, mock_constants):
        """Raises DatabaseConnectionError for unsupported database type."""
        mock_datasource.sgbd_name.value_char = "unsupported_db"
        with pytest.raises(DatabaseConnectionError) as exc_info:
            ConnectionManager(mock_datasource)
        assert "non supporté" in str(exc_info.value)


# =====================
# get_connection_params Tests
# =====================

class TestGetConnectionParams:
    """Tests for get_connection_params method."""

    def test_postgresql_params_basic(self, mock_datasource, mock_constants):
        """Returns correct params for PostgreSQL without TLS."""
        mock_datasource.sgbd_name.value_char = "postgresql"
        mock_datasource.sgbd_tls = False
        manager = ConnectionManager(mock_datasource)
        params = manager.get_connection_params()
        
        assert params['host'] == "localhost"
        assert params['port'] == 5432
        assert params['user'] == "test_user"
        assert params['password'] == "test_password"
        assert params['database'] == "test_db"
        assert 'sslmode' not in params

    def test_postgresql_params_with_tls(self, mock_datasource, mock_constants):
        """Returns correct params for PostgreSQL with TLS enabled."""
        mock_datasource.sgbd_name.value_char = "postgresql"
        mock_datasource.sgbd_tls = True
        manager = ConnectionManager(mock_datasource)
        params = manager.get_connection_params()
        
        assert params['sslmode'] == 'require'

    def test_oracle_params_with_dsn(self, mock_datasource, mock_constants):
        """Returns correct params for Oracle with DSN."""
        mock_datasource.sgbd_name.value_char = "oracle"
        mock_datasource.sgbd_port = 1521
        mock_datasource.sgbd_sid = "ORCL"
        manager = ConnectionManager(mock_datasource)
        params = manager.get_connection_params()
        
        assert params['dsn'] == "localhost:1521/ORCL"

    def test_sqlserver_params_default_driver(self, mock_datasource, mock_constants):
        """Returns correct params for SQL Server with default driver."""
        mock_datasource.sgbd_name.value_char = "sqlserver"
        mock_datasource.sgbd_driver = None
        manager = ConnectionManager(mock_datasource)
        params = manager.get_connection_params()
        
        assert params['database'] == "test_db"
        assert params['driver'] == '{ODBC Driver 17 for SQL Server}'

    def test_sqlserver_params_custom_driver(self, mock_datasource, mock_constants):
        """Returns correct params for SQL Server with custom driver."""
        mock_datasource.sgbd_name.value_char = "sqlserver"
        mock_datasource.sgbd_driver = "{ODBC Driver 18 for SQL Server}"
        manager = ConnectionManager(mock_datasource)
        params = manager.get_connection_params()
        
        assert params['driver'] == "{ODBC Driver 18 for SQL Server}"

    def test_mysql_params_basic(self, mock_datasource, mock_constants):
        """Returns correct params for MySQL without TLS."""
        mock_datasource.sgbd_name.value_char = "mysql"
        mock_datasource.sgbd_tls = False
        manager = ConnectionManager(mock_datasource)
        params = manager.get_connection_params()
        
        assert params['database'] == "test_db"
        assert 'ssl' not in params

    def test_mysql_params_with_tls(self, mock_datasource, mock_constants):
        """Returns correct params for MySQL with TLS enabled."""
        mock_datasource.sgbd_name.value_char = "mysql"
        mock_datasource.sgbd_tls = True
        manager = ConnectionManager(mock_datasource)
        params = manager.get_connection_params()
        
        assert params['ssl'] == {'ssl': True}

    def test_default_port_fallback(self, mock_datasource, mock_constants):
        """Uses default port when sgbd_port is None."""
        mock_datasource.sgbd_name.value_char = "postgresql"
        mock_datasource.sgbd_port = None
        manager = ConnectionManager(mock_datasource)
        params = manager.get_connection_params()
        
        assert params['port'] == 5432


# =====================
# _create_connection Tests
# =====================

class TestCreateConnection:
    """Tests for _create_connection method.
    
    Note: Les drivers (psycopg2, cx_Oracle, etc.) sont importés dynamiquement
    dans _create_connection. On utilise patch.dict(sys.modules) pour les mocker.
    """

    def test_postgresql_connection_success(self, mock_datasource, mock_constants):
        """Creates PostgreSQL connection successfully."""
        import sys
        mock_datasource.sgbd_name.value_char = "postgresql"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        mock_psycopg2 = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT = 0
        
        with patch.dict(sys.modules, {'psycopg2': mock_psycopg2, 'psycopg2.extensions': mock_psycopg2.extensions}):
            conn = manager._create_connection(autocommit=False)
        
        assert conn == mock_conn
        mock_psycopg2.connect.assert_called_once()

    def test_postgresql_connection_with_autocommit(self, mock_datasource, mock_constants):
        """Creates PostgreSQL connection with autocommit enabled."""
        import sys
        mock_datasource.sgbd_name.value_char = "postgresql"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        mock_psycopg2 = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT = 0
        
        with patch.dict(sys.modules, {'psycopg2': mock_psycopg2, 'psycopg2.extensions': mock_psycopg2.extensions}):
            manager._create_connection(autocommit=True)
        
        mock_conn.set_isolation_level.assert_called_once_with(0)

    def test_oracle_connection_success(self, mock_datasource, mock_constants):
        """Creates Oracle connection successfully."""
        import sys
        mock_datasource.sgbd_name.value_char = "oracle"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        mock_cx_oracle = MagicMock()
        mock_cx_oracle.connect.return_value = mock_conn
        
        with patch.dict(sys.modules, {'cx_Oracle': mock_cx_oracle}):
            conn = manager._create_connection(autocommit=False)
        
        assert conn == mock_conn
        mock_cx_oracle.connect.assert_called_once()

    def test_oracle_connection_with_autocommit(self, mock_datasource, mock_constants):
        """Creates Oracle connection with autocommit enabled."""
        import sys
        mock_datasource.sgbd_name.value_char = "oracle"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        mock_cx_oracle = MagicMock()
        mock_cx_oracle.connect.return_value = mock_conn
        
        with patch.dict(sys.modules, {'cx_Oracle': mock_cx_oracle}):
            manager._create_connection(autocommit=True)
        
        assert mock_conn.autocommit is True

    def test_sqlserver_connection_success(self, mock_datasource, mock_constants):
        """Creates SQL Server connection successfully."""
        import sys
        mock_datasource.sgbd_name.value_char = "sqlserver"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        mock_pyodbc = MagicMock()
        mock_pyodbc.connect.return_value = mock_conn
        
        with patch.dict(sys.modules, {'pyodbc': mock_pyodbc}):
            conn = manager._create_connection(autocommit=False)
        
        assert conn == mock_conn
        mock_pyodbc.connect.assert_called_once()

    def test_sqlserver_connection_with_autocommit(self, mock_datasource, mock_constants):
        """Creates SQL Server connection with autocommit in connect call."""
        import sys
        mock_datasource.sgbd_name.value_char = "sqlserver"
        manager = ConnectionManager(mock_datasource)
        
        mock_pyodbc = MagicMock()
        
        with patch.dict(sys.modules, {'pyodbc': mock_pyodbc}):
            manager._create_connection(autocommit=True)
        
        call_kwargs = mock_pyodbc.connect.call_args
        assert call_kwargs[1]['autocommit'] is True

    def test_mysql_connection_success(self, mock_datasource, mock_constants):
        """Creates MySQL connection successfully."""
        import sys
        mock_datasource.sgbd_name.value_char = "mysql"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        mock_mysqldb = MagicMock()
        mock_mysqldb.connect.return_value = mock_conn
        
        with patch.dict(sys.modules, {'MySQLdb': mock_mysqldb}):
            conn = manager._create_connection(autocommit=False)
        
        assert conn == mock_conn
        mock_mysqldb.connect.assert_called_once()

    def test_mysql_connection_with_autocommit(self, mock_datasource, mock_constants):
        """Creates MySQL connection with autocommit enabled."""
        import sys
        mock_datasource.sgbd_name.value_char = "mysql"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        mock_mysqldb = MagicMock()
        mock_mysqldb.connect.return_value = mock_conn
        
        with patch.dict(sys.modules, {'MySQLdb': mock_mysqldb}):
            manager._create_connection(autocommit=True)
        
        mock_conn.autocommit.assert_called_once_with(True)


# =====================
# get_connection Context Manager Tests
# =====================

class TestGetConnection:
    """Tests for get_connection context manager."""

    def test_yields_connection_and_closes(self, mock_datasource, mock_constants):
        """Yields connection and closes it after context exits."""
        mock_datasource.sgbd_name.value_char = "postgresql"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        with patch.object(manager, '_create_connection', return_value=mock_conn):
            with manager.get_connection() as conn:
                assert conn == mock_conn
        
        mock_conn.close.assert_called_once()

    def test_passes_autocommit_flag(self, mock_datasource, mock_constants):
        """Passes autocommit flag to _create_connection."""
        mock_datasource.sgbd_name.value_char = "postgresql"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        with patch.object(manager, '_create_connection', return_value=mock_conn) as mock_create:
            with manager.get_connection(autocommit=True):
                pass
        
        mock_create.assert_called_once_with(True)

    def test_raises_database_connection_error_on_import_error(self, mock_datasource, mock_constants):
        """Raises DatabaseConnectionError when driver import fails."""
        mock_datasource.sgbd_name.value_char = "postgresql"
        manager = ConnectionManager(mock_datasource)
        
        with patch.object(manager, '_create_connection', side_effect=ImportError("No module named 'psycopg2'")):
            with pytest.raises(DatabaseConnectionError) as exc_info:
                with manager.get_connection():
                    pass
        
        assert "non installé" in str(exc_info.value)

    def test_raises_database_connection_error_on_generic_exception(self, mock_datasource, mock_constants):
        """Raises DatabaseConnectionError on generic connection exception."""
        mock_datasource.sgbd_name.value_char = "postgresql"
        manager = ConnectionManager(mock_datasource)
        
        with patch.object(manager, '_create_connection', side_effect=Exception("Connection refused")):
            with pytest.raises(DatabaseConnectionError) as exc_info:
                with manager.get_connection():
                    pass
        
        assert "Erreur de connexion" in str(exc_info.value)

    def test_closes_connection_even_on_exception(self, mock_datasource, mock_constants):
        """Closes connection even when exception occurs in context."""
        mock_datasource.sgbd_name.value_char = "postgresql"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        with patch.object(manager, '_create_connection', return_value=mock_conn):
            with pytest.raises(DatabaseConnectionError):
                with manager.get_connection():
                    raise Exception("Error inside context")
        
        mock_conn.close.assert_called_once()

    def test_handles_close_exception_silently(self, mock_datasource, mock_constants):
        """Handles exception during connection close silently."""
        mock_datasource.sgbd_name.value_char = "postgresql"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        mock_conn.close.side_effect = Exception("Close failed")
        
        with patch.object(manager, '_create_connection', return_value=mock_conn):
            # Should not raise exception
            with manager.get_connection():
                pass


# =====================
# test_connection Tests
# =====================

class TestTestConnection:
    """Tests for test_connection method."""

    def test_returns_success_on_successful_connection(self, mock_datasource, mock_constants):
        """Returns (True, message) on successful connection test."""
        mock_datasource.sgbd_name.value_char = "postgresql"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch.object(manager, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
            
            success, message = manager.test_connection()
        
        assert success is True
        assert "Connexion réussie" in message
        assert "test_datasource" in message

    def test_executes_correct_query_for_postgresql(self, mock_datasource, mock_constants):
        """Executes SELECT version() for PostgreSQL."""
        mock_datasource.sgbd_name.value_char = "postgresql"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch.object(manager, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
            
            manager.test_connection()
        
        mock_cursor.execute.assert_called_once_with("SELECT version()")

    def test_executes_correct_query_for_oracle(self, mock_datasource, mock_constants):
        """Executes SELECT * FROM DUAL for Oracle."""
        mock_datasource.sgbd_name.value_char = "oracle"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch.object(manager, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
            
            manager.test_connection()
        
        mock_cursor.execute.assert_called_once_with("SELECT * FROM DUAL")

    def test_executes_correct_query_for_sqlserver(self, mock_datasource, mock_constants):
        """Executes SELECT @@VERSION for SQL Server."""
        mock_datasource.sgbd_name.value_char = "sqlserver"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch.object(manager, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
            
            manager.test_connection()
        
        mock_cursor.execute.assert_called_once_with("SELECT @@VERSION")

    def test_executes_correct_query_for_mysql(self, mock_datasource, mock_constants):
        """Executes SELECT VERSION() for MySQL."""
        mock_datasource.sgbd_name.value_char = "mysql"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch.object(manager, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
            
            manager.test_connection()
        
        mock_cursor.execute.assert_called_once_with("SELECT VERSION()")

    def test_returns_failure_on_exception(self, mock_datasource, mock_constants):
        """Returns (False, message) when connection fails."""
        mock_datasource.sgbd_name.value_char = "postgresql"
        manager = ConnectionManager(mock_datasource)
        
        with patch.object(manager, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = MagicMock(side_effect=Exception("Connection failed"))
            mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
            
            success, message = manager.test_connection()
        
        assert success is False
        assert "Échec de connexion" in message

    def test_closes_cursor_after_test(self, mock_datasource, mock_constants):
        """Closes cursor after successful test."""
        mock_datasource.sgbd_name.value_char = "postgresql"
        manager = ConnectionManager(mock_datasource)
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch.object(manager, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
            
            manager.test_connection()
        
        mock_cursor.close.assert_called_once()


# =====================
# Summary of Covered Cases
# =====================
# - _detect_db_type:
#   - Direct match for postgresql, oracle, sqlserver, mysql
#   - Alias match for postgres, mssql, mariadb
#   - Case insensitive detection
#   - Raises DatabaseConnectionError for unsupported DB
#
# - get_connection_params:
#   - PostgreSQL basic params
#   - PostgreSQL with TLS
#   - Oracle with DSN
#   - SQL Server with default/custom driver
#   - MySQL basic params
#   - MySQL with TLS
#   - Default port fallback
#
# - _create_connection:
#   - PostgreSQL connection success
#   - PostgreSQL with autocommit
#   - Oracle connection success
#   - Oracle with autocommit
#   - SQL Server connection success
#   - SQL Server with autocommit
#   - MySQL connection success
#   - MySQL with autocommit
#
# - get_connection:
#   - Yields connection and closes
#   - Passes autocommit flag
#   - Raises DatabaseConnectionError on ImportError
#   - Raises DatabaseConnectionError on generic exception
#   - Closes connection on context exception
#   - Handles close exception silently
#
# - test_connection:
#   - Returns success on successful connection
#   - Executes correct query for each DB type
#   - Returns failure on exception
#   - Closes cursor after test