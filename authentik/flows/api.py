"""Flow API Views"""
from django.core.cache import cache
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

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


class FlowViewSet(ModelViewSet):
    """Flow Viewset"""

    queryset = Flow.objects.all()
    serializer_class = FlowSerializer
    lookup_field = "slug"


class FlowStageBindingSerializer(ModelSerializer):
    """FlowStageBinding Serializer"""

    class Meta:

        model = FlowStageBinding
        fields = [
            "pk",
            "target",
            "stage",
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
