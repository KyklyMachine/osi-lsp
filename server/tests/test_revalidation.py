import pytest
import os
from unittest.mock import MagicMock, ANY
from lsprotocol.types import DidChangeTextDocumentParams, VersionedTextDocumentIdentifier
from osi_lsp.server import OSILanguageServer

def test_did_change_init_triggers_revalidation():
    """
    Test that changing INIT.osi triggers validation for other open documents
    in the same directory.
    """
    # 1. Setup Server and Workspace
    server = OSILanguageServer()
    
    # Mock workspace completely
    server.lsp = MagicMock()
    server.lsp.workspace = MagicMock()
    
    server.validate_document = MagicMock()
    server.project = MagicMock()
    
    # Mock workspace documents
    # Directory: /project/
    # Files: INIT.osi, fileA.osi, other/fileB.osi
    init_uri = "file:///project/INIT.osi"
    file_a_uri = "file:///project/fileA.osi"
    file_b_uri = "file:///project/other/fileB.osi" # Different directory
    
    # Use MagicMock for documents to avoid file I/O
    doc_init = MagicMock()
    doc_init.uri = init_uri
    doc_init.source = "source_init"
    # Ensure path property exists for logic that might use it
    doc_init.path = "/project/INIT.osi"
    
    doc_a = MagicMock()
    doc_a.uri = file_a_uri
    doc_a.source = "source_a"
    doc_a.path = "/project/fileA.osi"
    
    doc_b = MagicMock()
    doc_b.uri = file_b_uri
    doc_b.source = "source_b"
    doc_b.path = "/project/other/fileB.osi"
    
    # Setup get_document to return correct doc
    documents_map = {
        init_uri: doc_init,
        file_a_uri: doc_a,
        file_b_uri: doc_b
    }
    
    def get_document_side_effect(uri):
        return documents_map.get(uri)
        
    server.lsp.workspace.get_document.side_effect = get_document_side_effect
    server.lsp.workspace.get_text_document.side_effect = get_document_side_effect
    
    # Mock documents property for iteration
    server.lsp.workspace.documents = documents_map
    
    # Patch the property on server instance if it accesses self.workspace via self.lsp
    # server.workspace is a property that delegates to self.lsp.workspace
    # We mocked self.lsp, so server.workspace should return our mock.
    
    # 2. Trigger did_change for INIT.osi
    params = DidChangeTextDocumentParams(
        text_document=VersionedTextDocumentIdentifier(uri=init_uri, version=2),
        content_changes=[]
    )
    
    # Actually, let's just use the `did_change` function imported from osi_lsp.server
    from osi_lsp.server import did_change
    import asyncio
    
    # Create a dummy loop for async execution if needed, or just run it.
    # did_change is async.
    
    async def run_test():
        await did_change(server, params)
        
        # 3. Assertions
        
        # INIT.osi should be validated (standard behavior)
        server.validate_document.assert_any_call(init_uri, doc_init)
        
        # fileA.osi SHOULD be validated (it's in the same directory)
        # This assertion is expected to FAIL before the fix
        try:
            server.validate_document.assert_any_call(file_a_uri, doc_a)
        except AssertionError:
            print("Expected failure: fileA.osi was not re-validated")
            # raise # Commented out to allow test to pass if we are just verifying setup, but we want it to fail until fixed.
            raise
            
        # fileB.osi should NOT be validated (different directory)
        with pytest.raises(AssertionError):
             server.validate_document.assert_any_call(file_b_uri, doc_b)

    asyncio.run(run_test())

if __name__ == "__main__":
    test_did_change_init_triggers_revalidation()
