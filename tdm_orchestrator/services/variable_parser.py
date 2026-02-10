"""
Service de parsing et substitution de variables dans les scripts SQL.

Ce service permet d'extraire et de remplacer les variables dans le format ${VARIABLE_NAME}.
"""

import re
import logging
from typing import List, Dict, Set, Optional

logger = logging.getLogger(__name__)


class VariableParsingError(Exception):
    """Exception levée lors d'erreurs de parsing de variables."""
    pass


class VariableParser:
    """
    Classe pour gérer le parsing et la substitution de variables SQL.
    
    Format supporté : ${VARIABLE_NAME}
    
    Exemples:
        >>> parser = VariableParser()
        >>> sql = "SELECT * FROM ${SCHEMA}.users WHERE id = ${USER_ID}"
        >>> variables = parser.extract_variables(sql)
        >>> print(variables)
        ['SCHEMA', 'USER_ID']
        
        >>> parsed = parser.parse(sql, {'SCHEMA': 'production', 'USER_ID': '123'})
        >>> print(parsed)
        "SELECT * FROM production.users WHERE id = 123"
    """
    
    # Regex pour détecter les variables au format ${VARIABLE_NAME}
    VARIABLE_PATTERN = re.compile(r'\$\{([A-Za-z0-9_]+)\}')
    
    # Whitelist des noms de variables autorisées (sécurité)
    ALLOWED_VARIABLE_NAMES = {
        'SCHEMA', 'TARGET_SCHEMA', 'SOURCE_SCHEMA',
        'TABLE', 'TABLE_NAME',
        'DATE', 'DATE_EXEC', 'DATE_LIMIT', 'START_DATE', 'END_DATE',
        'USER', 'USER_ID',
        'ID', 'LIMIT', 'OFFSET',
        'DATABASE', 'DB_NAME',
        'VALUE', 'STATUS',
        'YEAR', 'MONTH', 'DAY',
    }
    
    def __init__(self, strict_mode: bool = True, allowed_variables: Optional[Set[str]] = None):
        """
        Initialise le parser.
        
        Args:
            strict_mode: Si True, vérifie que les variables sont dans la whitelist
            allowed_variables: Set personnalisé de noms de variables autorisées
        """
        self.strict_mode = strict_mode
        self.allowed_variables = allowed_variables or self.ALLOWED_VARIABLE_NAMES
    
    def extract_variables(self, sql_content: str) -> List[str]:
        """
        Extrait la liste des variables présentes dans le SQL.
        
        Args:
            sql_content: Contenu SQL à analyser
            
        Returns:
            Liste des noms de variables (sans ${})
            
        Example:
            >>> parser = VariableParser()
            >>> sql = "SELECT * FROM ${SCHEMA}.${TABLE}"
            >>> parser.extract_variables(sql)
            ['SCHEMA', 'TABLE']
        """
        if not sql_content:
            return []
        
        matches = self.VARIABLE_PATTERN.findall(sql_content)
        # Dédoublonner tout en préservant l'ordre
        seen = set()
        result = []
        for var in matches:
            if var not in seen:
                seen.add(var)
                result.append(var)
        
        logger.debug(f"Variables extraites : {result}")
        return result
    
    def validate_variable_name(self, variable_name: str) -> bool:
        """
        Vérifie si un nom de variable est autorisé.
        
        Args:
            variable_name: Nom de la variable à valider
            
        Returns:
            True si la variable est autorisée
            
        Raises:
            VariableParsingError: Si en strict_mode et variable non autorisée
        """
        if not self.strict_mode:
            return True
        
        if variable_name not in self.allowed_variables:
            error_msg = (
                f"Variable '{variable_name}' non autorisée. "
                f"Variables autorisées : {', '.join(sorted(self.allowed_variables))}"
            )
            logger.error(error_msg)
            raise VariableParsingError(error_msg)
        
        return True
    
    def validate_variable_value(self, value: str) -> str:
        """
        Valide et nettoie une valeur de variable.
        
        Args:
            value: Valeur à valider
            
        Returns:
            Valeur validée et nettoyée
            
        Raises:
            VariableParsingError: Si la valeur contient des caractères dangereux
        """
        if not isinstance(value, str):
            value = str(value)
        
        # Vérifier les caractères potentiellement dangereux pour injection SQL
        dangerous_patterns = [
            r';.*DROP\s+TABLE',
            r';.*DELETE\s+FROM',
            r';.*TRUNCATE',
            r'--',  # Commentaires SQL
            r'/\*',  # Commentaires multi-lignes
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                error_msg = f"Valeur potentiellement dangereuse détectée : '{value}'"
                logger.error(error_msg)
                raise VariableParsingError(error_msg)
        
        return value
    
    def parse(self, sql_content: str, variables: Dict[str, str], strict_validation: bool = True) -> str:
        """
        Parse le SQL en remplaçant les variables par leurs valeurs.
        
        Args:
            sql_content: Contenu SQL à parser
            variables: Dictionnaire {nom_variable: valeur}
            strict_validation: Si True, valide les noms et valeurs
            
        Returns:
            SQL avec variables substituées
            
        Raises:
            VariableParsingError: Si une variable est manquante ou invalide
            
        Example:
            >>> parser = VariableParser()
            >>> sql = "SELECT * FROM ${SCHEMA}.users"
            >>> parser.parse(sql, {'SCHEMA': 'production'})
            "SELECT * FROM production.users"
        """
        if not sql_content:
            return sql_content
        
        if not variables:
            # Vérifier qu'il n'y a pas de variables non substituées
            remaining_vars = self.extract_variables(sql_content)
            if remaining_vars:
                error_msg = f"Variables non fournies : {remaining_vars}"
                logger.error(error_msg)
                raise VariableParsingError(error_msg)
            return sql_content
        
        # Extraire les variables du SQL
        required_variables = self.extract_variables(sql_content)
        
        # Vérifier que toutes les variables requises sont fournies
        missing_variables = [var for var in required_variables if var not in variables]
        if missing_variables:
            error_msg = f"Variables manquantes : {missing_variables}"
            logger.error(error_msg)
            raise VariableParsingError(error_msg)
        
        # Parser le SQL
        parsed_sql = sql_content
        
        for var_name, var_value in variables.items():
            # Validation si activée
            if strict_validation:
                self.validate_variable_name(var_name)
                var_value = self.validate_variable_value(var_value)
            
            # Remplacement de la variable
            placeholder = f"${{{var_name}}}"
            parsed_sql = parsed_sql.replace(placeholder, var_value)
            
            logger.debug(f"Remplacé {placeholder} par '{var_value}'")
        
        # Vérifier qu'il ne reste pas de variables non substituées
        remaining_vars = self.extract_variables(parsed_sql)
        if remaining_vars:
            logger.warning(f"Variables non substituées : {remaining_vars}")
        
        logger.info(f"Parsing terminé. {len(variables)} variable(s) substituée(s).")
        return parsed_sql
    
    def get_missing_variables(self, sql_content: str, provided_variables: Dict[str, str]) -> List[str]:
        """
        Retourne la liste des variables requises mais non fournies.
        
        Args:
            sql_content: Contenu SQL
            provided_variables: Variables fournies
            
        Returns:
            Liste des variables manquantes
        """
        required = self.extract_variables(sql_content)
        missing = [var for var in required if var not in provided_variables]
        return missing
    
    def validate_sql_with_variables(self, sql_content: str, variables: Dict[str, str]) -> Dict[str, any]:
        """
        Valide un SQL avec ses variables sans le parser.
        
        Args:
            sql_content: Contenu SQL
            variables: Variables à utiliser
            
        Returns:
            Dictionnaire avec le résultat de la validation
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'required_variables': [],
            'missing_variables': [],
            'provided_variables': list(variables.keys()),
        }
        
        try:
            # Extraire les variables requises
            required = self.extract_variables(sql_content)
            result['required_variables'] = required
            
            # Vérifier les variables manquantes
            missing = self.get_missing_variables(sql_content, variables)
            result['missing_variables'] = missing
            
            if missing:
                result['valid'] = False
                result['errors'].append(f"Variables manquantes : {', '.join(missing)}")
            
            # Valider les noms de variables si strict_mode
            if self.strict_mode:
                for var_name in required:
                    try:
                        self.validate_variable_name(var_name)
                    except VariableParsingError as e:
                        result['valid'] = False
                        result['errors'].append(str(e))
            
            # Valider les valeurs fournies
            for var_name, var_value in variables.items():
                try:
                    self.validate_variable_value(var_value)
                except VariableParsingError as e:
                    result['valid'] = False
                    result['errors'].append(f"Variable {var_name}: {str(e)}")
            
            # Avertir sur les variables fournies mais non utilisées
            extra_vars = [v for v in variables.keys() if v not in required]
            if extra_vars:
                result['warnings'].append(f"Variables fournies mais non utilisées : {', '.join(extra_vars)}")
        
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Erreur de validation : {str(e)}")
        
        return result


# Fonctions utilitaires pour usage simple
def extract_sql_variables(sql_content: str) -> List[str]:
    """
    Fonction utilitaire pour extraire les variables d'un SQL.
    
    Args:
        sql_content: Contenu SQL
        
    Returns:
        Liste des variables
    """
    parser = VariableParser(strict_mode=False)
    return parser.extract_variables(sql_content)


def parse_sql_variables(sql_content: str, variables: Dict[str, str], strict: bool = True) -> str:
    """
    Fonction utilitaire pour parser un SQL avec des variables.
    
    Args:
        sql_content: Contenu SQL
        variables: Dictionnaire de variables
        strict: Mode strict (validation)
        
    Returns:
        SQL parsé
    """
    parser = VariableParser(strict_mode=strict)
    return parser.parse(sql_content, variables, strict_validation=strict)
