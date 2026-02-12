# python
import pytest
from django.contrib.auth import get_user_model
from rest_framework import serializers as drf_serializers
from unittest.mock import MagicMock

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
    SqlScriptDetailSerializer,
    RunnerStepSerializer,
    RunnerStepNestedSerializer,
    RunnerStepCreateSerializer,
    RunnerListSerializer,
    RunnerDetailSerializer,
    RunnerCreateUpdateSerializer,
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
    """Create a test user for serializer tests."""
    return get_user_model().objects.create_user(username='serializer_user', password='pw')


@pytest.fixture
def sgbd_type(db):
    """Create a SGBD type for DataSource tests."""
    return Type.objects.create(
        reference='SGBD_MYSQL',
        value_format='f',
        value_char='MySQL',
        type_list='SGBD'
    )


@pytest.fixture
def forme_juridique_type(db):
    """Create a forme juridique type for Entity tests."""
    return Type.objects.create(
        reference='FJ_SA',
        value_format='f',
        value_char='SA',
        type_list='FORME_JURIDIQUE'
    )


@pytest.fixture
def type_entite_type(db):
    """Create a type entite type for Entity tests."""
    return Type.objects.create(
        reference='TE_FILIALE',
        value_format='f',
        value_char='Filiale',
        type_list='TYPE_ENTITE'
    )


@pytest.fixture
def app_type(db):
    """Create an application type for Application tests."""
    return Type.objects.create(
        reference='APP_TYPE_WEB',
        value_format='f',
        value_char='Web Application',
        type_list='APP_TYPE'
    )


# =====================
# TypeSerializer Tests
# =====================

class TestTypeSerializer:
    """Tests for TypeSerializer."""

    @pytest.mark.django_db
    def test_serializes_all_fields_correctly(self):
        """TypeSerializer should serialize all fields correctly."""
        type_obj = Type.objects.create(
            reference='TYPE_TEST',
            value_format='string',
            value_char='Test Value',
            value_num=42,
            type_list='TEST_LIST',
            source='SYSTEM',
            lock=False,
            is_active=True,
            is_deleted=False
        )
        serializer = TypeSerializer(type_obj)
        data = serializer.data
        
        assert data['reference'] == 'TYPE_TEST'
        assert data['value_format'] == 'string'
        assert data['value_char'] == 'Test Value'
        assert data['value_num'] == 42
        assert data['type_list'] == 'TEST_LIST'
        assert data['source'] == 'SYSTEM'
        assert data['lock'] is False
        assert data['is_active'] is True
        assert data['is_deleted'] is False

    @pytest.mark.django_db
    def test_read_only_fields_not_writable(self):
        """TypeSerializer should not allow writing to read-only fields."""
        data = {
            'id': 999,
            'reference': 'TYPE_NEW',
            'value_format': 'f',
            'value_char': 'New',
            'type_list': 'LIST',
            'created_at': '2020-01-01T00:00:00Z',
            'update_at': '2020-01-01T00:00:00Z',
        }
        serializer = TypeSerializer(data=data)
        assert serializer.is_valid()
        # id and timestamps should not be in validated_data
        assert 'id' not in serializer.validated_data
        assert 'created_at' not in serializer.validated_data
        assert 'update_at' not in serializer.validated_data

    @pytest.mark.django_db
    def test_meta_fields_list_complete(self):
        """TypeSerializer Meta.fields should include all expected fields."""
        expected_fields = [
            'id', 'reference', 'value_format', 'value_char', 'value_num',
            'value_date', 'type_list', 'source', 'lock', 'is_active',
            'is_deleted', 'created_at', 'update_at', 'extern_ref_admin_lov'
        ]
        assert TypeSerializer.Meta.fields == expected_fields


# =====================
# EntityListSerializer Tests
# =====================

