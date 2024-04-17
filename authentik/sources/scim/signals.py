from django.db.models import Model
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from authentik.core.models import Token, TokenIntents, User, UserTypes
from authentik.sources.scim.models import SCIMSource


@receiver(pre_save, sender=SCIMSource)
def scim_source_pre_save(sender: type[Model], instance: SCIMSource, **_):
    """Create service account before source is saved"""
    # .service_account_identifier will auto-assign a primary key uuid to the source
    # if none is set yet, just so we can get the identifier before we save
    identifier = instance.service_account_identifier
    user = User.objects.create(
        username=identifier,
        name=f"SCIM Source {instance.name} Service-Account",
        type=UserTypes.SERVICE_ACCOUNT,
    )
    token = Token.objects.create(
        user=user,
        identifier=identifier,
        intent=TokenIntents.INTENT_API,
        expiring=False,
        managed=f"goauthentik.io/sources/scim/{instance.pk}",
    )
    instance.token = token


@receiver(pre_delete, sender=SCIMSource)
def scim_source_pre_delete(sender: type[Model], instance: SCIMSource, **_):
    """Delete SCIM Source service account before deleting source"""
    Token.objects.filter(
        identifier=instance.service_account_identifier, intent=TokenIntents.INTENT_API
    ).delete()
    User.objects.filter(
        username=instance.service_account_identifier, type=UserTypes.SERVICE_ACCOUNT
    ).delete()
