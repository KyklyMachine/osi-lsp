# Protocol Language Server

Language Server Protocol (LSP) implementation for the Protocol Language - a specialized language for describing network protocols (transport, session, presentation, and application layers).

## Features

✅ **Syntax Highlighting** - Full syntax highlighting for Protocol Language
✅ **Diagnostics** - Real-time error detection and warnings
✅ **Auto-completion** - Context-aware code completion
✅ **Hover Information** - Documentation and type information on hover
✅ **Go to Definition** - Navigate to variable, label, and subroutine definitions
✅ **Find References** - Find all usages of symbols
✅ **Semantic Analysis** - Type checking and unused symbol detection

## Language Overview

### Structure

Code is organized into event handlers:

```protocol
## HANDLER_NAME
```
code here
```
```

### Data Types

- `integer` - Integer numbers
- `buffer` - Byte buffers
- `string` - Text strings
- `queue` - Queues

### Example

```protocol
## EXAMPLE_HANDLER
```
counter declare integer
0 varset counter

$counter + 1 varset counter
$counter > 10 if overflow

out "Counter: " $counter
return

overflow:
    out "Overflow!"
    0 varset counter
    return
```
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- VS Code 1.75 or higher

### Step 1: Install Python Dependencies

```bash
cd server
python -m venv venv

# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

### Step 2: Install Node Dependencies

```bash
cd client
npm install
```

### Step 3: Compile TypeScript

```bash
cd client
npm run compile
```

### Step 4: Install the Extension

#### Option A: Development Mode

1. Open the project folder in VS Code
2. Press F5 to launch Extension Development Host
3. In the new window, open a `.protocol` file

#### Option B: Package and Install

```bash
# Install vsce (VS Code Extension Manager)
npm install -g @vscode/vsce

# Package the extension
cd client
vsce package

# Install the .vsix file
code --install-extension protocol-language-0.1.0.vsix
```

## Usage

1. Create a file with `.protocol` or `.prot` extension
2. Start writing your protocol code
3. The language server will automatically:
   - Highlight syntax
   - Show errors and warnings
   - Provide auto-completion
   - Enable navigation features

### Keyboard Shortcuts

- `Ctrl+Space` - Trigger auto-completion
- `F12` - Go to definition
- `Shift+F12` - Find all references
- Hover over a symbol to see documentation

## Language Features

### Variables

Declare and use variables:

```protocol
counter declare integer
0 varset counter
$counter + 1 varset counter
```

### Control Flow

```protocol
goto label_name
condition if label_name
return

label_name:
    ; code here
```

### Buffers

Create and parse buffers:

```protocol
buffer declare buffer
buffer bufferit 10 value1 2 value2 3
unbufferit buffer var1 2 var2 3
```

### Timers

```protocol
EVENT timer timer_var 1000 param1 value1
untimer $timer_var
```

### Queues

```protocol
queue_name declare queue
queue queue_name $value
dequeue(queue_name) varset first
peek(queue_name) varset first
qcount(queue_name) varset size
clearqueue queue_name
```

### Events

```protocol
EVENT.NAME generateup param1 value1
EVENT.NAME eventdown param2 value2
```

### Subroutines

```protocol
subprog subroutine_name

return  ; Stop execution before subroutine definitions

substart subroutine_name
    ; code here
subend
```

## Configuration

Configure the extension in VS Code settings:

```json
{
  "protocolLanguageServer.pythonPath": "python",
  "protocolLanguageServer.trace.server": "off"
}
```

## Development

### Project Structure

```
protocol-language-server/
├── client/                     # VS Code Extension
│   ├── src/
│   │   └── extension.ts       # Extension entry point
│   ├── package.json
│   └── tsconfig.json
│
├── server/                     # Language Server (Python)
│   ├── protocol_ls/
│   │   ├── parser/            # Lexer and Parser
│   │   ├── analysis/          # Semantic analysis
│   │   ├── providers/         # LSP providers
│   │   └── server.py          # Main server
│   └── requirements.txt
│
├── syntaxes/                   # TextMate grammar
│   └── protocol.tmLanguage.json
│
└── examples/                   # Example code
```

### Running in Development Mode

1. Install dependencies (see Installation)
2. Open the project in VS Code
3. Press F5 to start debugging
4. A new VS Code window will open with the extension loaded

### Running Tests

```bash
# Run Python tests
cd server
python -m pytest

# Run TypeScript tests
cd client
npm test
```

### Logging

To enable detailed logging:

1. Set `"protocolLanguageServer.trace.server": "verbose"` in VS Code settings
2. Open the Output panel (View → Output)
3. Select "Protocol Language Server" from the dropdown

## Troubleshooting

### Extension doesn't activate

- Check that Python is installed and in PATH
- Verify the server files exist in `server/protocol_ls/`
- Check the Output panel for error messages

### Auto-completion not working

- Ensure the file has `.protocol` or `.prot` extension
- Try reloading the window (Ctrl+Shift+P → "Developer: Reload Window")

### Syntax highlighting not working

- Verify the TextMate grammar file exists at `syntaxes/protocol.tmLanguage.json`
- Check that the language is recognized (bottom-right corner of VS Code)

## Language Reference

### Keywords

- `declare` - Variable declaration
- `varset` - Assignment
- `goto` - Unconditional jump
- `if` - Conditional jump
- `return` - Return from handler

### Operators

- `bufferit` - Create buffer
- `unbufferit` - Parse buffer
- `calccrc` - Calculate CRC
- `timer` - Set timer
- `untimer` - Cancel timer
- `queue` - Add to queue
- `clearqueue` - Clear queue
- `dequeue` - Remove from queue
- `peek` - Peek at queue
- `qcount` - Queue count
- `generateup` - Generate event up
- `eventdown` - Send event down
- `out` - Debug output
- `subprog` - Call subroutine
- `substart` - Start subroutine definition
- `subend` - End subroutine definition
- `delete` - Delete substring

### Functions

- `sizeof(var)` - Get size of buffer/string
- `copy(str, start, len)` - Copy substring
- `pos(substr, str)` - Find substring position
- `locguide(str)` - Location guide
- `CurrentSystemName()` - Get system name

### Operators

- Arithmetic: `+`, `-`, `*`, `/`, `%`
- Comparison: `==`, `!=`, `>`, `<`, `>=`, `<=`
- Logical: `&&`, `||`

## Examples

See the `examples/` directory for complete examples:

- `simple_counter.protocol` - Basic variable usage and control flow
- `protocol_example.protocol` - Network protocol with buffers and timers
- `queue_example.protocol` - Queue operations

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built with [pygls](https://github.com/openlawlibrary/pygls) - Python LSP library
- VS Code extension based on [vscode-languageclient](https://www.npmjs.com/package/vscode-languageclient)

## Support

For issues, questions, or suggestions:

- Open an issue on GitHub
- Check existing issues for solutions
- Review the examples directory

## Roadmap

### Current Version (0.1.0)

- ✅ Basic syntax highlighting
- ✅ Error detection
- ✅ Auto-completion
- ✅ Hover information
- ✅ Go to definition
- ✅ Find references

### Future Features

- [ ] Code formatting
- [ ] Refactoring (rename, extract)
- [ ] Snippets
- [ ] Debugger integration
- [ ] Code folding
- [ ] Semantic highlighting
- [ ] Documentation generation
- [ ] Test framework
