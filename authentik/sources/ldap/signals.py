"""authentik ldap source signals"""

from typing import Any

from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import ValidationError
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.core.signals import password_changed
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.sources.ldap.models import LDAPSource
from authentik.sources.ldap.password import LDAPPasswordChanger
from authentik.stages.prompt.signals import password_validate

LOGGER = get_logger()


@receiver(password_validate)
def ldap_password_validate(sender, password: str, plan_context: dict[str, Any], **__):
    """if there's an LDAP Source with enabled password sync, check the password"""
    sources = LDAPSource.objects.filter(sync_users_password=True, enabled=True)
    if not sources.exists():
        return
    source = sources.first()
    user = plan_context.get(PLAN_CONTEXT_PENDING_USER, None)
    if user and not LDAPPasswordChanger.should_check_user(user):
        return
    changer = LDAPPasswordChanger(source)
    if changer.check_ad_password_complexity_enabled():
        passing = changer.ad_password_complexity(password, user)
        if not passing:
            raise ValidationError(_("Password does not match Active Directory Complexity."))


@receiver(password_changed)
def ldap_sync_password(sender, user: User, password: str, **_):
    """Connect to ldap and update password."""
    sources = LDAPSource.objects.filter(sync_users_password=True, enabled=True)
    if not sources.exists():
        return
    source = sources.first()
    if source.pk == getattr(sender, "pk", None):
        return
    if not LDAPPasswordChanger.should_check_user(user):
        return
    from ldap3.core.exceptions import LDAPException, LDAPOperationResult

    try:
        changer = LDAPPasswordChanger(source)
        changer.change_password(user, password)
    except LDAPException as exc:
        LOGGER.warning("failed to set LDAP password", exc=exc)
        if isinstance(exc, LDAPOperationResult):
            message = (
                "Failed to change password in LDAP source due to remote error: "
                f"{exc.result}, {exc.message}, {exc.description}"
            )
        else:
            message = f"Failed to change password in LDAP source: {type(exc).__name__}: {exc}"
        Event.new(
            EventAction.CONFIGURATION_ERROR,
            message=message,
            source=source,
        ).set_user(user).save()
        raise ValidationError("Failed to set password") from exc
