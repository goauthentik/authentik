from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.requests.models import RequestRuleChildBinding


class RequestRuleChildBindingSerializer(ModelSerializer):

    class Meta:
        model = RequestRuleChildBinding
        fields = [
            "uuid",
            "binding",
            "target",
        ]


class RequestRuleChildBindingViewSet(UsedByMixin, ModelViewSet):

    queryset = RequestRuleChildBinding.objects.all()
    serializer_class = RequestRuleChildBindingSerializer
    filterset_fields = ["binding", "target"]
    ordering = ["binding"]
    search_fields = []
