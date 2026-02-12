"""
Résultat d'exécution SQL.

Ce module contient la dataclass représentant le résultat
d'une exécution SQL avec tous les détails.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class SqlExecutionResult:
    """
    Résultat d'une exécution SQL.
    
    Attributes:
        success: Indique si l'exécution a réussi
        duration_ms: Durée de l'exécution en millisecondes
        logs: Logs détaillés de l'exécution
        error_message: Message d'erreur si échec
        rows_affected: Nombre de lignes affectées
        statements_executed: Nombre d'instructions exécutées avec succès
        statements_failed: Nombre d'instructions échouées
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
    
    @property
    def has_errors(self) -> bool:
        """Indique si des erreurs ont été rencontrées."""
        return self.statements_failed > 0 or self.error_message is not None
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire pour sérialisation API."""
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
    
    @classmethod
    def success_result(cls, duration_ms: int, logs: str, 
                       statements_executed: int = 0, 
                       rows_affected: int = None) -> 'SqlExecutionResult':
        """Factory method pour créer un résultat de succès."""
        return cls(
            success=True,
            duration_ms=duration_ms,
            logs=logs,
            statements_executed=statements_executed,
            rows_affected=rows_affected
        )
    
    @classmethod
    def failure_result(cls, duration_ms: int, logs: str, 
                       error_message: str,
                       statements_executed: int = 0,
                       statements_failed: int = 0) -> 'SqlExecutionResult':
        """Factory method pour créer un résultat d'échec."""
        return cls(
            success=False,
            duration_ms=duration_ms,
            logs=logs,
            error_message=error_message,
            statements_executed=statements_executed,
            statements_failed=statements_failed
        )
