"""authentik kerberos source signals"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from kadmin.exceptions import PyKAdminException
from rest_framework.serializers import ValidationError
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.core.signals import password_changed
from authentik.events.models import Event, EventAction
from authentik.sources.kerberos.models import (
    KerberosSource,
    Krb5ConfContext,
    UserKerberosSourceConnection,
)
from authentik.sources.kerberos.tasks import kerberos_connectivity_check, kerberos_sync_single

LOGGER = get_logger()


@receiver(post_save, sender=KerberosSource)
def sync_kerberos_source_on_save(sender, instance: KerberosSource, **_):
    """Ensure that source is synced on save (if enabled)"""
    if not instance.enabled or not instance.sync_users:
        return
    kerberos_sync_single.delay(instance.pk)
    kerberos_connectivity_check.delay(instance.pk)


@receiver(password_changed)
def kerberos_sync_password(sender, user: User, password: str, **_):
    """Connect to kerberos and update password."""
    user_source_connections = UserKerberosSourceConnection.objects.select_related(
        "source__kerberossource"
    ).filter(
        user=user,
        source__enabled=True,
        source__kerberossource__sync_users=True,
        source__kerberossource__sync_users_password=True,
    )
    for user_source_connection in user_source_connections:
        source = user_source_connection.source.kerberossource
        if source.pk == getattr(sender, "pk", None):
            continue
        with Krb5ConfContext(source):
            try:
                kadm = source.connection()
                kadm.get_principal(user_source_connection.identifier).change_password(
                    kadm,
                    password,
                )
            except PyKAdminException as exc:
                LOGGER.warning("failed to set Kerberos password", exc=exc, source=source)
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=(
                        "Failed to change password in Kerberos source due to remote error: "
                        f"{exc}"
                    ),
                    source=source,
                ).set_user(user).save()
                raise ValidationError("Failed to set password") from exc
