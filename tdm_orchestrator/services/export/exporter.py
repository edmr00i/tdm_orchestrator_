"""
Service d'export de runners - Facade allégée.

Ce module fournit une interface simplifiée pour l'export
en utilisant ConfigBuilder et ZipBuilder.
"""

import logging
from typing import Dict, Optional

from .config_builder import ConfigBuilder
from .zip_builder import ZipBuilder
from ..constants import (
    ESTIMATED_CONFIG_SIZE_KB,
    ESTIMATED_README_SIZE_KB,
    ESTIMATED_HEADER_SIZE_BYTES,
    ZIP_COMPRESSION_RATIO,
)
from ..exceptions import ExportError

logger = logging.getLogger(__name__)


class RunnerExporter:
    """
    Facade pour l'export de runners en fichiers ZIP.
    
    Coordonne ConfigBuilder et ZipBuilder pour générer
    un package complet.
    
    Example:
        >>> exporter = RunnerExporter(runner)
        >>> zip_path = exporter.export()
    """
    
    def __init__(self, runner):
        """
        Initialise l'exporter.
        
        Args:
            runner: Instance de Runner (modèle Django)
        """
        self.runner = runner
        self.config_builder = ConfigBuilder(runner)
        self.zip_builder = ZipBuilder(runner)
    
    def export(self, output_path: Optional[str] = None) -> str:
        """
        Exporte le runner en fichier ZIP.
        
        Args:
            output_path: Chemin de sortie du ZIP (optionnel)
            
        Returns:
            Chemin du fichier ZIP créé
            
        Raises:
            ExportError: Si une erreur survient
        """
        try:
            logger.info(f"Export du runner : {self.runner.name}")
            
            # Générer la configuration
            config = self.config_builder.build()
            
            # Écrire les fichiers
            self.zip_builder.write_config_file(config)
            self.zip_builder.write_script_files(config)
            self.zip_builder.write_readme(config)
            
            # Créer le ZIP
            zip_path = self.zip_builder.create_zip(output_path)
            
            logger.info(f"Export terminé : {zip_path}")
            return zip_path
        
        except Exception as e:
            error_msg = f"Erreur export : {str(e)}"
            logger.error(error_msg)
            raise ExportError(error_msg)
        
        finally:
            self.zip_builder.cleanup()
    
    def get_export_info(self) -> Dict:
        """
        Retourne les informations sur l'export sans le générer.
        
        Returns:
            Dictionnaire avec les infos de l'export
        """
        config = self.config_builder.build()
        
        return {
            'runner_name': config['metadata']['runner_name'],
            'runner_reference': config['metadata']['runner_reference'],
            'application': config['metadata']['application_name'],
            'pre_scripts_count': len(config['pre_scripts']),
            'post_scripts_count': len(config['post_scripts']),
            'total_scripts': len(config['pre_scripts']) + len(config['post_scripts']),
            'required_variables': config['required_variables'],
            'variables_count': len(config['required_variables']),
            'estimated_size_kb': self._estimate_export_size(),
        }
    
    def _estimate_export_size(self) -> int:
        """Estime la taille du ZIP en Ko."""
        total_size = ESTIMATED_CONFIG_SIZE_KB + ESTIMATED_README_SIZE_KB
        
        pre_steps = self.runner.get_pre_scripts()
        post_steps = self.runner.get_post_scripts()
        
        for step in list(pre_steps) + list(post_steps):
            script_size = len(step.script.content.encode('utf-8'))
            script_size += ESTIMATED_HEADER_SIZE_BYTES
            total_size += script_size // 1024
        
        total_size = int(total_size * ZIP_COMPRESSION_RATIO)
        return max(1, total_size)


# Fonction utilitaire
def export_runner_to_zip(runner, output_path: Optional[str] = None) -> str:
    """
    Fonction utilitaire pour exporter un runner.
    
    Args:
        runner: Instance Runner
        output_path: Chemin de sortie (optionnel)
        
    Returns:
        Chemin du ZIP créé
    """
    exporter = RunnerExporter(runner)
    return exporter.export(output_path)
