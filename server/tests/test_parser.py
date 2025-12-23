import pytest
from osi_lsp.parser.lexer import Lexer
from osi_lsp.parser.parser import Parser
from osi_lsp.parser.ast_nodes import DeclareStatement, VarsetStatement, LabelStatement

def parse(text):
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()

def test_parse_declare():
    ast = parse("counter declare integer")
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, DeclareStatement)
    assert stmt.name == "counter"
    assert stmt.var_type == "integer"

def test_parse_varset():
    ast = parse("5 varset counter")
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, VarsetStatement)
    assert stmt.variable == "counter"
    # Expression checking omitted for brevity, assuming structure is correct

def test_parse_handler_structure():
    # In strict parsing, we might expect specific structure, but currently parser parses a list of statements
    # The structure validation happens in Validator.
    code = """
    HANDLER:
        0 varset counter
        return
    """
    ast = parse(code)
    # Parser returns Program which has statements.
    # Label 'HANDLER:' is parsed as LabelStatement.
    assert len(ast.statements) == 3 # Label, Varset, Return
    assert isinstance(ast.statements[0], LabelStatement)
    assert ast.statements[0].name == "HANDLER"
