import pytest
from osi_lsp.analysis.symbol_table import SymbolTable, SymbolType

def test_use_symbol_in_parent_scope():
    parent = SymbolTable()
    parent.declare_symbol("global_var", SymbolType.INTEGER, 1, 1)
    
    child = SymbolTable(parent=parent)
    
    # This should return True if scope-aware, currently False
    assert child.use_symbol("global_var", 10, 10) == True

def test_initialize_symbol_in_parent_scope():
    parent = SymbolTable()
    parent.declare_symbol("global_var", SymbolType.INTEGER, 1, 1)
    
    child = SymbolTable(parent=parent)
    
    # This just modifies state, no return value
    child.initialize_symbol("global_var")
    
    # Verify it was marked initialized in parent
    assert parent.get_symbol("global_var").initialized == True
