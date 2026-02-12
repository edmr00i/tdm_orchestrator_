"""
Tests for Infrastructure ViewSets - Type, Entity, DataSource, Application API endpoints.

Covers:
- TypeViewSet: get_queryset, perform_destroy, configuration
- EntityViewSet: get_queryset, get_serializer_class, configuration
- DataSourceViewSet: get_queryset, get_serializer_class, test_connection action, configuration
- ApplicationViewSet: get_queryset, get_serializer_class, scripts action, runners action, configuration
"""

from unittest.mock import MagicMock

import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from tdm_orchestrator.api.views.infrastructure import (
    TypeViewSet,
    EntityViewSet,
    DataSourceViewSet,
    ApplicationViewSet,
)


# =====================
# Fixtures
# =====================

@pytest.fixture
def api_factory():
    """Create an APIRequestFactory instance."""
    return APIRequestFactory()


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    user.is_authenticated = True
    return user


@pytest.fixture
def mock_type_instance():
    """Create a mock Type instance."""
    type_obj = MagicMock()
    type_obj.id = 1
    type_obj.pk = 1
    type_obj.reference = "TYPE_001"
    type_obj.value_char = "Test Type"
    type_obj.type_list = "SGBD"
    type_obj.source = "SYSTEM"
    type_obj.is_active = True
    type_obj.is_deleted = False
    type_obj.lock = False
    type_obj.save = MagicMock()
    return type_obj


@pytest.fixture
def mock_entity_instance():
    """Create a mock Entity instance."""
    entity = MagicMock()
    entity.id = 1
    entity.pk = 1
    entity.reference = "ENTITY_001"
    entity.name = "Test Entity"
    entity.siret = "12345678901234"
    entity.sigle = "TE"
    entity.is_active = True
    entity.is_deleted = False
    entity.forme_juridique = MagicMock()
    entity.type_entite = MagicMock()
    entity.parent = None
    entity.created_by = MagicMock()
    return entity


@pytest.fixture
def mock_datasource_instance():
    """Create a mock DataSource instance."""
    ds = MagicMock()
    ds.id = 1
    ds.pk = 1
    ds.reference = "DS_001"
    ds.name = "Test DataSource"
    ds.sgbd_host = "localhost"
    ds.sgbd_database = "testdb"
    ds.sgbd_name = MagicMock()
    ds.sgbd_tls = False
    ds.sgbd_x509 = False
    ds.is_active = True
    ds.is_deleted = False
    ds.created_by = MagicMock()
    return ds


@pytest.fixture
def mock_application_instance():
    """Create a mock Application instance."""
    app = MagicMock()
    app.id = 1
    app.pk = 1
    app.reference = "APP_001"
    app.name = "Test Application"
    app.description = "Test description"
    app.ip_address = "192.168.1.1"
    app.is_active = True
    app.is_deleted = False
    app.type1 = MagicMock()
    app.created_by = MagicMock()
    app.entity = MagicMock()
    app.data_sources = MagicMock()
    
    # Mock related managers
    mock_scripts = MagicMock()
    mock_scripts.filter.return_value = mock_scripts
    mock_scripts.count.return_value = 2
    app.sql_scripts = mock_scripts
    
    mock_runners = MagicMock()
    mock_runners.filter.return_value = mock_runners
    mock_runners.count.return_value = 3
    app.runners = mock_runners
    
    return app


@pytest.fixture
def mock_queryset():
    """Create a mock queryset."""
    qs = MagicMock()
    qs.all.return_value = qs
    qs.filter.return_value = qs
    qs.exclude.return_value = qs
    qs.select_related.return_value = qs
    qs.prefetch_related.return_value = qs
    return qs


# =====================
# TypeViewSet Tests
# =====================

