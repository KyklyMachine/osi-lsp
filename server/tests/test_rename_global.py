import pytest
from lsprotocol.types import Position
from osi_lsp.analysis.symbol_table import SymbolTable, SymbolType
from osi_lsp.analysis.semantic_analyzer import SemanticAnalyzer
from osi_lsp.providers.rename import RenameProvider

def test_global_rename():
    """Test renaming a global variable from a local file usage."""
    # 1. Setup Global Scope (INIT.osi)
    global_table = SymbolTable()
    global_uri = "file:///INIT.osi"
    
    # Declare GlobalVar in INIT.osi
    global_table.declare_symbol("GlobalVar", SymbolType.INTEGER, line=0, column=0, file_uri=global_uri)
    
    # 2. Setup Local Scope (fileA.osi)
    local_table = SymbolTable(parent=global_table)
    local_uri = "file:///fileA.osi"
    
    # Simulate usage in fileA.osi
    local_table.use_symbol("GlobalVar", line=5, column=10, file_uri=local_uri)
    
    # 3. Trigger Rename from fileA
    provider = RenameProvider(local_table, local_uri)
    edit = provider.rename_symbol("GlobalVar", "NewGlobalVar")
    
    assert edit is not None
    assert edit.changes is not None
    
    # 4. Verify Edits
    assert global_uri in edit.changes
    assert local_uri in edit.changes
    
    # INIT.osi: Declaration update
    init_edits = edit.changes[global_uri]
    assert len(init_edits) == 1
    assert init_edits[0].new_text == "NewGlobalVar"
    
    # fileA.osi: Reference update
    file_edits = edit.changes[local_uri]
    assert len(file_edits) == 1
    assert file_edits[0].new_text == "$NewGlobalVar"

def test_global_rename_from_init():
    """Test renaming a global variable from its declaration in INIT.osi."""
    # 1. Setup Global Scope (INIT.osi)
    global_table = SymbolTable()
    global_uri = "file:///INIT.osi"
    global_table.declare_symbol("GlobalVar", SymbolType.INTEGER, line=0, column=0, file_uri=global_uri)
    
    # 2. Setup Local Scope (fileA.osi)
    local_table = SymbolTable(parent=global_table)
    local_uri = "file:///fileA.osi"
    local_table.use_symbol("GlobalVar", line=5, column=10, file_uri=local_uri)
    
    # 3. Trigger Rename from INIT.osi
    provider = RenameProvider(global_table, global_uri)
    edit = provider.rename_symbol("GlobalVar", "NewGlobalVar")
    
    assert edit is not None
    assert global_uri in edit.changes
    assert local_uri in edit.changes

def test_global_rename_multiple_files():
    """Test renaming a global variable used in multiple files."""
    # 1. Setup Global Scope
    global_table = SymbolTable()
    global_uri = "file:///INIT.osi"
    global_table.declare_symbol("CommonVar", SymbolType.STRING, line=1, column=0, file_uri=global_uri)
    
    # 2. Setup File A
    table_a = SymbolTable(parent=global_table)
    uri_a = "file:///fileA.osi"
    table_a.use_symbol("CommonVar", line=10, column=5, file_uri=uri_a)
    
    # 3. Setup File B
    table_b = SymbolTable(parent=global_table)
    uri_b = "file:///fileB.osi"
    table_b.use_symbol("CommonVar", line=20, column=8, file_uri=uri_b)
    table_b.use_symbol("CommonVar", line=25, column=8, file_uri=uri_b) # Second usage in B
    
    # 4. Trigger Rename from File B
    provider = RenameProvider(table_b, uri_b)
    edit = provider.rename_symbol("CommonVar", "NewCommonVar")
    
    assert edit is not None
    changes = edit.changes
    
    assert len(changes) == 3 # INIT, A, B
    
    # Verify INIT
    assert global_uri in changes
    assert changes[global_uri][0].new_text == "NewCommonVar"
    
    # Verify A
    assert uri_a in changes
    assert len(changes[uri_a]) == 1
    assert changes[uri_a][0].new_text == "$NewCommonVar"
    
    # Verify B (2 usages)
    assert uri_b in changes
    assert len(changes[uri_b]) == 2
    assert all(c.new_text == "$NewCommonVar" for c in changes[uri_b])

