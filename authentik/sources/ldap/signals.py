"""authentik ldap source signals"""
from typing import Any

from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from ldap3.core.exceptions import LDAPException

from authentik.core.models import User
from authentik.core.signals import password_changed
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.sources.ldap.models import LDAPSource
from authentik.sources.ldap.password import LDAPPasswordChanger
from authentik.sources.ldap.tasks import ldap_sync
from authentik.stages.prompt.signals import password_validate


@receiver(post_save, sender=LDAPSource)
# pylint: disable=unused-argument
def sync_ldap_source_on_save(sender, instance: LDAPSource, **_):
    """Ensure that source is synced on save (if enabled)"""
    if instance.enabled:
        ldap_sync.delay(instance.pk)


@receiver(password_validate)
# pylint: disable=unused-argument
def ldap_password_validate(sender, password: str, plan_context: dict[str, Any], **__):
    """if there's an LDAP Source with enabled password sync, check the password"""
    sources = LDAPSource.objects.filter(sync_users_password=True)
    if not sources.exists():
        return
    source = sources.first()
    changer = LDAPPasswordChanger(source)
    if changer.check_ad_password_complexity_enabled():
        passing = changer.ad_password_complexity(
            password, plan_context.get(PLAN_CONTEXT_PENDING_USER, None)
        )
        if not passing:
            raise ValidationError(
                _("Password does not match Active Direcory Complexity.")
            )


@receiver(password_changed)
# pylint: disable=unused-argument
def ldap_sync_password(sender, user: User, password: str, **_):
    """Connect to ldap and update password. We do this in the background to get
    automatic retries on error."""
    sources = LDAPSource.objects.filter(sync_users_password=True)
    if not sources.exists():
        return
    source = sources.first()
    changer = LDAPPasswordChanger(source)
    try:
        changer.change_password(user, password)
    except LDAPException as exc:
        raise ValidationError("Failed to set password") from exc
