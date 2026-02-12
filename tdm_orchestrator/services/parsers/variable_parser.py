"""
Service de parsing et substitution de variables dans les scripts SQL.

Ce module permet d'extraire et de remplacer les variables au format ${VARIABLE_NAME}.
"""

import re
import logging
from typing import Dict, List, Optional, Set

from ..constants import VARIABLE_PATTERN, ALLOWED_VARIABLE_NAMES, DANGEROUS_VARIABLE_VALUE_PATTERNS
from ..exceptions import VariableParsingError, VariableValidationError

logger = logging.getLogger(__name__)


class VariableParser:
    """
    Classe pour gérer le parsing et la substitution de variables SQL.
    
    Format supporté : ${VARIABLE_NAME}
    
    Example:
        >>> parser = VariableParser()
        >>> sql = "SELECT * FROM ${SCHEMA}.users WHERE id = ${USER_ID}"
        >>> variables = parser.extract_variables(sql)
        >>> parsed = parser.parse(sql, {'SCHEMA': 'production', 'USER_ID': '123'})
    """
    
    def __init__(self, strict_mode: bool = True, 
                 allowed_variables: Optional[Set[str]] = None):
        """
        Initialise le parser.
        
        Args:
            strict_mode: Si True, vérifie que les variables sont dans la whitelist
            allowed_variables: Set personnalisé de variables autorisées
        """
        self.strict_mode = strict_mode
        self.allowed_variables = allowed_variables or ALLOWED_VARIABLE_NAMES
    
    def extract_variables(self, sql_content: str) -> List[str]:
        """
        Extrait la liste des variables présentes dans le SQL.
        
        Args:
            sql_content: Contenu SQL à analyser
            
        Returns:
            Liste des noms de variables (sans ${})
        """
        if not sql_content:
            return []
        
        matches = VARIABLE_PATTERN.findall(sql_content)
        
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
            VariableValidationError: Si strict_mode et variable non autorisée
        """
        if not self.strict_mode:
            return True
        
        if variable_name not in self.allowed_variables:
            error_msg = (
                f"Variable '{variable_name}' non autorisée. "
                f"Autorisées : {', '.join(sorted(self.allowed_variables))}"
            )
            logger.error(error_msg)
            raise VariableValidationError(error_msg)
        
        return True
    
    def validate_variable_value(self, value: str) -> str:
        """
        Valide et nettoie une valeur de variable.
        
        Args:
            value: Valeur à valider
            
        Returns:
            Valeur validée et nettoyée
            
        Raises:
            VariableValidationError: Si valeur potentiellement dangereuse
        """
        if not isinstance(value, str):
            value = str(value)
        
        for pattern in DANGEROUS_VARIABLE_VALUE_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                error_msg = f"Valeur potentiellement dangereuse : '{value}'"
                logger.error(error_msg)
                raise VariableValidationError(error_msg)
        
        return value
    
    def parse(self, sql_content: str, variables: Dict[str, str], 
              strict_validation: bool = True) -> str:
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
        """
        if not sql_content:
            return sql_content
        
        if not variables:
            remaining_vars = self.extract_variables(sql_content)
            if remaining_vars:
                raise VariableParsingError(f"Variables non fournies : {remaining_vars}")
            return sql_content
        
        # Vérifier les variables manquantes
        required = self.extract_variables(sql_content)
        missing = [var for var in required if var not in variables]
        if missing:
            raise VariableParsingError(f"Variables manquantes : {missing}")
        
        # Parser le SQL
        parsed_sql = sql_content
        
        for var_name, var_value in variables.items():
            if strict_validation:
                self.validate_variable_name(var_name)
                var_value = self.validate_variable_value(var_value)
            
            placeholder = f"${{{var_name}}}"
            parsed_sql = parsed_sql.replace(placeholder, var_value)
            logger.debug(f"Remplacé {placeholder} par '{var_value}'")
        
        # Avertir sur les variables restantes
        remaining = self.extract_variables(parsed_sql)
        if remaining:
            logger.warning(f"Variables non substituées : {remaining}")
        
        logger.info(f"Parsing terminé. {len(variables)} variable(s) substituée(s).")
        return parsed_sql
    
    def get_missing_variables(self, sql_content: str, 
                              provided: Dict[str, str]) -> List[str]:
        """Retourne les variables requises mais non fournies."""
        required = self.extract_variables(sql_content)
        return [var for var in required if var not in provided]
    
    def validate_sql_with_variables(self, sql_content: str, 
                                    variables: Dict[str, str]) -> Dict:
        """
        Valide un SQL avec ses variables sans le parser.
        
        Returns:
            Dictionnaire avec le résultat de validation
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
            required = self.extract_variables(sql_content)
            result['required_variables'] = required
            
            missing = self.get_missing_variables(sql_content, variables)
            result['missing_variables'] = missing
            
            if missing:
                result['valid'] = False
                result['errors'].append(f"Variables manquantes : {', '.join(missing)}")
            
            if self.strict_mode:
                for var_name in required:
                    try:
                        self.validate_variable_name(var_name)
                    except VariableValidationError as e:
                        result['valid'] = False
                        result['errors'].append(str(e))
            
            for var_name, var_value in variables.items():
                try:
                    self.validate_variable_value(var_value)
                except VariableValidationError as e:
                    result['valid'] = False
                    result['errors'].append(f"Variable {var_name}: {str(e)}")
            
            extra = [v for v in variables.keys() if v not in required]
            if extra:
                result['warnings'].append(f"Variables non utilisées : {', '.join(extra)}")
        
        except Exception as e:
            result['valid'] = False
            result['errors'].append(str(e))
        
        return result


# =====================
# Fonctions utilitaires
# =====================
def extract_sql_variables(sql_content: str) -> List[str]:
    """Fonction utilitaire pour extraire les variables d'un SQL."""
    parser = VariableParser(strict_mode=False)
    return parser.extract_variables(sql_content)


def parse_sql_variables(sql_content: str, variables: Dict[str, str], 
                        strict: bool = True) -> str:
    """Fonction utilitaire pour parser un SQL avec des variables."""
    parser = VariableParser(strict_mode=strict)
    return parser.parse(sql_content, variables, strict_validation=strict)
