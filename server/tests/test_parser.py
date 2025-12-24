import pytest
from osi_lsp.parser.lexer import Lexer
from osi_lsp.parser.parser import Parser
from osi_lsp.parser.ast_nodes import *

def parse(text):
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast, _ = parser.parse()
    return ast

def test_parse_declare():
    ast = parse("counter declare integer")
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, DeclareStatement)
    assert stmt.name == "counter"
    assert stmt.var_type == "integer"

def test_parse_varset():
    ast = parse("$x + 5 varset counter")
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, VarsetStatement)
    assert stmt.variable == "counter"
    assert isinstance(stmt.expression, BinaryOperation)
    assert stmt.expression.operator == "+"

def test_parse_bufferit():
    ast = parse("buff bufferit 10 1 2 500 4")
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, BufferitStatement)
    assert stmt.buffer_name == "buff"
    assert isinstance(stmt.total_length, NumberLiteral)
    assert stmt.total_length.value == 10
    assert len(stmt.fields) == 2
    assert stmt.fields[0][0].value == 1
    assert stmt.fields[0][1].value == 2
    assert stmt.fields[1][0].value == 500
    assert stmt.fields[1][1].value == 4

def test_parse_unbufferit():
    ast = parse("unbufferit $buff type 1 value 4")
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, UnbufferitStatement)
    assert stmt.buffer_name == "buff"
    assert len(stmt.fields) == 2
    assert stmt.fields[0][0] == "type"
    assert stmt.fields[0][1].value == 1
    assert stmt.fields[1][0] == "value"
    assert stmt.fields[1][1].value == 4

def test_parse_timer():
    ast = parse("TIMEOUT_EVENT timer my_timer 5000 correlation_id $id")
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, TimerStatement)
    assert stmt.event_name == "TIMEOUT_EVENT"
    assert stmt.timer_var == "my_timer"
    assert stmt.delay.value == 5000
    assert "correlation_id" in stmt.parameters

def test_parse_if_goto():
    ast = parse("$counter > 10 if EndLoop")
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, IfStatement)
    assert stmt.label == "EndLoop"
    assert stmt.condition.operator == ">"

def test_parse_subprog():
    ast = parse("subprog MySub")
    assert len(ast.statements) == 1
    assert isinstance(ast.statements[0], SubprogStatement)
    assert ast.statements[0].name == "MySub"

def test_parse_substart_end():
    code = """
    substart MySub
        1 varset $x
    subend
    """
    ast = parse(code)
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, SubstartStatement)
    assert stmt.name == "MySub"
    assert len(stmt.statements) == 1

def test_parse_queue():
    ast = parse("my_queue queue 100")
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, QueueStatement)
    assert stmt.queue_name == "my_queue"
    assert stmt.value.value == 100

def test_parse_generateup_eventdown():
    ast = parse("DATA.IND generateup param1 1")
    assert isinstance(ast.statements[0], GenerateupStatement)
    
    ast = parse("DATA.REQ eventdown param1 1")
    assert isinstance(ast.statements[0], EventdownStatement)

def test_parse_expressions():
    # Test precedence: 1 + 2 * 3 should be 1 + (2 * 3)
    ast = parse("1 + 2 * 3 varset x")
    stmt = ast.statements[0]
    expr = stmt.expression
    assert expr.operator == "+"
    assert expr.right.operator == "*"

    # Test parentheses: (1 + 2) * 3
    ast = parse("(1 + 2) * 3 varset x")
    stmt = ast.statements[0]
    expr = stmt.expression
    assert expr.operator == "*"
    assert expr.left.operator == "+"

def test_parse_function_calls():
    ast = parse("sizeof($buff) varset x")
    stmt = ast.statements[0]
    assert isinstance(stmt.expression, FunctionCall)
    assert stmt.expression.name == "sizeof"

    ast = parse("copy($str, 0, 5) varset x")
    stmt = ast.statements[0]
    assert len(stmt.expression.arguments) == 3

def test_parse_standalone_expr():
    ast = parse("MyFunc(1, 2)")
    assert len(ast.statements) == 1
    assert isinstance(ast.statements[0], ExpressionStatement)
    assert isinstance(ast.statements[0].expression, FunctionCall)

def test_parse_char_code():
    ast = parse("#10 varset x")
    stmt = ast.statements[0]
    assert isinstance(stmt.expression, CharCodeLiteral)
    assert stmt.expression.value == 10

def test_parse_calccrc():
    ast = parse("calccrc $res $buff")
    stmt = ast.statements[0]
    assert isinstance(stmt, CalccrcStatement)
    assert stmt.result_var == "res"

def test_parse_delete():
    ast = parse("delete $str 0 5")
    stmt = ast.statements[0]
    assert isinstance(stmt, DeleteStatement)
    assert stmt.string_var == "str"

    def test_parser_recovery():

        # Code with syntax error in middle

        code = """

        1 varset x

        timer my_timer  ; Syntax error: missing event name

        2 varset y

        """

        lexer = Lexer(code)

        tokens = lexer.tokenize()

        parser = Parser(tokens)

        ast, errors = parser.parse()

    

        # Should have recovered and parsed the other valid statements

        assert len(errors) == 1

        assert "timer needs event name first" in errors[0].message

    

        # Check valid statements (x and y assignments)

        # The middle statement failed, so we should have 2 statements

        assert len(ast.statements) == 2

        assert ast.statements[0].variable == "x"

        assert ast.statements[1].variable == "y"


