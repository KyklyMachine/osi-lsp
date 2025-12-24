"""Comprehensive lexer tests for edge cases and full coverage"""

import pytest
from osi_lsp.parser.lexer import Lexer, TokenType
from osi_lsp.parser.errors import ProtocolError


class TestLexerEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_input(self):
        """Test lexing empty string"""
        lexer = Lexer("")
        tokens = lexer.tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_whitespace_only(self):
        """Test input with only whitespace"""
        lexer = Lexer("   \t  \n  ")
        tokens = lexer.tokenize()
        # Should have newline and EOF
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.NEWLINE

    def test_unterminated_string(self):
        """Test error on unterminated string"""
        lexer = Lexer('"hello world')
        with pytest.raises(ProtocolError) as exc_info:
            lexer.tokenize()
        assert "Unterminated string" in str(exc_info.value)

    def test_keywords_case_insensitive(self):
        """Test that keywords are case-insensitive"""
        lexer = Lexer("DECLARE Declare dEcLaRe")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert all(t.type == TokenType.DECLARE for t in tokens)

    def test_identifiers_with_dots(self):
        """Test identifiers with dots (like EVENT.NAME)"""
        lexer = Lexer("DATA.REQ ERROR.IND N_DATA.RSP")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert len(tokens) == 3
        assert all(t.type == TokenType.IDENTIFIER for t in tokens)
        assert tokens[0].value == "DATA.REQ"
        assert tokens[1].value == "ERROR.IND"
        assert tokens[2].value == "N_DATA.RSP"

    def test_identifiers_with_underscores(self):
        """Test identifiers with underscores"""
        lexer = Lexer("my_var __private _start var_123")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert len(tokens) == 4
        assert all(t.type == TokenType.IDENTIFIER for t in tokens)
        assert tokens[0].value == "my_var"
        assert tokens[1].value == "__private"
        assert tokens[2].value == "_start"
        assert tokens[3].value == "var_123"


