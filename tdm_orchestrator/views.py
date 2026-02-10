"""
ViewSets pour les APIs REST du module TDM SQL Orchestrator.
"""

import datetime
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .services.variable_parser import parse_sql_variables, VariableParsingError
from .services.sql_executor import SqlExecutor, SqlExecutionError
from .services.export_service import RunnerExporter, ExportError

from .models import (
    Type,
    Entity,
    DataSource,
    Application,
    SqlScript,
    Runner,
    RunnerStep,
    ExecutionLog,
)
from .serializers import (
    TypeSerializer,
    EntityListSerializer,
    EntityDetailSerializer,
    DataSourceListSerializer,
    DataSourceDetailSerializer,
    DataSourceCreateUpdateSerializer,
    ApplicationListSerializer,
    ApplicationDetailSerializer,
    ApplicationCreateUpdateSerializer,
    SqlScriptListSerializer,
    SqlScriptDetailSerializer,
    RunnerListSerializer,
    RunnerDetailSerializer,
    RunnerCreateUpdateSerializer,
    ExecutionLogSerializer,
)


# =====================
# Type ViewSet
# =====================
class TypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des types.
    
    Endpoints:
    - GET    /api/types/          : Liste des types
    - POST   /api/types/          : Créer un type
    - GET    /api/types/{id}/     : Détail d'un type
    - PUT    /api/types/{id}/     : Mettre à jour un type
    - PATCH  /api/types/{id}/     : Mettre à jour partiellement
    - DELETE /api/types/{id}/     : Supprimer un type (soft delete)
    """
    
    serializer_class = TypeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type_list', 'source', 'is_active', 'lock']
    search_fields = ['reference', 'value_char']
    ordering_fields = ['created_at', 'value_char']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Retourne les types non supprimés."""
        queryset = Type.objects.all()
        
        include_deleted = self.request.query_params.get('include_deleted', 'false').lower() == 'true'
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        # Filtrage par type_list
        type_list = self.request.query_params.get('type_list')
        if type_list:
            queryset = queryset.filter(type_list=type_list)
        
        return queryset
    
    def perform_destroy(self, instance):
        """Soft delete."""
        instance.is_deleted = True
        instance.is_active = False
        instance.save()


# =====================
# Entity ViewSet
# =====================
class EntityViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des entités.
    
    Endpoints:
    - GET    /api/entities/          : Liste des entités
    - POST   /api/entities/          : Créer une entité
    - GET    /api/entities/{id}/     : Détail d'une entité
    - PUT    /api/entities/{id}/     : Mettre à jour une entité
    - PATCH  /api/entities/{id}/     : Mettre à jour partiellement
    - DELETE /api/entities/{id}/     : Supprimer une entité (soft delete)
    """
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'forme_juridique', 'type_entite', 'parent']
    search_fields = ['reference', 'name', 'siret', 'sigle']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Retourne les entités non supprimées."""
        queryset = Entity.objects.select_related(
            'forme_juridique',
            'type_entite',
            'parent',
            'created_by'
        )
        
        include_deleted = self.request.query_params.get('include_deleted', 'false').lower() == 'true'
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        return queryset
    
    def get_serializer_class(self):
        """Utilise un serializer différent pour la liste et le détail."""
        if self.action == 'list':
            return EntityListSerializer
        return EntityDetailSerializer
    
    def perform_destroy(self, instance):
        """Soft delete."""
        instance.is_deleted = True
        instance.is_active = False
        instance.save()
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restaure une entité supprimée."""
        entity = self.get_object()
        
        if not entity.is_deleted:
            return Response(
                {'detail': 'Cette entité n\'est pas supprimée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        entity.is_deleted = False
        entity.is_active = True
        entity.save()
        
        serializer = self.get_serializer(entity)
        return Response(serializer.data)


# =====================
# DataSource ViewSet
# =====================
class DataSourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des sources de données.
    
    Endpoints:
    - GET    /api/datasources/          : Liste des sources
    - POST   /api/datasources/          : Créer une source
    - GET    /api/datasources/{id}/     : Détail d'une source
    - PUT    /api/datasources/{id}/     : Mettre à jour une source
    - PATCH  /api/datasources/{id}/     : Mettre à jour partiellement
    - DELETE /api/datasources/{id}/     : Supprimer une source (soft delete)
    """
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'sgbd_name', 'sgbd_tls', 'sgbd_x509']
    search_fields = ['reference', 'name', 'sgbd_host', 'sgbd_database']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Retourne les sources non supprimées."""
        queryset = DataSource.objects.select_related(
            'sgbd_name',
            'created_by'
        )
        
        include_deleted = self.request.query_params.get('include_deleted', 'false').lower() == 'true'
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        return queryset
    
    def get_serializer_class(self):
        """Utilise un serializer différent selon l'action."""
        if self.action == 'list':
            return DataSourceListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DataSourceCreateUpdateSerializer
        return DataSourceDetailSerializer
    
    def perform_destroy(self, instance):
        """Soft delete."""
        instance.is_deleted = True
        instance.is_active = False
        instance.save()
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restaure une source de données supprimée."""
        datasource = self.get_object()
        
        if not datasource.is_deleted:
            return Response(
                {'detail': 'Cette source de données n\'est pas supprimée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        datasource.is_deleted = False
        datasource.is_active = True
        datasource.save()
        
        serializer = self.get_serializer(datasource)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Teste la connexion à la source de données."""
        datasource = self.get_object()
        # TODO: Implémenter le test de connexion réel
        return Response({
            'datasource_id': datasource.id,
            'datasource_name': datasource.name,
            'status': 'not_implemented',
            'message': 'Le test de connexion n\'est pas encore implémenté.'
        })


