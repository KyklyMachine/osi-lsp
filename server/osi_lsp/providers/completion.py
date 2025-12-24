"""Completion provider for Protocol Language"""

from typing import List
from lsprotocol.types import CompletionItem, CompletionItemKind, CompletionList
from ..analysis.symbol_table import SymbolTable


class CompletionProvider:
    """Provides autocompletion suggestions"""

    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table

    def get_completions(self, line: str, character: int) -> CompletionList:
        """Get completion suggestions based on context"""
        items: List[CompletionItem] = []

        # Get context (what comes before cursor)
        prefix = line[:character] if character <= len(line) else line

        # Keywords and operators
        # insert_text is set to label to avoid replacing with full template
        keywords = [
            ("declare", CompletionItemKind.Keyword, "Declare a variable", "declare"),
            ("varset", CompletionItemKind.Keyword, "Assign value to variable", "varset"),
            ("goto", CompletionItemKind.Keyword, "Unconditional jump", "goto"),
            ("if", CompletionItemKind.Keyword, "Conditional jump", "if"),
            ("return", CompletionItemKind.Keyword, "Return from handler", "return"),
        ]

        operators = [
            ("bufferit", CompletionItemKind.Function, "Create buffer", "bufferit"),
            ("unbufferit", CompletionItemKind.Function, "Parse buffer", "unbufferit"),
            ("calccrc", CompletionItemKind.Function, "Calculate CRC", "calccrc"),
            ("timer", CompletionItemKind.Function, "Set timer", "timer"),
            ("untimer", CompletionItemKind.Function, "Cancel timer", "untimer"),
            ("queue", CompletionItemKind.Function, "Add to queue", "queue"),
            ("clearqueue", CompletionItemKind.Function, "Clear queue", "clearqueue"),
            ("dequeue", CompletionItemKind.Function, "Remove from queue", "dequeue"),
            ("peek", CompletionItemKind.Function, "Peek at queue", "peek"),
            ("qcount", CompletionItemKind.Function, "Queue count", "qcount"),
            ("generateup", CompletionItemKind.Function, "Generate event up", "generateup"),
            ("eventdown", CompletionItemKind.Function, "Send event down", "eventdown"),
            ("out", CompletionItemKind.Function, "Debug output", "out"),
            ("subprog", CompletionItemKind.Function, "Call subroutine", "subprog"),
            ("substart", CompletionItemKind.Function, "Start subroutine", "substart"),
            ("subend", CompletionItemKind.Keyword, "End subroutine", "subend"),
            ("delete", CompletionItemKind.Function, "Delete substring", "delete"),
        ]

        types = [
            ("integer", CompletionItemKind.TypeParameter, "Integer type", "integer"),
            ("buffer", CompletionItemKind.TypeParameter, "Buffer type", "buffer"),
            ("string", CompletionItemKind.TypeParameter, "String type", "string"),
            ("queue", CompletionItemKind.TypeParameter, "Queue type", "queue"),
        ]

        functions = [
            ("sizeof", CompletionItemKind.Function, "Get size", "sizeof"),
            ("copy", CompletionItemKind.Function, "Copy substring", "copy"),
            ("pos", CompletionItemKind.Function, "Find substring", "pos"),
            ("locguide", CompletionItemKind.Function, "Location guide", "locguide"),
            ("CurrentSystemName", CompletionItemKind.Function, "Get system name", "CurrentSystemName"),
        ]

        # Check context to provide relevant suggestions
        if "declare" in prefix:
            # After declare, suggest types
            for label, kind, detail, insert_text in types:
                items.append(CompletionItem(
                    label=label,
                    kind=kind,
                    detail=detail,
                    insert_text=insert_text
                ))
        else:
            # Add all keywords and operators
            for label, kind, detail, insert_text in keywords + operators + functions:
                items.append(CompletionItem(
                    label=label,
                    kind=kind,
                    detail=detail,
                    insert_text=insert_text
                ))

        # Add variables from symbol table
        for symbol in self.symbol_table.get_all_symbols():
            items.append(CompletionItem(
                label=f"${symbol.name}",
                kind=CompletionItemKind.Variable,
                detail=f"{symbol.symbol_type.value} variable",
                insert_text=f"${symbol.name}"
            ))

        # Add labels
        for label in self.symbol_table.get_all_labels():
            items.append(CompletionItem(
                label=label.name,
                kind=CompletionItemKind.Constant,
                detail="Label",
                insert_text=label.name
            ))

        # Add subroutines
        for subroutine in self.symbol_table.get_all_subroutines():
            items.append(CompletionItem(
                label=subroutine.name,
                kind=CompletionItemKind.Function,
                detail="Subroutine",
                insert_text=subroutine.name
            ))

        # Add handlers
        for handler in self.symbol_table.get_all_handlers():
            items.append(CompletionItem(
                label=handler.name,
                kind=CompletionItemKind.Event,
                detail="Event Handler",
                insert_text=handler.name
            ))

        return CompletionList(is_incomplete=False, items=items)
