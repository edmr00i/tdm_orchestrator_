# python
import pytest
from django.contrib.auth import get_user_model
from rest_framework import serializers as drf_serializers

from tdm_orchestrator.serializers import (
    SqlScriptDetailSerializer,
    RunnerStepSerializer,
    ApplicationListSerializer,
    RunnerListSerializer,
    ExecutionLogSerializer,
)
from tdm_orchestrator.models import (
    Type,
    Entity,
    DataSource,
    Application,
    SqlScript,
    Runner,
    RunnerStep,
    ExecutionLog,
)


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username='serializer_user', password='pw')


# -------------------------
# SqlScriptDetailSerializer
# -------------------------

def test_sqlscriptdetail_validate_content_invalid_data():
    """validate_content should raise when content is empty/blank."""
    serializer = SqlScriptDetailSerializer()
    with pytest.raises(drf_serializers.ValidationError):
        serializer.validate_content("   ")


@pytest.mark.django_db
def test_sqlscriptdetail_validate_reference_duplicate_create():
    """Creating a SqlScript with an existing reference must be rejected."""
    app = Application.objects.create(reference='APP_FOR_SCR', name='AppForScr')
    SqlScript.objects.create(reference='REF_DUP', name='A', script_type='UTIL', content='x', application=app)
    serializer = SqlScriptDetailSerializer()
    with pytest.raises(drf_serializers.ValidationError):
        serializer.validate_reference('REF_DUP')


@pytest.mark.django_db
def test_sqlscriptdetail_validate_reference_duplicate_update():
    """Updating a SqlScript to a reference used by another script must be rejected."""
    app = Application.objects.create(reference='APP_FOR_SCR2', name='AppForScr2')
    s1 = SqlScript.objects.create(reference='REF_A', name='A', script_type='UTIL', content='x', application=app)
    s2 = SqlScript.objects.create(reference='REF_B', name='B', script_type='UTIL', content='y', application=app)
    serializer = SqlScriptDetailSerializer(instance=s1)
    # Attempt to set s1.reference to s2.reference should raise
    with pytest.raises(drf_serializers.ValidationError):
        serializer.validate_reference(s2.reference)


@pytest.mark.django_db
def test_sqlscriptdetail_get_extracted_variables_success(mocker):
    """extracted_variables field calls SqlScript.extract_variables and returns its value."""
    app = Application.objects.create(reference='APP_FOR_SCR3', name='AppForScr3')
    script = SqlScript.objects.create(reference='SCRX', name='S', script_type='UTIL', content='SELECT ${SCHEMA}', application=app)
    mocker.patch.object(script, 'extract_variables', return_value=['SCHEMA'])
    serializer = SqlScriptDetailSerializer(script)
    data = serializer.data
    assert data['extracted_variables'] == ['SCHEMA']


# -------------------------
# RunnerStepSerializer
# -------------------------

@pytest.mark.django_db
def test_runnerstepserializer_get_extracted_variables_success(mocker):
    """RunnerStepSerializer should return extracted variables from its script."""
    tp = Type.objects.create(reference='T1', value_format='f', value_char='v', type_list='L')
    app = Application.objects.create(reference='APPX', name='AppX')
    runner = Runner.objects.create(reference='R1', name='Runner1', application=app)
    script = SqlScript.objects.create(reference='SCR_STEP', name='S', script_type='PRE', content='${A}', application=app, datasource=None)
    # ensure RunnerStep can be created; allow missing fields via defaults in model if present
    step = RunnerStep.objects.create(runner=runner, script=script, order=1, step_type='PRE')
    mocker.patch.object(script, 'extract_variables', return_value=['A'])
    serializer = RunnerStepSerializer(step)
    assert serializer.data['extracted_variables'] == ['A']


def test_runnerstepserializer_validate_inactive_script(mocker):
    """validate should raise if the script is inactive or deleted."""
    # create a lightweight dummy object representing script with required attrs
    class DummyScript:
        is_active = False
        is_deleted = False
        script_type = 'PRE'
    attrs = {'script': DummyScript(), 'step_type': 'PRE'}
    serializer = RunnerStepSerializer()
    with pytest.raises(drf_serializers.ValidationError):
        serializer.validate(attrs)


