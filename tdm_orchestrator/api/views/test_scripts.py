"""
Tests for SqlScriptViewSet - SQL Scripts API endpoints.

Covers:
- get_queryset: QuerySet construction with select_related
- get_serializer_class: Serializer selection based on action
- variables: GET action to extract script variables
- validate: POST action to validate script (dry run)
- execute: POST action to execute script
- parse: POST action to parse script with variables
"""

import pytest
from unittest.mock import MagicMock, patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from tdm_orchestrator.api.views.scripts import SqlScriptViewSet


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
def mock_anonymous_user():
    """Create a mock anonymous user."""
    user = MagicMock()
    user.id = None
    user.is_authenticated = False
    return user


@pytest.fixture
def mock_application():
    """Create a mock application."""
    app = MagicMock()
    app.id = 1
    app.name = "Test Application"
    app.reference = "APP_001"
    return app


@pytest.fixture
def mock_datasource():
    """Create a mock datasource."""
    ds = MagicMock()
    ds.id = 1
    ds.name = "Test Datasource"
    ds.reference = "DS_001"
    return ds


@pytest.fixture
def mock_script(mock_application, mock_datasource):
    """Create a mock SQL script instance."""
    script = MagicMock()
    script.id = 1
    script.pk = 1
    script.reference = "SCRIPT_001"
    script.name = "Test Script"
    script.description = "Test script description"
    script.content = "SELECT * FROM table WHERE id = :id"
    script.script_type = "SQL"
    script.application = mock_application
    script.datasource = mock_datasource
    script.is_active = True
    script.extract_variables.return_value = ["id", "name"]
    script.get_parsed_content.return_value = "SELECT * FROM table WHERE id = 1"
    return script


@pytest.fixture
def mock_script_no_datasource(mock_application):
    """Create a mock SQL script without datasource."""
    script = MagicMock()
    script.id = 2
    script.pk = 2
    script.reference = "SCRIPT_002"
    script.name = "Script Without Datasource"
    script.description = None
    script.content = "SELECT 1"
    script.script_type = "SQL"
    script.application = mock_application
    script.datasource = None
    script.is_active = True
    script.extract_variables.return_value = []
    return script


@pytest.fixture
def mock_queryset(mock_script):
    """Create a mock queryset."""
    qs = MagicMock()
    qs.select_related.return_value = qs
    qs.filter.return_value = qs
    qs.exclude.return_value = qs
    qs.get.return_value = mock_script
    qs.first.return_value = mock_script
    return qs


@pytest.fixture
def mock_execution_result_success():
    """Create a mock successful execution result."""
    result = MagicMock()
    result.success = True
    result.duration_ms = 150
    result.rows_affected = 10
    result.logs = ["Query executed successfully"]
    result.error_message = None
    result.statements_executed = 1
    return result


@pytest.fixture
def mock_execution_result_failure():
    """Create a mock failed execution result."""
    result = MagicMock()
    result.success = False
    result.duration_ms = 50
    result.rows_affected = 0
    result.logs = ["Error during execution"]
    result.error_message = "Syntax error at line 1"
    result.statements_executed = 0
    return result


@pytest.fixture
def mock_execution_log():
    """Create a mock execution log."""
    log = MagicMock()
    log.id = 100
    log.status = "RUNNING"
    log.mark_success = MagicMock()
    log.mark_failure = MagicMock()
    return log


@pytest.fixture
def viewset():
    """Create a SqlScriptViewSet instance."""
    return SqlScriptViewSet()


# =====================
# get_queryset Tests
# =====================

