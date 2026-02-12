"""
Constructeur de configuration pour l'export de runners.

Ce module gère la génération du fichier config.json
et des métadonnées d'export.
"""

import logging
from datetime import datetime
from typing import Dict, List

from ..constants import EXPORT_VERSION

logger = logging.getLogger(__name__)


class ConfigBuilder:
    """
    Constructeur de configuration d'export.
    
    Génère la structure de configuration JSON pour un runner.
    """
    
    def __init__(self, runner):
        """
        Initialise le builder avec un runner.
        
        Args:
            runner: Instance de Runner (modèle Django)
        """
        self.runner = runner
    
    def build(self) -> Dict:
        """
        Génère le dictionnaire de configuration complet.
        
        Returns:
            Configuration complète du runner
        """
        config = {
            'metadata': self._build_metadata(),
            'execution_settings': self._build_execution_settings(),
            'pre_scripts': [],
            'anonymization': {
                'engine': 'TDM_CORE',
                'note': 'Gérée par le moteur TDM principal',
            },
            'post_scripts': [],
        }
        
        # Ajouter les scripts
        config['pre_scripts'] = self._build_scripts_config(
            self.runner.get_pre_scripts(), 'pre'
        )
        config['post_scripts'] = self._build_scripts_config(
            self.runner.get_post_scripts(), 'post'
        )
        
        # Collecter les variables
        config['required_variables'] = self._collect_variables(config)
        
        logger.info(
            f"Config générée : {len(config['pre_scripts'])} PRE, "
            f"{len(config['post_scripts'])} POST"
        )
        
        return config
    
    def _build_metadata(self) -> Dict:
        """Construit les métadonnées."""
        return {
            'runner_reference': self.runner.reference,
            'runner_name': self.runner.name,
            'runner_description': self.runner.description or '',
            'application_name': self.runner.application.name,
            'application_reference': self.runner.application.reference,
            'export_date': datetime.now().isoformat(),
            'export_version': EXPORT_VERSION,
        }
    
    def _build_execution_settings(self) -> Dict:
        """Construit les paramètres d'exécution."""
        return {
            'stop_on_error': self.runner.stop_on_error,
            'verbose_logging': self.runner.verbose_logging,
        }
    
    def _build_scripts_config(self, steps, step_type: str) -> List[Dict]:
        """
        Construit la configuration des scripts.
        
        Args:
            steps: QuerySet des RunnerStep
            step_type: 'pre' ou 'post'
            
        Returns:
            Liste de configurations de scripts
        """
        scripts = []
        
        for step in steps:
            script = step.script
            scripts.append({
                'order': step.order,
                'script_reference': script.reference,
                'script_name': script.name,
                'script_description': script.description or '',
                'script_type': script.script_type,
                'datasource_name': script.datasource.name if script.datasource else None,
                'datasource_reference': script.datasource.reference if script.datasource else None,
                'file': self._get_script_filename(script, step.order, step_type),
                'variables': script.extract_variables(),
            })
        
        return scripts
    
    def _get_script_filename(self, script, order: int, step_type: str) -> str:
        """Génère un nom de fichier standardisé."""
        from .file_utils import sanitize_filename
        script_name = sanitize_filename(script.name)
        return f"{step_type}_{order:03d}_{script_name}.sql"
    
    def _collect_variables(self, config: Dict) -> List[str]:
        """Collecte toutes les variables uniques."""
        all_variables = set()
        
        for script_info in config['pre_scripts'] + config['post_scripts']:
            all_variables.update(script_info['variables'])
        
        return sorted(list(all_variables))