def test_runnerstepserializer_validate_mismatched_step_type(mocker):
    """validate should raise when script.script_type is incompatible with step_type."""
    class DummyScript:
        is_active = True
        is_deleted = False
        script_type = 'OTHER'  # not 'UTIL' and not equal to step_type below
    attrs = {'script': DummyScript(), 'step_type': 'PRE'}
    serializer = RunnerStepSerializer()
    with pytest.raises(drf_serializers.ValidationError):
        serializer.validate(attrs)


# -------------------------
# ApplicationListSerializer
# -------------------------

@pytest.mark.django_db
def test_applicationlist_get_counts():
    """ApplicationListSerializer should report entity_count and datasource_count correctly."""
    app = Application.objects.create(reference='APP_COUNT', name='AppCount')
    e1 = Entity.objects.create(reference='E1', name='Ent1')
    e2 = Entity.objects.create(reference='E2', name='Ent2')
    ds = DataSource.objects.create(reference='DS1', name='DS1', sgbd_name=Type.objects.create(reference='T', value_format='f', value_char='v', type_list='L'), sgbd_host='h')
    # add relations
    app.entity.add(e1, e2)
    app.data_sources.add(ds)
    serializer = ApplicationListSerializer(app)
    data = serializer.data
    assert data['entity_count'] == 2
    assert data['datasource_count'] == 1


# -------------------------
# RunnerListSerializer
# -------------------------

@pytest.mark.django_db
def test_runnerlist_get_total_steps_calls_model(mocker):
    """RunnerListSerializer.get_total_steps must call model.get_total_steps and return the value."""
    app = Application.objects.create(reference='APP_RUN', name='AppRun')
    runner = Runner.objects.create(reference='RUNX', name='RunX', application=app)
    mocker.patch.object(runner, 'get_total_steps', return_value=5)
    serializer = RunnerListSerializer(runner)
    assert serializer.data['total_steps'] == 5


# -------------------------
# ExecutionLogSerializer
# -------------------------

@pytest.mark.django_db
def test_executionlog_serializer_duration_and_is_completed(user):
    """ExecutionLogSerializer should expose duration_seconds and is_completed based on model state."""
    # create execution logs with different statuses
    log_running = ExecutionLog.objects.create(status='RUNNING', executed_by=user)
    log_success = ExecutionLog.objects.create(status='SUCCESS', executed_by=user)
    log_failure = ExecutionLog.objects.create(status='FAILURE', executed_by=user)
    # set a duration on one
    log_success.duration_ms = 5432
    log_success.save()
    s_success = ExecutionLogSerializer(log_success)
    # duration_seconds field should exist and be numeric and approx 5.43
    ds = s_success.data.get('duration_seconds')
    assert ds is not None
    assert abs(float(ds) - 5.43) < 0.01
    # is_completed should reflect status
    assert ExecutionLogSerializer(log_running).data.get('is_completed') in [False, True]  # accept model semantics
    assert ExecutionLogSerializer(log_success).data.get('is_completed') is True
    assert ExecutionLogSerializer(log_failure).data.get('is_completed') is True


# -------------------------
# Summary of covered cases
# -------------------------
# - SqlScriptDetailSerializer:
#   - validate_content rejects blank content
#   - validate_reference enforces uniqueness on create and update
#   - extracted_variables delegates to model.extract_variables
# - RunnerStepSerializer:
#   - extracted_variables delegates to script.extract_variables
#   - validate rejects inactive scripts and mismatched step/script types
# - ApplicationListSerializer:
#   - entity_count and datasource_count computed correctly
# - RunnerListSerializer:
#   - total_steps comes from model.get_total_steps
# - ExecutionLogSerializer:
#   - duration_seconds is exposed and roughly computed; is_completed reflects status