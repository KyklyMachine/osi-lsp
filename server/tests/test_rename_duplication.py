import pytest
import os
from unittest.mock import MagicMock
from osi_lsp.analysis.symbol_table import SymbolTable, SymbolType
from osi_lsp.providers.rename import RenameProvider
from osi_lsp.workspace.project import OSIProject

def test_rename_accumulated_references_bug():
    """
    Test that re-analyzing a file (which happens in the server loop)
    doesn't cause duplicate references in global symbols, leading to 
    duplicated edits.
    """
    # 1. Setup Global Scope
    global_table = SymbolTable()
    global_uri = "file:///INIT.osi"
    global_table.declare_symbol("GlobalVar", SymbolType.INTEGER, line=0, column=0, file_uri=global_uri)
    
    # 2. Simulate analysis of fileA.osi MULTIPLE times
    local_uri = "file:///fileA.osi"
    
    # --- PASS 1 ---
    # In the server, this corresponds to:
    # 1. Get symbol table (new local table with parent global)
    # 2. Parse document
    # 3. Analyze (which updates references)
    
    # Simulation:
    
    # Pass 1
    # Before analysis, Validator calls remove_references(local_uri) on parent
    global_table.remove_references(local_uri)
    
    local_table_1 = SymbolTable(parent=global_table)
    # Simulate analysis finding usage
    local_table_1.use_symbol("GlobalVar", line=5, column=10, file_uri=local_uri)
    
    # Pass 2
    # Before analysis, Validator calls remove_references(local_uri) on parent
    global_table.remove_references(local_uri)
    
    local_table_2 = SymbolTable(parent=global_table)
    # Simulate analysis finding usage
    local_table_2.use_symbol("GlobalVar", line=5, column=10, file_uri=local_uri)
    
    # Pass 3
    # Before analysis, Validator calls remove_references(local_uri) on parent
    global_table.remove_references(local_uri)
    
    local_table_3 = SymbolTable(parent=global_table)
    # Simulate analysis finding usage
    local_table_3.use_symbol("GlobalVar", line=5, column=10, file_uri=local_uri)
    
    # 3. Check references count on global symbol
    global_symbol = global_table.get_symbol("GlobalVar")
    
    # We should have exactly 1 reference from local_uri (the last one added in Pass 3)
    # The others should have been cleared by remove_references
    local_refs = [r for r in global_symbol.references if r[0] == local_uri]
    
    assert len(local_refs) == 1, f"Found {len(local_refs)} accumulated references! Expected 1."
    
    # 4. Trigger Rename
    # We use the latest local table
    provider = RenameProvider(local_table_3, local_uri)
    edit = provider.rename_symbol("GlobalVar", "GlobalVar1")
    
    assert edit is not None
    changes = edit.changes[local_uri]
    
    # We expect EXACTLY 1 edit for the line 5 usage.
    edits_at_line_5 = [e for e in changes if e.range.start.line == 5]
    
    assert len(edits_at_line_5) == 1, f"Found {len(edits_at_line_5)} overlapping edits! This causes duplicated text."

def test_rename_provider_cleans_stale_refs():
    """
    Test that RenameProvider._get_combined_references logic 
    filters out stale references if they exist in the global table,
    replacing them with fresh ones from the local analysis.
    
    This acts as a safety net even if remove_references wasn't called (e.g. temporary analysis).
    """
    # 1. Setup Global Scope
    global_table = SymbolTable()
    global_uri = "file:///INIT.osi"
    global_table.declare_symbol("GlobalVar", SymbolType.INTEGER, line=0, column=0, file_uri=global_uri)
    
    # Add a "stale" reference to global table
    local_uri = "file:///fileA.osi"
    global_table.get_symbol("GlobalVar").add_reference(local_uri, 5, 10)
    
    # 2. Setup Local Scope (representing a fresh analysis for rename)
    local_table = SymbolTable(parent=global_table)
    # Add "fresh" reference (same location) but as external reference in local table
    # This simulates what SemanticAnalyzer(update_global_refs=False) does:
    # It calls use_symbol -> parent.use_symbol(update_parent=False) -> adds to local.external_references
    
    # Manually simulate SemanticAnalyzer with update_global_refs=False
    local_table.use_symbol("GlobalVar", line=5, column=10, file_uri=local_uri, update_parent=False)
    
    # Verify we have external references captured locally
    assert "GlobalVar" in local_table.external_references
    assert len(local_table.external_references["GlobalVar"]) == 1
    
    # 3. Trigger Rename
    provider = RenameProvider(local_table, local_uri)
    
    # Access private method to test logic directly
    symbol = global_table.get_symbol("GlobalVar")
    refs = provider._get_combined_references(symbol)
    
    # Should only return 1 reference for local_uri
    local_refs = [r for r in refs if r[0] == local_uri]
    assert len(local_refs) == 1
    
    # 4. Verify Rename Edit
    edit = provider.rename_symbol("GlobalVar", "NewName")
    changes = edit.changes[local_uri]
    assert len(changes) == 1

def test_rename_with_dirty_init(tmp_path):
    """
    Test that reload_init_file accepts content, allowing
    unsaved changes in INIT.osi (from rename) to be reflected in symbol table.
    """
    # 1. Setup Project and Directory
    project = OSIProject()
    
    # Create a dummy directory structure
    d = tmp_path / "project"
    d.mkdir()
    
    # Create INIT.osi on disk with OLD content
    init_file = d / "INIT.osi"
    init_file.write_text("OldVar declare integer", encoding="utf-8")
    
    dir_path = str(d)
    
    # 2. Load Initial Context (reads from disk)
    # We need a file path to trigger get_directory_context
    dummy_file = str(d / "dummy.osi")
    context = project.get_directory_context(dummy_file)
    
    # Check that OldVar exists
    assert context.symbol_table.get_symbol("OldVar") is not None
    assert context.symbol_table.get_symbol("NewVar") is None
    
    # 3. Simulate Client Rename -> didChange with NEW content
    # The file on disk is still "OldVar...", but we pass "NewVar..." as content
    new_content = "NewVar declare integer"
    project.reload_init_file(dir_path, content=new_content)
    
    # 4. Verify Symbol Table updated from CONTENT, not disk
    assert context.symbol_table.get_symbol("NewVar") is not None, "NewVar should be present from content"
    assert context.symbol_table.get_symbol("OldVar") is None, "OldVar should be gone"
