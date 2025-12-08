class DjangoQLError(Exception):
    def __init__(self, message=None, value=None, line=None, column=None):
        self.value = value
        self.line = line
        self.column = column
        super().__init__(message)

    def __str__(self):
        message = super().__str__()
        if self.line:
            position_info = f"Line {self.line}"
            if self.column:
                position_info += f", col {self.column}"
            return f"{position_info}: {message}"
        else:
            return message


class DjangoQLSyntaxError(DjangoQLError):
    pass


class DjangoQLLexerError(DjangoQLSyntaxError):
    pass


class DjangoQLParserError(DjangoQLSyntaxError):
    pass


class DjangoQLSchemaError(DjangoQLError):
    pass
