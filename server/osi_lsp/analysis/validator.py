"""Validator for generating diagnostics"""

import os
from typing import List
from urllib.parse import unquote, urlparse
from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range

from ..parser.ast_nodes import Program, DeclareStatement, LabelStatement, ReturnStatement
from .symbol_table import SymbolTable
from .semantic_analyzer import SemanticAnalyzer


class Validator:
    """Validator for generating LSP diagnostics"""

    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.diagnostics: List[Diagnostic] = []

    def validate(self, ast: Program, file_uri: str, valid_init: bool = True) -> List[Diagnostic]:
        """
        Validate the AST and generate diagnostics.
        Returns a list of Diagnostic objects for LSP.
        """
        self.diagnostics = []

        if not ast:
            return self.diagnostics

        # Get filename and check type
        try:
            file_path = unquote(urlparse(file_uri).path)
            # Handle Windows paths if necessary (remove leading /)
            if os.name == 'nt' and file_path.startswith('/'):
                 file_path = file_path[1:]
            filename = os.path.basename(file_path)
        except Exception:
            filename = "unknown"
            
        is_init = filename == "INIT.osi"

        # Check INIT.osi existence
        if not is_init and not valid_init:
             self.diagnostics.append(
                Diagnostic(
                    range=Range(start=Position(line=0, character=0), end=Position(line=0, character=0)),
                    message="Directory must contain INIT.osi file",
                    severity=DiagnosticSeverity.Error,
                    source="osi-ls"
                )
            )

        # Structure checks
        self._validate_structure(ast, is_init, filename)

        # Run semantic analyzer
        analyzer = SemanticAnalyzer(self.symbol_table, file_uri=file_uri)
        analyzer.analyze(ast)

        # Convert errors to diagnostics
        for error in analyzer.errors:
            self._add_diagnostic_from_message(error, DiagnosticSeverity.Error)

        # Convert warnings to diagnostics
        for warning in analyzer.warnings:
            self._add_diagnostic_from_message(warning, DiagnosticSeverity.Warning)

        # Skip usage checks for INIT.osi (global vars usage requires full project scan)
        if not is_init:
            # Check for unused symbols (local declarations)
            for symbol in self.symbol_table.get_unused_symbols():
                # Only report if it's not from parent (INIT.osi)
                # But get_unused_symbols() returns declarations from THIS table.
                # Since SymbolTable for handler has parent, declare_symbol goes to self.symbols.
                # So this is correct for local vars.
                self.diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=symbol.line, character=symbol.column),
                            end=Position(line=symbol.line, character=symbol.column + len(symbol.name))
                        ),
                        message=f"Variable '{symbol.name}' is declared but never used",
                        severity=DiagnosticSeverity.Warning,
                        source="osi-ls"
                    )
                )

            # Check for unused labels
            for label in self.symbol_table.get_unused_labels():
                self.diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=label.line, character=label.column),
                            end=Position(line=label.line, character=label.column + len(label.name))
                        ),
                        message=f"Label '{label.name}' is defined but never used",
                        severity=DiagnosticSeverity.Warning,
                        source="osi-ls"
                    )
                )

            # Check for unused subroutines
            for subroutine in self.symbol_table.get_unused_subroutines():
                self.diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=subroutine.line, character=subroutine.column),
                            end=Position(line=subroutine.line, character=subroutine.column + len(subroutine.name))
                        ),
                        message=f"Subroutine '{subroutine.name}' is defined but never called",
                        severity=DiagnosticSeverity.Warning,
                        source="osi-ls"
                    )
                )

            # Check for uninitialized variables
            for symbol in self.symbol_table.get_uninitialized_symbols():
                 # Check if it is local. If it is from parent, we assume it is initialized in INIT?
                 # No, vars in INIT are just declared. They are initialized by assignment.
                 # But we might use them before assignment in handler if they were assigned in another handler.
                 # Flow analysis for global vars is complex.
                 # For now, let's keep it simple.
                self.diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=symbol.line, character=symbol.column),
                            end=Position(line=symbol.line, character=symbol.column + len(symbol.name))
                        ),
                        message=f"Variable '{symbol.name}' may be used before being initialized",
                        severity=DiagnosticSeverity.Warning,
                        source="osi-ls"
                    )
                )

        return self.diagnostics

    def _validate_structure(self, ast: Program, is_init: bool, filename: str):
        """Validate file structure rules"""
        
        has_executable_code = False
        handler_label_found = False
        
        # Helper to check for executable statements
        def is_executable(stmt):
            return not isinstance(stmt, (DeclareStatement, LabelStatement)) # Label is structural

        for stmt in ast.statements:
            if isinstance(stmt, DeclareStatement):
                if not is_init:
                    self._add_diagnostic(stmt, "Variable declarations are only allowed in INIT.osi", DiagnosticSeverity.Error)
            
            if is_executable(stmt):
                has_executable_code = True
                
            if isinstance(stmt, LabelStatement):
                # Check handler name matching filename (without extension)
                # Spec says: "Handler label (matches filename)"
                expected_name = os.path.splitext(filename)[0]
                if stmt.name == expected_name:
                    handler_label_found = True
                # If it's a handler file, the FIRST label usually denotes the handler.
                # Or we can just check if ANY label matches.
                # Spec: "Handler name MUST match filename"
        
        if is_init:
            if has_executable_code:
                 # We can't easily point to "all code", but we can flag the file
                 # Or better, flag the first executable statement?
                 # Loop again to find first
                 for stmt in ast.statements:
                     if is_executable(stmt):
                         self._add_diagnostic(stmt, "INIT.osi cannot contain executable code", DiagnosticSeverity.Error)
                         break
        else:
            if not handler_label_found and filename != "unknown":
                 expected_name = os.path.splitext(filename)[0]
                 self.diagnostics.append(
                    Diagnostic(
                        range=Range(start=Position(0,0), end=Position(0,0)),
                        message=f"Handler name must match filename '{expected_name}'",
                        severity=DiagnosticSeverity.Error,
                        source="osi-ls"
                    )
                )
            
            # Check for return statement
            # Spec: "Handler should end with 'return' statement" (Warning)
            # We check if the last statement is return.
            if ast.statements:
                last_stmt = ast.statements[-1]
                if not isinstance(last_stmt, ReturnStatement):
                     self.diagnostics.append(
                        Diagnostic(
                            range=Range(
                                start=Position(line=last_stmt.line, character=last_stmt.column),
                                end=Position(line=last_stmt.line, character=last_stmt.column + 5)
                            ),
                            message="Handler should end with 'return' statement",
                            severity=DiagnosticSeverity.Warning,
                            source="osi-ls"
                        )
                    )

    def _add_diagnostic(self, node, message, severity):
        self.diagnostics.append(
            Diagnostic(
                range=Range(
                    start=Position(line=node.line, character=node.column),
                    end=Position(line=node.line, character=node.column + 10)
                ),
                message=message,
                severity=severity,
                source="osi-ls"
            )
        )

    def _add_diagnostic_from_message(self, message: str, severity: DiagnosticSeverity):
        """
        Parse error/warning message and create diagnostic.
        Expected format: "line:column: message"
        """
        try:
            parts = message.split(":", 2)
            if len(parts) >= 3:
                line = int(parts[0])
                column = int(parts[1])
                msg = parts[2].strip()

                self.diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=line, character=column),
                            end=Position(line=line, character=column + 10)  # Arbitrary length
                        ),
                        message=msg,
                        severity=severity,
                        source="osi-ls"
                    )
                )
        except (ValueError, IndexError):
            # If parsing fails, create a generic diagnostic at line 0
            self.diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=0, character=0),
                        end=Position(line=0, character=0)
                    ),
                    message=message,
                    severity=severity,
                    source="osi-ls"
                )
            )