"""
Tests pour les APIs REST du module TDM SQL Orchestrator.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from ..models import SqlScript, Runner, RunnerStep, ExecutionLog

# Note: Vous devrez créer des fixtures pour Application et DataSource


class SqlScriptAPITest(TestCase):
    """Tests pour l'API SqlScript."""
    
    def setUp(self):
        """Configuration initiale."""
        self.client = APIClient()
        
        # Note: Créer Application et DataSource
        # self.application = Application.objects.create(...)
        # self.datasource = DataSource.objects.create(...)
    
    def test_list_scripts(self):
        """Test GET /api/scripts/"""
        url = reverse('script-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_script(self):
        """Test POST /api/scripts/"""
        url = reverse('script-list')
        
        data = {
            'reference': 'TEST_001',
            'name': 'Test Script',
            'description': 'Script de test',
            # 'application': self.application.id,
            # 'datasource': self.datasource.id,
            'script_type': 'PRE',
            'content': 'SELECT * FROM test'
        }
        
        # Note: Décommenter quand vous aurez les fixtures
        # response = self.client.post(url, data, format='json')
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # self.assertEqual(response.data['reference'], 'TEST_001')
    
    def test_get_script_detail(self):
        """Test GET /api/scripts/{id}/"""
        # Note: Créer un script et tester
        pass
    
    def test_update_script(self):
        """Test PUT /api/scripts/{id}/"""
        # Note: Créer un script et tester
        pass
    
    def test_delete_script(self):
        """Test DELETE /api/scripts/{id}/ (soft delete)"""
        # Note: Créer un script, le supprimer, vérifier is_deleted=True
        pass
    
    def test_extract_variables(self):
        """Test GET /api/scripts/{id}/variables/"""
        # Note: Créer un script avec variables et tester
        pass
    
    def test_parse_script(self):
        """Test POST /api/scripts/{id}/parse/"""
        # Note: Créer un script avec variables et tester le parsing
        pass


class RunnerAPITest(TestCase):
    """Tests pour l'API Runner."""
    
    def setUp(self):
        """Configuration initiale."""
        self.client = APIClient()
        
        # Note: Créer Application et DataSource
        # self.application = Application.objects.create(...)
    
    def test_list_runners(self):
        """Test GET /api/runners/"""
        url = reverse('runner-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_runner_with_steps(self):
        """Test POST /api/runners/ avec steps"""
        url = reverse('runner-list')
        
        # Note: Créer des scripts d'abord
        # script1 = SqlScript.objects.create(...)
        # script2 = SqlScript.objects.create(...)
        
        data = {
            'reference': 'RUN_001',
            'name': 'Test Runner',
            'description': 'Runner de test',
            # 'application': self.application.id,
            'stop_on_error': True,
            'verbose_logging': False,
            'steps': [
                # {'script': script1.id, 'order': 1, 'step_type': 'PRE'},
                # {'script': script2.id, 'order': 2, 'step_type': 'PRE'}
            ]
        }
        
        # Note: Décommenter quand vous aurez les fixtures
        # response = self.client.post(url, data, format='json')
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_get_runner_detail(self):
        """Test GET /api/runners/{id}/"""
        # Note: Créer un runner et tester
        pass
    
    def test_update_runner(self):
        """Test PUT /api/runners/{id}/"""
        # Note: Créer un runner et tester
        pass
    
    def test_delete_runner(self):
        """Test DELETE /api/runners/{id}/ (soft delete)"""
        # Note: Créer un runner, le supprimer, vérifier is_deleted=True
        pass
    
    def test_get_execution_plan(self):
        """Test GET /api/runners/{id}/execution_plan/"""
        # Note: Créer un runner avec steps et tester
        pass


class ExecutionLogAPITest(TestCase):
    """Tests pour l'API ExecutionLog (read-only)."""
    
    def setUp(self):
        """Configuration initiale."""
        self.client = APIClient()
    
    def test_list_logs(self):
        """Test GET /api/execution-logs/"""
        url = reverse('executionlog-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_log_detail(self):
        """Test GET /api/execution-logs/{id}/"""
        # Note: Créer un log et tester
        pass
    
    def test_cannot_create_log(self):
        """Vérifier qu'on ne peut pas créer un log via l'API"""
        url = reverse('executionlog-list')
        
        data = {
            'status': 'SUCCESS'
        }
        
        response = self.client.post(url, data, format='json')
        
        # Should return 405 Method Not Allowed
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_cannot_delete_log(self):
        """Vérifier qu'on ne peut pas supprimer un log via l'API"""
        # Note: Créer un log et tester
        pass