class TestEntityListSerializer:
    """Tests for EntityListSerializer."""

    @pytest.mark.django_db
    def test_nested_field_forme_juridique_name(self, forme_juridique_type, user):
        """EntityListSerializer should display forme_juridique_name correctly."""
        entity = Entity.objects.create(
            reference='ENT_TEST',
            name='Test Entity',
            forme_juridique=forme_juridique_type,
            created_by=user
        )
        serializer = EntityListSerializer(entity)
        data = serializer.data
        
        assert data['forme_juridique_name'] == 'SA'

    @pytest.mark.django_db
    def test_nested_field_type_entite_name(self, type_entite_type, user):
        """EntityListSerializer should display type_entite_name correctly."""
        entity = Entity.objects.create(
            reference='ENT_TEST2',
            name='Test Entity 2',
            type_entite=type_entite_type,
            created_by=user
        )
        serializer = EntityListSerializer(entity)
        data = serializer.data
        
        assert data['type_entite_name'] == 'Filiale'

    @pytest.mark.django_db
    def test_nested_field_parent_name(self, user):
        """EntityListSerializer should display parent_name correctly."""
        parent = Entity.objects.create(reference='PARENT', name='Parent Entity')
        child = Entity.objects.create(
            reference='CHILD',
            name='Child Entity',
            parent=parent,
            created_by=user
        )
        serializer = EntityListSerializer(child)
        data = serializer.data
        
        assert data['parent_name'] == 'Parent Entity'

    @pytest.mark.django_db
    def test_nested_field_created_by_name(self, user):
        """EntityListSerializer should display created_by_name correctly."""
        entity = Entity.objects.create(
            reference='ENT_TEST3',
            name='Test Entity 3',
            created_by=user
        )
        serializer = EntityListSerializer(entity)
        data = serializer.data
        
        assert data['created_by_name'] == 'serializer_user'

    @pytest.mark.django_db
    def test_null_nested_fields(self):
        """EntityListSerializer should handle null nested fields."""
        entity = Entity.objects.create(
            reference='ENT_NULL',
            name='Entity Without Relations'
        )
        serializer = EntityListSerializer(entity)
        data = serializer.data
        
        assert data['forme_juridique_name'] is None
        assert data['type_entite_name'] is None
        assert data['parent_name'] is None
        assert data['created_by_name'] is None


# =====================
# EntityDetailSerializer Tests
# =====================

class TestEntityDetailSerializer:
    """Tests for EntityDetailSerializer."""

    @pytest.mark.django_db
    def test_includes_additional_fields(self, forme_juridique_type, user):
        """EntityDetailSerializer should include address_postal and numero_dpo."""
        entity = Entity.objects.create(
            reference='ENT_DETAIL',
            name='Detail Entity',
            address_postal='123 Main St',
            numero_dpo='DPO123',
            forme_juridique=forme_juridique_type,
            created_by=user
        )
        serializer = EntityDetailSerializer(entity)
        data = serializer.data
        
        assert data['address_postal'] == '123 Main St'
        assert data['numero_dpo'] == 'DPO123'
        assert data['is_deleted'] is False

    @pytest.mark.django_db
    def test_read_only_fields(self):
        """EntityDetailSerializer should not allow writing to read-only fields."""
        expected_read_only = ['id', 'created_at', 'updated_at', 'created_by']
        assert EntityDetailSerializer.Meta.read_only_fields == expected_read_only


# =====================
# DataSourceListSerializer Tests
# =====================

class TestDataSourceListSerializer:
    """Tests for DataSourceListSerializer."""

    @pytest.mark.django_db
    def test_sgbd_name_display(self, sgbd_type, user):
        """DataSourceListSerializer should display sgbd_name_display correctly."""
        ds = DataSource.objects.create(
            reference='DS_TEST',
            name='Test DataSource',
            sgbd_name=sgbd_type,
            sgbd_host='localhost',
            sgbd_port=3306,
            sgbd_database='testdb',
            created_by=user
        )
        serializer = DataSourceListSerializer(ds)
        data = serializer.data
        
        assert data['sgbd_name_display'] == 'MySQL'
        assert data['sgbd_host'] == 'localhost'
        assert data['sgbd_port'] == 3306
        assert data['sgbd_database'] == 'testdb'

    @pytest.mark.django_db
    def test_created_by_name(self, sgbd_type, user):
        """DataSourceListSerializer should display created_by_name correctly."""
        ds = DataSource.objects.create(
            reference='DS_TEST2',
            name='Test DataSource 2',
            sgbd_name=sgbd_type,
            sgbd_host='localhost',
            created_by=user
        )
        serializer = DataSourceListSerializer(ds)
        data = serializer.data
        
        assert data['created_by_name'] == 'serializer_user'


# =====================
# DataSourceDetailSerializer Tests
# =====================

