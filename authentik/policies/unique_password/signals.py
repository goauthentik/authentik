"""authentik policy signals"""

from typing import Any

from django.dispatch import receiver
from django.http import HttpRequest

from authentik.core.middleware import SESSION_KEY_IMPERSONATE_USER
from authentik.core.models import User
from authentik.policies.unique_password.models import UniquePasswordPolicy, UserPasswordHistory
from authentik.stages.user_write.signals import user_write


@receiver(user_write)
def copy_password_to_password_history(
    sender, request: HttpRequest, user: User, data: dict[str, Any], **kwargs
):
    """Preserve the user's old password if UniquePasswordPolicy is enabled anywhere"""

    user_changed_own_password = (
        any("password" in x for x in data.keys())
        and request.user.pk == user.pk
        and SESSION_KEY_IMPERSONATE_USER not in request.session
    )
    if user_changed_own_password:
        # Check if any UniquePasswordPolicy is in use
        unique_pwd_policy_in_use = UniquePasswordPolicy.is_in_use()

        if unique_pwd_policy_in_use:
            """NOTE: Because we run this in a signal after saving the user,
            we are not atomically guaranteed to save password history.
            """
            UserPasswordHistory.objects.create(user=user, old_password=user.password)
