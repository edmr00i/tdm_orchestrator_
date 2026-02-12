"""
Module de compatibilité pour les imports existants.

Ce fichier conserve la rétro-compatibilité avec les imports depuis views.py
Les ViewSets ont été déplacés vers api/views/ pour une meilleure organisation.

MIGRATION : Utilisez plutôt les imports depuis tdm_orchestrator.api.views
"""

# Re-export depuis le nouveau package pour compatibilité
from .api.views import (
    TypeViewSet,
    EntityViewSet,
    DataSourceViewSet,
    ApplicationViewSet,
    SqlScriptViewSet,
    RunnerViewSet,
    ExecutionLogViewSet,
)

__all__ = [
    'TypeViewSet',
    'EntityViewSet',
    'DataSourceViewSet',
    'ApplicationViewSet',
    'SqlScriptViewSet',
    'RunnerViewSet',
    'ExecutionLogViewSet',
]
