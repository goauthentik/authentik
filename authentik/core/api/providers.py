"""Provider API Views"""

from django.db.models import QuerySet
from django.db.models.query import Q
from django.utils.translation import gettext_lazy as _
from django_filters.filters import BooleanFilter
from django_filters.filterset import FilterSet
from rest_framework import mixins
from rest_framework.fields import ReadOnlyField, SerializerMethodField
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.object_types import TypesMixin
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import MetaNameSerializer, ModelSerializer
from authentik.core.models import Provider


class ProviderSerializer(ModelSerializer, MetaNameSerializer):
    """Provider Serializer"""

    assigned_application_slug = ReadOnlyField(source="application.slug")
    assigned_application_name = ReadOnlyField(source="application.name")
    assigned_backchannel_application_slug = ReadOnlyField(source="backchannel_application.slug")
    assigned_backchannel_application_name = ReadOnlyField(source="backchannel_application.name")

    component = SerializerMethodField()

    def get_component(self, obj: Provider) -> str:  # pragma: no cover
        """Get object component so that we know how to edit the object"""
        if obj.__class__ == Provider:
            return ""
        return obj.component

    class Meta:
        model = Provider
        fields = [
            "pk",
            "name",
            "authentication_flow",
            "authorization_flow",
            "invalidation_flow",
            "property_mappings",
            "component",
            "assigned_application_slug",
            "assigned_application_name",
            "assigned_backchannel_application_slug",
            "assigned_backchannel_application_name",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
        ]
        extra_kwargs = {
            "authorization_flow": {"required": True, "allow_null": False},
            "invalidation_flow": {"required": True, "allow_null": False},
        }


class ProviderFilter(FilterSet):
    """Filter for providers"""

    application__isnull = BooleanFilter(method="filter_application__isnull")
    backchannel = BooleanFilter(
        method="filter_backchannel",
        label=_(
            "When not set all providers are returned. When set to true, only backchannel "
            "providers are returned. When set to false, backchannel providers are excluded"
        ),
    )

    def filter_application__isnull(self, queryset: QuerySet, name, value):
        """Only return providers that are neither assigned to application,
        both as provider or application provider"""
        return queryset.filter(
            Q(backchannel_application__isnull=value, is_backchannel=True)
            | Q(application__isnull=value)
        )

    def filter_backchannel(self, queryset: QuerySet, name, value):
        """By default all providers are returned. When set to true, only backchannel providers are
        returned. When set to false, backchannel providers are excluded"""
        return queryset.filter(is_backchannel=value)


class ProviderViewSet(
    TypesMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Provider Viewset"""

    queryset = Provider.objects.none()
    serializer_class = ProviderSerializer
    filterset_class = ProviderFilter
    search_fields = [
        "name",
        "application__name",
    ]

    def get_queryset(self):  # pragma: no cover
        return Provider.objects.select_subclasses()
