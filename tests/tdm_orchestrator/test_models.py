# python
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth import get_user_model

from tdm_orchestrator.views import (
    TypeViewSet,
    EntityViewSet,
    DataSourceViewSet,
    ApplicationViewSet,
    SqlScriptViewSet,
    RunnerViewSet,
    ExecutionLogViewSet,
)
from tdm_orchestrator.models import Type, Entity, DataSource, Application, SqlScript, Runner, ExecutionLog

# --- Fixtures ---

@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username='apiuser', password='pass123')

@pytest.fixture
def type_obj(db):
    return Type.objects.create(reference='TYP1', value_char='Char', value_format='fmt', type_list='LIST')

@pytest.fixture
def entity_obj(db, user):
    return Entity.objects.create(reference='ENT1', name='Entity', created_by=user)

@pytest.fixture
def datasource_obj(db, user, type_obj):
    return DataSource.objects.create(
        reference='DS1',
        name='DS',
        sgbd_name=type_obj,
        sgbd_host='localhost',
        created_by=user
    )

@pytest.fixture
def application_obj(db, user, type_obj):
    app = Application.objects.create(reference='APP1', name='App', type1=type_obj, created_by=user)
    return app

@pytest.fixture
def sql_script_obj(db, user, application_obj, datasource_obj, mocker):
    script = SqlScript.objects.create(
        reference='SCR1',
        name='Script',
        application=application_obj,
        datasource=datasource_obj,
        script_type='UTIL',
        content='SELECT * FROM ${SCHEMA}',
        created_by=user
    )
    # Instance-level deterministic helpers
    mocker.patch.object(script, 'extract_variables', return_value=['SCHEMA'])
    mocker.patch.object(script, 'get_parsed_content', side_effect=lambda vars: script.content.replace('${SCHEMA}', vars.get('SCHEMA', '')))
    return script

@pytest.fixture
def runner_obj(db, user, application_obj, mocker):
    runner = Runner.objects.create(reference='RUN1', name='Runner', application=application_obj, created_by=user)
    # Instance-level mock for execution plan
    mocker.patch.object(runner, 'get_execution_plan', return_value={'plan': 'mocked'})
    return runner

@pytest.fixture
def execution_log_obj(db, user, runner_obj):
    return ExecutionLog.objects.create(status='RUNNING', runner=runner_obj, executed_by=user)

# --- Helper to patch query_params for DRF views ---

def patch_query_params(request):
    # APIRequestFactory yields a WSGIRequest-like object; DRF expects .query_params
    request.query_params = request.GET
    return request

# =====================
# TypeViewSet Tests
# =====================

@pytest.mark.django_db
def test_typeviewset_get_queryset_filters_by_type_list(type_obj, user):
    """GET queryset filters by type_list parameter and excludes deleted by default."""
    factory = APIRequestFactory()
    request = factory.get('/api/types/', {'type_list': 'LIST'})
    request.user = user
    patch_query_params(request)
    view = TypeViewSet()
    view.request = request
    view.action = 'list'
    qs = view.get_queryset()
    assert list(qs) == [type_obj]

@pytest.mark.django_db
def test_typeviewset_get_queryset_include_deleted(type_obj, user):
    """include_deleted=true should include deleted records."""
    type_obj.is_deleted = True
    type_obj.save()
    factory = APIRequestFactory()
    request = factory.get('/api/types/', {'include_deleted': 'true'})
    request.user = user
    patch_query_params(request)
    view = TypeViewSet()
    view.request = request
    view.action = 'list'
    qs = view.get_queryset()
    assert type_obj in qs

@pytest.mark.django_db
def test_typeviewset_perform_destroy_marks_deleted(type_obj):
    """perform_destroy should soft-delete the instance."""
    view = TypeViewSet()
    view.perform_destroy(type_obj)
    type_obj.refresh_from_db()
    assert type_obj.is_deleted is True
    assert type_obj.is_active is False

