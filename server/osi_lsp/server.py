"""Language Server for OSI Protocol Language"""

import logging
import os
from typing import Optional, Dict
from urllib.parse import unquote, urlparse
from lsprotocol.types import (
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_HOVER,
    TEXT_DOCUMENT_DEFINITION,
    TEXT_DOCUMENT_REFERENCES,
    CompletionParams,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DidCloseTextDocumentParams,
    HoverParams,
    DefinitionParams,
    ReferenceParams,
    CompletionList,
    Hover,
    Location,
    Diagnostic,
    DiagnosticSeverity,
    Range,
    Position,
)
from pygls.server import LanguageServer
from pygls.workspace import Document

from .parser.lexer import Lexer
from .parser.parser import Parser
from .parser.errors import ProtocolError
from .analysis.symbol_table import SymbolTable
from .analysis.validator import Validator
from .analysis.semantic_analyzer import SemanticAnalyzer
from .providers.completion import CompletionProvider
from .providers.hover import HoverProvider
from .providers.definition import DefinitionProvider
from .workspace.project import OSIProject

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OSILanguageServer(LanguageServer):
    """Language Server for OSI Protocol Language"""

    def __init__(self):
        super().__init__("osi-language-server", "v1.0.0")
        self.project = OSIProject()
        self.document_asts: Dict[str, any] = {}

    def get_symbol_table(self, uri: str) -> SymbolTable:
        """Get symbol table for a document (local + parent)"""
        # Get directory context
        file_path = unquote(urlparse(uri).path)
        # Handle Windows paths if necessary
        if os.name == 'nt' and file_path.startswith('/'):
            file_path = file_path[1:]
            
        context = self.project.get_directory_context(file_path)
        
        # Create local symbol table with parent
        symbol_table = SymbolTable(parent=context.symbol_table)
        return symbol_table

    def parse_document(self, document: Document) -> tuple[Optional[any], SymbolTable]:
        """Parse a document and return AST and symbol table"""
        try:
            symbol_table = self.get_symbol_table(document.uri)
            
            # Tokenize
            lexer = Lexer(document.source)
            tokens = lexer.tokenize()

            # Parse
            parser = Parser(tokens)
            ast = parser.parse()

            # Store AST
            self.document_asts[document.uri] = ast

            return ast, symbol_table

        except ProtocolError as e:
            # Re-raise to be handled by caller
            raise e
        except Exception as e:
            logger.error(f"Error parsing document {document.uri}: {e}", exc_info=True)
            # Return empty symbol table if parse failed completely
            return None, SymbolTable()

    def validate_document(self, uri: str, document: Document):
        """Validate document and publish diagnostics"""
        try:
            # Get directory context to check validity
            file_path = unquote(urlparse(uri).path)
            if os.name == 'nt' and file_path.startswith('/'):
                file_path = file_path[1:]
                
            context = self.project.get_directory_context(file_path)
            
            ast, symbol_table = self.parse_document(document)

            # Validate
            validator = Validator(symbol_table)
            diagnostics = validator.validate(ast, uri, context.valid_init)

            # Publish diagnostics
            self.publish_diagnostics(uri, diagnostics)

        except ProtocolError as e:
            # Create diagnostic for syntax error
            diagnostic = Diagnostic(
                range=Range(
                    start=Position(line=e.line, character=e.column),
                    end=Position(line=e.line, character=e.column + 1)
                ),
                message=e.message,
                severity=DiagnosticSeverity.Error,
                source="osi-ls"
            )
            self.publish_diagnostics(uri, [diagnostic])

        except Exception as e:
            logger.error(f"Error validating document {uri}: {e}", exc_info=True)


# Create server instance
server = OSILanguageServer()


@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: OSILanguageServer, params: DidOpenTextDocumentParams):
    """Handle document open event"""
    logger.info(f"Document opened: {params.text_document.uri}")
    document = ls.workspace.get_document(params.text_document.uri)
    ls.validate_document(params.text_document.uri, document)


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
async def did_change(ls: OSILanguageServer, params: DidChangeTextDocumentParams):
    """Handle document change event"""
    logger.info(f"Document changed: {params.text_document.uri}")
    document = ls.workspace.get_document(params.text_document.uri)
    
    # If INIT.osi changed, reload project context
    if params.text_document.uri.endswith("INIT.osi"):
        path = unquote(urlparse(params.text_document.uri).path)
        if os.name == 'nt' and path.startswith('/'):
            path = path[1:]
        dir_path = os.path.dirname(path)
        ls.project.reload_init_file(dir_path)
        
    ls.validate_document(params.text_document.uri, document)


@server.feature(TEXT_DOCUMENT_DID_CLOSE)
async def did_close(ls: OSILanguageServer, params: DidCloseTextDocumentParams):
    """Handle document close event"""
    logger.info(f"Document closed: {params.text_document.uri}")
    if params.text_document.uri in ls.document_asts:
        del ls.document_asts[params.text_document.uri]


