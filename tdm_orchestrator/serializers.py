"""
Serializers pour les APIs REST du module TDM SQL Orchestrator.
"""

from rest_framework import serializers
from .models import (
    Type,
    Entity,
    DataSource,
    Application,
    SqlScript,
    Runner,
    RunnerStep,
    ExecutionLog,
)


# =====================
# Type Serializers
# =====================
class TypeSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Type."""
    
    class Meta:
        model = Type
        fields = [
            'id',
            'reference',
            'value_format',
            'value_char',
            'value_num',
            'value_date',
            'type_list',
            'source',
            'lock',
            'is_active',
            'is_deleted',
            'created_at',
            'update_at',
            'extern_ref_admin_lov',
        ]
        read_only_fields = ['id', 'created_at', 'update_at']


# =====================
# Entity Serializers
# =====================
class EntityListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des entités."""
    
    forme_juridique_name = serializers.CharField(source='forme_juridique.value_char', read_only=True, allow_null=True)
    type_entite_name = serializers.CharField(source='type_entite.value_char', read_only=True, allow_null=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = Entity
        fields = [
            'id',
            'reference',
            'name',
            'siret',
            'sigle',
            'dpo',
            'forme_juridique',
            'forme_juridique_name',
            'type_entite',
            'type_entite_name',
            'parent',
            'parent_name',
            'is_active',
            'created_at',
            'updated_at',
            'created_by_name',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EntityDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une entité."""
    
    forme_juridique_name = serializers.CharField(source='forme_juridique.value_char', read_only=True, allow_null=True)
    type_entite_name = serializers.CharField(source='type_entite.value_char', read_only=True, allow_null=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = Entity
        fields = [
            'id',
            'reference',
            'name',
            'siret',
            'sigle',
            'dpo',
            'forme_juridique',
            'forme_juridique_name',
            'address_postal',
            'numero_dpo',
            'parent',
            'parent_name',
            'type_entite',
            'type_entite_name',
            'is_active',
            'is_deleted',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_name',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


# =====================
# DataSource Serializers
# =====================
class DataSourceListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des sources de données."""
    
    sgbd_name_display = serializers.CharField(source='sgbd_name.value_char', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = DataSource
        fields = [
            'id',
            'reference',
            'name',
            'sgbd_name',
            'sgbd_name_display',
            'sgbd_host',
            'sgbd_port',
            'sgbd_database',
            'sgbd_tls',
            'is_active',
            'created_at',
            'updated_at',
            'created_by_name',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DataSourceDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une source de données."""
    
    sgbd_name_display = serializers.CharField(source='sgbd_name.value_char', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = DataSource
        fields = [
            'id',
            'reference',
            'name',
            'sgbd_name',
            'sgbd_name_display',
            'sgbd_host',
            'sgbd_user',
            'sgbd_port',
            'sgbd_driver',
            'sgbd_sid',
            'sgbd_database',
            'sgbd_tls',
            'sgbd_x509',
            'sgbd_ca_file',
            'sgbd_certificate_key_file',
            'sgbd_certificate_file',
            'is_active',
            'is_deleted',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_name',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
        extra_kwargs = {
            'sgbd_password': {'write_only': True},
            'priv_key': {'write_only': True},
            'sgbd_certificate_key_file_password': {'write_only': True},
        }


class DataSourceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la création/modification d'une source de données."""
    
    class Meta:
        model = DataSource
        fields = [
            'id',
            'reference',
            'name',
            'sgbd_name',
            'sgbd_password',
            'priv_key',
            'sgbd_host',
            'sgbd_user',
            'sgbd_port',
            'sgbd_driver',
            'sgbd_sid',
            'sgbd_database',
            'sgbd_tls',
            'sgbd_x509',
            'sgbd_ca_file',
            'sgbd_certificate_key_file',
            'sgbd_certificate_file',
            'sgbd_certificate_key_file_password',
            'is_active',
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'sgbd_password': {'write_only': True},
            'priv_key': {'write_only': True},
            'sgbd_certificate_key_file_password': {'write_only': True},
        }


# =====================
# Application Serializers
# =====================
class ApplicationListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des applications."""
    
    type1_name = serializers.CharField(source='type1.value_char', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    entity_count = serializers.SerializerMethodField()
    datasource_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Application
        fields = [
            'id',
            'reference',
            'name',
            'type1',
            'type1_name',
            'type2',
            'description',
            'ip_address',
            'entity_count',
            'datasource_count',
            'is_active',
            'created_at',
            'updated_at',
            'created_by_name',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_entity_count(self, obj):
        return obj.entity.count()
    
    def get_datasource_count(self, obj):
        return obj.data_sources.count()


class ApplicationDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une application."""
    
    type1_name = serializers.CharField(source='type1.value_char', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    entities = EntityListSerializer(source='entity', many=True, read_only=True)
    datasources = DataSourceListSerializer(source='data_sources', many=True, read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id',
            'reference',
            'name',
            'type1',
            'type1_name',
            'type2',
            'address',
            'description',
            'mac_address',
            'ip_address',
            'entity',
            'entities',
            'data_sources',
            'datasources',
            'is_active',
            'is_deleted',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_name',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class ApplicationCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la création/modification d'une application."""
    
    class Meta:
        model = Application
        fields = [
            'id',
            'reference',
            'name',
            'type1',
            'type2',
            'address',
            'description',
            'mac_address',
            'ip_address',
            'entity',
            'data_sources',
            'is_active',
        ]
        read_only_fields = ['id']


# =====================
# SqlScript Serializers
# =====================
class SqlScriptListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des scripts (vue simplifiée)."""
    
    application_name = serializers.CharField(source='application.name', read_only=True)
    datasource_name = serializers.CharField(source='datasource.name', read_only=True, allow_null=True)
    script_type_display = serializers.CharField(source='get_script_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = SqlScript
        fields = [
            'id',
            'reference',
            'name',
            'description',
            'application',
            'application_name',
            'datasource',
            'datasource_name',
            'script_type',
            'script_type_display',
            'is_active',
            'created_at',
            'updated_at',
            'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SqlScriptDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un script (inclut le contenu SQL)."""
    
    application_name = serializers.CharField(source='application.name', read_only=True)
    datasource_name = serializers.CharField(source='datasource.name', read_only=True, allow_null=True)
    script_type_display = serializers.CharField(source='get_script_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    extracted_variables = serializers.SerializerMethodField()
    
    class Meta:
        model = SqlScript
        fields = [
            'id',
            'reference',
            'name',
            'description',
            'application',
            'application_name',
            'datasource',
            'datasource_name',
            'script_type',
            'script_type_display',
            'content',
            'extracted_variables',
            'is_active',
            'is_deleted',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_extracted_variables(self, obj):
        """Extrait les variables du contenu SQL."""
        return obj.extract_variables()
    
    def validate_content(self, value):
        """Validation du contenu SQL."""
        if not value or not value.strip():
            raise serializers.ValidationError("Le contenu SQL ne peut pas être vide.")
        return value
    
    def validate_reference(self, value):
        """Validation de la référence unique."""
        if self.instance:  # Update
            if SqlScript.objects.exclude(id=self.instance.id).filter(reference=value).exists():
                raise serializers.ValidationError(f"La référence '{value}' existe déjà.")
        else:  # Create
            if SqlScript.objects.filter(reference=value).exists():
                raise serializers.ValidationError(f"La référence '{value}' existe déjà.")
        return value


# =====================
# RunnerStep Serializers
# =====================
class RunnerStepSerializer(serializers.ModelSerializer):
    """Serializer pour les étapes d'un runner."""
    
    script_name = serializers.CharField(source='script.name', read_only=True)
    script_reference = serializers.CharField(source='script.reference', read_only=True)
    script_type = serializers.CharField(source='script.script_type', read_only=True)
    script_content = serializers.CharField(source='script.content', read_only=True)
    script_description = serializers.CharField(source='script.description', read_only=True, allow_null=True)
    datasource_name = serializers.CharField(source='script.datasource.name', read_only=True, allow_null=True)
    datasource_id = serializers.IntegerField(source='script.datasource.id', read_only=True, allow_null=True)
    step_type_display = serializers.CharField(source='get_step_type_display', read_only=True)
    extracted_variables = serializers.SerializerMethodField()
    
    class Meta:
        model = RunnerStep
        fields = [
            'id',
            'script',
            'script_name',
            'script_reference',
            'script_type',
            'script_description',
            'script_content',
            'extracted_variables',
            'datasource_id',
            'datasource_name',
            'order',
            'step_type',
            'step_type_display'
        ]
    
    def get_extracted_variables(self, obj):
        """Extrait les variables du script."""
        if obj.script:
            return obj.script.extract_variables()
        return []
    
    def validate(self, attrs):
        """Validation personnalisée."""
        # Vérifier que le script est actif
        script = attrs.get('script')
        if script and (not script.is_active or script.is_deleted):
            raise serializers.ValidationError({
                'script': "Le script sélectionné n'est pas actif."
            })
        
        # Vérifier la cohérence entre step_type et script_type
        step_type = attrs.get('step_type')
        if script and script.script_type not in ['UTIL', step_type]:
            raise serializers.ValidationError({
                'script': f"Le script est de type {script.script_type} mais l'étape est de type {step_type}."
            })
        
        return attrs


class RunnerStepNestedSerializer(serializers.ModelSerializer):
    """Serializer nested complet pour les étapes avec script inclus."""
    
    script = SqlScriptDetailSerializer(read_only=True)
    step_type_display = serializers.CharField(source='get_step_type_display', read_only=True)
    
    class Meta:
        model = RunnerStep
        fields = [
            'id',
            'script',
            'order',
            'step_type',
            'step_type_display'
        ]


class RunnerStepCreateSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la création d'étapes (nested dans Runner)."""
    
    class Meta:
        model = RunnerStep
        fields = ['script', 'order', 'step_type']


# =====================
# Runner Serializers
# =====================
class RunnerListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des runners (vue simplifiée)."""
    
    application_name = serializers.CharField(source='application.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    total_steps = serializers.SerializerMethodField()
    last_execution = serializers.SerializerMethodField()
    
    class Meta:
        model = Runner
        fields = [
            'id',
            'reference',
            'name',
            'description',
            'application',
            'application_name',
            'stop_on_error',
            'verbose_logging',
            'total_steps',
            'last_execution',
            'is_active',
            'created_at',
            'updated_at',
            'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_steps(self, obj):
        """Retourne le nombre total d'étapes."""
        return obj.get_total_steps()
    
    def get_last_execution(self, obj):
        """Retourne les infos de la dernière exécution."""
        last_log = obj.execution_logs.order_by('-started_at').first()
        if last_log:
            return {
                'id': last_log.id,
                'status': last_log.status,
                'started_at': last_log.started_at,
                'duration_seconds': last_log.duration_seconds
            }
        return None


class RunnerDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un runner (inclut les steps)."""
    
    application_name = serializers.CharField(source='application.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    
    # Steps ordonnés
    pre_steps = serializers.SerializerMethodField()
    post_steps = serializers.SerializerMethodField()
    
    # Statistiques
    total_steps = serializers.SerializerMethodField()
    execution_plan = serializers.SerializerMethodField()
    
    class Meta:
        model = Runner
        fields = [
            'id',
            'reference',
            'name',
            'description',
            'application',
            'application_name',
            'stop_on_error',
            'verbose_logging',
            'pre_steps',
            'post_steps',
            'total_steps',
            'execution_plan',
            'is_active',
            'is_deleted',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_pre_steps(self, obj):
        """Retourne les steps PRE."""
        steps = obj.get_pre_scripts()
        return RunnerStepSerializer(steps, many=True).data
    
    def get_post_steps(self, obj):
        """Retourne les steps POST."""
        steps = obj.get_post_scripts()
        return RunnerStepSerializer(steps, many=True).data
    
    def get_total_steps(self, obj):
        """Retourne le nombre total d'étapes."""
        return obj.get_total_steps()
    
    def get_execution_plan(self, obj):
        """Retourne le plan d'exécution complet."""
        return obj.get_execution_plan()
    
    def validate_reference(self, value):
        """Validation de la référence unique."""
        if self.instance:  # Update
            if Runner.objects.exclude(id=self.instance.id).filter(reference=value).exists():
                raise serializers.ValidationError(f"La référence '{value}' existe déjà.")
        else:  # Create
            if Runner.objects.filter(reference=value).exists():
                raise serializers.ValidationError(f"La référence '{value}' existe déjà.")
        return value


class RunnerCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la création/modification d'un runner avec steps."""
    
    steps = RunnerStepCreateSerializer(many=True, required=False)
    
    class Meta:
        model = Runner
        fields = [
            'id',
            'reference',
            'name',
            'description',
            'application',
            'stop_on_error',
            'verbose_logging',
            'steps',
            'is_active'
        ]
        read_only_fields = ['id']
    
    def validate_reference(self, value):
        """Validation de la référence unique."""
        if self.instance:  # Update
            if Runner.objects.exclude(id=self.instance.id).filter(reference=value).exists():
                raise serializers.ValidationError(f"La référence '{value}' existe déjà.")
        else:  # Create
            if Runner.objects.filter(reference=value).exists():
                raise serializers.ValidationError(f"La référence '{value}' existe déjà.")
        return value
    
    def create(self, validated_data):
        """Création d'un runner avec ses steps."""
        steps_data = validated_data.pop('steps', [])
        
        # Créer le runner
        runner = Runner.objects.create(**validated_data)
        
        # Créer les steps
        for step_data in steps_data:
            RunnerStep.objects.create(runner=runner, **step_data)
        
        return runner
    
    def update(self, instance, validated_data):
        """Mise à jour d'un runner avec ses steps."""
        steps_data = validated_data.pop('steps', None)
        
        # Mettre à jour les champs du runner
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Si des steps sont fournis, remplacer tous les steps existants
        if steps_data is not None:
            # Supprimer les anciens steps
            instance.runnerstep_set.all().delete()
            
            # Créer les nouveaux steps
            for step_data in steps_data:
                RunnerStep.objects.create(runner=instance, **step_data)
        
        return instance


# =====================
# ExecutionLog Serializers
# =====================
class ExecutionLogSerializer(serializers.ModelSerializer):
    """Serializer pour les logs d'exécution (read-only)."""
    
    runner_name = serializers.CharField(source='runner.name', read_only=True, allow_null=True)
    script_name = serializers.CharField(source='script.name', read_only=True, allow_null=True)
    executed_by_name = serializers.CharField(source='executed_by.username', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ExecutionLog
        fields = [
            'id',
            'runner',
            'runner_name',
            'script',
            'script_name',
            'status',
            'status_display',
            'logs',
            'error_message',
            'started_at',
            'ended_at',
            'duration_ms',
            'duration_seconds',
            'executed_by',
            'executed_by_name',
            'variables_used',
            'is_completed'
        ]
        # Tout est read-only — DRF attend une liste/tuple, pas une string
        read_only_fields = [
            'id',
            'runner',
            'runner_name',
            'script',
            'script_name',
            'status',
            'status_display',
            'logs',
            'error_message',
            'started_at',
            'ended_at',
            'duration_ms',
            'duration_seconds',
            'executed_by',
            'executed_by_name',
            'variables_used',
            'is_completed',
        ]