class TestDataSourceDetailSerializer:
    """Tests for DataSourceDetailSerializer."""

    @pytest.mark.django_db
    def test_includes_security_fields(self, sgbd_type, user):
        """DataSourceDetailSerializer should include TLS and X509 fields."""
        ds = DataSource.objects.create(
            reference='DS_DETAIL',
            name='Detail DataSource',
            sgbd_name=sgbd_type,
            sgbd_host='localhost',
            sgbd_tls=True,
            sgbd_x509=True,
            sgbd_ca_file='/path/to/ca.pem',
            created_by=user
        )
        serializer = DataSourceDetailSerializer(ds)
        data = serializer.data
        
        assert data['sgbd_tls'] is True
        assert data['sgbd_x509'] is True
        assert data['sgbd_ca_file'] == '/path/to/ca.pem'

    def test_write_only_fields_not_in_output(self):
        """DataSourceDetailSerializer should not expose password fields in output."""
        extra_kwargs = DataSourceDetailSerializer.Meta.extra_kwargs
        
        assert extra_kwargs.get('sgbd_password', {}).get('write_only') is True
        assert extra_kwargs.get('priv_key', {}).get('write_only') is True
        assert extra_kwargs.get('sgbd_certificate_key_file_password', {}).get('write_only') is True


# =====================
# DataSourceCreateUpdateSerializer Tests
# =====================

class TestDataSourceCreateUpdateSerializer:
    """Tests for DataSourceCreateUpdateSerializer."""

    def test_includes_password_fields(self):
        """DataSourceCreateUpdateSerializer should include password fields for writing."""
        fields = DataSourceCreateUpdateSerializer.Meta.fields
        
        assert 'sgbd_password' in fields
        assert 'priv_key' in fields
        assert 'sgbd_certificate_key_file_password' in fields

    def test_password_fields_are_write_only(self):
        """DataSourceCreateUpdateSerializer password fields should be write-only."""
        extra_kwargs = DataSourceCreateUpdateSerializer.Meta.extra_kwargs
        
        assert extra_kwargs.get('sgbd_password', {}).get('write_only') is True
        assert extra_kwargs.get('priv_key', {}).get('write_only') is True
        assert extra_kwargs.get('sgbd_certificate_key_file_password', {}).get('write_only') is True


# =====================
# ApplicationDetailSerializer Tests
# =====================

class TestApplicationDetailSerializer:
    """Tests for ApplicationDetailSerializer."""

    @pytest.mark.django_db
    def test_nested_entities_serialization(self, user):
        """ApplicationDetailSerializer should serialize nested entities."""
        entity = Entity.objects.create(reference='ENT_APP', name='App Entity')
        app = Application.objects.create(
            reference='APP_DETAIL',
            name='Detail App',
            created_by=user
        )
        app.entity.add(entity)
        
        serializer = ApplicationDetailSerializer(app)
        data = serializer.data
        
        assert 'entities' in data
        assert len(data['entities']) == 1
        assert data['entities'][0]['name'] == 'App Entity'

    @pytest.mark.django_db
    def test_nested_datasources_serialization(self, sgbd_type, user):
        """ApplicationDetailSerializer should serialize nested datasources."""
        ds = DataSource.objects.create(
            reference='DS_APP',
            name='App DataSource',
            sgbd_name=sgbd_type,
            sgbd_host='localhost'
        )
        app = Application.objects.create(
            reference='APP_DETAIL2',
            name='Detail App 2',
            created_by=user
        )
        app.data_sources.add(ds)
        
        serializer = ApplicationDetailSerializer(app)
        data = serializer.data
        
        assert 'datasources' in data
        assert len(data['datasources']) == 1
        assert data['datasources'][0]['name'] == 'App DataSource'

    @pytest.mark.django_db
    def test_type1_name_display(self, app_type, user):
        """ApplicationDetailSerializer should display type1_name correctly."""
        app = Application.objects.create(
            reference='APP_TYPE',
            name='Typed App',
            type1=app_type,
            created_by=user
        )
        serializer = ApplicationDetailSerializer(app)
        data = serializer.data
        
        assert data['type1_name'] == 'Web Application'


# =====================
# ApplicationCreateUpdateSerializer Tests
# =====================

class TestApplicationCreateUpdateSerializer:
    """Tests for ApplicationCreateUpdateSerializer."""

    def test_fields_list(self):
        """ApplicationCreateUpdateSerializer should have correct fields."""
        expected_fields = [
            'id', 'reference', 'name', 'type1', 'type2', 'address',
            'description', 'mac_address', 'ip_address', 'entity',
            'data_sources', 'is_active'
        ]
        assert ApplicationCreateUpdateSerializer.Meta.fields == expected_fields

    def test_read_only_fields(self):
        """ApplicationCreateUpdateSerializer should have id as read-only."""
        assert ApplicationCreateUpdateSerializer.Meta.read_only_fields == ['id']