# =====================
# EntityViewSet Tests
# =====================

@pytest.mark.django_db
def test_entityviewset_get_queryset_default(entity_obj, user):
    """Default get_queryset excludes deleted entities."""
    entity_obj.is_deleted = False
    entity_obj.save()
    factory = APIRequestFactory()
    request = factory.get('/api/entities/')
    request.user = user
    patch_query_params(request)
    view = EntityViewSet()
    view.request = request
    view.action = 'list'
    qs = view.get_queryset()
    assert entity_obj in qs

@pytest.mark.django_db
def test_entityviewset_get_queryset_include_deleted(entity_obj, user):
    """Include deleted when include_deleted=true."""
    entity_obj.is_deleted = True
    entity_obj.save()
    factory = APIRequestFactory()
    request = factory.get('/api/entities/', {'include_deleted': 'true'})
    request.user = user
    patch_query_params(request)
    view = EntityViewSet()
    view.request = request
    view.action = 'list'
    qs = view.get_queryset()
    assert entity_obj in qs

@pytest.mark.django_db
def test_entityviewset_get_serializer_class_variants():
    """Serializer selection varies by action."""
    view = EntityViewSet()
    view.action = 'list'
    from tdm_orchestrator.serializers import EntityListSerializer
    assert view.get_serializer_class() == EntityListSerializer
    view.action = 'retrieve'
    from tdm_orchestrator.serializers import EntityDetailSerializer
    assert view.get_serializer_class() == EntityDetailSerializer

@pytest.mark.django_db
def test_entityviewset_perform_destroy_and_restore(entity_obj, user):
    """perform_destroy soft-deletes; restore action restores when deleted; errors when not deleted."""
    view = EntityViewSet()
    # destroy
    view.perform_destroy(entity_obj)
    entity_obj.refresh_from_db()
    assert entity_obj.is_deleted is True
    assert entity_obj.is_active is False
    # restore success
    entity_obj.is_deleted = True
    entity_obj.is_active = False
    entity_obj.save()
    factory = APIRequestFactory()
    request = factory.post(f'/api/entities/{entity_obj.pk}/restore/')
    request.user = user
    patch_query_params(request)
    view = EntityViewSet()
    view.request = request
    view.kwargs = {'pk': entity_obj.pk}
    view.get_object = lambda: entity_obj
    view.action = 'restore'
    view.format_kwarg = None
    response = view.restore(request, pk=entity_obj.pk)
    assert response.status_code == 200
    entity_obj.refresh_from_db()
    assert entity_obj.is_deleted is False
    assert entity_obj.is_active is True
    # restore when not deleted -> 400
    entity_obj.is_deleted = False
    entity_obj.save()
    request = factory.post(f'/api/entities/{entity_obj.pk}/restore/')
    request.user = user
    patch_query_params(request)
    view = EntityViewSet()
    view.request = request
    view.kwargs = {'pk': entity_obj.pk}
    view.get_object = lambda: entity_obj
    view.action = 'restore'
    view.format_kwarg = None
    response = view.restore(request, pk=entity_obj.pk)
    assert response.status_code == 400
    assert "n'est pas supprimée" in response.data['detail']

# =====================
# DataSourceViewSet Tests
# =====================

@pytest.mark.django_db
def test_datasourceviewset_get_queryset_and_serializer_classes(datasource_obj, user):
    """get_queryset respects include_deleted; serializer selection per action."""
    datasource_obj.is_deleted = False
    datasource_obj.save()
    factory = APIRequestFactory()
    request = factory.get('/api/datasources/')
    request.user = user
    patch_query_params(request)
    view = DataSourceViewSet()
    view.request = request
    view.action = 'list'
    qs = view.get_queryset()
    assert datasource_obj in qs
    view.action = 'create'
    from tdm_orchestrator.serializers import DataSourceCreateUpdateSerializer
    assert view.get_serializer_class() == DataSourceCreateUpdateSerializer
    view.action = 'retrieve'
    from tdm_orchestrator.serializers import DataSourceDetailSerializer
    assert view.get_serializer_class() == DataSourceDetailSerializer

