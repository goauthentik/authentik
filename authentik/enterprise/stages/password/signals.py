"""Enterprise password stage signals."""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpRequest

from authentik.core.models import User
from authentik.core.signals import password_changed, password_hash_changed
from authentik.enterprise.stages.password.lockout import unlock_password_login

PASSWORD_CHANGED_MARKER = "_enterprise_password_changed"


@receiver(password_hash_changed)
@receiver(password_changed)
def user_password_changed(
    sender,
    user: User,
    request: HttpRequest | None = None,
    **_,
) -> None:
    """Remember that a persisted password change should clear login state after save."""
    setattr(user, PASSWORD_CHANGED_MARKER, request)


@receiver(post_save, sender=User)
def user_password_post_save(sender, instance: User, **_) -> None:
    """Clear password login state after a password change is persisted."""
    if not hasattr(instance, PASSWORD_CHANGED_MARKER):
        return
    request = getattr(instance, PASSWORD_CHANGED_MARKER)
    unlock_password_login(instance, request=request, reason="password_changed")
    delattr(instance, PASSWORD_CHANGED_MARKER)
