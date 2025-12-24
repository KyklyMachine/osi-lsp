"""Comprehensive parser tests for edge cases and full coverage"""

import pytest
from osi_lsp.parser.lexer import Lexer, TokenType
from osi_lsp.parser.parser import Parser
from osi_lsp.parser.ast_nodes import *
from osi_lsp.parser.errors import ProtocolError


def parse(text):
    """Helper to parse text"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast, errors = parser.parse()
    if errors:
        raise errors[0]
    return ast


class TestParserStatements:
    """Test parsing of all statement types"""

    def test_parse_goto(self):
        """Test goto statement"""
        ast = parse("goto my_label")
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert isinstance(stmt, GotoStatement)
        assert stmt.label == "my_label"

    def test_parse_return(self):
        """Test return statement"""
        ast = parse("return")
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert isinstance(stmt, ReturnStatement)

    def test_parse_label(self):
        """Test label definition"""
        ast = parse("my_label:")
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert isinstance(stmt, LabelStatement)
        assert stmt.name == "my_label"

    def test_parse_out(self):
        """Test out statement"""
        ast = parse('out "Debug message"')
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert isinstance(stmt, OutStatement)
        assert isinstance(stmt.expression, StringLiteral)
        assert stmt.expression.value == "Debug message"

        # Out with variable
        ast = parse("out $counter")
        stmt = ast.statements[0]
        assert isinstance(stmt.expression, VariableExpression)

    def test_parse_untimer(self):
        """Test untimer statement"""
        ast = parse("untimer $my_timer")
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert isinstance(stmt, UntimerStatement)
        assert isinstance(stmt.timer_id, VariableExpression)

    def test_parse_clearqueue(self):
        """Test clearqueue statement"""
        ast = parse("clearqueue my_queue")
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert isinstance(stmt, ClearqueueStatement)
        assert stmt.queue_name == "my_queue"

        # With variable
        ast = parse("clearqueue $my_queue")
        stmt = ast.statements[0]
        assert stmt.queue_name == "my_queue"

    def test_parse_delete(self):
        """Test delete statement"""
        ast = parse("delete $str 5 10")
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert isinstance(stmt, DeleteStatement)
        assert stmt.string_var == "str"
        assert isinstance(stmt.start, NumberLiteral)
        assert stmt.start.value == 5
        assert isinstance(stmt.length, NumberLiteral)
        assert stmt.length.value == 10

    def test_parse_multiple_statements(self):
        """Test parsing multiple statements"""
        code = """
        counter declare integer
        0 varset $counter
        goto start
        return
        """
        ast = parse(code)
        # Filter out None (from newlines)
        stmts = [s for s in ast.statements if s is not None]
        assert len(stmts) == 4
        assert isinstance(stmts[0], DeclareStatement)
        assert isinstance(stmts[1], VarsetStatement)
        assert isinstance(stmts[2], GotoStatement)
        assert isinstance(stmts[3], ReturnStatement)


class TestParserExpressions:
    """Test expression parsing"""

    def test_parse_string_literal(self):
        """Test string literals in expressions"""
        ast = parse('"hello" varset $str')
        stmt = ast.statements[0]
        assert isinstance(stmt.expression, StringLiteral)
        assert stmt.expression.value == "hello"

    def test_parse_all_arithmetic_operators(self):
        """Test all arithmetic operators"""
        # Addition
        ast = parse("1 + 2 varset $x")
        assert ast.statements[0].expression.operator == "+"

        # Subtraction
        ast = parse("5 - 3 varset $x")
        assert ast.statements[0].expression.operator == "-"

        # Multiplication
        ast = parse("2 * 3 varset $x")
        assert ast.statements[0].expression.operator == "*"

        # Division
        ast = parse("10 / 2 varset $x")
        assert ast.statements[0].expression.operator == "/"

        # Modulo
        ast = parse("10 % 3 varset $x")
        assert ast.statements[0].expression.operator == "%"

    def test_parse_all_comparison_operators(self):
        """Test all comparison operators"""
        operators = [
            ("==", TokenType.EQUAL),
            ("!=", TokenType.NOT_EQUAL),
            (">", TokenType.GREATER),
            ("<", TokenType.LESS),
            (">=", TokenType.GREATER_EQUAL),
            ("<=", TokenType.LESS_EQUAL)
        ]

        for op_str, _ in operators:
            code = f"$a {op_str} $b if label"
            ast = parse(code)
            stmt = ast.statements[0]
            assert isinstance(stmt, IfStatement)
            assert stmt.condition.operator == op_str

    def test_parse_logical_operators(self):
        """Test logical AND and OR"""
        # AND
        ast = parse("$a && $b if label")
        stmt = ast.statements[0]
        assert stmt.condition.operator == "&&"

        # OR
        ast = parse("$a || $b if label")
        stmt = ast.statements[0]
        assert stmt.condition.operator == "||"

        # Combined
        ast = parse("$a && $b || $c if label")
        stmt = ast.statements[0]
        # Should be: (a && b) || c due to precedence
        assert stmt.condition.operator == "||"
        assert stmt.condition.left.operator == "&&"

    def test_parse_operator_precedence(self):
        """Test complex operator precedence"""
        # Multiplication before addition: 1 + 2 * 3 = 1 + (2 * 3)
        ast = parse("1 + 2 * 3 varset $x")
        expr = ast.statements[0].expression
        assert expr.operator == "+"
        assert expr.left.value == 1
        assert expr.right.operator == "*"

        # Division before subtraction: 10 - 6 / 2 = 10 - (6 / 2)
        ast = parse("10 - 6 / 2 varset $x")
        expr = ast.statements[0].expression
        assert expr.operator == "-"
        assert expr.right.operator == "/"

        # Comparison before logical: a > 5 && b < 10
        ast = parse("$a > 5 && $b < 10 if label")
        expr = ast.statements[0].condition
        assert expr.operator == "&&"
        assert expr.left.operator == ">"
        assert expr.right.operator == "<"

    def test_parse_nested_parentheses(self):
        """Test nested parenthesized expressions"""
        ast = parse("((1 + 2) * 3) varset $x")
        expr = ast.statements[0].expression
        assert expr.operator == "*"
        assert expr.left.operator == "+"

        ast = parse("(1 + (2 * 3)) varset $x")
        expr = ast.statements[0].expression
        assert expr.operator == "+"
        assert expr.right.operator == "*"


class TestParserFunctions:
    """Test function call parsing"""

    def test_parse_sizeof(self):
        """Test sizeof function"""
        ast = parse("sizeof($buffer) varset $size")
        stmt = ast.statements[0]
        assert isinstance(stmt.expression, FunctionCall)
        assert stmt.expression.name == "sizeof"
        assert len(stmt.expression.arguments) == 1

    def test_parse_copy(self):
        """Test copy function"""
        ast = parse("copy($str, 0, 10) varset $result")
        stmt = ast.statements[0]
        assert isinstance(stmt.expression, FunctionCall)
        assert stmt.expression.name == "copy"
        assert len(stmt.expression.arguments) == 3

    def test_parse_pos(self):
        """Test pos function"""
        ast = parse('pos("substring", $str) varset $index')
        stmt = ast.statements[0]
        assert isinstance(stmt.expression, FunctionCall)
        assert stmt.expression.name == "pos"
        assert len(stmt.expression.arguments) == 2

    def test_parse_locguide(self):
        """Test locguide function"""
        ast = parse("locguide($str) varset $result")
        stmt = ast.statements[0]
        assert isinstance(stmt.expression, FunctionCall)
        assert stmt.expression.name == "locguide"

    def test_parse_currentsystemname(self):
        """Test CurrentSystemName function"""
        ast = parse("CurrentSystemName() varset $name")
        stmt = ast.statements[0]
        assert isinstance(stmt.expression, FunctionCall)
        assert stmt.expression.name == "currentsystemname"
        assert len(stmt.expression.arguments) == 0

    def test_parse_dequeue(self):
        """Test dequeue function in expression"""
        ast = parse("dequeue($queue) varset $value")
        stmt = ast.statements[0]
        assert isinstance(stmt.expression, FunctionCall)
        assert stmt.expression.name == "dequeue"

    def test_parse_peek(self):
        """Test peek function"""
        ast = parse("peek($queue) varset $value")
        stmt = ast.statements[0]
        assert isinstance(stmt.expression, FunctionCall)
        assert stmt.expression.name == "peek"

    def test_parse_qcount(self):
        """Test qcount function"""
        ast = parse("qcount($queue) varset $size")
        stmt = ast.statements[0]
        assert isinstance(stmt.expression, FunctionCall)
        assert stmt.expression.name == "qcount"

    def test_parse_function_no_args(self):
        """Test function with no arguments"""
        ast = parse("MyFunc()")
        stmt = ast.statements[0]
        assert isinstance(stmt, ExpressionStatement)
        assert isinstance(stmt.expression, FunctionCall)
        assert len(stmt.expression.arguments) == 0

    def test_parse_function_multiple_args(self):
        """Test function with multiple arguments"""
        ast = parse("MyFunc(1, 2, 3, $var)")
        stmt = ast.statements[0]
        func = stmt.expression
        assert len(func.arguments) == 4
        assert isinstance(func.arguments[0], NumberLiteral)
        assert isinstance(func.arguments[3], VariableExpression)


class TestParserComplexStatements:
    """Test complex statement parsing"""

    def test_parse_bufferit_complex(self):
        """Test bufferit with expressions"""
        ast = parse("buff bufferit $len + 4 $val1 2 $val2 + 1 2")
        stmt = ast.statements[0]
        assert isinstance(stmt, BufferitStatement)
        assert isinstance(stmt.total_length, BinaryOperation)
        assert len(stmt.fields) == 2
        # First field: $val1, length 2
        assert isinstance(stmt.fields[0][0], VariableExpression)
        assert isinstance(stmt.fields[0][1], NumberLiteral)
        # Second field: $val2 + 1, length 2
        assert isinstance(stmt.fields[1][0], BinaryOperation)

    def test_parse_timer_with_params(self):
        """Test timer with multiple parameters"""
        ast = parse("TIMEOUT timer $timer 1000 id $id type 5 data $buff")
        stmt = ast.statements[0]
        assert isinstance(stmt, TimerStatement)
        assert stmt.event_name == "TIMEOUT"
        assert stmt.timer_var == "timer"
        assert len(stmt.parameters) == 3
        assert "id" in stmt.parameters
        assert "type" in stmt.parameters
        assert "data" in stmt.parameters

    def test_parse_events_with_dotted_names(self):
        """Test events with dotted names like DATA.REQ"""
        ast = parse("DATA.REQ generateup param1 $val")
        stmt = ast.statements[0]
        assert isinstance(stmt, GenerateupStatement)
        assert stmt.event_name == "DATA.REQ"
        assert "param1" in stmt.parameters

        ast = parse("N_DATA.IND eventdown payload $buff length 10")
        stmt = ast.statements[0]
        assert isinstance(stmt, EventdownStatement)
        assert stmt.event_name == "N_DATA.IND"
        assert "payload" in stmt.parameters
        assert "length" in stmt.parameters

    def test_parse_unbufferit_with_identifiers(self):
        """Test unbufferit with both variables and identifiers"""
        ast = parse("unbufferit $buff var1 2 $var2 4")
        stmt = ast.statements[0]
        assert len(stmt.fields) == 2
        assert stmt.fields[0][0] == "var1"
        assert stmt.fields[1][0] == "var2"


class TestParserSubroutines:
    """Test subroutine parsing"""

    def test_parse_subprog_call(self):
        """Test subroutine call"""
        ast = parse("subprog MySub")
        stmt = ast.statements[0]
        assert isinstance(stmt, SubprogStatement)
        assert stmt.name == "MySub"

    def test_parse_substart_subend(self):
        """Test subroutine definition"""
        code = """
        substart MySub
            $x + 1 varset x
            out "In subroutine"
            return
        subend
        """
        ast = parse(code)
        stmts = [s for s in ast.statements if s is not None]
        assert len(stmts) == 1
        sub = stmts[0]
        assert isinstance(sub, SubstartStatement)
        assert sub.name == "MySub"
        assert len(sub.statements) == 3
        assert isinstance(sub.statements[0], VarsetStatement)
        assert isinstance(sub.statements[1], OutStatement)
        assert isinstance(sub.statements[2], ReturnStatement)

    def test_parse_nested_subroutine_calls(self):
        """Test multiple subroutine calls"""
        code = """
        subprog Sub1
        subprog Sub2
        subprog Sub3
        """
        ast = parse(code)
        stmts = [s for s in ast.statements if s is not None]
        assert len(stmts) == 3
        assert all(isinstance(s, SubprogStatement) for s in stmts)

    def test_parse_empty_subroutine(self):
        """Test empty subroutine definition"""
        code = """
        substart EmptySub
        subend
        """
        ast = parse(code)
        stmts = [s for s in ast.statements if s is not None]
        assert len(stmts) == 1
        assert len(stmts[0].statements) == 0


class TestParserTypes:
    """Test type declarations"""

    def test_parse_all_types(self):
        """Test all supported types"""
        types = ["integer", "buffer", "string", "queue"]

        for type_name in types:
            code = f"var declare {type_name}"
            ast = parse(code)
            stmt = ast.statements[0]
            assert isinstance(stmt, DeclareStatement)
            assert stmt.var_type == type_name

    def test_parse_multiple_declarations(self):
        """Test multiple variable declarations"""
        code = """
        x declare integer
        y declare buffer
        z declare string
        q declare queue
        """
        ast = parse(code)
        stmts = [s for s in ast.statements if s is not None]
        assert len(stmts) == 4
        assert all(isinstance(s, DeclareStatement) for s in stmts)


class TestParserControlFlow:
    """Test control flow statements"""

    def test_parse_if_with_complex_condition(self):
        """Test if with complex conditions"""
        ast = parse("$a > 5 && $b < 10 if label")
        stmt = ast.statements[0]
        assert isinstance(stmt, IfStatement)
        assert stmt.label == "label"
        assert isinstance(stmt.condition, BinaryOperation)

    def test_parse_goto_to_various_labels(self):
        """Test goto with different label names"""
        labels = ["start", "end", "error_handler", "loop_1", "DONE"]
        for label in labels:
            ast = parse(f"goto {label}")
            stmt = ast.statements[0]
            assert stmt.label == label

    def test_parse_label_and_goto(self):
        """Test label definition and goto together"""
        code = """
        start:
            $x + 1 varset x
            $x < 10 if start
        """
        ast = parse(code)
        stmts = [s for s in ast.statements if s is not None]
        assert isinstance(stmts[0], LabelStatement)
        assert isinstance(stmts[2], IfStatement)


class TestParserCompletePrograms:
    """Test parsing complete programs"""

    def test_parse_simple_program(self):
        """Test complete simple program"""
        code = """
        counter declare integer
        0 varset $counter

        loop:
            $counter + 1 varset counter
            out $counter
            $counter < 10 if loop

        return
        """
        ast = parse(code)
        stmts = [s for s in ast.statements if s is not None]
        assert len(stmts) >= 6

    def test_parse_handler_with_subroutines(self):
        """Test handler with subroutine definitions"""
        code = """
        x declare integer
        5 varset $x

        subprog PrintValue
        return

        substart PrintValue
            out "Value: "
            out $x
        subend
        """
        ast = parse(code)
        stmts = [s for s in ast.statements if s is not None]

        # Find the substart
        substart = [s for s in stmts if isinstance(s, SubstartStatement)]
        assert len(substart) == 1
        assert substart[0].name == "PrintValue"

    def test_parse_event_handler(self):
        """Test complete event handler"""
        code = """
        data_buffer declare buffer
        length declare integer

        data_buffer bufferit 10 1 2 500 4
        sizeof($data_buffer) varset length

        DATA.IND generateup payload $data_buffer size $length

        return
        """
        ast = parse(code)
        stmts = [s for s in ast.statements if s is not None]
        assert any(isinstance(s, DeclareStatement) for s in stmts)
        assert any(isinstance(s, BufferitStatement) for s in stmts)
        assert any(isinstance(s, VarsetStatement) for s in stmts)
        assert any(isinstance(s, GenerateupStatement) for s in stmts)
        assert any(isinstance(s, ReturnStatement) for s in stmts)


class TestParserErrorHandling:
    """Test parser error cases"""

    def test_error_varset_first(self):
        """Test error when varset is first token"""
        with pytest.raises(ProtocolError) as exc_info:
            parse("varset x")
        assert "varset cannot be the first token" in str(exc_info.value)

    def test_error_if_first(self):
        """Test error when if is first token"""
        with pytest.raises(ProtocolError) as exc_info:
            parse("if label")
        assert "if cannot be the first token" in str(exc_info.value)

    def test_error_bufferit_first(self):
        """Test error when bufferit is first token"""
        with pytest.raises(ProtocolError) as exc_info:
            parse("bufferit 10")
        assert "bufferit needs buffer name first" in str(exc_info.value)

    def test_error_timer_first(self):
        """Test error when timer is first token"""
        with pytest.raises(ProtocolError) as exc_info:
            parse("timer $t 1000")
        assert "timer needs event name first" in str(exc_info.value)

    def test_error_queue_first(self):
        """Test error when queue is first token"""
        with pytest.raises(ProtocolError) as exc_info:
            parse("queue 100")
        assert "queue needs queue name first" in str(exc_info.value)

    def test_error_generateup_first(self):
        """Test error when generateup is first token"""
        with pytest.raises(ProtocolError) as exc_info:
            parse("generateup param 1")
        assert "generateup needs event name first" in str(exc_info.value)

    def test_error_eventdown_first(self):
        """Test error when eventdown is first token"""
        with pytest.raises(ProtocolError) as exc_info:
            parse("eventdown param 1")
        assert "eventdown needs event name first" in str(exc_info.value)

    def test_error_unexpected_token(self):
        """Test error on unexpected token in expression"""
        with pytest.raises(ProtocolError):
            # DECLARE cannot be in expression position
            parse("declare + 5 varset x")

    def test_error_missing_expected_token(self):
        """Test error when expected token is missing"""
        with pytest.raises(ProtocolError) as exc_info:
            parse("goto")  # Missing label
        assert "Expected IDENTIFIER" in str(exc_info.value)

    def test_error_unclosed_parenthesis(self):
        """Test error on unclosed parenthesis"""
        with pytest.raises(ProtocolError) as exc_info:
            parse("(1 + 2 varset x")
        assert "Expected RPAREN" in str(exc_info.value)


class TestParserEdgeCases:
    """Test edge cases"""

    def test_parse_empty_program(self):
        """Test parsing empty program"""
        ast = parse("")
        assert len(ast.statements) == 0

    def test_parse_only_newlines(self):
        """Test program with only newlines"""
        ast = parse("\n\n\n")
        # Newlines produce None statements which are filtered
        assert all(s is None for s in ast.statements)

    def test_parse_only_comments(self):
        """Test program with only comments"""
        code = """; Comment 1
