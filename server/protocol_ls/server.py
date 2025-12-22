"""Language Server for Protocol Language"""

import logging
from typing import Optional, Dict
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
)
from pygls.server import LanguageServer
from pygls.workspace import Document

from .parser.lexer import Lexer
from .parser.parser import Parser
from .analysis.symbol_table import SymbolTable
from .analysis.validator import Validator
from .providers.completion import CompletionProvider
from .providers.hover import HoverProvider
from .providers.definition import DefinitionProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProtocolLanguageServer(LanguageServer):
    """Language Server for Protocol Language"""

    def __init__(self):
        super().__init__("protocol-language-server", "v0.1.0")
        self.document_tables: Dict[str, SymbolTable] = {}
        self.document_asts: Dict[str, any] = {}

    def get_symbol_table(self, uri: str) -> SymbolTable:
        """Get or create symbol table for a document"""
        if uri not in self.document_tables:
            self.document_tables[uri] = SymbolTable()
        return self.document_tables[uri]

    def parse_document(self, document: Document) -> tuple[Optional[any], SymbolTable]:
        """Parse a document and return AST and symbol table"""
        try:
            # Clear symbol table
            symbol_table = self.get_symbol_table(document.uri)
            symbol_table.clear()

            # Tokenize
            lexer = Lexer(document.source)
            tokens = lexer.tokenize()

            # Parse
            parser = Parser(tokens)
            ast = parser.parse()

            # Store AST
            self.document_asts[document.uri] = ast

            return ast, symbol_table

        except Exception as e:
            logger.error(f"Error parsing document {document.uri}: {e}", exc_info=True)
            return None, symbol_table

    def validate_document(self, uri: str, document: Document):
        """Validate document and publish diagnostics"""
        try:
            ast, symbol_table = self.parse_document(document)

            # Validate
            validator = Validator(symbol_table)
            diagnostics = validator.validate(ast)

            # Publish diagnostics
            self.publish_diagnostics(uri, diagnostics)

        except Exception as e:
            logger.error(f"Error validating document {uri}: {e}", exc_info=True)


# Create server instance
server = ProtocolLanguageServer()


@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: ProtocolLanguageServer, params: DidOpenTextDocumentParams):
    """Handle document open event"""
    logger.info(f"Document opened: {params.text_document.uri}")
    document = ls.workspace.get_document(params.text_document.uri)
    ls.validate_document(params.text_document.uri, document)


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
async def did_change(ls: ProtocolLanguageServer, params: DidChangeTextDocumentParams):
    """Handle document change event"""
    logger.info(f"Document changed: {params.text_document.uri}")
    document = ls.workspace.get_document(params.text_document.uri)
    ls.validate_document(params.text_document.uri, document)


@server.feature(TEXT_DOCUMENT_DID_CLOSE)
async def did_close(ls: ProtocolLanguageServer, params: DidCloseTextDocumentParams):
    """Handle document close event"""
    logger.info(f"Document closed: {params.text_document.uri}")
    # Clean up
    if params.text_document.uri in ls.document_tables:
        del ls.document_tables[params.text_document.uri]
    if params.text_document.uri in ls.document_asts:
        del ls.document_asts[params.text_document.uri]


@server.feature(TEXT_DOCUMENT_COMPLETION)
async def completions(ls: ProtocolLanguageServer, params: CompletionParams) -> CompletionList:
    """Provide completions"""
    logger.info(f"Completion requested at {params.position}")

    try:
        document = ls.workspace.get_document(params.text_document.uri)
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
async def hover(ls: ProtocolLanguageServer, params: HoverParams) -> Optional[Hover]:
    """Provide hover information"""
    logger.info(f"Hover requested at {params.position}")

    try:
        document = ls.workspace.get_document(params.text_document.uri)
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
async def definition(ls: ProtocolLanguageServer, params: DefinitionParams) -> Optional[Location]:
    """Provide definition location"""
    logger.info(f"Definition requested at {params.position}")

    try:
        document = ls.workspace.get_document(params.text_document.uri)
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
async def references(ls: ProtocolLanguageServer, params: ReferenceParams) -> Optional[list[Location]]:
    """Provide reference locations"""
    logger.info(f"References requested at {params.position}")

    try:
        document = ls.workspace.get_document(params.text_document.uri)
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
    logger.info("Starting Protocol Language Server...")
    server.start_io()


if __name__ == "__main__":
    main()
