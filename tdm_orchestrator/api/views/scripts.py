"""
ViewSets pour les scripts SQL.

Ce module contient les ViewSets pour la gestion des scripts SQL.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .mixins import SoftDeleteMixin, IncludeDeletedMixin
from tdm_orchestrator.models import SqlScript, ExecutionLog
from tdm_orchestrator.serializers import (
    SqlScriptListSerializer,
    SqlScriptDetailSerializer,
)
from tdm_orchestrator.services.sql import SqlExecutor
from tdm_orchestrator.services.exceptions import SqlExecutionError


class SqlScriptViewSet(SoftDeleteMixin, IncludeDeletedMixin, viewsets.ModelViewSet):
    """ViewSet pour la gestion des scripts SQL."""
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['script_type', 'application', 'datasource', 'is_active']
    search_fields = ['reference', 'name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = SqlScript.objects.select_related(
            'application', 'datasource', 'created_by'
        )
        return self.filter_deleted(queryset)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SqlScriptListSerializer
        return SqlScriptDetailSerializer
    
    @action(detail=True, methods=['get'])
    def variables(self, request, pk=None):
        """Retourne les variables extraites du script."""
        script = self.get_object()
        variables = script.extract_variables()
        
        return Response({
            'script_id': script.id,
            'script_name': script.name,
            'variables': variables,
            'count': len(variables)
        })
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Valide un script en mode dry run."""
        script = self.get_object()
        variables = request.data.get('variables', {})
        
        if not script.datasource:
            return Response(
                {'detail': 'Aucune datasource configurée pour ce script.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            executor = SqlExecutor(script.datasource)
            result = executor.execute_dry_run(script.content, variables)
            
            return Response({
                'success': result.success,
                'duration_ms': result.duration_ms,
                'logs': result.logs,
                'error_message': result.error_message,
                'statements_executed': result.statements_executed,
            })
        
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Exécute un script réellement."""
        script = self.get_object()
        variables = request.data.get('variables', {})
        
        if not script.datasource:
            return Response(
                {'detail': 'Aucune datasource configurée pour ce script.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        execution_log = None
        try:
            executor = SqlExecutor(script.datasource)
            
            # Créer le log d'exécution
            execution_log = ExecutionLog.objects.create(
                script=script,
                status='RUNNING',
                executed_by=request.user if request.user.is_authenticated else None,
                variables_used=variables
            )
            
            result = executor.execute(script.content, variables)
            
            if result.success:
                execution_log.mark_success(result.logs)
            else:
                execution_log.mark_failure(result.error_message, result.logs)
            
            return Response({
                'execution_log_id': execution_log.id,
                'success': result.success,
                'duration_ms': result.duration_ms,
                'rows_affected': result.rows_affected,
                'logs': result.logs,
                'error_message': result.error_message,
            })
        
        except Exception as e:
            if execution_log:
                execution_log.mark_failure(str(e))
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def parse(self, request, pk=None):
        """Parse le script avec les variables fournies."""
        script = self.get_object()
        variables = request.data.get('variables', {})
        
        if not isinstance(variables, dict):
            return Response(
                {'detail': 'Le champ variables doit être un objet.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            parsed_content = script.get_parsed_content(variables)
            
            return Response({
                'script_id': script.id,
                'script_name': script.name,
                'original_content': script.content,
                'parsed_content': parsed_content,
                'variables_used': variables
            })
        except Exception as e:
            return Response(
                {'detail': f'Erreur lors du parsing: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