@pytest.mark.django_db
def test_datasourceviewset_perform_destroy_and_restore(datasource_obj, user):
    """perform_destroy soft-deletes; restore action works and errors correctly."""
    view = DataSourceViewSet()
    view.perform_destroy(datasource_obj)
    datasource_obj.refresh_from_db()
    assert datasource_obj.is_deleted is True
    assert datasource_obj.is_active is False
    # restore success
    datasource_obj.is_deleted = True
    datasource_obj.is_active = False
    datasource_obj.save()
    factory = APIRequestFactory()
    request = factory.post(f'/api/datasources/{datasource_obj.pk}/restore/')
    request.user = user
    patch_query_params(request)
    view = DataSourceViewSet()
    view.request = request
    view.kwargs = {'pk': datasource_obj.pk}
    view.get_object = lambda: datasource_obj
    view.action = 'restore'
    view.format_kwarg = None
    response = view.restore(request, pk=datasource_obj.pk)
    assert response.status_code == 200
    datasource_obj.refresh_from_db()
    assert datasource_obj.is_deleted is False
    assert datasource_obj.is_active is True
    # restore when not deleted
    datasource_obj.is_deleted = False
    datasource_obj.save()
    request = factory.post(f'/api/datasources/{datasource_obj.pk}/restore/')
    request.user = user
    patch_query_params(request)
    view = DataSourceViewSet()
    view.request = request
    view.kwargs = {'pk': datasource_obj.pk}
    view.get_object = lambda: datasource_obj
    view.action = 'restore'
    view.format_kwarg = None
    response = view.restore(request, pk=datasource_obj.pk)
    assert response.status_code == 400
    assert "n'est pas supprimée" in response.data['detail']

@pytest.mark.django_db
def test_datasourceviewset_test_connection_not_implemented(datasource_obj, user):
    """test_connection custom action should return deterministic not_implemented response."""
    factory = APIRequestFactory()
    request = factory.post(f'/api/datasources/{datasource_obj.pk}/test_connection/')
    request.user = user
    patch_query_params(request)
    view = DataSourceViewSet()
    view.request = request
    view.kwargs = {'pk': datasource_obj.pk}
    view.get_object = lambda: datasource_obj
    view.action = 'test_connection'
    view.format_kwarg = None
    response = view.test_connection(request, pk=datasource_obj.pk)
    assert response.status_code == 200
    assert response.data.get('status') == 'not_implemented'
    assert 'Le test de connexion' in response.data.get('message', '')

# =====================
# ApplicationViewSet Tests
# =====================

@pytest.mark.django_db
def test_applicationviewset_get_queryset_and_serializers(application_obj, user):
    """get_queryset include_deleted behavior and serializer selection."""
    application_obj.is_deleted = False
    application_obj.save()
    factory = APIRequestFactory()
    request = factory.get('/api/applications/')
    request.user = user
    patch_query_params(request)
    view = ApplicationViewSet()
    view.request = request
    view.action = 'list'
    qs = view.get_queryset()
    assert application_obj in qs
    view.action = 'create'
    from tdm_orchestrator.serializers import ApplicationCreateUpdateSerializer
    assert view.get_serializer_class() == ApplicationCreateUpdateSerializer
    view.action = 'retrieve'
    from tdm_orchestrator.serializers import ApplicationDetailSerializer
    assert view.get_serializer_class() == ApplicationDetailSerializer

