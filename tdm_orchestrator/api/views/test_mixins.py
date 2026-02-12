"""
Tests for ViewSet Mixins - SoftDeleteMixin and IncludeDeletedMixin.

Covers:
- SoftDeleteMixin.perform_destroy: Soft delete behavior
- SoftDeleteMixin.restore: Restore deleted objects
- IncludeDeletedMixin.filter_deleted: Filter deleted objects based on query param
"""

from unittest.mock import MagicMock

import pytest
from rest_framework import status

from tdm_orchestrator.api.views.mixins import SoftDeleteMixin, IncludeDeletedMixin


# =====================
# Fixtures
# =====================

@pytest.fixture
def mock_instance():
    """Create a mock model instance with soft delete fields."""
    instance = MagicMock()
    instance.is_deleted = False
    instance.is_active = True
    instance.save = MagicMock()
    return instance


@pytest.fixture
def mock_deleted_instance():
    """Create a mock deleted model instance."""
    instance = MagicMock()
    instance.is_deleted = True
    instance.is_active = False
    instance.save = MagicMock()
    return instance


@pytest.fixture
def mock_queryset():
    """Create a mock queryset."""
    qs = MagicMock()
    qs.filter.return_value = qs
    return qs


@pytest.fixture
def mock_request():
    """Create a mock request with query_params."""
    request = MagicMock()
    request.query_params = {}
    return request


@pytest.fixture
def mock_serializer():
    """Create a mock serializer."""
    serializer = MagicMock()
    serializer.data = {'id': 1, 'name': 'Test Object', 'is_deleted': False}
    return serializer


@pytest.fixture
def soft_delete_mixin(mock_instance, mock_serializer):
    """Create a SoftDeleteMixin instance with mocked methods."""
    mixin = SoftDeleteMixin()
    mixin.get_object = MagicMock(return_value=mock_instance)
    mixin.get_serializer = MagicMock(return_value=mock_serializer)
    return mixin


@pytest.fixture
def include_deleted_mixin(mock_request, mock_queryset):
    """Create an IncludeDeletedMixin instance with mocked request."""
    mixin = IncludeDeletedMixin()
    mixin.request = mock_request
    return mixin


# =====================
# SoftDeleteMixin.perform_destroy Tests
# =====================

class TestPerformDestroy:
    """Tests for SoftDeleteMixin.perform_destroy method."""

    def test_sets_is_deleted_to_true(self, mock_instance):
        """Sets is_deleted to True on instance."""
        mixin = SoftDeleteMixin()
        
        mixin.perform_destroy(mock_instance)
        
        assert mock_instance.is_deleted is True

    def test_sets_is_active_to_false(self, mock_instance):
        """Sets is_active to False on instance."""
        mixin = SoftDeleteMixin()
        
        mixin.perform_destroy(mock_instance)
        
        assert mock_instance.is_active is False

    def test_calls_save_on_instance(self, mock_instance):
        """Calls save() on instance after setting fields."""
        mixin = SoftDeleteMixin()
        
        mixin.perform_destroy(mock_instance)
        
        mock_instance.save.assert_called_once()

    def test_does_not_delete_instance_from_database(self, mock_instance):
        """Does not call delete() on instance (soft delete)."""
        mixin = SoftDeleteMixin()
        mock_instance.delete = MagicMock()
        
        mixin.perform_destroy(mock_instance)
        
        mock_instance.delete.assert_not_called()

    def test_handles_already_deleted_instance(self, mock_deleted_instance):
        """Handles already deleted instance without error."""
        mixin = SoftDeleteMixin()
        
        mixin.perform_destroy(mock_deleted_instance)
        
        assert mock_deleted_instance.is_deleted is True
        assert mock_deleted_instance.is_active is False
        mock_deleted_instance.save.assert_called_once()


# =====================
# SoftDeleteMixin.restore Tests
# =====================

