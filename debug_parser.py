import sys
import os

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from osi_lsp.parser.lexer import Lexer
from osi_lsp.parser.parser import Parser
from osi_lsp.parser.errors import ProtocolError

def debug_parse(text):
    print("--- Lexing ---")
    lexer = Lexer(text)
    try:
        tokens = lexer.tokenize()
        for t in tokens:
            print(t)
    except Exception as e:
        print(f"Lexer error: {e}")
        return

    print("\n--- Parsing ---")
    parser = Parser(tokens)
    try:
        ast = parser.parse()
        print("Parsing successful!")
        # print(ast) # AST might be large
    except ProtocolError as e:
        print(f"Parser ProtocolError: {e}")
        # Print token context if possible
        if parser.current_token:
            print(f"Current token: {parser.current_token}")
    except Exception as e:
        print(f"Parser Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "test_timer.protocol"
        
    print(f"Parsing {filename}...")
    try:
        with open(filename, "r") as f:
            text = f.read()
        debug_parse(text)
    except FileNotFoundError:
        print(f"File {filename} not found.")