class TestTypeViewSetGetQueryset:
    """Tests for TypeViewSet.get_queryset method."""

    def test_returns_all_types_by_default(self, mocker):
        """Returns all non-deleted types by default."""
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        
        mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.Type.objects',
            mock_qs
        )
        
        viewset = TypeViewSet()
        viewset.request = MagicMock()
        viewset.request.query_params = {}
        
        viewset.get_queryset()
        
        mock_qs.all.assert_called_once()

    def test_filters_deleted_when_include_deleted_false(self, mocker):
        """Filters deleted types when include_deleted=false."""
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        
        mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.Type.objects',
            mock_qs
        )
        
        viewset = TypeViewSet()
        viewset.request = MagicMock()
        viewset.request.query_params = {'include_deleted': 'false'}
        
        viewset.get_queryset()
        
        mock_qs.filter.assert_any_call(is_deleted=False)

    def test_includes_deleted_when_include_deleted_true(self, mocker):
        """Includes deleted types when include_deleted=true."""
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        
        mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.Type.objects',
            mock_qs
        )
        
        viewset = TypeViewSet()
        viewset.request = MagicMock()
        viewset.request.query_params = {'include_deleted': 'true'}
        
        result = viewset.get_queryset()
        
        # Should not filter by is_deleted
        filter_calls = [call for call in mock_qs.filter.call_args_list 
                       if 'is_deleted' in str(call)]
        assert len(filter_calls) == 0

    def test_filters_by_type_list_when_provided(self, mocker):
        """Filters by type_list when query param provided."""
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        
        mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.Type.objects',
            mock_qs
        )
        
        viewset = TypeViewSet()
        viewset.request = MagicMock()
        viewset.request.query_params = {'type_list': 'SGBD'}
        
        viewset.get_queryset()
        
        mock_qs.filter.assert_any_call(type_list='SGBD')

    def test_does_not_filter_by_type_list_when_not_provided(self, mocker):
        """Does not filter by type_list when param not provided."""
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        
        mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.Type.objects',
            mock_qs
        )
        
        viewset = TypeViewSet()
        viewset.request = MagicMock()
        viewset.request.query_params = {}
        
        viewset.get_queryset()
        
        # Check that type_list filter was not called
        type_list_calls = [call for call in mock_qs.filter.call_args_list 
                         if 'type_list' in str(call)]
        assert len(type_list_calls) == 0


class TestTypeViewSetPerformDestroy:
    """Tests for TypeViewSet.perform_destroy method."""

    def test_sets_is_deleted_to_true(self, mock_type_instance):
        """Sets is_deleted to True on instance."""
        viewset = TypeViewSet()
        
        viewset.perform_destroy(mock_type_instance)
        
        assert mock_type_instance.is_deleted is True

    def test_sets_is_active_to_false(self, mock_type_instance):
        """Sets is_active to False on instance."""
        viewset = TypeViewSet()
        
        viewset.perform_destroy(mock_type_instance)
        
        assert mock_type_instance.is_active is False

    def test_calls_save_on_instance(self, mock_type_instance):
        """Calls save() on instance."""
        viewset = TypeViewSet()
        
        viewset.perform_destroy(mock_type_instance)
        
        mock_type_instance.save.assert_called_once()


class TestTypeViewSetConfiguration:
    """Tests for TypeViewSet class configuration."""

    def test_serializer_class_is_type_serializer(self):
        """Serializer class is TypeSerializer."""
        from tdm_orchestrator.serializers import TypeSerializer
        
        assert TypeViewSet.serializer_class == TypeSerializer

    def test_filter_backends_configured(self):
        """Filter backends are configured correctly."""
        from django_filters.rest_framework import DjangoFilterBackend
        from rest_framework import filters
        
        assert DjangoFilterBackend in TypeViewSet.filter_backends
        assert filters.SearchFilter in TypeViewSet.filter_backends
        assert filters.OrderingFilter in TypeViewSet.filter_backends

    def test_filterset_fields_configured(self):
        """Filterset fields are configured correctly."""
        expected_fields = ['type_list', 'source', 'is_active', 'lock']
        
        assert TypeViewSet.filterset_fields == expected_fields

    def test_search_fields_configured(self):
        """Search fields are configured correctly."""
        expected_fields = ['reference', 'value_char']
        
        assert TypeViewSet.search_fields == expected_fields

    def test_ordering_fields_configured(self):
        """Ordering fields are configured correctly."""
        expected_fields = ['created_at', 'value_char']
        
        assert TypeViewSet.ordering_fields == expected_fields

    def test_default_ordering_configured(self):
        """Default ordering is configured correctly."""
        assert TypeViewSet.ordering == ['-created_at']


# =====================
# EntityViewSet Tests
# =====================

class TestEntityViewSetGetQueryset:
    """Tests for EntityViewSet.get_queryset method."""

    def test_calls_select_related_with_correct_fields(self, mocker):
        """Calls select_related with forme_juridique, type_entite, parent, created_by."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        
        mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.Entity.objects',
            mock_qs
        )
        
        viewset = EntityViewSet()
        viewset.request = MagicMock()
        viewset.request.query_params = {}
        
        # Mock filter_deleted to return the queryset
        viewset.filter_deleted = MagicMock(return_value=mock_qs)
        
        viewset.get_queryset()
        
        mock_qs.select_related.assert_called_once_with(
            'forme_juridique', 'type_entite', 'parent', 'created_by'
        )

    def test_calls_filter_deleted(self, mocker):
        """Calls filter_deleted mixin method."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        
        mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.Entity.objects',
            mock_qs
        )
        
        viewset = EntityViewSet()
        viewset.request = MagicMock()
        viewset.request.query_params = {}
        mock_filter_deleted = MagicMock(return_value=mock_qs)
        viewset.filter_deleted = mock_filter_deleted
        
        viewset.get_queryset()
        
        mock_filter_deleted.assert_called_once_with(mock_qs)


