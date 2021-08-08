"""OAuth2Provider API Views"""
from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.propertymappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.providers.oauth2.models import ScopeMapping


class ScopeMappingSerializer(PropertyMappingSerializer):
    """ScopeMapping Serializer"""

    class Meta:

        model = ScopeMapping
        fields = PropertyMappingSerializer.Meta.fields + [
            "scope_name",
            "description",
        ]


class ScopeMappingFilter(FilterSet):
    """Filter for ScopeMapping"""

    managed = AllValuesMultipleFilter(field_name="managed")

    class Meta:
        model = ScopeMapping
        fields = ["scope_name", "name", "managed"]


class ScopeMappingViewSet(UsedByMixin, ModelViewSet):
    """ScopeMapping Viewset"""

    queryset = ScopeMapping.objects.all()
    serializer_class = ScopeMappingSerializer
    filterset_class = ScopeMappingFilter
    ordering = ["scope_name", "name"]
