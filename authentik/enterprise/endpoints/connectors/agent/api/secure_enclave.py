from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.connectors.agent.models import AppleIndependentSecureEnclave


class AppleIndependentSecureEnclaveSerializer(ModelSerializer):
    class Meta:
        model = AppleIndependentSecureEnclave
        fields = [
            "uuid",
            "user",
            "apple_secure_enclave_key",
            "apple_enclave_key_id",
            "device_type",
        ]


class AppleIndependentSecureEnclaveViewSet(UsedByMixin, ModelViewSet):
    queryset = AppleIndependentSecureEnclave.objects.all()
    serializer_class = AppleIndependentSecureEnclaveSerializer
    search_fields = [
        "name",
        "user__name",
    ]
    ordering = ["uuid"]
    filterset_fields = ["user", "apple_enclave_key_id"]
