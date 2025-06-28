from uuid import uuid4

from django.db import models

from authentik.core.models import ExpiringModel, User
from authentik.crypto.models import CertificateKeyPair
from authentik.providers.oauth2.models import (
    ClientTypes,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)


class ApplePlatformSSOProvider(OAuth2Provider):

    def set_oauth_defaults(self):
        """Ensure all OAuth2-related settings are correct"""
        self.client_type = ClientTypes.PUBLIC
        self.signing_key = CertificateKeyPair.objects.get(name="authentik Self-signed Certificate")
        self.include_claims_in_id_token = True
        scopes = ScopeMapping.objects.filter(
            managed__in=[
                "goauthentik.io/providers/oauth2/scope-openid",
                "goauthentik.io/providers/oauth2/scope-profile",
                "goauthentik.io/providers/oauth2/scope-email",
                "goauthentik.io/providers/oauth2/scope-offline_access",
                "goauthentik.io/providers/oauth2/scope-authentik_api",
            ]
        )
        self.property_mappings.add(*list(scopes))
        self.redirect_uris = [
            RedirectURI(RedirectURIMatchingMode.STRICT, "io.goauthentik.endpoint:/oauth2redirect"),
        ]


class AppleDevice(models.Model):

    endpoint_uuid = models.UUIDField(default=uuid4, primary_key=True)

    signing_key = models.TextField()
    encryption_key = models.TextField()
    key_exchange_key = models.TextField()
    sign_key_id = models.TextField()
    enc_key_id = models.TextField()
    creation_time = models.DateTimeField(auto_now_add=True)
    provider = models.ForeignKey(ApplePlatformSSOProvider, on_delete=models.CASCADE)
    users = models.ManyToManyField(User, through="AppleDeviceUser")


class AppleDeviceUser(models.Model):

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    device = models.ForeignKey(AppleDevice, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    signing_key = models.TextField()
    encryption_key = models.TextField()
    sign_key_id = models.TextField()
    enc_key_id = models.TextField()


class AppleNonce(ExpiringModel):
    nonce = models.TextField()
