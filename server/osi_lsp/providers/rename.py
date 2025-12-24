"""Rename provider for Protocol Language"""

from typing import Optional, List, Dict
from lsprotocol.types import WorkspaceEdit, TextEdit, Range, Position
from ..analysis.symbol_table import SymbolTable


class RenameProvider:
    """Provides rename refactoring functionality"""

    def __init__(self, symbol_table: SymbolTable, uri: str):
        self.symbol_table = symbol_table
        self.uri = uri

    def rename_symbol(self, word: str, new_name: str) -> Optional[WorkspaceEdit]:
        if not word:
            return None
            
        # Clean up names
        clean_word = word
        clean_new = new_name
        
        is_variable_ref = False
        if word.startswith('$'):
            clean_word = word[1:]
            is_variable_ref = True
            
        if clean_new.startswith('$'):
            clean_new = clean_new[1:]
        
        # Check if it's a variable (local or global)
        symbol = self.symbol_table.get_symbol(clean_word)
        if symbol:
            return self._create_edit_variable(symbol, clean_new)
            
        # Check if it's a label (local or global)
        label = self.symbol_table.get_label(clean_word)
        if label:
            return self._create_edit_label(label, clean_new)

        # Check if it's a subroutine (local or global)
        sub = self.symbol_table.get_subroutine(clean_word)
        if sub:
             return self._create_edit_label(sub, clean_new) # Logic is same as label
             
        return None

    def _get_combined_references(self, symbol) -> List[tuple[str, int, int]]:
        """
        Get all references for a symbol, combining global references
        with fresh local references from the current analysis.
        """
        # Start with references from the symbol (could be global or local)
        refs = list(symbol.references)
        
        # Check if we have fresh external references for this symbol in the local table
        # This happens when we analyze the current file without updating the global table
        if symbol.name in self.symbol_table.external_references:
            # If we have fresh local refs, we must discard any STALE refs for the current URI
            # that might exist in the global symbol.
            refs = [r for r in refs if r[0] != self.uri]
            
            # Add the fresh refs
            refs.extend(self.symbol_table.external_references[symbol.name])
            
        return refs

    def _create_edit_variable(self, symbol, new_name_clean: str) -> WorkspaceEdit:
        changes: Dict[str, List[TextEdit]] = {}
        old_len = len(symbol.name)
        
        # 1. Update Definition (Declaration)
        # Declaration is "name declare type". No $.
        # Use symbol.file_uri if available, otherwise fallback to current uri (should be available)
        def_uri = symbol.file_uri if symbol.file_uri else self.uri
        
        if def_uri not in changes:
            changes[def_uri] = []
            
        changes[def_uri].append(TextEdit(
            range=Range(
                start=Position(line=symbol.line, character=symbol.column),
                end=Position(line=symbol.line, character=symbol.column + old_len)
            ),
            new_text=new_name_clean
        ))

        # 2. Update References
        # References usage is "$name".
        # Reference position points to $.
        
        all_refs = self._get_combined_references(symbol)
        
        for ref_uri, ref_line, ref_col in all_refs:
            # Use provided URI or fallback to current
            target_uri = ref_uri if ref_uri else self.uri
            
            if target_uri not in changes:
                changes[target_uri] = []

            changes[target_uri].append(TextEdit(
                range=Range(
                    start=Position(line=ref_line, character=ref_col),
                    end=Position(line=ref_line, character=ref_col + old_len + 1) # +1 for $
                ),
                new_text=f"${new_name_clean}"
            ))
            
        return WorkspaceEdit(changes=changes)

    def _create_edit_label(self, symbol, new_name_clean: str) -> WorkspaceEdit:
        changes: Dict[str, List[TextEdit]] = {}
        old_len = len(symbol.name)
        
        # 1. Update Definition
        # "LABEL:" or "substart NAME"
        # In both cases, symbol.column points to start of name.
        def_uri = symbol.file_uri if symbol.file_uri else self.uri
        
        if def_uri not in changes:
            changes[def_uri] = []

        changes[def_uri].append(TextEdit(
            range=Range(
                start=Position(line=symbol.line, character=symbol.column),
                end=Position(line=symbol.line, character=symbol.column + old_len)
            ),
            new_text=new_name_clean
        ))

        # 2. Update References
        # "goto LABEL" or "subprog NAME"
        # Reference position points to start of name.
        
        all_refs = self._get_combined_references(symbol)

        for ref_uri, ref_line, ref_col in all_refs:
             target_uri = ref_uri if ref_uri else self.uri
             
             if target_uri not in changes:
                changes[target_uri] = []
                
             changes[target_uri].append(TextEdit(
                range=Range(
                    start=Position(line=ref_line, character=ref_col),
                    end=Position(line=ref_line, character=ref_col + old_len)
                ),
                new_text=new_name_clean
            ))
            
        return WorkspaceEdit(changes=changes)