class TestGetQueryset:
    """Tests for SqlScriptViewSet.get_queryset method."""

    def test_calls_select_related_with_application_datasource_created_by(
        self, viewset, mocker
    ):
        """Calls select_related with application, datasource and created_by."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        
        mocker.patch.object(
            viewset, 'filter_deleted', return_value=mock_qs
        )
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlScript.objects',
            mock_qs
        )
        
        viewset.get_queryset()
        
        mock_qs.select_related.assert_called_once_with(
            'application', 'datasource', 'created_by'
        )

    def test_calls_filter_deleted_mixin_method(self, viewset, mocker):
        """Calls filter_deleted mixin method."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        
        mock_filter_deleted = mocker.patch.object(
            viewset, 'filter_deleted', return_value=mock_qs
        )
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlScript.objects',
            mock_qs
        )
        
        viewset.get_queryset()
        
        mock_filter_deleted.assert_called_once()

    def test_returns_filtered_queryset(self, viewset, mocker):
        """Returns the filtered queryset."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        filtered_qs = MagicMock()
        
        mocker.patch.object(
            viewset, 'filter_deleted', return_value=filtered_qs
        )
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlScript.objects',
            mock_qs
        )
        
        result = viewset.get_queryset()
        
        assert result == filtered_qs


# =====================
# get_serializer_class Tests
# =====================

class TestGetSerializerClass:
    """Tests for SqlScriptViewSet.get_serializer_class method."""

    def test_returns_list_serializer_for_list_action(self, viewset, mocker):
        """Returns SqlScriptListSerializer for list action."""
        viewset.action = 'list'
        
        mock_list_serializer = mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlScriptListSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_list_serializer

    def test_returns_detail_serializer_for_retrieve_action(self, viewset, mocker):
        """Returns SqlScriptDetailSerializer for retrieve action."""
        viewset.action = 'retrieve'
        
        mock_detail_serializer = mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlScriptDetailSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_detail_serializer

    def test_returns_detail_serializer_for_create_action(self, viewset, mocker):
        """Returns SqlScriptDetailSerializer for create action."""
        viewset.action = 'create'
        
        mock_detail_serializer = mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlScriptDetailSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_detail_serializer

    def test_returns_detail_serializer_for_update_action(self, viewset, mocker):
        """Returns SqlScriptDetailSerializer for update action."""
        viewset.action = 'update'
        
        mock_detail_serializer = mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlScriptDetailSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_detail_serializer

    def test_returns_detail_serializer_for_partial_update_action(self, viewset, mocker):
        """Returns SqlScriptDetailSerializer for partial_update action."""
        viewset.action = 'partial_update'
        
        mock_detail_serializer = mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlScriptDetailSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_detail_serializer

    def test_returns_detail_serializer_for_destroy_action(self, viewset, mocker):
        """Returns SqlScriptDetailSerializer for destroy action."""
        viewset.action = 'destroy'
        
        mock_detail_serializer = mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlScriptDetailSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_detail_serializer

    def test_returns_detail_serializer_for_custom_action(self, viewset, mocker):
        """Returns SqlScriptDetailSerializer for custom actions."""
        viewset.action = 'variables'
        
        mock_detail_serializer = mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlScriptDetailSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_detail_serializer


# =====================
# variables Action Tests
# =====================

class TestVariablesAction:
    """Tests for SqlScriptViewSet.variables action."""

    def test_returns_200_on_success(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns 200 status on success."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.get('/scripts/1/variables/')
        request.user = mock_user
        
        response = viewset.variables(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK

    def test_calls_get_object(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Calls get_object to retrieve script."""
        mock_get_object = mocker.patch.object(
            viewset, 'get_object', return_value=mock_script
        )
        
        request = api_factory.get('/scripts/1/variables/')
        request.user = mock_user
        
        viewset.variables(request, pk=1)
        
        mock_get_object.assert_called_once()

    def test_calls_extract_variables_on_script(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Calls script.extract_variables() method."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.get('/scripts/1/variables/')
        request.user = mock_user
        
        viewset.variables(request, pk=1)
        
        mock_script.extract_variables.assert_called_once()

    def test_returns_script_id_in_response(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns script_id in response."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.get('/scripts/1/variables/')
        request.user = mock_user
        
        response = viewset.variables(request, pk=1)
        
        assert response.data['script_id'] == 1

    def test_returns_script_name_in_response(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns script_name in response."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.get('/scripts/1/variables/')
        request.user = mock_user
        
        response = viewset.variables(request, pk=1)
        
        assert response.data['script_name'] == 'Test Script'

    def test_returns_variables_list_in_response(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns variables list in response."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.get('/scripts/1/variables/')
        request.user = mock_user
        
        response = viewset.variables(request, pk=1)
        
        assert response.data['variables'] == ['id', 'name']

    def test_returns_correct_count_in_response(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns correct count in response."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.get('/scripts/1/variables/')
        request.user = mock_user
        
        response = viewset.variables(request, pk=1)
        
        assert response.data['count'] == 2

    def test_returns_empty_variables_for_script_without_variables(
        self, viewset, mock_script_no_datasource, api_factory, mock_user, mocker
    ):
        """Returns empty variables list for script without variables."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script_no_datasource)
        
        request = api_factory.get('/scripts/2/variables/')
        request.user = mock_user
        
        response = viewset.variables(request, pk=2)
        
        assert response.data['variables'] == []
        assert response.data['count'] == 0


# =====================
# validate Action Tests
# =====================

class TestValidateAction:
    """Tests for SqlScriptViewSet.validate action."""

    def test_returns_200_on_success(
        self, viewset, mock_script, mock_execution_result_success, 
        api_factory, mock_user, mocker
    ):
        """Returns 200 status on successful validation."""
        mock_executor = MagicMock()
        mock_executor.execute_dry_run.return_value = mock_execution_result_success
        
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        
        request = api_factory.post(
            '/scripts/1/validate/',
            {'variables': {'id': 1}},
            format='json'
        )
        request.user = mock_user
        request.data = {'variables': {'id': 1}}
        
        response = viewset.validate(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK

    def test_returns_400_when_no_datasource(
        self, viewset, mock_script_no_datasource, api_factory, mock_user, mocker
    ):
        """Returns 400 status when script has no datasource."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script_no_datasource)
        
        request = api_factory.post('/scripts/2/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.validate(request, pk=2)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_error_message_when_no_datasource(
        self, viewset, mock_script_no_datasource, api_factory, mock_user, mocker
    ):
        """Returns error message when script has no datasource."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script_no_datasource)
        
        request = api_factory.post('/scripts/2/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.validate(request, pk=2)
        
        assert response.data['detail'] == 'Aucune datasource configurée pour ce script.'

    def test_calls_sql_executor_with_datasource(
        self, viewset, mock_script, mock_execution_result_success, 
        api_factory, mock_user, mocker
    ):
        """Calls SqlExecutor with script datasource."""
        mock_executor = MagicMock()
        mock_executor.execute_dry_run.return_value = mock_execution_result_success
        
        mock_executor_class = mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        viewset.validate(request, pk=1)
        
        mock_executor_class.assert_called_once_with(mock_script.datasource)

    def test_calls_execute_dry_run_with_content_and_variables(
        self, viewset, mock_script, mock_execution_result_success, 
        api_factory, mock_user, mocker
    ):
        """Calls execute_dry_run with script content and variables."""
        mock_executor = MagicMock()
        mock_executor.execute_dry_run.return_value = mock_execution_result_success
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        variables = {'id': 1, 'name': 'test'}
        request = api_factory.post(
            '/scripts/1/validate/',
            {'variables': variables},
            format='json'
        )
        request.user = mock_user
        request.data = {'variables': variables}
        
        viewset.validate(request, pk=1)
        
        mock_executor.execute_dry_run.assert_called_once_with(
            mock_script.content, variables
        )

    def test_uses_empty_dict_when_no_variables_provided(
        self, viewset, mock_script, mock_execution_result_success, 
        api_factory, mock_user, mocker
    ):
        """Uses empty dict when no variables in request."""
        mock_executor = MagicMock()
        mock_executor.execute_dry_run.return_value = mock_execution_result_success
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        viewset.validate(request, pk=1)
        
        mock_executor.execute_dry_run.assert_called_once_with(
            mock_script.content, {}
        )

    def test_returns_success_in_response(
        self, viewset, mock_script, mock_execution_result_success, 
        api_factory, mock_user, mocker
    ):
        """Returns success field in response."""
        mock_executor = MagicMock()
        mock_executor.execute_dry_run.return_value = mock_execution_result_success
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.validate(request, pk=1)
        
        assert response.data['success'] is True

    def test_returns_duration_ms_in_response(
        self, viewset, mock_script, mock_execution_result_success, 
        api_factory, mock_user, mocker
    ):
        """Returns duration_ms field in response."""
        mock_executor = MagicMock()
        mock_executor.execute_dry_run.return_value = mock_execution_result_success
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.validate(request, pk=1)
        
        assert response.data['duration_ms'] == 150

    def test_returns_logs_in_response(
        self, viewset, mock_script, mock_execution_result_success, 
        api_factory, mock_user, mocker
    ):
        """Returns logs field in response."""
        mock_executor = MagicMock()
        mock_executor.execute_dry_run.return_value = mock_execution_result_success
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.validate(request, pk=1)
        
        assert response.data['logs'] == ["Query executed successfully"]

    def test_returns_error_message_in_response(
        self, viewset, mock_script, mock_execution_result_failure, 
        api_factory, mock_user, mocker
    ):
        """Returns error_message field in response."""
        mock_executor = MagicMock()
        mock_executor.execute_dry_run.return_value = mock_execution_result_failure
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.validate(request, pk=1)
        
        assert response.data['error_message'] == "Syntax error at line 1"

    def test_returns_statements_executed_in_response(
        self, viewset, mock_script, mock_execution_result_success, 
        api_factory, mock_user, mocker
    ):
        """Returns statements_executed field in response."""
        mock_executor = MagicMock()
        mock_executor.execute_dry_run.return_value = mock_execution_result_success
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.validate(request, pk=1)
        
        assert response.data['statements_executed'] == 1

    def test_returns_400_on_exception(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns 400 status on exception."""
        mock_executor = MagicMock()
        mock_executor.execute_dry_run.side_effect = Exception("Connection failed")
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.validate(request, pk=1)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_exception_message_on_error(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns exception message in response on error."""
        mock_executor = MagicMock()
        mock_executor.execute_dry_run.side_effect = Exception("Database timeout")
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.validate(request, pk=1)
        
        assert response.data['detail'] == "Database timeout"


# =====================
# execute Action Tests
# =====================

class TestExecuteAction:
    """Tests for SqlScriptViewSet.execute action."""

    def test_returns_200_on_success(
        self, viewset, mock_script, mock_execution_result_success, 
        mock_execution_log, api_factory, mock_user, mocker
    ):
        """Returns 200 status on successful execution."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_execution_result_success
        
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.execute(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK

    def test_returns_400_when_no_datasource(
        self, viewset, mock_script_no_datasource, api_factory, mock_user, mocker
    ):
        """Returns 400 status when script has no datasource."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script_no_datasource)
        
        request = api_factory.post('/scripts/2/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.execute(request, pk=2)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_error_message_when_no_datasource(
        self, viewset, mock_script_no_datasource, api_factory, mock_user, mocker
    ):
        """Returns error message when script has no datasource."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script_no_datasource)
        
        request = api_factory.post('/scripts/2/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.execute(request, pk=2)
        
        assert response.data['detail'] == 'Aucune datasource configurée pour ce script.'

    def test_creates_execution_log(
        self, viewset, mock_script, mock_execution_result_success, 
        mock_execution_log, api_factory, mock_user, mocker
    ):
        """Creates ExecutionLog entry."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_execution_result_success
        
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mock_log_create = mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {'variables': {'id': 1}}
        
        viewset.execute(request, pk=1)
        
        mock_log_create.assert_called_once_with(
            script=mock_script,
            status='RUNNING',
            executed_by=mock_user,
            variables_used={'id': 1}
        )

    def test_creates_execution_log_with_none_user_when_anonymous(
        self, viewset, mock_script, mock_execution_result_success, 
        mock_execution_log, api_factory, mock_anonymous_user, mocker
    ):
        """Creates ExecutionLog with None user for anonymous users."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_execution_result_success
        
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mock_log_create = mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_anonymous_user
        request.data = {}
        
        viewset.execute(request, pk=1)
        
        mock_log_create.assert_called_once_with(
            script=mock_script,
            status='RUNNING',
            executed_by=None,
            variables_used={}
        )

    def test_calls_sql_executor_with_datasource(
        self, viewset, mock_script, mock_execution_result_success, 
        mock_execution_log, api_factory, mock_user, mocker
    ):
        """Calls SqlExecutor with script datasource."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_execution_result_success
        
        mock_executor_class = mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        viewset.execute(request, pk=1)
        
        mock_executor_class.assert_called_once_with(mock_script.datasource)

    def test_calls_execute_with_content_and_variables(
        self, viewset, mock_script, mock_execution_result_success, 
        mock_execution_log, api_factory, mock_user, mocker
    ):
        """Calls execute with script content and variables."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_execution_result_success
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        variables = {'id': 1, 'name': 'test'}
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {'variables': variables}
        
        viewset.execute(request, pk=1)
        
        mock_executor.execute.assert_called_once_with(mock_script.content, variables)

    def test_marks_log_success_on_successful_execution(
        self, viewset, mock_script, mock_execution_result_success, 
        mock_execution_log, api_factory, mock_user, mocker
    ):
        """Calls mark_success on log when execution succeeds."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_execution_result_success
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        viewset.execute(request, pk=1)
        
        mock_execution_log.mark_success.assert_called_once_with(
            mock_execution_result_success.logs
        )

    def test_marks_log_failure_on_failed_execution(
        self, viewset, mock_script, mock_execution_result_failure, 
        mock_execution_log, api_factory, mock_user, mocker
    ):
        """Calls mark_failure on log when execution fails."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_execution_result_failure
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        viewset.execute(request, pk=1)
        
        mock_execution_log.mark_failure.assert_called_once_with(
            mock_execution_result_failure.error_message,
            mock_execution_result_failure.logs
        )

    def test_returns_execution_log_id_in_response(
        self, viewset, mock_script, mock_execution_result_success, 
        mock_execution_log, api_factory, mock_user, mocker
    ):
        """Returns execution_log_id in response."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_execution_result_success
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.execute(request, pk=1)
        
        assert response.data['execution_log_id'] == 100

    def test_returns_success_in_response(
        self, viewset, mock_script, mock_execution_result_success, 
        mock_execution_log, api_factory, mock_user, mocker
    ):
        """Returns success field in response."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_execution_result_success
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.execute(request, pk=1)
        
        assert response.data['success'] is True

    def test_returns_duration_ms_in_response(
        self, viewset, mock_script, mock_execution_result_success, 
        mock_execution_log, api_factory, mock_user, mocker
    ):
        """Returns duration_ms field in response."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_execution_result_success
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.execute(request, pk=1)
        
        assert response.data['duration_ms'] == 150

    def test_returns_rows_affected_in_response(
        self, viewset, mock_script, mock_execution_result_success, 
        mock_execution_log, api_factory, mock_user, mocker
    ):
        """Returns rows_affected field in response."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_execution_result_success
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.execute(request, pk=1)
        
        assert response.data['rows_affected'] == 10

    def test_returns_500_on_exception(
        self, viewset, mock_script, mock_execution_log, 
        api_factory, mock_user, mocker
    ):
        """Returns 500 status on exception."""
        mock_executor = MagicMock()
        mock_executor.execute.side_effect = Exception("Database connection lost")
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.execute(request, pk=1)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_marks_log_failure_on_exception(
        self, viewset, mock_script, mock_execution_log, 
        api_factory, mock_user, mocker
    ):
        """Calls mark_failure on log when exception occurs."""
        mock_executor = MagicMock()
        mock_executor.execute.side_effect = Exception("Unexpected error")
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        viewset.execute(request, pk=1)
        
        mock_execution_log.mark_failure.assert_called_once_with("Unexpected error")

    def test_does_not_mark_failure_when_log_not_created(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Does not call mark_failure when log was not created before exception."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            side_effect=Exception("Connection failed before log creation")
        )
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            side_effect=Exception("Cannot create log")
        )
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        # Should not raise, just return 500
        response = viewset.execute(request, pk=1)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_returns_exception_message_on_error(
        self, viewset, mock_script, mock_execution_log, 
        api_factory, mock_user, mocker
    ):
        """Returns exception message in response on error."""
        mock_executor = MagicMock()
        mock_executor.execute.side_effect = Exception("Query timeout")
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.execute(request, pk=1)
        
        assert response.data['detail'] == "Query timeout"


# =====================
# parse Action Tests
# =====================

class TestParseAction:
    """Tests for SqlScriptViewSet.parse action."""

    def test_returns_200_on_success(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns 200 status on success."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post(
            '/scripts/1/parse/',
            {'variables': {'id': 1}},
            format='json'
        )
        request.user = mock_user
        request.data = {'variables': {'id': 1}}
        
        response = viewset.parse(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK

    def test_returns_400_when_variables_not_dict(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns 400 status when variables is not a dict."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post(
            '/scripts/1/parse/',
            {'variables': 'not_a_dict'},
            format='json'
        )
        request.user = mock_user
        request.data = {'variables': 'not_a_dict'}
        
        response = viewset.parse(request, pk=1)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_error_message_when_variables_not_dict(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns error message when variables is not a dict."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post(
            '/scripts/1/parse/',
            {'variables': ['list', 'of', 'values']},
            format='json'
        )
        request.user = mock_user
        request.data = {'variables': ['list', 'of', 'values']}
        
        response = viewset.parse(request, pk=1)
        
        assert response.data['detail'] == 'Le champ variables doit être un objet.'

    def test_returns_400_when_variables_is_list(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns 400 status when variables is a list."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/parse/', {}, format='json')
        request.user = mock_user
        request.data = {'variables': [1, 2, 3]}
        
        response = viewset.parse(request, pk=1)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_400_when_variables_is_number(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns 400 status when variables is a number."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/parse/', {}, format='json')
        request.user = mock_user
        request.data = {'variables': 123}
        
        response = viewset.parse(request, pk=1)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_calls_get_parsed_content_with_variables(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Calls script.get_parsed_content with variables."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        variables = {'id': 1, 'name': 'test'}
        request = api_factory.post(
            '/scripts/1/parse/',
            {'variables': variables},
            format='json'
        )
        request.user = mock_user
        request.data = {'variables': variables}
        
        viewset.parse(request, pk=1)
        
        mock_script.get_parsed_content.assert_called_once_with(variables)

    def test_uses_empty_dict_when_no_variables_provided(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Uses empty dict when no variables in request."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/parse/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        viewset.parse(request, pk=1)
        
        mock_script.get_parsed_content.assert_called_once_with({})

    def test_returns_script_id_in_response(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns script_id in response."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/parse/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.parse(request, pk=1)
        
        assert response.data['script_id'] == 1

    def test_returns_script_name_in_response(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns script_name in response."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/parse/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.parse(request, pk=1)
        
        assert response.data['script_name'] == 'Test Script'

    def test_returns_original_content_in_response(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns original_content in response."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/parse/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.parse(request, pk=1)
        
        assert response.data['original_content'] == "SELECT * FROM table WHERE id = :id"

    def test_returns_parsed_content_in_response(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns parsed_content in response."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/parse/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.parse(request, pk=1)
        
        assert response.data['parsed_content'] == "SELECT * FROM table WHERE id = 1"

    def test_returns_variables_used_in_response(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns variables_used in response."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        variables = {'id': 1, 'name': 'test'}
        request = api_factory.post(
            '/scripts/1/parse/',
            {'variables': variables},
            format='json'
        )
        request.user = mock_user
        request.data = {'variables': variables}
        
        response = viewset.parse(request, pk=1)
        
        assert response.data['variables_used'] == variables

    def test_returns_400_on_exception(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns 400 status on exception."""
        mock_script.get_parsed_content.side_effect = Exception("Missing variable")
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/parse/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.parse(request, pk=1)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_formatted_error_message_on_exception(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Returns formatted error message in response on exception."""
        mock_script.get_parsed_content.side_effect = Exception("Variable 'xyz' not found")
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/parse/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.parse(request, pk=1)
        
        assert response.data['detail'] == "Erreur lors du parsing: Variable 'xyz' not found"


# =====================
# ViewSet Configuration Tests
# =====================

class TestViewSetConfiguration:
    """Tests for SqlScriptViewSet class attributes."""

    def test_filter_backends_configured(self):
        """Filter backends are configured correctly."""
        from django_filters.rest_framework import DjangoFilterBackend
        from rest_framework import filters
        
        assert DjangoFilterBackend in SqlScriptViewSet.filter_backends
        assert filters.SearchFilter in SqlScriptViewSet.filter_backends
        assert filters.OrderingFilter in SqlScriptViewSet.filter_backends

    def test_filterset_fields_configured(self):
        """Filterset fields are configured correctly."""
        expected_fields = ['script_type', 'application', 'datasource', 'is_active']
        
        assert SqlScriptViewSet.filterset_fields == expected_fields

    def test_search_fields_configured(self):
        """Search fields are configured correctly."""
        expected_fields = ['reference', 'name', 'description']
        
        assert SqlScriptViewSet.search_fields == expected_fields

    def test_ordering_fields_configured(self):
        """Ordering fields are configured correctly."""
        expected_fields = ['created_at', 'updated_at', 'name']
        
        assert SqlScriptViewSet.ordering_fields == expected_fields

    def test_default_ordering_configured(self):
        """Default ordering is configured correctly."""
        assert SqlScriptViewSet.ordering == ['-created_at']


# =====================
# Edge Cases
# =====================

class TestEdgeCases:
    """Edge case tests for SqlScriptViewSet."""

    def test_variables_with_many_variables(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Handles script with many variables."""
        mock_script.extract_variables.return_value = [
            f"var_{i}" for i in range(100)
        ]
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.get('/scripts/1/variables/')
        request.user = mock_user
        
        response = viewset.variables(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 100

    def test_parse_with_empty_dict_variables(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Handles parsing with empty variables dict."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/parse/', {}, format='json')
        request.user = mock_user
        request.data = {'variables': {}}
        
        response = viewset.parse(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['variables_used'] == {}

    def test_execute_with_complex_variables(
        self, viewset, mock_script, mock_execution_result_success, 
        mock_execution_log, api_factory, mock_user, mocker
    ):
        """Handles execution with complex variable values."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_execution_result_success
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        complex_variables = {
            'string_var': 'test value',
            'int_var': 123,
            'float_var': 3.14,
            'bool_var': True,
            'unicode_var': '日本語テスト',
            'special_chars': "O'Brien",
        }
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {'variables': complex_variables}
        
        response = viewset.execute(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK

    def test_validate_with_unicode_error_message(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Handles validation with unicode error message."""
        mock_executor = MagicMock()
        mock_executor.execute_dry_run.side_effect = Exception("エラー: 無効なクエリ")
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.validate(request, pk=1)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['detail'] == "エラー: 無効なクエリ"

    def test_parse_with_unicode_script_content(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Handles parsing script with unicode content."""
        mock_script.content = "SELECT * FROM 表 WHERE 名前 = :名前"
        mock_script.get_parsed_content.return_value = "SELECT * FROM 表 WHERE 名前 = '田中'"
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.post('/scripts/1/parse/', {}, format='json')
        request.user = mock_user
        request.data = {'variables': {'名前': '田中'}}
        
        response = viewset.parse(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK
        assert "田中" in response.data['parsed_content']

    def test_execute_logs_empty_variables(
        self, viewset, mock_script, mock_execution_result_success, 
        mock_execution_log, api_factory, mock_user, mocker
    ):
        """Execution log records empty variables correctly."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = mock_execution_result_success
        
        mocker.patch(
            'tdm_orchestrator.api.views.scripts.SqlExecutor',
            return_value=mock_executor
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        mock_log_create = mocker.patch(
            'tdm_orchestrator.api.views.scripts.ExecutionLog.objects.create',
            return_value=mock_execution_log
        )
        
        request = api_factory.post('/scripts/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        viewset.execute(request, pk=1)
        
        # Verify empty dict was passed as variables_used
        call_kwargs = mock_log_create.call_args[1]
        assert call_kwargs['variables_used'] == {}

    def test_variables_with_special_characters_in_name(
        self, viewset, mock_script, api_factory, mock_user, mocker
    ):
        """Handles script with special characters in variable names."""
        mock_script.extract_variables.return_value = [
            "var_with_underscore",
            "VAR_WITH_UPPERCASE",
            "var123",
            "_private_var",
        ]
        mocker.patch.object(viewset, 'get_object', return_value=mock_script)
        
        request = api_factory.get('/scripts/1/variables/')
        request.user = mock_user
        
        response = viewset.variables(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4


# =====================
# Mixin Inheritance Tests
# =====================

class TestMixinInheritance:
    """Tests for mixin inheritance."""

    def test_inherits_from_soft_delete_mixin(self):
        """SqlScriptViewSet inherits from SoftDeleteMixin."""
        from tdm_orchestrator.api.views.mixins import SoftDeleteMixin
        
        assert issubclass(SqlScriptViewSet, SoftDeleteMixin)

    def test_inherits_from_include_deleted_mixin(self):
        """SqlScriptViewSet inherits from IncludeDeletedMixin."""
        from tdm_orchestrator.api.views.mixins import IncludeDeletedMixin
        
        assert issubclass(SqlScriptViewSet, IncludeDeletedMixin)

    def test_inherits_from_model_viewset(self):
        """SqlScriptViewSet inherits from ModelViewSet."""
        from rest_framework import viewsets
        
        assert issubclass(SqlScriptViewSet, viewsets.ModelViewSet)


# =====================
# Summary of Covered Cases
# =====================
# get_queryset:
# - Calls select_related with application, datasource, created_by
# - Calls filter_deleted mixin method
# - Returns filtered queryset
#
# get_serializer_class:
# - Returns SqlScriptListSerializer for list action
# - Returns SqlScriptDetailSerializer for retrieve/create/update/partial_update/destroy/custom actions
#
# variables:
# - Returns 200 on success
# - Calls get_object
# - Calls extract_variables on script
# - Returns script_id, script_name, variables, count in response
# - Returns empty variables list for script without variables
#
# validate:
# - Returns 200 on success
# - Returns 400 when no datasource
# - Returns error message when no datasource
# - Calls SqlExecutor with datasource
# - Calls execute_dry_run with content and variables
# - Uses empty dict when no variables provided
# - Returns success, duration_ms, logs, error_message, statements_executed
# - Returns 400 on exception with error message
#
# execute:
# - Returns 200 on success
# - Returns 400 when no datasource
# - Creates ExecutionLog entry
# - Creates ExecutionLog with None user for anonymous users
# - Calls SqlExecutor with datasource
# - Calls execute with content and variables
# - Marks log success on successful execution
# - Marks log failure on failed execution
# - Returns execution_log_id, success, duration_ms, rows_affected, logs, error_message
# - Returns 500 on exception
# - Marks log failure on exception
# - Does not mark failure when log not created
# - Returns exception message on error
#
# parse:
# - Returns 200 on success
# - Returns 400 when variables not dict (string, list, number)
# - Returns error message when variables not dict
# - Calls get_parsed_content with variables
# - Uses empty dict when no variables provided
# - Returns script_id, script_name, original_content, parsed_content, variables_used
# - Returns 400 on exception with formatted error message
#
# ViewSet Configuration:
# - Filter backends configured
# - Filterset fields configured
# - Search fields configured
# - Ordering fields configured
# - Default ordering configured
#
# Edge cases:
# - Many variables
# - Empty dict variables
# - Complex variable values
# - Unicode error messages
# - Unicode script content
# - Empty variables in execution log
# - Special characters in variable names
#
# Mixin inheritance:
# - Inherits from SoftDeleteMixin
# - Inherits from IncludeDeletedMixin
# - Inherits from ModelViewSet