class TestEntityViewSetGetSerializerClass:
    """Tests for EntityViewSet.get_serializer_class method."""

    def test_returns_list_serializer_for_list_action(self, mocker):
        """Returns EntityListSerializer for list action."""
        viewset = EntityViewSet()
        viewset.action = 'list'
        
        mock_list_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.EntityListSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_list_serializer

    def test_returns_detail_serializer_for_retrieve_action(self, mocker):
        """Returns EntityDetailSerializer for retrieve action."""
        viewset = EntityViewSet()
        viewset.action = 'retrieve'
        
        mock_detail_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.EntityDetailSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_detail_serializer

    def test_returns_detail_serializer_for_create_action(self, mocker):
        """Returns EntityDetailSerializer for create action."""
        viewset = EntityViewSet()
        viewset.action = 'create'
        
        mock_detail_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.EntityDetailSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_detail_serializer


class TestEntityViewSetConfiguration:
    """Tests for EntityViewSet class configuration."""

    def test_inherits_from_soft_delete_mixin(self):
        """EntityViewSet inherits from SoftDeleteMixin."""
        from tdm_orchestrator.api.views.mixins import SoftDeleteMixin
        
        assert issubclass(EntityViewSet, SoftDeleteMixin)

    def test_inherits_from_include_deleted_mixin(self):
        """EntityViewSet inherits from IncludeDeletedMixin."""
        from tdm_orchestrator.api.views.mixins import IncludeDeletedMixin
        
        assert issubclass(EntityViewSet, IncludeDeletedMixin)

    def test_filterset_fields_configured(self):
        """Filterset fields are configured correctly."""
        expected_fields = ['is_active', 'forme_juridique', 'type_entite', 'parent']
        
        assert EntityViewSet.filterset_fields == expected_fields

    def test_search_fields_configured(self):
        """Search fields are configured correctly."""
        expected_fields = ['reference', 'name', 'siret', 'sigle']
        
        assert EntityViewSet.search_fields == expected_fields

    def test_ordering_fields_configured(self):
        """Ordering fields are configured correctly."""
        expected_fields = ['created_at', 'updated_at', 'name']
        
        assert EntityViewSet.ordering_fields == expected_fields

    def test_default_ordering_configured(self):
        """Default ordering is configured correctly."""
        assert EntityViewSet.ordering == ['-created_at']


# =====================
# DataSourceViewSet Tests
# =====================

class TestDataSourceViewSetGetQueryset:
    """Tests for DataSourceViewSet.get_queryset method."""

    def test_calls_select_related_with_correct_fields(self, mocker):
        """Calls select_related with sgbd_name, created_by."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        
        mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.DataSource.objects',
            mock_qs
        )
        
        viewset = DataSourceViewSet()
        viewset.request = MagicMock()
        viewset.request.query_params = {}
        viewset.filter_deleted = MagicMock(return_value=mock_qs)
        
        viewset.get_queryset()
        
        mock_qs.select_related.assert_called_once_with('sgbd_name', 'created_by')

    def test_calls_filter_deleted(self, mocker):
        """Calls filter_deleted mixin method."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        
        mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.DataSource.objects',
            mock_qs
        )
        
        viewset = DataSourceViewSet()
        viewset.request = MagicMock()
        viewset.request.query_params = {}
        mock_filter_deleted = MagicMock(return_value=mock_qs)
        viewset.filter_deleted = mock_filter_deleted
        
        viewset.get_queryset()
        
        mock_filter_deleted.assert_called_once_with(mock_qs)


class TestDataSourceViewSetGetSerializerClass:
    """Tests for DataSourceViewSet.get_serializer_class method."""

    def test_returns_list_serializer_for_list_action(self, mocker):
        """Returns DataSourceListSerializer for list action."""
        viewset = DataSourceViewSet()
        viewset.action = 'list'
        
        mock_list_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.DataSourceListSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_list_serializer

    def test_returns_create_update_serializer_for_create_action(self, mocker):
        """Returns DataSourceCreateUpdateSerializer for create action."""
        viewset = DataSourceViewSet()
        viewset.action = 'create'
        
        mock_create_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.DataSourceCreateUpdateSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_create_serializer

    def test_returns_create_update_serializer_for_update_action(self, mocker):
        """Returns DataSourceCreateUpdateSerializer for update action."""
        viewset = DataSourceViewSet()
        viewset.action = 'update'
        
        mock_create_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.DataSourceCreateUpdateSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_create_serializer

    def test_returns_create_update_serializer_for_partial_update_action(self, mocker):
        """Returns DataSourceCreateUpdateSerializer for partial_update action."""
        viewset = DataSourceViewSet()
        viewset.action = 'partial_update'
        
        mock_create_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.DataSourceCreateUpdateSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_create_serializer

    def test_returns_detail_serializer_for_retrieve_action(self, mocker):
        """Returns DataSourceDetailSerializer for retrieve action."""
        viewset = DataSourceViewSet()
        viewset.action = 'retrieve'
        
        mock_detail_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.DataSourceDetailSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_detail_serializer


