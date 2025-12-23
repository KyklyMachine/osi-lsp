import pytest
from osi_lsp.parser.lexer import Lexer
from osi_lsp.parser.parser import Parser
from osi_lsp.analysis.symbol_table import SymbolTable
from osi_lsp.analysis.validator import Validator
from lsprotocol.types import DiagnosticSeverity

def validate(code, filename="test.osi", is_init=False):
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    st = SymbolTable()
    validator = Validator(st)
    # Mocking URI
    uri = f"file:///{filename}"
    return validator.validate(ast, uri, valid_init=True)

def test_validate_undeclared_variable():
    code = """
    HANDLER:
        $x varset y
        return
    """
    diagnostics = validate(code, "HANDLER.osi")
    # Should have error for undeclared 'x' (used in expr) and 'y' (assigned to)
    errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
    assert len(errors) > 0
    assert any("not declared" in d.message for d in errors)

def test_validate_init_restriction():
    code = """
    HANDLER:
        return
    """
    # Filename is INIT.osi, but contains executable code
    diagnostics = validate(code, "INIT.osi")
    errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
    assert len(errors) > 0
    assert any("cannot contain executable code" in d.message for d in errors)

def test_validate_handler_restriction():
    code = """
    counter declare integer
    HANDLER:
        return
    """
    # Filename is HANDLER.osi, but contains declare
    diagnostics = validate(code, "HANDLER.osi")
    errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
    assert len(errors) > 0
    assert any("only allowed in INIT.osi" in d.message for d in errors)

def test_validate_handler_name_mismatch():
    code = """
    OTHER:
        return
    """
    # Filename HANDLER.osi, label OTHER
    diagnostics = validate(code, "HANDLER.osi")
    errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
    # We check for structural error
    # Our validator might catch this?
    # Spec says: "Handler name 'HANDLER2' does not match filename"
    # My implementation checks if ANY label matches filename.
    # Here OTHER != HANDLER, so it should error.
    assert len(errors) > 0
    assert any("must match filename" in d.message for d in errors)
