"""Reproduction script for uninitialized variable warning"""

from osi_lsp.analysis.symbol_table import SymbolTable, SymbolType
from osi_lsp.analysis.validator import Validator
from osi_lsp.parser.parser import Parser
from osi_lsp.parser.lexer import Lexer
from osi_lsp.analysis.semantic_analyzer import SemanticAnalyzer

def parse(text):
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast, _ = parser.parse()
    return ast

def test_repro():
    # Setup parent table (INIT.osi)
    init_table = SymbolTable()
    init_table.declare_symbol("global_var", SymbolType.INTEGER, 1, 0)
    
    # Handler code using global_var
    code = """
    HANDLER:
        out $global_var
        return
    """
    ast = parse(code)
    
    # Local table
    handler_table = SymbolTable(parent=init_table)
    
    # Validate
    validator = Validator(handler_table)
    diagnostics = validator.validate(ast, "file:///HANDLER.osi", valid_init=True)
    
    print("Diagnostics:")
    for d in diagnostics:
        print(f"- {d.message} ({d.severity})")

if __name__ == "__main__":
    test_repro()
