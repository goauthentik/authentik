"""Flow API Views"""
from dataclasses import dataclass

from django.core.cache import cache
from django.db.models import Model
from django.shortcuts import get_object_or_404, reverse
from drf_yasg2.utils import swagger_auto_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import (
    CharField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
)
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from authentik.core.api.utils import (
    CacheSerializer,
    MetaNameSerializer,
    TypeCreateSerializer,
)
from authentik.flows.models import Flow, FlowStageBinding, Stage
from authentik.flows.planner import cache_key
from authentik.lib.templatetags.authentik_utils import verbose_name
from authentik.lib.utils.reflection import all_subclasses


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


class FlowDiagramSerializer(Serializer):
    """response of the flow's /diagram/ action"""

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


class FlowViewSet(ModelViewSet):
    """Flow Viewset"""

    queryset = Flow.objects.all()
    serializer_class = FlowSerializer
    lookup_field = "slug"
    search_fields = ["name", "slug", "designation", "title"]
    filterset_fields = ["flow_uuid", "name", "slug", "designation"]

    @swagger_auto_schema(responses={200: CacheSerializer(many=False)})
    @action(detail=False)
    def cached(self, request: Request) -> Response:
        """Info about cached flows"""
        return Response(data={"count": len(cache.keys("flow_*"))})

    @swagger_auto_schema(responses={200: FlowDiagramSerializer()})
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
        body: list[DiagramElement] = []
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
                    no_element = body[index + 1]
                    if no_element.type != "end":
                        no_element = body[index + 2]
                    footer.append(
                        f"{element.identifier}(no, bottom)->{no_element.identifier}"
                    )
                elif element.type == "operation":
                    footer.append(
                        f"{element.identifier}(bottom)->{body[index + 1].identifier}"
                    )
        diagram = "\n".join([str(x) for x in header + body + footer])
        return Response({"diagram": diagram})


class StageSerializer(ModelSerializer, MetaNameSerializer):
    """Stage Serializer"""

    object_type = SerializerMethodField()

    def get_object_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("stage", "")

    class Meta:

        model = Stage
        fields = ["pk", "name", "object_type", "verbose_name", "verbose_name_plural"]


class StageViewSet(ReadOnlyModelViewSet):
    """Stage Viewset"""

    queryset = Stage.objects.all()
    serializer_class = StageSerializer

    def get_queryset(self):
        return Stage.objects.select_subclasses()

    @swagger_auto_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False)
    def types(self, request: Request) -> Response:
        """Get all creatable stage types"""
        data = []
        for subclass in all_subclasses(self.queryset.model, False):
            data.append(
                {
                    "name": verbose_name(subclass),
                    "description": subclass.__doc__,
                    "link": reverse("authentik_admin:stage-create")
                    + f"?type={subclass.__name__}",
                }
            )
        data = sorted(data, key=lambda x: x["name"])
        return Response(TypeCreateSerializer(data, many=True).data)


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
