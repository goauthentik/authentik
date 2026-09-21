from datetime import datetime

from django.urls import reverse
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

from authentik.enterprise.license import LicenseKey
from authentik.providers.scim.models import SCIMAuthenticationMode, SCIMProvider
from authentik.sources.oauth.models import UserOAuthSourceConnection


class SCIMProviderSerializerMixin:

    def _get_token(self, instance: SCIMProvider) -> UserOAuthSourceConnection | None:
        user = instance.auth_oauth_user
        conn = UserOAuthSourceConnection.objects.filter(
            user=user, source=instance.auth_oauth
        ).first()
        return conn

    def get_auth_oauth_token_last_updated(self, instance: SCIMProvider) -> datetime | None:
        conn = self._get_token(instance)
        return conn.last_updated if conn else None

    def get_auth_oauth_token_expires(self, instance: SCIMProvider) -> datetime | None:
        conn = self._get_token(instance)
        return conn.expires if conn else None

    def get_auth_oauth_url_callback(self, instance: SCIMProvider) -> str | None:
        if (
            instance.auth_mode
            in [
                SCIMAuthenticationMode.TOKEN,
                SCIMAuthenticationMode.OAUTH_SILENT,
            ]
            or not instance.backchannel_application
        ):
            return None
        relative_url = reverse(
            "authentik_enterprise_providers_scim:callback",
            kwargs={"application_slug": instance.backchannel_application.slug},
        )
        if "request" not in self.context:
            return relative_url
        return self.context["request"].build_absolute_uri(relative_url)

    def get_auth_oauth_url_start(self, instance: SCIMProvider) -> str | None:
        if (
            instance.auth_mode
            in [
                SCIMAuthenticationMode.TOKEN,
                SCIMAuthenticationMode.OAUTH_SILENT,
            ]
            or not instance.backchannel_application
        ):
            return None
        relative_url = reverse(
            "authentik_enterprise_providers_scim:start",
            kwargs={"application_slug": instance.backchannel_application.slug},
        )
        if "request" not in self.context:
            return relative_url
        return self.context["request"].build_absolute_uri(relative_url)

    def validate_auth_mode(self, auth_mode: SCIMAuthenticationMode) -> SCIMAuthenticationMode:
        if auth_mode in [
            SCIMAuthenticationMode.OAUTH_SILENT,
            SCIMAuthenticationMode.OAUTH_INTERACTIVE,
        ]:
            if not LicenseKey.cached_summary().status.is_valid:
                raise ValidationError(_("Enterprise is required to use the OAuth mode."))
        return auth_mode