class TestDataSourceViewSetTestConnection:
    """Tests for DataSourceViewSet.test_connection action."""

    def test_returns_success_response_on_successful_connection(
        self, mock_datasource_instance, api_factory, mock_user, mocker
    ):
        """Returns success response when connection succeeds."""
        mock_executor = MagicMock()
        mock_executor.test_connection.return_value = (True, "Connection successful")
        
        mocker.patch(
            'tdm_orchestrator.services.sql.SqlExecutor',
            return_value=mock_executor
        )
        
        viewset = DataSourceViewSet()
        viewset.get_object = MagicMock(return_value=mock_datasource_instance)
        
        request = api_factory.post('/datasources/1/test_connection/')
        request.user = mock_user
        
        response = viewset.test_connection(request, pk=1)
        
        assert response.data['success'] is True
        assert response.data['message'] == "Connection successful"

    def test_returns_failure_response_on_failed_connection(
        self, mock_datasource_instance, api_factory, mock_user, mocker
    ):
        """Returns failure response when connection fails."""
        mock_executor = MagicMock()
        mock_executor.test_connection.return_value = (False, "Connection refused")
        
        mocker.patch(
            'tdm_orchestrator.services.sql.SqlExecutor',
            return_value=mock_executor
        )
        
        viewset = DataSourceViewSet()
        viewset.get_object = MagicMock(return_value=mock_datasource_instance)
        
        request = api_factory.post('/datasources/1/test_connection/')
        request.user = mock_user
        
        response = viewset.test_connection(request, pk=1)
        
        assert response.data['success'] is False
        assert response.data['message'] == "Connection refused"

    def test_returns_datasource_id_in_response(
        self, mock_datasource_instance, api_factory, mock_user, mocker
    ):
        """Returns datasource_id in response."""
        mock_executor = MagicMock()
        mock_executor.test_connection.return_value = (True, "OK")
        
        mocker.patch(
            'tdm_orchestrator.services.sql.SqlExecutor',
            return_value=mock_executor
        )
        
        viewset = DataSourceViewSet()
        viewset.get_object = MagicMock(return_value=mock_datasource_instance)
        
        request = api_factory.post('/datasources/1/test_connection/')
        request.user = mock_user
        
        response = viewset.test_connection(request, pk=1)
        
        assert response.data['datasource_id'] == 1

    def test_returns_datasource_name_in_response(
        self, mock_datasource_instance, api_factory, mock_user, mocker
    ):
        """Returns datasource_name in response."""
        mock_executor = MagicMock()
        mock_executor.test_connection.return_value = (True, "OK")
        
        mocker.patch(
            'tdm_orchestrator.services.sql.SqlExecutor',
            return_value=mock_executor
        )
        
        viewset = DataSourceViewSet()
        viewset.get_object = MagicMock(return_value=mock_datasource_instance)
        
        request = api_factory.post('/datasources/1/test_connection/')
        request.user = mock_user
        
        response = viewset.test_connection(request, pk=1)
        
        assert response.data['datasource_name'] == "Test DataSource"

    def test_handles_exception_gracefully(
        self, mock_datasource_instance, api_factory, mock_user, mocker
    ):
        """Handles exception and returns failure response."""
        mocker.patch(
            'tdm_orchestrator.services.sql.SqlExecutor',
            side_effect=Exception("Import error")
        )
        
        viewset = DataSourceViewSet()
        viewset.get_object = MagicMock(return_value=mock_datasource_instance)
        
        request = api_factory.post('/datasources/1/test_connection/')
        request.user = mock_user
        
        response = viewset.test_connection(request, pk=1)
        
        assert response.data['success'] is False
        assert response.data['message'] == "Import error"

    def test_calls_get_object(
        self, mock_datasource_instance, api_factory, mock_user, mocker
    ):
        """Calls get_object to retrieve datasource."""
        mock_executor = MagicMock()
        mock_executor.test_connection.return_value = (True, "OK")
        
        mocker.patch(
            'tdm_orchestrator.services.sql.SqlExecutor',
            return_value=mock_executor
        )
        
        viewset = DataSourceViewSet()
        mock_get_object = MagicMock(return_value=mock_datasource_instance)
        viewset.get_object = mock_get_object
        
        request = api_factory.post('/datasources/1/test_connection/')
        request.user = mock_user
        
        viewset.test_connection(request, pk=1)
        
        mock_get_object.assert_called_once()

    def test_calls_sql_executor_with_datasource(
        self, mock_datasource_instance, api_factory, mock_user, mocker
    ):
        """Calls SqlExecutor with datasource."""
        mock_executor = MagicMock()
        mock_executor.test_connection.return_value = (True, "OK")
        
        mock_executor_class = mocker.patch(
            'tdm_orchestrator.services.sql.SqlExecutor',
            return_value=mock_executor
        )
        
        viewset = DataSourceViewSet()
        viewset.get_object = MagicMock(return_value=mock_datasource_instance)
        
        request = api_factory.post('/datasources/1/test_connection/')
        request.user = mock_user
        
        viewset.test_connection(request, pk=1)
        
        mock_executor_class.assert_called_once_with(mock_datasource_instance)


