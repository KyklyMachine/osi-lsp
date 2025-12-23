import pytest
from osi_lsp.analysis.symbol_table import SymbolTable, SymbolType, Symbol

def test_declare_symbol():
    st = SymbolTable()
    success = st.declare_symbol("counter", SymbolType.INTEGER, 1, 1)
    assert success
    assert "counter" in st.symbols
    assert st.symbols["counter"].symbol_type == SymbolType.INTEGER

def test_redeclare_symbol():
    st = SymbolTable()
    st.declare_symbol("counter", SymbolType.INTEGER, 1, 1)
    success = st.declare_symbol("counter", SymbolType.INTEGER, 2, 1)
    assert not success

def test_parent_scope():
    parent = SymbolTable()
    parent.declare_symbol("global", SymbolType.INTEGER, 1, 1)
    
    child = SymbolTable(parent=parent)
    child.declare_symbol("local", SymbolType.INTEGER, 2, 1)
    
    # Get local
    assert child.get_symbol("local") is not None
    # Get global via child
    assert child.get_symbol("global") is not None
    # Parent doesn't have local
    assert parent.get_symbol("local") is None

def test_shadowing():
    parent = SymbolTable()
    parent.declare_symbol("x", SymbolType.INTEGER, 1, 1)
    
    child = SymbolTable(parent=parent)
    child.declare_symbol("x", SymbolType.STRING, 2, 1)
    
    sym = child.get_symbol("x")
    assert sym.symbol_type == SymbolType.STRING # Local one
    
    all_syms = child.get_all_symbols()
    # Should contain the local one
    names = [s.name for s in all_syms]
    assert "x" in names
    # And check type
    for s in all_syms:
        if s.name == "x":
            assert s.symbol_type == SymbolType.STRING
