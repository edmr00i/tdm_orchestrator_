"""
ViewSets pour le monitoring (ExecutionLog).

Ce module contient les ViewSets pour la consultation des logs d'exécution.
"""

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from tdm_orchestrator.models import ExecutionLog
from tdm_orchestrator.serializers import ExecutionLogSerializer


class ExecutionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet READ-ONLY pour consulter les logs d'exécution."""
    
    serializer_class = ExecutionLogSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'runner', 'script', 'executed_by']
    ordering_fields = ['started_at', 'duration_ms']
    ordering = ['-started_at']
    
    def get_queryset(self):
        return ExecutionLog.objects.select_related(
            'runner', 'script', 'executed_by'
        )
