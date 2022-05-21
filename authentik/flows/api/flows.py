"""Flow API Views"""
from dataclasses import dataclass

from django.core.cache import cache
from django.db.models import Model
from django.http.response import HttpResponseBadRequest, JsonResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import ReadOnlyField
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import CharField, ModelSerializer, Serializer, SerializerMethodField
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.api.decorators import permission_required
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import (
    CacheSerializer,
    FilePathSerializer,
    FileUploadSerializer,
    LinkSerializer,
)
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import Flow
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlanner, cache_key
from authentik.flows.transfer.common import DataclassEncoder
from authentik.flows.transfer.exporter import FlowExporter
from authentik.flows.transfer.importer import FlowImporter
from authentik.flows.views.executor import SESSION_KEY_HISTORY, SESSION_KEY_PLAN
from authentik.lib.views import bad_request_message

LOGGER = get_logger()


class FlowSerializer(ModelSerializer):
    """Flow Serializer"""

    cache_count = SerializerMethodField()

    background = ReadOnlyField(source="background_url")

    export_url = SerializerMethodField()

    def get_cache_count(self, flow: Flow) -> int:
        """Get count of cached flows"""
        return len(cache.keys(f"{cache_key(flow)}*"))

    def get_export_url(self, flow: Flow) -> str:
        """Get export URL for flow"""
        return reverse("authentik_api:flow-export", kwargs={"slug": flow.slug})

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
        ]
        extra_kwargs = {
            "background": {"read_only": True},
        }


class FlowDiagramSerializer(Serializer):
    """response of the flow's diagram action"""

    diagram = CharField(read_only=True)

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


@dataclass
class DiagramElement:
    """Single element used in a diagram"""

    identifier: str
    type: str
    rest: str

    def __str__(self) -> str:
        return f"{self.identifier}=>{self.type}: {self.rest}"


