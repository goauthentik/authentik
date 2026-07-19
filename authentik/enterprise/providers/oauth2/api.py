"""OAuth2 Dynamic Client Registration API"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.providers.oauth2.models import (
    OAuth2DynamicClientRegistration,
)


class OAuth2DynamicClientRegistrationSerializer(EnterpriseRequiredMixin, ModelSerializer):
    """Serializer for OAuth2DynamicClientRegistration"""

    class Meta:
        model = OAuth2DynamicClientRegistration
        fields = [
            "pbm_uuid",
            "provider",
            "create_application",
            "default_application_group",
            "default_client_type",
            "default_authorization_flow",
            "default_invalidation_flow",
            "default_property_mappings",
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
