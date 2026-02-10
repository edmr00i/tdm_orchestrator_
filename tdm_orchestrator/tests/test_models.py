"""
Tests unitaires pour les modèles du module TDM SQL Orchestrator.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from ..models import Type, Application, DataSource, SqlScript, Runner, RunnerStep, ExecutionLog


class SqlScriptModelTest(TestCase):
    """Tests pour le modèle SqlScript."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Créer le type SGBD requis pour DataSource
        self.sgbd_type = Type.objects.create(
            reference='SGBD_POSTGRES',
            value_format='char',
            value_char='PostgreSQL',
            type_list='SGBD'
        )
        
        # Créer l'application requise
        self.application = Application.objects.create(
            reference='APP_TEST',
            name='Test Application'
        )
        
        # Créer la datasource
        self.datasource = DataSource.objects.create(
            reference='DS_TEST',
            name='Test DataSource',
            sgbd_name=self.sgbd_type,
            sgbd_host='localhost'
        )
    
    def test_create_sql_script(self):
        """Test de création d'un script SQL basique."""
        script = SqlScript.objects.create(
            reference='TEST_001',
            name='Test Script',
            description='Script de test',
            application=self.application,
            datasource=self.datasource,
            script_type='PRE',
            content='SELECT * FROM test',
            created_by=self.user
        )
        
        self.assertEqual(script.reference, 'TEST_001')
        self.assertEqual(script.name, 'Test Script')
        self.assertEqual(script.script_type, 'PRE')
        self.assertTrue(script.is_active)
        self.assertFalse(script.is_deleted)
    
    def test_extract_variables(self):
        """Test de l'extraction des variables du contenu SQL."""
        script = SqlScript(
            content='''
                SELECT * FROM ${SCHEMA}.users
                WHERE created_date > '${DATE_EXEC}'
                AND schema = '${SCHEMA}'
            '''
        )
        
        variables = script.extract_variables()
        
        # L'ordre peut varier, on utilise set pour comparer
        self.assertEqual(set(variables), {'SCHEMA', 'DATE_EXEC'})
    
    def test_extract_variables_no_variables(self):
        """Test quand il n'y a pas de variables."""
        script = SqlScript(
            content='SELECT * FROM users WHERE id = 1'
        )
        
        variables = script.extract_variables()
        self.assertEqual(variables, [])
    
    def test_get_parsed_content(self):
        """Test du remplacement des variables."""
        script = SqlScript(
            content='SELECT * FROM ${SCHEMA}.users WHERE date > ${DATE}'
        )
        
        parsed = script.get_parsed_content({
            'SCHEMA': 'production',
            'DATE': '2024-01-01'
        })
        
        expected = 'SELECT * FROM production.users WHERE date > 2024-01-01'
        self.assertEqual(parsed, expected)
    
    def test_get_parsed_content_no_variables(self):
        """Test sans dictionnaire de variables."""
        script = SqlScript(
            content='SELECT * FROM users'
        )
        
        parsed = script.get_parsed_content()
        self.assertEqual(parsed, script.content)
    
    def test_str_representation(self):
        """Test de la représentation string."""
        script = SqlScript(
            name='Test Script',
            script_type='PRE'
        )
        
        self.assertEqual(str(script), 'Test Script (Pre-Processing)')


class RunnerModelTest(TestCase):
    """Tests pour le modèle Runner."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Créer l'application requise
        self.application = Application.objects.create(
            reference='APP_TEST',
            name='Test Application'
        )
    
    def test_create_runner(self):
        """Test de création d'un runner basique."""
        runner = Runner.objects.create(
            reference='RUN_001',
            name='Test Runner',
            description='Runner de test',
            application=self.application,
            stop_on_error=True,
            verbose_logging=False,
            created_by=self.user
        )
        
        self.assertEqual(runner.reference, 'RUN_001')
        self.assertEqual(runner.name, 'Test Runner')
        self.assertTrue(runner.stop_on_error)
        self.assertFalse(runner.verbose_logging)
    
    def test_get_total_steps(self):
        """Test du comptage total des étapes."""
        # Note: Créer runner avec steps
        # runner = Runner.objects.create(...)
        # RunnerStep.objects.create(runner=runner, ...)
        # self.assertEqual(runner.get_total_steps(), expected_count)
        pass
    
    def test_get_execution_plan(self):
        """Test de la génération du plan d'exécution."""
        # Note: Créer runner avec plusieurs steps PRE et POST
        # plan = runner.get_execution_plan()
        # self.assertIn('pre_scripts', plan)
        # self.assertIn('post_scripts', plan)
        pass


