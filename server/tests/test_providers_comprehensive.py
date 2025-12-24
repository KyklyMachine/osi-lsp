"""Comprehensive tests for providers (completion, hover, definition)"""

from osi_lsp.analysis.symbol_table import SymbolTable, SymbolType
from osi_lsp.providers.completion import CompletionProvider
from osi_lsp.providers.hover import HoverProvider
from osi_lsp.providers.definition import DefinitionProvider
from lsprotocol.types import CompletionItemKind


class TestCompletionProvider:
    """Test CompletionProvider functionality"""

    def test_keywords_completion(self):
        """Test keyword completions"""
        table = SymbolTable()
        provider = CompletionProvider(table)
        result = provider.get_completions("", 0)

        # Check for basic keywords
        labels = [item.label for item in result.items]
        assert "declare" in labels
        assert "varset" in labels
        assert "goto" in labels
        assert "if" in labels
        assert "return" in labels

    def test_operators_completion(self):
        """Test operator/function completions"""
        table = SymbolTable()
        provider = CompletionProvider(table)
        result = provider.get_completions("", 0)

        labels = [item.label for item in result.items]
        assert "bufferit" in labels
        assert "unbufferit" in labels
        assert "timer" in labels
        assert "untimer" in labels
        assert "queue" in labels
        assert "generateup" in labels
        assert "eventdown" in labels

    def test_functions_completion(self):
        """Test built-in functions completion"""
        table = SymbolTable()
        provider = CompletionProvider(table)
        result = provider.get_completions("", 0)

        labels = [item.label for item in result.items]
        assert "sizeof" in labels
        assert "copy" in labels
        assert "pos" in labels
        assert "locguide" in labels
        assert "CurrentSystemName" in labels
        assert "dequeue" in labels
        assert "peek" in labels
        assert "qcount" in labels

    def test_types_after_declare(self):
        """Test type suggestions after declare keyword"""
        table = SymbolTable()
        provider = CompletionProvider(table)
        result = provider.get_completions("x declare ", 10)

        labels = [item.label for item in result.items]
        # Should suggest types
        assert "integer" in labels
        assert "buffer" in labels
        assert "string" in labels
        assert "queue" in labels

        # Should only have types when after declare
        type_items = [item for item in result.items if item.kind == CompletionItemKind.TypeParameter]
        assert len(type_items) > 0

    def test_variables_completion(self):
        """Test variable completions from symbol table"""
        table = SymbolTable()
        table.declare_symbol("counter", SymbolType.INTEGER, 1, 0)
        table.declare_symbol("buffer", SymbolType.BUFFER, 2, 0)
        table.declare_symbol("message", SymbolType.STRING, 3, 0)

        provider = CompletionProvider(table)
        result = provider.get_completions("", 0)

        labels = [item.label for item in result.items]
        assert "$counter" in labels
        assert "$buffer" in labels
        assert "$message" in labels

        # Check details
        counter_item = next(item for item in result.items if item.label == "$counter")
        assert "integer" in counter_item.detail

    def test_labels_completion(self):
        """Test label completions"""
        table = SymbolTable()
        table.declare_label("start", 1, 0)
        table.declare_label("error_handler", 2, 0)
        table.declare_label("end", 3, 0)

        provider = CompletionProvider(table)
        result = provider.get_completions("", 0)

        labels = [item.label for item in result.items]
        assert "start" in labels
        assert "error_handler" in labels
        assert "end" in labels

        # Check kind
        label_items = [item for item in result.items if item.label == "start"]
        assert label_items[0].kind == CompletionItemKind.Constant

    def test_subroutines_completion(self):
        """Test subroutine completions"""
        table = SymbolTable()
        table.declare_subroutine("MySub", 1, 0)
        table.declare_subroutine("ErrorHandler", 2, 0)

        provider = CompletionProvider(table)
        result = provider.get_completions("", 0)

        labels = [item.label for item in result.items]
        assert "MySub" in labels
        assert "ErrorHandler" in labels

        # Check kind
        sub_item = next(item for item in result.items if item.label == "MySub")
        assert sub_item.kind == CompletionItemKind.Function
        assert "Subroutine" in sub_item.detail

    def test_handlers_completion(self):
        """Test handler completions"""
        table = SymbolTable()
        table.declare_handler("INIT", "file:///init.osi")
        table.declare_handler("DATA.REQ", "file:///data_req.osi", ["param1", "param2"])

        provider = CompletionProvider(table)
        result = provider.get_completions("", 0)

        labels = [item.label for item in result.items]
        assert "INIT" in labels
        assert "DATA.REQ" in labels

        # Check kind
        handler_item = next(item for item in result.items if item.label == "DATA.REQ")
        assert handler_item.kind == CompletionItemKind.Event

    def test_completion_with_parent_scope(self):
        """Test completions include parent scope symbols"""
        parent = SymbolTable()
        parent.declare_symbol("global_var", SymbolType.INTEGER, 1, 0)
        parent.declare_handler("GLOBAL_HANDLER", "file:///global.osi")

        child = SymbolTable(parent=parent)
        child.declare_symbol("local_var", SymbolType.STRING, 2, 0)

        provider = CompletionProvider(child)
        result = provider.get_completions("", 0)

        labels = [item.label for item in result.items]
        assert "$global_var" in labels
        assert "$local_var" in labels
        assert "GLOBAL_HANDLER" in labels

    def test_completion_empty_table(self):
        """Test completions with empty symbol table"""
        table = SymbolTable()
        provider = CompletionProvider(table)
        result = provider.get_completions("", 0)

        # Should still have keywords and built-ins
        assert len(result.items) > 0
        labels = [item.label for item in result.items]
        assert "declare" in labels
        assert "sizeof" in labels


