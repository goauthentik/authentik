"""Reputation policy API Views"""

from django.utils.translation import gettext_lazy as _
from django_filters.filters import BaseInFilter, CharFilter
from django_filters.filterset import FilterSet
from rest_framework import mixins
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.reputation.models import Reputation, ReputationPolicy


class CharInFilter(BaseInFilter, CharFilter):
    pass


class ReputationPolicySerializer(PolicySerializer):
    """Reputation Policy Serializer"""

    def validate(self, attrs: dict) -> dict:
        if not attrs.get("check_ip", False) and not attrs.get("check_username", False):
            raise ValidationError(_("Either IP or Username must be checked"))
        return super().validate(attrs)

    class Meta:
        model = ReputationPolicy
        fields = PolicySerializer.Meta.fields + [
            "check_ip",
            "check_username",
            "threshold",
        ]


class ReputationPolicyViewSet(UsedByMixin, ModelViewSet):
    """Reputation Policy Viewset"""

    queryset = ReputationPolicy.objects.all()
    serializer_class = ReputationPolicySerializer
    filterset_fields = "__all__"
    search_fields = ["name", "threshold"]
    ordering = ["name"]


class ReputationFilter(FilterSet):
    """Filter for reputation"""

    identifier_in = CharInFilter(field_name="identifier", lookup_expr="in")

    class Meta:
        model = Reputation
        fields = ["identifier", "ip", "score"]


class ReputationSerializer(ModelSerializer):
    """Reputation Serializer"""

    class Meta:
        model = Reputation
        fields = [
            "pk",
            "identifier",
            "ip",
            "ip_geo_data",
            "ip_asn_data",
            "score",
            "updated",
        ]


class ReputationViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Reputation Viewset"""

    queryset = Reputation.objects.all()
    serializer_class = ReputationSerializer
    search_fields = ["identifier", "ip", "score"]
    filterset_class = ReputationFilter
    ordering = ["ip"]
