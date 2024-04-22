"""Google provider signals"""

from django.db.models import Model
from django.db.models.signals import post_save
from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.enterprise.providers.google.models import GoogleProvider
from authentik.enterprise.providers.google.tasks import google_sync

LOGGER = get_logger()


@receiver(post_save, sender=GoogleProvider)
def post_save_provider(sender: type[Model], instance, created: bool, **_):
    """Trigger sync when Google provider is saved"""
    google_sync.delay(instance.pk)


# @receiver(post_save, sender=User)
# @receiver(post_save, sender=Group)
# def post_save_scim(sender: type[Model], instance: User | Group, created: bool, **_):
#     """Post save handler"""
#     if not SCIMProvider.objects.filter(backchannel_application__isnull=False).exists():
#         return
#     scim_signal_direct.delay(class_to_path(instance.__class__), instance.pk, PatchOp.add.value)


# @receiver(pre_delete, sender=User)
# @receiver(pre_delete, sender=Group)
# def pre_delete_scim(sender: type[Model], instance: User | Group, **_):
#     """Pre-delete handler"""
#     if not SCIMProvider.objects.filter(backchannel_application__isnull=False).exists():
#         return
#     scim_signal_direct.delay(class_to_path(instance.__class__), instance.pk, PatchOp.remove.value)


# @receiver(m2m_changed, sender=User.ak_groups.through)
# def m2m_changed_scim(
#     sender: type[Model], instance, action: str, pk_set: set, reverse: bool, **kwargs
# ):
#     """Sync group membership"""
#     if action not in ["post_add", "post_remove"]:
#         return
#     if not SCIMProvider.objects.filter(backchannel_application__isnull=False).exists():
#         return
#     # reverse: instance is a Group, pk_set is a list of user pks
#     # non-reverse: instance is a User, pk_set is a list of groups
#     if reverse:
#         scim_signal_m2m.delay(str(instance.pk), action, list(pk_set))
#     else:
#         for group_pk in pk_set:
#             scim_signal_m2m.delay(group_pk, action, [instance.pk])