# =====================
# SqlScriptListSerializer Tests
# =====================

class TestSqlScriptListSerializer:
    """Tests for SqlScriptListSerializer."""

    @pytest.mark.django_db
    def test_application_name_display(self, user):
        """SqlScriptListSerializer should display application_name correctly."""
        app = Application.objects.create(
            reference='APP_SCRIPT',
            name='Script App',
            created_by=user
        )
        script = SqlScript.objects.create(
            reference='SCRIPT_LIST',
            name='List Script',
            script_type='UTIL',
            content='SELECT 1',
            application=app
        )
        serializer = SqlScriptListSerializer(script)
        data = serializer.data
        
        assert data['application_name'] == 'Script App'

    @pytest.mark.django_db
    def test_datasource_name_display(self, sgbd_type, user):
        """SqlScriptListSerializer should display datasource_name correctly."""
        app = Application.objects.create(reference='APP_SCRIPT2', name='Script App 2')
        ds = DataSource.objects.create(
            reference='DS_SCRIPT',
            name='Script DataSource',
            sgbd_name=sgbd_type,
            sgbd_host='localhost'
        )
        script = SqlScript.objects.create(
            reference='SCRIPT_LIST2',
            name='List Script 2',
            script_type='UTIL',
            content='SELECT 1',
            application=app,
            datasource=ds
        )
        serializer = SqlScriptListSerializer(script)
        data = serializer.data
        
        assert data['datasource_name'] == 'Script DataSource'

    @pytest.mark.django_db
    def test_null_datasource_name(self, user):
        """SqlScriptListSerializer should handle null datasource."""
        app = Application.objects.create(reference='APP_SCRIPT3', name='Script App 3')
        script = SqlScript.objects.create(
            reference='SCRIPT_LIST3',
            name='List Script 3',
            script_type='UTIL',
            content='SELECT 1',
            application=app,
            datasource=None
        )
        serializer = SqlScriptListSerializer(script)
        data = serializer.data
        
        assert data['datasource_name'] is None


# =====================
# SqlScriptDetailSerializer Additional Tests
# =====================

class TestSqlScriptDetailSerializerAdditional:
    """Additional tests for SqlScriptDetailSerializer."""

    def test_validate_content_valid_success(self):
        """validate_content should pass for non-empty content."""
        serializer = SqlScriptDetailSerializer()
        result = serializer.validate_content("SELECT * FROM table")
        
        assert result == "SELECT * FROM table"

    def test_validate_content_whitespace_only_invalid(self):
        """validate_content should reject whitespace-only content."""
        serializer = SqlScriptDetailSerializer()
        
        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate_content("   \n\t   ")
        
        assert "Le contenu SQL ne peut pas être vide" in str(exc_info.value)

    def test_validate_content_empty_string_invalid(self):
        """validate_content should reject empty string."""
        serializer = SqlScriptDetailSerializer()
        
        with pytest.raises(drf_serializers.ValidationError):
            serializer.validate_content("")

    @pytest.mark.django_db
    def test_validate_reference_unique_on_create(self):
        """validate_reference should allow unique reference on create."""
        app = Application.objects.create(reference='APP_REF', name='Ref App')
        SqlScript.objects.create(
            reference='EXISTING_REF',
            name='Existing',
            script_type='UTIL',
            content='x',
            application=app
        )
        
        serializer = SqlScriptDetailSerializer()
        # Should not raise for a new unique reference
        result = serializer.validate_reference('NEW_UNIQUE_REF')
        
        assert result == 'NEW_UNIQUE_REF'

    @pytest.mark.django_db
    def test_validate_reference_allows_same_on_update(self):
        """validate_reference should allow same reference when updating same instance."""
        app = Application.objects.create(reference='APP_REF2', name='Ref App 2')
        script = SqlScript.objects.create(
            reference='MY_REF',
            name='My Script',
            script_type='UTIL',
            content='x',
            application=app
        )
        
        serializer = SqlScriptDetailSerializer(instance=script)
        # Should not raise when reference is the same
        result = serializer.validate_reference('MY_REF')
        
        assert result == 'MY_REF'


