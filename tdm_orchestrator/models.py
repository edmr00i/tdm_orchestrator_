"""
Modèles pour le module TDM SQL Orchestrator

Ce module permet de gérer des scripts SQL utilitaires et de les orchestrer
autour du processus d'anonymisation des données (TDM).
"""

from django.db import models, connection
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone

# Définition du manager après les imports
class TypeManager(models.Manager):
    pass

class Type(models.Model):
    reference = models.CharField(max_length=255, blank=True, null=True)
    value_format = models.CharField(max_length=50)
    value_char = models.CharField(max_length=255, blank=True, null=True)
    value_num = models.IntegerField(blank=True, null=True)
    value_date = models.DateTimeField(blank=True, null=True)
    type_list = models.CharField(max_length=255)
    source = models.CharField(max_length=30, default='client')
    lock = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(db_column="creation_date", auto_now_add=True)
    update_at = models.DateTimeField(db_column="modification_date", auto_now=True)
    extern_ref_admin_lov = models.BigIntegerField(blank=True, null=True, default=None)
    objects = TypeManager()

    def get_translated_field_value(self, field_name):
        value = self.__dict__[field_name]
        return value

    def find_by_value_char(self, value_char):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM yourapp_typetable
                WHERE value_char = %s AND is_active = %s AND is_deleted = %s
            """, [value_char, True, False])
            result = cursor.fetchall()
            types = []
            for row in result:
                types.append(self.__class__(*row))
            return types

    @property
    def value_char_translated(self):
        return self.get_translated_field_value('value_char')

    def __str__(self):
        return self.value_char or str(self.pk)

# Nouveau modèle Entity
class Entity(models.Model):
    reference = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=255)
    siret = models.CharField(max_length=255, null=True, blank=True)
    sigle = models.CharField(max_length=255, null=True, blank=True)
    dpo = models.CharField(max_length=255, null=True, blank=True)
    forme_juridique = models.ForeignKey(
        Type,
        related_name='forme_juridique',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    address_postal = models.CharField(max_length=255, null=True, blank=True)
    numero_dpo = models.CharField(max_length=255, null=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    type_entite = models.ForeignKey(
        Type,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(
        db_column="creation_date",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        db_column="modification_date",
        auto_now=True
    )
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        null=True
    )
    def __str__(self):
        return self.name

# =====================
# DataSource et Application
# =====================
class DataSource(models.Model):
    reference = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    sgbd_name = models.ForeignKey(Type, related_name='sgbd', on_delete=models.PROTECT)
    sgbd_password = models.TextField(blank=True, null=True)
    priv_key = models.TextField(blank=True, null=True)
    sgbd_host = models.CharField(max_length=255)
    sgbd_user = models.CharField(max_length=255, null=True, blank=True)
    sgbd_port = models.IntegerField(null=True, blank=True)
    sgbd_driver = models.CharField(max_length=255, null=True, blank=True)
    sgbd_sid = models.CharField(max_length=255, null=True, blank=True)
    sgbd_database = models.CharField(max_length=255, null=True, blank=True)
    sgbd_tls = models.BooleanField(default=False)
    sgbd_x509 = models.BooleanField(default=False)
    sgbd_ca_file = models.TextField(blank=True, null=True)
    sgbd_certificate_key_file = models.TextField(blank=True, null=True)
    sgbd_certificate_file = models.TextField(blank=True, null=True)
    sgbd_certificate_key_file_password = models.CharField(max_length=256, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(db_column="creation_date", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="modification_date", auto_now=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, null=True)
    def __str__(self):
        return self.name

class Application(models.Model):
    reference = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    type1 = models.ForeignKey(Type, on_delete=models.PROTECT, blank=True, null=True)
    type2 = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(null=True)
    mac_address = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.CharField(max_length=255, blank=True, null=True)
    entity = models.ManyToManyField(Entity, related_name='application_entity')
    data_sources = models.ManyToManyField('DataSource', related_name='application_datasource', blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(db_column="creation_date", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="modification_date", auto_now=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, null=True)
    def __str__(self):
        return self.name
# =====================
# Script SQL
# =====================
class SqlScript(models.Model):
    """
    Modèle représentant un script SQL unitaire.
    
    Un script peut être de type :
    - PRE : Pré-traitement (désactivation FK, nettoyage logs, etc.)
    - POST : Post-traitement (reconstruction index, réactivation FK, etc.)
    - UTIL : Utilitaire (script générique réutilisable)
    """
    
    SCRIPT_TYPES = [
        ('PRE', 'Pre-Processing'),
        ('POST', 'Post-Processing'),
        ('UTIL', 'Utility'),
    ]
    
    # Champs principaux
    reference = models.CharField(max_length=100, unique=True, help_text="Référence unique du script")
    name = models.CharField(max_length=255, help_text="Nom du script")
    description = models.TextField(blank=True, null=True, help_text="Description détaillée du script")
    
    # Relations
    application = models.ForeignKey(
        'Application',
        on_delete=models.PROTECT,
        related_name='sql_scripts',
        help_text="Application cible"
    )
    datasource = models.ForeignKey(
        'DataSource',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='sql_scripts',
        help_text="Source de données sur laquelle le script sera exécuté"
    )
    
    # Caractéristiques du script
    script_type = models.CharField(
        max_length=10,
        choices=SCRIPT_TYPES,
        help_text="Type de script (Pre-Processing, Post-Processing ou Utility)"
    )
    content = models.TextField(help_text="Contenu SQL brut du script (supporte les variables ${VAR})")
    
    # Métadonnées standards
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(db_column="creation_date", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="modification_date", auto_now=True)
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_sql_scripts'
    )
    
    class Meta:
        db_table = 'tdm_sql_script'
        ordering = ['-created_at']
        verbose_name = 'Script SQL'
        verbose_name_plural = 'Scripts SQL'
        indexes = [
            models.Index(fields=['script_type', 'is_active', 'is_deleted']),
            models.Index(fields=['application', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_script_type_display()})"
    
    def get_parsed_content(self, variables_dict=None):
        """
        Retourne le contenu SQL avec les variables remplacées.
        
        Args:
            variables_dict (dict): Dictionnaire des variables {nom: valeur}
            
        Returns:
            str: Contenu SQL avec variables substituées
            
        Example:
            >>> script.content = "SELECT * FROM ${SCHEMA}.users"
            >>> script.get_parsed_content({'SCHEMA': 'production'})
            "SELECT * FROM production.users"
        """
        if not variables_dict:
            return self.content
        
        parsed_content = self.content
        for var_name, var_value in variables_dict.items():
            placeholder = f"${{{var_name}}}"
            parsed_content = parsed_content.replace(placeholder, str(var_value))
        
        return parsed_content
    
    def extract_variables(self):
        """
        Extrait la liste des variables présentes dans le contenu SQL.
        
        Returns:
            list: Liste des noms de variables (sans ${})
            
        Example:
            >>> script.content = "DROP TABLE ${SCHEMA}.${TABLE}"
            >>> script.extract_variables()
            ['SCHEMA', 'TABLE']
        """
        import re
        pattern = r'\$\{([A-Za-z0-9_]+)\}'
        variables = re.findall(pattern, self.content)
        return list(set(variables))  # Dédoublonner


# =====================
# Runner (Orchestrateur)
# =====================
class Runner(models.Model):
    """
    Modèle représentant un orchestrateur de scripts SQL.
    
    Un Runner définit un scénario complet d'exécution avec :
    - Des scripts en pré-traitement
    - Le processus d'anonymisation (géré ailleurs)
    - Des scripts en post-traitement
    """
    
    # Champs principaux
    reference = models.CharField(max_length=100, unique=True, help_text="Référence unique du runner")
    name = models.CharField(max_length=255, help_text="Nom du runner")
    description = models.TextField(blank=True, null=True, help_text="Description du scénario")
    
    # Relations
    application = models.ForeignKey(
        'Application',
        on_delete=models.PROTECT,
        related_name='runners',
        help_text="Application cible"
    )
    
    # Configuration
    stop_on_error = models.BooleanField(
        default=True,
        help_text="Arrêter l'exécution au premier échec ou continuer (best effort)"
    )
    verbose_logging = models.BooleanField(
        default=False,
        help_text="Activer les logs détaillés"
    )
    
    # Relation Many-to-Many vers SqlScript via table intermédiaire
    scripts = models.ManyToManyField(
        SqlScript,
        through='RunnerStep',
        related_name='runners',
        help_text="Scripts SQL associés à ce runner"
    )
    
    # Métadonnées standards
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(db_column="creation_date", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="modification_date", auto_now=True)
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_runners'
    )
    
    class Meta:
        db_table = 'tdm_runner'
        ordering = ['-created_at']
        verbose_name = 'Runner'
        verbose_name_plural = 'Runners'
        indexes = [
            models.Index(fields=['application', 'is_active', 'is_deleted']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.application.name}"
    
    def get_pre_scripts(self):
        """
        Retourne les scripts de pré-traitement ordonnés.
        
        Returns:
            QuerySet: Scripts de type PRE ordonnés
        """
        return self.runnerstep_set.filter(
            step_type='PRE',
            script__is_active=True,
            script__is_deleted=False
        ).select_related('script').order_by('order')
    
    def get_post_scripts(self):
        """
        Retourne les scripts de post-traitement ordonnés.
        
        Returns:
            QuerySet: Scripts de type POST ordonnés
        """
        return self.runnerstep_set.filter(
            step_type='POST',
            script__is_active=True,
            script__is_deleted=False
        ).select_related('script').order_by('order')
    
    def get_execution_plan(self):
        """
        Retourne le plan d'exécution complet du runner.
        
        Returns:
            dict: Plan d'exécution structuré
            
        Example:
            {
                'runner_name': 'Refresh Mensuel CRM',
                'application': 'CRM Core',
                'stop_on_error': True,
                'pre_scripts': [
                    {'order': 1, 'name': 'Disable_FK', 'script_id': 1},
                    {'order': 2, 'name': 'Clean_Logs', 'script_id': 2}
                ],
                'anonymization': 'TDM Engine (handled separately)',
                'post_scripts': [
                    {'order': 1, 'name': 'Rebuild_Index', 'script_id': 3}
                ]
            }
        """
        plan = {
            'runner_name': self.name,
            'application': self.application.name,
            'stop_on_error': self.stop_on_error,
            'verbose_logging': self.verbose_logging,
            'pre_scripts': [],
            'anonymization': 'TDM Engine (handled separately)',
            'post_scripts': []
        }
        
        for step in self.get_pre_scripts():
            plan['pre_scripts'].append({
                'order': step.order,
                'name': step.script.name,
                'script_id': step.script.id,
                'datasource': step.script.datasource.name if step.script.datasource else None
            })
        
        for step in self.get_post_scripts():
            plan['post_scripts'].append({
                'order': step.order,
                'name': step.script.name,
                'script_id': step.script.id,
                'datasource': step.script.datasource.name if step.script.datasource else None
            })
        
        return plan
    
    def get_total_steps(self):
        """Retourne le nombre total d'étapes (PRE + POST)."""
        return self.runnerstep_set.filter(
            script__is_active=True,
            script__is_deleted=False
        ).count()


