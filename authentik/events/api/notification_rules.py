"""NotificationRule API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.groups import GroupSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.events.models import NotificationRule


class NotificationRuleSerializer(ModelSerializer):
    """NotificationRule Serializer"""

    destination_group_obj = GroupSerializer(read_only=True, source="destination_group")

    class Meta:
        model = NotificationRule
        fields = [
            "pk",
            "name",
            "transports",
            "severity",
            "destination_group",
            "destination_group_obj",
            "destination_event_user",
        ]


class NotificationRuleViewSet(UsedByMixin, ModelViewSet):
    """NotificationRule Viewset"""

    queryset = NotificationRule.objects.all()
    serializer_class = NotificationRuleSerializer
    filterset_fields = ["name", "severity", "destination_group__name"]
    ordering = ["name"]
    search_fields = ["name", "destination_group__name"]
