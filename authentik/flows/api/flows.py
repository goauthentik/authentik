"""Flow API Views"""
from django.core.cache import cache
from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, CharField, DictField, ListField, ReadOnlyField
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.api.decorators import permission_required
from authentik.blueprints.v1.exporter import FlowExporter
from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT, Importer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import CacheSerializer, LinkSerializer, PassiveSerializer
from authentik.events.utils import sanitize_dict
from authentik.flows.api.flows_diagram import FlowDiagram, FlowDiagramSerializer
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import Flow
from authentik.flows.planner import CACHE_PREFIX, PLAN_CONTEXT_PENDING_USER, FlowPlanner, cache_key
from authentik.flows.views.executor import SESSION_KEY_HISTORY, SESSION_KEY_PLAN
from authentik.lib.utils.file import (
    FilePathSerializer,
    FileUploadSerializer,
    set_file,
    set_file_url,
)
from authentik.lib.views import bad_request_message

LOGGER = get_logger()


class FlowSerializer(ModelSerializer):
    """Flow Serializer"""

    background = ReadOnlyField(source="background_url")

    cache_count = SerializerMethodField()
    export_url = SerializerMethodField()

    def get_cache_count(self, flow: Flow) -> int:
        """Get count of cached flows"""
        return len(cache.keys(f"{cache_key(flow)}*"))

    def get_export_url(self, flow: Flow) -> str:
        """Get export URL for flow"""
        return reverse("authentik_api:flow-export", kwargs={"slug": flow.slug})

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if SERIALIZER_CONTEXT_BLUEPRINT in self.context:
            self.fields["background"] = CharField(required=False)

    class Meta:
        model = Flow
        fields = [
            "pk",
            "policybindingmodel_ptr_id",
            "name",
            "slug",
            "title",
            "designation",
            "background",
            "stages",
            "policies",
            "cache_count",
            "policy_engine_mode",
            "compatibility_mode",
            "export_url",
            "layout",
            "denied_action",
            "authentication",
        ]
        extra_kwargs = {
            "background": {"read_only": True},
        }


class FlowSetSerializer(FlowSerializer):
    """Stripped down flow serializer"""

    class Meta:
        model = Flow
        fields = [
            "pk",
            "policybindingmodel_ptr_id",
            "name",
            "slug",
            "title",
            "designation",
            "background",
            "policy_engine_mode",
            "compatibility_mode",
            "export_url",
            "layout",
            "denied_action",
        ]


class FlowImportResultSerializer(PassiveSerializer):
    """Logs of an attempted flow import"""

    logs = ListField(child=DictField(), read_only=True)
    success = BooleanField(read_only=True)


