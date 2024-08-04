"""authentik policy signals"""

from typing import Any

from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.http import HttpRequest

from authentik.core.middleware import SESSION_KEY_IMPERSONATE_USER
from authentik.core.models import User
from authentik.policies.models import PolicyBinding
from authentik.policies.unique_password.tasks import (
    purge_password_history_table,
    trim_user_password_history,
)
from authentik.stages.user_write.signals import user_write


@receiver(post_delete, sender=PolicyBinding)
def purge_password_history(sender, instance, **_):
    from authentik.policies.unique_password.models import UniquePasswordPolicy

    if not isinstance(instance.policy, UniquePasswordPolicy):
        return
    purge_password_history_table.delay()


@receiver(user_write)
def on_user_write(sender, request: HttpRequest, user: User, data: dict[str, Any], **kwargs):
    """Preserve the user's old password if UniquePasswordPolicy is enabled anywhere"""
    from authentik.core.models import UserPasswordHistory
    from authentik.policies.unique_password.models import UniquePasswordPolicy

    user_changed_own_password = (
        any("password" in x for x in data.keys())
        and request.user.pk == user.pk
        and SESSION_KEY_IMPERSONATE_USER not in request.session
    )
    if user_changed_own_password:
        unique_password_policies = UniquePasswordPolicy.objects.all()

        unique_pwd_policy_binding = PolicyBinding.objects.filter(
            policy__in=unique_password_policies
        ).filter(enabled=True)

        if unique_pwd_policy_binding.exists():
            """NOTE: Because we run this in a signal after saving the user, 
            we are not atomically guaranteed to save password history.
            """
            UserPasswordHistory.objects.create(user=user, change={"old_password": user.password})
            trim_user_password_history.delay(user.pk)
