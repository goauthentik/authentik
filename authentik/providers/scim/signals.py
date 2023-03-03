"""SCIM provider signals"""
from django.db.models import Model
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.core.models import Group, User
from authentik.lib.utils.reflection import class_to_path
from authentik.providers.scim.clients.exceptions import SCIMRequestException, StopSync
from authentik.providers.scim.clients.group import SCIMGroupClient
from authentik.providers.scim.models import SCIMProvider
from authentik.providers.scim.tasks import (
    client_for_model,
    scim_signal_post_save,
    scim_signal_pre_delete,
    scim_sync,
)

LOGGER = get_logger()


@receiver(post_save, sender=SCIMProvider)
def post_save_provider(sender: type[Model], instance, created: bool, **_):
    """Trigger sync when SCIM provider is saved"""
    scim_sync.delay(instance.pk)


@receiver(post_save, sender=User)
@receiver(post_save, sender=Group)
def post_save_scim(sender: type[Model], instance: User | Group, created: bool, **_):
    """Post save handler"""
    scim_signal_post_save.delay(class_to_path(instance.__class__), instance.pk)


@receiver(pre_delete, sender=User)
@receiver(pre_delete, sender=Group)
def pre_delete_scim(sender: type[Model], instance: User | Group, **_):
    """Pre-delete handler"""
    scim_signal_pre_delete.delay(class_to_path(instance.__class__), instance.pk)


@receiver(m2m_changed, sender=User.ak_groups.through)
def m2m_changed_scim(sender: type[Model], instance, action: str, pk_set: set, **kwargs):
    """Sync group membership"""
    if action not in ["post_add", "post_remove"]:
        return
    print(sender, type(sender), instance, action, pk_set)
    # TODO: Run in task
    for provider in SCIMProvider.objects.all():
        client = SCIMGroupClient(provider)
        try:
            if action == "post_add":
                client.post_add(instance, pk_set)
            if action == "post_remove":
                client.post_remove(instance, pk_set)
        except (StopSync, SCIMRequestException) as exc:
            LOGGER.warning(exc)
