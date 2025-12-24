import pytest
from osi_lsp.parser.lexer import Lexer
from osi_lsp.parser.parser import Parser
from osi_lsp.analysis.symbol_table import SymbolTable
from osi_lsp.analysis.validator import Validator
from lsprotocol.types import DiagnosticSeverity

def validate(code, filename="test.osi", valid_init=True):
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast, _ = parser.parse()
    
    st = SymbolTable()
    validator = Validator(st)
    # Mocking URI
    uri = f"file:///path/to/project/{filename}"
    return validator.validate(ast, uri, valid_init=valid_init)

def test_validate_undeclared_variable():
    code = """
    HANDLER:
        $x varset y
        return
    """
    diagnostics = validate(code, "HANDLER.osi")
    errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
    assert len(errors) >= 2 # x and y
    assert any("'x' is not declared" in d.message for d in errors)
    assert any("'y' is not declared" in d.message for d in errors)

def test_validate_init_restriction():
    code = """
    HANDLER:
        return
    """
    diagnostics = validate(code, "INIT.osi")
    errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
    assert any("cannot contain executable code" in d.message for d in errors)

def test_validate_handler_restriction():
    code = """
    counter declare integer
    HANDLER:
        return
    """
    diagnostics = validate(code, "HANDLER.osi")
    errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
    assert any("only allowed in INIT.osi" in d.message for d in errors)

def test_validate_handler_name_mismatch():
    code = """
    OTHER:
        return
    """
    diagnostics = validate(code, "HANDLER.osi")
    errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
    assert any("must match filename" in d.message for d in errors)

def test_validate_missing_return():
    code = """
    HANDLER:
        0 varset $x
    """
    # Assuming x is declared in INIT, but for this test we just care about missing return
    diagnostics = validate(code, "HANDLER.osi")
    warnings = [d for d in diagnostics if d.severity == DiagnosticSeverity.Warning]
    assert any("should end with 'return' statement" in d.message for d in warnings)

def test_validate_unused_variable():
    code = """
    HANDLER:
        x declare integer
        return
    """
    # We need to simulate that x is in handler, which is technically invalid per rules but Validator allows it to report error.
    # Actually, if we use HANDLER.osi, declare will be an error.
    # Let's use a dummy filename that is NOT INIT.osi but we want to check unused.
    diagnostics = validate(code, "DUMMY.osi")
    warnings = [d for d in diagnostics if d.severity == DiagnosticSeverity.Warning]
    assert any("is declared but never used" in d.message for d in warnings)

def test_validate_unused_label():
    code = """
    HANDLER:
    UNUSED_LABEL:
        return
    """
    diagnostics = validate(code, "HANDLER.osi")
    warnings = [d for d in diagnostics if d.severity == DiagnosticSeverity.Warning]
    assert any("Label 'UNUSED_LABEL' is defined but never used" in d.message for d in warnings)

def test_validate_duplicate_declaration():
    code = """
    x declare integer
    x declare string
    """
    diagnostics = validate(code, "INIT.osi")
    errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
    assert any("Variable 'x' is already declared" in d.message for d in errors)

def test_validate_goto_undefined_label():
    code = """
    HANDLER:
        goto MISSING
        return
    """
    diagnostics = validate(code, "HANDLER.osi")
    errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
    assert any("Label 'MISSING' is not defined" in d.message for d in errors)

def test_validate_type_mismatch():
    code = """
    HANDLER:
        "string" varset $counter
        return
    """
    # We need counter to be declared. Validator gets a fresh SymbolTable.
    # We can use a trick: declare it in the same file for the test, 
    # even if it's technically an error in a handler, SemanticAnalyzer will still see it.
    code_with_decl = """
    counter declare integer
    HANDLER:
        "string" varset $counter
        return
    """
def test_validate_nested_subroutine():
    code = """
    substart Outer
        substart Inner
            return
        subend
        subprog Inner
    subend
    subprog Outer
    """
    diagnostics = validate(code, "INIT.osi")
    errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
    # If Inner is not registered in pre-pass, it should be missing
    assert any("Subroutine 'Inner' is not defined" in d.message for d in errors)
