"""Symbol table for Protocol Language"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum


class SymbolType(Enum):
    """Variable types in Protocol Language"""
    INTEGER = "integer"
    BUFFER = "buffer"
    STRING = "string"
    QUEUE = "queue"
    UNKNOWN = "unknown"


@dataclass
class Symbol:
    """Symbol (variable) information"""
    name: str
    symbol_type: SymbolType
    line: int
    column: int
    file_uri: str = ""
    initialized: bool = False
    used: bool = False
    references: List[tuple[int, int]] = field(default_factory=list)  # (line, column) pairs

    def add_reference(self, line: int, column: int):
        """Add a reference to this symbol"""
        self.references.append((line, column))


@dataclass
class Label:
    """Label information"""
    name: str
    line: int
    column: int
    file_uri: str = ""
    used: bool = False
    references: List[tuple[int, int]] = field(default_factory=list)

    def add_reference(self, line: int, column: int):
        """Add a reference to this label"""
        self.references.append((line, column))


@dataclass
class Subroutine:
    """Subroutine information"""
    name: str
    line: int
    column: int
    file_uri: str = ""
    used: bool = False
    references: List[tuple[int, int]] = field(default_factory=list)

    def add_reference(self, line: int, column: int):
        """Add a reference to this subroutine"""
        self.references.append((line, column))


@dataclass
class HandlerSymbol:
    """Handler information"""
    name: str
    file_uri: str = ""
    parameters: List[str] = field(default_factory=list)
    line: int = 0
    column: int = 0


class SymbolTable:
    """Symbol table for tracking variables, labels, subroutines, etc."""

    def __init__(self, parent: Optional['SymbolTable'] = None):
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        self.labels: Dict[str, Label] = {}
        self.subroutines: Dict[str, Subroutine] = {}
        self.handlers: Dict[str, HandlerSymbol] = {}

    def declare_symbol(self, name: str, symbol_type: SymbolType, line: int, column: int, file_uri: str = "") -> bool:
        """
        Declare a variable.
        Returns True if successful, False if already declared.
        """
        if name in self.symbols:
            return False

        self.symbols[name] = Symbol(name, symbol_type, line, column, file_uri=file_uri)
        return True

    def get_symbol(self, name: str) -> Optional[Symbol]:
        """Get symbol information"""
        symbol = self.symbols.get(name)
        if symbol:
            return symbol
        if self.parent:
            return self.parent.get_symbol(name)
        return None

    def use_symbol(self, name: str, line: int, column: int) -> bool:
        """
        Mark symbol as used and add reference.
        Returns True if symbol exists, False otherwise.
        """
        if name in self.symbols:
            self.symbols[name].used = True
            self.symbols[name].add_reference(line, column)
            return True
        
        if self.parent:
            return self.parent.use_symbol(name, line, column)
            
        return False

    def initialize_symbol(self, name: str):
        """Mark symbol as initialized"""
        if name in self.symbols:
            self.symbols[name].initialized = True
            return

        if self.parent:
            self.parent.initialize_symbol(name)

    def declare_label(self, name: str, line: int, column: int, file_uri: str = "") -> bool:
        """
        Declare a label.
        Returns True if successful, False if already declared.
        """
        if name in self.labels:
            return False

        self.labels[name] = Label(name, line, column, file_uri=file_uri)
        return True

    def get_label(self, name: str) -> Optional[Label]:
        """Get label information"""
        return self.labels.get(name)

    def use_label(self, name: str, line: int, column: int) -> bool:
        """
        Mark label as used and add reference.
        Returns True if label exists, False otherwise.
        """
        if name in self.labels:
            self.labels[name].used = True
            self.labels[name].add_reference(line, column)
            return True
        return False

    def declare_subroutine(self, name: str, line: int, column: int, file_uri: str = "") -> bool:
        """
        Declare a subroutine.
        Returns True if successful, False if already declared.
        """
        if name in self.subroutines:
            return False

        self.subroutines[name] = Subroutine(name, line, column, file_uri=file_uri)
        return True

    def get_subroutine(self, name: str) -> Optional[Subroutine]:
        """Get subroutine information"""
        return self.subroutines.get(name)

    def use_subroutine(self, name: str, line: int, column: int) -> bool:
        """
        Mark subroutine as used and add reference.
        Returns True if subroutine exists, False otherwise.
        """
        if name in self.subroutines:
            self.subroutines[name].used = True
            self.subroutines[name].add_reference(line, column)
            return True
        return False
        
    def declare_handler(self, name: str, file_uri: str, parameters: List[str] = None) -> bool:
        """Declare a handler (usually from file scan)"""
        if name in self.handlers:
            return False
        self.handlers[name] = HandlerSymbol(name, file_uri, parameters or [])
        return True

    def get_handler(self, name: str) -> Optional[HandlerSymbol]:
        """Get handler information"""
        handler = self.handlers.get(name)
        if handler:
            return handler
        if self.parent:
            return self.parent.get_handler(name)
        return None

    def get_all_handlers(self) -> List[HandlerSymbol]:
        """Get all handlers (local + parent)"""
        handlers_map = {name: h for name, h in self.handlers.items()}
        if self.parent:
            parent_handlers = self.parent.get_all_handlers()
            for h in parent_handlers:
                if h.name not in handlers_map:
                    handlers_map[h.name] = h
        return list(handlers_map.values())

    def get_unused_symbols(self) -> List[Symbol]:
        """Get list of declared but unused symbols"""
        return [s for s in self.symbols.values() if not s.used]

    def get_unused_labels(self) -> List[Label]:
        """Get list of declared but unused labels"""
        return [l for l in self.labels.values() if not l.used]

    def get_unused_subroutines(self) -> List[Subroutine]:
        """Get list of declared but unused subroutines"""
        return [s for s in self.subroutines.values() if not s.used]

    def get_uninitialized_symbols(self) -> List[Symbol]:
        """Get list of symbols that are used but not initialized"""
        return [s for s in self.symbols.values() if s.used and not s.initialized]

    def get_all_symbols(self) -> List[Symbol]:
        """Get all symbols (local and parent)"""
        # Start with local symbols
        symbols_map = {name: symbol for name, symbol in self.symbols.items()}
        
        # Add parent symbols if not already present (shadowing)
        if self.parent:
            parent_symbols = self.parent.get_all_symbols()
            for symbol in parent_symbols:
                if symbol.name not in symbols_map:
                    symbols_map[symbol.name] = symbol
                    
        return list(symbols_map.values())

    def get_all_labels(self) -> List[Label]:
        """Get all labels"""
        return list(self.labels.values())

    def get_all_subroutines(self) -> List[Subroutine]:
        """Get all subroutines"""
        return list(self.subroutines.values())

    def clear(self):
        """Clear all symbols"""
        self.symbols.clear()
        self.labels.clear()
        self.subroutines.clear()

