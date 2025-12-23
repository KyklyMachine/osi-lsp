import pytest
import os
import tempfile
import shutil
from osi_lsp.workspace.project import OSIProject
from osi_lsp.analysis.symbol_table import SymbolType

@pytest.fixture
def temp_project():
    # Create a temp directory structure
    tmp_dir = tempfile.mkdtemp()
    
    # Structure:
    # /project
    #   /transport
    #     INIT.osi
    #     HANDLER.osi
    
    transport_dir = os.path.join(tmp_dir, "transport")
    os.makedirs(transport_dir)
    
    init_content = """
    global_var declare integer
    buffer_var declare buffer
    """
    with open(os.path.join(transport_dir, "INIT.osi"), "w") as f:
        f.write(init_content)
        
    handler_content = """
    HANDLER:
        return
    """
    with open(os.path.join(transport_dir, "HANDLER.osi"), "w") as f:
        f.write(handler_content)
        
    yield tmp_dir
    
    # Cleanup
    shutil.rmtree(tmp_dir)

def test_project_load_init(temp_project):
    project = OSIProject()
    transport_dir = os.path.join(temp_project, "transport")
    handler_path = os.path.join(transport_dir, "HANDLER.osi")
    
    # Getting context for handler should load INIT.osi
    context = project.get_directory_context(handler_path)
    
    assert context.valid_init is True
    assert context.init_file == os.path.join(transport_dir, "INIT.osi")
    
    # Check if global symbols are loaded
    sym = context.symbol_table.get_symbol("global_var")
    assert sym is not None
    assert sym.symbol_type == SymbolType.INTEGER

def test_project_scan_handlers(temp_project):
    project = OSIProject()
    transport_dir = os.path.join(temp_project, "transport")
    handler_path = os.path.join(transport_dir, "HANDLER.osi")
    
    context = project.get_directory_context(handler_path)
    
    # Check if HANDLER was registered
    handler = context.symbol_table.get_handler("HANDLER")
    assert handler is not None
    assert handler.name == "HANDLER"
    assert handler.file_uri.endswith("HANDLER.osi")

def test_project_missing_init(temp_project):
    project = OSIProject()
    # Create dir without INIT
    empty_dir = os.path.join(temp_project, "empty")
    os.makedirs(empty_dir)
    file_path = os.path.join(empty_dir, "file.osi")
    
    context = project.get_directory_context(file_path)
    
    assert context.valid_init is False
    assert context.init_file is None