class TestHoverProvider:
    """Test HoverProvider functionality"""

    def test_hover_keyword(self):
        """Test hover on keywords"""
        table = SymbolTable()
        provider = HoverProvider(table)

        # Test various keywords
        for keyword in ["declare", "varset", "goto", "if", "return", "bufferit"]:
            hover = provider.get_hover(keyword)
            assert hover is not None
            assert keyword in hover.contents.value
            assert "Syntax:" in hover.contents.value

    def test_hover_variable(self):
        """Test hover on variables"""
        table = SymbolTable()
        table.declare_symbol("counter", SymbolType.INTEGER, 5, 10)
        table.initialize_symbol("counter")
        table.use_symbol("counter", 10, 5)
        table.use_symbol("counter", 12, 8)

        provider = HoverProvider(table)

        # Test with $ prefix
        hover = provider.get_hover("$counter")
        assert hover is not None
        assert "$counter" in hover.contents.value
        assert "integer" in hover.contents.value
        assert "line 6" in hover.contents.value  # line is 0-indexed, displayed as 1-indexed
        assert "Initialized" in hover.contents.value
        assert "2 usage(s)" in hover.contents.value

        # Test without $ prefix
        hover = provider.get_hover("counter")
        assert hover is not None

    def test_hover_uninitialized_variable(self):
        """Test hover on uninitialized variable"""
        table = SymbolTable()
        table.declare_symbol("uninit", SymbolType.BUFFER, 3, 5)

        provider = HoverProvider(table)
        hover = provider.get_hover("$uninit")

        assert hover is not None
        assert "Not initialized" in hover.contents.value

    def test_hover_label(self):
        """Test hover on labels"""
        table = SymbolTable()
        table.declare_label("start", 10, 0)
        table.use_label("start", 5, 10)
        table.use_label("start", 7, 15)

        provider = HoverProvider(table)
        hover = provider.get_hover("start")

        assert hover is not None
        assert "Label" in hover.contents.value
        assert "start:" in hover.contents.value
        assert "line 11" in hover.contents.value
        assert "2 jump(s)" in hover.contents.value

    def test_hover_subroutine(self):
        """Test hover on subroutines"""
        table = SymbolTable()
        table.declare_subroutine("MySub", 20, 0)
        table.use_subroutine("MySub", 5, 5)

        provider = HoverProvider(table)
        hover = provider.get_hover("MySub")

        assert hover is not None
        assert "Subroutine" in hover.contents.value
        assert "MySub" in hover.contents.value
        assert "line 21" in hover.contents.value
        assert "1 time(s)" in hover.contents.value

    def test_hover_handler(self):
        """Test hover on handlers"""
        table = SymbolTable()
        table.declare_handler("DATA.REQ", "file:///data_req.osi", ["payload", "length"])

        provider = HoverProvider(table)
        hover = provider.get_hover("DATA.REQ")

        assert hover is not None
        assert "Event Handler" in hover.contents.value
        assert "DATA.REQ" in hover.contents.value
        assert "payload" in hover.contents.value
        assert "length" in hover.contents.value

    def test_hover_nonexistent(self):
        """Test hover on non-existent symbol"""
        table = SymbolTable()
        provider = HoverProvider(table)

        hover = provider.get_hover("nonexistent")
        assert hover is None

    def test_hover_empty_string(self):
        """Test hover on empty string"""
        table = SymbolTable()
        provider = HoverProvider(table)

        hover = provider.get_hover("")
        assert hover is None

    def test_hover_all_keywords(self):
        """Test hover works for all documented keywords"""
        table = SymbolTable()
        provider = HoverProvider(table)

        keywords = [
            "declare", "varset", "goto", "if", "return",
            "bufferit", "unbufferit", "calccrc", "timer", "untimer",
            "queue", "clearqueue", "dequeue", "peek", "qcount",
            "generateup", "eventdown", "out",
            "subprog", "substart", "subend", "delete",
            "sizeof", "copy", "pos"
        ]

        for keyword in keywords:
            hover = provider.get_hover(keyword)
            assert hover is not None, f"No hover for keyword: {keyword}"
            assert keyword in hover.contents.value.lower()

    def test_hover_case_insensitive_keyword(self):
        """Test hover on keywords is case-insensitive"""
        table = SymbolTable()
        provider = HoverProvider(table)

        hover_lower = provider.get_hover("declare")
        hover_upper = provider.get_hover("DECLARE")
        hover_mixed = provider.get_hover("DeCLaRe")

        assert hover_lower is not None
        assert hover_upper is not None
        assert hover_mixed is not None


