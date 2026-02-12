"""
Exceptions personnalisées pour les services TDM Orchestrator.

Ce module centralise toutes les exceptions métier pour éviter
la duplication et faciliter la gestion des erreurs.
"""


class TDMOrchestratorError(Exception):
    """Exception de base pour toutes les erreurs TDM Orchestrator."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# =====================
# Exceptions SQL
# =====================
class SqlExecutionError(TDMOrchestratorError):
    """Exception levée lors d'erreurs d'exécution SQL."""
    pass


class DatabaseConnectionError(TDMOrchestratorError):
    """Exception levée lors d'erreurs de connexion à la base de données."""
    pass


class SqlSplitError(TDMOrchestratorError):
    """Exception levée lors d'erreurs de découpage SQL."""
    pass


# =====================
# Exceptions Parsing
# =====================
class VariableParsingError(TDMOrchestratorError):
    """Exception levée lors d'erreurs de parsing de variables."""
    pass


class VariableValidationError(VariableParsingError):
    """Exception levée lors d'erreurs de validation de variables."""
    pass


# =====================
# Exceptions Export
# =====================
class ExportError(TDMOrchestratorError):
    """Exception levée lors d'erreurs d'export."""
    pass


class ZipCreationError(ExportError):
    """Exception levée lors d'erreurs de création de ZIP."""
    pass


class ConfigGenerationError(ExportError):
    """Exception levée lors d'erreurs de génération de configuration."""
    pass


# =====================
# Exceptions Orchestration
# =====================
class OrchestrationError(TDMOrchestratorError):
    """Exception levée lors d'erreurs d'orchestration."""
    pass


class StepExecutionError(OrchestrationError):
    """Exception levée lors d'erreurs d'exécution d'une étape."""
    
    def __init__(self, message: str, step_name: str = None, step_order: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.step_name = step_name
        self.step_order = step_order


class RunnerExecutionError(OrchestrationError):
    """Exception levée lors d'erreurs d'exécution d'un runner."""
    
    def __init__(self, message: str, runner_id: int = None, runner_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.runner_id = runner_id
        self.runner_name = runner_name