class RunnerStepModelTest(TestCase):
    """Tests pour le modèle RunnerStep."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Note: Créer les objets nécessaires
        # self.runner = Runner.objects.create(...)
        # self.script = SqlScript.objects.create(...)
    
    def test_create_runner_step(self):
        """Test de création d'une étape."""
        # step = RunnerStep.objects.create(
        #     runner=self.runner,
        #     script=self.script,
        #     order=1,
        #     step_type='PRE'
        # )
        # self.assertEqual(step.order, 1)
        # self.assertEqual(step.step_type, 'PRE')
        pass
    
    def test_unique_order_per_type(self):
        """Test de l'unicité de l'ordre par type dans un runner."""
        # Créer deux steps avec même ordre et type devrait échouer
        pass
    
    def test_clean_validation_inactive_script(self):
        """Test de validation : script inactif."""
        # Créer un script inactif
        # Tenter de créer un step avec ce script
        # Devrait lever ValidationError
        pass


class ExecutionLogModelTest(TestCase):
    """Tests pour le modèle ExecutionLog."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_execution_log(self):
        """Test de création d'un log d'exécution."""
        log = ExecutionLog.objects.create(
            # runner ou script
            status='RUNNING',
            executed_by=self.user
        )
        
        self.assertEqual(log.status, 'RUNNING')
        self.assertIsNotNone(log.started_at)
        self.assertIsNone(log.ended_at)
    
    def test_mark_success(self):
        """Test de marquage d'une exécution réussie."""
        log = ExecutionLog.objects.create(
            status='RUNNING',
            executed_by=self.user
        )
        
        log.mark_success(logs_output='Execution completed successfully')
        
        self.assertEqual(log.status, 'SUCCESS')
        self.assertIsNotNone(log.ended_at)
        self.assertIsNotNone(log.duration_ms)
        self.assertEqual(log.logs, 'Execution completed successfully')
    
    def test_mark_failure(self):
        """Test de marquage d'une exécution échouée."""
        log = ExecutionLog.objects.create(
            status='RUNNING',
            executed_by=self.user
        )
        
        log.mark_failure(
            error_msg='SQL syntax error',
            logs_output='Error on line 5'
        )
        
        self.assertEqual(log.status, 'FAILURE')
        self.assertIsNotNone(log.ended_at)
        self.assertIsNotNone(log.duration_ms)
        self.assertEqual(log.error_message, 'SQL syntax error')
        self.assertEqual(log.logs, 'Error on line 5')
    
    def test_mark_cancelled(self):
        """Test de marquage d'une exécution annulée."""
        log = ExecutionLog.objects.create(
            status='RUNNING',
            executed_by=self.user
        )
        
        log.mark_cancelled()
        
        self.assertEqual(log.status, 'CANCELLED')
        self.assertIsNotNone(log.ended_at)
        self.assertIsNotNone(log.duration_ms)
    
    def test_duration_seconds_property(self):
        """Test de la propriété duration_seconds."""
        log = ExecutionLog.objects.create(
            status='RUNNING',
            executed_by=self.user
        )
        
        log.duration_ms = 5432  # 5.432 secondes
        
        self.assertEqual(log.duration_seconds, 5.43)
    
    def test_is_completed_property(self):
        """Test de la propriété is_completed."""
        log_running = ExecutionLog.objects.create(
            status='RUNNING',
            executed_by=self.user
        )
        
        log_success = ExecutionLog.objects.create(
            status='SUCCESS',
            executed_by=self.user
        )
        
        log_failure = ExecutionLog.objects.create(
            status='FAILURE',
            executed_by=self.user
        )
        
        self.assertFalse(log_running.is_completed)
        self.assertTrue(log_success.is_completed)
        self.assertTrue(log_failure.is_completed)


class ModelIntegrationTest(TestCase):
    """Tests d'intégration entre les modèles."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_full_runner_workflow(self):
        """
        Test du workflow complet :
        1. Créer des scripts
        2. Créer un runner
        3. Ajouter les scripts au runner
        4. Générer le plan d'exécution
        5. Créer un log d'exécution
        """
        # Note: À implémenter avec les fixtures complètes
        pass
    
    def test_cascade_deletion(self):
        """
        Test des comportements de suppression en cascade.
        """
        # Note: Vérifier que la suppression d'un runner supprime ses steps
        # Mais que la suppression d'un script est protégée si utilisé
        pass
