"""
Executor SQL principal allégé.

Ce module coordonne les services de connexion, parsing et exécution.
La logique métier lourde est déléguée aux sous-modules.
"""

import re
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

from .result import SqlExecutionResult
from .connection import ConnectionManager
from .splitters import get_splitter
from ..parsers.variable_parser import VariableParser
from ..constants import TRANSACTION_FORBIDDEN_PATTERNS, LOG_TIMESTAMP_FORMAT
from ..exceptions import SqlExecutionError, DatabaseConnectionError

logger = logging.getLogger(__name__)


class SqlExecutor:
    """
    Executor SQL utilisant la composition des services.
    
    Cette classe coordonne :
    - ConnectionManager pour les connexions
    - VariableParser pour le parsing des variables
    - Splitters pour le découpage SQL
    
    Example:
        >>> executor = SqlExecutor(datasource)
        >>> result = executor.execute_dry_run(sql, variables)
        >>> if result.success:
        ...     result = executor.execute(sql, variables)
    """
    
    def __init__(self, datasource):
        """
        Initialise l'executor avec une datasource.
        
        Args:
            datasource: Objet DataSource du modèle Django
        """
        self.datasource = datasource
        self.connection_manager = ConnectionManager(datasource)
        self.variable_parser = VariableParser(strict_mode=False)
        self.splitter = get_splitter(self.connection_manager.db_type)
        self._logs: List[str] = []
    
    @property
    def db_type(self) -> str:
        """Type de base de données."""
        return self.connection_manager.db_type
    
    def _log(self, message: str, level: str = 'INFO'):
        """Ajoute un message au log interne."""
        timestamp = datetime.now().strftime(LOG_TIMESTAMP_FORMAT)
        log_entry = f"[{timestamp}] [{level}] {message}"
        self._logs.append(log_entry)
        
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(message)
    
    def _is_transaction_forbidden(self, sql: str) -> bool:
        """Détecte les commandes qui ne supportent pas les transactions."""
        return any(
            re.search(pattern, sql, re.IGNORECASE) 
            for pattern in TRANSACTION_FORBIDDEN_PATTERNS
        )
    
    def _execute_autocommit(self, statement: str) -> None:
        """Exécute une commande en mode autocommit."""
        try:
            with self.connection_manager.get_connection(autocommit=True) as conn:
                cursor = conn.cursor()
                cursor.execute(statement)
                cursor.close()
        except Exception as e:
            raise SqlExecutionError(f"Erreur autocommit : {str(e)}")
    
    def _parse_and_split(self, sql_content: str, variables: Dict[str, str], 
                         strict: bool = False) -> List[str]:
        """Parse les variables et découpe le SQL."""
        parsed_sql = self.variable_parser.parse(
            sql_content, 
            variables or {}, 
            strict_validation=strict
        )
        return self.splitter.split(parsed_sql)
    
    def execute_dry_run(self, sql_content: str, 
                        variables: Optional[Dict[str, str]] = None,
                        strict_variables: bool = False) -> SqlExecutionResult:
        """
        Exécute le SQL en mode dry run (ROLLBACK systématique).
        
        Args:
            sql_content: Contenu SQL à exécuter
            variables: Variables à substituer
            strict_variables: Valide les noms de variables
            
        Returns:
            SqlExecutionResult avec le résultat de validation
        """
        self._logs = []
        start_time = time.time()
        statements_executed = 0
        statements_failed = 0
        
        try:
            self._log("=== DÉBUT DRY RUN ===")
            self._log(f"Base : {self.db_type} ({self.datasource.name})")
            
            statements = self._parse_and_split(sql_content, variables or {}, strict_variables)
            
            if variables:
                self._log(f"Variables : {list(variables.keys())}")
            
            if not statements:
                self._log("⚠ Aucune instruction SQL", 'WARNING')
                return SqlExecutionResult.success_result(
                    duration_ms=int((time.time() - start_time) * 1000),
                    logs='\n'.join(self._logs),
                    statements_executed=0
                )
            
            with self.connection_manager.get_connection() as conn:
                cursor = conn.cursor()
                self._log("Transaction démarrée")
                
                for i, statement in enumerate(statements, 1):
                    try:
                        preview = statement[:100] + '...' if len(statement) > 100 else statement
                        self._log(f"[{i}/{len(statements)}] {preview}")
                        cursor.execute(statement)
                        statements_executed += 1
                        self._log(f"✓ Instruction {i} validée")
                    except Exception as e:
                        statements_failed += 1
                        raise SqlExecutionError(f"Erreur instruction {i}: {str(e)}")
                
                conn.rollback()
                self._log("ROLLBACK effectué")
                cursor.close()
            
            duration_ms = int((time.time() - start_time) * 1000)
            self._log(f"=== FIN DRY RUN - {duration_ms}ms ===")
            
            return SqlExecutionResult.success_result(
                duration_ms=duration_ms,
                logs='\n'.join(self._logs),
                statements_executed=statements_executed
            )
        
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return SqlExecutionResult.failure_result(
                duration_ms=duration_ms,
                logs='\n'.join(self._logs),
                error_message=str(e),
                statements_executed=statements_executed,
                statements_failed=statements_failed
            )
    
    def execute(self, sql_content: str, 
                variables: Optional[Dict[str, str]] = None,
                auto_commit: bool = True,
                dry_run: bool = False,
                strict_variables: bool = False,
                stop_on_error: bool = True) -> SqlExecutionResult:
        """
        Exécute le SQL réellement.
        
        Args:
            sql_content: Contenu SQL à exécuter
            variables: Variables à substituer
            auto_commit: COMMIT automatique si succès
            dry_run: Mode validation (ROLLBACK)
            strict_variables: Valide les noms de variables
            stop_on_error: Arrête à la première erreur
            
        Returns:
            SqlExecutionResult détaillé
        """
        if dry_run:
            return self.execute_dry_run(sql_content, variables, strict_variables)
        
        self._logs = []
        start_time = time.time()
        statements_executed = 0
        statements_failed = 0
        total_rows_affected = 0
        errors = []
        
        try:
            self._log("=== DÉBUT EXÉCUTION ===")
            self._log(f"Base : {self.db_type} ({self.datasource.name})")
            
            statements = self._parse_and_split(sql_content, variables or {}, strict_variables)
            
            if not statements:
                self._log("⚠ Aucune instruction SQL", 'WARNING')
                return SqlExecutionResult.success_result(
                    duration_ms=int((time.time() - start_time) * 1000),
                    logs='\n'.join(self._logs),
                    statements_executed=0,
                    rows_affected=0
                )
            
            # Séparer les commandes transactionnelles et non-transactionnelles
            transactional = [s for s in statements if not self._is_transaction_forbidden(s)]
            non_transactional = [s for s in statements if self._is_transaction_forbidden(s)]
            
            if non_transactional:
                self._log(f"⚠ {len(non_transactional)} commande(s) hors-transaction", 'WARNING')
            
            # Exécution transactionnelle
            if transactional:
                with self.connection_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    self._log(f"Transaction : {len(transactional)} instruction(s)")
                    
                    for i, stmt in enumerate(transactional, 1):
                        try:
                            preview = stmt[:100] + '...' if len(stmt) > 100 else stmt
                            self._log(f"[{i}/{len(transactional)}] {preview}")
                            cursor.execute(stmt)
                            
                            if cursor.rowcount and cursor.rowcount > 0:
                                total_rows_affected += cursor.rowcount
                            
                            statements_executed += 1
                        except Exception as e:
                            statements_failed += 1
                            error_msg = f"Erreur instruction {i}: {str(e)}"
                            errors.append(error_msg)
                            self._log(f"✗ {error_msg}", 'ERROR')
                            
                            if stop_on_error:
                                conn.rollback()
                                raise SqlExecutionError(error_msg)
                    
                    if auto_commit and (statements_failed == 0 or not stop_on_error):
                        conn.commit()
                        self._log("COMMIT effectué")
                    else:
                        conn.rollback()
                        self._log("ROLLBACK effectué")
                    
                    cursor.close()
            
            # Exécution hors-transaction
            for i, stmt in enumerate(non_transactional, 1):
                try:
                    self._log(f"[HT-{i}] AUTOCOMMIT")
                    self._execute_autocommit(stmt)
                    statements_executed += 1
                except Exception as e:
                    statements_failed += 1
                    error_msg = f"Erreur HT-{i}: {str(e)}"
                    errors.append(error_msg)
                    if stop_on_error:
                        raise SqlExecutionError(error_msg)
            
            duration_ms = int((time.time() - start_time) * 1000)
            success = statements_failed == 0 or not stop_on_error
            
            self._log(f"=== FIN - {statements_executed} OK, {statements_failed} KO ===")
            
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
            return SqlExecutionResult.failure_result(
                duration_ms=duration_ms,
                logs='\n'.join(self._logs),
                error_message=str(e),
                statements_executed=statements_executed,
                statements_failed=statements_failed
            )
    
    def test_connection(self) -> tuple:
        """Teste la connexion à la base de données."""
        return self.connection_manager.test_connection()
