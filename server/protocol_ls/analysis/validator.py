"""Validator for generating diagnostics"""

from typing import List
from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range

from ..parser.ast_nodes import Program
from .symbol_table import SymbolTable
from .semantic_analyzer import SemanticAnalyzer


class Validator:
    """Validator for generating LSP diagnostics"""

    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.diagnostics: List[Diagnostic] = []

    def validate(self, ast: Program) -> List[Diagnostic]:
        """
        Validate the AST and generate diagnostics.
        Returns a list of Diagnostic objects for LSP.
        """
        self.diagnostics = []

        if not ast:
            return self.diagnostics

        # Run semantic analyzer
        analyzer = SemanticAnalyzer(self.symbol_table)
        analyzer.analyze(ast)

        # Convert errors to diagnostics
        for error in analyzer.errors:
            self._add_diagnostic_from_message(error, DiagnosticSeverity.Error)

        # Convert warnings to diagnostics
        for warning in analyzer.warnings:
            self._add_diagnostic_from_message(warning, DiagnosticSeverity.Warning)

        # Check for unused symbols
        for symbol in self.symbol_table.get_unused_symbols():
            self.diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=symbol.line, character=symbol.column),
                        end=Position(line=symbol.line, character=symbol.column + len(symbol.name))
                    ),
                    message=f"Variable '{symbol.name}' is declared but never used",
                    severity=DiagnosticSeverity.Warning,
                    source="protocol-ls"
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
                    source="protocol-ls"
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
                    source="protocol-ls"
                )
            )

        # Check for uninitialized variables
        for symbol in self.symbol_table.get_uninitialized_symbols():
            self.diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=symbol.line, character=symbol.column),
                        end=Position(line=symbol.line, character=symbol.column + len(symbol.name))
                    ),
                    message=f"Variable '{symbol.name}' may be used before being initialized",
                    severity=DiagnosticSeverity.Warning,
                    source="protocol-ls"
                )
            )

        return self.diagnostics

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
                        source="protocol-ls"
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
                    source="protocol-ls"
                )
            )
