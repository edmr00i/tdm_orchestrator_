"""
Tests for RunnerViewSet - Orchestration API endpoints.

Covers:
- get_queryset: QuerySet construction with select_related/prefetch_related
- get_serializer_class: Serializer selection based on action
- execution_plan: GET action to retrieve runner execution plan
- export: GET action to export runner as ZIP file
- export_info: GET action to retrieve export metadata
- execute: POST action to execute runner
- validate: POST action to validate runner (dry run)
"""

import datetime
from io import BytesIO
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Mark all tests in this module to use Django database
pytestmark = pytest.mark.django_db

# Imports that require Django to be configured must be done after pytest-django sets up
from django.http import FileResponse
from rest_framework import status
from rest_framework.test import APIRequestFactory

from tdm_orchestrator.api.views.orchestration import RunnerViewSet
from tdm_orchestrator.services.exceptions import ExportError


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
def mock_application():
    """Create a mock application."""
    app = MagicMock()
    app.id = 1
    app.name = "Test Application"
    app.reference = "APP_001"
    return app


@pytest.fixture
def mock_runner(mock_application):
    """Create a mock runner instance."""
    runner = MagicMock()
    runner.id = 1
    runner.pk = 1
    runner.reference = "RUNNER_001"
    runner.name = "Test Runner"
    runner.description = "Test runner description"
    runner.application = mock_application
    runner.is_active = True
    runner.stop_on_error = True
    runner.get_execution_plan.return_value = {
        'pre_scripts': [],
        'post_scripts': [],
        'total_steps': 0,
    }
    return runner


@pytest.fixture
def mock_queryset(mock_runner):
    """Create a mock queryset."""
    qs = MagicMock()
    qs.select_related.return_value = qs
    qs.prefetch_related.return_value = qs
    qs.filter.return_value = qs
    qs.exclude.return_value = qs
    qs.get.return_value = mock_runner
    qs.first.return_value = mock_runner
    return qs


@pytest.fixture
def mock_execution_result():
    """Create a mock execution result."""
    result = MagicMock()
    result.to_dict.return_value = {
        'status': 'success',
        'steps_executed': 5,
        'errors': [],
        'duration': 1.5,
    }
    return result


@pytest.fixture
def mock_validation_result():
    """Create a mock validation result."""
    result = MagicMock()
    result.to_dict.return_value = {
        'status': 'valid',
        'warnings': [],
        'missing_variables': [],
    }
    return result


@pytest.fixture
def viewset():
    """Create a RunnerViewSet instance."""
    return RunnerViewSet()


# =====================
# get_queryset Tests
# =====================

class TestGetQueryset:
    """Tests for RunnerViewSet.get_queryset method."""

    def test_calls_select_related_with_application_and_created_by(
        self, viewset, mocker
    ):
        """Calls select_related with application and created_by."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.prefetch_related.return_value = mock_qs
        
        mocker.patch.object(
            viewset, 'filter_deleted', return_value=mock_qs
        )
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.Runner.objects',
            mock_qs
        )
        
        viewset.get_queryset()
        
        mock_qs.select_related.assert_called_once_with('application', 'created_by')

    def test_calls_prefetch_related_with_runnerstep_script(
        self, viewset, mocker
    ):
        """Calls prefetch_related with runnerstep_set__script."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.prefetch_related.return_value = mock_qs
        
        mocker.patch.object(
            viewset, 'filter_deleted', return_value=mock_qs
        )
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.Runner.objects',
            mock_qs
        )
        
        viewset.get_queryset()
        
        mock_qs.prefetch_related.assert_called_once_with('runnerstep_set__script')

    def test_calls_filter_deleted(self, viewset, mocker):
        """Calls filter_deleted mixin method."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.prefetch_related.return_value = mock_qs
        
        mock_filter_deleted = mocker.patch.object(
            viewset, 'filter_deleted', return_value=mock_qs
        )
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.Runner.objects',
            mock_qs
        )
        
        viewset.get_queryset()
        
        mock_filter_deleted.assert_called_once()

    def test_returns_filtered_queryset(self, viewset, mocker):
        """Returns the filtered queryset."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.prefetch_related.return_value = mock_qs
        filtered_qs = MagicMock()
        
        mocker.patch.object(
            viewset, 'filter_deleted', return_value=filtered_qs
        )
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.Runner.objects',
            mock_qs
        )
        
        result = viewset.get_queryset()
        
        assert result == filtered_qs


# =====================
# get_serializer_class Tests
# =====================

