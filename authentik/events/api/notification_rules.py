"""NotificationRule API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.groups import GroupSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.events.models import NotificationRule


class NotificationRuleSerializer(ModelSerializer):
    """NotificationRule Serializer"""

    group_obj = GroupSerializer(read_only=True, source="group")

    class Meta:

        model = NotificationRule
        fields = [
            "pk",
            "name",
            "transports",
            "severity",
            "group",
            "group_obj",
        ]


class NotificationRuleViewSet(UsedByMixin, ModelViewSet):
    """NotificationRule Viewset"""

    queryset = NotificationRule.objects.all()
    serializer_class = NotificationRuleSerializer
    filterset_fields = ["name", "severity", "group__name"]
    ordering = ["name"]
    search_fields = ["name", "group__name"]
