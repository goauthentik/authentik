"""Event Matcher Policy API"""
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ChoiceField
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.event_matcher.models import EventMatcherPolicy, app_choices


class EventMatcherPolicySerializer(PolicySerializer):
    """Event Matcher Policy Serializer"""

    app = ChoiceField(
        choices=app_choices(),
        required=False,
        allow_blank=True,
        help_text=_(
            "Match events created by selected application. When left empty, "
            "all applications are matched."
        ),
    )

    def validate(self, attrs: dict) -> dict:
        if attrs["action"] == "" and attrs["client_ip"] == "" and attrs["app"] == "":
            raise ValidationError(_("At least one criteria must be set."))
        return super().validate(attrs)

    class Meta:
        model = EventMatcherPolicy
        fields = PolicySerializer.Meta.fields + [
            "action",
            "client_ip",
            "app",
        ]


class EventMatcherPolicyViewSet(UsedByMixin, ModelViewSet):
    """Event Matcher Policy Viewset"""

    queryset = EventMatcherPolicy.objects.all()
    serializer_class = EventMatcherPolicySerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]
