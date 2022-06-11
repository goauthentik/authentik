"""Django listener"""
from django.db.models import Q
from django.utils.tree import Node

from authentik.sources.scim.filters.ScimFilterListener import ScimFilterListener
from authentik.sources.scim.filters.ScimFilterParser import ScimFilterParser


class DjangoQueryListener(ScimFilterListener):
    """SCIM filter listener that converts it to a query"""

    _query: Node
    _last_node: Node

    def __init__(self) -> None:
        super().__init__()
        self._query = Q()
        self._last_node = Q()

    @property
    def query(self) -> Node:
        return self._query

    def enterParse(self, ctx: ScimFilterParser.ParseContext):
        print("enterParse", ctx)

    def exitParse(self, ctx: ScimFilterParser.ParseContext):
        print("exitParse", ctx)

    def enterAndExp(self, ctx: ScimFilterParser.AndExpContext):
        print("enterAndExp", ctx)

    def exitAndExp(self, ctx: ScimFilterParser.AndExpContext):
        print("exitAndExp", ctx)

    def enterValPathExp(self, ctx: ScimFilterParser.ValPathExpContext):
        print("enterValPathExp", ctx.getText())

    def exitValPathExp(self, ctx: ScimFilterParser.ValPathExpContext):
        print("exitValPathExp", ctx)

    def enterPresentExp(self, ctx: ScimFilterParser.PresentExpContext):
        print("enterPresentExp", ctx)

    def exitPresentExp(self, ctx: ScimFilterParser.PresentExpContext):
        print("exitPresentExp", ctx)

    def enterOperatorExp(self, ctx: ScimFilterParser.OperatorExpContext):
        print("enterOperatorExp", ctx)

    def exitOperatorExp(self, ctx: ScimFilterParser.OperatorExpContext):
        print("exitOperatorExp", ctx)

    def enterBraceExp(self, ctx: ScimFilterParser.BraceExpContext):
        print("enterBraceExp", ctx)

    def exitBraceExp(self, ctx: ScimFilterParser.BraceExpContext):
        print("exitBraceExp", ctx)

    def enterOrExp(self, ctx: ScimFilterParser.OrExpContext):
        print("enterOrExp", ctx)

    def exitOrExp(self, ctx: ScimFilterParser.OrExpContext):
        print("exitOrExp", ctx)

    def enterValPathOperatorExp(self, ctx: ScimFilterParser.ValPathOperatorExpContext):
        print("enterValPathOperatorExp", ctx)

    def exitValPathOperatorExp(self, ctx: ScimFilterParser.ValPathOperatorExpContext):
        print("exitValPathOperatorExp", ctx)

    def enterValPathPresentExp(self, ctx: ScimFilterParser.ValPathPresentExpContext):
        print("enterValPathPresentExp", ctx)

    def exitValPathPresentExp(self, ctx: ScimFilterParser.ValPathPresentExpContext):
        print("exitValPathPresentExp", ctx)

    def enterValPathAndExp(self, ctx: ScimFilterParser.ValPathAndExpContext):
        print("enterValPathAndExp", ctx.getText())

    def exitValPathAndExp(self, ctx: ScimFilterParser.ValPathAndExpContext):
        print("exitValPathAndExp", ctx)

    def enterValPathOrExp(self, ctx: ScimFilterParser.ValPathOrExpContext):
        print("enterValPathOrExp", ctx)

    def exitValPathOrExp(self, ctx: ScimFilterParser.ValPathOrExpContext):
        print("exitValPathOrExp", ctx)

    def enterValPathBraceExp(self, ctx: ScimFilterParser.ValPathBraceExpContext):
        print("enterValPathBraceExp", ctx)

    def exitValPathBraceExp(self, ctx: ScimFilterParser.ValPathBraceExpContext):
        print("exitValPathBraceExp", ctx)

    def enterAttrPath(self, ctx: ScimFilterParser.AttrPathContext):
        self._last_node = Q(ctx.getText())

    def exitAttrPath(self, ctx: ScimFilterParser.AttrPathContext):
        self._query = self._last_node
        self._last_node = Q()
