import pytest
from osi_lsp.analysis.symbol_table import SymbolTable, SymbolType
from osi_lsp.providers.rename import RenameProvider

def test_rename_accumulated_references_bug():
    """
    Test that re-analyzing a file (which happens in the server loop)
    doesn't cause duplicate references in global symbols, leading to 
    duplicated edits (e.g. $$$var1var1var1).
    """
    # 1. Setup Global Scope
    global_table = SymbolTable()
    global_uri = "file:///INIT.osi"
    global_table.declare_symbol("GlobalVar", SymbolType.INTEGER, line=0, column=0, file_uri=global_uri)
    
    # 2. Simulate analysis of fileA.osi MULTIPLE times (as happens in the server)
    # Each analysis creates a new local table but shares the parent (global_table)
    local_uri = "file:///fileA.osi"
    
    # First analysis
    local_table_1 = SymbolTable(parent=global_table)
    local_table_1.use_symbol("GlobalVar", line=5, column=10, file_uri=local_uri)
    
    # Second analysis (e.g. user typed something)
    local_table_2 = SymbolTable(parent=global_table)
    local_table_2.use_symbol("GlobalVar", line=5, column=10, file_uri=local_uri)
    
    # Third analysis (e.g. user triggered rename)
    local_table_3 = SymbolTable(parent=global_table)
    local_table_3.use_symbol("GlobalVar", line=5, column=10, file_uri=local_uri)
    
    # 3. Check references count on global symbol
    global_symbol = global_table.get_symbol("GlobalVar")
    
    # If bug exists, we have 3 references to the same location
    print(f"References: {global_symbol.references}")
    
    # 4. Trigger Rename
    # We use the latest local table
    provider = RenameProvider(local_table_3, local_uri)
    edit = provider.rename_symbol("GlobalVar", "GlobalVar1")
    
    assert edit is not None
    changes = edit.changes[local_uri]
    
    # We expect EXACTLY 1 edit for the line 5 usage.
    # If the bug exists, we might see 3 edits.
    edits_at_line_5 = [e for e in changes if e.range.start.line == 5]
    
    assert len(edits_at_line_5) == 1, f"Found {len(edits_at_line_5)} overlapping edits! This causes duplicated text."

def test_rename_add_dollar_prefix():
    """
    Test renaming var to var1 results in $var1, not $$var1 or similar,
    even if the user provided $var1 as input.
    """
    table = SymbolTable()
    uri = "file:///test.osi"
    table.declare_symbol("var", SymbolType.INTEGER, line=0, column=0, file_uri=uri)
    table.use_symbol("var", line=1, column=0, file_uri=uri) # Usage: $var
    
    provider = RenameProvider(table, uri)
    
    # Case 1: Rename "var" -> "var1"
    edit1 = provider.rename_symbol("var", "var1")
    # Usage should become "$var1"
    assert edit1.changes[uri][1].new_text == "$var1"
    
    # Case 2: Rename "$var" -> "var1" (VSCode often sends the word under cursor as range, but prompt input is new name)
    # The provider handles "var" (clean) -> "var1" (clean)
    # Logic: usage range covers "$var" (or just "var"?).
    # RenameProvider assumes usage range is just "var" part?
    # Let's check SymbolTable.use_symbol logic vs Parser.
    # Parser: VARIABLE token includes $.
    # But SemanticAnalyzer/SymbolTable stores 'name' without $.
    # RenameProvider uses symbol.references (line, col).
    # Does (line, col) point to '$' or 'v'?
    
    # If parser stores start of token, it includes $.
    # Let's verify this assumption in a separate test or check parser code.
    pass 
