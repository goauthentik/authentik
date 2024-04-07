from antlr4 import CommonTokenStream, InputStream, ParseTreeWalker
from django.db.models import Q
from rest_framework.test import APITestCase

from authentik.sources.scim.filters.django import DjangoQueryListener
from authentik.sources.scim.filters.ScimFilterLexer import ScimFilterLexer
from authentik.sources.scim.filters.ScimFilterParser import ScimFilterParser


class TestSCIMFilter(APITestCase):

    def test_filter_parse(self):
        filters = [
            ('emails[type eq "work" and value ew "example.com"]', Q()),
        ]
        for filter, expected in filters:
            with self.subTest(filter=filter, expected=expected):
                lexer = ScimFilterLexer(InputStream(filter))
                stream = CommonTokenStream(lexer)
                parser = ScimFilterParser(stream)
                tree = parser.filter_()
                listener = DjangoQueryListener()
                walker = ParseTreeWalker()
                walker.walk(listener, tree)
                print(listener.query)
