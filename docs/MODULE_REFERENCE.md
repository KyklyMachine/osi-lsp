# OSI Language Server - Module Reference

Comprehensive documentation of all modules in the OSI Language Server implementation.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Parser Modules](#parser-modules)
3. [Analysis Modules](#analysis-modules)
4. [Provider Modules](#provider-modules)
5. [Workspace Modules](#workspace-modules)
6. [Server Module](#server-module)

---

## Architecture Overview

### Component Structure
```
server/osi_lsp/
├── parser/          # Lexical and syntactic analysis
├── analysis/        # Semantic analysis and validation
├── providers/       # LSP feature implementations
├── workspace/       # Multi-file project management
└── server.py        # Main LSP server
```

### Processing Pipeline
```
Source Text → Lexer → Tokens → Parser → AST → Semantic Analyzer → Symbol Table
                                                                   ↓
                                            LSP Features ← Providers + Validator
```

---

## Parser Modules

### `parser/lexer.py`

**Purpose**: Tokenization of source code.

**Key Classes**:
- `TokenType` (Enum): Defines 95 token types including keywords, operators, literals, identifiers, and delimiters
- `Token` (Dataclass): Represents a single token with type, value, line, and column
- `Lexer`: Main tokenization engine

**Features**:
- **Character-by-character scanning** with lookahead capability
- **Position tracking**: Maintains line and column numbers for error reporting
- **Comment handling**: Recognizes and skips semicolon-prefixed comments
- **Multi-character operator recognition**: `==`, `!=`, `>=`, `<=`, `&&`, `||`
- **String literal parsing** with escape sequence support (`\n`, `\t`, `\r`, `\\`, `\"`)
- **Special token types**:
  - Variables prefixed with `$`
  - Labels suffixed with `:`
  - Character codes prefixed with `#`
  - Handler names prefixed with `##`
- **Case-insensitive keyword matching**
- **Error reporting**: Raises `ProtocolError` with exact position

**API**:
- `tokenize() -> List[Token]`: Tokenizes entire input
- `get_next_token() -> Token`: Returns next token in stream
- `peek(offset) -> str`: Lookahead without consuming

---

### `parser/parser.py`

**Purpose**: Syntactic analysis and AST construction.

**Key Classes**:
- `Parser`: Recursive descent parser

**Features**:
- **Recursive descent parsing** with operator precedence climbing
- **Operator precedence handling** (7 levels from logical OR to primary expressions)
- **Two-pass statement parsing**:
  - Expression-first statements (RPN style)
  - Keyword-first statements
- **Comment filtering**: Automatically removes comment tokens
- **Lookahead capability**: Can peek at next token without consuming
- **Error recovery**: Implements synchronization to continue parsing after errors (skips to next line).
- **Structured statement parsing**:
  - Declarations
  - Assignments
  - Control flow (goto, if, return)
  - Buffer operations
  - Queue operations
  - Timer operations
  - Event operations
  - Subroutine definitions
- **Expression parsing**:
  - Binary operations with precedence
  - Function calls with arguments
  - Literals (number, string, character codes)
  - Variable references
  - Parenthesized expressions

**API**:
- `parse() -> (Program, List[ProtocolError])`: Parses entire program, returning AST and list of errors
- `parse_statement() -> Statement`: Parses single statement
- `parse_expression() -> Expression`: Parses expression with precedence
- `expect(TokenType) -> Token`: Enforces token type

---

### `parser/ast_nodes.py`

**Purpose**: Abstract Syntax Tree node definitions.

**Features**:
- **Visitor pattern implementation**: All nodes implement `accept(visitor)`
- **Hierarchical structure**:
  - `ASTNode` (abstract base)
    - `Program` (root node)
    - `Statement` (abstract base for statements)
    - `Expression` (abstract base for expressions)
- **26 statement types**: Declarations, control flow, operations, etc.
- **6 expression types**: Literals, variables, operations, function calls
- **Dataclass-based**: All nodes are dataclasses with immutable structure
- **Position tracking**: All nodes store line and column
- **Visitor interface**: `ASTVisitor` abstract class with methods for each node type

**Node Categories**:
- **Declarations**: Variable declarations
- **Assignments**: Variable assignments
- **Control Flow**: Goto, if, return, labels
- **Operations**: Buffer, queue, timer, CRC operations
- **Events**: Upward and downward event generation
- **Subroutines**: Definition and calls
- **Expressions**: Literals, variables, binary operations, function calls

---

### `parser/errors.py`

**Purpose**: Custom exception for parsing errors.

**Features**:
- **Position-aware errors**: Stores line and column
- **Formatted output**: `{line}:{column}: {message}`
- **Used by**: Both lexer and parser
- **Converted to LSP diagnostics** by server

---

## Analysis Modules

### `analysis/symbol_table.py`

**Purpose**: Symbol management with hierarchical scoping.

**Key Classes**:
- `SymbolType` (Enum): 5 variable types (integer, buffer, string, queue, unknown)
- `Symbol`: Variable information with usage tracking
- `Label`: Label information with usage tracking
- `Subroutine`: Subroutine information with usage tracking
- `HandlerSymbol`: Event handler information
- `SymbolTable`: Main symbol management class

**Features**:
- **Hierarchical scoping**: Parent-child symbol table relationships
- **Symbol lifecycle tracking**:
  - Declaration location (line, column, file URI)
  - Initialization status
  - Usage status
  - All reference locations
- **Four symbol categories**:
  - Variables (typed: integer, buffer, string, queue)
  - Labels (for goto/if statements)
  - Subroutines (callable code blocks)
  - Handlers (event handlers)
- **Scope resolution**: Searches local table first, then parent
- **Cross-file support**: Stores file URI for each symbol
- **Analysis utilities**:
  - Find unused symbols
  - Find uninitialized symbols
  - Get all symbols (local + parent)
- **Reference tracking**: Records every usage location
- **Prevents redeclaration**: Returns false if symbol already exists

**API**:
- `declare_symbol(name, type, line, col, uri) -> bool`
- `get_symbol(name) -> Optional[Symbol]`
- `use_symbol(name, line, col) -> bool`
- `initialize_symbol(name)`
- Similar APIs for labels, subroutines, handlers
- `get_unused_symbols() -> List[Symbol]`
- `get_uninitialized_symbols() -> List[Symbol]`

---

### `analysis/semantic_analyzer.py`

**Purpose**: Semantic analysis through AST traversal.

**Key Classes**:
- `SemanticAnalyzer`: Implements `ASTVisitor` pattern

**Features**:
- **Symbol table population**: Builds symbol table from AST
- **Two-pass analysis**:
  1. Register all labels and subroutines
  2. Analyze all statements
- **Type checking**: Performs simplified type inference and checking
- **Error collection**: Accumulates errors and warnings without stopping
- **Initialization tracking**: Marks variables as initialized on assignment
- **Usage tracking**: Marks symbols as used when referenced
- **Cross-reference validation**:
  - Ensures goto/if targets exist
  - Ensures subroutine call targets exist
  - Ensures variables are declared before use
- **Type inference**: Infers expression types based on literals, operations, and functions
- **Duplicate detection**: Reports redeclaration errors
- **Warning generation**: Unused symbols

**Checks Performed**:
- Variable declaration before use
- No duplicate declarations
- Label existence for goto/if
- Subroutine existence for calls
- Queue type validation
- Type compatibility (Errors)

**API**:
- `analyze(ast: Program)`: Main entry point
- `visit_*` methods for each AST node type
- `get_expression_type(expr) -> SymbolType`: Type inference
- `errors: List[str]`: Accumulated errors
- `warnings: List[str]`: Accumulated warnings

---

### `analysis/validator.py`

**Purpose**: Generate LSP diagnostics from semantic analysis.

**Key Classes**:
- `Validator`: Converts analysis results to LSP diagnostics

**Features**:
- **Structure validation**:
  - INIT.osi files: Cannot contain executable code
  - Handler files: Must have matching label, should end with return
  - Directory validation: Checks for INIT.osi existence
- **Semantic validation**: Runs `SemanticAnalyzer` and converts results
- **Usage validation**: Reports unused symbols, labels, subroutines
- **Initialization validation**: Warns about uninitialized variables
- **Diagnostic creation**:
  - Converts error messages to LSP `Diagnostic` objects
  - Sets appropriate severity (Error vs Warning)
  - Creates ranges from position information
- **File type detection**: Different rules for INIT.osi vs handler files
- **Skip logic**: Skips usage checks for INIT.osi (requires project-wide analysis)

**Validation Rules**:
- INIT.osi: Only declarations allowed
- Handler files: Must match filename, should end with return
- All files: No undeclared variables, no duplicate declarations
- All files: Warns on unused/uninitialized symbols

**API**:
- `validate(ast, file_uri, valid_init) -> List[Diagnostic]`

---

## Provider Modules

### `providers/completion.py`

**Purpose**: Autocompletion suggestions.

**Key Classes**:
- `CompletionProvider`: Generates completion items

**Features**:
- **Context-aware completions**: Different suggestions based on cursor position
- **Multiple completion categories**:
  - Keywords (declare, varset, goto, if, return)
  - Operators (bufferit, timer, queue, etc.)
  - Types (integer, buffer, string, queue)
  - Built-in functions (sizeof, copy, pos, etc.)
  - User-defined symbols from symbol table
- **Symbol table integration**:
  - Variables with type information
  - Labels
  - Subroutines
  - Event handlers
- **Rich completion items**:
  - Label: Display text
  - Kind: Icon type (keyword, function, variable, etc.)
  - Detail: Description
  - Insert text: Code snippet
- **Special context handling**: Shows only types after "declare" keyword

**Completion Categories**:
- 5 keywords
- 17 operators/functions
- 4 types
- 5 built-in functions
- All user symbols from symbol table

**API**:
- `get_completions(line, character) -> CompletionList`

---

### `providers/hover.py`

**Purpose**: Hover documentation.

**Key Classes**:
- `HoverProvider`: Generates hover information

**Features**:
- **Documentation for keywords**: Built-in documentation for all language keywords
- **Symbol information**: Shows details for user-defined symbols
- **Markdown formatting**: Rich formatting with bold, code blocks
- **Multiple information sources**:
  - Keyword documentation (syntax and description)
  - Variable information (type, location, initialization status, references)
  - Label information (location, jump count)
  - Subroutine information (location, call count)
  - Handler information (location, parameters)
- **Reference counting**: Shows number of usages
- **Status indicators**: Visual indicators (✓ for initialized, ⚠ for not initialized)
- **Position information**: Shows declaration/definition location

**Information Displayed**:
- **Variables**: Type, declaration location, initialization status, reference count
- **Labels**: Definition location, jump count
- **Subroutines**: Definition location, call count
- **Handlers**: Definition location, parameters
- **Keywords**: Syntax and description

**API**:
- `get_hover(word) -> Optional[Hover]`

---

### `providers/definition.py`

**Purpose**: Go to Definition and Find References.

**Key Classes**:
- `DefinitionProvider`: Navigation to definitions and references

**Features**:
- **Go to Definition**:
  - Variables: Jump to declaration
  - Labels: Jump to definition
  - Subroutines: Jump to definition
  - Handlers: Jump to handler file
- **Cross-file navigation**: Supports jumping to symbols in different files
- **URI handling**: Converts file paths to file:// URIs
- **Find References**:
  - Shows definition location
  - Shows all usage locations
  - Includes reference count
- **Symbol lookup priority**:
  1. Variables
  2. Labels
  3. Subroutines
  4. Handlers

**Current Limitations**:
- References are file-local (project-wide tracking not yet implemented)
- Subroutine references not fully tracked

**API**:
- `get_definition(word) -> Optional[Location]`
- `get_references(word) -> List[Location]`

---

## Workspace Modules

### `workspace/project.py`

**Purpose**: Multi-file project structure management.

**Key Classes**:
- `DirectoryContext`: Context for a single directory
- `OSIProject`: Project-wide management

**Features**:
- **Multi-file support**: Manages relationships between INIT.osi and handler files
- **Directory-based scoping**: Each directory has its own global scope
- **Lazy loading**: Loads INIT.osi on first access to directory
- **Caching**: Caches parsed INIT.osi to avoid repeated parsing
- **Automatic handler discovery**: Scans directory for all .osi files
- **Symbol table hierarchy**: INIT.osi table becomes parent for handler tables
- **Reload capability**: Can reload INIT.osi when it changes
- **Error tolerance**: Continues working even if INIT.osi has errors
- **Validity tracking**: Tracks whether INIT.osi was successfully parsed
- **Global Initialization**: Marks symbols from INIT.osi as initialized by default.

**DirectoryContext**:
- Stores path, INIT.osi path, symbol table, and validity flag
- One per directory
- Created on-demand

**OSIProject**:
- Manages all directory contexts
- Provides access to directory scopes
- Handles INIT.osi reloading

**Workflow**:
1. File opened in directory
2. Get or create directory context
3. Load and parse INIT.osi if not already loaded
4. Scan for handler files
5. Build symbol table from INIT.osi
6. Return context with populated symbol table

**API**:
- `get_directory_context(file_path) -> DirectoryContext`
- `reload_init_file(dir_path)`

---

## Server Module

### `server.py`

**Purpose**: Main LSP server implementation.

**Key Classes**:
- `OSILanguageServer`: Extends `pygls.LanguageServer`

**Features**:

#### Core Functionality
- **Project management**: Maintains `OSIProject` instance
- **AST caching**: Caches parsed ASTs per document
- **Symbol table creation**: Creates hierarchical symbol tables with INIT.osi parent
- **Document parsing**: Three-phase processing (lex, parse, analyze) with error recovery
- **Validation**: Runs validator and publishes diagnostics
- **Error handling**: Converts exceptions to LSP diagnostics

#### LSP Protocol Handlers

**Text Synchronization**:
- `did_open`: Document opened
  - Validates document immediately
- `did_change`: Document changed
  - Detects INIT.osi changes and reloads directory context
  - Validates document
- `did_close`: Document closed
  - Removes AST from cache

**Language Features**:
- `completions`: Autocompletion (TEXT_DOCUMENT_COMPLETION)
  - Parses document
  - Populates symbol table
  - Uses `CompletionProvider`
  - Returns completion list

- `hover`: Hover information (TEXT_DOCUMENT_HOVER)
  - Parses document
  - Extracts word at position
  - Uses `HoverProvider`
  - Returns hover information

- `definition`: Go to Definition (TEXT_DOCUMENT_DEFINITION)
  - Parses document
  - Extracts word at position
  - Uses `DefinitionProvider`
  - Returns definition location

- `references`: Find References (TEXT_DOCUMENT_REFERENCES)
  - Parses document
  - Extracts word at position
  - Uses `DefinitionProvider`
  - Returns all reference locations

#### Utility Functions
- `get_word_at_position(line, character) -> str`: Extracts word at cursor
  - Handles special characters: `$`, `.`, `-`, `_`
  - Used by hover, definition, and references

#### Error Handling
- **Parse errors**: Converted to diagnostics at error position. Parser can return partial AST with errors.
- **Feature errors**: Logged but return safe defaults (empty/None)
- **INIT.osi errors**: Logged, validity flag set to false

#### Logging
- **Level**: INFO
- **Format**: Timestamp, logger name, level, message
- **Events logged**:
  - Document lifecycle (open, change, close)
  - Feature requests
  - Errors

**API**:
- `get_symbol_table(uri) -> SymbolTable`
- `parse_document(document) -> (AST, SymbolTable, List[ProtocolError])`
- `validate_document(uri, document)`
- LSP feature handlers (async)

---

## Module Interaction Flow

### Document Open
```
User opens file.osi
    ↓
did_open handler
    ↓
validate_document
    ├→ get_directory_context (OSIProject)
    │   ├→ load INIT.osi (if needed)
    │   ├→ Lexer → Parser → SemanticAnalyzer
    │   └→ Build directory symbol table
    ↓
parse_document
    ├→ get_symbol_table (with INIT parent)
    ├→ Lexer → tokenize
    ├→ Parser → parse → (AST, Errors)
    └→ Cache AST
    ↓
Validator.validate
    ├→ Structure checks
    ├→ SemanticAnalyzer.analyze
    └→ Usage checks
    ↓
Publish diagnostics (Parser errors + Semantic errors)
```

### Completion Request
```
User triggers completion
    ↓
completions handler
    ↓
parse_document
    ├→ Lexer → Parser → AST
    └→ get_symbol_table
    ↓
SemanticAnalyzer.analyze
    └→ Populate symbol table
    ↓
CompletionProvider.get_completions
    ├→ Context analysis
    ├→ Keyword suggestions
    └→ Symbol table symbols
    ↓
Return CompletionList
```

### Hover Request
```
User hovers over word
    ↓
hover handler
    ↓
parse_document + analyze
    ↓
get_word_at_position
    ↓
HoverProvider.get_hover
    ├→ Check if keyword → return keyword doc
    ├→ Check symbol table → return symbol info
    ├→ Check labels → return label info
    └→ Check subroutines → return subroutine info
    ↓
Return Hover with Markdown
```

### INIT.osi Change
```
User edits INIT.osi
    ↓
did_change handler
    ↓
Detect INIT.osi filename
    ↓
OSIProject.reload_init_file
    ├→ Clear directory symbol table
    └→ Re-parse INIT.osi
    ↓
validate_document
    └→ Use updated directory context
```

---

## Key Design Patterns

### 1. Visitor Pattern
- **Where**: AST traversal
- **Why**: Separates node structure from operations
- **Classes**: `ASTVisitor`, `SemanticAnalyzer`

### 2. Symbol Table Hierarchy
- **Where**: Scoping
- **Why**: INIT.osi symbols available to all handlers
- **Classes**: `SymbolTable` with parent

### 3. Provider Pattern
- **Where**: LSP features
- **Why**: Separation of concerns, testability
- **Classes**: `CompletionProvider`, `HoverProvider`, `DefinitionProvider`

### 4. Caching
- **Where**: AST storage, directory contexts
- **Why**: Performance, avoid re-parsing
- **Classes**: `OSILanguageServer`, `OSIProject`

### 5. Three-Phase Processing
- **Where**: Document parsing
- **Why**: Separation of concerns, clear error boundaries
- **Phases**: Lexing → Parsing → Semantic Analysis

---

## Performance Characteristics

### Time Complexity
- **Lexing**: O(n) where n = character count
- **Parsing**: O(n) where n = token count
- **Symbol table lookup**: O(1) for local, O(d) for parent chain (d = depth)
- **Completion**: O(s) where s = symbol count
- **Validation**: O(n) where n = AST node count

### Space Complexity
- **AST**: O(n) where n = statement count
- **Symbol Table**: O(s) where s = unique symbol count
- **Token List**: O(t) where t = token count
- **Directory Context Cache**: O(d) where d = directory count

### Optimization Strategies
- Comment tokens filtered early
- AST caching per document
- Directory context caching
- Lazy INIT.osi loading
- Parent symbol table reference (no copy)

---

## Error Handling Strategy

### Lexer Errors
- **Type**: Syntax errors (unterminated string, unknown character)
- **Action**: Raise `ProtocolError` immediately
- **Recovery**: None (stop lexing)

### Parser Errors
- **Type**: Syntax errors (unexpected token, missing token)
- **Action**: Raise `ProtocolError` which is caught by parse loop
- **Recovery**: Synchronization (skip to next line) and continue parsing

### Semantic Errors
- **Type**: Undeclared variables, duplicate declarations, type mismatches
- **Action**: Collect in list, continue analysis
- **Recovery**: Continue to find all errors

### Runtime Errors
- **Type**: File I/O errors, unexpected exceptions
- **Action**: Log error, return safe defaults
- **Recovery**: Continue server operation

### LSP Error Responses
- **Completion failure**: Return empty list
- **Hover failure**: Return None
- **Definition failure**: Return None
- **Parse failure**: Return diagnostic at error position

---

## Extension Points

### Adding a New LSP Feature
1. Create provider class in `providers/`
2. Add handler in `server.py` with `@server.feature` decorator
3. Call provider from handler
4. Handle errors gracefully

### Adding a New Validation Rule
1. Add check in `Validator._validate_structure()` or
2. Add check in `SemanticAnalyzer.visit_*()` method
3. Create diagnostic with appropriate severity

### Adding a New Symbol Type
1. Add to `SymbolType` enum
2. Add declaration/usage methods to `SymbolTable`
3. Update `SemanticAnalyzer` to track new type
4. Update providers to show new type

---

## Testing Infrastructure

### Test Files Location
```
server/tests/
├── test_lexer.py              # Tokenization tests
├── test_parser.py             # AST construction tests
├── test_validator.py          # Validation tests
├── test_symbol_table.py       # Symbol table tests
├── test_project.py            # Multi-file tests
└── test_lsp_features.py       # Integration tests
```

### Test Coverage Areas
- **Lexer**: All token types, error cases
- **Parser**: All statement types, expressions, precedence
- **Semantic Analysis**: All validation rules
- **Symbol Table**: All operations, scoping
- **Providers**: Completion, hover, definition generation
- **Project**: INIT.osi loading, reloading, handler discovery

---

## Dependencies

### External Libraries
- **pygls**: Language Server Protocol framework
- **lsprotocol**: LSP type definitions
- **Python 3.x**: Standard library (dataclasses, enum, typing, logging, pathlib)

### Internal Dependencies
```
server.py → all modules
workspace.project → parser, analysis
providers.* → analysis.symbol_table
analysis.validator → analysis.semantic_analyzer → analysis.symbol_table
analysis.semantic_analyzer → parser.ast_nodes
parser.parser → parser.lexer, parser.ast_nodes
parser.lexer → parser.errors
```

---

## Future Enhancements

### Planned Features
- **Project-wide reference tracking**: Find references across all files
- **Rename refactoring**: Rename symbols across project
- **Code actions**: Quick fixes for diagnostics
- **Document formatting**: Auto-formatting
- **Document symbols**: Outline view
- **Incremental parsing**: Parse only changed regions
- **Semantic tokens**: Enhanced syntax highlighting

### Architecture Improvements
- **Background validation**: Non-blocking validation
- **Persistent cache**: Save parsed ASTs to disk
- **Configurable rules**: User-defined validation rules
- **Plugin system**: Custom validators and providers

---

**Version**: 1.0
**Last Updated**: 2025-12-24
