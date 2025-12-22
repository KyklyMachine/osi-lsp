"""AST Node definitions for Protocol Language"""

from dataclasses import dataclass
from typing import List, Optional, Any, Dict
from abc import ABC, abstractmethod


class ASTNode(ABC):
    """Base class for all AST nodes"""

    @abstractmethod
    def accept(self, visitor):
        """Accept a visitor for the visitor pattern"""
        pass


@dataclass
class Program(ASTNode):
    """Root of the program - contains all handlers"""
    handlers: List['Handler']

    def accept(self, visitor):
        return visitor.visit_program(self)


@dataclass
class Handler(ASTNode):
    """Event handler block (## NAME)"""
    name: str
    line: int
    column: int
    statements: List['Statement']

    def accept(self, visitor):
        return visitor.visit_handler(self)


# === Statements ===

class Statement(ASTNode):
    """Base class for all statements"""
    line: int
    column: int


@dataclass
class DeclareStatement(Statement):
    """Variable declaration: name declare type"""
    name: str
    var_type: str  # 'integer', 'buffer', 'string', 'queue'
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_declare(self)


@dataclass
class VarsetStatement(Statement):
    """Assignment: expression varset variable"""
    expression: 'Expression'
    variable: str
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_varset(self)


@dataclass
class BufferitStatement(Statement):
    """Create buffer: buffer bufferit length field1 len1 ..."""
    buffer_name: str
    total_length: 'Expression'
    fields: List[tuple['Expression', 'Expression']]  # (value, length) pairs
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_bufferit(self)


@dataclass
class UnbufferitStatement(Statement):
    """Parse buffer: unbufferit buffer var1 len1 ..."""
    buffer_name: str
    fields: List[tuple[str, 'Expression']]  # (variable, length) pairs
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_unbufferit(self)


@dataclass
class CalccrcStatement(Statement):
    """Calculate CRC: calccrc result buffer"""
    result_var: str
    buffer_expr: 'Expression'
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_calccrc(self)


@dataclass
class TimerStatement(Statement):
    """Set timer: event timer timer_var delay params..."""
    event_name: str
    timer_var: str
    delay: 'Expression'
    parameters: Dict[str, Any]
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_timer(self)


@dataclass
class UntimerStatement(Statement):
    """Cancel timer: untimer timer_id"""
    timer_id: 'Expression'
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_untimer(self)


@dataclass
class QueueStatement(Statement):
    """Add to queue: queue queue_name value"""
    queue_name: str
    value: 'Expression'
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_queue(self)


@dataclass
class ClearqueueStatement(Statement):
    """Clear queue: clearqueue queue_name"""
    queue_name: str
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_clearqueue(self)


@dataclass
class GenerateupStatement(Statement):
    """Generate event up: EVENT.NAME generateup params..."""
    event_name: str
    parameters: Dict[str, Any]
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_generateup(self)


@dataclass
class EventdownStatement(Statement):
    """Send event down: EVENT.NAME eventdown params..."""
    event_name: str
    parameters: Dict[str, Any]
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_eventdown(self)


@dataclass
class GotoStatement(Statement):
    """Unconditional jump: goto label"""
    label: str
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_goto(self)


@dataclass
class IfStatement(Statement):
    """Conditional jump: condition if label"""
    condition: 'Expression'
    label: str
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_if(self)


@dataclass
class ReturnStatement(Statement):
    """Return from handler: return"""
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_return(self)


@dataclass
class LabelStatement(Statement):
    """Label definition: label:"""
    name: str
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_label(self)


@dataclass
class OutStatement(Statement):
    """Debug output: out expression"""
    expression: 'Expression'
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_out(self)


@dataclass
class SubprogStatement(Statement):
    """Subroutine call: subprog name"""
    name: str
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_subprog(self)


@dataclass
class SubstartStatement(Statement):
    """Subroutine definition start: substart name"""
    name: str
    line: int
    column: int
    statements: List[Statement]

    def accept(self, visitor):
        return visitor.visit_substart(self)


@dataclass
class SubendStatement(Statement):
    """Subroutine definition end: subend"""
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_subend(self)


@dataclass
class DeleteStatement(Statement):
    """Delete substring: delete string start length"""
    string_var: str
    start: 'Expression'
    length: 'Expression'
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_delete(self)


# === Expressions ===

class Expression(ASTNode):
    """Base class for all expressions"""
    pass


@dataclass
class NumberLiteral(Expression):
    """Numeric literal"""
    value: int
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_number(self)


@dataclass
class StringLiteral(Expression):
    """String literal"""
    value: str
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_string(self)


@dataclass
class CharCodeLiteral(Expression):
    """Character code literal (#255)"""
    value: int
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_charcode(self)


@dataclass
class VariableExpression(Expression):
    """Variable reference ($name)"""
    name: str
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_variable(self)


@dataclass
class BinaryOperation(Expression):
    """Binary operation: left op right"""
    left: Expression
    operator: str  # '+', '-', '*', '/', '%', '==', '!=', '>', '<', '>=', '<=', '&&', '||'
    right: Expression
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_binary_op(self)


@dataclass
class FunctionCall(Expression):
    """Function call: func(args)"""
    name: str
    arguments: List[Expression]
    line: int
    column: int

    def accept(self, visitor):
        return visitor.visit_function_call(self)


# === Visitor Interface ===

class ASTVisitor(ABC):
    """Base visitor for traversing the AST"""

    def visit_program(self, node: Program):
        pass

    def visit_handler(self, node: Handler):
        pass

    def visit_declare(self, node: DeclareStatement):
        pass

    def visit_varset(self, node: VarsetStatement):
        pass

    def visit_bufferit(self, node: BufferitStatement):
        pass

    def visit_unbufferit(self, node: UnbufferitStatement):
        pass

    def visit_calccrc(self, node: CalccrcStatement):
        pass

    def visit_timer(self, node: TimerStatement):
        pass

    def visit_untimer(self, node: UntimerStatement):
        pass

    def visit_queue(self, node: QueueStatement):
        pass

    def visit_clearqueue(self, node: ClearqueueStatement):
        pass

    def visit_generateup(self, node: GenerateupStatement):
        pass

    def visit_eventdown(self, node: EventdownStatement):
        pass

    def visit_goto(self, node: GotoStatement):
        pass

    def visit_if(self, node: IfStatement):
        pass

    def visit_return(self, node: ReturnStatement):
        pass

    def visit_label(self, node: LabelStatement):
        pass

    def visit_out(self, node: OutStatement):
        pass

    def visit_subprog(self, node: SubprogStatement):
        pass

    def visit_substart(self, node: SubstartStatement):
        pass

    def visit_subend(self, node: SubendStatement):
        pass

    def visit_delete(self, node: DeleteStatement):
        pass

    def visit_number(self, node: NumberLiteral):
        pass

    def visit_string(self, node: StringLiteral):
        pass

    def visit_charcode(self, node: CharCodeLiteral):
        pass

    def visit_variable(self, node: VariableExpression):
        pass

    def visit_binary_op(self, node: BinaryOperation):
        pass

    def visit_function_call(self, node: FunctionCall):
        pass
