"""OIDC Outlet signals"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from passbook.channels.out_oidc.models import OpenIDOutlet
from passbook.core.models import Application


@receiver(post_save, sender=Application)
# pylint: disable=unused-argument
def on_application_save(sender, instance: Application, **_):
    """Synchronize application's skip_authorization with oidc_client's require_consent"""
    if isinstance(instance.outlet, OpenIDOutlet):
        instance.outlet.oidc_client.require_consent = not instance.skip_authorization
        instance.outlet.oidc_client.save()
