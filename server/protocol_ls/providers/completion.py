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
        keywords = [
            ("declare", CompletionItemKind.Keyword, "Declare a variable", "name declare type"),
            ("varset", CompletionItemKind.Keyword, "Assign value to variable", "expression varset $variable"),
            ("goto", CompletionItemKind.Keyword, "Unconditional jump", "goto label"),
            ("if", CompletionItemKind.Keyword, "Conditional jump", "condition if label"),
            ("return", CompletionItemKind.Keyword, "Return from handler", "return"),
        ]

        operators = [
            ("bufferit", CompletionItemKind.Function, "Create buffer", "buffer bufferit length field1 len1 ..."),
            ("unbufferit", CompletionItemKind.Function, "Parse buffer", "unbufferit buffer var1 len1 ..."),
            ("calccrc", CompletionItemKind.Function, "Calculate CRC", "calccrc $result $buffer"),
            ("timer", CompletionItemKind.Function, "Set timer", "EVENT timer $timer_var delay ..."),
            ("untimer", CompletionItemKind.Function, "Cancel timer", "untimer $timer_id"),
            ("queue", CompletionItemKind.Function, "Add to queue", "queue_name queue value"),
            ("clearqueue", CompletionItemKind.Function, "Clear queue", "clearqueue queue_name"),
            ("dequeue", CompletionItemKind.Function, "Remove from queue", "dequeue(queue_name)"),
            ("peek", CompletionItemKind.Function, "Peek at queue", "peek(queue_name)"),
            ("qcount", CompletionItemKind.Function, "Queue count", "qcount(queue_name)"),
            ("generateup", CompletionItemKind.Function, "Generate event up", "EVENT generateup param value ..."),
            ("eventdown", CompletionItemKind.Function, "Send event down", "EVENT eventdown param value ..."),
            ("out", CompletionItemKind.Function, "Debug output", "out expression"),
            ("subprog", CompletionItemKind.Function, "Call subroutine", "subprog name"),
            ("substart", CompletionItemKind.Function, "Start subroutine", "substart name ... subend"),
            ("subend", CompletionItemKind.Keyword, "End subroutine", "subend"),
            ("delete", CompletionItemKind.Function, "Delete substring", "delete string start length"),
        ]

        types = [
            ("integer", CompletionItemKind.TypeParameter, "Integer type", "name declare integer"),
            ("buffer", CompletionItemKind.TypeParameter, "Buffer type", "name declare buffer"),
            ("string", CompletionItemKind.TypeParameter, "String type", "name declare string"),
            ("queue", CompletionItemKind.TypeParameter, "Queue type", "name declare queue"),
        ]

        functions = [
            ("sizeof", CompletionItemKind.Function, "Get size", "sizeof($variable)"),
            ("copy", CompletionItemKind.Function, "Copy substring", "copy($string, start, length)"),
            ("pos", CompletionItemKind.Function, "Find substring", "pos($substring, $string)"),
            ("locguide", CompletionItemKind.Function, "Location guide", "locguide($string)"),
            ("CurrentSystemName", CompletionItemKind.Function, "Get system name", "CurrentSystemName()"),
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
