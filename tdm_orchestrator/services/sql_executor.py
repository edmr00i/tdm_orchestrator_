"""
Service d'exécution de scripts SQL sur différentes bases de données.

Supporte : PostgreSQL, Oracle, SQL Server, MySQL
Fonctionnalités : Dry run (avec rollback), Exécution réelle, Gestion des erreurs
"""

import re
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager

from .variable_parser import parse_sql_variables

logger = logging.getLogger(__name__)


# =====================
# Exceptions
# =====================
class SqlExecutionError(Exception):
    """Exception levée lors d'erreurs d'exécution SQL."""
    pass


class DatabaseConnectionError(Exception):
    """Exception levée lors d'erreurs de connexion."""
    pass


# =====================
# Résultat d'exécution
# =====================
@dataclass
class SqlExecutionResult:
    """
    Résultat d'une exécution SQL.
    """
    success: bool
    duration_ms: int
    logs: str
    error_message: Optional[str] = None
    rows_affected: Optional[int] = None
    statements_executed: int = 0
    statements_failed: int = 0
    
    @property
    def duration_seconds(self) -> float:
        """Retourne la durée en secondes."""
        return round(self.duration_ms / 1000, 2)
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire."""
        return {
            'success': self.success,
            'duration_ms': self.duration_ms,
            'duration_seconds': self.duration_seconds,
            'logs': self.logs,
            'error_message': self.error_message,
            'rows_affected': self.rows_affected,
            'statements_executed': self.statements_executed,
            'statements_failed': self.statements_failed,
        }


# =====================
# Executor SQL
# =====================
class SqlExecutor:
    """
    Classe pour exécuter des scripts SQL sur différentes bases de données.
    
    Supporte :
    - PostgreSQL (via psycopg2)
    - Oracle (via cx_Oracle)
    - SQL Server (via pyodbc)
    - MySQL (via mysqlclient)
    
    Exemples:
        >>> executor = SqlExecutor(datasource)
        >>> result = executor.execute_dry_run(sql, variables)
        >>> if result.success:
        ...     print("Validation réussie !")
        
        >>> result = executor.execute(sql, variables)
        >>> print(f"Exécuté en {result.duration_seconds}s")
    """
    
    # Drivers disponibles
    SUPPORTED_DATABASES = {
        'postgresql': 'psycopg2',
        'oracle': 'cx_Oracle',
        'sqlserver': 'pyodbc',
        'mysql': 'mysqlclient',
    }
    
    def __init__(self, datasource):
        """
        Initialise l'executor avec une datasource.
        
        Args:
            datasource: Objet DataSource du modèle Django
        """
        self.datasource = datasource
        self.db_type = self._detect_db_type()
        self.connection = None
        self._logs = []
    
    def _detect_db_type(self) -> str:
        """
        Détecte le type de base de données depuis la datasource.
        
        Returns:
            Type de DB (postgresql, oracle, sqlserver, mysql)
        """
        sgbd_name = self.datasource.sgbd_name.value_char.lower()
        
        if 'postgres' in sgbd_name:
            return 'postgresql'
        elif 'oracle' in sgbd_name:
            return 'oracle'
        elif 'sql server' in sgbd_name or 'sqlserver' in sgbd_name:
            return 'sqlserver'
        elif 'mysql' in sgbd_name or 'mariadb' in sgbd_name:
            return 'mysql'
        else:
            raise DatabaseConnectionError(f"Type de base de données non supporté : {sgbd_name}")
    
    def _log(self, message: str, level: str = 'INFO'):
        """Ajoute un message au log."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        self._logs.append(log_entry)
        
        if level == 'ERROR':
            logger.error(message)
        elif level == 'WARNING':
            logger.warning(message)
        else:
            logger.info(message)
    
    def _is_transaction_forbidden(self, sql: str) -> bool:
        """
        Détecte les commandes qui ne supportent pas d'être dans une transaction.
        
        Certaines commandes PostgreSQL (et autres SGBD) ne peuvent pas être
        exécutées dans un bloc transactionnel. Ces commandes doivent être
        exécutées en mode autocommit.
        
        Args:
            sql: Instruction SQL à analyser
            
        Returns:
            True si la commande doit être exécutée hors transaction
            
        Example:
            >>> executor._is_transaction_forbidden("VACUUM ANALYZE users")
            True
            >>> executor._is_transaction_forbidden("SELECT * FROM users")
            False
        """
        # Patterns de commandes interdites en transaction
        forbidden_patterns = [
            # PostgreSQL - Opérations CONCURRENTLY
            r'\bREINDEX\s+.*\bCONCURRENTLY\b',
            r'\bCREATE\s+INDEX\s+CONCURRENTLY\b',
            r'\bDROP\s+INDEX\s+CONCURRENTLY\b',
            r'\bCREATE\s+DATABASE\b',
            r'\bDROP\s+DATABASE\b',
            
            # PostgreSQL - Maintenance
            r'\bVACUUM\b',
            r'\bCLUSTER\b(?!\s+ON)',  # CLUSTER sans ON (qui refait la table)
            
            # PostgreSQL - Réplication et recovery
            r'\bALTER\s+SYSTEM\b',
            
            # MySQL - Commandes DDL implicitement commitées
            r'\bLOAD\s+DATA\b',
            r'\bLOCK\s+TABLES\b',
            r'\bUNLOCK\s+TABLES\b',
            
            # Oracle - Commandes hors transaction
            r'\bALTER\s+DATABASE\b',
        ]
        
        return any(re.search(pattern, sql, re.IGNORECASE) for pattern in forbidden_patterns)
    
    def _execute_autocommit(self, statement: str) -> None:
        """
        Exécute une commande en mode autocommit (hors transaction).
        
        Utilisé pour les commandes comme VACUUM, CREATE INDEX CONCURRENTLY, etc.
        qui ne peuvent pas être exécutées dans une transaction.
        
        Args:
            statement: Instruction SQL à exécuter
            
        Raises:
            SqlExecutionError: Si l'exécution échoue
        """
        conn = None
        
        try:
            if self.db_type == 'postgresql':
                import psycopg2
                from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
                
                params = self._get_connection_params()
                conn = psycopg2.connect(
                    host=params['host'],
                    port=params['port'],
                    database=params['database'],
                    user=params['user'],
                    password=params['password']
                )
                # Activer le mode autocommit
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            elif self.db_type == 'oracle':
                import cx_Oracle
                params = self._get_connection_params()
                conn = cx_Oracle.connect(
                    user=params['user'],
                    password=params['password'],
                    dsn=params['dsn']
                )
                conn.autocommit = True
            
            elif self.db_type == 'sqlserver':
                import pyodbc
                params = self._get_connection_params()
                conn_str = (
                    f"DRIVER={params['driver']};"
                    f"SERVER={params['host']};"
                    f"DATABASE={params['database']};"
                    f"UID={params['user']};"
                    f"PWD={params['password']}"
                )
                conn = pyodbc.connect(conn_str, autocommit=True)
            
            elif self.db_type == 'mysql':
                import MySQLdb
                params = self._get_connection_params()
                conn = MySQLdb.connect(
                    host=params['host'],
                    port=params['port'],
                    user=params['user'],
                    passwd=params['password'],
                    db=params['database']
                )
                conn.autocommit(True)
            
            cursor = conn.cursor()
            cursor.execute(statement)
            cursor.close()
        
        except Exception as e:
            raise SqlExecutionError(f"Erreur autocommit : {str(e)}")
        
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def _get_connection_params(self) -> Dict[str, Any]:
        """
        Prépare les paramètres de connexion selon le type de DB.
        
        Returns:
            Dictionnaire de paramètres de connexion
        """
        params = {
            'host': self.datasource.sgbd_host,
            'port': self.datasource.sgbd_port,
            'user': self.datasource.sgbd_user,
            'password': self.datasource.sgbd_password,
        }
        
        if self.db_type == 'postgresql':
            params['database'] = self.datasource.sgbd_database
            if self.datasource.sgbd_tls:
                params['sslmode'] = 'require'
        
        elif self.db_type == 'oracle':
            # Oracle utilise un DSN
            params['dsn'] = f"{self.datasource.sgbd_host}:{self.datasource.sgbd_port}/{self.datasource.sgbd_sid}"
        
        elif self.db_type == 'sqlserver':
            params['database'] = self.datasource.sgbd_database
            params['driver'] = self.datasource.sgbd_driver or '{ODBC Driver 17 for SQL Server}'
        
        elif self.db_type == 'mysql':
            params['database'] = self.datasource.sgbd_database
            if self.datasource.sgbd_tls:
                params['ssl'] = {'ssl': True}
        
        return params
    
    @contextmanager
    def get_connection(self):
        """
        Context manager pour obtenir une connexion à la base.
        
        Usage:
            with executor.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
        
        Yields:
            Connection object
        """
        conn = None
        
        try:
            self._log(f"Connexion à {self.db_type} ({self.datasource.name})")
            
            if self.db_type == 'postgresql':
                import psycopg2
                params = self._get_connection_params()
                conn = psycopg2.connect(
                    host=params['host'],
                    port=params['port'],
                    database=params['database'],
                    user=params['user'],
                    password=params['password']
                )
            
            elif self.db_type == 'oracle':
                import cx_Oracle
                params = self._get_connection_params()
                conn = cx_Oracle.connect(
                    user=params['user'],
                    password=params['password'],
                    dsn=params['dsn']
                )
            
            elif self.db_type == 'sqlserver':
                import pyodbc
                params = self._get_connection_params()
                conn_str = (
                    f"DRIVER={params['driver']};"
                    f"SERVER={params['host']};"
                    f"DATABASE={params['database']};"
                    f"UID={params['user']};"
                    f"PWD={params['password']}"
                )
                conn = pyodbc.connect(conn_str)
            
            elif self.db_type == 'mysql':
                import MySQLdb
                params = self._get_connection_params()
                conn = MySQLdb.connect(
                    host=params['host'],
                    port=params['port'],
                    user=params['user'],
                    passwd=params['password'],
                    db=params['database']
                )
            
            self._log("Connexion établie avec succès")
            yield conn
        
        except ImportError as e:
            error_msg = f"Driver {self.SUPPORTED_DATABASES[self.db_type]} non installé : {str(e)}"
            self._log(error_msg, 'ERROR')
            raise DatabaseConnectionError(error_msg)
        
        except Exception as e:
            error_msg = f"Erreur de connexion : {str(e)}"
            self._log(error_msg, 'ERROR')
            raise DatabaseConnectionError(error_msg)
        
        finally:
            if conn:
                try:
                    conn.close()
                    self._log("Connexion fermée")
                except:
                    pass
    
    def split_sql_statements(self, sql_content: str) -> List[str]:
        """
        Découpe intelligemment le SQL en instructions individuelles.
        
        Gère correctement :
        - Les blocs PostgreSQL Dollar-Quoted ($$...$$, $tag$...$tag$)
        - Les chaînes de caractères ('...' et "...")
        - Les quotes échappées ('')
        - Les commentaires mono-ligne (--) et multi-lignes (/* */)
        - Les délimiteurs spécifiques à chaque SGBD (;, GO, /)
        
        Args:
            sql_content: Contenu SQL complet
            
        Returns:
            Liste d'instructions SQL nettoyées
            
        Example:
            >>> executor.split_sql_statements('''
            ...     SELECT * FROM users;
            ...     DO $$ BEGIN RAISE NOTICE 'test'; END $$;
            ...     UPDATE users SET name = 'O''Brien';
            ... ''')
            ['SELECT * FROM users', "DO $$ BEGIN RAISE NOTICE 'test'; END $$", ...]
        """
        # Déléguer au parser intelligent pour PostgreSQL et MySQL
        if self.db_type in ('postgresql', 'mysql'):
            return self._split_sql_statements_smart(sql_content)
        
        # Pour SQL Server, utiliser GO comme délimiteur
        elif self.db_type == 'sqlserver':
            return self._split_sql_statements_sqlserver(sql_content)
        
        # Pour Oracle, gérer les blocs PL/SQL
        elif self.db_type == 'oracle':
            return self._split_sql_statements_oracle(sql_content)
        
        # Fallback simple
        else:
            return self._split_sql_statements_simple(sql_content)
    
    def _split_sql_statements_smart(self, sql_content: str) -> List[str]:
        """
        Découpage intelligent pour PostgreSQL/MySQL.
        
        Gère les blocs $$, les chaînes quotées et les commentaires.
        """
        # Retirer les commentaires mono-ligne en dehors des chaînes
        # On les traite d'abord car ils peuvent contenir des ;
        cleaned_lines = []
        for line in sql_content.split('\n'):
            # Trouver la position du -- en dehors des quotes
            in_quote = False
            quote_char = None
            comment_pos = -1
            
            i = 0
            while i < len(line):
                char = line[i]
                
                # Gestion des quotes
                if char in ("'", '"') and not in_quote:
                    in_quote = True
                    quote_char = char
                elif in_quote and char == quote_char:
                    # Vérifier quote échappée
                    if i + 1 < len(line) and line[i + 1] == quote_char:
                        i += 1  # Sauter la quote échappée
                    else:
                        in_quote = False
                        quote_char = None
                
                # Détecter -- en dehors des quotes
                elif not in_quote and line[i:i+2] == '--':
                    comment_pos = i
                    break
                
                i += 1
            
            if comment_pos >= 0:
                cleaned_lines.append(line[:comment_pos])
            else:
                cleaned_lines.append(line)
        
        sql_content = '\n'.join(cleaned_lines)
        
        # Retirer les commentaires multi-lignes /* ... */
        # Attention à ne pas les retirer dans les chaînes
        result = []
        i = 0
        in_quote = False
        quote_char = None
        in_comment = False
        
        while i < len(sql_content):
            char = sql_content[i]
            
            # Gestion commentaires multi-lignes
            if not in_quote and not in_comment and sql_content[i:i+2] == '/*':
                in_comment = True
                i += 2
                continue
            
            if in_comment and sql_content[i:i+2] == '*/':
                in_comment = False
                i += 2
                continue
            
            if in_comment:
                i += 1
                continue
            
            # Gestion des quotes
            if char in ("'", '"') and not in_quote:
                in_quote = True
                quote_char = char
            elif in_quote and char == quote_char:
                if i + 1 < len(sql_content) and sql_content[i + 1] == quote_char:
                    result.append(char)
                    i += 1
                else:
                    in_quote = False
                    quote_char = None
            
            result.append(char)
            i += 1
        
        sql_content = ''.join(result)
        
        # Maintenant, découper par ; en gérant les blocs $$ et les quotes
        statements = []
        current_stmt = []
        in_quote = False
        quote_char = None
        in_dollar_block = False
        dollar_tag = None
        
        i = 0
        while i < len(sql_content):
            char = sql_content[i]
            
            # Gestion des Dollar-Quoted Strings PostgreSQL ($$ ou $tag$)
            if char == '$' and not in_quote:
                # Chercher le tag complet ($$ ou $identifier$)
                match = re.match(r'\$([A-Za-z_]*)\$', sql_content[i:])
                if match:
                    tag = match.group(0)
                    
                    if not in_dollar_block:
                        # Début d'un bloc dollar
                        in_dollar_block = True
                        dollar_tag = tag
                        current_stmt.append(tag)
                        i += len(tag)
                        continue
                    elif tag == dollar_tag:
                        # Fin du bloc dollar
                        in_dollar_block = False
                        dollar_tag = None
                        current_stmt.append(tag)
                        i += len(tag)
                        continue
            
            # Gestion des quotes standards (' ou ")
            if char in ("'", '"') and not in_dollar_block:
                if not in_quote:
                    in_quote = True
                    quote_char = char
                elif char == quote_char:
                    # Vérifier si c'est une quote échappée
                    if i + 1 < len(sql_content) and sql_content[i + 1] == quote_char:
                        current_stmt.append(char)
                        current_stmt.append(char)
                        i += 2
                        continue
                    else:
                        in_quote = False
                        quote_char = None
            
            # Découpage au point-virgule (seulement si pas dans un bloc)
            if char == ';' and not in_quote and not in_dollar_block:
                stmt_text = ''.join(current_stmt).strip()
                if stmt_text:
                    statements.append(stmt_text)
                current_stmt = []
            else:
                current_stmt.append(char)
            
            i += 1
        
        # Ajouter la dernière instruction si pas de ; final
        last_stmt = ''.join(current_stmt).strip()
        if last_stmt:
            statements.append(last_stmt)
        
        self._log(f"{len(statements)} instruction(s) SQL détectée(s)")
        return statements
    
    def _split_sql_statements_sqlserver(self, sql_content: str) -> List[str]:
        """
        Découpage pour SQL Server utilisant GO comme séparateur.
        """
        # Retirer les commentaires
        sql_content = re.sub(r'--[^\n]*', '', sql_content)
        sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
        
        # Découper par GO (mot-clé seul sur une ligne ou en fin de ligne)
        statements = re.split(r'\bGO\b', sql_content, flags=re.IGNORECASE)
        statements = [stmt.strip() for stmt in statements if stmt.strip()]
        
        self._log(f"{len(statements)} batch(es) SQL Server détecté(s)")
        return statements
    
    def _split_sql_statements_oracle(self, sql_content: str) -> List[str]:
        """
        Découpage pour Oracle avec gestion des blocs PL/SQL.
        """
        # Retirer les commentaires
        sql_content = re.sub(r'--[^\n]*', '', sql_content)
        sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
        
        statements = []
        current_stmt = []
        in_plsql_block = False
        block_depth = 0
        
        # Tokeniser grossièrement
        tokens = re.split(r'(\s+|;|/)', sql_content)
        
        for token in tokens:
            upper_token = token.upper().strip()
            
            # Détecter début de bloc PL/SQL
            if upper_token in ('BEGIN', 'DECLARE'):
                in_plsql_block = True
                block_depth += 1
            
            # Détecter END de bloc
            if upper_token == 'END' and in_plsql_block:
                block_depth -= 1
                if block_depth <= 0:
                    in_plsql_block = False
                    block_depth = 0
            
            # Séparateur / pour blocs PL/SQL
            if token == '/' and not in_plsql_block:
                stmt_text = ''.join(current_stmt).strip()
                if stmt_text:
                    statements.append(stmt_text)
                current_stmt = []
                continue
            
            # Séparateur ; pour SQL standard
            if token == ';' and not in_plsql_block:
                stmt_text = ''.join(current_stmt).strip()
                if stmt_text:
                    statements.append(stmt_text)
                current_stmt = []
                continue
            
            current_stmt.append(token)
        
        # Dernière instruction
        last_stmt = ''.join(current_stmt).strip()
        if last_stmt:
            statements.append(last_stmt)
        
        self._log(f"{len(statements)} instruction(s) Oracle détectée(s)")
        return statements
    
    def _split_sql_statements_simple(self, sql_content: str) -> List[str]:
        """
        Découpage simple par point-virgule (fallback).
        """
        sql_content = re.sub(r'--[^\n]*', '', sql_content)
        sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
        
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        self._log(f"{len(statements)} instruction(s) SQL détectée(s)")
        return statements
    
    def execute_dry_run(self, sql_content: str, variables: Optional[Dict[str, str]] = None,
                        strict_variables: bool = False) -> SqlExecutionResult:
        """
        Exécute le SQL en mode dry run (avec ROLLBACK).
        
        Le SQL est exécuté dans une transaction qui est systématiquement
        annulée (ROLLBACK). Utile pour valider la syntaxe sans impact.
        
        Args:
            sql_content: Contenu SQL à exécuter
            variables: Variables à substituer (optionnel)
            strict_variables: Si True, valide les noms de variables (whitelist)
            
        Returns:
            SqlExecutionResult avec le résultat
        """
        self._logs = []
        start_time = time.time()
        statements_executed = 0
        statements_failed = 0
        
        try:
            self._log("=== DÉBUT DRY RUN ===")
            self._log(f"Mode : Validation (ROLLBACK automatique)")
            self._log(f"Base de données : {self.db_type} ({self.datasource.name})")
            
            # --- ÉTAPE 1 : REMPLACEMENT DES VARIABLES (AVANT découpage !) ---
            # On transforme le template SQL en SQL pur (ex: ${SCHEMA} -> public)
            parsed_sql = parse_sql_variables(sql_content, variables or {}, strict=strict_variables)
            if variables:
                self._log(f"Parsing avec {len(variables)} variable(s) : {list(variables.keys())}")
            self._log("Parsing des variables terminé")
            
            # --- ÉTAPE 2 : DÉCOUPAGE INTELLIGENT ---
            # Maintenant qu'on a du SQL pur, on le découpe sans risque
            statements = self.split_sql_statements(parsed_sql)
            
            if not statements:
                self._log("⚠ Aucune instruction SQL à exécuter", 'WARNING')
                return SqlExecutionResult(
                    success=True,
                    duration_ms=int((time.time() - start_time) * 1000),
                    logs='\n'.join(self._logs),
                    statements_executed=0,
                    statements_failed=0
                )
            
            # Exécution avec rollback
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                self._log("Transaction démarrée")
                
                for i, statement in enumerate(statements, 1):
                    try:
                        # Log du début d'instruction (tronqué si trop long)
                        stmt_preview = statement[:100] + '...' if len(statement) > 100 else statement
                        self._log(f"[{i}/{len(statements)}] Exécution : {stmt_preview}")
                        
                        cursor.execute(statement)
                        statements_executed += 1
                        self._log(f"✓ Instruction {i} validée")
                    except Exception as e:
                        statements_failed += 1
                        error_msg = f"✗ Erreur instruction {i}: {str(e)}"
                        self._log(error_msg, 'ERROR')
                        raise SqlExecutionError(error_msg)
                
                # ROLLBACK systématique
                conn.rollback()
                self._log("ROLLBACK effectué (aucune modification en base)")
                
                cursor.close()
            
            duration_ms = int((time.time() - start_time) * 1000)
            self._log(f"=== FIN DRY RUN - Durée: {duration_ms}ms - {statements_executed} instruction(s) validée(s) ===")
            
            return SqlExecutionResult(
                success=True,
                duration_ms=duration_ms,
                logs='\n'.join(self._logs),
                statements_executed=statements_executed,
                statements_failed=statements_failed
            )
        
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            self._log(f"=== ÉCHEC DRY RUN - {error_msg} ===", 'ERROR')
            
            return SqlExecutionResult(
                success=False,
                duration_ms=duration_ms,
                logs='\n'.join(self._logs),
                error_message=error_msg,
                statements_executed=statements_executed,
                statements_failed=statements_failed
            )
    
    def execute(self, sql_content: str, variables: Optional[Dict[str, str]] = None, 
                auto_commit: bool = True, dry_run: bool = False,
                strict_variables: bool = False, stop_on_error: bool = True) -> SqlExecutionResult:
        """
        Exécute le SQL réellement (avec COMMIT) ou en mode dry_run.
        
        Cette méthode est le point d'entrée principal pour l'exécution SQL.
        Elle supporte :
        - L'exécution réelle avec COMMIT
        - Le mode dry_run (validation sans modification)
        - La substitution de variables avec validation optionnelle
        - L'arrêt ou la continuation en cas d'erreur
        
        Args:
            sql_content: Contenu SQL à exécuter
            variables: Variables à substituer (optionnel)
            auto_commit: Si True, COMMIT automatique en cas de succès
            dry_run: Si True, exécute en mode validation (ROLLBACK)
            strict_variables: Si True, valide les noms de variables (whitelist)
            stop_on_error: Si True, arrête à la première erreur
            
        Returns:
            SqlExecutionResult avec le résultat détaillé
            
        Example:
            >>> executor = SqlExecutor(datasource)
            >>> # Validation sans exécution réelle
            >>> result = executor.execute(sql, variables, dry_run=True)
            >>> if result.success:
            ...     # Exécution réelle
            ...     result = executor.execute(sql, variables)
        """
        # Déléguer au dry_run si demandé
        if dry_run:
            return self.execute_dry_run(sql_content, variables, strict_variables)
        
        self._logs = []
        start_time = time.time()
        statements_executed = 0
        statements_failed = 0
        total_rows_affected = 0
        
        try:
            self._log("=== DÉBUT EXÉCUTION RÉELLE ===")
            self._log(f"Base de données : {self.db_type} ({self.datasource.name})")
            self._log(f"Mode : Exécution avec {'COMMIT' if auto_commit else 'COMMIT manuel'}")
            self._log(f"Stop on error : {'Oui' if stop_on_error else 'Non (best effort)'}")
            
            # --- ÉTAPE 1 : REMPLACEMENT DES VARIABLES (AVANT découpage !) ---
            # On transforme le template SQL en SQL pur (ex: ${SCHEMA} -> public)
            parsed_sql = parse_sql_variables(sql_content, variables or {}, strict=strict_variables)
            if variables:
                self._log(f"Parsing avec {len(variables)} variable(s) : {list(variables.keys())}")
            self._log("Parsing des variables terminé")
            
            # --- ÉTAPE 2 : DÉCOUPAGE INTELLIGENT ---
            # Maintenant qu'on a du SQL pur, on le découpe sans risque
            statements = self.split_sql_statements(parsed_sql)
            
            if not statements:
                self._log("⚠ Aucune instruction SQL à exécuter", 'WARNING')
                return SqlExecutionResult(
                    success=True,
                    duration_ms=int((time.time() - start_time) * 1000),
                    logs='\n'.join(self._logs),
                    rows_affected=0,
                    statements_executed=0,
                    statements_failed=0
                )
            
            errors = []
            
            # --- ÉTAPE 3 : SÉPARER LES COMMANDES TRANSACTIONNELLES ET NON-TRANSACTIONNELLES ---
            transactional_stmts = []
            non_transactional_stmts = []
            
            for stmt in statements:
                if self._is_transaction_forbidden(stmt):
                    non_transactional_stmts.append(stmt)
                else:
                    transactional_stmts.append(stmt)
            
            if non_transactional_stmts:
                self._log(f"⚠ {len(non_transactional_stmts)} commande(s) hors-transaction détectée(s)", 'WARNING')
            
            # --- ÉTAPE 4A : EXÉCUTION DES COMMANDES TRANSACTIONNELLES ---
            if transactional_stmts:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    self._log(f"Transaction démarrée ({len(transactional_stmts)} instruction(s))")
                    
                    for i, statement in enumerate(transactional_stmts, 1):
                        try:
                            # Log du début d'instruction (tronqué si trop long)
                            stmt_preview = statement[:100] + '...' if len(statement) > 100 else statement
                            self._log(f"[{i}/{len(transactional_stmts)}] Exécution : {stmt_preview}")
                            
                            cursor.execute(statement)
                            
                            # Compter les lignes affectées si disponible
                            if cursor.rowcount and cursor.rowcount > 0:
                                total_rows_affected += cursor.rowcount
                                self._log(f"  → {cursor.rowcount} ligne(s) affectée(s)")
                            
                            statements_executed += 1
                            self._log(f"✓ Instruction {i} exécutée")
                        
                        except Exception as e:
                            statements_failed += 1
                            error_msg = f"✗ Erreur instruction {i}: {str(e)}"
                            self._log(error_msg, 'ERROR')
                            errors.append(error_msg)
                            
                            if stop_on_error:
                                # Rollback en cas d'erreur avec stop_on_error
                                conn.rollback()
                                self._log("ROLLBACK effectué suite à l'erreur", 'WARNING')
                                raise SqlExecutionError(error_msg)
                            else:
                                # Continuer en mode best effort
                                self._log("Poursuite de l'exécution (stop_on_error=False)", 'WARNING')
                    
                    # COMMIT si succès et auto_commit activé
                    if auto_commit:
                        if statements_failed == 0 or not stop_on_error:
                            conn.commit()
                            self._log("COMMIT effectué - Modifications enregistrées")
                        else:
                            conn.rollback()
                            self._log("ROLLBACK effectué - Aucune modification enregistrée")
                    else:
                        self._log("Mode manuel : COMMIT non effectué (vous devez appeler commit())")
                    
                    cursor.close()
            
            # --- ÉTAPE 4B : EXÉCUTION DES COMMANDES HORS-TRANSACTION (AUTOCOMMIT) ---
            if non_transactional_stmts:
                self._log(f"=== Exécution des commandes hors-transaction ({len(non_transactional_stmts)}) ===")
                
                for i, statement in enumerate(non_transactional_stmts, 1):
                    try:
                        stmt_preview = statement[:100] + '...' if len(statement) > 100 else statement
                        self._log(f"[HT-{i}/{len(non_transactional_stmts)}] Exécution AUTOCOMMIT : {stmt_preview}")
                        
                        # Exécuter en mode autocommit (nouvelle connexion)
                        self._execute_autocommit(statement)
                        
                        statements_executed += 1
                        self._log(f"✓ Commande hors-transaction {i} exécutée")
                    
                    except Exception as e:
                        statements_failed += 1
                        error_msg = f"✗ Erreur commande hors-transaction {i}: {str(e)}"
                        self._log(error_msg, 'ERROR')
                        errors.append(error_msg)
                        
                        if stop_on_error:
                            raise SqlExecutionError(error_msg)
                        else:
                            self._log("Poursuite de l'exécution (stop_on_error=False)", 'WARNING')
            
            # Vérifier si on a eu des erreurs en mode best effort
            if statements_failed > 0 and not stop_on_error:
                self._log(f"⚠ {statements_failed} erreur(s) rencontrée(s) en mode best effort", 'WARNING')
            
            duration_ms = int((time.time() - start_time) * 1000)
            success = statements_failed == 0 or not stop_on_error
            
            summary = f"Durée: {duration_ms}ms - {statements_executed} exécutée(s), {statements_failed} échouée(s)"
            if total_rows_affected > 0:
                summary += f", {total_rows_affected} ligne(s) affectée(s)"
            self._log(f"=== FIN EXÉCUTION - {summary} ===")
            
            return SqlExecutionResult(
                success=success,
                duration_ms=duration_ms,
                logs='\n'.join(self._logs),
                error_message='\n'.join(errors) if errors else None,
                rows_affected=total_rows_affected,
                statements_executed=statements_executed,
                statements_failed=statements_failed
            )
        
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            self._log(f"=== ÉCHEC EXÉCUTION - {error_msg} ===", 'ERROR')
            
            return SqlExecutionResult(
                success=False,
                duration_ms=duration_ms,
                logs='\n'.join(self._logs),
                error_message=error_msg,
                statements_executed=statements_executed,
                statements_failed=statements_failed
            )
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Teste la connexion à la base de données.
        
        Returns:
            Tuple (success, message)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Requête de test selon le type de DB
                if self.db_type == 'postgresql':
                    cursor.execute("SELECT version()")
                elif self.db_type == 'oracle':
                    cursor.execute("SELECT * FROM DUAL")
                elif self.db_type == 'sqlserver':
                    cursor.execute("SELECT @@VERSION")
                elif self.db_type == 'mysql':
                    cursor.execute("SELECT VERSION()")
                
                result = cursor.fetchone()
                cursor.close()
                
                return True, f"Connexion réussie à {self.datasource.name}"
        
        except Exception as e:
            return False, f"Échec de connexion : {str(e)}"
