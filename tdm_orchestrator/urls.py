from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import depuis le nouveau package api/views
from .api.views import (
    TypeViewSet,
    EntityViewSet,
    DataSourceViewSet,
    ApplicationViewSet,
    SqlScriptViewSet,
    RunnerViewSet,
    ExecutionLogViewSet,
)

# Configuration du router DRF
router = DefaultRouter()
router.register(r'types', TypeViewSet, basename='type')
router.register(r'entities', EntityViewSet, basename='entity')
router.register(r'datasources', DataSourceViewSet, basename='datasource')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'scripts', SqlScriptViewSet, basename='script')
router.register(r'runners', RunnerViewSet, basename='runner')
router.register(r'execution-logs', ExecutionLogViewSet, basename='executionlog')

urlpatterns = [
    path('', include(router.urls)),
]
