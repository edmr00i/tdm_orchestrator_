"""
Orchestrateur d'exécution de runners.

Ce service coordonne l'exécution des scripts SQL d'un runner
en utilisant SqlExecutor et en gérant les logs d'exécution.
"""

import time
import logging
from typing import Dict, Optional

from .results import StepResult, RunnerExecutionResult
from ..sql import SqlExecutor
from ..exceptions import (
    OrchestrationError,
    StepExecutionError,
    SqlExecutionError,
)

logger = logging.getLogger(__name__)


class RunnerOrchestrator:
    """
    Orchestrateur pour l'exécution de runners.
    
    Coordonne l'exécution des scripts PRE et POST en utilisant
    SqlExecutor. Gère les logs d'exécution et le comportement
    stop_on_error.
    
    Example:
        >>> orchestrator = RunnerOrchestrator(runner)
        >>> result = orchestrator.execute({'SCHEMA': 'test'})
        >>> if result.overall_success:
        ...     print("Tous les scripts exécutés avec succès")
    """
    
    def __init__(self, runner, user=None):
        """
        Initialise l'orchestrateur.
        
        Args:
            runner: Instance de Runner (modèle Django)
            user: Utilisateur exécutant (optionnel)
        """
        self.runner = runner
        self.user = user
        self._executors: Dict[int, SqlExecutor] = {}
    
    def _get_executor(self, datasource) -> SqlExecutor:
        """
        Obtient ou crée un SqlExecutor pour une datasource.
        
        Utilise un cache pour réutiliser les executors.
        """
        if datasource.id not in self._executors:
            self._executors[datasource.id] = SqlExecutor(datasource)
        return self._executors[datasource.id]
    
    def _execute_step(self, step, variables: Dict[str, str], 
                      step_type: str) -> StepResult:
        """
        Exécute un seul step.
        
        Args:
            step: Instance de RunnerStep
            variables: Variables à substituer
            step_type: 'pre' ou 'post'
            
        Returns:
            StepResult avec le résultat
        """
        script = step.script
        
        # Vérifier la datasource
        if not script.datasource:
            return StepResult(
                script_name=script.name,
                script_reference=script.reference,
                step_type=step_type,
                order=step.order,
                success=False,
                duration_ms=0,
                error_message='Aucune datasource configurée'
            )
        
        try:
            executor = self._get_executor(script.datasource)
            result = executor.execute(script.content, variables)
            
            return StepResult(
                script_name=script.name,
                script_reference=script.reference,
                step_type=step_type,
                order=step.order,
                success=result.success,
                duration_ms=result.duration_ms,
                error_message=result.error_message,
                rows_affected=result.rows_affected
            )
        
        except Exception as e:
            logger.error(f"Erreur step {step.order}: {str(e)}")
            return StepResult(
                script_name=script.name,
                script_reference=script.reference,
                step_type=step_type,
                order=step.order,
                success=False,
                duration_ms=0,
                error_message=str(e)
            )
    
    def _create_execution_log(self, variables: Dict[str, str]):
        """Crée un log d'exécution."""
        from tdm_orchestrator.models import ExecutionLog
        
        return ExecutionLog.objects.create(
            runner=self.runner,
            status='RUNNING',
            executed_by=self.user if self.user and self.user.is_authenticated else None,
            variables_used=variables
        )
    
    def execute(self, variables: Optional[Dict[str, str]] = None,
                create_log: bool = True) -> RunnerExecutionResult:
        """
        Exécute le runner complet.
        
        Args:
            variables: Variables à substituer
            create_log: Créer un ExecutionLog
            
        Returns:
            RunnerExecutionResult avec tous les détails
        """
        variables = variables or {}
        start_time = time.time()
        
        logger.info(f"Début exécution runner : {self.runner.name}")
        
        # Créer le résultat
        result = RunnerExecutionResult(
            runner_id=self.runner.id,
            runner_name=self.runner.name
        )
        
        # Créer le log d'exécution
        execution_log = None
        if create_log:
            try:
                execution_log = self._create_execution_log(variables)
                result.execution_log_id = execution_log.id
            except Exception as e:
                logger.warning(f"Impossible de créer le log : {e}")
        
        try:
            # Exécuter les scripts PRE
            for step in self.runner.get_pre_scripts():
                step_result = self._execute_step(step, variables, 'pre')
                result.add_pre_result(step_result)
                
                if not step_result.success and self.runner.stop_on_error:
                    result.error_message = f"Échec PRE: {step.script.name}"
                    break
            
            # Exécuter les scripts POST (si pas d'erreur bloquante)
            if result.overall_success or not self.runner.stop_on_error:
                for step in self.runner.get_post_scripts():
                    step_result = self._execute_step(step, variables, 'post')
                    result.add_post_result(step_result)
                    
                    if not step_result.success and self.runner.stop_on_error:
                        result.error_message = f"Échec POST: {step.script.name}"
                        break
            
            # Calculer la durée totale
            result.total_duration_ms = int((time.time() - start_time) * 1000)
            
            # Mettre à jour le log
            if execution_log:
                if result.overall_success:
                    execution_log.mark_success("Exécution terminée avec succès")
                else:
                    execution_log.mark_failure(result.error_message or "Échec d'exécution")
            
            logger.info(
                f"Fin exécution runner : {result.overall_success} "
                f"({result.total_duration_ms}ms)"
            )
            
            return result
        
        except Exception as e:
            result.overall_success = False
            result.error_message = str(e)
            result.total_duration_ms = int((time.time() - start_time) * 1000)
            
            if execution_log:
                execution_log.mark_failure(str(e))
            
            logger.error(f"Erreur orchestration : {e}")
            return result
    
    def execute_dry_run(self, variables: Optional[Dict[str, str]] = None) -> RunnerExecutionResult:
        """
        Exécute le runner en mode validation (dry run).
        
        Valide tous les scripts sans les exécuter réellement.
        
        Args:
            variables: Variables à substituer
            
        Returns:
            RunnerExecutionResult avec la validation
        """
        variables = variables or {}
        start_time = time.time()
        
        logger.info(f"Dry run runner : {self.runner.name}")
        
        result = RunnerExecutionResult(
            runner_id=self.runner.id,
            runner_name=self.runner.name
        )
        
        # Valider les scripts PRE
        for step in self.runner.get_pre_scripts():
            step_result = self._validate_step(step, variables, 'pre')
            result.add_pre_result(step_result)
        
        # Valider les scripts POST
        for step in self.runner.get_post_scripts():
            step_result = self._validate_step(step, variables, 'post')
            result.add_post_result(step_result)
        
        result.total_duration_ms = int((time.time() - start_time) * 1000)
        
        return result
    
    def _validate_step(self, step, variables: Dict[str, str], 
                       step_type: str) -> StepResult:
        """Valide un step en dry run."""
        script = step.script
        
        if not script.datasource:
            return StepResult(
                script_name=script.name,
                script_reference=script.reference,
                step_type=step_type,
                order=step.order,
                success=False,
                duration_ms=0,
                error_message='Aucune datasource configurée'
            )
        
        try:
            executor = self._get_executor(script.datasource)
            result = executor.execute_dry_run(script.content, variables)
            
            return StepResult(
                script_name=script.name,
                script_reference=script.reference,
                step_type=step_type,
                order=step.order,
                success=result.success,
                duration_ms=result.duration_ms,
                error_message=result.error_message
            )
        
        except Exception as e:
            return StepResult(
                script_name=script.name,
                script_reference=script.reference,
                step_type=step_type,
                order=step.order,
                success=False,
                duration_ms=0,
                error_message=str(e)
            )
