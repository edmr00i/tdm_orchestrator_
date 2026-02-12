"""
ViewSets pour l'orchestration (Runner, RunnerStep).

Ce module contient les ViewSets pour la gestion des runners
et leur exécution.
"""

import datetime
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend

from .mixins import SoftDeleteMixin, IncludeDeletedMixin
from tdm_orchestrator.models import Runner
from tdm_orchestrator.serializers import (
    RunnerListSerializer,
    RunnerDetailSerializer,
    RunnerCreateUpdateSerializer,
)
from tdm_orchestrator.services.orchestration import RunnerOrchestrator
from tdm_orchestrator.services.export import RunnerExporter
from tdm_orchestrator.services.exceptions import ExportError


class RunnerViewSet(SoftDeleteMixin, IncludeDeletedMixin, viewsets.ModelViewSet):
    """ViewSet pour la gestion des runners (orchestrateurs)."""
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['application', 'is_active', 'stop_on_error']
    search_fields = ['reference', 'name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Runner.objects.select_related(
            'application', 'created_by'
        ).prefetch_related('runnerstep_set__script')
        return self.filter_deleted(queryset)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RunnerListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RunnerCreateUpdateSerializer
        return RunnerDetailSerializer
    
    @action(detail=True, methods=['get'])
    def execution_plan(self, request, pk=None):
        """Retourne le plan d'exécution du runner."""
        runner = self.get_object()
        return Response(runner.get_execution_plan())
    
    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """Exporte le runner en ZIP."""
        runner = self.get_object()
        
        try:
            exporter = RunnerExporter(runner)
            zip_path = exporter.export()
            
            response = FileResponse(
                open(zip_path, 'rb'),
                content_type='application/zip'
            )
            filename = f"runner_{runner.reference}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
        
        except ExportError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def export_info(self, request, pk=None):
        """Retourne les infos d'export sans générer le ZIP."""
        runner = self.get_object()
        
        try:
            exporter = RunnerExporter(runner)
            info = exporter.get_export_info()
            return Response(info)
        
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Exécute le runner complet."""
        runner = self.get_object()
        variables = request.data.get('variables', {})
        
        try:
            orchestrator = RunnerOrchestrator(runner, user=request.user)
            result = orchestrator.execute(variables)
            
            return Response(result.to_dict())
        
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Valide le runner en dry run."""
        runner = self.get_object()
        variables = request.data.get('variables', {})
        
        try:
            orchestrator = RunnerOrchestrator(runner)
            result = orchestrator.execute_dry_run(variables)
            
            return Response(result.to_dict())
        
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
