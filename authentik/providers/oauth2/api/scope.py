"""OAuth2Provider API Views"""
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


class ScopeMappingViewSet(UsedByMixin, ModelViewSet):
    """ScopeMapping Viewset"""

    queryset = ScopeMapping.objects.all()
    serializer_class = ScopeMappingSerializer
    filterset_fields = ["scope_name", "name", "managed"]
    ordering = ["scope_name", "name"]
