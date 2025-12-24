import os
import logging
from pathlib import Path
from typing import Dict, Optional
from ..parser.lexer import Lexer
from ..parser.parser import Parser
from ..analysis.symbol_table import SymbolTable
from ..analysis.semantic_analyzer import SemanticAnalyzer

logger = logging.getLogger(__name__)

class DirectoryContext:
    def __init__(self, path: str):
        self.path = path
        self.init_file: Optional[str] = None
        self.symbol_table = SymbolTable() # Table for INIT.osi (Global Scope)
        self.valid_init = False

class OSIProject:
    def __init__(self):
        self.directories: Dict[str, DirectoryContext] = {}

    def get_directory_context(self, file_path: str) -> DirectoryContext:
        """Get or create directory context for a file"""
        dir_path = os.path.dirname(file_path)
        if dir_path not in self.directories:
            self.directories[dir_path] = DirectoryContext(dir_path)
            self._load_init_file(dir_path)
        return self.directories[dir_path]

    def reload_init_file(self, dir_path: str):
        """Reload INIT.osi for a directory"""
        if dir_path in self.directories:
            # Clear existing table
            self.directories[dir_path].symbol_table.clear()
            self._load_init_file(dir_path)

    def _load_init_file(self, dir_path: str):
        """Load and parse INIT.osi if it exists"""
        context = self.directories[dir_path]
        
        # Scan for handlers
        try:
            import glob
            osi_files = glob.glob(os.path.join(dir_path, "*.osi"))
            for f in osi_files:
                name = os.path.splitext(os.path.basename(f))[0]
                if name != "INIT":
                    # Convert file path to URI
                    uri = Path(f).resolve().as_uri()
                    context.symbol_table.declare_handler(name, uri)
        except Exception as e:
            logger.error(f"Error scanning handlers in {dir_path}: {e}")

        init_path = os.path.abspath(os.path.join(dir_path, "INIT.osi"))
        
        if os.path.exists(init_path):
            context.init_file = init_path
            try:
                with open(init_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # Parse
                lexer = Lexer(text)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast, _ = parser.parse()
                
                # Build Symbol Table using SemanticAnalyzer
                if ast:
                    init_uri = Path(init_path).resolve().as_uri()
                    analyzer = SemanticAnalyzer(context.symbol_table, file_uri=init_uri)
                    analyzer.visit_program(ast)
                    
                    # Mark all global variables as initialized
                    for symbol in context.symbol_table.symbols.values():
                        symbol.initialized = True
                        
                    context.valid_init = True
                else:
                    context.valid_init = False
                
            except Exception as e:
                logger.error(f"Error loading INIT.osi at {init_path}: {e}")
                context.valid_init = False
        else:
            context.valid_init = False