class TestDefinitionProvider:
    """Test DefinitionProvider functionality"""

    def test_definition_variable(self):
        """Test go to definition for variable"""
        table = SymbolTable()
        table.declare_symbol("counter", SymbolType.INTEGER, 5, 10, file_uri="file:///test.osi")

        provider = DefinitionProvider(table, "file:///test.osi")
        location = provider.get_definition("$counter")

        assert location is not None
        assert location.uri == "file:///test.osi"
        assert location.range.start.line == 5
        assert location.range.start.character == 10
        assert location.range.end.character == 10 + len("counter")

    def test_definition_without_dollar(self):
        """Test definition works without $ prefix"""
        table = SymbolTable()
        table.declare_symbol("counter", SymbolType.INTEGER, 5, 10)

        provider = DefinitionProvider(table, "file:///test.osi")
        location = provider.get_definition("counter")

        assert location is not None
        assert location.range.start.line == 5

    def test_definition_label(self):
        """Test go to definition for label"""
        table = SymbolTable()
        table.declare_label("start", 15, 0, file_uri="file:///test.osi")

        provider = DefinitionProvider(table, "file:///test.osi")
        location = provider.get_definition("start")

        assert location is not None
        assert location.range.start.line == 15

    def test_definition_subroutine(self):
        """Test go to definition for subroutine"""
        table = SymbolTable()
        table.declare_subroutine("MySub", 25, 0, file_uri="file:///test.osi")

        provider = DefinitionProvider(table, "file:///test.osi")
        location = provider.get_definition("MySub")

        assert location is not None
        assert location.range.start.line == 25

    def test_definition_handler(self):
        """Test go to definition for handler"""
        table = SymbolTable()
        table.declare_handler("DATA.REQ", "file:///data_req.osi")

        provider = DefinitionProvider(table, "file:///current.osi")
        location = provider.get_definition("DATA.REQ")

        assert location is not None
        # Note: The definition provider may convert paths to URIs
        assert "data_req.osi" in location.uri or "file://" in location.uri

    def test_definition_nonexistent(self):
        """Test definition for non-existent symbol"""
        table = SymbolTable()
        provider = DefinitionProvider(table, "file:///test.osi")

        location = provider.get_definition("nonexistent")
        assert location is None

    def test_definition_empty_string(self):
        """Test definition for empty string"""
        table = SymbolTable()
        provider = DefinitionProvider(table, "file:///test.osi")

        location = provider.get_definition("")
        assert location is None

    def test_definition_parent_scope(self):
        """Test definition lookup in parent scope"""
        parent = SymbolTable()
        parent.declare_symbol("global_var", SymbolType.INTEGER, 3, 0, file_uri="file:///init.osi")

        child = SymbolTable(parent=parent)

        provider = DefinitionProvider(child, "file:///handler.osi")
        location = provider.get_definition("$global_var")

        assert location is not None
        assert location.uri == "file:///init.osi"
        assert location.range.start.line == 3

    def test_references_variable(self):
        """Test find all references for variable"""
        table = SymbolTable()
        table.declare_symbol("counter", SymbolType.INTEGER, 2, 0, file_uri="file:///test.osi")
        table.use_symbol("counter", 5, 10)
        table.use_symbol("counter", 8, 15)
        table.use_symbol("counter", 12, 5)

        provider = DefinitionProvider(table, "file:///test.osi")
        locations = provider.get_references("$counter")

        # Should include definition + 3 references = 4 locations
        assert len(locations) == 4

        # First should be definition
        assert locations[0].range.start.line == 2

        # Others should be references
        ref_lines = [loc.range.start.line for loc in locations[1:]]
        assert 5 in ref_lines
        assert 8 in ref_lines
        assert 12 in ref_lines

    def test_references_label(self):
        """Test find all references for label"""
        table = SymbolTable()
        table.declare_label("loop", 10, 0, file_uri="file:///test.osi")
        table.use_label("loop", 5, 10)
        table.use_label("loop", 7, 15)

        provider = DefinitionProvider(table, "file:///test.osi")
        locations = provider.get_references("loop")

        # Definition + 2 references = 3 locations
        assert len(locations) == 3

    def test_references_nonexistent(self):
        """Test references for non-existent symbol"""
        table = SymbolTable()
        provider = DefinitionProvider(table, "file:///test.osi")

        locations = provider.get_references("nonexistent")
        assert len(locations) == 0

    def test_references_empty_list(self):
        """Test references for symbol with no references"""
        table = SymbolTable()
        table.declare_symbol("unused", SymbolType.INTEGER, 5, 0)

        provider = DefinitionProvider(table, "file:///test.osi")
        locations = provider.get_references("$unused")

        # Should still have the definition
        assert len(locations) == 1
        assert locations[0].range.start.line == 5


