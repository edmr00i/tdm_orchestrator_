"""
Splitters SQL pour découper les scripts en instructions individuelles.

Ce module contient les stratégies de découpage selon le type de base
de données (PostgreSQL, Oracle, SQL Server, MySQL).
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import List

logger = logging.getLogger(__name__)


class BaseSqlSplitter(ABC):
    """Classe abstraite pour les splitters SQL."""
    
    @abstractmethod
    def split(self, sql_content: str) -> List[str]:
        """Découpe le SQL en instructions individuelles."""
        pass
    
    def _remove_single_line_comments(self, sql_content: str) -> str:
        """Retire les commentaires mono-ligne en dehors des chaînes."""
        cleaned_lines = []
        
        for line in sql_content.split('\n'):
            in_quote = False
            quote_char = None
            comment_pos = -1
            
            i = 0
            while i < len(line):
                char = line[i]
                
                if char in ("'", '"') and not in_quote:
                    in_quote = True
                    quote_char = char
                elif in_quote and char == quote_char:
                    if i + 1 < len(line) and line[i + 1] == quote_char:
                        i += 1
                    else:
                        in_quote = False
                        quote_char = None
                elif not in_quote and line[i:i+2] == '--':
                    comment_pos = i
                    break
                
                i += 1
            
            if comment_pos >= 0:
                cleaned_lines.append(line[:comment_pos])
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _remove_multiline_comments(self, sql_content: str) -> str:
        """Retire les commentaires multi-lignes /* */ en dehors des chaînes."""
        result = []
        i = 0
        in_quote = False
        quote_char = None
        in_comment = False
        
        while i < len(sql_content):
            char = sql_content[i]
            
            if not in_quote and not in_comment and sql_content[i:i+2] == '/*':
                in_comment = True
                i += 2
                continue
            
            if in_comment and sql_content[i:i+2] == '*/':
                in_comment = False
                i += 2
                continue
            
            if in_comment:
                i += 1
                continue
            
            if char in ("'", '"') and not in_quote:
                in_quote = True
                quote_char = char
            elif in_quote and char == quote_char:
                if i + 1 < len(sql_content) and sql_content[i + 1] == quote_char:
                    result.append(char)
                    i += 1
                else:
                    in_quote = False
                    quote_char = None
            
            result.append(char)
            i += 1
        
        return ''.join(result)


class PostgreSqlSplitter(BaseSqlSplitter):
    """
    Splitter pour PostgreSQL/MySQL.
    
    Gère les blocs Dollar-Quoted ($$...$$, $tag$...$tag$),
    les chaînes quotées et les commentaires.
    """
    
    def split(self, sql_content: str) -> List[str]:
        """Découpe le SQL PostgreSQL en instructions."""
        sql_content = self._remove_single_line_comments(sql_content)
        sql_content = self._remove_multiline_comments(sql_content)
        
        statements = []
        current_stmt = []
        in_quote = False
        quote_char = None
        in_dollar_block = False
        dollar_tag = None
        
        i = 0
        while i < len(sql_content):
            char = sql_content[i]
            
            # Gestion des Dollar-Quoted Strings
            if char == '$' and not in_quote:
                match = re.match(r'\$([A-Za-z_]*)\$', sql_content[i:])
                if match:
                    tag = match.group(0)
                    
                    if not in_dollar_block:
                        in_dollar_block = True
                        dollar_tag = tag
                        current_stmt.append(tag)
                        i += len(tag)
                        continue
                    elif tag == dollar_tag:
                        in_dollar_block = False
                        dollar_tag = None
                        current_stmt.append(tag)
                        i += len(tag)
                        continue
            
            # Gestion des quotes standards
            if char in ("'", '"') and not in_dollar_block:
                if not in_quote:
                    in_quote = True
                    quote_char = char
                elif char == quote_char:
                    if i + 1 < len(sql_content) and sql_content[i + 1] == quote_char:
                        current_stmt.append(char)
                        current_stmt.append(char)
                        i += 2
                        continue
                    else:
                        in_quote = False
                        quote_char = None
            
            # Découpage au point-virgule
            if char == ';' and not in_quote and not in_dollar_block:
                stmt_text = ''.join(current_stmt).strip()
                if stmt_text:
                    statements.append(stmt_text)
                current_stmt = []
            else:
                current_stmt.append(char)
            
            i += 1
        
        # Dernière instruction
        last_stmt = ''.join(current_stmt).strip()
        if last_stmt:
            statements.append(last_stmt)
        
        logger.debug(f"{len(statements)} instruction(s) PostgreSQL détectée(s)")
        return statements


class SqlServerSplitter(BaseSqlSplitter):
    """
    Splitter pour SQL Server.
    
    Utilise GO comme séparateur de batch.
    """
    
    def split(self, sql_content: str) -> List[str]:
        """Découpe le SQL Server en batches."""
        sql_content = re.sub(r'--[^\n]*', '', sql_content)
        sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
        
        statements = re.split(r'\bGO\b', sql_content, flags=re.IGNORECASE)
        statements = [stmt.strip() for stmt in statements if stmt.strip()]
        
        logger.debug(f"{len(statements)} batch(es) SQL Server détecté(s)")
        return statements


class OracleSplitter(BaseSqlSplitter):
    """
    Splitter pour Oracle.
    
    Gère les blocs PL/SQL et le séparateur /.
    """
    
    def split(self, sql_content: str) -> List[str]:
        """Découpe le SQL Oracle en instructions."""
        sql_content = re.sub(r'--[^\n]*', '', sql_content)
        sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
        
        statements = []
        current_stmt = []
        in_plsql_block = False
        block_depth = 0
        
        tokens = re.split(r'(\s+|;|/)', sql_content)
        
        for token in tokens:
            upper_token = token.upper().strip()
            
            if upper_token in ('BEGIN', 'DECLARE'):
                in_plsql_block = True
                block_depth += 1
            
            if upper_token == 'END' and in_plsql_block:
                block_depth -= 1
                if block_depth <= 0:
                    in_plsql_block = False
                    block_depth = 0
            
            if token == '/' and not in_plsql_block:
                stmt_text = ''.join(current_stmt).strip()
                if stmt_text:
                    statements.append(stmt_text)
                current_stmt = []
                continue
            
            if token == ';' and not in_plsql_block:
                stmt_text = ''.join(current_stmt).strip()
                if stmt_text:
                    statements.append(stmt_text)
                current_stmt = []
                continue
            
            current_stmt.append(token)
        
        last_stmt = ''.join(current_stmt).strip()
        if last_stmt:
            statements.append(last_stmt)
        
        logger.debug(f"{len(statements)} instruction(s) Oracle détectée(s)")
        return statements


class SimpleSplitter(BaseSqlSplitter):
    """Splitter simple par point-virgule (fallback)."""
    
    def split(self, sql_content: str) -> List[str]:
        """Découpe simple par point-virgule."""
        sql_content = re.sub(r'--[^\n]*', '', sql_content)
        sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
        
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        logger.debug(f"{len(statements)} instruction(s) SQL détectée(s)")
        return statements


def get_splitter(db_type: str) -> BaseSqlSplitter:
    """
    Factory pour obtenir le splitter approprié.
    
    Args:
        db_type: Type de base (postgresql, oracle, sqlserver, mysql)
        
    Returns:
        Instance du splitter approprié
    """
    splitters = {
        'postgresql': PostgreSqlSplitter,
        'mysql': PostgreSqlSplitter,  # Même logique que PostgreSQL
        'sqlserver': SqlServerSplitter,
        'oracle': OracleSplitter,
    }
    
    splitter_class = splitters.get(db_type, SimpleSplitter)
    return splitter_class()
