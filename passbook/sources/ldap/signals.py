"""passbook ldap source signals"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from passbook.sources.ldap.models import LDAPSource
from passbook.sources.ldap.tasks import sync_single


@receiver(post_save, sender=LDAPSource)
# pylint: disable=unused-argument
def sync_ldap_source_on_save(sender, instance: LDAPSource, **_):
    """Ensure that source is synced on save (if enabled)"""
    if instance.enabled:
        sync_single.delay(instance.pk)
