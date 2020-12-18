"""Flow API Views"""
from dataclasses import dataclass

from django.core.cache import cache
from django.shortcuts import get_object_or_404
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import (
    ModelSerializer,
    Serializer,
    SerializerMethodField,
)
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ReadOnlyModelViewSet

from authentik.flows.models import Flow, FlowStageBinding, Stage
from authentik.flows.planner import cache_key


class FlowSerializer(ModelSerializer):
    """Flow Serializer"""

    cache_count = SerializerMethodField()

    def get_cache_count(self, flow: Flow):
        """Get count of cached flows"""
        return len(cache.keys(f"{cache_key(flow)}*"))

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
        ]


@dataclass
class DiagramElement:
    """Single element used in a diagram"""

    identifier: str
    type: str
    rest: str

    def __str__(self) -> str:
        return f"{self.identifier}=>{self.type}: {self.rest}"


class FlowViewSet(ModelViewSet):
    """Flow Viewset"""

    queryset = Flow.objects.all()
    serializer_class = FlowSerializer
    lookup_field = "slug"

    @action(detail=True, methods=["get"])
    def diagram(self, request: Request, slug: str) -> Response:
        """Return diagram for flow with slug `slug`, in the format used by flowchart.js"""
        flow = get_object_or_404(
            get_objects_for_user(request.user, "authentik_flows.view_flow").filter(
                slug=slug
            )
        )
        header = [
            DiagramElement("st", "start", "Start"),
        ]
        body = []
        footer = []
        # First, collect all elements we need
        for s_index, stage_binding in enumerate(
            get_objects_for_user(request.user, "authentik_flows.view_flowstagebinding")
            .filter(target=flow)
            .order_by("order")
        ):
            body.append(
                DiagramElement(
                    f"stage_{s_index}",
                    "operation",
                    f"Stage\n{stage_binding.stage.name}",
                )
            )
            for p_index, policy_binding in enumerate(
                get_objects_for_user(
                    request.user, "authentik_policies.view_policybinding"
                )
                .filter(target=stage_binding)
                .order_by("order")
            ):
                body.append(
                    DiagramElement(
                        f"stage_{s_index}_policy_{p_index}",
                        "condition",
                        f"Policy\n{policy_binding.policy.name}",
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
                    footer.append(
                        f"{element.identifier}(yes, right)->{body[index + 1].identifier}"
                    )
                    # Policy doesn't pass, go to stage after next stage
                    footer.append(
                        f"{element.identifier}(no, bottom)->{body[index + 2].identifier}"
                    )
                elif element.type == "operation":
                    footer.append(
                        f"{element.identifier}(bottom)->{body[index + 1].identifier}"
                    )
        diagram = "\n".join([str(x) for x in header + body + footer])
        return Response(diagram)


class StageSerializer(ModelSerializer):
    """Stage Serializer"""

    __type__ = SerializerMethodField(method_name="get_type")
    verbose_name = SerializerMethodField(method_name="get_verbose_name")

    def get_type(self, obj: Stage) -> str:
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("stage", "")

    def get_verbose_name(self, obj: Stage) -> str:
        """Get verbose name for UI"""
        return obj._meta.verbose_name

    class Meta:

        model = Stage
        fields = ["pk", "name", "__type__", "verbose_name"]


class StageViewSet(ReadOnlyModelViewSet):
    """Stage Viewset"""

    queryset = Stage.objects.all()
    serializer_class = StageSerializer

    def get_queryset(self):
        return Stage.objects.select_subclasses()


class FlowStageBindingSerializer(ModelSerializer):
    """FlowStageBinding Serializer"""

    stage_obj = StageSerializer(read_only=True, source="stage")

    class Meta:

        model = FlowStageBinding
        fields = [
            "pk",
            "policybindingmodel_ptr_id",
            "target",
            "stage",
            "stage_obj",
            "evaluate_on_plan",
            "re_evaluate_policies",
            "order",
            "policies",
        ]


class FlowStageBindingViewSet(ModelViewSet):
    """FlowStageBinding Viewset"""

    queryset = FlowStageBinding.objects.all()
    serializer_class = FlowStageBindingSerializer
    filterset_fields = "__all__"


class FlowCacheViewSet(ListModelMixin, GenericViewSet):
    """Info about cached flows"""

    queryset = Flow.objects.none()
    serializer_class = Serializer

    def list(self, request: Request) -> Response:
        """Info about cached flows"""
        return Response(data={"pagination": {"count": len(cache.keys("flow_*"))}})
