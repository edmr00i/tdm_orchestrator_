"""
Utilitaires pour la gestion des fichiers d'export.

Ce module contient les fonctions utilitaires pour la manipulation
des fichiers et noms de fichiers.
"""

from ..constants import INVALID_FILENAME_CHARS, MAX_FILENAME_LENGTH


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour éviter les caractères invalides.
    
    Args:
        filename: Nom de fichier original
        
    Returns:
        Nom de fichier nettoyé
    """
    for char in INVALID_FILENAME_CHARS:
        filename = filename.replace(char, '_')
    
    if len(filename) > MAX_FILENAME_LENGTH:
        filename = filename[:MAX_FILENAME_LENGTH]
    
    return filename


def sanitize_reference(reference: str) -> str:
    """
    Nettoie une référence pour usage dans un nom de fichier.
    
    Args:
        reference: Référence originale
        
    Returns:
        Référence nettoyée
    """
    return reference.replace('/', '_').replace('\\', '_')
