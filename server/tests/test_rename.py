import pytest
from lsprotocol.types import Position
from osi_lsp.parser.lexer import Lexer
from osi_lsp.parser.parser import Parser
from osi_lsp.analysis.symbol_table import SymbolTable, SymbolType
from osi_lsp.analysis.semantic_analyzer import SemanticAnalyzer
from osi_lsp.providers.rename import RenameProvider

def parse_and_analyze(code):
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast, errors = parser.parse()
    # Ensure no parse errors for valid tests
    if errors:
        print(f"Parse errors: {errors}")
    
    symbol_table = SymbolTable()
    analyzer = SemanticAnalyzer(symbol_table, "file:///test.osi")
    analyzer.analyze(ast)
    
    return symbol_table

def test_rename_variable():
    # Correct syntax: 10 varset var1 (or $var1)
    # Using 'var1' without $ as variable name is allowed by parser if it's identifier?
    # Parser: expect VARIABLE or IDENTIFIER.
    # Semantic check: varset expects declared variable.
    code = """
    var1 declare integer
    out $var1
    10 varset var1
    """
    symbol_table = parse_and_analyze(code)
    provider = RenameProvider(symbol_table, "file:///test.osi")
    
    # Rename 'var1' to 'new_var'
    edit = provider.rename_symbol("var1", "new_var")
    
    assert edit is not None
    assert len(edit.changes) == 1
    changes = edit.changes["file:///test.osi"]
    assert len(changes) == 3 # Declare + 2 references
    
    # 1. Declaration: "var1 declare" -> "new_var"
    # Find change at line 1
    decl_edit = [c for c in changes if c.range.start.line == 1 and c.new_text == "new_var"]
    assert len(decl_edit) == 1
    
    # 2. Reference 1: "out $var1" -> "$new_var"
    # Line 2. Range 8-13.
    ref1 = [c for c in changes if c.range.start.line == 2 and c.new_text == "$new_var"]
    assert len(ref1) == 1
    
    # 3. Reference 2: "10 varset var1" -> "$new_var" or "new_var"?
    # Line 3. "10 varset var1".
    # var1 is IDENTIFIER. No $.
    # RenameProvider adds $ by default in _create_edit_variable loop for references.
    # This is problematic if usage didn't have $.
    # But wait, parser allows Identifier for varset.
    # Should rename force $?
    # Spec says variables usually have $.
    # If I rename `var1` to `new`, result `$new`.
    # `10 varset $new`. Correct syntax.
    # But we must ensure we don't break the range.
    # If source was `var1` (len 4). Range covers 4 chars.
    # We replace with `$new_var`.
    # It inserts `$`.
    # This is fine.
    
    ref2 = [c for c in changes if c.range.start.line == 3 and c.new_text == "$new_var"]
    assert len(ref2) == 1

def test_rename_label():
    code = """
    START:
    goto START
    """
    symbol_table = parse_and_analyze(code)
    provider = RenameProvider(symbol_table, "file:///test.osi")
    
    edit = provider.rename_symbol("START", "END")
    
    assert edit is not None
    changes = edit.changes["file:///test.osi"]
    assert len(changes) == 2 # Def + Ref
    
    # Both use "END"
    assert all(c.new_text == "END" for c in changes)

def test_rename_subroutine():
    code = """
    substart mysub
    subend
    subprog mysub
    """
    symbol_table = parse_and_analyze(code)
    provider = RenameProvider(symbol_table, "file:///test.osi")
    
    edit = provider.rename_symbol("mysub", "newsub")
    
    assert edit is not None
    changes = edit.changes["file:///test.osi"]
    assert len(changes) == 2

def test_rename_not_found():
    code = "out 1"
    symbol_table = parse_and_analyze(code)
    provider = RenameProvider(symbol_table, "file:///test.osi")
    
    edit = provider.rename_symbol("unknown", "new")
    assert edit is None

def test_rename_with_dollar_input():
    code = """
    var1 declare integer
    """
    symbol_table = parse_and_analyze(code)
    provider = RenameProvider(symbol_table, "file:///test.osi")
    
    # User selects "$var1" (word) and types "$new"
    edit = provider.rename_symbol("$var1", "$new")
    
    assert edit is not None
    changes = edit.changes["file:///test.osi"]
    # Declaration should be "new" (stripped $)
    decl = changes[0]
    assert decl.new_text == "new"

def test_rename_with_dollar_input_target_no_dollar():
    code = """
    var1 declare integer
    """
    symbol_table = parse_and_analyze(code)
    provider = RenameProvider(symbol_table, "file:///test.osi")
    
    # User selects "$var1" and types "new"
    edit = provider.rename_symbol("$var1", "new")
    
    assert edit is not None
    changes = edit.changes["file:///test.osi"]
    decl = changes[0]
    assert decl.new_text == "new"

