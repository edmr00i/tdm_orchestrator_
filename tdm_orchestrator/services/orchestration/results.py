"""
Résultats d'exécution de l'orchestration.

Ce module contient les dataclasses pour les résultats
d'exécution des steps et runners.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class StepResult:
    """Résultat d'exécution d'un step."""
    script_name: str
    script_reference: str
    step_type: str  # 'pre' ou 'post'
    order: int
    success: bool
    duration_ms: int
    error_message: Optional[str] = None
    rows_affected: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire."""
        return {
            'script_name': self.script_name,
            'script_reference': self.script_reference,
            'step_type': self.step_type,
            'order': self.order,
            'success': self.success,
            'duration_ms': self.duration_ms,
            'error': self.error_message,
            'rows_affected': self.rows_affected,
        }


@dataclass
class RunnerExecutionResult:
    """Résultat d'exécution d'un runner complet."""
    runner_id: int
    runner_name: str
    execution_log_id: Optional[int] = None
    overall_success: bool = True
    total_duration_ms: int = 0
    pre_scripts: List[StepResult] = field(default_factory=list)
    post_scripts: List[StepResult] = field(default_factory=list)
    error_message: Optional[str] = None
    
    @property
    def pre_success_count(self) -> int:
        """Nombre de scripts PRE réussis."""
        return sum(1 for s in self.pre_scripts if s.success)
    
    @property
    def post_success_count(self) -> int:
        """Nombre de scripts POST réussis."""
        return sum(1 for s in self.post_scripts if s.success)
    
    @property
    def total_scripts(self) -> int:
        """Nombre total de scripts."""
        return len(self.pre_scripts) + len(self.post_scripts)
    
    @property
    def failed_scripts(self) -> List[StepResult]:
        """Liste des scripts échoués."""
        return [s for s in self.pre_scripts + self.post_scripts if not s.success]
    
    def add_pre_result(self, result: StepResult):
        """Ajoute un résultat de script PRE."""
        self.pre_scripts.append(result)
        if not result.success:
            self.overall_success = False
    
    def add_post_result(self, result: StepResult):
        """Ajoute un résultat de script POST."""
        self.post_scripts.append(result)
        if not result.success:
            self.overall_success = False
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire pour l'API."""
        return {
            'runner_id': self.runner_id,
            'runner_name': self.runner_name,
            'execution_log_id': self.execution_log_id,
            'overall_success': self.overall_success,
            'total_duration_ms': self.total_duration_ms,
            'pre_scripts': [s.to_dict() for s in self.pre_scripts],
            'post_scripts': [s.to_dict() for s in self.post_scripts],
            'summary': {
                'total': self.total_scripts,
                'pre_success': self.pre_success_count,
                'post_success': self.post_success_count,
                'failed': len(self.failed_scripts),
            },
            'error_message': self.error_message,
        }