class TestRestore:
    """Tests for SoftDeleteMixin.restore action."""

    def test_returns_400_when_object_not_deleted(
        self, soft_delete_mixin, mock_instance
    ):
        """Returns 400 status when object is not deleted."""
        mock_instance.is_deleted = False
        request = MagicMock()
        
        response = soft_delete_mixin.restore(request, pk=1)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_error_message_when_object_not_deleted(
        self, soft_delete_mixin, mock_instance
    ):
        """Returns error message when object is not deleted."""
        mock_instance.is_deleted = False
        request = MagicMock()
        
        response = soft_delete_mixin.restore(request, pk=1)
        
        assert response.data['detail'] == "Cet objet n'est pas supprimé."

    def test_sets_is_deleted_to_false_when_restoring(
        self, soft_delete_mixin, mock_deleted_instance
    ):
        """Sets is_deleted to False when restoring."""
        soft_delete_mixin.get_object = MagicMock(return_value=mock_deleted_instance)
        request = MagicMock()
        
        soft_delete_mixin.restore(request, pk=1)
        
        assert mock_deleted_instance.is_deleted is False

    def test_sets_is_active_to_true_when_restoring(
        self, soft_delete_mixin, mock_deleted_instance
    ):
        """Sets is_active to True when restoring."""
        soft_delete_mixin.get_object = MagicMock(return_value=mock_deleted_instance)
        request = MagicMock()
        
        soft_delete_mixin.restore(request, pk=1)
        
        assert mock_deleted_instance.is_active is True

    def test_calls_save_when_restoring(
        self, soft_delete_mixin, mock_deleted_instance
    ):
        """Calls save() on instance when restoring."""
        soft_delete_mixin.get_object = MagicMock(return_value=mock_deleted_instance)
        request = MagicMock()
        
        soft_delete_mixin.restore(request, pk=1)
        
        mock_deleted_instance.save.assert_called_once()

    def test_calls_get_object(self, soft_delete_mixin):
        """Calls get_object to retrieve the instance."""
        request = MagicMock()
        
        soft_delete_mixin.restore(request, pk=1)
        
        soft_delete_mixin.get_object.assert_called_once()

    def test_returns_serialized_data_on_success(
        self, soft_delete_mixin, mock_deleted_instance, mock_serializer
    ):
        """Returns serialized data on successful restore."""
        soft_delete_mixin.get_object = MagicMock(return_value=mock_deleted_instance)
        request = MagicMock()
        
        response = soft_delete_mixin.restore(request, pk=1)
        
        assert response.data == mock_serializer.data

    def test_returns_200_status_on_success(
        self, soft_delete_mixin, mock_deleted_instance
    ):
        """Returns 200 status on successful restore."""
        soft_delete_mixin.get_object = MagicMock(return_value=mock_deleted_instance)
        request = MagicMock()
        
        response = soft_delete_mixin.restore(request, pk=1)
        
        assert response.status_code == status.HTTP_200_OK

    def test_calls_get_serializer_with_restored_object(
        self, soft_delete_mixin, mock_deleted_instance
    ):
        """Calls get_serializer with the restored object."""
        soft_delete_mixin.get_object = MagicMock(return_value=mock_deleted_instance)
        request = MagicMock()
        
        soft_delete_mixin.restore(request, pk=1)
        
        soft_delete_mixin.get_serializer.assert_called_once_with(mock_deleted_instance)


# =====================
# IncludeDeletedMixin.filter_deleted Tests
# =====================

