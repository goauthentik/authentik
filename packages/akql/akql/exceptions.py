class DjangoQLError(Exception):
    def __init__(self, message=None, value=None, line=None, column=None):
        self.value = value
        self.line = line
        self.column = column
        super(DjangoQLError, self).__init__(message)

    def __str__(self):
        message = super(DjangoQLError, self).__str__()
        if self.line:
            position_info = 'Line %s' % self.line
            if self.column:
                position_info += ', col %s' % self.column
            return '%s: %s' % (position_info, message)
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
