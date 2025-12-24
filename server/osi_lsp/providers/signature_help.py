"""Signature Help provider for Protocol Language"""

from typing import Optional, List, Dict
from lsprotocol.types import (
    SignatureHelp,
    SignatureInformation,
    ParameterInformation,
    MarkupContent,
    MarkupKind
)
from ..parser.lexer import Lexer, TokenType

class SignatureHelpProvider:
    """Provides signature help for functions"""

    # Define signatures for built-in functions
    SIGNATURES = {
        'bufferit': SignatureInformation(
            label='bufferit buffer total_length field1 len1 [field2 len2 ...]',
            documentation='Create a buffer with specified fields. Remaining space is filled with zeros.',
            parameters=[
                ParameterInformation(label='buffer', documentation='Name of the buffer variable'),
                ParameterInformation(label='total_length', documentation='Total length of the buffer in bytes'),
                ParameterInformation(label='field1', documentation='First value to put in buffer'),
                ParameterInformation(label='len1', documentation='Length of first value'),
                ParameterInformation(label='...', documentation='Additional value/length pairs'),
            ]
        ),
        'unbufferit': SignatureInformation(
            label='unbufferit buffer var1 len1 [var2 len2 ...]',
            documentation='Parse buffer into variables.',
            parameters=[
                ParameterInformation(label='buffer', documentation='Buffer variable to read from'),
                ParameterInformation(label='var1', documentation='Variable to store first field'),
                ParameterInformation(label='len1', documentation='Length to read for first field'),
                ParameterInformation(label='...', documentation='Additional variable/length pairs'),
            ]
        ),
        'timer': SignatureInformation(
            label='timer timer_var delay [param1 value1 ...]',
            documentation='Set a delayed event. Syntax: EVENT_NAME timer ...',
            parameters=[
                ParameterInformation(label='timer_var', documentation='Timer ID variable'),
                ParameterInformation(label='delay', documentation='Delay in system time units'),
                ParameterInformation(label='...', documentation='Optional parameters for the event'),
            ]
        ),
        'delete': SignatureInformation(
            label='delete string start length',
            documentation='Delete a substring from a string variable.',
            parameters=[
                ParameterInformation(label='string', documentation='String variable to modify'),
                ParameterInformation(label='start', documentation='Start position (1-based)'),
                ParameterInformation(label='length', documentation='Number of characters to delete'),
            ]
        ),
        'copy': SignatureInformation(
            label='copy(string, start, length)',
            documentation='Extract a substring.',
            parameters=[
                ParameterInformation(label='string', documentation='Source string'),
                ParameterInformation(label='start', documentation='Start position (1-based)'),
                ParameterInformation(label='length', documentation='Length to copy'),
            ]
        ),
        'pos': SignatureInformation(
            label='pos(substring, string)',
            documentation='Find position of substring.',
            parameters=[
                ParameterInformation(label='substring', documentation='Substring to find'),
                ParameterInformation(label='string', documentation='String to search in'),
            ]
        ),
        'sizeof': SignatureInformation(
            label='sizeof(variable)',
            documentation='Get size of variable.',
            parameters=[
                ParameterInformation(label='variable', documentation='Variable to measure'),
            ]
        ),
        'qcount': SignatureInformation(
            label='qcount(queue)',
            documentation='Get number of elements in queue.',
            parameters=[
                ParameterInformation(label='queue', documentation='Queue variable'),
            ]
        ),
        'peek': SignatureInformation(
            label='peek(queue)',
            documentation='Peek at first element of queue.',
            parameters=[
                ParameterInformation(label='queue', documentation='Queue variable'),
            ]
        ),
        'dequeue': SignatureInformation(
            label='dequeue(queue)',
            documentation='Remove and return first element from queue.',
            parameters=[
                ParameterInformation(label='queue', documentation='Queue variable'),
            ]
        ),
        'calccrc': SignatureInformation(
            label='calccrc result buffer',
            documentation='Calculate CRC checksum.',
            parameters=[
                ParameterInformation(label='result', documentation='Variable to store result'),
                ParameterInformation(label='buffer', documentation='Buffer to calculate CRC for'),
            ]
        ),
         'out': SignatureInformation(
            label='out expression',
            documentation='Output debug message.',
            parameters=[
                ParameterInformation(label='expression', documentation='Value to output'),
            ]
        ),
         'queue': SignatureInformation(
            label='queue queue_name value',
            documentation='Add value to queue.',
            parameters=[
                ParameterInformation(label='queue_name', documentation='Target queue'),
                ParameterInformation(label='value', documentation='Value to add'),
            ]
        ),
    }

    def get_signature_help(self, line: str, character: int) -> Optional[SignatureHelp]:
        """
        Determine the active function signature and parameter index.
        """
        # Truncate line to cursor position
        context = line[:character]
        
        # We need to find the "active" function call.
        # Simple approach: Tokenize backwards or find closest function keyword/identifier
        
        # Tokenize the line context
        try:
            lexer = Lexer(context)
            tokens = lexer.tokenize()
        except Exception:
            # If lexing fails (e.g. unterminated string), we might bail out
            return None

        if not tokens:
            return None

        # Filter out EOF and Newline
        tokens = [t for t in tokens if t.type not in (TokenType.EOF, TokenType.NEWLINE)]
        if not tokens:
            return None

        # Iterate backwards to find the function call we are in
        # We need to count commas to find parameter index
        # We also need to respect parentheses for functions like copy() vs keywords like bufferit
        
        param_index = 0
        paren_depth = 0
        found_func = None
        
        for i in range(len(tokens) - 1, -1, -1):
            token = tokens[i]
            
            if token.type == TokenType.RPAREN:
                paren_depth += 1
            elif token.type == TokenType.LPAREN:
                if paren_depth > 0:
                    paren_depth -= 1
                else:
                    # We found the start of a function call like func(
                    # The previous token should be the function name
                    if i > 0:
                        prev = tokens[i-1]
                        if prev.value in self.SIGNATURES:
                            found_func = prev.value
                            break
            elif token.type == TokenType.COMMA:
                if paren_depth == 0:
                    param_index += 1
            
            # Check for keyword-style functions (bufferit, timer, etc.)
            # These don't use parentheses (usually), they just list args
            # But wait, how do we know where the args start?
            # Usually strict syntax: "bufferit buf len ..."
            # If we hit a keyword that starts a statement, that's likely our function
            if paren_depth == 0:
                if token.value in self.SIGNATURES:
                     # Check if it's really the start of the statement or expression
                     # For simplicity, if we find a known function keyword and we are "to the right" of it, assume it's the one.
                     # But we must be careful about nested calls.
                     # e.g. "out sizeof(buf)" -> cursor inside sizeof -> found_func should be sizeof
                     # "out sizeof(buf) + 1" -> cursor at end -> found_func should be out? 
                     # Actually OSI usually has one statement per line.
                     # Expressions can be nested.
                     
                     # Since we iterate backwards:
                     # "out sizeof(buf" -> cursor after '('. 
                     # 1. '(' -> depth 0 -> match LPAREN block above. found sizeof. Done.
                     
                     # "bufferit buf 10" -> cursor at end.
                     # tokens: bufferit, buf, 10
                     # reverse: 10, buf, bufferit
                     # no parens.
                     # hit bufferit. It's in signatures. 
                     # param_index is count of "separators"? 
                     # For keyword statements, separators are spaces (which are gone in tokens)
                     # So every token is a parameter.
                     
                     # We need to count how many tokens are between the function keyword and cursor.
                     # tokens[i] is the function keyword.
                     # tokens[i+1 ... end] are parameters.
                     # We need to count expressions.
                     # But since we just have a list of tokens, we can approximate:
                     # param_index = (len(tokens) - 1) - i
                     # But commas? Keyword funcs usually don't use commas. 
                     # Wait, spec says:
                     # "bufferit buffer length field1 len1 ..." - space separated?
                     # "copy(str, start, len)" - comma separated.
                     
                     # Let's distinguish paren-based vs space-based.
                     if self._is_paren_function(token.value):
                         # If we hit the name but didn't hit an LPAREN yet (reverse), 
                         # it means we are like "copy|" -> not inside args yet.
                         pass 
                     else:
                         found_func = token.value
                         # Count tokens after this one as params
                         # But we need to exclude commas if they exist (though usually they don't for these)
                         # Actually, let's just count significant tokens.
                         # And we need to subtract 1 because index 0 is the first param.
                         # tokens after func: len(tokens) - 1 - i
                         # But wait, if we are typing the 2nd param, we have func, param1. 
                         # current token is param1? Or we are typing param2?
                         # The context includes text up to cursor.
                         # If cursor is after "bufferit buf ", tokens are [bufferit, buf].
                         # We are about to type param 2.
                         # param_index should be 1.
                         # (len - 1) - i = (2 - 1) - 0 = 1. Correct.
                         
                         param_index = 0
                         # Recalculate param index based on tokens to the right
                         # We need to handle expressions properly (e.g. 1 + 2 is one param)
                         # This is hard without full parsing.
                         # Approximation: just count tokens for now? 
                         # Or better: count commas for paren funcs, count tokens for others.
                         # For keyword funcs, 1+2 might be parsed as 3 tokens.
                         # "out 1 + 2" -> out (1+2). 
                         # If we count tokens: out, 1, +, 2. 3 params? No.
                         
                         # Since this is a simple implementation, let's stick to simple token counting 
                         # but maybe ignore operators? 
                         # It's tricky.
                         # Let's just use the simple logic: 
                         # For paren functions: strictly rely on commas inside parens.
                         # For keyword functions: rely on whitespace/tokens, maybe just raw token count is "good enough" for simple args.
                         
                         # Refined logic for keyword functions:
                         # Calculate param_index by counting tokens to the right of found function.
                         # But simplistic counting is flawed for expressions.
                         # However, for bufferit/unbufferit, args are usually simple vars or literals.
                         
                         current_tokens_count = len(tokens) - 1 - i
                         param_index = current_tokens_count
                         break

        if found_func:
            sig_info = self.SIGNATURES[found_func]
            
            # Handle variable arguments (ellipsis)
            # If param_index exceeds declared params, clamp it if the last one is ...
            # Actually, we can just highlight the last parameter if it's varargs
            if param_index >= len(sig_info.parameters):
                 # Check if last param is generic (like "...")
                 last_param = sig_info.parameters[-1]
                 if last_param.label == '...':
                     param_index = len(sig_info.parameters) - 1
                 else:
                     # Index out of bounds, maybe show nothing or last one
                     param_index = len(sig_info.parameters) - 1

            return SignatureHelp(
                signatures=[sig_info],
                active_signature=0,
                active_parameter=param_index
            )
            
        return None

    def _is_paren_function(self, name: str) -> bool:
        # Functions that use parentheses
        return name in ('copy', 'pos', 'sizeof', 'qcount', 'peek', 'dequeue', 'locguide', 'CurrentSystemName')