class TestFilterDeleted:
    """Tests for IncludeDeletedMixin.filter_deleted method."""

    def test_filters_deleted_when_include_deleted_not_provided(
        self, include_deleted_mixin, mock_queryset
    ):
        """Filters deleted objects when include_deleted param not provided."""
        include_deleted_mixin.request.query_params = {}
        
        result = include_deleted_mixin.filter_deleted(mock_queryset)
        
        mock_queryset.filter.assert_called_once_with(is_deleted=False)

    def test_filters_deleted_when_include_deleted_is_false(
        self, include_deleted_mixin, mock_queryset
    ):
        """Filters deleted objects when include_deleted=false."""
        include_deleted_mixin.request.query_params = {'include_deleted': 'false'}
        
        result = include_deleted_mixin.filter_deleted(mock_queryset)
        
        mock_queryset.filter.assert_called_once_with(is_deleted=False)

    def test_does_not_filter_when_include_deleted_is_true(
        self, include_deleted_mixin, mock_queryset
    ):
        """Does not filter deleted objects when include_deleted=true."""
        include_deleted_mixin.request.query_params = {'include_deleted': 'true'}
        
        result = include_deleted_mixin.filter_deleted(mock_queryset)
        
        mock_queryset.filter.assert_not_called()

    def test_returns_unfiltered_queryset_when_include_deleted_true(
        self, include_deleted_mixin, mock_queryset
    ):
        """Returns unfiltered queryset when include_deleted=true."""
        include_deleted_mixin.request.query_params = {'include_deleted': 'true'}
        
        result = include_deleted_mixin.filter_deleted(mock_queryset)
        
        assert result == mock_queryset

    def test_returns_filtered_queryset_when_include_deleted_false(
        self, include_deleted_mixin, mock_queryset
    ):
        """Returns filtered queryset when include_deleted=false."""
        include_deleted_mixin.request.query_params = {'include_deleted': 'false'}
        filtered_qs = MagicMock()
        mock_queryset.filter.return_value = filtered_qs
        
        result = include_deleted_mixin.filter_deleted(mock_queryset)
        
        assert result == filtered_qs

    def test_handles_uppercase_true_value(
        self, include_deleted_mixin, mock_queryset
    ):
        """Handles uppercase TRUE value for include_deleted."""
        include_deleted_mixin.request.query_params = {'include_deleted': 'TRUE'}
        
        result = include_deleted_mixin.filter_deleted(mock_queryset)
        
        mock_queryset.filter.assert_not_called()

    def test_handles_mixed_case_true_value(
        self, include_deleted_mixin, mock_queryset
    ):
        """Handles mixed case True value for include_deleted."""
        include_deleted_mixin.request.query_params = {'include_deleted': 'True'}
        
        result = include_deleted_mixin.filter_deleted(mock_queryset)
        
        mock_queryset.filter.assert_not_called()

    def test_handles_uppercase_false_value(
        self, include_deleted_mixin, mock_queryset
    ):
        """Handles uppercase FALSE value for include_deleted."""
        include_deleted_mixin.request.query_params = {'include_deleted': 'FALSE'}
        
        result = include_deleted_mixin.filter_deleted(mock_queryset)
        
        mock_queryset.filter.assert_called_once_with(is_deleted=False)

    def test_handles_invalid_value_as_false(
        self, include_deleted_mixin, mock_queryset
    ):
        """Handles invalid value as false (filters deleted)."""
        include_deleted_mixin.request.query_params = {'include_deleted': 'invalid'}
        
        result = include_deleted_mixin.filter_deleted(mock_queryset)
        
        mock_queryset.filter.assert_called_once_with(is_deleted=False)

    def test_handles_empty_string_value_as_false(
        self, include_deleted_mixin, mock_queryset
    ):
        """Handles empty string value as false (filters deleted)."""
        include_deleted_mixin.request.query_params = {'include_deleted': ''}
        
        result = include_deleted_mixin.filter_deleted(mock_queryset)
        
        mock_queryset.filter.assert_called_once_with(is_deleted=False)

    def test_handles_yes_value_as_false(
        self, include_deleted_mixin, mock_queryset
    ):
        """Handles 'yes' value as false (only 'true' is accepted)."""
        include_deleted_mixin.request.query_params = {'include_deleted': 'yes'}
        
        result = include_deleted_mixin.filter_deleted(mock_queryset)
        
        mock_queryset.filter.assert_called_once_with(is_deleted=False)

    def test_handles_1_value_as_false(
        self, include_deleted_mixin, mock_queryset
    ):
        """Handles '1' value as false (only 'true' is accepted)."""
        include_deleted_mixin.request.query_params = {'include_deleted': '1'}
        
        result = include_deleted_mixin.filter_deleted(mock_queryset)
        
        mock_queryset.filter.assert_called_once_with(is_deleted=False)


# =====================
# Edge Cases
# =====================

