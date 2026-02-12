"""
Constructeur de fichiers ZIP pour l'export.

Ce module gère la création du fichier ZIP contenant
les scripts SQL et la configuration.
"""

import os
import json
import tempfile
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from zipfile import ZipFile, ZIP_DEFLATED

from .file_utils import sanitize_filename, sanitize_reference
from ..constants import DATETIME_FORMAT, DATETIME_FORMAT_FILE
from ..exceptions import ZipCreationError

logger = logging.getLogger(__name__)


class ZipBuilder:
    """
    Constructeur de fichiers ZIP pour l'export de runners.
    
    Gère la création du répertoire temporaire, l'écriture des fichiers
    et la compression finale.
    """
    
    def __init__(self, runner):
        """
        Initialise le builder.
        
        Args:
            runner: Instance de Runner
        """
        self.runner = runner
        self.temp_dir: Optional[str] = None
    
    def _create_temp_directory(self) -> str:
        """Crée un répertoire temporaire."""
        timestamp = datetime.now().strftime(DATETIME_FORMAT_FILE)
        runner_ref = sanitize_reference(self.runner.reference)
        dir_name = f"runner_export_{runner_ref}_{timestamp}"
        
        self.temp_dir = os.path.join(tempfile.gettempdir(), dir_name)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        logger.info(f"Répertoire temporaire : {self.temp_dir}")
        return self.temp_dir
    
    def cleanup(self):
        """Supprime le répertoire temporaire."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"Nettoyage : {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Échec nettoyage : {e}")
    
    def write_config_file(self, config: Dict) -> str:
        """
        Écrit le fichier config.json.
        
        Args:
            config: Configuration à écrire
            
        Returns:
            Chemin du fichier créé
        """
        if not self.temp_dir:
            self._create_temp_directory()
        
        config_path = os.path.join(self.temp_dir, 'config.json')
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"config.json créé")
        return config_path
    
    def write_script_files(self, config: Dict):
        """
        Écrit tous les fichiers SQL.
        
        Args:
            config: Configuration contenant les infos des scripts
        """
        if not self.temp_dir:
            self._create_temp_directory()
        
        scripts_written = 0
        
        # Scripts PRE
        for step in self.runner.get_pre_scripts():
            self._write_single_script(step, 'pre')
            scripts_written += 1
        
        # Scripts POST
        for step in self.runner.get_post_scripts():
            self._write_single_script(step, 'post')
            scripts_written += 1
        
        logger.info(f"{scripts_written} fichier(s) SQL créé(s)")
    
    def _write_single_script(self, step, step_type: str):
        """Écrit un fichier SQL individuel."""
        script = step.script
        filename = self._get_script_filename(script, step.order, step_type)
        filepath = os.path.join(self.temp_dir, filename)
        
        header = self._generate_sql_header(script, step.order, step_type.upper())
        content = header + '\n' + script.content
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.debug(f"Script écrit : {filename}")
    
    def _get_script_filename(self, script, order: int, step_type: str) -> str:
        """Génère un nom de fichier standardisé."""
        script_name = sanitize_filename(script.name)
        return f"{step_type}_{order:03d}_{script_name}.sql"
    
    def _generate_sql_header(self, script, order: int, step_type: str) -> str:
        """Génère un en-tête descriptif pour un fichier SQL."""
        variables_str = ', '.join(script.extract_variables()) or 'Aucune'
        datasource_name = script.datasource.name if script.datasource else 'Non spécifiée'
        
        return f"""-- ============================================================================
-- Script : {script.name}
-- Référence : {script.reference}
-- Type : {step_type}-Processing (Ordre: {order})
-- ============================================================================
-- Description : {script.description or 'Aucune description'}
-- Source de données : {datasource_name}
-- Variables requises : {variables_str}
-- Date d'export : {datetime.now().strftime(DATETIME_FORMAT)}
-- ============================================================================
"""
    
    def write_readme(self, config: Dict):
        """
        Crée le fichier README.md.
        
        Args:
            config: Configuration du runner
        """
        if not self.temp_dir:
            self._create_temp_directory()
        
        content = self._generate_readme_content(config)
        readme_path = os.path.join(self.temp_dir, 'README.md')
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("README.md créé")
    
    def _generate_readme_content(self, config: Dict) -> str:
        """Génère le contenu du README."""
        meta = config['metadata']
        settings = config['execution_settings']
        
        content = f"""# Runner Export: {meta['runner_name']}

## 📋 Informations

- **Référence** : {meta['runner_reference']}
- **Application** : {meta['application_name']}
- **Date d'export** : {meta['export_date']}

## 📝 Description

{meta['runner_description']}

## ⚙️ Configuration

- **Arrêt sur erreur** : {'Oui' if settings['stop_on_error'] else 'Non'}
- **Logs verbeux** : {'Oui' if settings['verbose_logging'] else 'Non'}

## 🔄 Séquence d'exécution

### Pré-traitement ({len(config['pre_scripts'])} script(s))
"""
        
        for script in config['pre_scripts']:
            content += f"\n**{script['order']}.** `{script['file']}`\n"
        
        content += f"\n### Post-traitement ({len(config['post_scripts'])} script(s))\n"
        
        for script in config['post_scripts']:
            content += f"\n**{script['order']}.** `{script['file']}`\n"
        
        if config['required_variables']:
            content += "\n## 🔧 Variables requises\n\n"
            for var in config['required_variables']:
                content += f"- `${{{var}}}`\n"
        
        content += "\n---\n*Généré par TDM SQL Orchestrator*\n"
        
        return content
    
    def create_zip(self, output_path: Optional[str] = None) -> str:
        """
        Crée le fichier ZIP final.
        
        Args:
            output_path: Chemin de sortie (optionnel)
            
        Returns:
            Chemin du fichier ZIP créé
        """
        if not self.temp_dir:
            raise ZipCreationError("Aucun fichier à compresser")
        
        if output_path is None:
            timestamp = datetime.now().strftime(DATETIME_FORMAT_FILE)
            runner_ref = sanitize_filename(self.runner.reference)
            zip_filename = f"runner_{runner_ref}_{timestamp}.zip"
            output_path = os.path.join(tempfile.gettempdir(), zip_filename)
        
        try:
            with ZipFile(output_path, 'w', ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.temp_dir)
                        zipf.write(file_path, arcname)
            
            file_size = os.path.getsize(output_path)
            logger.info(f"ZIP créé : {output_path} ({file_size} octets)")
            
            return output_path
        
        except Exception as e:
            raise ZipCreationError(f"Erreur création ZIP : {str(e)}")