class FlowViewSet(UsedByMixin, ModelViewSet):
    """Flow Viewset"""

    queryset = Flow.objects.all()
    serializer_class = FlowSerializer
    lookup_field = "slug"
    ordering = ["slug", "name"]
    search_fields = ["name", "slug", "designation", "title"]
    filterset_fields = ["flow_uuid", "name", "slug", "designation"]

    @permission_required(None, ["authentik_flows.view_flow_cache"])
    @extend_schema(responses={200: CacheSerializer(many=False)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def cache_info(self, request: Request) -> Response:
        """Info about cached flows"""
        return Response(data={"count": len(cache.keys("flow_*"))})

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
        keys = cache.keys("flow_*")
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
            204: OpenApiResponse(description="Successfully imported flow"),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(detail=False, methods=["POST"], parser_classes=(MultiPartParser,))
    def import_flow(self, request: Request) -> Response:
        """Import flow from .akflow file"""
        file = request.FILES.get("file", None)
        if not file:
            return HttpResponseBadRequest()
        importer = FlowImporter(file.read().decode())
        valid = importer.validate()
        if not valid:
            return HttpResponseBadRequest()
        successful = importer.apply()
        if not successful:
            return HttpResponseBadRequest()
        return Response(status=204)

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
    # pylint: disable=unused-argument
    def export(self, request: Request, slug: str) -> Response:
        """Export flow to .akflow file"""
        flow = self.get_object()
        exporter = FlowExporter(flow)
        response = JsonResponse(exporter.export(), encoder=DataclassEncoder, safe=False)
        response["Content-Disposition"] = f'attachment; filename="{flow.slug}.akflow"'
        return response

    @extend_schema(responses={200: FlowDiagramSerializer()})
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["get"])
    # pylint: disable=unused-argument
    def diagram(self, request: Request, slug: str) -> Response:
        """Return diagram for flow with slug `slug`, in the format used by flowchart.js"""
        flow = self.get_object()
        header = [
            DiagramElement("st", "start", "Start"),
        ]
        body: list[DiagramElement] = []
        footer = []
        # Collect all elements we need
        # First, policies bound to the flow itself
        for p_index, policy_binding in enumerate(
            get_objects_for_user(request.user, "authentik_policies.view_policybinding")
            .filter(target=flow)
            .exclude(policy__isnull=True)
            .order_by("order")
        ):
            body.append(
                DiagramElement(
                    f"flow_policy_{p_index}",
                    "condition",
                    _("Policy (%(type)s)" % {"type": policy_binding.policy._meta.verbose_name})
                    + "\n"
                    + policy_binding.policy.name,
                )
            )
        # Collect all stages
        for s_index, stage_binding in enumerate(
            get_objects_for_user(request.user, "authentik_flows.view_flowstagebinding")
            .filter(target=flow)
            .order_by("order")
        ):
            # First all policies bound to stages since they execute before stages
            for p_index, policy_binding in enumerate(
                get_objects_for_user(request.user, "authentik_policies.view_policybinding")
                .filter(target=stage_binding)
                .exclude(policy__isnull=True)
                .order_by("order")
            ):
                body.append(
                    DiagramElement(
                        f"stage_{s_index}_policy_{p_index}",
                        "condition",
                        _("Policy (%(type)s)" % {"type": policy_binding.policy._meta.verbose_name})
                        + "\n"
                        + policy_binding.policy.name,
                    )
                )
            body.append(
                DiagramElement(
                    f"stage_{s_index}",
                    "operation",
                    _("Stage (%(type)s)" % {"type": stage_binding.stage._meta.verbose_name})
                    + "\n"
                    + stage_binding.stage.name,
                )
            )
        # If the 2nd last element is a policy, we need to have an item to point to
        # for a negative case
        body.append(
            DiagramElement("e", "end", "End|future"),
        )
        if len(body) == 1:
            footer.append("st(right)->e")
        else:
            # Actual diagram flow
            footer.append(f"st(right)->{body[0].identifier}")
            for index in range(len(body) - 1):
                element: DiagramElement = body[index]
                if element.type == "condition":
                    # Policy passes, link policy yes to next stage
                    footer.append(f"{element.identifier}(yes, right)->{body[index + 1].identifier}")
                    # Policy doesn't pass, go to stage after next stage
                    no_element = body[index + 1]
                    if no_element.type != "end":
                        no_element = body[index + 2]
                    footer.append(f"{element.identifier}(no, bottom)->{no_element.identifier}")
                elif element.type == "operation":
                    footer.append(f"{element.identifier}(bottom)->{body[index + 1].identifier}")
        diagram = "\n".join([str(x) for x in header + body + footer])
        return Response({"diagram": diagram})

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
    # pylint: disable=unused-argument
    def set_background(self, request: Request, slug: str):
        """Set Flow background"""
        flow: Flow = self.get_object()
        background = request.FILES.get("file", None)
        clear = request.data.get("clear", "false").lower() == "true"
        if clear:
            if flow.background_url.startswith("/media"):
                # .delete() saves the model by default
                flow.background.delete()
            else:
                flow.background = None
                flow.save()
            return Response({})
        if background:
            flow.background = background
            flow.save()
            return Response({})
        return HttpResponseBadRequest()

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
    # pylint: disable=unused-argument
    def set_background_url(self, request: Request, slug: str):
        """Set Flow background (as URL)"""
        flow: Flow = self.get_object()
        url = request.data.get("url", None)
        if not url:
            return HttpResponseBadRequest()
        flow.background.name = url
        flow.save()
        return Response({})

    @extend_schema(
        responses={
            200: LinkSerializer(many=False),
            400: OpenApiResponse(description="Flow not applicable"),
        },
    )
    @action(detail=True, pagination_class=None, filter_backends=[])
    # pylint: disable=unused-argument
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
                    % {"messages": str(exc)}
                ),
            )
        return Response(
            {
                "link": request._request.build_absolute_uri(
                    reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
                )
            }
        )
