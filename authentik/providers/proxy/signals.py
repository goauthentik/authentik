"""Proxy provider signals"""

from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from authentik.crypto.secrets.models import Secret
from authentik.crypto.secrets.signals import secret_value_validating

# The outpost derives its session cookie key from the secret and rejects shorter values.
MIN_COOKIE_SECRET_LENGTH = 32


@receiver(secret_value_validating, sender=Secret)
def validate_proxy_cookie_secret(sender, secret: Secret, value: str, **kwargs):
    """Keep cookie secrets long enough for outposts to sign sessions."""
    if len(value.encode()) < MIN_COOKIE_SECRET_LENGTH and secret.proxy_providers.exists():
        raise ValidationError(
            _("Cookie secrets must be at least %(length)d bytes long.")
            % {"length": MIN_COOKIE_SECRET_LENGTH}
        )
