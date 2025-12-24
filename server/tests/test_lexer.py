import pytest
from osi_lsp.parser.lexer import Lexer, TokenType

def test_lexer_numbers():
    lexer = Lexer("42 -15 0")
    tokens = lexer.tokenize()
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    assert len(tokens) == 3
    assert tokens[0].type == TokenType.NUMBER
    assert tokens[0].value == "42"
    assert tokens[1].type == TokenType.NUMBER
    assert tokens[1].value == "-15"
    assert tokens[2].type == TokenType.NUMBER
    assert tokens[2].value == "0"

def test_lexer_strings():
    lexer = Lexer('"hello" "world\\n" "with\\"quote"')
    tokens = lexer.tokenize()
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    assert len(tokens) == 3
    assert tokens[0].type == TokenType.STRING_LITERAL
    assert tokens[0].value == "hello"
    assert tokens[1].type == TokenType.STRING_LITERAL
    assert tokens[1].value == "world\n"
    assert tokens[2].type == TokenType.STRING_LITERAL
    assert tokens[2].value == 'with"quote'

def test_lexer_variables():
    lexer = Lexer("$counter $my_var $var123")
    tokens = lexer.tokenize()
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    assert len(tokens) == 3
    assert tokens[0].type == TokenType.VARIABLE
    assert tokens[0].value == "counter"
    assert tokens[1].type == TokenType.VARIABLE
    assert tokens[1].value == "my_var"
    assert tokens[2].type == TokenType.VARIABLE
    assert tokens[2].value == "var123"

def test_lexer_keywords():
    lexer = Lexer("declare varset goto if return subprog substart subend delete bufferit unbufferit calccrc timer untimer queue clearqueue generateup eventdown out")
    tokens = lexer.tokenize()
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    expected_types = [
        TokenType.DECLARE, TokenType.VARSET, TokenType.GOTO, TokenType.IF, 
        TokenType.RETURN, TokenType.SUBPROG, TokenType.SUBSTART, TokenType.SUBEND,
        TokenType.DELETE, TokenType.BUFFERIT, TokenType.UNBUFFERIT, TokenType.CALCCRC,
        TokenType.TIMER, TokenType.UNTIMER, TokenType.QUEUE, TokenType.CLEARQUEUE,
        TokenType.GENERATEUP, TokenType.EVENTDOWN, TokenType.OUT
    ]
    
    assert len(tokens) == len(expected_types)
    for i, t in enumerate(tokens):
        assert t.type == expected_types[i]

def test_lexer_types():
    lexer = Lexer("integer buffer string queue")
    tokens = lexer.tokenize()
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    expected_types = [
        TokenType.INTEGER, TokenType.BUFFER, TokenType.STRING, TokenType.QUEUE
    ]
    
    assert len(tokens) == len(expected_types)
    for i, t in enumerate(tokens):
        assert t.type == expected_types[i]

def test_lexer_functions():
    lexer = Lexer("sizeof copy pos locguide CurrentSystemName dequeue peek qcount")
    tokens = lexer.tokenize()
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    expected_types = [
        TokenType.SIZEOF, TokenType.COPY, TokenType.POS, TokenType.LOCGUIDE, 
        TokenType.CURRENTSYSTEMNAME, TokenType.DEQUEUE, TokenType.PEEK, TokenType.QCOUNT
    ]
    
    assert len(tokens) == len(expected_types)
    for i, t in enumerate(tokens):
        assert t.type == expected_types[i]

def test_lexer_operators():
    lexer = Lexer("+ - * / % == != > < >= <= && ||")
    tokens = lexer.tokenize()
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    expected_types = [
        TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO,
        TokenType.EQUAL, TokenType.NOT_EQUAL, TokenType.GREATER, TokenType.LESS,
        TokenType.GREATER_EQUAL, TokenType.LESS_EQUAL, TokenType.AND, TokenType.OR
    ]
    
    assert len(tokens) == len(expected_types)
    for i, t in enumerate(tokens):
        assert t.type == expected_types[i]

def test_lexer_delimiters():
    lexer = Lexer("( ) , : .")
    tokens = lexer.tokenize()
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    expected_types = [
        TokenType.LPAREN, TokenType.RPAREN, TokenType.COMMA, TokenType.COLON, TokenType.DOT
    ]
    
    assert len(tokens) == len(expected_types)
    for i, t in enumerate(tokens):
        assert t.type == expected_types[i]

def test_lexer_char_codes():
    lexer = Lexer("#0 #255")
    tokens = lexer.tokenize()
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    assert len(tokens) == 2
    assert tokens[0].type == TokenType.CHAR_CODE
    assert tokens[0].value == "0"
    assert tokens[1].type == TokenType.CHAR_CODE
    assert tokens[1].value == "255"

def test_lexer_handler():
    lexer = Lexer("## MY_HANDLER")
    tokens = lexer.tokenize()
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.HANDLER
    assert tokens[0].value == "MY_HANDLER"

def test_lexer_labels():
    lexer = Lexer("MY_LABEL: OTHER_LABEL:")
    tokens = lexer.tokenize()
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    assert len(tokens) == 2
    assert tokens[0].type == TokenType.LABEL
    assert tokens[0].value == "MY_LABEL"
    assert tokens[1].type == TokenType.LABEL
    assert tokens[1].value == "OTHER_LABEL"

def test_lexer_comments():
    lexer = Lexer("declare ; this is a comment\ninteger")
    tokens = lexer.tokenize()
    # comments are skipped in get_next_token currently
    tokens = [t for t in tokens if t.type != TokenType.EOF]
    
    assert len(tokens) == 3 # DECLARE, NEWLINE, INTEGER
    assert tokens[0].type == TokenType.DECLARE
    assert tokens[1].type == TokenType.NEWLINE
    assert tokens[2].type == TokenType.INTEGER

def test_lexer_unknown():
    lexer = Lexer("@")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.UNKNOWN
    assert tokens[0].value == "@"

def test_lexer_complex():
    code = """
    ## INIT
    x declare integer
    0 varset $x
    
    LOOP:
        $x + 1 varset x
        $x < 10 if LOOP
    return
    """
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    
    # Check some key tokens
    types = [t.type for t in tokens]
    assert TokenType.HANDLER in types
    assert TokenType.DECLARE in types
    assert TokenType.VARSET in types
    assert TokenType.LABEL in types
    assert TokenType.IF in types
    assert TokenType.RETURN in types
