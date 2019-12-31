"""Source API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.policies.forms import GENERAL_SERIALIZER_FIELDS
from passbook.policies.webhook.models import WebhookPolicy


class WebhookPolicySerializer(ModelSerializer):
    """Webhook Policy Serializer"""

    class Meta:
        model = WebhookPolicy
        fields = GENERAL_SERIALIZER_FIELDS + [
            "url",
            "method",
            "json_body",
            "json_headers",
            "result_jsonpath",
            "result_json_value",
        ]


class WebhookPolicyViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = WebhookPolicy.objects.all()
    serializer_class = WebhookPolicySerializer
