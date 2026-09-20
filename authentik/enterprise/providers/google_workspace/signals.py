"""Google provider signals"""

from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from authentik.crypto.secrets.models import Secret, secret_value_validating
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
from authentik.enterprise.providers.google_workspace.tasks import (
    google_workspace_sync_delete_dispatch,
    google_workspace_sync_direct_dispatch,
    google_workspace_sync_m2m_dispatch,
)
from authentik.lib.sync.outgoing.signals import register_signals

register_signals(
    GoogleWorkspaceProvider,
    task_sync_direct_dispatch=google_workspace_sync_direct_dispatch,
    task_sync_delete_dispatch=google_workspace_sync_delete_dispatch,
    task_sync_m2m_dispatch=google_workspace_sync_m2m_dispatch,
)


@receiver(secret_value_validating, sender=Secret)
def validate_google_workspace_providers_secret(sender, secret: Secret, value: str, **kwargs):
    """Validate service account credential replacements."""
    if secret.google_workspace_providers.exists():
        try:
            Secret(type=secret.type, value=value).get_json()
        except ValueError:
            raise ValidationError(_("Secret must contain a JSON or YAML object.")) from None
