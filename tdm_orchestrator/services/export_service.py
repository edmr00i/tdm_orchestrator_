"""
Service d'export de runners en fichier ZIP pour l'automatisation DAN AUTO.

Génère un package ZIP contenant :
- config.json : Configuration du runner
- pre_XXX_ScriptName.sql : Scripts de pré-traitement
- post_XXX_ScriptName.sql : Scripts de post-traitement
"""

import os
import json
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED

logger = logging.getLogger(__name__)


class ExportError(Exception):
    """Exception levée lors d'erreurs d'export."""
    pass


class RunnerExporter:
    """
    Classe pour exporter un Runner en fichier ZIP.
    
    Le ZIP généré contient :
    - config.json : Métadonnées et configuration
    - Scripts SQL ordonnés avec nommage standardisé
    
    Exemple:
        >>> exporter = RunnerExporter(runner)
        >>> zip_path = exporter.export()
        >>> print(f"ZIP créé : {zip_path}")
    """
    
    def __init__(self, runner):
        """
        Initialise l'exporter avec un runner.
        
        Args:
            runner: Instance de Runner (modèle Django)
        """
        self.runner = runner
        self.temp_dir = None
    
    def _create_temp_directory(self) -> str:
        """
        Crée un répertoire temporaire pour préparer le ZIP.
        
        Returns:
            Chemin du répertoire temporaire
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        runner_ref = self.runner.reference.replace('/', '_').replace('\\', '_')
        dir_name = f"runner_export_{runner_ref}_{timestamp}"
        
        self.temp_dir = os.path.join(tempfile.gettempdir(), dir_name)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        logger.info(f"Répertoire temporaire créé : {self.temp_dir}")
        return self.temp_dir
    
    def _cleanup_temp_directory(self):
        """Supprime le répertoire temporaire."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"Répertoire temporaire supprimé : {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Impossible de supprimer {self.temp_dir}: {str(e)}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Nettoie un nom de fichier pour éviter les caractères invalides.
        
        Args:
            filename: Nom de fichier original
            
        Returns:
            Nom de fichier nettoyé
        """
        # Remplacer les caractères interdits
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limiter la longueur
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename
    
    def _generate_config_json(self) -> Dict:
        """
        Génère le dictionnaire de configuration pour le fichier JSON.
        
        Returns:
            Configuration complète du runner
        """
        config = {
            'metadata': {
                'runner_reference': self.runner.reference,
                'runner_name': self.runner.name,
                'runner_description': self.runner.description or '',
                'application_name': self.runner.application.name,
                'application_reference': self.runner.application.reference,
                'export_date': datetime.now().isoformat(),
                'export_version': '1.0',
            },
            'execution_settings': {
                'stop_on_error': self.runner.stop_on_error,
                'verbose_logging': self.runner.verbose_logging,
            },
            'pre_scripts': [],
            'anonymization': {
                'engine': 'TDM_CORE',
                'note': 'Cette étape est gérée par le moteur TDM principal (non inclus dans ce package)',
            },
            'post_scripts': [],
        }
        
        # Ajouter les scripts PRE
        pre_steps = self.runner.get_pre_scripts()
        for step in pre_steps:
            script_info = {
                'order': step.order,
                'script_reference': step.script.reference,
                'script_name': step.script.name,
                'script_description': step.script.description or '',
                'script_type': step.script.script_type,
                'datasource_name': step.script.datasource.name if step.script.datasource else None,
                'datasource_reference': step.script.datasource.reference if step.script.datasource else None,
                'file': self._get_script_filename(step.script, step.order, 'pre'),
                'variables': step.script.extract_variables(),
            }
            config['pre_scripts'].append(script_info)
        
        # Ajouter les scripts POST
        post_steps = self.runner.get_post_scripts()
        for step in post_steps:
            script_info = {
                'order': step.order,
                'script_reference': step.script.reference,
                'script_name': step.script.name,
                'script_description': step.script.description or '',
                'script_type': step.script.script_type,
                'datasource_name': step.script.datasource.name if step.script.datasource else None,
                'datasource_reference': step.script.datasource.reference if step.script.datasource else None,
                'file': self._get_script_filename(step.script, step.order, 'post'),
                'variables': step.script.extract_variables(),
            }
            config['post_scripts'].append(script_info)
        
        # Collecter toutes les variables uniques
        all_variables = set()
        for script_info in config['pre_scripts'] + config['post_scripts']:
            all_variables.update(script_info['variables'])
        
        config['required_variables'] = sorted(list(all_variables))
        
        logger.info(f"Configuration générée : {len(config['pre_scripts'])} PRE, {len(config['post_scripts'])} POST")
        return config
    
    def _get_script_filename(self, script, order: int, step_type: str) -> str:
        """
        Génère un nom de fichier standardisé pour un script.
        
        Format : {type}_{order:03d}_{script_name}.sql
        Exemple : pre_001_Clean_Audit_Logs.sql
        
        Args:
            script: Instance SqlScript
            order: Numéro d'ordre
            step_type: 'pre' ou 'post'
            
        Returns:
            Nom de fichier
        """
        script_name = self._sanitize_filename(script.name)
        filename = f"{step_type}_{order:03d}_{script_name}.sql"
        return filename
    
    def _write_config_file(self, temp_dir: str, config: Dict) -> str:
        """
        Écrit le fichier config.json dans le répertoire temporaire.
        
        Args:
            temp_dir: Répertoire temporaire
            config: Configuration à écrire
            
        Returns:
            Chemin du fichier créé
        """
        config_path = os.path.join(temp_dir, 'config.json')
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Fichier config.json créé : {config_path}")
        return config_path
    
    def _write_script_files(self, temp_dir: str, config: Dict):
        """
        Écrit tous les fichiers SQL dans le répertoire temporaire.
        
        Args:
            temp_dir: Répertoire temporaire
            config: Configuration contenant les infos des scripts
        """
        scripts_written = 0
        
        # Écrire les scripts PRE
        pre_steps = self.runner.get_pre_scripts()
        for step in pre_steps:
            filename = self._get_script_filename(step.script, step.order, 'pre')
            filepath = os.path.join(temp_dir, filename)
            
            # Ajouter un en-tête au fichier SQL
            header = self._generate_sql_header(step.script, step.order, 'PRE')
            content = header + '\n' + step.script.content
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            scripts_written += 1
            logger.debug(f"Script PRE écrit : {filename}")
        
        # Écrire les scripts POST
        post_steps = self.runner.get_post_scripts()
        for step in post_steps:
            filename = self._get_script_filename(step.script, step.order, 'post')
            filepath = os.path.join(temp_dir, filename)
            
            # Ajouter un en-tête au fichier SQL
            header = self._generate_sql_header(step.script, step.order, 'POST')
            content = header + '\n' + step.script.content
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            scripts_written += 1
            logger.debug(f"Script POST écrit : {filename}")
        
        logger.info(f"{scripts_written} fichier(s) SQL créé(s)")
    
    def _generate_sql_header(self, script, order: int, step_type: str) -> str:
        """
        Génère un en-tête descriptif pour un fichier SQL.
        
        Args:
            script: Instance SqlScript
            order: Numéro d'ordre
            step_type: 'PRE' ou 'POST'
            
        Returns:
            En-tête SQL commenté
        """
        variables_str = ', '.join(script.extract_variables()) or 'Aucune'
        datasource_name = script.datasource.name if script.datasource else 'Non spécifiée'
        
        header = f"""-- ============================================================================
-- Script : {script.name}
-- Référence : {script.reference}
-- Type : {step_type}-Processing (Ordre: {order})
-- ============================================================================
-- Description : {script.description or 'Aucune description'}
-- Source de données : {datasource_name}
-- Variables requises : {variables_str}
-- Date d'export : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- ============================================================================
"""
        return header
    
    def _create_readme(self, temp_dir: str, config: Dict):
        """
        Crée un fichier README.md avec les instructions d'utilisation.
        
        Args:
            temp_dir: Répertoire temporaire
            config: Configuration du runner
        """
        readme_content = f"""# Runner Export: {config['metadata']['runner_name']}

## 📋 Informations

- **Référence** : {config['metadata']['runner_reference']}
- **Application** : {config['metadata']['application_name']}
- **Date d'export** : {config['metadata']['export_date']}
- **Version** : {config['metadata']['export_version']}

## 📝 Description

{config['metadata']['runner_description']}

## ⚙️ Configuration

- **Arrêt sur erreur** : {'Oui' if config['execution_settings']['stop_on_error'] else 'Non'}
- **Logs verbeux** : {'Oui' if config['execution_settings']['verbose_logging'] else 'Non'}

## 📂 Structure du package

```
.
├── config.json              # Configuration complète du runner
├── README.md               # Ce fichier
├── pre_001_*.sql          # Scripts de pré-traitement (ordre d'exécution)
├── pre_002_*.sql
├── ...
├── post_001_*.sql         # Scripts de post-traitement
└── post_002_*.sql
```

## 🔄 Séquence d'exécution

### 1. Pré-traitement ({len(config['pre_scripts'])} script(s))

"""
        
        for script in config['pre_scripts']:
            readme_content += f"**{script['order']}.** `{script['file']}`\n"
            readme_content += f"   - {script['script_description']}\n"
            if script['variables']:
                readme_content += f"   - Variables : {', '.join(script['variables'])}\n"
            readme_content += "\n"
        
        readme_content += f"""
### 2. Anonymisation

Exécutée par le moteur TDM principal (non inclus dans ce package).

### 3. Post-traitement ({len(config['post_scripts'])} script(s))

"""
        
        for script in config['post_scripts']:
            readme_content += f"**{script['order']}.** `{script['file']}`\n"
            readme_content += f"   - {script['script_description']}\n"
            if script['variables']:
                readme_content += f"   - Variables : {', '.join(script['variables'])}\n"
            readme_content += "\n"
        
        if config['required_variables']:
            readme_content += f"""
## 🔧 Variables requises

Les variables suivantes doivent être fournies lors de l'exécution :

"""
            for var in config['required_variables']:
                readme_content += f"- `${{{var}}}`\n"
        
        readme_content += """
## 🚀 Utilisation avec DAN AUTO

Ce package est conçu pour être utilisé avec les scripts Python DAN AUTO.

**Exemple d'utilisation** :

```python
import json
from dan_auto import RunnerExecutor

# Charger la configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# Définir les variables
variables = {
    'SCHEMA': 'production',
    'DATE_EXEC': '2024-02-06',
    # ... autres variables
}

# Exécuter le runner
executor = RunnerExecutor(config, variables)
executor.run()
```

##  Notes importantes

1. **Vérifiez les variables** : Assurez-vous de fournir toutes les variables requises
2. **Testez en DRY RUN** : Utilisez le mode validation avant l'exécution réelle
3. **Sauvegardez** : Effectuez une sauvegarde avant exécution
4. **Vérifiez les connexions** : Assurez-vous d'avoir accès aux bases de données cibles

##  Support

Pour toute question, contactez l'équipe TDM.

---
*Package généré automatiquement par TDM SQL Orchestrator*
"""
        
        readme_path = os.path.join(temp_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"README.md créé : {readme_path}")
    
    def _create_zip_file(self, temp_dir: str, output_path: Optional[str] = None) -> str:
        """
        Crée le fichier ZIP à partir du répertoire temporaire.
        
        Args:
            temp_dir: Répertoire contenant les fichiers à compresser
            output_path: Chemin de sortie du ZIP (optionnel)
            
        Returns:
            Chemin du fichier ZIP créé
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            runner_ref = self._sanitize_filename(self.runner.reference)
            zip_filename = f"runner_{runner_ref}_{timestamp}.zip"
            output_path = os.path.join(tempfile.gettempdir(), zip_filename)
        
        with ZipFile(output_path, 'w', ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
                    logger.debug(f"Ajouté au ZIP : {arcname}")
        
        file_size = os.path.getsize(output_path)
        logger.info(f"ZIP créé : {output_path} ({file_size} octets)")
        
        return output_path
    
    def export(self, output_path: Optional[str] = None) -> str:
        """
        Exporte le runner en fichier ZIP.
        
        Args:
            output_path: Chemin de sortie du ZIP (optionnel)
            
        Returns:
            Chemin du fichier ZIP créé
            
        Raises:
            ExportError: Si une erreur survient lors de l'export
        """
        try:
            logger.info(f"Début de l'export du runner : {self.runner.name}")
            
            # Créer le répertoire temporaire
            temp_dir = self._create_temp_directory()
            
            # Générer la configuration
            config = self._generate_config_json()
            
            # Écrire le fichier config.json
            self._write_config_file(temp_dir, config)
            
            # Écrire les fichiers SQL
            self._write_script_files(temp_dir, config)
            
            # Créer le README
            self._create_readme(temp_dir, config)
            
            # Créer le ZIP
            zip_path = self._create_zip_file(temp_dir, output_path)
            
            logger.info(f"Export terminé avec succès : {zip_path}")
            
            return zip_path
        
        except Exception as e:
            error_msg = f"Erreur lors de l'export : {str(e)}"
            logger.error(error_msg)
            raise ExportError(error_msg)
        
        finally:
            # Nettoyage
            self._cleanup_temp_directory()
    
    def get_export_info(self) -> Dict:
        """
        Retourne les informations sur l'export sans le générer.
        
        Returns:
            Dictionnaire avec les infos de l'export
        """
        config = self._generate_config_json()
        
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
        """
        Estime la taille du ZIP en Ko.
        
        Returns:
            Taille estimée en Ko
        """
        total_size = 0
        
        # Config JSON : ~5 Ko
        total_size += 5
        
        # README : ~2 Ko
        total_size += 2
        
        # Scripts SQL
        pre_steps = self.runner.get_pre_scripts()
        post_steps = self.runner.get_post_scripts()
        
        for step in list(pre_steps) + list(post_steps):
            # Taille du contenu + en-tête
            script_size = len(step.script.content.encode('utf-8'))
            script_size += 500  # En-tête
            total_size += script_size // 1024  # Convertir en Ko
        
        # Compression ZIP (estimation : 70% de compression)
        total_size = int(total_size * 0.3)
        
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
