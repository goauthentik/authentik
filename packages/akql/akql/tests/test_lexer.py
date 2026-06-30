from django.test import TestCase

from akql.lexer import AKQLLexer


class TestLexer(TestCase):

    def test_lexer_simple(self):
        lexer = AKQLLexer().input('foo = "bar"')
        tokens = list(str(t) for t in lexer)
        self.assertEqual(
            tokens,
            [
                "LexToken(NAME,'foo',1,0)",
                "LexToken(EQUALS,'=',1,4)",
                "LexToken(STRING_VALUE,'bar',1,6)",
            ],
        )
