"""Document Symbol provider for Protocol Language"""

from typing import List, Optional
from lsprotocol.types import (
    DocumentSymbol,
    SymbolKind,
    Range,
    Position,
)
from ..parser.ast_nodes import (
    Program,
    Statement,
    DeclareStatement,
    LabelStatement,
    SubstartStatement,
    SubprogStatement,
    ASTVisitor
)


class DocumentSymbolProvider(ASTVisitor):
    """
    Visits the AST to produce a hierarchy of DocumentSymbols.
    """

    def __init__(self):
        self.symbols: List[DocumentSymbol] = []
        self._current_children: List[DocumentSymbol] = []

    def get_symbols(self, ast: Program) -> List[DocumentSymbol]:
        """Get document symbols from AST"""
        self.symbols = []
        if not ast:
            return []

        # We visit the program, which will populate self.symbols
        self.visit_program(ast)
        return self.symbols

    def visit_program(self, node: Program):
        for stmt in node.statements:
            self._visit_statement(stmt)

    def _visit_statement(self, stmt: Statement):
        """Dispatch based on statement type"""
        # We only care about declarations, labels, and subroutines for the outline
        if isinstance(stmt, DeclareStatement):
            self.visit_declare(stmt)
        elif isinstance(stmt, LabelStatement):
            self.visit_label(stmt)
        elif isinstance(stmt, SubstartStatement):
            self.visit_substart(stmt)
        # We can also add other things like buffers/timers if we want detailed outline

    def visit_declare(self, node: DeclareStatement):
        # Create symbol for variable declaration
        # Range: we only have start. specific end is missing.
        # We'll assume the declaration is on one line.
        start_pos = Position(line=node.line, character=node.column)
        # Approximate end: start + length of "name declare type"
        # Since we don't have the exact source text here, we'll just make it cover the name
        end_pos = Position(line=node.line, character=node.column + len(node.name) + 10) 
        
        symbol = DocumentSymbol(
            name=f"${node.name}",
            kind=SymbolKind.Variable,
            range=Range(start=start_pos, end=end_pos),
            selection_range=Range(start=start_pos, end=Position(line=node.line, character=node.column + len(node.name))),
            detail=node.var_type
        )
        self.symbols.append(symbol)

    def visit_label(self, node: LabelStatement):
        start_pos = Position(line=node.line, character=node.column)
        end_pos = Position(line=node.line, character=node.column + len(node.name) + 1) # +1 for colon

        symbol = DocumentSymbol(
            name=node.name,
            kind=SymbolKind.Key, # or Constant or Function
            range=Range(start=start_pos, end=end_pos),
            selection_range=Range(start=start_pos, end=end_pos),
            detail="Label"
        )
        self.symbols.append(symbol)

    def visit_substart(self, node: SubstartStatement):
        # Subroutine is a container
        start_pos = Position(line=node.line, character=node.column)
        
        # Determine end position based on children
        end_line = node.line
        end_char = node.column + len(node.name)
        
        if node.statements:
            last_stmt = node.statements[-1]
            end_line = last_stmt.line + 1 # Add one line buffer
            end_char = 0
        else:
            end_line = node.line + 1

        range_obj = Range(
            start=start_pos,
            end=Position(line=end_line, character=end_char)
        )
        
        # Create the symbol
        sub_symbol = DocumentSymbol(
            name=node.name,
            kind=SymbolKind.Function,
            range=range_obj,
            selection_range=Range(
                start=start_pos, 
                end=Position(line=node.line, character=node.column + len(node.name))
            ),
            detail="Subroutine",
            children=[]
        )

        # Recursively visit children
        # We need to temporarily redirect where new symbols are added
        # But wait, the visitor structure I made adds to self.symbols.
        # I need a way to collect children.
        
        # Save current context
        previous_symbols_list = self.symbols
        self.symbols = [] # New list for children
        
        # Visit children statements
        for stmt in node.statements:
            self._visit_statement(stmt)
            
        # Assign collected symbols as children
        sub_symbol.children = self.symbols
        
        # Restore context
        self.symbols = previous_symbols_list
        self.symbols.append(sub_symbol)