; Comment 2
; Comment 3"""
        ast = parse(code)
        # Comments are removed, newlines produce None
        stmts = [s for s in ast.statements if s is not None]
        assert len(stmts) == 0

    def test_parse_expression_as_statement(self):
        """Test standalone expression (function call)"""
        ast = parse("MyFunction($param)")
        stmt = ast.statements[0]
        assert isinstance(stmt, ExpressionStatement)
        assert isinstance(stmt.expression, FunctionCall)

    def test_parse_identifier_without_call(self):
        """Test identifier followed by varset (not a function call)"""
        ast = parse("my_var varset x")
        # Should parse as: identifier 'my_var' followed by 'varset x'
        # But 'my_var' needs to be in expression position
        # Actually this should parse as: my_var varset x
        # Where my_var is treated as an expression
        stmt = ast.statements[0]
        assert isinstance(stmt, VarsetStatement)
        assert isinstance(stmt.expression, VariableExpression)
        assert stmt.expression.name == "my_var"


class TestParserVariableReferences:
    """Test variable reference parsing"""

    def test_parse_variable_with_dollar(self):
        """Test $variable syntax"""
        ast = parse("$my_var + 1 varset x")
        stmt = ast.statements[0]
        assert isinstance(stmt.expression.left, VariableExpression)
        assert stmt.expression.left.name == "my_var"

    def test_parse_identifier_as_variable(self):
        """Test identifier used as variable (without $)"""
        ast = parse("my_var varset x")
        stmt = ast.statements[0]
        assert isinstance(stmt.expression, VariableExpression)
        assert stmt.expression.name == "my_var"

    def test_parse_mixed_variable_references(self):
        """Test mixing $ and non-$ references"""
        ast = parse("$a + b varset c")
        stmt = ast.statements[0]
        assert isinstance(stmt.expression.left, VariableExpression)
        assert stmt.expression.left.name == "a"
        assert isinstance(stmt.expression.right, VariableExpression)
        assert stmt.expression.right.name == "b"
