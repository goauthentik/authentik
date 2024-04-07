"""SCIM Utils"""

from typing import Any
from urllib.parse import urlparse

from django.http import HttpRequest
from django.urls import resolve
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from scim2_filter_parser.transpilers.django_q_object import get_query
from structlog import BoundLogger
from structlog.stdlib import get_logger

from authentik.core.models import Group, User
from authentik.sources.scim.models import SCIMSource
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

    source: SCIMSource
    logger: BoundLogger

    permission_classes = [IsAuthenticated]
    parser_classes = [SCIMParser]
    renderer_classes = [SCIMRenderer]

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self.logger = get_logger().bind()
        return super().setup(request, *args, **kwargs)

    def get_authenticators(self):
        return [SCIMTokenAuth(self)]

    def patch_resolve_value(self, raw_value: dict) -> User | Group | None:
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
            match raw_value["type"]:
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
        return get_query(path, {})


class SCIMRootView(SCIMView):
    """Root SCIM View"""

    def dispatch(self, request: Request, *args, **kwargs) -> Response:
        return Response({"message": "Use this base-URL with a SCIM-compatible system."})
