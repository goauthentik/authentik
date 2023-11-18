from antlr4 import CommonTokenStream, InputStream, ParseTreeWalker
from authentik.sources.scim.filters.django import DjangoQueryListener
from authentik.sources.scim.filters.ScimFilterLexer import ScimFilterLexer
from authentik.sources.scim.filters.ScimFilterParser import ScimFilterParser


lexer = ScimFilterLexer(InputStream('emails[type eq "work" and value ew "example.com"]'))
stream = CommonTokenStream(lexer)
parser = ScimFilterParser(stream)
tree = parser.filter_()
listener = DjangoQueryListener()
walker = ParseTreeWalker()
walker.walk(listener, tree)
print(listener.query)
