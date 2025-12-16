from django.test import TestCase

from akql.ast import Comparison, Const, Expression, Name, Variable
from akql.parser import AKQLParser


class TestParser(TestCase):

    def test_parser_simple(self):
        ast = AKQLParser().parse('foo = "bar"')
        self.assertEqual(
            ast,
            Expression(
                left=Name(parts=["foo"]),
                operator=Comparison(operator="="),
                right=Const(value="bar"),
            ),
        )

    def test_parser_not_startswith(self):
        ast = AKQLParser().parse('foo not startswith "bar"')
        self.assertEqual(
            ast,
            Expression(
                left=Name(parts=["foo"]),
                operator=Comparison(operator="not startswith"),
                right=Const(value="bar"),
            ),
        )

    def test_parser_variable(self):
        parser = AKQLParser()
        ast = parser.parse("foo = $bar")
        self.assertEqual(
            ast,
            Expression(
                left=Name(parts=["foo"]),
                operator=Comparison(operator="="),
                right=Variable(name="$bar", parser=parser),
            ),
        )
