import pytest
from lsprotocol.types import CompletionItemKind, Position
from osi_lsp.analysis.symbol_table import SymbolTable, SymbolType
from osi_lsp.providers.completion import CompletionProvider
from osi_lsp.providers.hover import HoverProvider
from osi_lsp.providers.definition import DefinitionProvider

@pytest.fixture
def symbol_table():
    st = SymbolTable()
    st.declare_symbol("my_var", SymbolType.INTEGER, 0, 0)
    st.declare_symbol("my_buffer", SymbolType.BUFFER, 1, 0)
    st.initialize_symbol("my_var")
    
    st.declare_label("start_label", 10, 0)
    st.declare_subroutine("do_work", 20, 0)
    st.declare_handler("SEND_DATA", "file:///path/to/SEND_DATA.osi")
    return st

class TestCompletion:
    def test_complete_keywords(self, symbol_table):
        provider = CompletionProvider(symbol_table)
        # Empty line - suggest keywords
        completions = provider.get_completions("", 0)
        
        labels = [i.label for i in completions.items]
        assert "declare" in labels
        assert "varset" in labels
        assert "if" in labels

    def test_complete_varset_insert_text(self, symbol_table):
        provider = CompletionProvider(symbol_table)
        completions = provider.get_completions("", 0)
        
        # Find varset item
        varset_item = next(i for i in completions.items if i.label == "varset")
        
        # Verify insert_text is just "varset" and NOT "expression varset $variable"
        assert varset_item.insert_text == "varset"

    def test_complete_variables(self, symbol_table):
        provider = CompletionProvider(symbol_table)
        completions = provider.get_completions("$my", 3)
        
        # Check for variable suggestions
        items = [i for i in completions.items if i.kind == CompletionItemKind.Variable]
        labels = [i.label for i in items]
        assert "$my_var" in labels
        assert "$my_buffer" in labels

    def test_complete_types_after_declare(self, symbol_table):
        provider = CompletionProvider(symbol_table)
        completions = provider.get_completions("name declare ", 13)
        
        items = [i for i in completions.items if i.kind == CompletionItemKind.TypeParameter]
        labels = [i.label for i in items]
        insert_texts = [i.insert_text for i in items]
        
        assert "integer" in labels
        assert "buffer" in labels
        
        # Verify insert_text matches label (not the full declaration pattern)
        assert "integer" in insert_texts
        assert "buffer" in insert_texts
        assert "name declare integer" not in insert_texts

class TestHover:
    def test_hover_variable(self, symbol_table):
        provider = HoverProvider(symbol_table)
        hover = provider.get_hover("$my_var")
        
        assert hover is not None
        content = hover.contents.value
        assert "**Variable**: `$my_var`" in content
        assert "**Type**: `integer`" in content
        assert "✓ Initialized" in content

    def test_hover_uninitialized_variable(self, symbol_table):
        symbol_table.declare_symbol("uninit", SymbolType.STRING, 5, 0)
        provider = HoverProvider(symbol_table)
        hover = provider.get_hover("$uninit")
        
        assert hover is not None
        assert "⚠ Not initialized" in hover.contents.value

    def test_hover_keyword(self, symbol_table):
        provider = HoverProvider(symbol_table)
        hover = provider.get_hover("varset")
        
        assert hover is not None
        assert "**varset** - Assign value" in hover.contents.value

    def test_hover_handler(self, symbol_table):
        provider = HoverProvider(symbol_table)
        hover = provider.get_hover("SEND_DATA")
        
        assert hover is not None
        assert "**Event Handler**: `## SEND_DATA`" in hover.contents.value

class TestDefinition:
    def test_definition_variable(self, symbol_table):
        provider = DefinitionProvider(symbol_table, "file:///test.osi")
        loc = provider.get_definition("$my_var")
        
        assert loc is not None
        assert loc.range.start.line == 0
        assert loc.range.start.character == 0

    def test_definition_handler(self, symbol_table):
        provider = DefinitionProvider(symbol_table, "file:///test.osi")
        loc = provider.get_definition("SEND_DATA")
        
        assert loc is not None
        # Should point to the file registered in handler
        assert "SEND_DATA.osi" in loc.uri
