"""Definition provider for Protocol Language"""

from typing import Optional, List
from lsprotocol.types import Location, Position, Range
from ..analysis.symbol_table import SymbolTable


class DefinitionProvider:
    """Provides 'Go to Definition' functionality"""

    def __init__(self, symbol_table: SymbolTable, uri: str):
        self.symbol_table = symbol_table
        self.uri = uri

    def get_definition(self, word: str) -> Optional[Location]:
        """Get the definition location for a word"""
        if not word:
            return None

        # Remove $ prefix if present
        var_name = word[1:] if word.startswith('$') else word

        # Check if it's a variable
        symbol = self.symbol_table.get_symbol(var_name)
        if symbol:
            uri = symbol.file_uri if symbol.file_uri else self.uri
            return Location(
                uri=uri,
                range=Range(
                    start=Position(line=symbol.line, character=symbol.column),
                    end=Position(line=symbol.line, character=symbol.column + len(symbol.name))
                )
            )

        # Check if it's a label
        label = self.symbol_table.get_label(var_name)
        if label:
            uri = label.file_uri if label.file_uri else self.uri
            return Location(
                uri=uri,
                range=Range(
                    start=Position(line=label.line, character=label.column),
                    end=Position(line=label.line, character=label.column + len(label.name))
                )
            )

        # Check if it's a subroutine
        subroutine = self.symbol_table.get_subroutine(var_name)
        if subroutine:
            uri = subroutine.file_uri if subroutine.file_uri else self.uri
            return Location(
                uri=uri,
                range=Range(
                    start=Position(line=subroutine.line, character=subroutine.column),
                    end=Position(line=subroutine.line, character=subroutine.column + len(subroutine.name))
                )
            )

        # Check if it's a handler
        handler = self.symbol_table.get_handler(var_name)
        if handler:
            # Use handler's file URI if available, otherwise current URI
            uri = handler.file_uri if handler.file_uri else self.uri
            # Use urlparse to handle file:/// vs path
            # But Location expects string URI.
            # If we scanned file, we stored path. We might need to convert to URI.
            from urllib.request import pathname2url
            if uri and not uri.startswith('file://'):
                 uri = 'file://' + pathname2url(uri)
                 
            return Location(
                uri=uri,
                range=Range(
                    start=Position(line=handler.line, character=handler.column),
                    end=Position(line=handler.line, character=handler.column + len(handler.name))
                )
            )

        return None

    def get_references(self, word: str) -> List[Location]:
        """Get all references to a symbol"""
        if not word:
            return []

        var_name = word[1:] if word.startswith('$') else word
        locations = []

        # Check if it's a variable
        symbol = self.symbol_table.get_symbol(var_name)
        if symbol:
            # Add definition
            def_uri = symbol.file_uri if symbol.file_uri else self.uri
            locations.append(Location(
                uri=def_uri,
                range=Range(
                    start=Position(line=symbol.line, character=symbol.column),
                    end=Position(line=symbol.line, character=symbol.column + len(symbol.name))
                )
            ))

            # Add all references (references are always in the current file because we don't have project-wide ref tracking yet)
            for ref_line, ref_col in symbol.references:
                locations.append(Location(
                    uri=self.uri,
                    range=Range(
                        start=Position(line=ref_line, character=ref_col),
                        end=Position(line=ref_line, character=ref_col + len(symbol.name))
                    )
                ))

        # Check if it's a label
        label = self.symbol_table.get_label(var_name)
        if label:
            # Add definition
            def_uri = label.file_uri if label.file_uri else self.uri
            locations.append(Location(
                uri=def_uri,
                range=Range(
                    start=Position(line=label.line, character=label.column),
                    end=Position(line=label.line, character=label.column + len(label.name))
                )
            ))

            # Add all references
            for ref_line, ref_col in label.references:
                locations.append(Location(
                    uri=self.uri,
                    range=Range(
                        start=Position(line=ref_line, character=ref_col),
                        end=Position(line=ref_line, character=ref_col + len(label.name))
                    )
                ))

        return locations
