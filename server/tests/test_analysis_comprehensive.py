"""Comprehensive tests for analysis module (symbol_table, semantic_analyzer, validator)"""

import pytest
from osi_lsp.analysis.symbol_table import SymbolTable, SymbolType, Symbol, Label, Subroutine, HandlerSymbol
from osi_lsp.analysis.semantic_analyzer import SemanticAnalyzer
from osi_lsp.analysis.validator import Validator
from osi_lsp.parser.lexer import Lexer
from osi_lsp.parser.parser import Parser
from lsprotocol.types import DiagnosticSeverity


def parse(text):
    """Helper to parse text"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast, _ = parser.parse()
    return ast


class TestSymbolTable:
    """Test SymbolTable functionality"""

    def test_declare_symbol_success(self):
        """Test successful symbol declaration"""
        table = SymbolTable()
        result = table.declare_symbol("counter", SymbolType.INTEGER, 1, 5)
        assert result is True
        assert "counter" in table.symbols
        symbol = table.get_symbol("counter")
        assert symbol.name == "counter"
        assert symbol.symbol_type == SymbolType.INTEGER
        assert symbol.line == 1
        assert symbol.column == 5

    def test_declare_symbol_duplicate(self):
        """Test duplicate symbol declaration fails"""
        table = SymbolTable()
        table.declare_symbol("counter", SymbolType.INTEGER, 1, 5)
        result = table.declare_symbol("counter", SymbolType.BUFFER, 2, 10)
        assert result is False

    def test_get_symbol_not_found(self):
        """Test getting non-existent symbol"""
        table = SymbolTable()
        symbol = table.get_symbol("nonexistent")
        assert symbol is None

    def test_use_symbol(self):
        """Test marking symbol as used"""
        table = SymbolTable()
        table.declare_symbol("counter", SymbolType.INTEGER, 1, 5)
        result = table.use_symbol("counter", 5, 10)
        assert result is True
        symbol = table.get_symbol("counter")
        assert symbol.used is True
        assert len(symbol.references) == 1
        assert symbol.references[0] == (5, 10)

    def test_use_symbol_multiple_times(self):
        """Test symbol with multiple references"""
        table = SymbolTable()
        table.declare_symbol("counter", SymbolType.INTEGER, 1, 5)
        table.use_symbol("counter", 5, 10)
        table.use_symbol("counter", 7, 15)
        table.use_symbol("counter", 9, 20)
        symbol = table.get_symbol("counter")
        assert len(symbol.references) == 3

    def test_initialize_symbol(self):
        """Test initializing symbol"""
        table = SymbolTable()
        table.declare_symbol("counter", SymbolType.INTEGER, 1, 5)
        symbol = table.get_symbol("counter")
        assert symbol.initialized is False
        table.initialize_symbol("counter")
        assert symbol.initialized is True

    def test_declare_label(self):
        """Test label declaration"""
        table = SymbolTable()
        result = table.declare_label("start", 10, 0)
        assert result is True
        label = table.get_label("start")
        assert label.name == "start"
        assert label.line == 10

    def test_use_label(self):
        """Test using label"""
        table = SymbolTable()
        table.declare_label("start", 10, 0)
        result = table.use_label("start", 5, 10)
        assert result is True
        label = table.get_label("start")
        assert label.used is True
        assert len(label.references) == 1

    def test_declare_subroutine(self):
        """Test subroutine declaration"""
        table = SymbolTable()
        result = table.declare_subroutine("MySub", 20, 0)
        assert result is True
        sub = table.get_subroutine("MySub")
        assert sub.name == "MySub"

    def test_use_subroutine(self):
        """Test using subroutine"""
        table = SymbolTable()
        table.declare_subroutine("MySub", 20, 0)
        result = table.use_subroutine("MySub", 5, 0)
        assert result is True
        sub = table.get_subroutine("MySub")
        assert sub.used is True

    def test_declare_handler(self):
        """Test handler declaration"""
        table = SymbolTable()
        result = table.declare_handler("DATA.REQ", "file:///test.osi", ["param1", "param2"])
        assert result is True
        handler = table.get_handler("DATA.REQ")
        assert handler.name == "DATA.REQ"
        assert len(handler.parameters) == 2

    def test_parent_scope_lookup(self):
        """Test symbol lookup in parent scope"""
        parent = SymbolTable()
        parent.declare_symbol("global_var", SymbolType.INTEGER, 1, 0)

        child = SymbolTable(parent=parent)
        child.declare_symbol("local_var", SymbolType.STRING, 2, 0)

        # Child can see both local and parent symbols
        assert child.get_symbol("local_var") is not None
        assert child.get_symbol("global_var") is not None

        # Parent cannot see child symbols
        assert parent.get_symbol("local_var") is None

    def test_shadowing(self):
        """Test local symbol shadows parent symbol"""
        parent = SymbolTable()
        parent.declare_symbol("var", SymbolType.INTEGER, 1, 0)

        child = SymbolTable(parent=parent)
        child.declare_symbol("var", SymbolType.STRING, 2, 0)

        # Child's version shadows parent
        symbol = child.get_symbol("var")
        assert symbol.symbol_type == SymbolType.STRING

    def test_use_symbol_in_parent(self):
        """Test marking parent symbol as used from child"""
        parent = SymbolTable()
        parent.declare_symbol("global_var", SymbolType.INTEGER, 1, 0)

        child = SymbolTable(parent=parent)
        child.use_symbol("global_var", 5, 10)

        # Parent symbol should be marked as used
        symbol = parent.get_symbol("global_var")
        assert symbol.used is True
        assert len(symbol.references) == 1

    def test_get_unused_symbols(self):
        """Test finding unused symbols"""
        table = SymbolTable()
        table.declare_symbol("used", SymbolType.INTEGER, 1, 0)
        table.declare_symbol("unused", SymbolType.INTEGER, 2, 0)
        table.use_symbol("used", 5, 0)

        unused = table.get_unused_symbols()
        assert len(unused) == 1
        assert unused[0].name == "unused"

    def test_get_unused_labels(self):
        """Test finding unused labels"""
        table = SymbolTable()
        table.declare_label("used", 1, 0)
        table.declare_label("unused", 2, 0)
        table.use_label("used", 5, 0)

        unused = table.get_unused_labels()
        assert len(unused) == 1
        assert unused[0].name == "unused"

    def test_get_uninitialized_symbols(self):
        """Test finding uninitialized symbols"""
        table = SymbolTable()
        table.declare_symbol("initialized", SymbolType.INTEGER, 1, 0)
        table.declare_symbol("uninitialized", SymbolType.INTEGER, 2, 0)

        table.initialize_symbol("initialized")
        table.use_symbol("initialized", 5, 0)
        table.use_symbol("uninitialized", 6, 0)

        uninit = table.get_uninitialized_symbols()
        assert len(uninit) == 1
        assert uninit[0].name == "uninitialized"

    def test_get_all_symbols_with_parent(self):
        """Test getting all symbols including parent"""
        parent = SymbolTable()
        parent.declare_symbol("global1", SymbolType.INTEGER, 1, 0)
        parent.declare_symbol("global2", SymbolType.BUFFER, 2, 0)

        child = SymbolTable(parent=parent)
        child.declare_symbol("local1", SymbolType.STRING, 3, 0)

        all_symbols = child.get_all_symbols()
        assert len(all_symbols) == 3
        names = [s.name for s in all_symbols]
        assert "global1" in names
        assert "global2" in names
        assert "local1" in names

    def test_get_all_handlers_with_parent(self):
        """Test getting all handlers including parent"""
        parent = SymbolTable()
        parent.declare_handler("INIT", "file:///init.osi")
        parent.declare_handler("GLOBAL_HANDLER", "file:///global.osi")

        child = SymbolTable(parent=parent)
        child.declare_handler("LOCAL_HANDLER", "file:///local.osi")

        all_handlers = child.get_all_handlers()
        assert len(all_handlers) == 3
        names = [h.name for h in all_handlers]
        assert "INIT" in names
        assert "GLOBAL_HANDLER" in names
        assert "LOCAL_HANDLER" in names

    def test_clear_symbols(self):
        """Test clearing symbol table"""
        table = SymbolTable()
        table.declare_symbol("var", SymbolType.INTEGER, 1, 0)
        table.declare_label("label", 2, 0)
        table.declare_subroutine("sub", 3, 0)

        table.clear()

        assert len(table.symbols) == 0
        assert len(table.labels) == 0
        assert len(table.subroutines) == 0

    def test_symbol_with_file_uri(self):
        """Test symbol with file URI"""
        table = SymbolTable()
        table.declare_symbol("var", SymbolType.INTEGER, 1, 0, file_uri="file:///test.osi")
        symbol = table.get_symbol("var")
        assert symbol.file_uri == "file:///test.osi"


class TestSemanticAnalyzer:
    """Test SemanticAnalyzer functionality"""

    def test_analyze_declare(self):
        """Test analyzing variable declarations"""
        code = """
        counter declare integer
        data_buffer declare buffer
        """
        ast = parse(code)
        table = SymbolTable()
        analyzer = SemanticAnalyzer(table)
        analyzer.analyze(ast)

        assert table.get_symbol("counter") is not None
        assert table.get_symbol("data_buffer") is not None
        assert table.get_symbol("counter").symbol_type == SymbolType.INTEGER
        assert table.get_symbol("data_buffer").symbol_type == SymbolType.BUFFER

    def test_analyze_duplicate_declaration(self):
        """Test detecting duplicate declarations"""
        code = """
        counter declare integer
        counter declare buffer
        """
        ast = parse(code)
        table = SymbolTable()
        analyzer = SemanticAnalyzer(table)
        analyzer.analyze(ast)

        assert len(analyzer.errors) == 1
        assert "already declared" in analyzer.errors[0]

    def test_analyze_varset(self):
        """Test analyzing varset statements"""
        code = """
        counter declare integer
        0 varset counter
        """
        ast = parse(code)
        table = SymbolTable()
        analyzer = SemanticAnalyzer(table)
        analyzer.analyze(ast)

        symbol = table.get_symbol("counter")
        assert symbol.initialized is True
        assert symbol.used is False  # Used flag is set when variable is read

    def test_analyze_undeclared_variable(self):
        """Test detecting undeclared variable"""
        code = """
        0 varset undeclared
        """
        ast = parse(code)
        table = SymbolTable()
        analyzer = SemanticAnalyzer(table)
        analyzer.analyze(ast)

        assert len(analyzer.errors) == 1
        assert "not declared" in analyzer.errors[0]

    def test_analyze_labels(self):
        """Test analyzing labels"""
        code = """
        start:
            goto end
        end:
            return
        """
        ast = parse(code)
        table = SymbolTable()
        analyzer = SemanticAnalyzer(table)
        analyzer.analyze(ast)

        assert table.get_label("start") is not None
        assert table.get_label("end") is not None
        assert table.get_label("end").used is True

    def test_analyze_undefined_label(self):
        """Test detecting undefined label"""
        code = """
        goto undefined_label
        """
        ast = parse(code)
        table = SymbolTable()
        analyzer = SemanticAnalyzer(table)
        analyzer.analyze(ast)

        assert len(analyzer.errors) == 1
        assert "not defined" in analyzer.errors[0]

    def test_analyze_subroutines(self):
        """Test analyzing subroutines"""
        code = """
        subprog MySub
        return

        substart MySub
            out "In subroutine"
        subend
        """
        ast = parse(code)
        table = SymbolTable()
        analyzer = SemanticAnalyzer(table)
        analyzer.analyze(ast)

        sub = table.get_subroutine("MySub")
        assert sub is not None
        assert sub.used is True

    def test_analyze_undefined_subroutine(self):
        """Test detecting undefined subroutine"""
        code = """
        subprog UndefinedSub
        """
        ast = parse(code)
        table = SymbolTable()
        analyzer = SemanticAnalyzer(table)
        analyzer.analyze(ast)

        assert len(analyzer.errors) == 1
        assert "not defined" in analyzer.errors[0]

    def test_analyze_variable_usage(self):
        """Test tracking variable usage"""
        code = """
        x declare integer
        y declare integer
        5 varset x
        $x + 1 varset y
        """
        ast = parse(code)
        table = SymbolTable()
        analyzer = SemanticAnalyzer(table)
        analyzer.analyze(ast)

        x_symbol = table.get_symbol("x")
        y_symbol = table.get_symbol("y")
        assert x_symbol.used is True  # x is used in expression
        assert x_symbol.initialized is True
        assert y_symbol.initialized is True

    def test_analyze_type_checking(self):
        """Test basic type checking"""
        code = """
        num declare integer
        str declare string
        "hello" varset num
        """
        ast = parse(code)
        table = SymbolTable()
        analyzer = SemanticAnalyzer(table)
        analyzer.analyze(ast)

        # Should have a type mismatch error (changed from warning)
        assert len(analyzer.errors) > 0
        assert "Type mismatch" in analyzer.errors[0]

    def test_analyze_bufferit(self):
        """Test analyzing bufferit"""
        code = """
        buff declare buffer
        buff bufferit 10 1 2 500 4
        """
        ast = parse(code)
        table = SymbolTable()
        analyzer = SemanticAnalyzer(table)
        analyzer.analyze(ast)

        symbol = table.get_symbol("buff")
        assert symbol.initialized is True

    def test_analyze_unbufferit(self):
        """Test analyzing unbufferit"""
        code = """
        buff declare buffer
        var1 declare integer
        var2 declare integer
        unbufferit buff var1 2 var2 4
        """
        ast = parse(code)
        table = SymbolTable()
        analyzer = SemanticAnalyzer(table)
        analyzer.analyze(ast)

        assert table.get_symbol("var1").initialized is True
        assert table.get_symbol("var2").initialized is True

    def test_analyze_unbufferit_undeclared_buffer(self):
        """Test unbufferit with undeclared buffer"""
        code = """
        var1 declare integer
        unbufferit undeclared_buff var1 2
        """
        ast = parse(code)
        table = SymbolTable()
        analyzer = SemanticAnalyzer(table)
        analyzer.analyze(ast)

        assert len(analyzer.errors) == 1
        assert "not declared" in analyzer.errors[0]

    def test_analyze_queue_operations(self):
        """Test analyzing queue operations"""
        code = """
        q declare queue
        q queue 100
        """
        ast = parse(code)
        table = SymbolTable()
        analyzer = SemanticAnalyzer(table)
        analyzer.analyze(ast)

        assert len(analyzer.errors) == 0

    def test_analyze_queue_type_mismatch(self):
        """Test queue operation on non-queue"""
        code = """
        not_queue declare integer
        not_queue queue 100
        """
        ast = parse(code)
        table = SymbolTable()
        analyzer = SemanticAnalyzer(table)
        analyzer.analyze(ast)

        assert len(analyzer.warnings) > 0
        assert "not a queue" in analyzer.warnings[0]

    def test_analyze_with_parent_scope(self):
        """Test analyzing with parent symbol table"""
        # Parent has global var
        parent = SymbolTable()
        parent.declare_symbol("global_var", SymbolType.INTEGER, 0, 0)

        # Child uses global var
        code = """
        $global_var + 1 varset global_var
        """
        ast = parse(code)
        child = SymbolTable(parent=parent)
        analyzer = SemanticAnalyzer(child)
        analyzer.analyze(ast)

        # Should have no errors
        assert len(analyzer.errors) == 0
        # Global var should be used
        assert parent.get_symbol("global_var").used is True


class TestValidator:
    """Test Validator functionality"""

    def test_validate_basic_program(self):
        """Test validating basic program"""
        code = """
        counter declare integer
        0 varset counter
        """
        ast = parse(code)
        table = SymbolTable()
        validator = Validator(table)
        diagnostics = validator.validate(ast, "file:///test.osi", valid_init=True)

        # Should have errors because declarations not in INIT.osi
        errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
        assert len(errors) > 0

    def test_validate_init_file(self):
        """Test validating INIT.osi"""
        code = """
        counter declare integer
        data_buffer declare buffer
        """
        ast = parse(code)
        table = SymbolTable()
        validator = Validator(table)
        diagnostics = validator.validate(ast, "file:///INIT.osi", valid_init=True)

        # INIT.osi can have declarations, should be no errors
        errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
        assert len(errors) == 0

    def test_validate_init_with_executable_code(self):
        """Test INIT.osi cannot have executable code"""
        code = """
        counter declare integer
        0 varset counter
        """
        ast = parse(code)
        table = SymbolTable()
        validator = Validator(table)
        diagnostics = validator.validate(ast, "file:///INIT.osi", valid_init=True)

        # Should have error about executable code in INIT
        errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
        assert any("cannot contain executable code" in d.message for d in errors)

    def test_validate_handler_without_return(self):
        """Test handler should end with return"""
        code = """
        DATA_HANDLER:
            out "test"
        """
        ast = parse(code)
        table = SymbolTable()
        validator = Validator(table)
        diagnostics = validator.validate(ast, "file:///DATA_HANDLER.osi", valid_init=True)

        # Should have warning about missing return
        warnings = [d for d in diagnostics if d.severity == DiagnosticSeverity.Warning]
        assert any("should end with 'return'" in d.message for d in warnings)

    def test_validate_handler_name_mismatch(self):
        """Test handler name must match filename"""
        code = """
        WRONG_NAME:
            return
        """
        ast = parse(code)
        table = SymbolTable()
        validator = Validator(table)
        diagnostics = validator.validate(ast, "file:///CORRECT_NAME.osi", valid_init=True)

        # Should have error about handler name mismatch
        errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
        assert any("must match filename" in d.message for d in errors)

    def test_validate_unused_variable(self):
        """Test warning for unused variables"""
        code = """
        HANDLER:
            used declare integer
            unused declare integer
            5 varset used
            out $used
            goto HANDLER
            return
        """
        ast = parse(code)
        table = SymbolTable()
        validator = Validator(table)
        diagnostics = validator.validate(ast, "file:///HANDLER.osi", valid_init=True)

        # Should have error about declarations and warning about unused variable
        warnings = [d for d in diagnostics if d.severity == DiagnosticSeverity.Warning]
        # Filter for unused variable warning (not label)
        unused_var_warnings = [w for w in warnings if "Variable" in w.message and "never used" in w.message]
        assert len(unused_var_warnings) == 1

    def test_validate_unused_label(self):
        """Test warning for unused labels"""
        code = """
        HANDLER:
            used:
                goto end
            unused:
                return
            end:
                return
        """
        ast = parse(code)
        table = SymbolTable()
        validator = Validator(table)
        diagnostics = validator.validate(ast, "file:///HANDLER.osi", valid_init=True)

        warnings = [d for d in diagnostics if d.severity == DiagnosticSeverity.Warning]
        unused_warnings = [w for w in warnings if "never used" in w.message]
        assert len(unused_warnings) > 0

    def test_validate_missing_init(self):
        """Test error when INIT.osi is missing"""
        code = """
        HANDLER:
            return
        """
        ast = parse(code)
        table = SymbolTable()
        validator = Validator(table)
        diagnostics = validator.validate(ast, "file:///HANDLER.osi", valid_init=False)

        # Should have error about missing INIT.osi
        errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
        assert any("must contain INIT.osi" in d.message for d in errors)

    def test_validate_semantic_errors(self):
        """Test semantic errors are converted to diagnostics"""
        code = """
        HANDLER:
            $undeclared + 1 varset x
            return
        """
        ast = parse(code)
        table = SymbolTable()
        validator = Validator(table)
        diagnostics = validator.validate(ast, "file:///HANDLER.osi", valid_init=True)

        errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
        # Should have errors about undeclared variables
        assert len(errors) > 0