class TestDataSourceViewSetConfiguration:
    """Tests for DataSourceViewSet class configuration."""

    def test_inherits_from_soft_delete_mixin(self):
        """DataSourceViewSet inherits from SoftDeleteMixin."""
        from tdm_orchestrator.api.views.mixins import SoftDeleteMixin
        
        assert issubclass(DataSourceViewSet, SoftDeleteMixin)

    def test_inherits_from_include_deleted_mixin(self):
        """DataSourceViewSet inherits from IncludeDeletedMixin."""
        from tdm_orchestrator.api.views.mixins import IncludeDeletedMixin
        
        assert issubclass(DataSourceViewSet, IncludeDeletedMixin)

    def test_filterset_fields_configured(self):
        """Filterset fields are configured correctly."""
        expected_fields = ['is_active', 'sgbd_name', 'sgbd_tls', 'sgbd_x509']
        
        assert DataSourceViewSet.filterset_fields == expected_fields

    def test_search_fields_configured(self):
        """Search fields are configured correctly."""
        expected_fields = ['reference', 'name', 'sgbd_host', 'sgbd_database']
        
        assert DataSourceViewSet.search_fields == expected_fields

    def test_ordering_fields_configured(self):
        """Ordering fields are configured correctly."""
        expected_fields = ['created_at', 'updated_at', 'name']
        
        assert DataSourceViewSet.ordering_fields == expected_fields

    def test_default_ordering_configured(self):
        """Default ordering is configured correctly."""
        assert DataSourceViewSet.ordering == ['-created_at']


# =====================
# ApplicationViewSet Tests
# =====================