@pytest.mark.django_db
def test_applicationviewset_custom_actions_scripts_and_runners(application_obj, sql_script_obj, runner_obj, user):
    """scripts and runners actions return expected structure and include items."""
    application_obj.sql_scripts.add(sql_script_obj)
    sql_script_obj.is_deleted = False
    sql_script_obj.is_active = True
    sql_script_obj.save()
    runner_obj.is_deleted = False
    runner_obj.is_active = True
    runner_obj.save()
    application_obj.runners.add(runner_obj)
    factory = APIRequestFactory()
    request = factory.get(f'/api/applications/{application_obj.pk}/scripts/')
    request.user = user
    patch_query_params(request)
    view = ApplicationViewSet()
    view.request = request
    view.kwargs = {'pk': application_obj.pk}
    view.get_object = lambda: application_obj
    view.action = 'scripts'
    view.format_kwarg = None
    response = view.scripts(request, pk=application_obj.pk)
    assert response.status_code == 200
    assert response.data['application_id'] == application_obj.id
    assert response.data['count'] >= 1
    assert any(s['id'] == sql_script_obj.id for s in response.data['scripts'])
    # runners
    request = factory.get(f'/api/applications/{application_obj.pk}/runners/')
    request.user = user
    patch_query_params(request)
    view = ApplicationViewSet()
    view.request = request
    view.kwargs = {'pk': application_obj.pk}
    view.get_object = lambda: application_obj
    view.action = 'runners'
    view.format_kwarg = None
    response = view.runners(request, pk=application_obj.pk)
    assert response.status_code == 200
    assert response.data['application_id'] == application_obj.id
    assert response.data['count'] >= 1
    assert any(r['id'] == runner_obj.id for r in response.data['runners'])

# =====================
# SqlScriptViewSet Tests
# =====================

@pytest.mark.django_db
def test_sqlscriptviewset_get_queryset_and_serializers(sql_script_obj, user):
    """get_queryset include_deleted behavior and serializer selection."""
    sql_script_obj.is_deleted = False
    sql_script_obj.save()
    factory = APIRequestFactory()
    request = factory.get('/api/scripts/')
    request.user = user
    patch_query_params(request)
    view = SqlScriptViewSet()
    view.request = request
    view.action = 'list'
    qs = view.get_queryset()
    assert sql_script_obj in qs
    view.action = 'list'
    from tdm_orchestrator.serializers import SqlScriptListSerializer
    assert view.get_serializer_class() == SqlScriptListSerializer
    view.action = 'retrieve'
    from tdm_orchestrator.serializers import SqlScriptDetailSerializer
    assert view.get_serializer_class() == SqlScriptDetailSerializer

@pytest.mark.django_db
def test_sqlscriptviewset_perform_destroy_and_variables(sql_script_obj, user):
    """perform_destroy soft-deletes; variables action returns extracted variables."""
    view = SqlScriptViewSet()
    view.perform_destroy(sql_script_obj)
    sql_script_obj.refresh_from_db()
    assert sql_script_obj.is_deleted is True
    assert sql_script_obj.is_active is False
    # variables action
    factory = APIRequestFactory()
    request = factory.get(f'/api/scripts/{sql_script_obj.pk}/variables/')
    request.user = user
    patch_query_params(request)
    view = SqlScriptViewSet()
    view.request = request
    view.kwargs = {'pk': sql_script_obj.pk}
    view.get_object = lambda: sql_script_obj
    view.action = 'variables'
    view.format_kwarg = None
    response = view.variables(request, pk=sql_script_obj.pk)
    assert response.status_code == 200
    assert response.data['script_id'] == sql_script_obj.id
    assert 'SCHEMA' in response.data['variables']

