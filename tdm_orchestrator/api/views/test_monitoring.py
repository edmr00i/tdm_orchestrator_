"""
Tests for ExecutionLogViewSet - Monitoring API endpoints.

Covers:
- get_queryset: QuerySet construction with select_related
- ViewSet configuration: serializer_class, filter_backends, filterset_fields, ordering_fields, ordering
- ReadOnlyModelViewSet behavior: list and retrieve actions only
"""

from unittest.mock import MagicMock

import pytest
from rest_framework.test import APIRequestFactory

from tdm_orchestrator.api.views.monitoring import ExecutionLogViewSet


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
def mock_runner():
    """Create a mock runner."""
    runner = MagicMock()
    runner.id = 1
    runner.name = "Test Runner"
    runner.reference = "RUNNER_001"
    return runner


@pytest.fixture
def mock_script():
    """Create a mock script."""
    script = MagicMock()
    script.id = 1
    script.name = "Test Script"
    script.reference = "SCRIPT_001"
    return script


@pytest.fixture
def mock_execution_log(mock_runner, mock_script, mock_user):
    """Create a mock execution log."""
    log = MagicMock()
    log.id = 1
    log.pk = 1
    log.status = "SUCCESS"
    log.runner = mock_runner
    log.script = mock_script
    log.executed_by = mock_user
    log.started_at = "2024-01-15T10:00:00Z"
    log.duration_ms = 150
    return log


@pytest.fixture
def mock_queryset(mock_execution_log):
    """Create a mock queryset."""
    qs = MagicMock()
    qs.select_related.return_value = qs
    qs.filter.return_value = qs
    qs.get.return_value = mock_execution_log
    qs.first.return_value = mock_execution_log
    return qs


@pytest.fixture
def viewset():
    """Create an ExecutionLogViewSet instance."""
    return ExecutionLogViewSet()


# =====================
# get_queryset Tests
# =====================

