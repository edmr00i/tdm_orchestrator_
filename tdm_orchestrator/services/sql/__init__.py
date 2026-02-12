"""
Package SQL - Services d'exécution SQL.

Ce package contient tous les composants pour exécuter des scripts SQL
sur différentes bases de données.
"""

from .result import SqlExecutionResult
from .connection import ConnectionManager
from .splitters import get_splitter, BaseSqlSplitter
from .executor import SqlExecutor

__all__ = [
    'SqlExecutor',
    'SqlExecutionResult',
    'ConnectionManager',
    'get_splitter',
    'BaseSqlSplitter',
]
