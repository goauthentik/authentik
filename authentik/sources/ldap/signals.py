"""authentik ldap source signals"""
from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from ldap3.core.exceptions import LDAPOperationResult
from rest_framework.serializers import ValidationError
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.core.signals import password_changed
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.lib.utils.reflection import class_to_path
from authentik.sources.ldap.models import LDAPSource
from authentik.sources.ldap.password import LDAPPasswordChanger
from authentik.sources.ldap.sync.groups import GroupLDAPSynchronizer
from authentik.sources.ldap.sync.membership import MembershipLDAPSynchronizer
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer
from authentik.sources.ldap.tasks import ldap_sync
from authentik.stages.prompt.signals import password_validate

LOGGER = get_logger()


@receiver(post_save, sender=LDAPSource)
def sync_ldap_source_on_save(sender, instance: LDAPSource, **_):
    """Ensure that source is synced on save (if enabled)"""
    if not instance.enabled:
        return
    # Don't sync sources when they don't have any property mappings. This will only happen if:
    # - the user forgets to set them or
    # - the source is newly created, this is the first save event
    #   and the mappings are created with an m2m event
    if not instance.property_mappings.exists() or not instance.property_mappings_group.exists():
        return
    for sync_class in [
        UserLDAPSynchronizer,
        GroupLDAPSynchronizer,
        MembershipLDAPSynchronizer,
    ]:
        ldap_sync.delay(instance.pk, class_to_path(sync_class))


@receiver(password_validate)
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
            raise ValidationError(_("Password does not match Active Directory Complexity."))


@receiver(password_changed)
def ldap_sync_password(sender, user: User, password: str, **_):
    """Connect to ldap and update password."""
    sources = LDAPSource.objects.filter(sync_users_password=True)
    if not sources.exists():
        return
    source = sources.first()
    try:
        changer = LDAPPasswordChanger(source)
        changer.change_password(user, password)
    except LDAPOperationResult as exc:
        LOGGER.warning("failed to set LDAP password", exc=exc)
        Event.new(
            EventAction.CONFIGURATION_ERROR,
            message=(
                "Failed to change password in LDAP source due to remote error: "
                f"{exc.result}, {exc.message}, {exc.description}"
            ),
            source=source,
        ).set_user(user).save()
        raise ValidationError("Failed to set password") from exc