@server.feature(TEXT_DOCUMENT_COMPLETION)
async def completions(ls: OSILanguageServer, params: CompletionParams) -> CompletionList:
    """Provide completions"""
    logger.info(f"Completion requested at {params.position}")

    try:
        document = ls.workspace.get_document(params.text_document.uri)
        
        try:
            ast, symbol_table = ls.parse_document(document)
            
            # Populate symbol table with semantic analyzer
            if ast:
                analyzer = SemanticAnalyzer(symbol_table, file_uri=params.text_document.uri)
                analyzer.analyze(ast)
        except Exception:
             # If parsing fails, we might still want to try completion on partial table
             # But here we just get a fresh one (with parent) if parse_document fails early.
             # If parse_document raises ProtocolError, we caught it?
             # Wait, parse_document raises ProtocolError. We need to catch it here.
             symbol_table = ls.get_symbol_table(params.text_document.uri)

        # Get current line
        line = document.lines[params.position.line] if params.position.line < len(document.lines) else ""

        # Get completions
        provider = CompletionProvider(symbol_table)
        return provider.get_completions(line, params.position.character)

    except Exception as e:
        logger.error(f"Error providing completions: {e}", exc_info=True)
        return CompletionList(is_incomplete=False, items=[])


@server.feature(TEXT_DOCUMENT_HOVER)
async def hover(ls: OSILanguageServer, params: HoverParams) -> Optional[Hover]:
    """Provide hover information"""
    logger.info(f"Hover requested at {params.position}")

    try:
        document = ls.workspace.get_document(params.text_document.uri)
        try:
            ast, symbol_table = ls.parse_document(document)
            if ast:
                analyzer = SemanticAnalyzer(symbol_table, file_uri=params.text_document.uri)
                analyzer.analyze(ast)
        except Exception:
             symbol_table = ls.get_symbol_table(params.text_document.uri)

        # Get word at position
        line = document.lines[params.position.line] if params.position.line < len(document.lines) else ""
        word = get_word_at_position(line, params.position.character)

        if not word:
            return None

        # Get hover info
        provider = HoverProvider(symbol_table)
        return provider.get_hover(word)

    except Exception as e:
        logger.error(f"Error providing hover: {e}", exc_info=True)
        return None


@server.feature(TEXT_DOCUMENT_DEFINITION)
async def definition(ls: OSILanguageServer, params: DefinitionParams) -> Optional[Location]:
    """Provide definition location"""
    logger.info(f"Definition requested at {params.position}")

    try:
        document = ls.workspace.get_document(params.text_document.uri)
        try:
            ast, symbol_table = ls.parse_document(document)
            if ast:
                analyzer = SemanticAnalyzer(symbol_table, file_uri=params.text_document.uri)
                analyzer.analyze(ast)
        except Exception:
             symbol_table = ls.get_symbol_table(params.text_document.uri)

        # Get word at position
        line = document.lines[params.position.line] if params.position.line < len(document.lines) else ""
        word = get_word_at_position(line, params.position.character)

        if not word:
            return None

        # Get definition
        provider = DefinitionProvider(symbol_table, params.text_document.uri)
        return provider.get_definition(word)

    except Exception as e:
        logger.error(f"Error providing definition: {e}", exc_info=True)
        return None


@server.feature(TEXT_DOCUMENT_REFERENCES)
async def references(ls: OSILanguageServer, params: ReferenceParams) -> Optional[list[Location]]:
    """Provide reference locations"""
    logger.info(f"References requested at {params.position}")

    try:
        document = ls.workspace.get_document(params.text_document.uri)
        try:
            ast, symbol_table = ls.parse_document(document)
            if ast:
                analyzer = SemanticAnalyzer(symbol_table, file_uri=params.text_document.uri)
                analyzer.analyze(ast)
        except Exception:
             symbol_table = ls.get_symbol_table(params.text_document.uri)

        # Get word at position
        line = document.lines[params.position.line] if params.position.line < len(document.lines) else ""
        word = get_word_at_position(line, params.position.character)

        if not word:
            return None

        # Get references
        provider = DefinitionProvider(symbol_table, params.text_document.uri)
        return provider.get_references(word)

    except Exception as e:
        logger.error(f"Error providing references: {e}", exc_info=True)
        return None


def get_word_at_position(line: str, character: int) -> Optional[str]:
    """Get the word at a specific position in a line"""
    if character >= len(line):
        character = len(line) - 1

    if character < 0:
        return None

    # Find start of word
    start = character
    while start > 0 and (line[start - 1].isalnum() or line[start - 1] in '_$.-'):
        start -= 1

    # Find end of word
    end = character
    while end < len(line) and (line[end].isalnum() or line[end] in '_.-'):
        end += 1

    word = line[start:end] if start < end else None
    return word if word else None


def main():
    """Start the language server"""
    logger.info("Starting OSI Language Server...")
    server.start_io()


if __name__ == "__main__":
    main()