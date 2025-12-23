"""Parser for Protocol Language"""

from typing import List, Optional, Dict, Any
from .lexer import Token, TokenType
from .ast_nodes import *
from .errors import ProtocolError


class Parser:
    """Recursive descent parser for Protocol Language"""

    def __init__(self, tokens: List[Token]):
        self.tokens = [t for t in tokens if t.type != TokenType.COMMENT]
        self.pos = 0
        self.current_token = self.tokens[0] if self.tokens else Token(TokenType.EOF, '', 0, 0)

    def error(self, msg: str):
        """Raise parser error"""
        raise ProtocolError(
            f"Parser error: {msg}",
            self.current_token.line,
            self.current_token.column
        )

    def advance(self):
        """Move to the next token"""
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = Token(TokenType.EOF, '', self.current_token.line, self.current_token.column)

    def peek(self, offset=1) -> Token:
        """Look ahead at the next token(s)"""
        peek_pos = self.pos + offset
        if peek_pos < len(self.tokens):
            return self.tokens[peek_pos]
        return Token(TokenType.EOF, '', self.current_token.line, self.current_token.column)

    def expect(self, token_type: TokenType) -> Token:
        """Expect a specific token type"""
        if self.current_token.type != token_type:
            self.error(f"Expected {token_type.name}, got {self.current_token.type.name}")
        token = self.current_token
        self.advance()
        return token

    def parse(self) -> Program:
        """Parse the entire program"""
        statements = []

        while self.current_token.type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)

        return Program(statements=statements)

    def parse_statement(self) -> Optional[Statement]:
        """Parse a single statement"""
        token = self.current_token

        # Newline (empty statement)
        if token.type == TokenType.NEWLINE:
            self.advance()
            return None

        # Label definition
        if token.type == TokenType.LABEL:
            return self.parse_label()

        # Declaration
        if self.peek().type == TokenType.DECLARE:
            return self.parse_declare()

        # Keywords
        if token.type == TokenType.VARSET:
            self.error("varset cannot be the first token (need expression first)")

        if token.type == TokenType.GOTO:
            return self.parse_goto()

        if token.type == TokenType.IF:
            self.error("if cannot be the first token (need condition first)")

        if token.type == TokenType.RETURN:
            return self.parse_return()

        if token.type == TokenType.BUFFERIT:
            self.error("bufferit needs buffer name first")

        if token.type == TokenType.UNBUFFERIT:
            return self.parse_unbufferit()

        if token.type == TokenType.CALCCRC:
            return self.parse_calccrc()

        if token.type == TokenType.TIMER:
            self.error("timer needs event name first")

        if token.type == TokenType.UNTIMER:
            return self.parse_untimer()

        if token.type == TokenType.QUEUE:
            self.error("queue needs queue name first")

        if token.type == TokenType.CLEARQUEUE:
            return self.parse_clearqueue()

        if token.type == TokenType.GENERATEUP:
            self.error("generateup needs event name first")

        if token.type == TokenType.EVENTDOWN:
            self.error("eventdown needs event name first")

        if token.type == TokenType.OUT:
            return self.parse_out()

        if token.type == TokenType.SUBPROG:
            return self.parse_subprog()

        if token.type == TokenType.SUBSTART:
            return self.parse_substart()

        if token.type == TokenType.SUBEND:
            return self.parse_subend()

        if token.type == TokenType.DELETE:
            return self.parse_delete()

        # Expression-based statements (expression followed by operation)
        if token.type in (TokenType.IDENTIFIER, TokenType.VARIABLE, TokenType.NUMBER,
                         TokenType.STRING_LITERAL, TokenType.LPAREN):
            return self.parse_expression_statement()

        # Unknown statement
        if token.type != TokenType.EOF:
            self.error(f"Unknown statement starting with {token.type.name}")

        return None

    def parse_expression_statement(self) -> Optional[Statement]:
        """Parse statements that start with an expression"""
        # Save position in case we need to backtrack
        start_pos = self.pos
        expr = self.parse_expression()

        # Check what follows the expression
        if self.current_token.type == TokenType.VARSET:
            return self.parse_varset_with_expr(expr)

        if self.current_token.type == TokenType.BUFFERIT:
            # expr is the buffer name (should be identifier)
            if isinstance(expr, VariableExpression):
                return self.parse_bufferit(expr.name, expr.line, expr.column)
            else:
                self.error("bufferit requires identifier before it")

        if self.current_token.type == TokenType.IF:
            return self.parse_if_with_condition(expr)

        if self.current_token.type == TokenType.TIMER:
            # expr is the event name
            if isinstance(expr, VariableExpression):
                return self.parse_timer(expr.name, expr.line, expr.column)
            else:
                self.error("timer requires event name before it")

        if self.current_token.type == TokenType.QUEUE:
            # expr is the queue name
            if isinstance(expr, VariableExpression):
                return self.parse_queue_with_name(expr.name, expr.line, expr.column)
            else:
                self.error("queue requires queue name before it")

        if self.current_token.type == TokenType.GENERATEUP:
            # expr is the event name (identifier)
            if isinstance(expr, VariableExpression):
                return self.parse_generateup(expr.name, expr.line, expr.column)
            else:
                self.error("generateup requires event name before it")

        if self.current_token.type == TokenType.EVENTDOWN:
            # expr is the event name
            if isinstance(expr, VariableExpression):
                return self.parse_eventdown(expr.name, expr.line, expr.column)
            else:
                self.error("eventdown requires event name before it")

        # If no specific statement keyword follows, treat as an expression statement
        # (e.g. standalone function call)
        return ExpressionStatement(
            expression=expr,
            line=expr.line,
            column=expr.column
        )

    def parse_declare(self) -> DeclareStatement:
        """Parse variable declaration: name declare type"""
        name_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.DECLARE)
        type_token = self.current_token

        if type_token.type not in (TokenType.INTEGER, TokenType.BUFFER, TokenType.STRING, TokenType.QUEUE, TokenType.QUEUE_TYPE):
            self.error(f"Expected type (integer, buffer, string, queue), got {type_token.value}")

        var_type = type_token.value.lower()
        self.advance()

        return DeclareStatement(
            name=name_token.value,
            var_type=var_type,
            line=name_token.line,
            column=name_token.column
        )

    def parse_varset_with_expr(self, expr: Expression) -> VarsetStatement:
        """Parse varset with already-parsed expression"""
        self.expect(TokenType.VARSET)
        
        var_token = self.current_token
        if var_token.type == TokenType.VARIABLE:
            self.advance()
        elif var_token.type == TokenType.IDENTIFIER:
            self.advance()
        else:
            self.error(f"Expected variable or identifier, got {var_token.type.name}")

        return VarsetStatement(
            expression=expr,
            variable=var_token.value,
            line=var_token.line,
            column=var_token.column
        )

    def parse_bufferit(self, buffer_name: str, line: int, column: int) -> BufferitStatement:
        """Parse bufferit: buffer bufferit length value1 len1 ..."""
        self.expect(TokenType.BUFFERIT)

        # Parse total length
        total_length = self.parse_expression()

        # Parse fields (value, length pairs)
        fields = []
        while self.current_token.type not in (TokenType.EOF, TokenType.IDENTIFIER,
                                              TokenType.GOTO, TokenType.RETURN, TokenType.LABEL,
                                              TokenType.OUT, TokenType.SUBPROG, TokenType.SUBSTART,
                                              TokenType.SUBEND, TokenType.NEWLINE) and \
              self.current_token.type not in (TokenType.UNBUFFERIT, TokenType.CALCCRC,
                                             TokenType.UNTIMER, TokenType.CLEARQUEUE, TokenType.DELETE):
            value = self.parse_expression()

            if self.current_token.type == TokenType.EOF:
                break

            length = self.parse_expression()
            fields.append((value, length))

        return BufferitStatement(
            buffer_name=buffer_name,
            total_length=total_length,
            fields=fields,
            line=line,
            column=column
        )

    def parse_unbufferit(self) -> UnbufferitStatement:
        """Parse unbufferit: unbufferit buffer var1 len1 ..."""
        token = self.expect(TokenType.UNBUFFERIT)

        # Parse buffer (can be variable or identifier)
        buffer_token = self.current_token
        if buffer_token.type == TokenType.VARIABLE:
            buffer_name = buffer_token.value
            self.advance()
        elif buffer_token.type == TokenType.IDENTIFIER:
            buffer_name = buffer_token.value
            self.advance()
        else:
            self.error(f"Expected buffer name, got {buffer_token.type.name}")

        # Parse fields (variable, length pairs)
        fields = []
        while self.current_token.type not in (TokenType.EOF, TokenType.NEWLINE) and \
              self.current_token.type not in (TokenType.GOTO, TokenType.RETURN, TokenType.LABEL,
                                             TokenType.OUT, TokenType.SUBPROG):
            if self.current_token.type == TokenType.VARIABLE:
                var_name = self.current_token.value
                self.advance()
            elif self.current_token.type == TokenType.IDENTIFIER:
                var_name = self.current_token.value
                self.advance()
            else:
                break

            length = self.parse_expression()
            fields.append((var_name, length))

        return UnbufferitStatement(
            buffer_name=buffer_name,
            fields=fields,
            line=token.line,
            column=token.column
        )

    def parse_calccrc(self) -> CalccrcStatement:
        """Parse calccrc: calccrc result buffer"""
        token = self.expect(TokenType.CALCCRC)

        # Parse result variable
        result_token = self.expect(TokenType.VARIABLE)

        # Parse buffer expression
        buffer_expr = self.parse_expression()

        return CalccrcStatement(
            result_var=result_token.value,
            buffer_expr=buffer_expr,
            line=token.line,
            column=token.column
        )

    def parse_timer(self, event_name: str, line: int, column: int) -> TimerStatement:
        """Parse timer: event timer timer_var delay params..."""
        self.expect(TokenType.TIMER)

        # Parse timer variable
        var_token = self.current_token
        if var_token.type == TokenType.VARIABLE:
            self.advance()
        elif var_token.type == TokenType.IDENTIFIER:
            self.advance()
        else:
            self.error(f"Expected variable or identifier for timer, got {var_token.type.name}")
        
        timer_var = var_token.value

        # Parse delay
        delay = self.parse_expression()

        # Parse optional parameters (key value pairs)
        parameters = {}
        while self.current_token.type == TokenType.IDENTIFIER:
            key = self.current_token.value
            self.advance()
            value = self.parse_expression()
            parameters[key] = value

        return TimerStatement(
            event_name=event_name,
            timer_var=timer_var,
            delay=delay,
            parameters=parameters,
            line=line,
            column=column
        )

    def parse_untimer(self) -> UntimerStatement:
        """Parse untimer: untimer timer_id"""
        token = self.expect(TokenType.UNTIMER)
        timer_id = self.parse_expression()

        return UntimerStatement(
            timer_id=timer_id,
            line=token.line,
            column=token.column
        )

    def parse_queue_with_name(self, queue_name: str, line: int, column: int) -> QueueStatement:
        """Parse queue: queue queue_name value"""
        self.expect(TokenType.QUEUE)
        value = self.parse_expression()

        return QueueStatement(
            queue_name=queue_name,
            value=value,
            line=line,
            column=column
        )

    def parse_clearqueue(self) -> ClearqueueStatement:
        """Parse clearqueue: clearqueue queue_name"""
        token = self.expect(TokenType.CLEARQUEUE)

        queue_token = self.current_token
        if queue_token.type in (TokenType.VARIABLE, TokenType.IDENTIFIER):
            queue_name = queue_token.value
            self.advance()
        else:
            self.error(f"Expected queue name, got {queue_token.type.name}")

        return ClearqueueStatement(
            queue_name=queue_name,
            line=token.line,
            column=token.column
        )

    def parse_generateup(self, event_name: str, line: int, column: int) -> GenerateupStatement:
        """Parse generateup: EVENT.NAME generateup params..."""
        self.expect(TokenType.GENERATEUP)

        # Parse optional parameters
        parameters = {}
        while self.current_token.type == TokenType.IDENTIFIER:
            key = self.current_token.value
            self.advance()
            value = self.parse_expression()
            parameters[key] = value

        return GenerateupStatement(
            event_name=event_name,
            parameters=parameters,
            line=line,
            column=column
        )

    def parse_eventdown(self, event_name: str, line: int, column: int) -> EventdownStatement:
        """Parse eventdown: EVENT.NAME eventdown params..."""
        self.expect(TokenType.EVENTDOWN)

        # Parse optional parameters
        parameters = {}
        while self.current_token.type == TokenType.IDENTIFIER:
            key = self.current_token.value
            self.advance()
            value = self.parse_expression()
            parameters[key] = value

        return EventdownStatement(
            event_name=event_name,
            parameters=parameters,
            line=line,
            column=column
        )

    def parse_goto(self) -> GotoStatement:
        """Parse goto: goto label"""
        token = self.expect(TokenType.GOTO)
        label = self.expect(TokenType.IDENTIFIER).value

        return GotoStatement(
            label=label,
            line=token.line,
            column=token.column
        )

    def parse_if_with_condition(self, condition: Expression) -> IfStatement:
        """Parse if with already-parsed condition"""
        token = self.expect(TokenType.IF)
        label = self.expect(TokenType.IDENTIFIER).value

        return IfStatement(
            condition=condition,
            label=label,
            line=token.line,
            column=token.column
        )

    def parse_return(self) -> ReturnStatement:
        """Parse return"""
        token = self.expect(TokenType.RETURN)

        return ReturnStatement(
            line=token.line,
            column=token.column
        )

    def parse_label(self) -> LabelStatement:
        """Parse label: label:"""
        token = self.expect(TokenType.LABEL)

        return LabelStatement(
            name=token.value,
            line=token.line,
            column=token.column
        )

    def parse_out(self) -> OutStatement:
        """Parse out: out expression"""
        token = self.expect(TokenType.OUT)
        expression = self.parse_expression()

        return OutStatement(
            expression=expression,
            line=token.line,
            column=token.column
        )

    def parse_subprog(self) -> SubprogStatement:
        """Parse subprog: subprog name"""
        token = self.expect(TokenType.SUBPROG)
        name = self.expect(TokenType.IDENTIFIER).value

        return SubprogStatement(
            name=name,
            line=token.line,
            column=token.column
        )

    def parse_substart(self) -> SubstartStatement:
        """Parse substart: substart name ... subend"""
        token = self.expect(TokenType.SUBSTART)
        name = self.expect(TokenType.IDENTIFIER).value

        statements = []
        while self.current_token.type not in (TokenType.SUBEND, TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)

        if self.current_token.type == TokenType.SUBEND:
            self.advance()

        return SubstartStatement(
            name=name,
            line=token.line,
            column=token.column,
            statements=statements
        )

    def parse_subend(self) -> SubendStatement:
        """Parse subend"""
        token = self.expect(TokenType.SUBEND)

        return SubendStatement(
            line=token.line,
            column=token.column
        )

    def parse_delete(self) -> DeleteStatement:
        """Parse delete: delete string start length"""
        token = self.expect(TokenType.DELETE)

        string_token = self.current_token
        if string_token.type in (TokenType.VARIABLE, TokenType.IDENTIFIER):
            string_var = string_token.value
            self.advance()
        else:
            self.error(f"Expected string variable, got {string_token.type.name}")

        start = self.parse_expression()
        length = self.parse_expression()

        return DeleteStatement(
            string_var=string_var,
            start=start,
            length=length,
            line=token.line,
            column=token.column
        )

    def parse_expression(self) -> Expression:
        """Parse expression with operator precedence"""
        return self.parse_logical_or()

    def parse_logical_or(self) -> Expression:
        """Parse logical OR (||)"""
        left = self.parse_logical_and()

        while self.current_token.type == TokenType.OR:
            op_token = self.current_token
            self.advance()
            right = self.parse_logical_and()
            left = BinaryOperation(
                left=left,
                operator='||',
                right=right,
                line=op_token.line,
                column=op_token.column
            )

        return left

    def parse_logical_and(self) -> Expression:
        """Parse logical AND (&&)"""
        left = self.parse_equality()

        while self.current_token.type == TokenType.AND:
            op_token = self.current_token
            self.advance()
            right = self.parse_equality()
            left = BinaryOperation(
                left=left,
                operator='&&',
                right=right,
                line=op_token.line,
                column=op_token.column
            )

        return left

    def parse_equality(self) -> Expression:
        """Parse equality (==, !=)"""
        left = self.parse_comparison()

        while self.current_token.type in (TokenType.EQUAL, TokenType.NOT_EQUAL):
            op_token = self.current_token
            op = '==' if op_token.type == TokenType.EQUAL else '!='
            self.advance()
            right = self.parse_comparison()
            left = BinaryOperation(
                left=left,
                operator=op,
                right=right,
                line=op_token.line,
                column=op_token.column
            )

        return left

    def parse_comparison(self) -> Expression:
        """Parse comparison (<, >, <=, >=)"""
        left = self.parse_additive()

        while self.current_token.type in (TokenType.LESS, TokenType.GREATER,
                                         TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL):
            op_token = self.current_token
            op_map = {
                TokenType.LESS: '<',
                TokenType.GREATER: '>',
                TokenType.LESS_EQUAL: '<=',
                TokenType.GREATER_EQUAL: '>='
            }
            op = op_map[op_token.type]
            self.advance()
            right = self.parse_additive()
            left = BinaryOperation(
                left=left,
                operator=op,
                right=right,
                line=op_token.line,
                column=op_token.column
            )

        return left

    def parse_additive(self) -> Expression:
        """Parse addition and subtraction (+, -)"""
        left = self.parse_multiplicative()

        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            op_token = self.current_token
            op = '+' if op_token.type == TokenType.PLUS else '-'
            self.advance()
            right = self.parse_multiplicative()
            left = BinaryOperation(
                left=left,
                operator=op,
                right=right,
                line=op_token.line,
                column=op_token.column
            )

        return left

    def parse_multiplicative(self) -> Expression:
        """Parse multiplication, division, modulo (*, /, %)"""
        left = self.parse_primary()

        while self.current_token.type in (TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            op_token = self.current_token
            op_map = {
                TokenType.MULTIPLY: '*',
                TokenType.DIVIDE: '/',
                TokenType.MODULO: '%'
            }
            op = op_map[op_token.type]
            self.advance()
            right = self.parse_primary()
            left = BinaryOperation(
                left=left,
                operator=op,
                right=right,
                line=op_token.line,
                column=op_token.column
            )

        return left

    def parse_primary(self) -> Expression:
        """Parse primary expressions (literals, variables, function calls, parentheses)"""
        token = self.current_token

        # Number
        if token.type == TokenType.NUMBER:
            self.advance()
            return NumberLiteral(
                value=int(token.value),
                line=token.line,
                column=token.column
            )

        # String
        if token.type == TokenType.STRING_LITERAL:
            self.advance()
            return StringLiteral(
                value=token.value,
                line=token.line,
                column=token.column
            )

        # Character code
        if token.type == TokenType.CHAR_CODE:
            self.advance()
            return CharCodeLiteral(
                value=int(token.value),
                line=token.line,
                column=token.column
            )

        # Variable
        if token.type == TokenType.VARIABLE:
            self.advance()
            return VariableExpression(
                name=token.value,
                line=token.line,
                column=token.column
            )

        # Function call or identifier
        if token.type == TokenType.IDENTIFIER:
            return self.parse_identifier_or_call()

        # Function names
        if token.type in (TokenType.SIZEOF, TokenType.COPY, TokenType.POS,
                         TokenType.DEQUEUE, TokenType.PEEK, TokenType.QCOUNT,
                         TokenType.LOCGUIDE, TokenType.CURRENTSYSTEMNAME):
            return self.parse_function_call()

        # Parenthesized expression
        if token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        self.error(f"Unexpected token in expression: {token.type.name}")

    def parse_identifier_or_call(self) -> Expression:
        """Parse identifier or function call"""
        token = self.current_token
        self.advance()

        # Check if it's a function call
        if self.current_token.type == TokenType.LPAREN:
            self.advance()
            arguments = []

            if self.current_token.type != TokenType.RPAREN:
                arguments.append(self.parse_expression())

                while self.current_token.type == TokenType.COMMA:
                    self.advance()
                    arguments.append(self.parse_expression())

            self.expect(TokenType.RPAREN)

            return FunctionCall(
                name=token.value,
                arguments=arguments,
                line=token.line,
                column=token.column
            )

        # Just an identifier (treated as variable without $)
        return VariableExpression(
            name=token.value,
            line=token.line,
            column=token.column
        )

    def parse_function_call(self) -> FunctionCall:
        """Parse function call"""
        token = self.current_token
        func_name = token.value if token.type == TokenType.IDENTIFIER else token.type.name.lower()
        self.advance()

        self.expect(TokenType.LPAREN)

        arguments = []
        if self.current_token.type != TokenType.RPAREN:
            arguments.append(self.parse_expression())

            while self.current_token.type == TokenType.COMMA:
                self.advance()
                arguments.append(self.parse_expression())

        self.expect(TokenType.RPAREN)

        return FunctionCall(
            name=func_name,
            arguments=arguments,
            line=token.line,
            column=token.column
        )