# =====================
# RunnerStepSerializer Additional Tests
# =====================

class TestRunnerStepSerializerAdditional:
    """Additional tests for RunnerStepSerializer."""

    def test_get_extracted_variables_no_script(self):
        """get_extracted_variables should return empty list when script is None."""
        # Create a mock step with script attribute set to None
        mock_step = MagicMock()
        mock_step.script = None
        
        serializer = RunnerStepSerializer()
        result = serializer.get_extracted_variables(mock_step)
        
        assert result == []

    def test_validate_deleted_script_raises(self):
        """validate should raise if script is deleted."""
        class DummyScript:
            is_active = True
            is_deleted = True
            script_type = 'PRE'
        
        attrs = {'script': DummyScript(), 'step_type': 'PRE'}
        serializer = RunnerStepSerializer()
        
        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate(attrs)
        
        assert 'script' in exc_info.value.detail

    def test_validate_util_script_type_allowed(self):
        """validate should allow UTIL script type with any step_type."""
        class DummyScript:
            is_active = True
            is_deleted = False
            script_type = 'UTIL'
        
        attrs = {'script': DummyScript(), 'step_type': 'PRE'}
        serializer = RunnerStepSerializer()
        
        # Should not raise
        result = serializer.validate(attrs)
        
        assert result == attrs

    def test_validate_matching_step_type_allowed(self):
        """validate should allow when script_type matches step_type."""
        class DummyScript:
            is_active = True
            is_deleted = False
            script_type = 'PRE'
        
        attrs = {'script': DummyScript(), 'step_type': 'PRE'}
        serializer = RunnerStepSerializer()
        
        # Should not raise
        result = serializer.validate(attrs)
        
        assert result == attrs


# =====================
# RunnerStepNestedSerializer Tests
# =====================

class TestRunnerStepNestedSerializer:
    """Tests for RunnerStepNestedSerializer."""

    def test_fields_list(self):
        """RunnerStepNestedSerializer should have correct fields."""
        expected_fields = ['id', 'script', 'order', 'step_type', 'step_type_display']
        assert RunnerStepNestedSerializer.Meta.fields == expected_fields


# =====================
# RunnerStepCreateSerializer Tests
# =====================

class TestRunnerStepCreateSerializer:
    """Tests for RunnerStepCreateSerializer."""

    def test_fields_list(self):
        """RunnerStepCreateSerializer should have minimal fields."""
        expected_fields = ['script', 'order', 'step_type']
        assert RunnerStepCreateSerializer.Meta.fields == expected_fields


# =====================
# RunnerListSerializer Additional Tests
# =====================

class TestRunnerListSerializerAdditional:
    """Additional tests for RunnerListSerializer."""

    @pytest.mark.django_db
    def test_get_last_execution_no_logs(self):
        """get_last_execution should return None when no execution logs exist."""
        app = Application.objects.create(reference='APP_RUNNER', name='Runner App')
        runner = Runner.objects.create(reference='RUNNER_NO_LOG', name='No Log Runner', application=app)
        
        serializer = RunnerListSerializer(runner)
        data = serializer.data
        
        assert data['last_execution'] is None

    @pytest.mark.django_db
    def test_get_last_execution_with_logs(self, user):
        """get_last_execution should return latest execution log info."""
        app = Application.objects.create(reference='APP_RUNNER2', name='Runner App 2')
        runner = Runner.objects.create(reference='RUNNER_WITH_LOG', name='Log Runner', application=app)
        
        # Create execution logs
        log1 = ExecutionLog.objects.create(runner=runner, status='SUCCESS', executed_by=user)
        log2 = ExecutionLog.objects.create(runner=runner, status='FAILURE', executed_by=user)
        
        serializer = RunnerListSerializer(runner)
        data = serializer.data
        
        assert data['last_execution'] is not None
        assert 'status' in data['last_execution']
        assert 'started_at' in data['last_execution']

    @pytest.mark.django_db
    def test_application_name_display(self, user):
        """RunnerListSerializer should display application_name correctly."""
        app = Application.objects.create(reference='APP_RUNNER3', name='Runner App 3')
        runner = Runner.objects.create(
            reference='RUNNER_APP',
            name='App Runner',
            application=app,
            created_by=user
        )
        
        serializer = RunnerListSerializer(runner)
        data = serializer.data
        
        assert data['application_name'] == 'Runner App 3'