# =====================
# Application ViewSet
# =====================
class ApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des applications.
    
    Endpoints:
    - GET    /api/applications/          : Liste des applications
    - POST   /api/applications/          : Créer une application
    - GET    /api/applications/{id}/     : Détail d'une application
    - PUT    /api/applications/{id}/     : Mettre à jour une application
    - PATCH  /api/applications/{id}/     : Mettre à jour partiellement
    - DELETE /api/applications/{id}/     : Supprimer une application (soft delete)
    """
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'type1']
    search_fields = ['reference', 'name', 'description', 'ip_address']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Retourne les applications non supprimées."""
        queryset = Application.objects.select_related(
            'type1',
            'created_by'
        ).prefetch_related(
            'entity',
            'data_sources'
        )
        
        include_deleted = self.request.query_params.get('include_deleted', 'false').lower() == 'true'
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        return queryset
    
    def get_serializer_class(self):
        """Utilise un serializer différent selon l'action."""
        if self.action == 'list':
            return ApplicationListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ApplicationCreateUpdateSerializer
        return ApplicationDetailSerializer
    
    def perform_destroy(self, instance):
        """Soft delete."""
        instance.is_deleted = True
        instance.is_active = False
        instance.save()
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restaure une application supprimée."""
        application = self.get_object()
        
        if not application.is_deleted:
            return Response(
                {'detail': 'Cette application n\'est pas supprimée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.is_deleted = False
        application.is_active = True
        application.save()
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def scripts(self, request, pk=None):
        """Retourne les scripts associés à l'application."""
        application = self.get_object()
        scripts = application.sql_scripts.filter(is_deleted=False, is_active=True)
        
        return Response({
            'application_id': application.id,
            'application_name': application.name,
            'scripts': SqlScriptListSerializer(scripts, many=True).data,
            'count': scripts.count()
        })
    
    @action(detail=True, methods=['get'])
    def runners(self, request, pk=None):
        """Retourne les runners associés à l'application."""
        application = self.get_object()
        runners = application.runners.filter(is_deleted=False, is_active=True)
        
        return Response({
            'application_id': application.id,
            'application_name': application.name,
            'runners': RunnerListSerializer(runners, many=True).data,
            'count': runners.count()
        })


