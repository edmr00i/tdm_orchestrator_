"""
Constantes et configurations pour les services TDM Orchestrator.

Ce module centralise toutes les constantes, patterns regex et
configurations fixes utilisées dans les services.
"""

import re
from typing import Set


# =====================
# Bases de données supportées
# =====================
SUPPORTED_DATABASES = {
    'postgresql': 'psycopg2',
    'oracle': 'cx_Oracle',
    'sqlserver': 'pyodbc',
    'mysql': 'mysqlclient',
}

DATABASE_ALIASES = {
    'postgres': 'postgresql',
    'pg': 'postgresql',
    'mssql': 'sqlserver',
    'sql server': 'sqlserver',
    'mariadb': 'mysql',
}

# Ports par défaut
DEFAULT_PORTS = {
    'postgresql': 5432,
    'oracle': 1521,
    'sqlserver': 1433,
    'mysql': 3306,
}


# =====================
# Patterns SQL
# =====================
# Pattern pour détecter les variables au format ${VARIABLE_NAME}
VARIABLE_PATTERN = re.compile(r'\$\{([A-Za-z0-9_]+)\}')

# Patterns de commandes interdites en transaction
TRANSACTION_FORBIDDEN_PATTERNS = [
    # PostgreSQL - Opérations CONCURRENTLY
    r'\bREINDEX\s+.*\bCONCURRENTLY\b',
    r'\bCREATE\s+INDEX\s+CONCURRENTLY\b',
    r'\bDROP\s+INDEX\s+CONCURRENTLY\b',
    r'\bCREATE\s+DATABASE\b',
    r'\bDROP\s+DATABASE\b',
    
    # PostgreSQL - Maintenance
    r'\bVACUUM\b',
    r'\bCLUSTER\b(?!\s+ON)',
    
    # PostgreSQL - Réplication et recovery
    r'\bALTER\s+SYSTEM\b',
    
    # MySQL - Commandes DDL implicitement commitées
    r'\bLOAD\s+DATA\b',
    r'\bLOCK\s+TABLES\b',
    r'\bUNLOCK\s+TABLES\b',
    
    # Oracle - Commandes hors transaction
    r'\bALTER\s+DATABASE\b',
]

# Patterns dangereux pour les injections SQL dans les valeurs de variables
DANGEROUS_VARIABLE_VALUE_PATTERNS = [
    r';.*DROP\s+TABLE',
    r';.*DELETE\s+FROM',
    r';.*TRUNCATE',
    r'--',  # Commentaires SQL
    r'/\*',  # Commentaires multi-lignes
]


# =====================
# Variables autorisées (whitelist)
# =====================
ALLOWED_VARIABLE_NAMES: Set[str] = {
    # Schémas
    'SCHEMA', 'TARGET_SCHEMA', 'SOURCE_SCHEMA',
    
    # Tables
    'TABLE', 'TABLE_NAME',
    
    # Dates
    'DATE', 'DATE_EXEC', 'DATE_LIMIT', 'START_DATE', 'END_DATE',
    
    # Utilisateurs
    'USER', 'USER_ID',
    
    # Identifiants et pagination
    'ID', 'LIMIT', 'OFFSET',
    
    # Base de données
    'DATABASE', 'DB_NAME',
    
    # Valeurs génériques
    'VALUE', 'STATUS',
    
    # Temporels
    'YEAR', 'MONTH', 'DAY',
}


# =====================
# Export
# =====================
EXPORT_VERSION = '1.0'

# Caractères invalides dans les noms de fichiers
INVALID_FILENAME_CHARS = '<>:"/\\|?*'

# Longueur max des noms de fichiers
MAX_FILENAME_LENGTH = 200

# Tailles estimées (en Ko)
ESTIMATED_CONFIG_SIZE_KB = 5
ESTIMATED_README_SIZE_KB = 2
ESTIMATED_HEADER_SIZE_BYTES = 500

# Ratio de compression ZIP
ZIP_COMPRESSION_RATIO = 0.3


# =====================
# Logging
# =====================
LOG_TIMESTAMP_FORMAT = '%H:%M:%S'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATETIME_FORMAT_FILE = '%Y%m%d_%H%M%S'


# =====================
# Script Types
# =====================
SCRIPT_TYPE_PRE = 'PRE'
SCRIPT_TYPE_POST = 'POST'
SCRIPT_TYPE_UTIL = 'UTIL'

SCRIPT_TYPES = [
    (SCRIPT_TYPE_PRE, 'Pre-Processing'),
    (SCRIPT_TYPE_POST, 'Post-Processing'),
    (SCRIPT_TYPE_UTIL, 'Utility'),
]