class TestGetSerializerClass:
    """Tests for RunnerViewSet.get_serializer_class method."""

    def test_returns_list_serializer_for_list_action(self, viewset, mocker):
        """Returns RunnerListSerializer for list action."""
        viewset.action = 'list'
        
        mock_list_serializer = mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerListSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_list_serializer

    def test_returns_create_update_serializer_for_create_action(
        self, viewset, mocker
    ):
        """Returns RunnerCreateUpdateSerializer for create action."""
        viewset.action = 'create'
        
        mock_create_serializer = mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerCreateUpdateSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_create_serializer

    def test_returns_create_update_serializer_for_update_action(
        self, viewset, mocker
    ):
        """Returns RunnerCreateUpdateSerializer for update action."""
        viewset.action = 'update'
        
        mock_create_serializer = mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerCreateUpdateSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_create_serializer

    def test_returns_create_update_serializer_for_partial_update_action(
        self, viewset, mocker
    ):
        """Returns RunnerCreateUpdateSerializer for partial_update action."""
        viewset.action = 'partial_update'
        
        mock_create_serializer = mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerCreateUpdateSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_create_serializer

    def test_returns_detail_serializer_for_retrieve_action(self, viewset, mocker):
        """Returns RunnerDetailSerializer for retrieve action."""
        viewset.action = 'retrieve'
        
        mock_detail_serializer = mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerDetailSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_detail_serializer

    def test_returns_detail_serializer_for_custom_action(self, viewset, mocker):
        """Returns RunnerDetailSerializer for custom actions."""
        viewset.action = 'execution_plan'
        
        mock_detail_serializer = mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerDetailSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_detail_serializer

    def test_returns_detail_serializer_for_destroy_action(self, viewset, mocker):
        """Returns RunnerDetailSerializer for destroy action."""
        viewset.action = 'destroy'
        
        mock_detail_serializer = mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerDetailSerializer'
        )
        
        result = viewset.get_serializer_class()
        
        assert result == mock_detail_serializer


# =====================
# execution_plan Tests
# =====================

