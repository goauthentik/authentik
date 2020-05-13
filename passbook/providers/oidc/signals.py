"""OIDC Provider signals"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from passbook.core.models import Application
from passbook.providers.oidc.models import OpenIDProvider


@receiver(post_save, sender=Application)
# pylint: disable=unused-argument
def on_application_save(sender, instance: Application, **_):
    """Synchronize application's skip_authorization with oidc_client's require_consent"""
    if isinstance(instance.provider, OpenIDProvider):
        instance.provider.oidc_client.require_consent = not instance.skip_authorization
        instance.provider.oidc_client.save()