class FlowViewSet(UsedByMixin, ModelViewSet):
    """Flow Viewset"""

    queryset = Flow.objects.all().prefetch_related("stages", "policies")
    serializer_class = FlowSerializer
    lookup_field = "slug"
    ordering = ["slug", "name"]
    search_fields = ["name", "slug", "designation", "title", "denied_action"]
    filterset_fields = ["flow_uuid", "name", "slug", "designation", "denied_action"]

    @permission_required(None, ["authentik_flows.view_flow_cache"])
    @extend_schema(responses={200: CacheSerializer(many=False)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def cache_info(self, request: Request) -> Response:
        """Info about cached flows"""
        return Response(data={"count": len(cache.keys(f"{CACHE_PREFIX}*"))})

    @permission_required(None, ["authentik_flows.clear_flow_cache"])
    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            204: OpenApiResponse(description="Successfully cleared cache"),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(detail=False, methods=["POST"])
    def cache_clear(self, request: Request) -> Response:
        """Clear flow cache"""
        keys = cache.keys(f"{CACHE_PREFIX}*")
        cache.delete_many(keys)
        LOGGER.debug("Cleared flow cache", keys=len(keys))
        return Response(status=204)

    @permission_required(
        None,
        [
            "authentik_flows.add_flow",
            "authentik_flows.change_flow",
            "authentik_flows.add_flowstagebinding",
            "authentik_flows.change_flowstagebinding",
            "authentik_flows.add_stage",
            "authentik_flows.change_stage",
            "authentik_policies.add_policy",
            "authentik_policies.change_policy",
            "authentik_policies.add_policybinding",
            "authentik_policies.change_policybinding",
            "authentik_stages_prompt.add_prompt",
            "authentik_stages_prompt.change_prompt",
        ],
    )
    @extend_schema(
        request={"multipart/form-data": FileUploadSerializer},
        responses={
            204: FlowImportResultSerializer,
            400: FlowImportResultSerializer,
        },
    )
    @action(url_path="import", detail=False, methods=["POST"], parser_classes=(MultiPartParser,))
    def import_flow(self, request: Request) -> Response:
        """Import flow from .yaml file"""
        import_response = FlowImportResultSerializer(
            data={
                "logs": [],
                "success": False,
            }
        )
        import_response.is_valid()
        file = request.FILES.get("file", None)
        if not file:
            return Response(data=import_response.initial_data, status=400)

        importer = Importer(file.read().decode())
        valid, logs = importer.validate()
        import_response.initial_data["logs"] = [sanitize_dict(log) for log in logs]
        import_response.initial_data["success"] = valid
        import_response.is_valid()
        if not valid:
            return Response(data=import_response.initial_data, status=200)

        successful = importer.apply()
        import_response.initial_data["success"] = successful
        import_response.is_valid()
        if not successful:
            return Response(data=import_response.initial_data, status=200)
        return Response(data=import_response.initial_data, status=200)

    @permission_required(
        "authentik_flows.export_flow",
        [
            "authentik_flows.view_flow",
            "authentik_flows.view_flowstagebinding",
            "authentik_flows.view_stage",
            "authentik_policies.view_policy",
            "authentik_policies.view_policybinding",
            "authentik_stages_prompt.view_prompt",
        ],
    )
    @extend_schema(
        responses={
            "200": OpenApiResponse(response=OpenApiTypes.BINARY),
        },
    )
    @action(detail=True, pagination_class=None, filter_backends=[])
    def export(self, request: Request, slug: str) -> Response:
        """Export flow to .yaml file"""
        flow = self.get_object()
        exporter = FlowExporter(flow)
        response = HttpResponse(content=exporter.export_to_string())
        response["Content-Disposition"] = f'attachment; filename="{flow.slug}.yaml"'
        return response

    @extend_schema(responses={200: FlowDiagramSerializer()})
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["get"])
    def diagram(self, request: Request, slug: str) -> Response:
        """Return diagram for flow with slug `slug`, in the format used by flowchart.js"""
        diagram = FlowDiagram(self.get_object(), request.user)
        output = diagram.build()
        return Response({"diagram": output})

    @permission_required("authentik_flows.change_flow")
    @extend_schema(
        request={
            "multipart/form-data": FileUploadSerializer,
        },
        responses={
            200: OpenApiResponse(description="Success"),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(
        detail=True,
        pagination_class=None,
        filter_backends=[],
        methods=["POST"],
        parser_classes=(MultiPartParser,),
    )
    def set_background(self, request: Request, slug: str):
        """Set Flow background"""
        flow: Flow = self.get_object()
        return set_file(request, flow, "background")

    @permission_required("authentik_core.change_application")
    @extend_schema(
        request=FilePathSerializer,
        responses={
            200: OpenApiResponse(description="Success"),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(
        detail=True,
        pagination_class=None,
        filter_backends=[],
        methods=["POST"],
    )
    def set_background_url(self, request: Request, slug: str):
        """Set Flow background (as URL)"""
        flow: Flow = self.get_object()
        return set_file_url(request, flow, "background")

    @extend_schema(
        responses={
            200: LinkSerializer(many=False),
            400: OpenApiResponse(description="Flow not applicable"),
        },
    )
    @action(detail=True, pagination_class=None, filter_backends=[])
    def execute(self, request: Request, slug: str):
        """Execute flow for current user"""
        # Because we pre-plan the flow here, and not in the planner, we need to manually clear
        # the history of the inspector
        request.session[SESSION_KEY_HISTORY] = []
        flow: Flow = self.get_object()
        planner = FlowPlanner(flow)
        planner.use_cache = False
        try:
            plan = planner.plan(self.request, {PLAN_CONTEXT_PENDING_USER: request.user})
            self.request.session[SESSION_KEY_PLAN] = plan
        except FlowNonApplicableException as exc:
            return bad_request_message(
                request,
                _(
                    "Flow not applicable to current user/request: %(messages)s"
                    % {"messages": exc.messages}
                ),
            )
        return Response(
            {
                "link": request._request.build_absolute_uri(
                    reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
                )
            }
        )
