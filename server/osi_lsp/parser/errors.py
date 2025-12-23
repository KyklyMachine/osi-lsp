class ProtocolError(Exception):
    """Exception raised for errors in the Protocol Language parser/lexer."""
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"{line}:{column}: {message}")
