"""Flow API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.flows.models import Flow, FlowFactorBinding


class FlowSerializer(ModelSerializer):
    """Flow Serializer"""

    class Meta:

        model = Flow
        fields = ["pk", "name", "slug", "designation", "factors", "policies"]


class FlowViewSet(ModelViewSet):
    """Flow Viewset"""

    queryset = Flow.objects.all()
    serializer_class = FlowSerializer


class FlowFactorBindingSerializer(ModelSerializer):
    """FlowFactorBinding Serializer"""

    class Meta:

        model = FlowFactorBinding
        fields = ["pk", "flow", "factor", "re_evaluate_policies", "order", "policies"]


class FlowFactorBindingViewSet(ModelViewSet):
    """FlowFactorBinding Viewset"""

    queryset = FlowFactorBinding.objects.all()
    serializer_class = FlowFactorBindingSerializer