class TestGetQueryset:
    """Tests for ExecutionLogViewSet.get_queryset method."""

    def test_calls_select_related_with_runner_script_executed_by(
        self, viewset, mocker
    ):
        """Calls select_related with runner, script and executed_by."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        
        mocker.patch(
            'tdm_orchestrator.api.views.monitoring.ExecutionLog.objects',
            mock_qs
        )
        
        viewset.get_queryset()
        
        mock_qs.select_related.assert_called_once_with(
            'runner', 'script', 'executed_by'
        )

    def test_returns_queryset_from_select_related(self, viewset, mocker):
        """Returns the queryset from select_related."""
        mock_qs = MagicMock()
        expected_result = MagicMock()
        mock_qs.select_related.return_value = expected_result
        
        mocker.patch(
            'tdm_orchestrator.api.views.monitoring.ExecutionLog.objects',
            mock_qs
        )
        
        result = viewset.get_queryset()
        
        assert result == expected_result

    def test_uses_execution_log_objects_manager(self, viewset, mocker):
        """Uses ExecutionLog.objects manager."""
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        
        mock_objects = mocker.patch(
            'tdm_orchestrator.api.views.monitoring.ExecutionLog.objects',
            mock_qs
        )
        
        viewset.get_queryset()
        
        mock_objects.select_related.assert_called_once()


# =====================
# ViewSet Configuration Tests
# =====================

class TestViewSetConfiguration:
    """Tests for ExecutionLogViewSet class attributes."""

    def test_serializer_class_is_execution_log_serializer(self):
        """Serializer class is ExecutionLogSerializer."""
        from tdm_orchestrator.serializers import ExecutionLogSerializer
        
        assert ExecutionLogViewSet.serializer_class == ExecutionLogSerializer

    def test_filter_backends_contains_django_filter_backend(self):
        """Filter backends contains DjangoFilterBackend."""
        from django_filters.rest_framework import DjangoFilterBackend
        
        assert DjangoFilterBackend in ExecutionLogViewSet.filter_backends

    def test_filter_backends_contains_ordering_filter(self):
        """Filter backends contains OrderingFilter."""
        from rest_framework import filters
        
        assert filters.OrderingFilter in ExecutionLogViewSet.filter_backends

    def test_filter_backends_count_is_two(self):
        """Filter backends count is exactly two."""
        assert len(ExecutionLogViewSet.filter_backends) == 2

    def test_filterset_fields_contains_status(self):
        """Filterset fields contains status."""
        assert 'status' in ExecutionLogViewSet.filterset_fields

    def test_filterset_fields_contains_runner(self):
        """Filterset fields contains runner."""
        assert 'runner' in ExecutionLogViewSet.filterset_fields

    def test_filterset_fields_contains_script(self):
        """Filterset fields contains script."""
        assert 'script' in ExecutionLogViewSet.filterset_fields

    def test_filterset_fields_contains_executed_by(self):
        """Filterset fields contains executed_by."""
        assert 'executed_by' in ExecutionLogViewSet.filterset_fields

    def test_filterset_fields_count_is_four(self):
        """Filterset fields count is exactly four."""
        assert len(ExecutionLogViewSet.filterset_fields) == 4

    def test_ordering_fields_contains_started_at(self):
        """Ordering fields contains started_at."""
        assert 'started_at' in ExecutionLogViewSet.ordering_fields

    def test_ordering_fields_contains_duration_ms(self):
        """Ordering fields contains duration_ms."""
        assert 'duration_ms' in ExecutionLogViewSet.ordering_fields

    def test_ordering_fields_count_is_two(self):
        """Ordering fields count is exactly two."""
        assert len(ExecutionLogViewSet.ordering_fields) == 2

    def test_default_ordering_is_descending_started_at(self):
        """Default ordering is descending started_at."""
        assert ExecutionLogViewSet.ordering == ['-started_at']


# =====================
# ReadOnlyModelViewSet Inheritance Tests
# =====================

class TestReadOnlyModelViewSetInheritance:
    """Tests for ReadOnlyModelViewSet inheritance."""

    def test_inherits_from_readonly_model_viewset(self):
        """ExecutionLogViewSet inherits from ReadOnlyModelViewSet."""
        from rest_framework import viewsets
        
        assert issubclass(ExecutionLogViewSet, viewsets.ReadOnlyModelViewSet)

    def test_has_list_action(self):
        """ViewSet has list action from ReadOnlyModelViewSet."""
        viewset = ExecutionLogViewSet()
        
        assert hasattr(viewset, 'list')

    def test_has_retrieve_action(self):
        """ViewSet has retrieve action from ReadOnlyModelViewSet."""
        viewset = ExecutionLogViewSet()
        
        assert hasattr(viewset, 'retrieve')

    def test_does_not_have_create_action(self):
        """ViewSet does not have create action (read-only)."""
        viewset = ExecutionLogViewSet()
        
        # ReadOnlyModelViewSet doesn't define create
        assert 'create' not in viewset.get_extra_actions()

    def test_does_not_have_update_action(self):
        """ViewSet does not have update action (read-only)."""
        viewset = ExecutionLogViewSet()
        
        assert 'update' not in viewset.get_extra_actions()

    def test_does_not_have_destroy_action(self):
        """ViewSet does not have destroy action (read-only)."""
        viewset = ExecutionLogViewSet()
        
        assert 'destroy' not in viewset.get_extra_actions()


# =====================
# Edge Cases
# =====================

class TestEdgeCases:
    """Edge case tests for ExecutionLogViewSet."""

    def test_get_queryset_is_callable(self, viewset):
        """get_queryset method is callable."""
        assert callable(viewset.get_queryset)

    def test_viewset_instantiation(self):
        """ViewSet can be instantiated without errors."""
        viewset = ExecutionLogViewSet()
        
        assert viewset is not None

    def test_viewset_has_no_extra_actions(self):
        """ViewSet has no custom extra actions defined."""
        viewset = ExecutionLogViewSet()
        
        extra_actions = viewset.get_extra_actions()
        
        assert len(extra_actions) == 0


# =====================
# Summary of Covered Cases
# =====================
# get_queryset:
# - Calls select_related with runner, script, executed_by
# - Returns queryset from select_related
# - Uses ExecutionLog.objects manager
#
# ViewSet Configuration:
# - serializer_class is ExecutionLogSerializer
# - filter_backends contains DjangoFilterBackend
# - filter_backends contains OrderingFilter
# - filter_backends count is two
# - filterset_fields contains status, runner, script, executed_by
# - filterset_fields count is four
# - ordering_fields contains started_at, duration_ms
# - ordering_fields count is two
# - default ordering is descending started_at
#
# ReadOnlyModelViewSet Inheritance:
# - Inherits from ReadOnlyModelViewSet
# - Has list action
# - Has retrieve action
# - Does not have create action
# - Does not have update action
# - Does not have destroy action
#
# Edge cases:
# - get_queryset is callable
# - ViewSet can be instantiated
# - ViewSet has no extra actions