# =====================
# RunnerDetailSerializer Tests
# =====================

class TestRunnerDetailSerializer:
    """Tests for RunnerDetailSerializer."""

    @pytest.mark.django_db
    def test_get_pre_steps(self):
        """get_pre_steps should return PRE steps."""
        app = Application.objects.create(reference='APP_DETAIL_RUN', name='Detail Runner App')
        runner = Runner.objects.create(reference='RUNNER_DETAIL', name='Detail Runner', application=app)
        script = SqlScript.objects.create(
            reference='PRE_SCRIPT',
            name='Pre Script',
            script_type='PRE',
            content='SELECT 1',
            application=app
        )
        RunnerStep.objects.create(runner=runner, script=script, order=1, step_type='PRE')
        
        serializer = RunnerDetailSerializer(runner)
        data = serializer.data
        
        assert 'pre_steps' in data
        assert len(data['pre_steps']) == 1

    @pytest.mark.django_db
    def test_get_post_steps(self):
        """get_post_steps should return POST steps."""
        app = Application.objects.create(reference='APP_DETAIL_RUN2', name='Detail Runner App 2')
        runner = Runner.objects.create(reference='RUNNER_DETAIL2', name='Detail Runner 2', application=app)
        script = SqlScript.objects.create(
            reference='POST_SCRIPT',
            name='Post Script',
            script_type='POST',
            content='SELECT 1',
            application=app
        )
        RunnerStep.objects.create(runner=runner, script=script, order=1, step_type='POST')
        
        serializer = RunnerDetailSerializer(runner)
        data = serializer.data
        
        assert 'post_steps' in data
        assert len(data['post_steps']) == 1

    @pytest.mark.django_db
    def test_get_execution_plan(self, mocker):
        """get_execution_plan should call model.get_execution_plan."""
        app = Application.objects.create(reference='APP_PLAN', name='Plan App')
        runner = Runner.objects.create(reference='RUNNER_PLAN', name='Plan Runner', application=app)
        
        mocker.patch.object(runner, 'get_execution_plan', return_value=[{'step': 1}])
        
        serializer = RunnerDetailSerializer(runner)
        data = serializer.data
        
        assert data['execution_plan'] == [{'step': 1}]

    @pytest.mark.django_db
    def test_validate_reference_duplicate_on_create(self):
        """validate_reference should reject duplicate reference on create."""
        app = Application.objects.create(reference='APP_VAL', name='Val App')
        Runner.objects.create(reference='EXISTING_RUNNER', name='Existing', application=app)
        
        serializer = RunnerDetailSerializer()
        
        with pytest.raises(drf_serializers.ValidationError):
            serializer.validate_reference('EXISTING_RUNNER')

    @pytest.mark.django_db
    def test_validate_reference_allows_same_on_update(self):
        """validate_reference should allow same reference when updating same instance."""
        app = Application.objects.create(reference='APP_VAL2', name='Val App 2')
        runner = Runner.objects.create(reference='MY_RUNNER', name='My Runner', application=app)
        
        serializer = RunnerDetailSerializer(instance=runner)
        result = serializer.validate_reference('MY_RUNNER')
        
        assert result == 'MY_RUNNER'


# =====================
# RunnerCreateUpdateSerializer Tests
# =====================

