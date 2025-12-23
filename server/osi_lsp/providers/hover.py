"""Hover provider for Protocol Language"""

from typing import Optional
from lsprotocol.types import Hover, MarkupContent, MarkupKind
from ..analysis.symbol_table import SymbolTable


class HoverProvider:
    """Provides hover information"""

    # Keyword documentation
    KEYWORDS_DOC = {
        'declare': '**declare** - Declare a variable\n\nSyntax: `name declare type`\n\nTypes: integer, buffer, string, queue',
        'varset': '**varset** - Assign value to variable\n\nSyntax: `expression varset $variable`',
        'goto': '**goto** - Unconditional jump\n\nSyntax: `goto label`',
        'if': '**if** - Conditional jump\n\nSyntax: `condition if label`',
        'return': '**return** - Return from handler\n\nSyntax: `return`',
        'bufferit': '**bufferit** - Create buffer\n\nSyntax: `buffer bufferit length field1 len1 field2 len2 ...`\n\nCreates a buffer with specified fields. Remaining space is filled with zeros.',
        'unbufferit': '**unbufferit** - Parse buffer\n\nSyntax: `unbufferit buffer var1 len1 var2 len2 ...`\n\nExtracts fields from buffer into variables.',
        'calccrc': '**calccrc** - Calculate CRC\n\nSyntax: `calccrc $result $buffer`\n\nCalculates CRC checksum of buffer.',
        'timer': '**timer** - Set timer\n\nSyntax: `EVENT timer $timer_var delay [param1 value1 ...]`\n\nSets a delayed event. Delay is in system time units.',
        'untimer': '**untimer** - Cancel timer\n\nSyntax: `untimer $timer_id`\n\nCancels all timers with the specified ID.',
        'queue': '**queue** - Add to queue\n\nSyntax: `queue_name queue value`\n\nAdds an element to the end of the queue.',
        'clearqueue': '**clearqueue** - Clear queue\n\nSyntax: `clearqueue queue_name`\n\nRemoves all elements from the queue.',
        'dequeue': '**dequeue** - Remove from queue\n\nSyntax: `dequeue(queue_name)`\n\nRemoves and returns the first element from the queue.',
        'peek': '**peek** - Peek at queue\n\nSyntax: `peek(queue_name)`\n\nReturns the first element without removing it.',
        'qcount': '**qcount** - Queue count\n\nSyntax: `qcount(queue_name)`\n\nReturns the number of elements in the queue.',
        'generateup': '**generateup** - Generate event up\n\nSyntax: `EVENT.NAME generateup [param1 value1 ...]`\n\nSends an event to the layer above.',
        'eventdown': '**eventdown** - Send event down\n\nSyntax: `EVENT.NAME eventdown [param1 value1 ...]`\n\nSends an event to the layer below.',
        'out': '**out** - Debug output\n\nSyntax: `out expression`\n\nOutputs a debug message.',
        'subprog': '**subprog** - Call subroutine\n\nSyntax: `subprog name`\n\nCalls a subroutine defined with substart/subend.',
        'substart': '**substart** - Start subroutine definition\n\nSyntax: `substart name ... subend`\n\nDefines a subroutine. Must end with `subend`.',
        'subend': '**subend** - End subroutine definition\n\nSyntax: `subend`\n\nEnds a subroutine definition.',
        'delete': '**delete** - Delete substring\n\nSyntax: `delete string start length`\n\nDeletes a substring from a string variable.',
        'sizeof': '**sizeof** - Get size\n\nSyntax: `sizeof($variable)`\n\nReturns the size of a variable (buffer or string).',
        'copy': '**copy** - Copy substring\n\nSyntax: `copy($string, start, length)`\n\nExtracts a substring.',
        'pos': '**pos** - Find substring\n\nSyntax: `pos($substring, $string)`\n\nFinds the position of a substring. Returns -1 if not found.',
    }

    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table

    def get_hover(self, word: str) -> Optional[Hover]:
        """Get hover information for a word"""
        if not word:
            return None

        # Remove $ prefix if present
        var_name = word[1:] if word.startswith('$') else word

        # Check if it's a keyword
        if var_name.lower() in self.KEYWORDS_DOC:
            content = self.KEYWORDS_DOC[var_name.lower()]
            return Hover(
                contents=MarkupContent(kind=MarkupKind.Markdown, value=content)
            )

        # Check if it's a variable
        symbol = self.symbol_table.get_symbol(var_name)
        if symbol:
            content = f"**Variable**: `${symbol.name}`\n\n"
            content += f"**Type**: `{symbol.symbol_type.value}`\n\n"
            content += f"**Declared at**: line {symbol.line + 1}, column {symbol.column + 1}\n\n"

            if symbol.initialized:
                content += "✓ Initialized\n\n"
            else:
                content += "⚠ Not initialized\n\n"

            if symbol.references:
                content += f"**References**: {len(symbol.references)} usage(s)"

            return Hover(
                contents=MarkupContent(kind=MarkupKind.Markdown, value=content)
            )

        # Check if it's a label
        label = self.symbol_table.get_label(var_name)
        if label:
            content = f"**Label**: `{label.name}:`\n\n"
            content += f"**Defined at**: line {label.line + 1}, column {label.column + 1}\n\n"

            if label.references:
                content += f"**References**: {len(label.references)} jump(s)"

            return Hover(
                contents=MarkupContent(kind=MarkupKind.Markdown, value=content)
            )

        # Check if it's a subroutine
        subroutine = self.symbol_table.get_subroutine(var_name)
        if subroutine:
            content = f"**Subroutine**: `{subroutine.name}`\n\n"
            content += f"**Defined at**: line {subroutine.line + 1}, column {subroutine.column + 1}\n\n"

            if subroutine.references:
                content += f"**Called**: {len(subroutine.references)} time(s)"

            return Hover(
                contents=MarkupContent(kind=MarkupKind.Markdown, value=content)
            )

        # Check if it's a handler
        handler = self.symbol_table.get_handler(var_name)
        if handler:
            content = f"**Event Handler**: `## {handler.name}`\n\n"
            content += f"**Defined at**: line {handler.line + 1}, column {handler.column + 1}"

            if handler.parameters:
                content += f"\n\n**Parameters**: {', '.join(handler.parameters)}"

            return Hover(
                contents=MarkupContent(kind=MarkupKind.Markdown, value=content)
            )

        return None