def test_shadowing_rename_local():
    """Test renaming a local variable that shadows a global one."""
    # 1. Setup Global Scope
    global_table = SymbolTable()
    global_uri = "file:///INIT.osi"
    global_table.declare_symbol("Shadowed", SymbolType.INTEGER, line=0, column=0, file_uri=global_uri)
    
    # 2. Setup Local Scope with Shadowing Declaration
    local_table = SymbolTable(parent=global_table)
    local_uri = "file:///local.osi"
    
    # Declare local symbol with same name
    local_table.declare_symbol("Shadowed", SymbolType.STRING, line=5, column=0, file_uri=local_uri)
    local_table.use_symbol("Shadowed", line=10, column=5, file_uri=local_uri)
    
    # 3. Trigger Rename on Local Symbol
    provider = RenameProvider(local_table, local_uri)
    edit = provider.rename_symbol("Shadowed", "NewLocal")
    
    assert edit is not None
    changes = edit.changes
    
    # Should only affect local file
    assert local_uri in changes
    assert global_uri not in changes
    
    # Should affect declaration + usage in local file
    assert len(changes[local_uri]) == 2
    
    # Verify global symbol is untouched in symbol table logic (implicit by edit not containing global_uri)

def test_shadowing_rename_global():
    """Test renaming a global variable when a local variable shadows it."""
    # 1. Setup Global Scope
    global_table = SymbolTable()
    global_uri = "file:///INIT.osi"
    global_table.declare_symbol("Shadowed", SymbolType.INTEGER, line=0, column=0, file_uri=global_uri)
    
    # 2. Setup Local Scope with Shadowing
    local_table = SymbolTable(parent=global_table)
    local_uri = "file:///local.osi"
    
    # Declare local variable shadowing 'Shadowed'
    local_table.declare_symbol("Shadowed", SymbolType.STRING, line=5, column=0, file_uri=local_uri)
    
    # 3. Setup Another File using Global
    other_table = SymbolTable(parent=global_table)
    other_uri = "file:///other.osi"
    other_table.use_symbol("Shadowed", line=2, column=2, file_uri=other_uri)
    
    # 4. Trigger Rename on Global Symbol from Global context (or non-shadowed context)
    provider = RenameProvider(global_table, global_uri)
    edit = provider.rename_symbol("Shadowed", "NewGlobal")
    
    assert edit is not None
    changes = edit.changes
    
    # Should affect INIT.osi and other.osi
    assert global_uri in changes
    assert other_uri in changes
    
    # Should NOT affect local.osi because it uses its own local 'Shadowed'
    assert local_uri not in changes

def test_global_label_rename():
    """Test renaming a global label."""
    # 1. Setup Global Scope
    global_table = SymbolTable()
    global_uri = "file:///INIT.osi"
    global_table.declare_label("GLOBAL_START", line=10, column=0, file_uri=global_uri)
    
    # 2. Setup Usage in Local File
    local_table = SymbolTable(parent=global_table)
    local_uri = "file:///main.osi"
    local_table.use_label("GLOBAL_START", line=5, column=5, file_uri=local_uri)
    
    # 3. Rename
    provider = RenameProvider(local_table, local_uri)
    edit = provider.rename_symbol("GLOBAL_START", "GLOBAL_END")
    
    assert edit is not None
    changes = edit.changes
    
    assert global_uri in changes
    assert local_uri in changes
    
    assert changes[global_uri][0].new_text == "GLOBAL_END"
    assert changes[local_uri][0].new_text == "GLOBAL_END"

def test_global_subroutine_rename():
    """Test renaming a global subroutine."""
    # 1. Setup Global Scope
    global_table = SymbolTable()
    global_uri = "file:///INIT.osi"
    global_table.declare_subroutine("GlobalSub", line=20, column=0, file_uri=global_uri)
    
    # 2. Setup Usage
    local_table = SymbolTable(parent=global_table)
    local_uri = "file:///main.osi"
    local_table.use_subroutine("GlobalSub", line=15, column=5, file_uri=local_uri)
    
    # 3. Rename
    provider = RenameProvider(local_table, local_uri)
    edit = provider.rename_symbol("GlobalSub", "NewGlobalSub")
    
    assert edit is not None
    changes = edit.changes
    
    assert global_uri in changes
    assert local_uri in changes
    
    assert changes[global_uri][0].new_text == "NewGlobalSub"
    assert changes[local_uri][0].new_text == "NewGlobalSub"

def test_global_rename_with_dollars():
    """Test renaming global variable when input includes $."""
    # 1. Setup Global
    global_table = SymbolTable()
    global_uri = "file:///INIT.osi"
    global_table.declare_symbol("MyVar", SymbolType.INTEGER, line=0, column=0, file_uri=global_uri)
    
    # 2. Setup Usage
    local_table = SymbolTable(parent=global_table)
    local_uri = "file:///test.osi"
    local_table.use_symbol("MyVar", line=1, column=1, file_uri=local_uri)
    
    # 3. Rename "$MyVar" -> "$NewVar"
    provider = RenameProvider(local_table, local_uri)
    edit = provider.rename_symbol("$MyVar", "$NewVar")
    
    changes = edit.changes
    # Decl in INIT (should not have $)
    assert changes[global_uri][0].new_text == "NewVar"
    # Usage in test (should have $)
    assert changes[local_uri][0].new_text == "$NewVar"
