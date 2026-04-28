from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

from authentik.enterprise.license import LicenseKey
from authentik.providers.scim.models import SCIMAuthenticationMode


class SCIMProviderSerializerMixin:

    def validate_auth_mode(self, auth_mode: SCIMAuthenticationMode) -> SCIMAuthenticationMode:
        if auth_mode == SCIMAuthenticationMode.OAUTH:
            if not LicenseKey.cached_summary().status.is_valid:
                raise ValidationError(_("Enterprise is required to use the OAuth mode."))
        return auth_mode
