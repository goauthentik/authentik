"""Source API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.policies.forms import GENERAL_SERIALIZER_FIELDS
from passbook.policies.matcher.models import FieldMatcherPolicy


class FieldMatcherPolicySerializer(ModelSerializer):
    """Field Matcher Policy Serializer"""

    class Meta:
        model = FieldMatcherPolicy
        fields = GENERAL_SERIALIZER_FIELDS + [
            "user_field",
            "match_action",
            "value",
        ]


class FieldMatcherPolicyViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = FieldMatcherPolicy.objects.all()
    serializer_class = FieldMatcherPolicySerializer
