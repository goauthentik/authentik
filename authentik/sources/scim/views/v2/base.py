"""SCIM Utils"""
from typing import Optional
from urllib.parse import urlparse

from antlr4 import CommonTokenStream, InputStream, ParseTreeWalker
from django.urls import resolve
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.core.models import Group, User
from authentik.sources.scim.filters.django import DjangoQueryListener
from authentik.sources.scim.filters.ScimFilterLexer import ScimFilterLexer
from authentik.sources.scim.filters.ScimFilterParser import ScimFilterParser
from authentik.sources.scim.views.v2.auth import SCIMTokenAuth

SCIM_CONTENT_TYPE = "application/scim+json"


class SCIMParser(JSONParser):
    """SCIM clients use a custom content type"""

    media_type = SCIM_CONTENT_TYPE


class SCIMRenderer(JSONRenderer):
    """SCIM clients also expect a custom content type"""

    media_type = SCIM_CONTENT_TYPE


class SCIMView(APIView):
    """Base class for SCIM Views"""

    authentication_classes = [SCIMTokenAuth]
    permission_classes = [IsAuthenticated]
    parser_classes = [SCIMParser]
    renderer_classes = [SCIMRenderer]

    def patch_resolve_value(self, raw_value: dict) -> Optional[User | Group]:
        """Attempt to resolve a raw `value` attribute of a patch operation into
        a database model"""
        model = User
        query = {}
        if "$ref" in raw_value:
            url = urlparse(raw_value["$ref"])
            if match := resolve(url.path):
                if match.url_name == "v2-users":
                    model = User
                    query = {"pk": int(match.kwargs["user_id"])}
        elif "type" in raw_value:
            match raw_value["tyoe"]:
                case "User":
                    model = User
                    query = {"pk": int(raw_value["value"])}
                case "Group":
                    model = Group
        else:
            return None
        return model.objects.filter(**query).first()

    def patch_parse_path(self, path: str):
        """Parse the path of a Patch Operation"""
        lexer = ScimFilterLexer(InputStream(path))
        stream = CommonTokenStream(lexer)
        parser = ScimFilterParser(stream)
        tree = parser.filter_()
        listener = DjangoQueryListener()
        walker = ParseTreeWalker()
        walker.walk(listener, tree)
        return listener.query


class SCIMRootView(SCIMView):
    """Root SCIM View"""

    def dispatch(self, request: Request, *args, **kwargs) -> Response:
        return Response({"message": "Use this base-URL with an SCIM-compatible system."})
