"""OAuth2Provider API Views"""

from rest_framework.fields import CharField
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingFilterSet, PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.providers.oauth2.models import ScopeMapping


def no_space(value: str) -> str:
    """Ensure value contains no spaces"""
    if " " in value:
        raise ValidationError("Value must not contain spaces.")
    return value


class ScopeMappingSerializer(PropertyMappingSerializer):
    """ScopeMapping Serializer"""

    scope_name = CharField(help_text="Scope name requested by the client", validators=[no_space])

    class Meta:
        model = ScopeMapping
        fields = PropertyMappingSerializer.Meta.fields + [
            "scope_name",
            "description",
        ]


class ScopeMappingFilter(PropertyMappingFilterSet):
    """Filter for ScopeMapping"""

    class Meta(PropertyMappingFilterSet.Meta):
        model = ScopeMapping
        fields = PropertyMappingFilterSet.Meta.fields + ["scope_name"]


class ScopeMappingViewSet(UsedByMixin, ModelViewSet):
    """ScopeMapping Viewset"""

    queryset = ScopeMapping.objects.all()
    serializer_class = ScopeMappingSerializer
    filterset_class = ScopeMappingFilter
    ordering = ["scope_name", "name"]
    search_fields = ["name", "scope_name"]