class TestLexerStringEscapes:
    """Test all string escape sequences"""

    def test_escape_newline(self):
        lexer = Lexer('"line1\\nline2"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING_LITERAL
        assert tokens[0].value == "line1\nline2"

    def test_escape_tab(self):
        lexer = Lexer('"col1\\tcol2"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING_LITERAL
        assert tokens[0].value == "col1\tcol2"

    def test_escape_carriage_return(self):
        lexer = Lexer('"text\\rmore"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING_LITERAL
        assert tokens[0].value == "text\rmore"

    def test_escape_backslash(self):
        lexer = Lexer('"path\\\\to\\\\file"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING_LITERAL
        assert tokens[0].value == "path\\to\\file"

    def test_escape_quote(self):
        lexer = Lexer('"He said \\"Hello\\""')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING_LITERAL
        assert tokens[0].value == 'He said "Hello"'

    def test_unknown_escape(self):
        """Unknown escape sequences are kept as-is"""
        lexer = Lexer('"test\\x"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING_LITERAL
        assert tokens[0].value == "testx"


class TestLexerNumbers:
    """Test number tokenization edge cases"""

    def test_single_digit(self):
        lexer = Lexer("0 1 5 9")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert len(tokens) == 4
        assert all(t.type == TokenType.NUMBER for t in tokens)

    def test_large_numbers(self):
        lexer = Lexer("999999 1000000 2147483647")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert all(t.type == TokenType.NUMBER for t in tokens)

    def test_negative_numbers(self):
        lexer = Lexer("-1 -42 -999")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert all(t.type == TokenType.NUMBER for t in tokens)
        assert tokens[0].value == "-1"
        assert tokens[1].value == "-42"

    def test_minus_operator_vs_negative(self):
        """Test distinguishing minus operator from negative number"""
        lexer = Lexer("5 - 3")  # minus operator
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[1].type == TokenType.MINUS
        assert tokens[2].type == TokenType.NUMBER

        lexer = Lexer("5 -3")  # negative number
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[1].type == TokenType.NUMBER
        assert tokens[1].value == "-3"


class TestLexerCharCodes:
    """Test character code tokenization"""

    def test_single_digit_char_codes(self):
        lexer = Lexer("#0 #1 #9")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert all(t.type == TokenType.CHAR_CODE for t in tokens)
        assert tokens[0].value == "0"
        assert tokens[1].value == "1"
        assert tokens[2].value == "9"

    def test_large_char_codes(self):
        lexer = Lexer("#255 #65535")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert all(t.type == TokenType.CHAR_CODE for t in tokens)
        assert tokens[0].value == "255"
        assert tokens[1].value == "65535"


class TestLexerHandlers:
    """Test handler tokenization"""

    def test_handler_basic(self):
        lexer = Lexer("## INIT")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.HANDLER
        assert tokens[0].value == "INIT"

    def test_handler_with_extra_spaces(self):
        lexer = Lexer("##   HANDLER_NAME  ")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert tokens[0].type == TokenType.HANDLER
        assert tokens[0].value == "HANDLER_NAME"

    def test_handler_with_dots(self):
        lexer = Lexer("## DATA.REQ")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert tokens[0].type == TokenType.HANDLER
        assert tokens[0].value == "DATA.REQ"

    def test_handler_multiline(self):
        lexer = Lexer("## HANDLER\nx declare integer")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert tokens[0].type == TokenType.HANDLER
        assert tokens[1].type == TokenType.NEWLINE
        assert tokens[2].type == TokenType.IDENTIFIER


class TestLexerLabels:
    """Test label tokenization"""

    def test_simple_labels(self):
        lexer = Lexer("start: end: loop:")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert all(t.type == TokenType.LABEL for t in tokens)
        assert tokens[0].value == "start"
        assert tokens[1].value == "end"
        assert tokens[2].value == "loop"

    def test_label_with_underscore(self):
        lexer = Lexer("error_handler: check_timeout:")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert all(t.type == TokenType.LABEL for t in tokens)

    def test_colon_without_label(self):
        """Standalone colon is a delimiter"""
        lexer = Lexer(":")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert tokens[0].type == TokenType.COLON


class TestLexerComments:
    """Test comment handling"""

    def test_comment_full_line(self):
        lexer = Lexer("; This is a comment")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        # Comments are skipped in get_next_token
        assert len(tokens) == 0

    def test_comment_after_code(self):
        lexer = Lexer("declare ; comment\ninteger")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert tokens[0].type == TokenType.DECLARE
        assert tokens[1].type == TokenType.NEWLINE
        assert tokens[2].type == TokenType.INTEGER

    def test_multiple_comments(self):
        code = """; Comment 1
; Comment 2
declare ; Comment 3
; Comment 4"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type not in (TokenType.EOF, TokenType.NEWLINE)]
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.DECLARE


class TestLexerLineColumnTracking:
    """Test line and column tracking"""

    def test_single_line_columns(self):
        lexer = Lexer("declare integer")
        tokens = lexer.tokenize()
        assert tokens[0].line == 0
        assert tokens[0].column == 0  # 'declare' starts at column 0
        assert tokens[1].line == 0
        assert tokens[1].column == 8  # 'integer' starts at column 8

    def test_multiline_tracking(self):
        code = """x declare integer
y declare buffer
z declare string"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]

        # First line
        assert tokens[0].line == 0  # x
        assert tokens[1].line == 0  # declare
        assert tokens[2].line == 0  # integer

        # Newline
        assert tokens[3].type == TokenType.NEWLINE
        assert tokens[3].line == 0

        # Second line
        assert tokens[4].line == 1  # y
        assert tokens[5].line == 1  # declare
        assert tokens[6].line == 1  # buffer

    def test_column_after_tab(self):
        """Tabs should advance column properly"""
        lexer = Lexer("\tdeclare")
        tokens = lexer.tokenize()
        assert tokens[0].column == 1  # After tab


class TestLexerOperatorCombinations:
    """Test operator tokenization and combinations"""

    def test_comparison_operators_no_space(self):
        """Test that operators work without spaces"""
        lexer = Lexer("a==b c!=d e>=f g<=h")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        ops = [t for t in tokens if t.type in (TokenType.EQUAL, TokenType.NOT_EQUAL,
                                                TokenType.GREATER_EQUAL, TokenType.LESS_EQUAL)]
        assert len(ops) == 4

    def test_logical_operators(self):
        lexer = Lexer("a && b || c")
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert tokens[1].type == TokenType.AND
        assert tokens[1].value == "&&"
        assert tokens[3].type == TokenType.OR
        assert tokens[3].value == "||"

    def test_single_ampersand_is_unknown(self):
        """Single & should be unknown token"""
        lexer = Lexer("&")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.UNKNOWN

    def test_single_pipe_is_unknown(self):
        """Single | should be unknown token"""
        lexer = Lexer("|")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.UNKNOWN


class TestLexerComplexPrograms:
    """Test lexing complete programs"""

    def test_complete_handler(self):
        code = """## DATA_HANDLER
counter declare integer
buffer declare buffer
0 varset $counter

start:
    $counter + 1 varset counter
    $counter < 10 if start

return"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        # Verify we get all expected token types
        types = [t.type for t in tokens]
        assert TokenType.HANDLER in types
        assert TokenType.DECLARE in types
        assert TokenType.INTEGER in types
        assert TokenType.BUFFER in types
        assert TokenType.VARSET in types
        assert TokenType.LABEL in types
        assert TokenType.VARIABLE in types
        assert TokenType.PLUS in types
        assert TokenType.LESS in types
        assert TokenType.IF in types
        assert TokenType.RETURN in types

    def test_event_handler_with_params(self):
        code = """TIMEOUT.IND generateup code 1 message "Timeout occurred" """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        tokens = [t for t in tokens if t.type != TokenType.EOF]

        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "TIMEOUT.IND"
        assert tokens[1].type == TokenType.GENERATEUP
        assert tokens[2].type == TokenType.IDENTIFIER  # code
        assert tokens[3].type == TokenType.NUMBER  # 1
        assert tokens[4].type == TokenType.IDENTIFIER  # message
        assert tokens[5].type == TokenType.STRING_LITERAL

    def test_subroutine(self):
        code = """substart MySub
    out "In subroutine"
    return
subend"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]

        assert TokenType.SUBSTART in types
        assert TokenType.OUT in types
        assert TokenType.STRING_LITERAL in types
        assert TokenType.RETURN in types
        assert TokenType.SUBEND in types