class TestRunnerCreateUpdateSerializer:
    """Tests for RunnerCreateUpdateSerializer."""

    @pytest.mark.django_db
    def test_create_runner_without_steps(self):
        """create should create runner without steps."""
        app = Application.objects.create(reference='APP_CREATE', name='Create App')
        
        data = {
            'reference': 'NEW_RUNNER',
            'name': 'New Runner',
            'application': app.id,
            'stop_on_error': True,
            'verbose_logging': False,
            'is_active': True
        }
        
        serializer = RunnerCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        
        runner = serializer.save()
        
        assert runner.reference == 'NEW_RUNNER'
        assert runner.stop_on_error is True
        assert runner.runnerstep_set.count() == 0

    @pytest.mark.django_db
    def test_create_runner_with_steps(self):
        """create should create runner with steps."""
        app = Application.objects.create(reference='APP_CREATE2', name='Create App 2')
        script = SqlScript.objects.create(
            reference='STEP_SCRIPT',
            name='Step Script',
            script_type='PRE',
            content='SELECT 1',
            application=app
        )
        
        data = {
            'reference': 'NEW_RUNNER2',
            'name': 'New Runner 2',
            'application': app.id,
            'steps': [
                {'script': script.id, 'order': 1, 'step_type': 'PRE'}
            ],
            'is_active': True
        }
        
        serializer = RunnerCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        
        runner = serializer.save()
        
        assert runner.runnerstep_set.count() == 1
        assert runner.runnerstep_set.first().order == 1

    @pytest.mark.django_db
    def test_update_runner_replaces_steps(self):
        """update should replace all existing steps when steps provided."""
        app = Application.objects.create(reference='APP_UPDATE', name='Update App')
        runner = Runner.objects.create(reference='UPDATE_RUNNER', name='Update Runner', application=app)
        script1 = SqlScript.objects.create(
            reference='OLD_SCRIPT',
            name='Old Script',
            script_type='PRE',
            content='SELECT 1',
            application=app
        )
        script2 = SqlScript.objects.create(
            reference='NEW_SCRIPT',
            name='New Script',
            script_type='POST',
            content='SELECT 2',
            application=app
        )
        
        # Create initial step
        RunnerStep.objects.create(runner=runner, script=script1, order=1, step_type='PRE')
        
        data = {
            'reference': 'UPDATE_RUNNER',
            'name': 'Updated Runner',
            'application': app.id,
            'steps': [
                {'script': script2.id, 'order': 1, 'step_type': 'POST'}
            ]
        }
        
        serializer = RunnerCreateUpdateSerializer(instance=runner, data=data)
        assert serializer.is_valid(), serializer.errors
        
        updated_runner = serializer.save()
        
        assert updated_runner.runnerstep_set.count() == 1
        assert updated_runner.runnerstep_set.first().script == script2

    @pytest.mark.django_db
    def test_update_runner_preserves_steps_when_not_provided(self):
        """update should preserve existing steps when steps not in data."""
        app = Application.objects.create(reference='APP_PRESERVE', name='Preserve App')
        runner = Runner.objects.create(reference='PRESERVE_RUNNER', name='Preserve Runner', application=app)
        script = SqlScript.objects.create(
            reference='PRESERVE_SCRIPT',
            name='Preserve Script',
            script_type='PRE',
            content='SELECT 1',
            application=app
        )
        RunnerStep.objects.create(runner=runner, script=script, order=1, step_type='PRE')
        
        data = {
            'reference': 'PRESERVE_RUNNER',
            'name': 'Updated Name Only',
            'application': app.id
            # No 'steps' key
        }
        
        serializer = RunnerCreateUpdateSerializer(instance=runner, data=data)
        assert serializer.is_valid(), serializer.errors
        
        updated_runner = serializer.save()
        
        assert updated_runner.name == 'Updated Name Only'
        assert updated_runner.runnerstep_set.count() == 1

    @pytest.mark.django_db
    def test_validate_reference_duplicate_on_create(self):
        """validate_reference should reject duplicate on create."""
        app = Application.objects.create(reference='APP_DUP', name='Dup App')
        Runner.objects.create(reference='DUP_REF', name='Dup Runner', application=app)
        
        serializer = RunnerCreateUpdateSerializer()
        
        with pytest.raises(drf_serializers.ValidationError):
            serializer.validate_reference('DUP_REF')


# =====================
# ExecutionLogSerializer Additional Tests
# =====================