class TestApplicationViewSetGetQueryset:
    """Tests for ApplicationViewSet.get_queryset method."""

    def test_calls_select_related_with_correct_fields(self, mocker):
        """Calls select_related with type1, created_by."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.prefetch_related.return_value = mock_qs
        
        mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.Application.objects',
            mock_qs
        )
        
        viewset = ApplicationViewSet()
        viewset.request = MagicMock()
        viewset.request.query_params = {}
        viewset.filter_deleted = MagicMock(return_value=mock_qs)
        
        viewset.get_queryset()
        
        mock_qs.select_related.assert_called_once_with('type1', 'created_by')

    def test_calls_prefetch_related_with_correct_fields(self, mocker):
        """Calls prefetch_related with entity, data_sources."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.prefetch_related.return_value = mock_qs
        
        mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.Application.objects',
            mock_qs
        )
        
        viewset = ApplicationViewSet()
        viewset.request = MagicMock()
        viewset.request.query_params = {}
        viewset.filter_deleted = MagicMock(return_value=mock_qs)
        
        viewset.get_queryset()
        
        mock_qs.prefetch_related.assert_called_once_with('entity', 'data_sources')

    def test_calls_filter_deleted(self, mocker):
        """Calls filter_deleted mixin method."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.prefetch_related.return_value = mock_qs
        
        mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.Application.objects',
            mock_qs
        )
        
        viewset = ApplicationViewSet()
        viewset.request = MagicMock()
        viewset.request.query_params = {}
        mock_filter_deleted = MagicMock(return_value=mock_qs)
        viewset.filter_deleted = mock_filter_deleted
        
        viewset.get_queryset()
        
        mock_filter_deleted.assert_called_once()


class TestApplicationViewSetGetSerializerClass:
    """Tests for ApplicationViewSet.get_serializer_class method."""

    def test_returns_list_serializer_for_list_action(self, mocker):
        """Returns ApplicationListSerializer for list action."""
        viewset = ApplicationViewSet()
        viewset.action = 'list'
        
        mock_list_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.ApplicationListSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_list_serializer

    def test_returns_create_update_serializer_for_create_action(self, mocker):
        """Returns ApplicationCreateUpdateSerializer for create action."""
        viewset = ApplicationViewSet()
        viewset.action = 'create'
        
        mock_create_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.ApplicationCreateUpdateSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_create_serializer

    def test_returns_create_update_serializer_for_update_action(self, mocker):
        """Returns ApplicationCreateUpdateSerializer for update action."""
        viewset = ApplicationViewSet()
        viewset.action = 'update'
        
        mock_create_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.ApplicationCreateUpdateSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_create_serializer

    def test_returns_create_update_serializer_for_partial_update_action(self, mocker):
        """Returns ApplicationCreateUpdateSerializer for partial_update action."""
        viewset = ApplicationViewSet()
        viewset.action = 'partial_update'
        
        mock_create_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.ApplicationCreateUpdateSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_create_serializer

    def test_returns_detail_serializer_for_retrieve_action(self, mocker):
        """Returns ApplicationDetailSerializer for retrieve action."""
        viewset = ApplicationViewSet()
        viewset.action = 'retrieve'
        
        mock_detail_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.ApplicationDetailSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_detail_serializer

    def test_returns_detail_serializer_for_destroy_action(self, mocker):
        """Returns ApplicationDetailSerializer for destroy action."""
        viewset = ApplicationViewSet()
        viewset.action = 'destroy'
        
        mock_detail_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.ApplicationDetailSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_detail_serializer


class TestApplicationViewSetScriptsAction:
    """Tests for ApplicationViewSet.scripts action."""

    def test_returns_200_on_success(
        self, mock_application_instance, api_factory, mock_user, mocker
    ):
        """Returns 200 status on success."""
        mock_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.SqlScriptListSerializer'
        )
        mock_serializer.return_value.data = []
        
        viewset = ApplicationViewSet()
        viewset.get_object = MagicMock(return_value=mock_application_instance)
        
        request = api_factory.get('/applications/1/scripts/')
        request.user = mock_user
        
        response = viewset.scripts(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK

    def test_returns_application_id_in_response(
        self, mock_application_instance, api_factory, mock_user, mocker
    ):
        """Returns application_id in response."""
        mock_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.SqlScriptListSerializer'
        )
        mock_serializer.return_value.data = []
        
        viewset = ApplicationViewSet()
        viewset.get_object = MagicMock(return_value=mock_application_instance)
        
        request = api_factory.get('/applications/1/scripts/')
        request.user = mock_user
        
        response = viewset.scripts(request, pk=1)
        
        assert response.data['application_id'] == 1

    def test_returns_application_name_in_response(
        self, mock_application_instance, api_factory, mock_user, mocker
    ):
        """Returns application_name in response."""
        mock_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.SqlScriptListSerializer'
        )
        mock_serializer.return_value.data = []
        
        viewset = ApplicationViewSet()
        viewset.get_object = MagicMock(return_value=mock_application_instance)
        
        request = api_factory.get('/applications/1/scripts/')
        request.user = mock_user
        
        response = viewset.scripts(request, pk=1)
        
        assert response.data['application_name'] == "Test Application"

    def test_filters_scripts_by_is_deleted_false(
        self, mock_application_instance, api_factory, mock_user, mocker
    ):
        """Filters scripts with is_deleted=False."""
        mock_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.SqlScriptListSerializer'
        )
        mock_serializer.return_value.data = []
        
        viewset = ApplicationViewSet()
        viewset.get_object = MagicMock(return_value=mock_application_instance)
        
        request = api_factory.get('/applications/1/scripts/')
        request.user = mock_user
        
        viewset.scripts(request, pk=1)
        
        mock_application_instance.sql_scripts.filter.assert_called_once_with(
            is_deleted=False, is_active=True
        )

    def test_returns_count_in_response(
        self, mock_application_instance, api_factory, mock_user, mocker
    ):
        """Returns count in response."""
        mock_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.SqlScriptListSerializer'
        )
        mock_serializer.return_value.data = []
        
        viewset = ApplicationViewSet()
        viewset.get_object = MagicMock(return_value=mock_application_instance)
        
        request = api_factory.get('/applications/1/scripts/')
        request.user = mock_user
        
        response = viewset.scripts(request, pk=1)
        
        assert response.data['count'] == 2

    def test_calls_get_object(
        self, mock_application_instance, api_factory, mock_user, mocker
    ):
        """Calls get_object to retrieve application."""
        mock_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.SqlScriptListSerializer'
        )
        mock_serializer.return_value.data = []
        
        viewset = ApplicationViewSet()
        mock_get_object = MagicMock(return_value=mock_application_instance)
        viewset.get_object = mock_get_object
        
        request = api_factory.get('/applications/1/scripts/')
        request.user = mock_user
        
        viewset.scripts(request, pk=1)
        
        mock_get_object.assert_called_once()


class TestApplicationViewSetRunnersAction:
    """Tests for ApplicationViewSet.runners action."""

    def test_returns_200_on_success(
        self, mock_application_instance, api_factory, mock_user, mocker
    ):
        """Returns 200 status on success."""
        mock_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.RunnerListSerializer'
        )
        mock_serializer.return_value.data = []
        
        viewset = ApplicationViewSet()
        viewset.get_object = MagicMock(return_value=mock_application_instance)
        
        request = api_factory.get('/applications/1/runners/')
        request.user = mock_user
        
        response = viewset.runners(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK

    def test_returns_application_id_in_response(
        self, mock_application_instance, api_factory, mock_user, mocker
    ):
        """Returns application_id in response."""
        mock_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.RunnerListSerializer'
        )
        mock_serializer.return_value.data = []
        
        viewset = ApplicationViewSet()
        viewset.get_object = MagicMock(return_value=mock_application_instance)
        
        request = api_factory.get('/applications/1/runners/')
        request.user = mock_user
        
        response = viewset.runners(request, pk=1)
        
        assert response.data['application_id'] == 1

    def test_returns_application_name_in_response(
        self, mock_application_instance, api_factory, mock_user, mocker
    ):
        """Returns application_name in response."""
        mock_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.RunnerListSerializer'
        )
        mock_serializer.return_value.data = []
        
        viewset = ApplicationViewSet()
        viewset.get_object = MagicMock(return_value=mock_application_instance)
        
        request = api_factory.get('/applications/1/runners/')
        request.user = mock_user
        
        response = viewset.runners(request, pk=1)
        
        assert response.data['application_name'] == "Test Application"

    def test_filters_runners_by_is_deleted_false(
        self, mock_application_instance, api_factory, mock_user, mocker
    ):
        """Filters runners with is_deleted=False."""
        mock_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.RunnerListSerializer'
        )
        mock_serializer.return_value.data = []
        
        viewset = ApplicationViewSet()
        viewset.get_object = MagicMock(return_value=mock_application_instance)
        
        request = api_factory.get('/applications/1/runners/')
        request.user = mock_user
        
        viewset.runners(request, pk=1)
        
        mock_application_instance.runners.filter.assert_called_once_with(
            is_deleted=False, is_active=True
        )

    def test_returns_count_in_response(
        self, mock_application_instance, api_factory, mock_user, mocker
    ):
        """Returns count in response."""
        mock_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.RunnerListSerializer'
        )
        mock_serializer.return_value.data = []
        
        viewset = ApplicationViewSet()
        viewset.get_object = MagicMock(return_value=mock_application_instance)
        
        request = api_factory.get('/applications/1/runners/')
        request.user = mock_user
        
        response = viewset.runners(request, pk=1)
        
        assert response.data['count'] == 3

    def test_calls_get_object(
        self, mock_application_instance, api_factory, mock_user, mocker
    ):
        """Calls get_object to retrieve application."""
        mock_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.RunnerListSerializer'
        )
        mock_serializer.return_value.data = []
        
        viewset = ApplicationViewSet()
        mock_get_object = MagicMock(return_value=mock_application_instance)
        viewset.get_object = mock_get_object
        
        request = api_factory.get('/applications/1/runners/')
        request.user = mock_user
        
        viewset.runners(request, pk=1)
        
        mock_get_object.assert_called_once()


class TestApplicationViewSetConfiguration:
    """Tests for ApplicationViewSet class configuration."""

    def test_inherits_from_soft_delete_mixin(self):
        """ApplicationViewSet inherits from SoftDeleteMixin."""
        from tdm_orchestrator.api.views.mixins import SoftDeleteMixin
        
        assert issubclass(ApplicationViewSet, SoftDeleteMixin)

    def test_inherits_from_include_deleted_mixin(self):
        """ApplicationViewSet inherits from IncludeDeletedMixin."""
        from tdm_orchestrator.api.views.mixins import IncludeDeletedMixin
        
        assert issubclass(ApplicationViewSet, IncludeDeletedMixin)

    def test_filterset_fields_configured(self):
        """Filterset fields are configured correctly."""
        expected_fields = ['is_active', 'type1']
        
        assert ApplicationViewSet.filterset_fields == expected_fields

    def test_search_fields_configured(self):
        """Search fields are configured correctly."""
        expected_fields = ['reference', 'name', 'description', 'ip_address']
        
        assert ApplicationViewSet.search_fields == expected_fields

    def test_ordering_fields_configured(self):
        """Ordering fields are configured correctly."""
        expected_fields = ['created_at', 'updated_at', 'name']
        
        assert ApplicationViewSet.ordering_fields == expected_fields

    def test_default_ordering_configured(self):
        """Default ordering is configured correctly."""
        assert ApplicationViewSet.ordering == ['-created_at']


# =====================
# Edge Cases
# =====================

class TestEdgeCases:
    """Edge case tests for infrastructure ViewSets."""

    def test_type_viewset_instantiation(self):
        """TypeViewSet can be instantiated."""
        viewset = TypeViewSet()
        
        assert viewset is not None

    def test_entity_viewset_instantiation(self):
        """EntityViewSet can be instantiated."""
        viewset = EntityViewSet()
        
        assert viewset is not None

    def test_datasource_viewset_instantiation(self):
        """DataSourceViewSet can be instantiated."""
        viewset = DataSourceViewSet()
        
        assert viewset is not None

    def test_application_viewset_instantiation(self):
        """ApplicationViewSet can be instantiated."""
        viewset = ApplicationViewSet()
        
        assert viewset is not None

    def test_type_viewset_handles_uppercase_include_deleted(self, mocker):
        """TypeViewSet handles uppercase TRUE for include_deleted."""
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        
        mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.Type.objects',
            mock_qs
        )
        
        viewset = TypeViewSet()
        viewset.request = MagicMock()
        viewset.request.query_params = {'include_deleted': 'TRUE'}
        
        result = viewset.get_queryset()
        
        # Should not filter by is_deleted when TRUE
        filter_calls = [call for call in mock_qs.filter.call_args_list 
                       if 'is_deleted' in str(call)]
        assert len(filter_calls) == 0

    def test_scripts_action_with_empty_scripts(
        self, api_factory, mock_user, mocker
    ):
        """Scripts action handles application with no scripts."""
        mock_app = MagicMock()
        mock_app.id = 1
        mock_app.name = "Empty App"
        mock_scripts = MagicMock()
        mock_scripts.filter.return_value = mock_scripts
        mock_scripts.count.return_value = 0
        mock_app.sql_scripts = mock_scripts
        
        mock_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.SqlScriptListSerializer'
        )
        mock_serializer.return_value.data = []
        
        viewset = ApplicationViewSet()
        viewset.get_object = MagicMock(return_value=mock_app)
        
        request = api_factory.get('/applications/1/scripts/')
        request.user = mock_user
        
        response = viewset.scripts(request, pk=1)
        
        assert response.data['count'] == 0
        assert response.data['scripts'] == []

    def test_runners_action_with_empty_runners(
        self, api_factory, mock_user, mocker
    ):
        """Runners action handles application with no runners."""
        mock_app = MagicMock()
        mock_app.id = 1
        mock_app.name = "Empty App"
        mock_runners = MagicMock()
        mock_runners.filter.return_value = mock_runners
        mock_runners.count.return_value = 0
        mock_app.runners = mock_runners
        
        mock_serializer = mocker.patch(
            'tdm_orchestrator.api.views.infrastructure.RunnerListSerializer'
        )
        mock_serializer.return_value.data = []
        
        viewset = ApplicationViewSet()
        viewset.get_object = MagicMock(return_value=mock_app)
        
        request = api_factory.get('/applications/1/runners/')
        request.user = mock_user
        
        response = viewset.runners(request, pk=1)
        
        assert response.data['count'] == 0
        assert response.data['runners'] == []

    def test_test_connection_with_unicode_error_message(
        self, mock_datasource_instance, api_factory, mock_user, mocker
    ):
        """test_connection handles unicode error messages."""
        mocker.patch(
            'tdm_orchestrator.services.sql.SqlExecutor',
            side_effect=Exception("接続エラー")
        )
        
        viewset = DataSourceViewSet()
        viewset.get_object = MagicMock(return_value=mock_datasource_instance)
        
        request = api_factory.post('/datasources/1/test_connection/')
        request.user = mock_user
        
        response = viewset.test_connection(request, pk=1)
        
        assert response.data['success'] is False
        assert response.data['message'] == "接続エラー"


# =====================
# Summary of Covered Cases
# =====================
# TypeViewSet:
# - get_queryset returns all types by default
# - get_queryset filters deleted when include_deleted=false
# - get_queryset includes deleted when include_deleted=true
# - get_queryset filters by type_list when provided
# - get_queryset does not filter by type_list when not provided
# - perform_destroy sets is_deleted to True
# - perform_destroy sets is_active to False
# - perform_destroy calls save
# - Configuration: serializer_class, filter_backends, filterset_fields, search_fields, ordering
#
# EntityViewSet:
# - get_queryset calls select_related with correct fields
# - get_queryset calls filter_deleted
# - get_serializer_class returns correct serializers for actions
# - Configuration: mixins inheritance, filterset_fields, search_fields, ordering
#
# DataSourceViewSet:
# - get_queryset calls select_related with correct fields
# - get_queryset calls filter_deleted
# - get_serializer_class returns correct serializers for actions
# - test_connection returns success response on successful connection
# - test_connection returns failure response on failed connection
# - test_connection returns datasource_id and datasource_name
# - test_connection handles exception gracefully
# - test_connection calls get_object and SqlExecutor
# - Configuration: mixins inheritance, filterset_fields, search_fields, ordering
#
# ApplicationViewSet:
# - get_queryset calls select_related and prefetch_related with correct fields
# - get_queryset calls filter_deleted
# - get_serializer_class returns correct serializers for actions
# - scripts action returns application info and filtered scripts
# - scripts action returns count
# - runners action returns application info and filtered runners
# - runners action returns count
# - Configuration: mixins inheritance, filterset_fields, search_fields, ordering
#
# Edge cases:
# - ViewSet instantiation
# - Uppercase include_deleted value
# - Empty scripts/runners
# - Unicode error messages