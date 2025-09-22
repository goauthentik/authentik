"""SSF Stream API Views"""

from rest_framework.viewsets import ReadOnlyModelViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.providers.ssf.api.providers import SSFProviderSerializer
from authentik.enterprise.providers.ssf.models import Stream


class SSFStreamSerializer(ModelSerializer):
    """SSFStream Serializer"""

    provider_obj = SSFProviderSerializer(source="provider", read_only=True)

    class Meta:
        model = Stream
        fields = [
            "pk",
            "provider",
            "provider_obj",
            "delivery_method",
            "endpoint_url",
            "events_requested",
            "format",
            "aud",
            "iss",
        ]


class SSFStreamViewSet(ReadOnlyModelViewSet):
    """SSFStream Viewset"""

    queryset = Stream.objects.all()
    serializer_class = SSFStreamSerializer
    filterset_fields = ["provider", "endpoint_url", "delivery_method"]
    search_fields = ["provider__name", "endpoint_url"]
    ordering = ["provider", "uuid"]
