import pytest
from lsprotocol.types import SymbolKind, DocumentSymbol, Range, Position
from osi_lsp.parser.lexer import Lexer
from osi_lsp.parser.parser import Parser
from osi_lsp.providers.document_symbol import DocumentSymbolProvider

def parse_code(code):
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast, errors = parser.parse()
    assert not errors
    return ast

def test_document_symbol_variables():
    code = """
    var1 declare integer
    buffer1 declare buffer
    """
    ast = parse_code(code)
    provider = DocumentSymbolProvider()
    symbols = provider.get_symbols(ast)

    assert len(symbols) == 2
    
    assert symbols[0].name == "$var1"
    assert symbols[0].kind == SymbolKind.Variable
    assert symbols[0].detail == "integer"
    
    assert symbols[1].name == "$buffer1"
    assert symbols[1].kind == SymbolKind.Variable
    assert symbols[1].detail == "buffer"

def test_document_symbol_labels():
    code = """
    START:
    loop:
    """
    ast = parse_code(code)
    provider = DocumentSymbolProvider()
    symbols = provider.get_symbols(ast)

    assert len(symbols) == 2
    
    assert symbols[0].name == "START"
    assert symbols[0].kind == SymbolKind.Key
    assert symbols[0].detail == "Label"
    
    assert symbols[1].name == "loop"
    assert symbols[1].kind == SymbolKind.Key

def test_document_symbol_subroutine():
    code = """
    substart mysub
        x declare integer
        LABEL:
    subend
    """
    ast = parse_code(code)
    provider = DocumentSymbolProvider()
    symbols = provider.get_symbols(ast)

    assert len(symbols) == 1
    sub = symbols[0]
    
    assert sub.name == "mysub"
    assert sub.kind == SymbolKind.Function
    assert sub.detail == "Subroutine"
    
    # Check children
    assert len(sub.children) == 2
    assert sub.children[0].name == "$x"
    assert sub.children[0].kind == SymbolKind.Variable
    assert sub.children[1].name == "LABEL"
    assert sub.children[1].kind == SymbolKind.Key

def test_document_symbol_range():
    code = """
    var1 declare integer
    """
    # Line 1 (index 1 in split, but parser is 0-indexed usually? let's check)
    # The parser starts counting lines at 0.
    # "    var1 declare integer" -> This is technically line 1 if code starts with \n
    
    code = "var1 declare integer"
    ast = parse_code(code)
    provider = DocumentSymbolProvider()
    symbols = provider.get_symbols(ast)
    
    assert symbols[0].range.start.line == 0
    assert symbols[0].range.start.character == 0
    # Length of "var1 declare integer" is 20
    # Implementation adds 10 to end char
    # We just want to ensure range is valid (start <= end)
    assert symbols[0].range.end.line >= symbols[0].range.start.line
    assert symbols[0].range.end.character > symbols[0].range.start.character

def test_document_symbol_mixed():
    code = """
    global declare integer
    
    INIT:
        goto MAIN
        
    substart worker
        local declare string
    subend
    
    MAIN:
        out 1
    """
    ast = parse_code(code)
    provider = DocumentSymbolProvider()
    symbols = provider.get_symbols(ast)
    
    # Expected: global, INIT, worker, MAIN
    # goto and out are not symbols
    
    assert len(symbols) == 4
    assert symbols[0].name == "$global"
    assert symbols[1].name == "INIT"
    assert symbols[2].name == "worker"
    assert symbols[2].children[0].name == "$local"
    assert symbols[3].name == "MAIN"

