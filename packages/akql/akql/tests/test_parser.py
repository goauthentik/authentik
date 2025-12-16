from django.test import TestCase

from akql.ast import Comparison, Const, Expression, Name, Variable
from akql.parser import DjangoQLParser


class TestParser(TestCase):

    def test_parser_simple(self):
        ast = DjangoQLParser().parse('foo = "bar"')
        self.assertEqual(
            ast,
            Expression(
                left=Name(parts=["foo"]),
                operator=Comparison(operator="="),
                right=Const(value="bar"),
            ),
        )

    def test_parser_variable(self):
        parser = DjangoQLParser()
        ast = parser.parse("foo = $bar")
        self.assertEqual(
            ast,
            Expression(
                left=Name(parts=["foo"]),
                operator=Comparison(operator="="),
                right=Variable(name="$bar", parser=parser),
            ),
        )
