from django.db.models import Model
from django.db.models.signals import post_save
from django.dispatch import receiver

from authentik.core.models import USER_PATH_SYSTEM_PREFIX, User, UserTypes
from authentik.events.middleware import audit_ignore
from authentik.providers.scim.models import SCIMProvider

USER_PATH_PROVIDERS_SCIM = USER_PATH_SYSTEM_PREFIX + "/providers/scim"


@receiver(post_save, sender=SCIMProvider)
def scim_provider_post_save(sender: type[Model], instance: SCIMProvider, created: bool, **_):
    """Create service account before provider is saved"""
    identifier = f"ak-providers-scim-{instance.pk}"
    if not instance.auth_oauth:
        return
    user, user_created = User.objects.update_or_create(
        username=identifier,
        defaults={
            "name": f"SCIM Provider {instance.name} Service-Account",
            "type": UserTypes.INTERNAL_SERVICE_ACCOUNT,
            "path": USER_PATH_PROVIDERS_SCIM,
        },
    )
    if created or user_created:
        with audit_ignore():
            instance.user = user
            instance.save()
