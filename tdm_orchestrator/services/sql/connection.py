"""
Gestionnaire de connexions aux bases de données.

Ce module gère la création et la gestion des connexions
aux différents types de bases de données supportés.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict

from ..constants import SUPPORTED_DATABASES, DATABASE_ALIASES, DEFAULT_PORTS
from ..exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Gestionnaire de connexions aux bases de données.
    
    Supporte : PostgreSQL, Oracle, SQL Server, MySQL
    
    Example:
        >>> manager = ConnectionManager(datasource)
        >>> with manager.get_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT 1")
    """
    
    def __init__(self, datasource):
        """
        Initialise le gestionnaire avec une datasource.
        
        Args:
            datasource: Objet DataSource du modèle Django
        """
        self.datasource = datasource
        self.db_type = self._detect_db_type()
    
    def _detect_db_type(self) -> str:
        """
        Détecte le type de base de données depuis la datasource.
        
        Returns:
            Type de DB normalisé (postgresql, oracle, sqlserver, mysql)
        """
        sgbd_name = self.datasource.sgbd_name.value_char.lower()
        
        # Vérifier les alias connus
        for alias, db_type in DATABASE_ALIASES.items():
            if alias in sgbd_name:
                return db_type
        
        # Vérification directe
        for db_type in SUPPORTED_DATABASES.keys():
            if db_type in sgbd_name:
                return db_type
        
        raise DatabaseConnectionError(
            f"Type de base de données non supporté : {sgbd_name}",
            details={'supported': list(SUPPORTED_DATABASES.keys())}
        )
    
    def get_connection_params(self) -> Dict[str, Any]:
        """
        Prépare les paramètres de connexion selon le type de DB.
        
        Returns:
            Dictionnaire de paramètres de connexion
        """
        params = {
            'host': self.datasource.sgbd_host,
            'port': self.datasource.sgbd_port or DEFAULT_PORTS.get(self.db_type),
            'user': self.datasource.sgbd_user,
            'password': self.datasource.sgbd_password,
        }
        
        if self.db_type == 'postgresql':
            params['database'] = self.datasource.sgbd_database
            if self.datasource.sgbd_tls:
                params['sslmode'] = 'require'
        
        elif self.db_type == 'oracle':
            params['dsn'] = f"{self.datasource.sgbd_host}:{params['port']}/{self.datasource.sgbd_sid}"
        
        elif self.db_type == 'sqlserver':
            params['database'] = self.datasource.sgbd_database
            params['driver'] = self.datasource.sgbd_driver or '{ODBC Driver 17 for SQL Server}'
        
        elif self.db_type == 'mysql':
            params['database'] = self.datasource.sgbd_database
            if self.datasource.sgbd_tls:
                params['ssl'] = {'ssl': True}
        
        return params
    
    def _create_connection(self, autocommit: bool = False):
        """
        Crée une connexion à la base de données.
        
        Args:
            autocommit: Active le mode autocommit
            
        Returns:
            Connection object
        """
        params = self.get_connection_params()
        
        if self.db_type == 'postgresql':
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            conn = psycopg2.connect(
                host=params['host'],
                port=params['port'],
                database=params['database'],
                user=params['user'],
                password=params['password']
            )
            if autocommit:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            return conn
        
        elif self.db_type == 'oracle':
            import cx_Oracle
            
            conn = cx_Oracle.connect(
                user=params['user'],
                password=params['password'],
                dsn=params['dsn']
            )
            if autocommit:
                conn.autocommit = True
            return conn
        
        elif self.db_type == 'sqlserver':
            import pyodbc
            
            conn_str = (
                f"DRIVER={params['driver']};"
                f"SERVER={params['host']};"
                f"DATABASE={params['database']};"
                f"UID={params['user']};"
                f"PWD={params['password']}"
            )
            return pyodbc.connect(conn_str, autocommit=autocommit)
        
        elif self.db_type == 'mysql':
            import MySQLdb
            
            conn = MySQLdb.connect(
                host=params['host'],
                port=params['port'],
                user=params['user'],
                passwd=params['password'],
                db=params['database']
            )
            if autocommit:
                conn.autocommit(True)
            return conn
    
    @contextmanager
    def get_connection(self, autocommit: bool = False):
        """
        Context manager pour obtenir une connexion à la base.
        
        Args:
            autocommit: Active le mode autocommit
        
        Yields:
            Connection object
            
        Example:
            >>> with manager.get_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT 1")
        """
        conn = None
        
        try:
            logger.info(f"Connexion à {self.db_type} ({self.datasource.name})")
            conn = self._create_connection(autocommit)
            logger.info("Connexion établie avec succès")
            yield conn
        
        except ImportError as e:
            driver = SUPPORTED_DATABASES.get(self.db_type, 'unknown')
            error_msg = f"Driver {driver} non installé : {str(e)}"
            logger.error(error_msg)
            raise DatabaseConnectionError(error_msg)
        
        except Exception as e:
            error_msg = f"Erreur de connexion : {str(e)}"
            logger.error(error_msg)
            raise DatabaseConnectionError(error_msg)
        
        finally:
            if conn:
                try:
                    conn.close()
                    logger.debug("Connexion fermée")
                except Exception:
                    pass
    
    def test_connection(self) -> tuple:
        """
        Teste la connexion à la base de données.
        
        Returns:
            Tuple (success: bool, message: str)
        """
        test_queries = {
            'postgresql': "SELECT version()",
            'oracle': "SELECT * FROM DUAL",
            'sqlserver': "SELECT @@VERSION",
            'mysql': "SELECT VERSION()",
        }
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(test_queries.get(self.db_type, "SELECT 1"))
                cursor.fetchone()
                cursor.close()
                return True, f"Connexion réussie à {self.datasource.name}"
        
        except Exception as e:
            return False, f"Échec de connexion : {str(e)}"
