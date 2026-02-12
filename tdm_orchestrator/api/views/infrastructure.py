"""
ViewSets pour l'infrastructure (Type, Entity, DataSource, Application).

Ce module contient les ViewSets pour la gestion des entités
d'infrastructure du système.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .mixins import SoftDeleteMixin, IncludeDeletedMixin
from tdm_orchestrator.models import Type, Entity, DataSource, Application
from tdm_orchestrator.serializers import (
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
    RunnerListSerializer,
)


class TypeViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des types."""
    
    serializer_class = TypeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type_list', 'source', 'is_active', 'lock']
    search_fields = ['reference', 'value_char']
    ordering_fields = ['created_at', 'value_char']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Type.objects.all()
        
        include_deleted = (
            self.request.query_params.get('include_deleted', 'false').lower() == 'true'
        )
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        type_list = self.request.query_params.get('type_list')
        if type_list:
            queryset = queryset.filter(type_list=type_list)
        
        return queryset
    
    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.is_active = False
        instance.save()


class EntityViewSet(SoftDeleteMixin, IncludeDeletedMixin, viewsets.ModelViewSet):
    """ViewSet pour la gestion des entités."""
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'forme_juridique', 'type_entite', 'parent']
    search_fields = ['reference', 'name', 'siret', 'sigle']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Entity.objects.select_related(
            'forme_juridique', 'type_entite', 'parent', 'created_by'
        )
        return self.filter_deleted(queryset)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EntityListSerializer
        return EntityDetailSerializer


class DataSourceViewSet(SoftDeleteMixin, IncludeDeletedMixin, viewsets.ModelViewSet):
    """ViewSet pour la gestion des sources de données."""
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'sgbd_name', 'sgbd_tls', 'sgbd_x509']
    search_fields = ['reference', 'name', 'sgbd_host', 'sgbd_database']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = DataSource.objects.select_related('sgbd_name', 'created_by')
        return self.filter_deleted(queryset)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DataSourceListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DataSourceCreateUpdateSerializer
        return DataSourceDetailSerializer
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Teste la connexion à la source de données."""
        datasource = self.get_object()
        
        try:
            from tdm_orchestrator.services.sql import SqlExecutor
            executor = SqlExecutor(datasource)
            success, message = executor.test_connection()
            
            return Response({
                'datasource_id': datasource.id,
                'datasource_name': datasource.name,
                'success': success,
                'message': message,
            })
        except Exception as e:
            return Response({
                'datasource_id': datasource.id,
                'datasource_name': datasource.name,
                'success': False,
                'message': str(e),
            })


class ApplicationViewSet(SoftDeleteMixin, IncludeDeletedMixin, viewsets.ModelViewSet):
    """ViewSet pour la gestion des applications."""
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'type1']
    search_fields = ['reference', 'name', 'description', 'ip_address']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Application.objects.select_related(
            'type1', 'created_by'
        ).prefetch_related('entity', 'data_sources')
        return self.filter_deleted(queryset)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ApplicationListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ApplicationCreateUpdateSerializer
        return ApplicationDetailSerializer
    
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
