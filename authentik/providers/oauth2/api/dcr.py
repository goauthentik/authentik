"""OAuth2 Dynamic Client Registration API"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.providers.oauth2.models import (
    OAuth2DynamicClientRegistration,
)


class OAuth2DynamicClientRegistrationSerializer(ModelSerializer):
    """Serializer for OAuth2DynamicClientRegistration"""

    class Meta:
        model = OAuth2DynamicClientRegistration
        fields = [
            "pbm_uuid",
            "provider",
            "default_application_group",
            "override_authorization_flow",
            "override_invalidation_flow",
            "override_property_mappings",
            "access_token_validity",
            "refresh_token_validity",
            "allowed_grant_types",
            "policy_engine_mode",
        ]


class OAuth2DynamicClientRegistrationViewSet(ModelViewSet):
    """OAuth2 Dynamic Client Registration configuration ViewSet"""

    queryset = OAuth2DynamicClientRegistration.objects.all()
    serializer_class = OAuth2DynamicClientRegistrationSerializer
    filterset_fields = ["provider"]
    search_fields = ["provider__name"]
    ordering = ["provider__name"]