class TestProvidersIntegration:
    """Test providers working together"""

    def test_complete_workflow(self):
        """Test a complete workflow with all providers"""
        # Set up symbol table
        table = SymbolTable()
        table.declare_symbol("counter", SymbolType.INTEGER, 1, 0, file_uri="file:///test.osi")
        table.declare_label("start", 5, 0, file_uri="file:///test.osi")
        table.declare_subroutine("MySub", 10, 0, file_uri="file:///test.osi")

        table.initialize_symbol("counter")
        table.use_symbol("counter", 3, 5)
        table.use_label("start", 8, 10)
        table.use_subroutine("MySub", 6, 5)

        # Test completion
        completion_provider = CompletionProvider(table)
        completions = completion_provider.get_completions("", 0)
        labels = [item.label for item in completions.items]
        assert "$counter" in labels
        assert "start" in labels
        assert "MySub" in labels

        # Test hover
        hover_provider = HoverProvider(table)

        counter_hover = hover_provider.get_hover("$counter")
        assert counter_hover is not None
        assert "integer" in counter_hover.contents.value

        start_hover = hover_provider.get_hover("start")
        assert start_hover is not None
        assert "Label" in start_hover.contents.value

        # Test definition
        def_provider = DefinitionProvider(table, "file:///test.osi")

        counter_def = def_provider.get_definition("$counter")
        assert counter_def is not None
        assert counter_def.range.start.line == 1

        start_def = def_provider.get_definition("start")
        assert start_def is not None
        assert start_def.range.start.line == 5

        # Test references
        counter_refs = def_provider.get_references("$counter")
        assert len(counter_refs) == 2  # Declaration + 1 use

    def test_providers_with_empty_table(self):
        """Test all providers work with empty symbol table"""
        table = SymbolTable()

        # Completion should still provide keywords
        comp_provider = CompletionProvider(table)
        completions = comp_provider.get_completions("", 0)
        assert len(completions.items) > 0

        # Hover should work for keywords
        hover_provider = HoverProvider(table)
        hover = hover_provider.get_hover("declare")
        assert hover is not None

        # Definition should return None
        def_provider = DefinitionProvider(table, "file:///test.osi")
        location = def_provider.get_definition("nonexistent")
        assert location is None

    def test_providers_preserve_references(self):
        """Test that providers correctly report reference counts"""
        table = SymbolTable()
        table.declare_symbol("var", SymbolType.INTEGER, 1, 0)

        # Use variable multiple times
        for i in range(5):
            table.use_symbol("var", i + 10, 0)

        # Hover should show correct count
        hover_provider = HoverProvider(table)
        hover = hover_provider.get_hover("$var")
        assert hover is not None
        assert "5 usage(s)" in hover.contents.value

        # References should show all uses
        def_provider = DefinitionProvider(table, "file:///test.osi")
        refs = def_provider.get_references("$var")
        assert len(refs) == 6  # 1 definition + 5 uses
