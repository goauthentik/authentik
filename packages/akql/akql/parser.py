import re
from decimal import Decimal
from typing import Any

from ply import yacc
from ply.yacc import LRParser, YaccProduction

from akql.ast import Comparison, Const, Expression, List, Logical, Name, Variable
from akql.exceptions import AKQLParserError
from akql.lexer import AKQLLexer

unescape_pattern = re.compile(
    "(" + AKQLLexer.re_escaped_char + "|" + AKQLLexer.re_escaped_unicode + ")",
)


def unescape_repl(m):
    contents = m.group(1)
    if len(contents) == 2:
        return contents[1]
    else:
        return contents.encode("utf8").decode("unicode_escape")


def unescape(value):
    if isinstance(value, bytes):
        value = value.decode("utf8")
    return re.sub(unescape_pattern, unescape_repl, value)


class AKQLParser:
    yacc: LRParser
    context: dict[str, Any]

    def __init__(self, debug=False, context: dict[str, Any] | None = None, **kwargs):
        self.default_lexer = AKQLLexer()
        self.tokens = self.default_lexer.tokens
        kwargs["debug"] = debug
        if "write_tables" not in kwargs:
            kwargs["write_tables"] = False
        self.context = context or {}
        self.yacc = yacc.yacc(module=self, **kwargs)

    def parse(
        self, input=None, lexer: AKQLLexer | None = None, **kwargs
    ) -> Expression:  # noqa: A002
        lexer = lexer or self.default_lexer
        return self.yacc.parse(input=input, lexer=lexer, **kwargs)

    start = "expression"

    def p_expression_parens(self, p: YaccProduction):
        """
        expression : PAREN_L expression PAREN_R
        """
        p[0] = p[2]

    def p_expression_logical(self, p: YaccProduction):
        """
        expression : expression logical expression
        """
        p[0] = Expression(left=p[1], operator=p[2], right=p[3])

    def p_expression_comparison(self, p: YaccProduction):
        """
        expression : name comparison_number number
                   | name comparison_string string
                   | name comparison_equality boolean_value
                   | name comparison_equality none
                   | name comparison_in_list const_list_value
                   | name comparison_number variable
                   | name comparison_string variable
                   | name comparison_equality variable
                   | name comparison_in_list variable
        """
        p[0] = Expression(left=p[1], operator=p[2], right=p[3])

    def p_name(self, p: YaccProduction):
        """
        name : NAME
        """
        p[0] = Name(parts=p[1].split("."))

    def p_logical(self, p: YaccProduction):
        """
        logical : AND
                | OR
        """
        p[0] = Logical(operator=p[1])

    def p_comparison_number(self, p: YaccProduction):
        """
        comparison_number : comparison_equality
                          | comparison_greater_less
        """
        p[0] = p[1]

    def p_comparison_string(self, p: YaccProduction):
        """
        comparison_string : comparison_equality
                          | comparison_greater_less
                          | comparison_string_specific
        """
        p[0] = p[1]

    def p_comparison_equality(self, p: YaccProduction):
        """
        comparison_equality : EQUALS
                            | NOT_EQUALS
        """
        p[0] = Comparison(operator=p[1])

    def p_comparison_greater_less(self, p: YaccProduction):
        """
        comparison_greater_less : GREATER
                                | GREATER_EQUAL
                                | LESS
                                | LESS_EQUAL
        """
        p[0] = Comparison(operator=p[1])

    def p_comparison_string_specific(self, p: YaccProduction):
        """
        comparison_string_specific : CONTAINS
                                   | NOT_CONTAINS
                                   | STARTSWITH
                                   | NOT STARTSWITH
                                   | ENDSWITH
                                   | NOT ENDSWITH
        """
        if len(p) == 2:
            p[0] = Comparison(operator=p[1])
        else:
            p[0] = Comparison(operator=f"{p[1]} {p[2]}")

    def p_comparison_in_list(self, p: YaccProduction):
        """
        comparison_in_list : IN
                           | NOT IN
        """
        if len(p) == 2:
            p[0] = Comparison(operator=p[1])
        else:
            p[0] = Comparison(operator=f"{p[1]} {p[2]}")

    def p_const_value(self, p: YaccProduction):
        """
        const_value : number
                    | string
                    | none
                    | boolean_value
        """
        p[0] = p[1]

    def p_variable(self, p: YaccProduction):
        """
        variable : VARIABLE
        """
        p[0] = Variable(name=unescape(p[1]), parser=self)

    def p_number_int(self, p: YaccProduction):
        """
        number : INT_VALUE
        """
        p[0] = Const(value=int(p[1]))

    def p_number_float(self, p: YaccProduction):
        """
        number : FLOAT_VALUE
        """
        p[0] = Const(value=Decimal(p[1]))

    def p_string(self, p: YaccProduction):
        """
        string : STRING_VALUE
        """
        p[0] = Const(value=unescape(p[1]))

    def p_none(self, p: YaccProduction):
        """
        none : NONE
        """
        p[0] = Const(value=None)

    def p_boolean_value(self, p: YaccProduction):
        """
        boolean_value : true
                      | false
        """
        p[0] = p[1]

    def p_true(self, p: YaccProduction):
        """
        true : TRUE
        """
        p[0] = Const(value=True)

    def p_false(self, p: YaccProduction):
        """
        false : FALSE
        """
        p[0] = Const(value=False)

    def p_const_list_value(self, p: YaccProduction):
        """
        const_list_value : PAREN_L const_value_list PAREN_R
        """
        p[0] = List(items=p[2])

    def p_const_value_list(self, p: YaccProduction):
        """
        const_value_list : const_value_list COMMA const_value
        """
        p[0] = p[1] + [p[3]]

    def p_const_value_list_single(self, p: YaccProduction):
        """
        const_value_list : const_value
        """
        p[0] = [p[1]]

    def p_error(self, token):
        if token is None:
            self.raise_syntax_error("Unexpected end of input")
        else:
            fragment = str(token.value)
            if len(fragment) > 20:
                fragment = fragment[:17] + "..."
            self.raise_syntax_error(
                f"Syntax error at {repr(fragment)}",
                token=token,
            )

    def raise_syntax_error(self, message, token=None):
        if token is None:
            raise AKQLParserError(message)
        lexer = token.lexer
        if callable(getattr(lexer, "find_column", None)):
            column = lexer.find_column(token)
        else:
            column = None
        raise AKQLParserError(
            message=message,
            value=token.value,
            line=token.lineno,
            column=column,
        )
