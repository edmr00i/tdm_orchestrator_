"""
Mixins communs pour les ViewSets.

Ce module contient les mixins réutilisables pour les ViewSets.
"""

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status


class SoftDeleteMixin:
    """
    Mixin pour implémenter le soft delete.
    
    Requiert que le modèle ait les champs is_deleted et is_active.
    """
    
    def perform_destroy(self, instance):
        """Soft delete au lieu de suppression réelle."""
        instance.is_deleted = True
        instance.is_active = False
        instance.save()
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restaure un objet supprimé."""
        obj = self.get_object()
        
        if not obj.is_deleted:
            return Response(
                {'detail': 'Cet objet n\'est pas supprimé.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        obj.is_deleted = False
        obj.is_active = True
        obj.save()
        
        serializer = self.get_serializer(obj)
        return Response(serializer.data)


class IncludeDeletedMixin:
    """
    Mixin pour filtrer les objets supprimés.
    
    Ajoute le paramètre ?include_deleted=true pour inclure les supprimés.
    """
    
    def filter_deleted(self, queryset):
        """Filtre les objets supprimés selon le paramètre."""
        include_deleted = (
            self.request.query_params.get('include_deleted', 'false').lower() == 'true'
        )
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        return queryset
