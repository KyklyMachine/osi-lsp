"""Semantic analyzer for Protocol Language"""

from typing import Optional
from ..parser.ast_nodes import *
from .symbol_table import SymbolTable, SymbolType


class SemanticAnalyzer(ASTVisitor):
    """
    Semantic analyzer that builds the symbol table
    and performs type checking.
    """

    def __init__(self, symbol_table: SymbolTable, file_uri: str = ""):
        self.symbol_table = symbol_table
        self.file_uri = file_uri
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def analyze(self, ast: Program):
        """Analyze the AST and build symbol table"""
        self.visit_program(ast)

    def add_error(self, line: int, column: int, message: str):
        """Add an error"""
        self.errors.append(f"{line}:{column}: {message}")

    def add_warning(self, line: int, column: int, message: str):
        """Add a warning"""
        self.warnings.append(f"{line}:{column}: {message}")

    def visit_program(self, node: Program):
        """Visit program node"""
        # First pass: register all labels and subroutines
        for statement in node.statements:
            if isinstance(statement, LabelStatement):
                if not self.symbol_table.declare_label(statement.name, statement.line, statement.column, file_uri=self.file_uri):
                    self.add_error(statement.line, statement.column, f"Label '{statement.name}' is already defined")
            elif isinstance(statement, SubstartStatement):
                if not self.symbol_table.declare_subroutine(statement.name, statement.line, statement.column, file_uri=self.file_uri):
                    self.add_error(statement.line, statement.column, f"Subroutine '{statement.name}' is already defined")

        # Second pass: analyze all statements
        for statement in node.statements:
            # Skip declarations of labels/subs in second pass to avoid re-declaration errors
            # (SymbolTable.declare_* returns False if already exists)
            # Actually, declare_* logic in visit_label/visit_substart would trigger "already defined" again.
            # So we should modify visit_label and visit_substart to NOT re-declare or check existence without error if it's the same definition.
            # OR simpler: Don't call accept on Label/Substart in the loop if we handled them?
            # But we want to visit contents of Substart.
            # Better approach:
            # Remove declare_label from visit_label and declare_subroutine from visit_substart
            # and rely on the pre-pass in visit_program.
            statement.accept(self)

    # Removed visit_handler


    def visit_declare(self, node: DeclareStatement):
        """Visit declaration"""
        # Map type string to SymbolType
        type_map = {
            'integer': SymbolType.INTEGER,
            'buffer': SymbolType.BUFFER,
            'string': SymbolType.STRING,
            'queue': SymbolType.QUEUE
        }

        symbol_type = type_map.get(node.var_type, SymbolType.UNKNOWN)

        if not self.symbol_table.declare_symbol(node.name, symbol_type, node.line, node.column, file_uri=self.file_uri):
            self.add_error(node.line, node.column, f"Variable '{node.name}' is already declared")

    def visit_varset(self, node: VarsetStatement):
        """Visit varset statement"""
        # Check if variable is declared
        symbol = self.symbol_table.get_symbol(node.variable)
        if not symbol:
            self.add_error(node.line, node.column, f"Variable '{node.variable}' is not declared")
        else:
            # Mark as initialized
            self.symbol_table.initialize_symbol(node.variable)

            # Visit expression
            expr_type = self.get_expression_type(node.expression)

            # Type checking (simplified - a full implementation would be more complex)
            if expr_type != SymbolType.UNKNOWN and symbol.symbol_type != expr_type:
                self.add_warning(
                    node.line, node.column,
                    f"Type mismatch: assigning {expr_type.value} to {symbol.symbol_type.value}"
                )

        # Visit expression to mark variables as used
        node.expression.accept(self)

    def visit_bufferit(self, node: BufferitStatement):
        """Visit bufferit statement"""
        # Check buffer variable
        symbol = self.symbol_table.get_symbol(node.buffer_name)
        if symbol:
            self.symbol_table.initialize_symbol(node.buffer_name)

        # Visit expressions
        node.total_length.accept(self)
        for value, length in node.fields:
            value.accept(self)
            length.accept(self)

    def visit_unbufferit(self, node: UnbufferitStatement):
        """Visit unbufferit statement"""
        # Check buffer
        buffer_symbol = self.symbol_table.get_symbol(node.buffer_name)
        if not buffer_symbol:
            self.add_error(node.line, node.column, f"Buffer '{node.buffer_name}' is not declared")

        # Check field variables and mark as initialized
        for var_name, length in node.fields:
            symbol = self.symbol_table.get_symbol(var_name)
            if not symbol:
                self.add_error(node.line, node.column, f"Variable '{var_name}' is not declared")
            else:
                self.symbol_table.initialize_symbol(var_name)

            length.accept(self)

    def visit_calccrc(self, node: CalccrcStatement):
        """Visit calccrc statement"""
        # Mark result as initialized
        result_symbol = self.symbol_table.get_symbol(node.result_var)
        if result_symbol:
            self.symbol_table.initialize_symbol(node.result_var)
        else:
            self.add_error(node.line, node.column, f"Variable '{node.result_var}' is not declared")

        # Visit buffer expression
        node.buffer_expr.accept(self)

    def visit_timer(self, node: TimerStatement):
        """Visit timer statement"""
        # Check timer variable
        timer_symbol = self.symbol_table.get_symbol(node.timer_var)
        if timer_symbol:
            self.symbol_table.initialize_symbol(node.timer_var)

        # Visit delay expression
        node.delay.accept(self)

        # Visit parameter expressions
        for value in node.parameters.values():
            if isinstance(value, ASTNode):
                value.accept(self)

    def visit_untimer(self, node: UntimerStatement):
        """Visit untimer statement"""
        node.timer_id.accept(self)

    def visit_queue(self, node: QueueStatement):
        """Visit queue statement"""
        # Check queue variable
        queue_symbol = self.symbol_table.get_symbol(node.queue_name)
        if not queue_symbol:
            self.add_error(node.line, node.column, f"Queue '{node.queue_name}' is not declared")
        elif queue_symbol.symbol_type != SymbolType.QUEUE:
            self.add_warning(node.line, node.column, f"'{node.queue_name}' is not a queue")

        node.value.accept(self)

    def visit_clearqueue(self, node: ClearqueueStatement):
        """Visit clearqueue statement"""
        queue_symbol = self.symbol_table.get_symbol(node.queue_name)
        if not queue_symbol:
            self.add_error(node.line, node.column, f"Queue '{node.queue_name}' is not declared")

    def visit_generateup(self, node: GenerateupStatement):
        """Visit generateup statement"""
        # Visit parameter expressions
        for value in node.parameters.values():
            if isinstance(value, ASTNode):
                value.accept(self)

    def visit_eventdown(self, node: EventdownStatement):
        """Visit eventdown statement"""
        # Visit parameter expressions
        for value in node.parameters.values():
            if isinstance(value, ASTNode):
                value.accept(self)

    def visit_goto(self, node: GotoStatement):
        """Visit goto statement"""
        if not self.symbol_table.use_label(node.label, node.line, node.column):
            self.add_error(node.line, node.column, f"Label '{node.label}' is not defined")

    def visit_if(self, node: IfStatement):
        """Visit if statement"""
        node.condition.accept(self)
        if not self.symbol_table.use_label(node.label, node.line, node.column):
            self.add_error(node.line, node.column, f"Label '{node.label}' is not defined")

    def visit_return(self, node: ReturnStatement):
        """Visit return statement"""
        pass

    def visit_label(self, node: LabelStatement):
        """Visit label definition"""
        pass  # Handled in pre-pass

    def visit_out(self, node: OutStatement):
        """Visit out statement"""
        node.expression.accept(self)

    def visit_subprog(self, node: SubprogStatement):
        """Visit subprog statement"""
        if not self.symbol_table.use_subroutine(node.name, node.line, node.column):
            self.add_error(node.line, node.column, f"Subroutine '{node.name}' is not defined")

    def visit_substart(self, node: SubstartStatement):
        """Visit substart statement"""
        # Declaration handled in pre-pass

        for statement in node.statements:
            statement.accept(self)

    def visit_subend(self, node: SubendStatement):
        """Visit subend statement"""
        pass

    def visit_delete(self, node: DeleteStatement):
        """Visit delete statement"""
        symbol = self.symbol_table.get_symbol(node.string_var)
        if not symbol:
            self.add_error(node.line, node.column, f"Variable '{node.string_var}' is not declared")

        node.start.accept(self)
        node.length.accept(self)

    def visit_expression_statement(self, node: ExpressionStatement):
        """Visit expression statement"""
        node.expression.accept(self)

    def visit_number(self, node: NumberLiteral):
        """Visit number literal"""
        pass

    def visit_string(self, node: StringLiteral):
        """Visit string literal"""
        pass

    def visit_charcode(self, node: CharCodeLiteral):
        """Visit character code literal"""
        pass

    def visit_variable(self, node: VariableExpression):
        """Visit variable expression"""
        if not self.symbol_table.use_symbol(node.name, node.line, node.column):
            self.add_error(node.line, node.column, f"Variable '{node.name}' is not declared")

    def visit_binary_op(self, node: BinaryOperation):
        """Visit binary operation"""
        node.left.accept(self)
        node.right.accept(self)

    def visit_function_call(self, node: FunctionCall):
        """Visit function call"""
        for arg in node.arguments:
            arg.accept(self)

    def get_expression_type(self, expr: Expression) -> SymbolType:
        """
        Get the type of an expression (simplified type inference).
        A full implementation would be more sophisticated.
        """
        if isinstance(expr, NumberLiteral):
            return SymbolType.INTEGER
        elif isinstance(expr, StringLiteral):
            return SymbolType.STRING
        elif isinstance(expr, CharCodeLiteral):
            return SymbolType.INTEGER
        elif isinstance(expr, VariableExpression):
            symbol = self.symbol_table.get_symbol(expr.name)
            return symbol.symbol_type if symbol else SymbolType.UNKNOWN
        elif isinstance(expr, BinaryOperation):
            # Simplified: assume integer for arithmetic, boolean for comparisons
            if expr.operator in ('+', '-', '*', '/', '%'):
                return SymbolType.INTEGER
            else:
                return SymbolType.INTEGER  # Treat booleans as integers for now
        elif isinstance(expr, FunctionCall):
            # Type depends on function
            if expr.name in ('sizeof', 'qcount', 'pos'):
                return SymbolType.INTEGER
            elif expr.name in ('copy', 'locguide', 'currentsystemname'):
                return SymbolType.STRING
            elif expr.name in ('dequeue', 'peek'):
                return SymbolType.UNKNOWN  # Depends on queue content type

        return SymbolType.UNKNOWN