# =====================
# SqlScript ViewSet
# =====================
class SqlScriptViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des scripts SQL.
    
    Endpoints:
    - GET    /api/scripts/          : Liste des scripts
    - POST   /api/scripts/          : Créer un script
    - GET    /api/scripts/{id}/     : Détail d'un script
    - PUT    /api/scripts/{id}/     : Mettre à jour un script
    - PATCH  /api/scripts/{id}/     : Mettre à jour partiellement
    - DELETE /api/scripts/{id}/     : Supprimer un script (soft delete)
    """
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['script_type', 'application', 'datasource', 'is_active']
    search_fields = ['reference', 'name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Retourne les scripts non supprimés.
        Possibilité d'inclure les supprimés avec ?include_deleted=true
        """
        queryset = SqlScript.objects.select_related(
            'application',
            'datasource',
            'created_by'
        )
        
        # Par défaut, exclure les supprimés
        include_deleted = self.request.query_params.get('include_deleted', 'false').lower() == 'true'
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        return queryset
    
    def get_serializer_class(self):
        """Utilise un serializer différent pour la liste et le détail."""
        if self.action == 'list':
            return SqlScriptListSerializer
        return SqlScriptDetailSerializer
    
    def perform_destroy(self, instance):
        """Soft delete au lieu de supprimer."""
        instance.is_deleted = True
        instance.is_active = False
        instance.save()
    
    @action(detail=True, methods=['get'])
    def variables(self, request, pk=None):
        """
        Retourne les variables extraites du script.
        
        GET /api/scripts/{id}/variables/
        """
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
        """
        Valide un script en mode dry run.
        
        POST /api/scripts/{id}/validate/
        Body: { "variables": {"SCHEMA": "test"} }
        """
        script = self.get_object()
        variables = request.data.get('variables', {})
        
        if not script.datasource:
            return Response(
                {'detail': 'Aucune datasource configurée pour ce script.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Créer l'executor
            executor = SqlExecutor(script.datasource)
            
            # Exécuter en dry run
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
        """
        Exécute un script réellement.
        
        POST /api/scripts/{id}/execute/
        Body: { "variables": {"SCHEMA": "production"} }
        """
        script = self.get_object()
        variables = request.data.get('variables', {})
        
        if not script.datasource:
            return Response(
                {'detail': 'Aucune datasource configurée pour ce script.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Créer l'executor
            executor = SqlExecutor(script.datasource)
            
            # Créer le log d'exécution
            from .models import ExecutionLog
            execution_log = ExecutionLog.objects.create(
                script=script,
                status='RUNNING',
                executed_by=request.user,
                variables_used=variables
            )
            
            # Exécuter
            result = executor.execute(script.content, variables)
            
            # Mettre à jour le log
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
            execution_log.mark_failure(str(e))
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def parse(self, request, pk=None):
        """
        Parse le script avec les variables fournies.
        
        POST /api/scripts/{id}/parse/
        Body: { "variables": { "SCHEMA": "production", "DATE": "2024-01-01" } }
        """
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


# =====================
# Runner ViewSet
# =====================
class RunnerViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des runners (orchestrateurs).
    
    Endpoints:
    - GET    /api/runners/          : Liste des runners
    - POST   /api/runners/          : Créer un runner
    - GET    /api/runners/{id}/     : Détail d'un runner
    - PUT    /api/runners/{id}/     : Mettre à jour un runner
    - PATCH  /api/runners/{id}/     : Mettre à jour partiellement
    - DELETE /api/runners/{id}/     : Supprimer un runner (soft delete)
    """
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['application', 'is_active', 'stop_on_error']
    search_fields = ['reference', 'name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Retourne les runners non supprimés.
        Possibilité d'inclure les supprimés avec ?include_deleted=true
        """
        queryset = Runner.objects.select_related(
            'application',
            'created_by'
        ).prefetch_related(
            'runnerstep_set__script'
        )
        
        # Par défaut, exclure les supprimés
        include_deleted = self.request.query_params.get('include_deleted', 'false').lower() == 'true'
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        return queryset
    
    def get_serializer_class(self):
        """Utilise un serializer différent selon l'action."""
        if self.action == 'list':
            return RunnerListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RunnerCreateUpdateSerializer
        return RunnerDetailSerializer
    
    def perform_destroy(self, instance):
        """Soft delete au lieu de supprimer."""
        instance.is_deleted = True
        instance.is_active = False
        instance.save()
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restaure un runner supprimé."""
        runner = self.get_object()
        
        if not runner.is_deleted:
            return Response(
                {'detail': 'Ce runner n\'est pas supprimé.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        runner.is_deleted = False
        runner.is_active = True
        runner.save()
        
        serializer = self.get_serializer(runner)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def execution_plan(self, request, pk=None):
        """
        Retourne le plan d'exécution du runner.
        
        GET /api/runners/{id}/execution_plan/
        """
        runner = self.get_object()
        return Response(runner.get_execution_plan())
    
    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """
        Exporte le runner en ZIP.
        
        GET /api/runners/{id}/export/
        """
        runner = self.get_object()
        
        try:
            # Créer l'exporter
            exporter = RunnerExporter(runner)
            
            # Générer le ZIP
            zip_path = exporter.export()
            
            # Retourner le fichier
            from django.http import FileResponse
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
        """
        Retourne les infos d'export sans générer le ZIP.
        
        GET /api/runners/{id}/export_info/
        """
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
        """
        Exécute le runner complet.
        
        POST /api/runners/{id}/execute/
        Body: { "variables": {"SCHEMA": "test", "DATE": "2024-01-01"} }
        """
        runner = self.get_object()
        variables = request.data.get('variables', {})
        
        # Créer un log global
        execution_log = ExecutionLog.objects.create(
            runner=runner,
            status='RUNNING',
            executed_by=request.user if request.user.is_authenticated else None,
            variables_used=variables
        )
        
        results = {
            'runner_id': runner.id,
            'runner_name': runner.name,
            'execution_log_id': execution_log.id,
            'pre_scripts': [],
            'post_scripts': [],
            'overall_success': True,
        }
        
        try:
            # Exécuter les scripts PRE
            for step in runner.get_pre_scripts():
                script = step.script
                
                if not script.datasource:
                    results['pre_scripts'].append({
                        'script_name': script.name,
                        'success': False,
                        'duration_ms': 0,
                        'error': 'Aucune datasource configurée',
                    })
                    continue
                
                executor = SqlExecutor(script.datasource)
                result = executor.execute(script.content, variables)
                
                results['pre_scripts'].append({
                    'script_name': script.name,
                    'success': result.success,
                    'duration_ms': result.duration_ms,
                    'error': result.error_message,
                })
                
                # Arrêter si erreur et stop_on_error
                if not result.success and runner.stop_on_error:
                    results['overall_success'] = False
                    execution_log.mark_failure(f"Échec script PRE: {script.name}")
                    return Response(results, status=status.HTTP_200_OK)
            
            # Exécuter les scripts POST
            for step in runner.get_post_scripts():
                script = step.script
                
                if not script.datasource:
                    results['post_scripts'].append({
                        'script_name': script.name,
                        'success': False,
                        'duration_ms': 0,
                        'error': 'Aucune datasource configurée',
                    })
                    continue
                
                executor = SqlExecutor(script.datasource)
                result = executor.execute(script.content, variables)
                
                results['post_scripts'].append({
                    'script_name': script.name,
                    'success': result.success,
                    'duration_ms': result.duration_ms,
                    'error': result.error_message,
                })
                
                if not result.success and runner.stop_on_error:
                    results['overall_success'] = False
                    execution_log.mark_failure(f"Échec script POST: {script.name}")
                    return Response(results, status=status.HTTP_200_OK)
            
            # Succès global
            execution_log.mark_success("Tous les scripts exécutés avec succès")
            return Response(results)
        
        except Exception as e:
            execution_log.mark_failure(str(e))
            return Response(
                {'detail': str(e), 'execution_log_id': execution_log.id},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =====================
# ExecutionLog ViewSet
# =====================
class ExecutionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet READ-ONLY pour consulter les logs d'exécution.
    
    Endpoints:
    - GET /api/execution-logs/          : Liste des logs
    - GET /api/execution-logs/{id}/     : Détail d'un log
    """
    
    serializer_class = ExecutionLogSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'runner', 'script', 'executed_by']
    ordering_fields = ['started_at', 'duration_ms']
    ordering = ['-started_at']
    
    def get_queryset(self):
        """Retourne tous les logs."""
        return ExecutionLog.objects.select_related(
            'runner',
            'script',
            'executed_by'
        )
