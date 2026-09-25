"""Validate credentials used by this consumer."""

from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from authentik.crypto.secrets.models import Secret
from authentik.crypto.secrets.signals import secret_value_validating


@receiver(secret_value_validating, sender=Secret)
def validate_google_chrome_connectors_secret(sender, secret: Secret, value: str, **kwargs):
    """Validate service account credential replacements."""
    if secret.google_chrome_connectors.exists():
        try:
            Secret(type=secret.type, value=value).get_json()
        except ValueError:
            raise ValidationError(_("Secret must contain a JSON or YAML object.")) from None