# =====================
# RunnerStep (Table de liaison)
# =====================
class RunnerStep(models.Model):
    """
    Table de liaison entre Runner et SqlScript.
    
    Gère l'ordre d'exécution et le type d'étape (PRE ou POST).
    """
    
    STEP_TYPES = [
        ('PRE', 'Pre-Process'),
        ('POST', 'Post-Process'),
    ]
    
    # Relations
    runner = models.ForeignKey(
        Runner,
        on_delete=models.CASCADE,
        help_text="Runner parent"
    )
    script = models.ForeignKey(
        SqlScript,
        on_delete=models.PROTECT,
        help_text="Script SQL à exécuter"
    )
    
    # Configuration de l'étape
    order = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Ordre d'exécution dans la séquence (1, 2, 3...)"
    )
    step_type = models.CharField(
        max_length=10,
        choices=STEP_TYPES,
        help_text="Type d'étape (Pre-Process ou Post-Process)"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(db_column="creation_date", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="modification_date", auto_now=True)
    
    class Meta:
        db_table = 'tdm_runner_step'
        ordering = ['step_type', 'order']
        verbose_name = 'Étape de Runner'
        verbose_name_plural = 'Étapes de Runner'
        unique_together = [
            ['runner', 'step_type', 'order']  # Un ordre unique par type dans un runner
        ]
        indexes = [
            models.Index(fields=['runner', 'step_type', 'order']),
        ]
    
    def __str__(self):
        return f"{self.runner.name} - {self.step_type} #{self.order}: {self.script.name}"
    
    def clean(self):
        """
        Validation personnalisée.
        
        Vérifie que le script est bien actif et du bon type si applicable.
        """
        from django.core.exceptions import ValidationError
        
        # Vérifier que le script est actif
        if self.script and (not self.script.is_active or self.script.is_deleted):
            raise ValidationError("Le script sélectionné n'est pas actif.")
        
        # Optionnel : Vérifier cohérence entre step_type et script_type
        # (Un script UTIL peut être utilisé partout)
        if self.script and self.script.script_type not in ['UTIL', self.step_type]:
            raise ValidationError(
                f"Le script est de type {self.script.script_type} "
                f"mais l'étape est de type {self.step_type}"
            )


# =====================
# ExecutionLog (Historique)
# =====================
class ExecutionLog(models.Model):
    """
    Modèle pour stocker l'historique des exécutions.
    
    Permet de tracer toutes les exécutions de scripts (unitaires ou via runner).
    """
    
    STATUS_CHOICES = [
        ('RUNNING', 'En cours'),
        ('SUCCESS', 'Succès'),
        ('FAILURE', 'Échec'),
        ('CANCELLED', 'Annulé'),
    ]
    
    # Relations (optionnelles car peut être script unitaire OU runner)
    runner = models.ForeignKey(
        Runner,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='execution_logs',
        help_text="Runner exécuté (si applicable)"
    )
    script = models.ForeignKey(
        SqlScript,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='execution_logs',
        help_text="Script exécuté (peut être NULL si exécution de runner complet)"
    )
    
    # Informations d'exécution
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='RUNNING',
        help_text="Statut de l'exécution"
    )
    logs = models.TextField(
        blank=True,
        null=True,
        help_text="Logs de console (stdout)"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Message d'erreur en cas d'échec"
    )
    
    # Métriques
    started_at = models.DateTimeField(db_column="start_date", auto_now_add=True)
    ended_at = models.DateTimeField(db_column="end_date", null=True, blank=True)
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Durée d'exécution en millisecondes"
    )
    
    # Contexte d'exécution
    executed_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='sql_executions',
        help_text="Utilisateur ayant lancé l'exécution"
    )
    variables_used = models.JSONField(
        null=True,
        blank=True,
        help_text="Variables utilisées lors de l'exécution (format JSON)"
    )
    
    class Meta:
        db_table = 'tdm_execution_log'
        ordering = ['-started_at']
        verbose_name = 'Log d\'exécution'
        verbose_name_plural = 'Logs d\'exécution'
        indexes = [
            models.Index(fields=['-started_at']),
            models.Index(fields=['status', '-started_at']),
            models.Index(fields=['runner', '-started_at']),
            models.Index(fields=['script', '-started_at']),
        ]
    
    def __str__(self):
        target = self.runner.name if self.runner else (self.script.name if self.script else 'Unknown')
        return f"{target} - {self.status} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"
    
    def mark_success(self, logs_output=''):
        """
        Marque l'exécution comme réussie.
        
        Args:
            logs_output (str): Logs de sortie
        """
        self.status = 'SUCCESS'
        self.ended_at = timezone.now()
        self.logs = logs_output
        
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)
        
        self.save()
    
    def mark_failure(self, error_msg, logs_output=''):
        """
        Marque l'exécution comme échouée.
        
        Args:
            error_msg (str): Message d'erreur
            logs_output (str): Logs de sortie
        """
        self.status = 'FAILURE'
        self.ended_at = timezone.now()
        self.error_message = error_msg
        self.logs = logs_output
        
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)
        
        self.save()
    
    def mark_cancelled(self):
        """Marque l'exécution comme annulée."""
        self.status = 'CANCELLED'
        self.ended_at = timezone.now()
        
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)
        
        self.save()
    
    @property
    def duration_seconds(self):
        """Retourne la durée en secondes (format lisible)."""
        if self.duration_ms:
            return round(self.duration_ms / 1000, 2)
        return None
    
    @property
    def is_completed(self):
        """Vérifie si l'exécution est terminée (succès ou échec)."""
        return self.status in ['SUCCESS', 'FAILURE', 'CANCELLED']