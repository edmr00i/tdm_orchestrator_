"""
Package Services - Services métier du TDM Orchestrator.

Ce package contient tous les services métier, organisés par domaine :
- sql/ : Exécution SQL (connexions, splitters, executor)
- parsers/ : Parsing de variables
- export/ : Export de runners en ZIP
- orchestration/ : Orchestration des runners
"""

# Exceptions centralisées
from .exceptions import (
    TDMOrchestratorError,
    SqlExecutionError,
    DatabaseConnectionError,
    SqlSplitError,
    VariableParsingError,
    VariableValidationError,
    ExportError,
    ZipCreationError,
    ConfigGenerationError,
    OrchestrationError,
    StepExecutionError,
    RunnerExecutionError,
)

# Services SQL
from .sql import (
    SqlExecutor,
    SqlExecutionResult,
    ConnectionManager,
)

# Parsers
from .parsers import (
    VariableParser,
    parse_sql_variables,
    extract_sql_variables,
)

# Export
from .export import (
    RunnerExporter,
    export_runner_to_zip,
)

# Orchestration
from .orchestration import (
    RunnerOrchestrator,
    StepResult,
    RunnerExecutionResult,
)

__all__ = [
    # Exceptions
    'TDMOrchestratorError',
    'SqlExecutionError',
    'DatabaseConnectionError',
    'SqlSplitError',
    'VariableParsingError',
    'VariableValidationError',
    'ExportError',
    'ZipCreationError',
    'ConfigGenerationError',
    'OrchestrationError',
    'StepExecutionError',
    'RunnerExecutionError',
    
    # SQL
    'SqlExecutor',
    'SqlExecutionResult',
    'ConnectionManager',
    
    # Parsers
    'VariableParser',
    'parse_sql_variables',
    'extract_sql_variables',
    
    # Export
    'RunnerExporter',
    'export_runner_to_zip',
    
    # Orchestration
    'RunnerOrchestrator',
    'StepResult',
    'RunnerExecutionResult',
]
