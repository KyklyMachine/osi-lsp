"""Lexer for Protocol Language"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional
from .errors import ProtocolError


class TokenType(Enum):
    """Token types for Protocol Language"""

    # Keywords
    DECLARE = auto()
    VARSET = auto()
    GOTO = auto()
    IF = auto()
    RETURN = auto()
    SUBPROG = auto()
    SUBSTART = auto()
    SUBEND = auto()
    DELETE = auto()

    # Operators
    BUFFERIT = auto()
    UNBUFFERIT = auto()
    CALCCRC = auto()
    TIMER = auto()
    UNTIMER = auto()
    QUEUE = auto()
    CLEARQUEUE = auto()
    DEQUEUE = auto()
    PEEK = auto()
    QCOUNT = auto()
    OUT = auto()

    # Events
    GENERATEUP = auto()
    EVENTDOWN = auto()

    # Types
    INTEGER = auto()
    BUFFER = auto()
    STRING = auto()
    QUEUE_TYPE = auto()

    # Functions
    SIZEOF = auto()
    COPY = auto()
    POS = auto()
    LOCGUIDE = auto()
    CURRENTSYSTEMNAME = auto()

    # Literals
    NUMBER = auto()
    STRING_LITERAL = auto()
    CHAR_CODE = auto()

    # Identifiers
    IDENTIFIER = auto()
    VARIABLE = auto()  # $variable
    LABEL = auto()     # label:
    HANDLER = auto()   # ## HANDLER_NAME

    # Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()

    EQUAL = auto()
    NOT_EQUAL = auto()
    GREATER = auto()
    LESS = auto()
    GREATER_EQUAL = auto()
    LESS_EQUAL = auto()

    AND = auto()
    OR = auto()

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    COLON = auto()
    DOT = auto()

    # Special
    COMMENT = auto()
    NEWLINE = auto()
    EOF = auto()

    # Error
    UNKNOWN = auto()


@dataclass
class Token:
    """Represents a single token"""
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}', {self.line}:{self.column})"


class Lexer:
    """Lexical analyzer for Protocol Language"""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 0
        self.column = 0
        self.current_char = self.text[0] if text else None

    def error(self, msg: str):
        """Raise lexer error"""
        raise ProtocolError(f"Lexer error: {msg}", self.line, self.column)

    def advance(self):
        """Move to the next character"""
        if self.current_char == '\n':
            self.line += 1
            self.column = 0
        else:
            self.column += 1

        self.pos += 1

        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def peek(self, offset=1) -> Optional[str]:
        """Look ahead at the next character(s) without consuming"""
        peek_pos = self.pos + offset
        if peek_pos < len(self.text):
            return self.text[peek_pos]
        return None

    def skip_whitespace(self):
        """Skip spaces and tabs (not newlines)"""
        while self.current_char and self.current_char in ' \t\r':
            self.advance()

    def skip_comment(self) -> Token:
        """Skip comment until end of line"""
        start_column = self.column
        comment_text = ''

        self.advance()  # skip ';'

        while self.current_char and self.current_char != '\n':
            comment_text += self.current_char
            self.advance()

        return Token(TokenType.COMMENT, comment_text.strip(), self.line, start_column)

    def read_number(self) -> Token:
        """Read a number literal"""
        start_column = self.column
        result = ''

        if self.current_char == '-':
            result += '-'
            self.advance()

        while self.current_char and self.current_char.isdigit():
            result += self.current_char
            self.advance()

        return Token(TokenType.NUMBER, result, self.line, start_column)

    def read_string(self) -> Token:
        """Read a string literal"""
        start_column = self.column
        result = ''
        self.advance()  # skip opening quote

        while self.current_char and self.current_char != '"':
            if self.current_char == '\\':
                self.advance()
                if self.current_char:
                    # Handle escape sequences
                    if self.current_char == 'n':
                        result += '\n'
                    elif self.current_char == 't':
                        result += '\t'
                    elif self.current_char == 'r':
                        result += '\r'
                    elif self.current_char == '\\':
                        result += '\\'
                    elif self.current_char == '"':
                        result += '"'
                    else:
                        result += self.current_char
                    self.advance()
            else:
                result += self.current_char
                self.advance()

        if self.current_char == '"':
            self.advance()  # skip closing quote
        else:
            self.error("Unterminated string literal")

        return Token(TokenType.STRING_LITERAL, result, self.line, start_column)

    def read_identifier(self) -> Token:
        """Read an identifier or keyword"""
        start_column = self.column
        result = ''

        # Identifiers can contain letters, digits, underscores, and dots
        # Hyphen '-' is removed to allow it as an operator without spaces
        while self.current_char and (self.current_char.isalnum() or
                                    self.current_char in '_.'):
            result += self.current_char
            self.advance()

        # Check for keywords (case-insensitive)
        keywords = {
            'declare': TokenType.DECLARE,
            'varset': TokenType.VARSET,
            'goto': TokenType.GOTO,
            'if': TokenType.IF,
            'return': TokenType.RETURN,
            'subprog': TokenType.SUBPROG,
            'substart': TokenType.SUBSTART,
            'subend': TokenType.SUBEND,
            'delete': TokenType.DELETE,
            'bufferit': TokenType.BUFFERIT,
            'unbufferit': TokenType.UNBUFFERIT,
            'calccrc': TokenType.CALCCRC,
            'timer': TokenType.TIMER,
            'untimer': TokenType.UNTIMER,
            'queue': TokenType.QUEUE,
            'clearqueue': TokenType.CLEARQUEUE,
            'dequeue': TokenType.DEQUEUE,
            'peek': TokenType.PEEK,
            'qcount': TokenType.QCOUNT,
            'generateup': TokenType.GENERATEUP,
            'eventdown': TokenType.EVENTDOWN,
            'integer': TokenType.INTEGER,
            'buffer': TokenType.BUFFER,
            'string': TokenType.STRING,
            'sizeof': TokenType.SIZEOF,
            'copy': TokenType.COPY,
            'pos': TokenType.POS,
            'out': TokenType.OUT,
            'locguide': TokenType.LOCGUIDE,
            'currentsystemname': TokenType.CURRENTSYSTEMNAME,
        }

        token_type = keywords.get(result.lower(), TokenType.IDENTIFIER)
        return Token(token_type, result, self.line, start_column)

    def read_variable(self) -> Token:
        """Read a variable ($name)"""
        start_column = self.column
        self.advance()  # skip '$'

        result = ''
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()

        return Token(TokenType.VARIABLE, result, self.line, start_column)

    def read_char_code(self) -> Token:
        """Read a character code (#255)"""
        start_column = self.column
        self.advance()  # skip '#'

        result = ''
        while self.current_char and self.current_char.isdigit():
            result += self.current_char
            self.advance()

        return Token(TokenType.CHAR_CODE, result, self.line, start_column)

    def read_handler(self) -> Token:
        """Read a handler name (## NAME)"""
        start_column = self.column
        self.advance()  # skip first #
        self.advance()  # skip second #

        # Skip whitespace after ##
        while self.current_char and self.current_char in ' \t':
            self.advance()

        result = ''
        while self.current_char and self.current_char not in '\n\r':
            result += self.current_char
            self.advance()

        return Token(TokenType.HANDLER, result.strip(), self.line, start_column)

    def get_next_token(self) -> Token:
        """Get the next token from the input"""
        while self.current_char:
            # Skip whitespace (but not newlines)
            if self.current_char in ' \t\r':
                self.skip_whitespace()
                continue

            # Comment
            if self.current_char == ';':
                self.skip_comment()
                continue

            # Newline
            if self.current_char == '\n':
                token = Token(TokenType.NEWLINE, '\\n', self.line, self.column)
                self.advance()
                return token

            # Handler (## NAME)
            if self.current_char == '#' and self.peek() == '#':
                return self.read_handler()

            # Character code (#255)
            if self.current_char == '#' and self.peek() and self.peek().isdigit():
                return self.read_char_code()

            # Numbers (including negative)
            if self.current_char.isdigit():
                return self.read_number()

            if self.current_char == '-' and self.peek() and self.peek().isdigit():
                return self.read_number()

            # Strings
            if self.current_char == '"':
                return self.read_string()

            # Variables
            if self.current_char == '$':
                return self.read_variable()

            # Identifiers and keywords
            if self.current_char.isalpha() or self.current_char == '_':
                token = self.read_identifier()
                # Check if it's a label (followed by :)
                if self.current_char == ':':
                    token.type = TokenType.LABEL
                    self.advance()  # consume ':'
                return token

            # Operators
            if self.current_char == '+':
                token = Token(TokenType.PLUS, '+', self.line, self.column)
                self.advance()
                return token

            if self.current_char == '-':
                token = Token(TokenType.MINUS, '-', self.line, self.column)
                self.advance()
                return token

            if self.current_char == '*':
                token = Token(TokenType.MULTIPLY, '*', self.line, self.column)
                self.advance()
                return token

            if self.current_char == '/':
                token = Token(TokenType.DIVIDE, '/', self.line, self.column)
                self.advance()
                return token

            if self.current_char == '%':
                token = Token(TokenType.MODULO, '%', self.line, self.column)
                self.advance()
                return token

            if self.current_char == '=':
                if self.peek() == '=':
                    token = Token(TokenType.EQUAL, '==', self.line, self.column)
                    self.advance()
                    self.advance()
                    return token

            if self.current_char == '!':
                if self.peek() == '=':
                    token = Token(TokenType.NOT_EQUAL, '!=', self.line, self.column)
                    self.advance()
                    self.advance()
                    return token

            if self.current_char == '>':
                if self.peek() == '=':
                    token = Token(TokenType.GREATER_EQUAL, '>=', self.line, self.column)
                    self.advance()
                    self.advance()
                    return token
                else:
                    token = Token(TokenType.GREATER, '>', self.line, self.column)
                    self.advance()
                    return token

            if self.current_char == '<':
                if self.peek() == '=':
                    token = Token(TokenType.LESS_EQUAL, '<=', self.line, self.column)
                    self.advance()
                    self.advance()
                    return token
                else:
                    token = Token(TokenType.LESS, '<', self.line, self.column)
                    self.advance()
                    return token

            if self.current_char == '&':
                if self.peek() == '&':
                    token = Token(TokenType.AND, '&&', self.line, self.column)
                    self.advance()
                    self.advance()
                    return token

            if self.current_char == '|':
                if self.peek() == '|':
                    token = Token(TokenType.OR, '||', self.line, self.column)
                    self.advance()
                    self.advance()
                    return token

            # Delimiters
            if self.current_char == '(':
                token = Token(TokenType.LPAREN, '(', self.line, self.column)
                self.advance()
                return token

            if self.current_char == ')':
                token = Token(TokenType.RPAREN, ')', self.line, self.column)
                self.advance()
                return token

            if self.current_char == ',':
                token = Token(TokenType.COMMA, ',', self.line, self.column)
                self.advance()
                return token

            if self.current_char == ':':
                token = Token(TokenType.COLON, ':', self.line, self.column)
                self.advance()
                return token

            if self.current_char == '.':
                token = Token(TokenType.DOT, '.', self.line, self.column)
                self.advance()
                return token

            # Unknown character
            token = Token(TokenType.UNKNOWN, self.current_char, self.line, self.column)
            self.advance()
            return token

        return Token(TokenType.EOF, '', self.line, self.column)

    def tokenize(self) -> List[Token]:
        """Tokenize the entire input"""
        tokens = []
        while True:
            token = self.get_next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return tokens