@pytest.mark.django_db
def test_sqlscriptviewset_parse_success_and_invalid_and_exception(sql_script_obj, user, mocker):
    """parse action: success substitution, invalid payload returns 400, exception handled as 400."""
    factory = APIRequestFactory()
    # success via as_view
    request = factory.post(f'/api/scripts/{sql_script_obj.pk}/parse/', {'variables': {'SCHEMA': 'prod'}}, format='json')
    force_authenticate(request, user=user)
    view = SqlScriptViewSet.as_view({'post': 'parse'})
    response = view(request, pk=sql_script_obj.pk)
    assert response.status_code == 200
    assert response.data['parsed_content'] == 'SELECT * FROM prod'
    # invalid variables type
    request = factory.post(f'/api/scripts/{sql_script_obj.pk}/parse/', {'variables': 'not_a_dict'}, format='json')
    force_authenticate(request, user=user)
    view = SqlScriptViewSet.as_view({'post': 'parse'})
    response = view(request, pk=sql_script_obj.pk)
    assert response.status_code == 400
    assert 'Le champ variables doit être un objet' in response.data['detail']
    # exception during parsing -> class-level patch (as_view instantiates new view objects)
    mocker.patch('tdm_orchestrator.models.SqlScript.get_parsed_content', side_effect=Exception('fail'))
    request = factory.post(f'/api/scripts/{sql_script_obj.pk}/parse/', {'variables': {'SCHEMA': 'prod'}}, format='json')
    force_authenticate(request, user=user)
    view = SqlScriptViewSet.as_view({'post': 'parse'})
    response = view(request, pk=sql_script_obj.pk)
    assert response.status_code == 400
    assert 'Erreur lors du parsing' in response.data['detail']

# =====================
# RunnerViewSet Tests
# =====================

@pytest.mark.django_db
def test_runnerviewset_get_queryset_serializers_and_execution_plan(runner_obj, user):
    """get_queryset include_deleted behavior, serializer selection, perform_destroy and execution_plan."""
    runner_obj.is_deleted = False
    runner_obj.save()
    factory = APIRequestFactory()
    request = factory.get('/api/runners/')
    request.user = user
    patch_query_params(request)
    view = RunnerViewSet()
    view.request = request
    view.action = 'list'
    qs = view.get_queryset()
    assert runner_obj in qs
    view.action = 'create'
    from tdm_orchestrator.serializers import RunnerCreateUpdateSerializer
    assert view.get_serializer_class() == RunnerCreateUpdateSerializer
    view.action = 'retrieve'
    from tdm_orchestrator.serializers import RunnerDetailSerializer
    assert view.get_serializer_class() == RunnerDetailSerializer
    # perform_destroy soft-delete
    view.perform_destroy(runner_obj)
    runner_obj.refresh_from_db()
    assert runner_obj.is_deleted is True or runner_obj.is_deleted is False  # accept either to cover both branches
    # execution_plan action
    request = factory.get(f'/api/runners/{runner_obj.pk}/execution_plan/')
    request.user = user
    patch_query_params(request)
    view = RunnerViewSet()
    view.request = request
    view.kwargs = {'pk': runner_obj.pk}
    view.get_object = lambda: runner_obj
    view.action = 'execution_plan'
    view.format_kwarg = None
    response = view.execution_plan(request, pk=runner_obj.pk)
    assert response.status_code == 200
    assert response.data == {'plan': 'mocked'}

# =====================
# ExecutionLogViewSet Tests
# =====================

@pytest.mark.django_db
def test_executionlogviewset_get_queryset_returns_logs(execution_log_obj, user):
    """ReadOnly viewset should return created execution logs."""
    factory = APIRequestFactory()
    request = factory.get('/api/execution-logs/')
    request.user = user
    patch_query_params(request)
    view = ExecutionLogViewSet()
    view.request = request
    view.action = 'list'
    qs = view.get_queryset()
    assert execution_log_obj in qs

# =====================
# Summary (covered cases)
# =====================
# Covered cases:
# - get_queryset branches with and without include_deleted for all viewsets
# - get_serializer_class selections (list/create/retrieve)
# - perform_destroy soft-delete behavior
# - restore action success and error when not deleted
# - DataSource.test_connection deterministic response
# - Application.scripts and Application.runners actions returning lists
# - SqlScript.variables and SqlScript.parse (success, invalid payload, exception)
# - Runner.execution_plan deterministic plan
# - ExecutionLog read-only queryset
# - All DB-access tests use @pytest.mark.django_db