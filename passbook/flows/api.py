"""Flow API Views"""
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from passbook.flows.models import Flow, FlowStageBinding, Stage


class FlowSerializer(ModelSerializer):
    """Flow Serializer"""

    class Meta:

        model = Flow
        fields = ["pk", "name", "slug", "designation", "stages", "policies"]


class FlowViewSet(ModelViewSet):
    """Flow Viewset"""

    queryset = Flow.objects.all()
    serializer_class = FlowSerializer


class FlowStageBindingSerializer(ModelSerializer):
    """FlowStageBinding Serializer"""

    class Meta:

        model = FlowStageBinding
        fields = ["pk", "flow", "stage", "re_evaluate_policies", "order", "policies"]


class FlowStageBindingViewSet(ModelViewSet):
    """FlowStageBinding Viewset"""

    queryset = FlowStageBinding.objects.all()
    serializer_class = FlowStageBindingSerializer


class StageSerializer(ModelSerializer):
    """Stage Serializer"""

    __type__ = SerializerMethodField(method_name="get_type")

    def get_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("stage", "")

    class Meta:

        model = Stage
        fields = ["pk", "name", "__type__"]


class StageViewSet(ReadOnlyModelViewSet):
    """Stage Viewset"""

    queryset = Stage.objects.all()
    serializer_class = StageSerializer

    def get_queryset(self):
        return Stage.objects.select_subclasses()