class TestExecutionLogSerializerAdditional:
    """Additional tests for ExecutionLogSerializer."""

    @pytest.mark.django_db
    def test_runner_name_display(self, user):
        """ExecutionLogSerializer should display runner_name correctly."""
        app = Application.objects.create(reference='APP_LOG', name='Log App')
        runner = Runner.objects.create(reference='LOG_RUNNER', name='Log Runner', application=app)
        log = ExecutionLog.objects.create(runner=runner, status='SUCCESS', executed_by=user)
        
        serializer = ExecutionLogSerializer(log)
        data = serializer.data
        
        assert data['runner_name'] == 'Log Runner'

    @pytest.mark.django_db
    def test_script_name_display(self, user):
        """ExecutionLogSerializer should display script_name correctly."""
        app = Application.objects.create(reference='APP_LOG2', name='Log App 2')
        script = SqlScript.objects.create(
            reference='LOG_SCRIPT',
            name='Log Script',
            script_type='UTIL',
            content='SELECT 1',
            application=app
        )
        log = ExecutionLog.objects.create(script=script, status='SUCCESS', executed_by=user)
        
        serializer = ExecutionLogSerializer(log)
        data = serializer.data
        
        assert data['script_name'] == 'Log Script'

    @pytest.mark.django_db
    def test_executed_by_name_display(self, user):
        """ExecutionLogSerializer should display executed_by_name correctly."""
        log = ExecutionLog.objects.create(status='SUCCESS', executed_by=user)
        
        serializer = ExecutionLogSerializer(log)
        data = serializer.data
        
        assert data['executed_by_name'] == 'serializer_user'

    @pytest.mark.django_db
    def test_null_runner_and_script(self, user):
        """ExecutionLogSerializer should handle null runner and script."""
        log = ExecutionLog.objects.create(status='SUCCESS', executed_by=user)
        
        serializer = ExecutionLogSerializer(log)
        data = serializer.data
        
        assert data['runner_name'] is None
        assert data['script_name'] is None

    @pytest.mark.django_db
    def test_all_fields_are_read_only(self):
        """ExecutionLogSerializer should have all fields as read-only."""
        expected_read_only = [
            'id', 'runner', 'runner_name', 'script', 'script_name',
            'status', 'status_display', 'logs', 'error_message',
            'started_at', 'ended_at', 'duration_ms', 'duration_seconds',
            'executed_by', 'executed_by_name', 'variables_used', 'is_completed'
        ]
        assert ExecutionLogSerializer.Meta.read_only_fields == expected_read_only

    @pytest.mark.django_db
    def test_variables_used_serialization(self, user):
        """ExecutionLogSerializer should serialize variables_used correctly."""
        log = ExecutionLog.objects.create(
            status='SUCCESS',
            executed_by=user,
            variables_used={'key1': 'value1', 'key2': 123}
        )
        
        serializer = ExecutionLogSerializer(log)
        data = serializer.data
        
        assert data['variables_used'] == {'key1': 'value1', 'key2': 123}


# =====================
# Summary of covered cases
# =====================
# - TypeSerializer:
#   - Serializes all fields correctly
#   - Read-only fields not writable
#   - Meta.fields list is complete
#
# - EntityListSerializer:
#   - Nested field forme_juridique_name
#   - Nested field type_entite_name
#   - Nested field parent_name
#   - Nested field created_by_name
#   - Null nested fields handling
#
# - EntityDetailSerializer:
#   - Includes additional fields (address_postal, numero_dpo)
#   - Read-only fields configuration
#
# - DataSourceListSerializer:
#   - sgbd_name_display
#   - created_by_name
#
# - DataSourceDetailSerializer:
#   - Security fields (TLS, X509)
#   - Write-only fields not in output
#
# - DataSourceCreateUpdateSerializer:
#   - Includes password fields
#   - Password fields are write-only
#
# - ApplicationDetailSerializer:
#   - Nested entities serialization
#   - Nested datasources serialization
#   - type1_name display
#
# - ApplicationCreateUpdateSerializer:
#   - Fields list
#   - Read-only fields
#
# - SqlScriptListSerializer:
#   - application_name display
#   - datasource_name display
#   - Null datasource handling
#
# - SqlScriptDetailSerializer (additional):
#   - validate_content valid success
#   - validate_content whitespace only invalid
#   - validate_content empty string invalid
#   - validate_reference unique on create
#   - validate_reference allows same on update
#
# - RunnerStepSerializer (additional):
#   - get_extracted_variables no script
#   - validate deleted script raises
#   - validate UTIL script type allowed
#   - validate matching step type allowed
#
# - RunnerStepNestedSerializer:
#   - Fields list
#
# - RunnerStepCreateSerializer:
#   - Fields list
#
# - RunnerListSerializer (additional):
#   - get_last_execution no logs
#   - get_last_execution with logs
#   - application_name display
#
# - RunnerDetailSerializer:
#   - get_pre_steps
#   - get_post_steps
#   - get_execution_plan
#   - validate_reference duplicate on create
#   - validate_reference allows same on update
#
# - RunnerCreateUpdateSerializer:
#   - create runner without steps
#   - create runner with steps
#   - update runner replaces steps
#   - update runner preserves steps when not provided
#   - validate_reference duplicate on create
#
# - ExecutionLogSerializer (additional):
#   - runner_name display
#   - script_name display
#   - executed_by_name display
#   - Null runner and script handling
#   - All fields are read-only
#   - variables_used serialization