"""OAuth2Provider API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.utils import MetaNameSerializer
from authentik.providers.oauth2.models import ScopeMapping


class ScopeMappingSerializer(ModelSerializer, MetaNameSerializer):
    """ScopeMapping Serializer"""

    class Meta:

        model = ScopeMapping
        fields = [
            "pk",
            "name",
            "scope_name",
            "description",
            "expression",
            "verbose_name",
            "verbose_name_plural",
        ]


class ScopeMappingViewSet(ModelViewSet):
    """ScopeMapping Viewset"""

    queryset = ScopeMapping.objects.all()
    serializer_class = ScopeMappingSerializer