class TestExecutionPlan:
    """Tests for RunnerViewSet.execution_plan action."""

    def test_returns_execution_plan_success(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Returns execution plan for valid runner."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/execution_plan/')
        request.user = mock_user
        
        response = viewset.execution_plan(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK

    def test_calls_get_object(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Calls get_object to retrieve runner."""
        mock_get_object = mocker.patch.object(
            viewset, 'get_object', return_value=mock_runner
        )
        
        request = api_factory.get('/runners/1/execution_plan/')
        request.user = mock_user
        
        viewset.execution_plan(request, pk=1)
        
        mock_get_object.assert_called_once()

    def test_calls_runner_get_execution_plan(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Calls runner.get_execution_plan method."""
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/execution_plan/')
        request.user = mock_user
        
        viewset.execution_plan(request, pk=1)
        
        mock_runner.get_execution_plan.assert_called_once()

    def test_returns_execution_plan_data(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Returns execution plan data in response."""
        expected_plan = {
            'pre_scripts': [{'order': 1, 'name': 'script1'}],
            'post_scripts': [{'order': 1, 'name': 'script2'}],
            'total_steps': 2,
        }
        mock_runner.get_execution_plan.return_value = expected_plan
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/execution_plan/')
        request.user = mock_user
        
        response = viewset.execution_plan(request, pk=1)
        
        assert response.data == expected_plan


# =====================
# export Tests
# =====================

class TestExport:
    """Tests for RunnerViewSet.export action."""

    def test_returns_file_response_on_success(
        self, viewset, mock_runner, api_factory, mock_user, mocker, tmp_path
    ):
        """Returns FileResponse on successful export."""
        # Create a temporary zip file
        zip_file = tmp_path / "test.zip"
        zip_file.write_bytes(b"PK\x03\x04")  # ZIP file signature
        
        mock_exporter = MagicMock()
        mock_exporter.export.return_value = str(zip_file)
        
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerExporter',
            return_value=mock_exporter
        )
        
        request = api_factory.get('/runners/1/export/')
        request.user = mock_user
        
        response = viewset.export(request, pk=1)
        
        assert isinstance(response, FileResponse)

    def test_calls_runner_exporter(
        self, viewset, mock_runner, api_factory, mock_user, mocker, tmp_path
    ):
        """Calls RunnerExporter with runner."""
        zip_file = tmp_path / "test.zip"
        zip_file.write_bytes(b"PK\x03\x04")
        
        mock_exporter = MagicMock()
        mock_exporter.export.return_value = str(zip_file)
        
        mock_exporter_class = mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerExporter',
            return_value=mock_exporter
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/export/')
        request.user = mock_user
        
        viewset.export(request, pk=1)
        
        mock_exporter_class.assert_called_once_with(mock_runner)

    def test_calls_exporter_export_method(
        self, viewset, mock_runner, api_factory, mock_user, mocker, tmp_path
    ):
        """Calls exporter.export method."""
        zip_file = tmp_path / "test.zip"
        zip_file.write_bytes(b"PK\x03\x04")
        
        mock_exporter = MagicMock()
        mock_exporter.export.return_value = str(zip_file)
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerExporter',
            return_value=mock_exporter
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/export/')
        request.user = mock_user
        
        viewset.export(request, pk=1)
        
        mock_exporter.export.assert_called_once()

    def test_sets_content_type_to_application_zip(
        self, viewset, mock_runner, api_factory, mock_user, mocker, tmp_path
    ):
        """Sets content type to application/zip."""
        zip_file = tmp_path / "test.zip"
        zip_file.write_bytes(b"PK\x03\x04")
        
        mock_exporter = MagicMock()
        mock_exporter.export.return_value = str(zip_file)
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerExporter',
            return_value=mock_exporter
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/export/')
        request.user = mock_user
        
        response = viewset.export(request, pk=1)
        
        assert response['Content-Type'] == 'application/zip'

    def test_sets_content_disposition_header(
        self, viewset, mock_runner, api_factory, mock_user, mocker, tmp_path
    ):
        """Sets Content-Disposition header with filename."""
        zip_file = tmp_path / "test.zip"
        zip_file.write_bytes(b"PK\x03\x04")
        
        mock_exporter = MagicMock()
        mock_exporter.export.return_value = str(zip_file)
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerExporter',
            return_value=mock_exporter
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.datetime.datetime'
        ).now.return_value.strftime.return_value = '20240115_103000'
        
        request = api_factory.get('/runners/1/export/')
        request.user = mock_user
        
        response = viewset.export(request, pk=1)
        
        assert 'Content-Disposition' in response
        assert 'attachment' in response['Content-Disposition']
        assert 'runner_RUNNER_001' in response['Content-Disposition']

    def test_returns_500_on_export_error(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Returns 500 status on ExportError."""
        mock_exporter = MagicMock()
        mock_exporter.export.side_effect = ExportError("Export failed")
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerExporter',
            return_value=mock_exporter
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/export/')
        request.user = mock_user
        
        response = viewset.export(request, pk=1)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_returns_error_detail_on_export_error(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Returns error detail in response on ExportError."""
        mock_exporter = MagicMock()
        mock_exporter.export.side_effect = ExportError("Disk full")
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerExporter',
            return_value=mock_exporter
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/export/')
        request.user = mock_user
        
        response = viewset.export(request, pk=1)
        
        assert response.data['detail'] == "Disk full"

    def test_filename_includes_timestamp(
        self, viewset, mock_runner, api_factory, mock_user, mocker, tmp_path
    ):
        """Filename includes timestamp in expected format."""
        zip_file = tmp_path / "test.zip"
        zip_file.write_bytes(b"PK\x03\x04")
        
        mock_exporter = MagicMock()
        mock_exporter.export.return_value = str(zip_file)
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerExporter',
            return_value=mock_exporter
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/export/')
        request.user = mock_user
        
        response = viewset.export(request, pk=1)
        
        # Check that Content-Disposition contains .zip extension
        assert '.zip' in response['Content-Disposition']


# =====================
# export_info Tests
# =====================

class TestExportInfo:
    """Tests for RunnerViewSet.export_info action."""

    def test_returns_200_on_success(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Returns 200 status on success."""
        mock_exporter = MagicMock()
        mock_exporter.get_export_info.return_value = {
            'runner_name': 'Test Runner',
            'scripts_count': 5,
        }
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerExporter',
            return_value=mock_exporter
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/export_info/')
        request.user = mock_user
        
        response = viewset.export_info(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK

    def test_calls_runner_exporter(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Calls RunnerExporter with runner."""
        mock_exporter = MagicMock()
        mock_exporter.get_export_info.return_value = {}
        
        mock_exporter_class = mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerExporter',
            return_value=mock_exporter
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/export_info/')
        request.user = mock_user
        
        viewset.export_info(request, pk=1)
        
        mock_exporter_class.assert_called_once_with(mock_runner)

    def test_calls_get_export_info_method(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Calls exporter.get_export_info method."""
        mock_exporter = MagicMock()
        mock_exporter.get_export_info.return_value = {}
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerExporter',
            return_value=mock_exporter
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/export_info/')
        request.user = mock_user
        
        viewset.export_info(request, pk=1)
        
        mock_exporter.get_export_info.assert_called_once()

    def test_returns_export_info_data(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Returns export info data in response."""
        expected_info = {
            'runner_name': 'Test Runner',
            'runner_reference': 'RUNNER_001',
            'pre_scripts_count': 3,
            'post_scripts_count': 2,
            'required_variables': ['VAR1', 'VAR2'],
        }
        
        mock_exporter = MagicMock()
        mock_exporter.get_export_info.return_value = expected_info
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerExporter',
            return_value=mock_exporter
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/export_info/')
        request.user = mock_user
        
        response = viewset.export_info(request, pk=1)
        
        assert response.data == expected_info

    def test_returns_400_on_exception(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Returns 400 status on exception."""
        mock_exporter = MagicMock()
        mock_exporter.get_export_info.side_effect = ValueError("Invalid runner")
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerExporter',
            return_value=mock_exporter
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/export_info/')
        request.user = mock_user
        
        response = viewset.export_info(request, pk=1)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_error_detail_on_exception(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Returns error detail in response on exception."""
        mock_exporter = MagicMock()
        mock_exporter.get_export_info.side_effect = ValueError("Config error")
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerExporter',
            return_value=mock_exporter
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/export_info/')
        request.user = mock_user
        
        response = viewset.export_info(request, pk=1)
        
        assert response.data['detail'] == "Config error"


# =====================
# execute Tests
# =====================

class TestExecute:
    """Tests for RunnerViewSet.execute action."""

    def test_returns_200_on_success(
        self, viewset, mock_runner, mock_execution_result, api_factory, 
        mock_user, mocker
    ):
        """Returns 200 status on successful execution."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = mock_execution_result
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.post(
            '/runners/1/execute/',
            {'variables': {'VAR1': 'value1'}},
            format='json'
        )
        request.user = mock_user
        request.data = {'variables': {'VAR1': 'value1'}}
        
        response = viewset.execute(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK

    def test_calls_runner_orchestrator_with_runner_and_user(
        self, viewset, mock_runner, mock_execution_result, api_factory, 
        mock_user, mocker
    ):
        """Calls RunnerOrchestrator with runner and user."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = mock_execution_result
        
        mock_orchestrator_class = mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.post('/runners/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        viewset.execute(request, pk=1)
        
        mock_orchestrator_class.assert_called_once_with(
            mock_runner, user=mock_user
        )

    def test_calls_orchestrator_execute_with_variables(
        self, viewset, mock_runner, mock_execution_result, api_factory, 
        mock_user, mocker
    ):
        """Calls orchestrator.execute with variables from request."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = mock_execution_result
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        variables = {'VAR1': 'value1', 'VAR2': 'value2'}
        request = api_factory.post(
            '/runners/1/execute/',
            {'variables': variables},
            format='json'
        )
        request.user = mock_user
        request.data = {'variables': variables}
        
        viewset.execute(request, pk=1)
        
        mock_orchestrator.execute.assert_called_once_with(variables)

    def test_uses_empty_dict_when_no_variables(
        self, viewset, mock_runner, mock_execution_result, api_factory, 
        mock_user, mocker
    ):
        """Uses empty dict when no variables in request."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = mock_execution_result
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.post('/runners/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        viewset.execute(request, pk=1)
        
        mock_orchestrator.execute.assert_called_once_with({})

    def test_returns_result_to_dict(
        self, viewset, mock_runner, mock_execution_result, api_factory, 
        mock_user, mocker
    ):
        """Returns result.to_dict() in response."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = mock_execution_result
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.post('/runners/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.execute(request, pk=1)
        
        mock_execution_result.to_dict.assert_called_once()
        assert response.data == mock_execution_result.to_dict()

    def test_returns_500_on_exception(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Returns 500 status on exception."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.side_effect = RuntimeError("Execution failed")
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.post('/runners/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.execute(request, pk=1)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_returns_error_detail_on_exception(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Returns error detail in response on exception."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.side_effect = RuntimeError("Database error")
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.post('/runners/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.execute(request, pk=1)
        
        assert response.data['detail'] == "Database error"


# =====================
# validate Tests
# =====================

class TestValidate:
    """Tests for RunnerViewSet.validate action."""

    def test_returns_200_on_success(
        self, viewset, mock_runner, mock_validation_result, api_factory, 
        mock_user, mocker
    ):
        """Returns 200 status on successful validation."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_dry_run.return_value = mock_validation_result
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.post(
            '/runners/1/validate/',
            {'variables': {'VAR1': 'value1'}},
            format='json'
        )
        request.user = mock_user
        request.data = {'variables': {'VAR1': 'value1'}}
        
        response = viewset.validate(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK

    def test_calls_runner_orchestrator_without_user(
        self, viewset, mock_runner, mock_validation_result, api_factory, 
        mock_user, mocker
    ):
        """Calls RunnerOrchestrator with runner only (no user)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_dry_run.return_value = mock_validation_result
        
        mock_orchestrator_class = mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.post('/runners/1/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        viewset.validate(request, pk=1)
        
        mock_orchestrator_class.assert_called_once_with(mock_runner)

    def test_calls_execute_dry_run_with_variables(
        self, viewset, mock_runner, mock_validation_result, api_factory, 
        mock_user, mocker
    ):
        """Calls orchestrator.execute_dry_run with variables."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_dry_run.return_value = mock_validation_result
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        variables = {'VAR1': 'test', 'VAR2': 'value'}
        request = api_factory.post(
            '/runners/1/validate/',
            {'variables': variables},
            format='json'
        )
        request.user = mock_user
        request.data = {'variables': variables}
        
        viewset.validate(request, pk=1)
        
        mock_orchestrator.execute_dry_run.assert_called_once_with(variables)

    def test_uses_empty_dict_when_no_variables(
        self, viewset, mock_runner, mock_validation_result, api_factory, 
        mock_user, mocker
    ):
        """Uses empty dict when no variables in request."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_dry_run.return_value = mock_validation_result
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.post('/runners/1/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        viewset.validate(request, pk=1)
        
        mock_orchestrator.execute_dry_run.assert_called_once_with({})

    def test_returns_result_to_dict(
        self, viewset, mock_runner, mock_validation_result, api_factory, 
        mock_user, mocker
    ):
        """Returns result.to_dict() in response."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_dry_run.return_value = mock_validation_result
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.post('/runners/1/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.validate(request, pk=1)
        
        mock_validation_result.to_dict.assert_called_once()
        assert response.data == mock_validation_result.to_dict()

    def test_returns_400_on_exception(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Returns 400 status on exception."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_dry_run.side_effect = ValueError("Validation error")
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.post('/runners/1/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.validate(request, pk=1)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_error_detail_on_exception(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Returns error detail in response on exception."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_dry_run.side_effect = ValueError("Missing variables")
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.post('/runners/1/validate/', {}, format='json')
        request.user = mock_user
        request.data = {}
        
        response = viewset.validate(request, pk=1)
        
        assert response.data['detail'] == "Missing variables"


# =====================
# ViewSet Configuration Tests
# =====================

class TestViewSetConfiguration:
    """Tests for RunnerViewSet class attributes."""

    def test_filter_backends_configured(self):
        """Filter backends are configured correctly."""
        from django_filters.rest_framework import DjangoFilterBackend
        from rest_framework import filters
        
        assert DjangoFilterBackend in RunnerViewSet.filter_backends
        assert filters.SearchFilter in RunnerViewSet.filter_backends
        assert filters.OrderingFilter in RunnerViewSet.filter_backends

    def test_filterset_fields_configured(self):
        """Filterset fields are configured correctly."""
        expected_fields = ['application', 'is_active', 'stop_on_error']
        
        assert RunnerViewSet.filterset_fields == expected_fields

    def test_search_fields_configured(self):
        """Search fields are configured correctly."""
        expected_fields = ['reference', 'name', 'description']
        
        assert RunnerViewSet.search_fields == expected_fields

    def test_ordering_fields_configured(self):
        """Ordering fields are configured correctly."""
        expected_fields = ['created_at', 'updated_at', 'name']
        
        assert RunnerViewSet.ordering_fields == expected_fields

    def test_default_ordering_configured(self):
        """Default ordering is configured correctly."""
        assert RunnerViewSet.ordering == ['-created_at']


# =====================
# Edge Cases
# =====================

class TestEdgeCases:
    """Edge case tests for RunnerViewSet."""

    def test_execute_with_empty_variables_object(
        self, viewset, mock_runner, mock_execution_result, api_factory, 
        mock_user, mocker
    ):
        """Handles execution with empty variables object."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = mock_execution_result
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.post('/runners/1/execute/', {}, format='json')
        request.user = mock_user
        request.data = {'variables': {}}
        
        response = viewset.execute(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK
        mock_orchestrator.execute.assert_called_once_with({})

    def test_validate_with_complex_variables(
        self, viewset, mock_runner, mock_validation_result, api_factory, 
        mock_user, mocker
    ):
        """Handles validation with complex variable values."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_dry_run.return_value = mock_validation_result
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerOrchestrator',
            return_value=mock_orchestrator
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        complex_variables = {
            'STRING_VAR': 'test value',
            'INT_VAR': 123,
            'BOOL_VAR': True,
            'LIST_VAR': [1, 2, 3],
            'UNICODE_VAR': '日本語テスト',
        }
        request = api_factory.post(
            '/runners/1/validate/',
            {'variables': complex_variables},
            format='json'
        )
        request.user = mock_user
        request.data = {'variables': complex_variables}
        
        response = viewset.validate(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK
        mock_orchestrator.execute_dry_run.assert_called_once_with(complex_variables)

    def test_export_with_special_characters_in_reference(
        self, viewset, mock_runner, api_factory, mock_user, mocker, tmp_path
    ):
        """Handles export with special characters in runner reference."""
        mock_runner.reference = "RUNNER/REF\\001"
        
        zip_file = tmp_path / "test.zip"
        zip_file.write_bytes(b"PK\x03\x04")
        
        mock_exporter = MagicMock()
        mock_exporter.export.return_value = str(zip_file)
        
        mocker.patch(
            'tdm_orchestrator.api.views.orchestration.RunnerExporter',
            return_value=mock_exporter
        )
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/export/')
        request.user = mock_user
        
        response = viewset.export(request, pk=1)
        
        # Should still return a valid response
        assert isinstance(response, FileResponse)

    def test_execution_plan_with_empty_plan(
        self, viewset, mock_runner, api_factory, mock_user, mocker
    ):
        """Handles execution plan with no scripts."""
        mock_runner.get_execution_plan.return_value = {
            'pre_scripts': [],
            'post_scripts': [],
            'total_steps': 0,
        }
        mocker.patch.object(viewset, 'get_object', return_value=mock_runner)
        
        request = api_factory.get('/runners/1/execution_plan/')
        request.user = mock_user
        
        response = viewset.execution_plan(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_steps'] == 0


# =====================
# Summary of Covered Cases
# =====================
# get_queryset:
# - Calls select_related with application and created_by
# - Calls prefetch_related with runnerstep_set__script
# - Calls filter_deleted mixin method
# - Returns filtered queryset
#
# get_serializer_class:
# - Returns RunnerListSerializer for list action
# - Returns RunnerCreateUpdateSerializer for create action
# - Returns RunnerCreateUpdateSerializer for update action
# - Returns RunnerCreateUpdateSerializer for partial_update action
# - Returns RunnerDetailSerializer for retrieve action
# - Returns RunnerDetailSerializer for custom actions
# - Returns RunnerDetailSerializer for destroy action
#
# execution_plan:
# - Returns 200 on success
# - Calls get_object
# - Calls runner.get_execution_plan
# - Returns execution plan data
#
# export:
# - Returns FileResponse on success
# - Calls RunnerExporter with runner
# - Calls exporter.export method
# - Sets content type to application/zip
# - Sets Content-Disposition header
# - Returns 500 on ExportError
# - Returns error detail on ExportError
# - Filename includes timestamp
#
# export_info:
# - Returns 200 on success
# - Calls RunnerExporter with runner
# - Calls get_export_info method
# - Returns export info data
# - Returns 400 on exception
# - Returns error detail on exception
#
# execute:
# - Returns 200 on success
# - Calls RunnerOrchestrator with runner and user
# - Calls execute with variables
# - Uses empty dict when no variables
# - Returns result.to_dict()
# - Returns 500 on exception
# - Returns error detail on exception
#
# validate:
# - Returns 200 on success
# - Calls RunnerOrchestrator without user
# - Calls execute_dry_run with variables
# - Uses empty dict when no variables
# - Returns result.to_dict()
# - Returns 400 on exception
# - Returns error detail on exception
#
# ViewSet Configuration:
# - Filter backends configured
# - Filterset fields configured
# - Search fields configured
# - Ordering fields configured
# - Default ordering configured
#
# Edge cases:
# - Empty variables object
# - Complex variable values
# - Special characters in reference
# - Empty execution plan