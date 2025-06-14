"""SCIM Utils"""

from typing import Any
from urllib.parse import urlparse

from django.conf import settings
from django.core.paginator import Page, Paginator
from django.db.models import Q, QuerySet
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
from authentik.core.sources.mapper import SourceMapper
from authentik.lib.sync.mapper import PropertyMappingManager
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
        super().setup(request, *args, **kwargs)

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

    def filter_parse(self, request: Request):
        """Parse the path of a Patch Operation"""
        path = request.query_params.get("filter")
        if not path:
            return Q()
        attr_map = {}
        if self.model == User:
            attr_map = {
                ("userName", None, None): "user__username",
                ("active", None, None): "user__is_active",
                ("name", "familyName", None): "attributes__familyName",
            }
        elif self.model == Group:
            attr_map = {
                ("displayName", None, None): "group__name",
                ("members", None, None): "group__users",
            }
        return get_query(
            path,
            attr_map,
        )

    def paginate_query(self, query: QuerySet) -> Page:
        per_page = 50
        start_index = 1
        try:
            per_page = int(settings.REST_FRAMEWORK["PAGE_SIZE"])
            start_index = int(self.request.query_params.get("startIndex", 1))
        except ValueError:
            pass
        paginator = Paginator(query, per_page=per_page)
        page = paginator.page(int(max(start_index / per_page, 1)))
        return page


class SCIMObjectView(SCIMView):
    """Base SCIM View for object management"""

    mapper: SourceMapper
    manager: PropertyMappingManager

    model: type[User | Group]

    def initial(self, request: Request, *args, **kwargs) -> None:
        super().initial(request, *args, **kwargs)
        # This needs to happen after authentication has happened, because we don't have
        # a source attribute before
        self.mapper = SourceMapper(self.source)
        self.manager = self.mapper.get_manager(self.model, ["data"])

    def build_object_properties(self, data: dict[str, Any]) -> dict[str, Any | dict[str, Any]]:
        return self.mapper.build_object_properties(
            object_type=self.model,
            manager=self.manager,
            user=None,
            request=self.request,
            data=data,
        )


class SCIMRootView(SCIMView):
    """Root SCIM View"""

    def dispatch(self, request: Request, *args, **kwargs) -> Response:
        return Response({"message": "Use this base-URL with a SCIM-compatible system."})
