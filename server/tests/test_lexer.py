import pytest
from osi_lsp.parser.lexer import Lexer, TokenType

def test_lexer_numbers():
    lexer = Lexer("42 -15")
    tokens = lexer.tokenize()
    
    # Filter out EOF
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    assert len(tokens) == 2
    assert tokens[0].type == TokenType.NUMBER
    assert tokens[0].value == "42"
    assert tokens[1].type == TokenType.NUMBER
    assert tokens[1].value == "-15"

def test_lexer_strings():
    lexer = Lexer('"hello" "world"')
    tokens = lexer.tokenize()
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    assert len(tokens) == 2
    assert tokens[0].type == TokenType.STRING_LITERAL
    assert tokens[0].value == "hello"
    assert tokens[1].type == TokenType.STRING_LITERAL
    assert tokens[1].value == "world"

def test_lexer_variables():
    lexer = Lexer("$counter $my_var")
    tokens = lexer.tokenize()
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    assert len(tokens) == 2
    assert tokens[0].type == TokenType.VARIABLE
    assert tokens[0].value == "counter"
    assert tokens[1].type == TokenType.VARIABLE
    assert tokens[1].value == "my_var"

def test_lexer_keywords():
    lexer = Lexer("declare varset goto if return")
    tokens = lexer.tokenize()
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    expected_types = [
        TokenType.DECLARE,
        TokenType.VARSET,
        TokenType.GOTO,
        TokenType.IF,
        TokenType.RETURN
    ]
    
    assert len(tokens) == 5
    for i, t in enumerate(tokens):
        assert t.type == expected_types[i]

def test_lexer_functions():
    lexer = Lexer("sizeof copy pos locguide CurrentSystemName")
    tokens = lexer.tokenize()
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    expected_types = [
        TokenType.SIZEOF,
        TokenType.COPY,
        TokenType.POS,
        TokenType.LOCGUIDE,
        TokenType.CURRENTSYSTEMNAME
    ]
    
    assert len(tokens) == 5
    for i, t in enumerate(tokens):
        assert t.type == expected_types[i]
