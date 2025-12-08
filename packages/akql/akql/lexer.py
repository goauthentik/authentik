from __future__ import unicode_literals

import ply.lex as lex
from ply.lex import TOKEN

from .exceptions import DjangoQLLexerError


class DjangoQLLexer(object):
    def __init__(self, **kwargs):
        self._lexer = lex.lex(module=self, **kwargs)
        self.reset()

    def reset(self):
        self.text = ''
        self._lexer.lineno = 1
        return self

    def input(self, s):
        self.reset()
        self.text = s
        self._lexer.input(s)
        return self

    def token(self):
        return self._lexer.token()

    # Iterator interface
    def __iter__(self):
        return self

    def next(self):
        t = self.token()
        if t is None:
            raise StopIteration
        return t

    __next__ = next

    def find_column(self, t):
        """
        Returns token position in current text, starting from 1
        """
        cr = max(
            self.text.rfind(lt, 0, t.lexpos) for lt in self.line_terminators
        )
        if cr == -1:
            return t.lexpos + 1
        return t.lexpos - cr

    whitespace = ' \t\v\f\u00A0'
    line_terminators = '\n\r\u2028\u2029'

    re_line_terminators = r'\n\r\u2028\u2029'

    re_escaped_char = r'\\[\"\\/bfnrt]'
    re_escaped_unicode = r'\\u[0-9A-Fa-f]{4}'
    re_string_char = r'[^\"\\' + re_line_terminators + u']'

    re_int_value = r'(-?0|-?[1-9][0-9]*)'
    re_fraction_part = r'\.[0-9]+'
    re_exponent_part = r'[eE][\+-]?[0-9]+'

    tokens = [
        'COMMA',
        'OR',
        'AND',
        'NOT',
        'IN',
        'TRUE',
        'FALSE',
        'NONE',
        'NAME',
        'STRING_VALUE',
        'FLOAT_VALUE',
        'INT_VALUE',
        'PAREN_L',
        'PAREN_R',
        'EQUALS',
        'NOT_EQUALS',
        'GREATER',
        'GREATER_EQUAL',
        'LESS',
        'LESS_EQUAL',
        'CONTAINS',
        'NOT_CONTAINS',
        'STARTSWITH',
        'ENDSWITH',
    ]

    t_COMMA = ','
    t_PAREN_L = r'\('
    t_PAREN_R = r'\)'
    t_EQUALS = '='
    t_NOT_EQUALS = '!='
    t_GREATER = '>'
    t_GREATER_EQUAL = '>='
    t_LESS = '<'
    t_LESS_EQUAL = '<='
    t_CONTAINS = '~'
    t_NOT_CONTAINS = '!~'

    t_NAME = r'[_A-Za-z][_0-9A-Za-z]*(\.[_A-Za-z][_0-9A-Za-z]*)*'

    t_ignore = whitespace

    @TOKEN(r'\"(' + re_escaped_char +
           '|' + re_escaped_unicode +
           '|' + re_string_char + r')*\"')
    def t_STRING_VALUE(self, t):
        t.value = t.value[1:-1]  # cut leading and trailing quotes ""
        return t

    @TOKEN(re_int_value + re_fraction_part + re_exponent_part + '|' +
           re_int_value + re_fraction_part + '|' +
           re_int_value + re_exponent_part)
    def t_FLOAT_VALUE(self, t):
        return t

    @TOKEN(re_int_value)
    def t_INT_VALUE(self, t):
        return t

    not_followed_by_name = '(?![_0-9A-Za-z])'

    @TOKEN('or' + not_followed_by_name)
    def t_OR(self, t):
        return t

    @TOKEN('and' + not_followed_by_name)
    def t_AND(self, t):
        return t

    @TOKEN('not' + not_followed_by_name)
    def t_NOT(self, t):
        return t

    @TOKEN('in' + not_followed_by_name)
    def t_IN(self, t):
        return t

    @TOKEN('startswith' + not_followed_by_name)
    def t_STARTSWITH(self, t):
        return t

    @TOKEN('endswith' + not_followed_by_name)
    def t_ENDSWITH(self, t):
        return t

    @TOKEN('True' + not_followed_by_name)
    def t_TRUE(self, t):
        return t

    @TOKEN('False' + not_followed_by_name)
    def t_FALSE(self, t):
        return t

    @TOKEN('None' + not_followed_by_name)
    def t_NONE(self, t):
        return t

    def t_error(self, t):
        raise DjangoQLLexerError(
            message='Illegal character %s' % repr(t.value[0]),
            value=t.value,
            line=t.lineno,
            column=self.find_column(t),
        )

    @TOKEN('[' + re_line_terminators + ']+')
    def t_newline(self, t):
        t.lexer.lineno += len(t.value)
        return
