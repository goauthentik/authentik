# Generated from /local/ScimFilter.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .ScimFilterParser import ScimFilterParser
else:
    from ScimFilterParser import ScimFilterParser

# This class defines a complete listener for a parse tree produced by ScimFilterParser.
class ScimFilterListener(ParseTreeListener):

    # Enter a parse tree produced by ScimFilterParser#parse.
    def enterParse(self, ctx:ScimFilterParser.ParseContext):
        pass

    # Exit a parse tree produced by ScimFilterParser#parse.
    def exitParse(self, ctx:ScimFilterParser.ParseContext):
        pass


    # Enter a parse tree produced by ScimFilterParser#andExp.
    def enterAndExp(self, ctx:ScimFilterParser.AndExpContext):
        pass

    # Exit a parse tree produced by ScimFilterParser#andExp.
    def exitAndExp(self, ctx:ScimFilterParser.AndExpContext):
        pass


    # Enter a parse tree produced by ScimFilterParser#valPathExp.
    def enterValPathExp(self, ctx:ScimFilterParser.ValPathExpContext):
        pass

    # Exit a parse tree produced by ScimFilterParser#valPathExp.
    def exitValPathExp(self, ctx:ScimFilterParser.ValPathExpContext):
        pass


    # Enter a parse tree produced by ScimFilterParser#presentExp.
    def enterPresentExp(self, ctx:ScimFilterParser.PresentExpContext):
        pass

    # Exit a parse tree produced by ScimFilterParser#presentExp.
    def exitPresentExp(self, ctx:ScimFilterParser.PresentExpContext):
        pass


    # Enter a parse tree produced by ScimFilterParser#operatorExp.
    def enterOperatorExp(self, ctx:ScimFilterParser.OperatorExpContext):
        pass

    # Exit a parse tree produced by ScimFilterParser#operatorExp.
    def exitOperatorExp(self, ctx:ScimFilterParser.OperatorExpContext):
        pass


    # Enter a parse tree produced by ScimFilterParser#braceExp.
    def enterBraceExp(self, ctx:ScimFilterParser.BraceExpContext):
        pass

    # Exit a parse tree produced by ScimFilterParser#braceExp.
    def exitBraceExp(self, ctx:ScimFilterParser.BraceExpContext):
        pass


    # Enter a parse tree produced by ScimFilterParser#orExp.
    def enterOrExp(self, ctx:ScimFilterParser.OrExpContext):
        pass

    # Exit a parse tree produced by ScimFilterParser#orExp.
    def exitOrExp(self, ctx:ScimFilterParser.OrExpContext):
        pass


    # Enter a parse tree produced by ScimFilterParser#valPathOperatorExp.
    def enterValPathOperatorExp(self, ctx:ScimFilterParser.ValPathOperatorExpContext):
        pass

    # Exit a parse tree produced by ScimFilterParser#valPathOperatorExp.
    def exitValPathOperatorExp(self, ctx:ScimFilterParser.ValPathOperatorExpContext):
        pass


    # Enter a parse tree produced by ScimFilterParser#valPathPresentExp.
    def enterValPathPresentExp(self, ctx:ScimFilterParser.ValPathPresentExpContext):
        pass

    # Exit a parse tree produced by ScimFilterParser#valPathPresentExp.
    def exitValPathPresentExp(self, ctx:ScimFilterParser.ValPathPresentExpContext):
        pass


    # Enter a parse tree produced by ScimFilterParser#valPathAndExp.
    def enterValPathAndExp(self, ctx:ScimFilterParser.ValPathAndExpContext):
        pass

    # Exit a parse tree produced by ScimFilterParser#valPathAndExp.
    def exitValPathAndExp(self, ctx:ScimFilterParser.ValPathAndExpContext):
        pass


    # Enter a parse tree produced by ScimFilterParser#valPathOrExp.
    def enterValPathOrExp(self, ctx:ScimFilterParser.ValPathOrExpContext):
        pass

    # Exit a parse tree produced by ScimFilterParser#valPathOrExp.
    def exitValPathOrExp(self, ctx:ScimFilterParser.ValPathOrExpContext):
        pass


    # Enter a parse tree produced by ScimFilterParser#valPathBraceExp.
    def enterValPathBraceExp(self, ctx:ScimFilterParser.ValPathBraceExpContext):
        pass

    # Exit a parse tree produced by ScimFilterParser#valPathBraceExp.
    def exitValPathBraceExp(self, ctx:ScimFilterParser.ValPathBraceExpContext):
        pass


    # Enter a parse tree produced by ScimFilterParser#attrPath.
    def enterAttrPath(self, ctx:ScimFilterParser.AttrPathContext):
        pass

    # Exit a parse tree produced by ScimFilterParser#attrPath.
    def exitAttrPath(self, ctx:ScimFilterParser.AttrPathContext):
        pass



del ScimFilterParser