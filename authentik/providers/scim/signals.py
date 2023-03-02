"""SCIM provider signals"""
from django.db.models import Model
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from authentik.core.models import Group, User
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.clients.group import SCIMGroupClient
from authentik.providers.scim.clients.user import SCIMUserClient
from authentik.providers.scim.models import SCIMProvider
from authentik.providers.scim.tasks import scim_sync_full


@receiver(post_save, sender=SCIMProvider)
def post_save_provider(sender: type[Model], instance, created: bool, **_):
    """Trigger sync when SCIM provider is saved"""
    scim_sync_full.delay(instance.pk)


@receiver(post_save, sender=User)
@receiver(post_save, sender=Group)
def post_save_scim(sender: type[Model], instance: User | Group, created: bool, **_):
    """Post save handler"""
    # TODO: Run in task
    for provider in SCIMProvider.objects.all():
        client = SCIMClient(provider)
        if sender == User:
            user_client = SCIMUserClient(client)
            user_client.write(instance)
        if sender == Group:
            group_client = SCIMGroupClient(client)
            group_client.write(instance)


@receiver(pre_delete, sender=User)
@receiver(pre_delete, sender=Group)
def pre_delete_scim(sender: type[Model], instance: User | Group, **_):
    """Pre-delete handler"""
    # TODO: Run in task
    for provider in SCIMProvider.objects.all():
        client = SCIMClient(provider)
        if sender == User:
            user_client = SCIMUserClient(client)
            user_client.delete(instance)
        if sender == Group:
            group_client = SCIMGroupClient(client)
            group_client.delete(instance)