class TestEdgeCases:
    """Edge case tests for mixins."""

    def test_soft_delete_mixin_instantiation(self):
        """SoftDeleteMixin can be instantiated."""
        mixin = SoftDeleteMixin()
        
        assert mixin is not None

    def test_include_deleted_mixin_instantiation(self):
        """IncludeDeletedMixin can be instantiated."""
        mixin = IncludeDeletedMixin()
        
        assert mixin is not None

    def test_restore_action_has_correct_decorator_config(self):
        """Restore action has correct decorator configuration."""
        # Check that restore is decorated as an action
        restore_method = SoftDeleteMixin.restore
        
        # The action decorator sets these attributes
        assert hasattr(restore_method, 'detail')
        assert restore_method.detail is True
        assert hasattr(restore_method, 'url_path')
        assert hasattr(restore_method, 'url_name')

    def test_perform_destroy_with_none_values(self):
        """Handles instance with None values for is_deleted and is_active."""
        mixin = SoftDeleteMixin()
        instance = MagicMock()
        instance.is_deleted = None
        instance.is_active = None
        instance.save = MagicMock()
        
        mixin.perform_destroy(instance)
        
        assert instance.is_deleted is True
        assert instance.is_active is False
        instance.save.assert_called_once()

    def test_filter_deleted_with_chained_querysets(
        self, include_deleted_mixin
    ):
        """Handles chained querysets correctly."""
        # Create a queryset that returns itself on filter for chaining
        mock_qs = MagicMock()
        filtered_qs = MagicMock()
        mock_qs.filter.return_value = filtered_qs
        include_deleted_mixin.request.query_params = {'include_deleted': 'false'}
        
        result = include_deleted_mixin.filter_deleted(mock_qs)
        
        assert result == filtered_qs


# =====================
# Integration-like Tests
# =====================

class TestMixinCombination:
    """Tests for using both mixins together."""

    def test_viewset_with_both_mixins(self):
        """A class can inherit from both mixins."""
        class TestViewSet(SoftDeleteMixin, IncludeDeletedMixin):
            pass
        
        viewset = TestViewSet()
        
        assert hasattr(viewset, 'perform_destroy')
        assert hasattr(viewset, 'restore')
        assert hasattr(viewset, 'filter_deleted')

    def test_perform_destroy_then_restore_workflow(self):
        """Tests the workflow of deleting then restoring an object."""
        # Create instance
        instance = MagicMock()
        instance.is_deleted = False
        instance.is_active = True
        instance.save = MagicMock()
        
        # Create mixin with required methods
        mixin = SoftDeleteMixin()
        mixin.get_object = MagicMock(return_value=instance)
        mixin.get_serializer = MagicMock(return_value=MagicMock(data={'id': 1}))
        
        # Step 1: Soft delete
        mixin.perform_destroy(instance)
        
        assert instance.is_deleted is True
        assert instance.is_active is False
        
        # Step 2: Restore
        request = MagicMock()
        response = mixin.restore(request, pk=1)
        
        assert instance.is_deleted is False
        assert instance.is_active is True
        assert response.status_code == status.HTTP_200_OK


# =====================
# Summary of Covered Cases
# =====================
# SoftDeleteMixin.perform_destroy:
# - Sets is_deleted to True
# - Sets is_active to False
# - Calls save() on instance
# - Does not call delete() (soft delete)
# - Handles already deleted instance
#
# SoftDeleteMixin.restore:
# - Returns 400 when object not deleted
# - Returns error message when object not deleted
# - Sets is_deleted to False when restoring
# - Sets is_active to True when restoring
# - Calls save() when restoring
# - Calls get_object
# - Returns serialized data on success
# - Returns 200 status on success
# - Calls get_serializer with restored object
#
# IncludeDeletedMixin.filter_deleted:
# - Filters deleted when include_deleted not provided
# - Filters deleted when include_deleted=false
# - Does not filter when include_deleted=true
# - Returns unfiltered queryset when include_deleted=true
# - Returns filtered queryset when include_deleted=false
# - Handles uppercase TRUE value
# - Handles mixed case True value
# - Handles uppercase FALSE value
# - Handles invalid value as false
# - Handles empty string value as false
# - Handles 'yes' value as false
# - Handles '1' value as false
#
# Edge cases:
# - Mixin instantiation
# - Restore action decorator configuration
# - Instance with None values
# - Chained querysets
#
# Integration:
# - Class with both mixins
# - Delete then restore workflow