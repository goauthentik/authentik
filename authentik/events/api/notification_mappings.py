"""NotificationWebhookMapping API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.events.models import NotificationWebhookMapping


class NotificationWebhookMappingSerializer(ModelSerializer):
    """NotificationWebhookMapping Serializer"""

    class Meta:

        model = NotificationWebhookMapping
        fields = [
            "pk",
            "name",
            "expression",
        ]


class NotificationWebhookMappingViewSet(UsedByMixin, ModelViewSet):
    """NotificationWebhookMapping Viewset"""

    queryset = NotificationWebhookMapping.objects.all()
    serializer_class = NotificationWebhookMappingSerializer
    filterset_fields = ["name"]
    ordering = ["name"]
    search_fields = ["name"]
