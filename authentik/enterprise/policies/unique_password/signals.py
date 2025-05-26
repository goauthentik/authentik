"""authentik policy signals"""

from django.dispatch import receiver

from authentik.core.models import User
from authentik.core.signals import password_changed
from authentik.enterprise.policies.unique_password.models import (
    UniquePasswordPolicy,
    UserPasswordHistory,
)


@receiver(password_changed)
def copy_password_to_password_history(sender, user: User, *args, **kwargs):
    """Preserve the user's old password if UniquePasswordPolicy is enabled anywhere"""
    # Check if any UniquePasswordPolicy is in use
    unique_pwd_policy_in_use = UniquePasswordPolicy.is_in_use()

    if unique_pwd_policy_in_use:
        """NOTE: Because we run this in a signal after saving the user,
        we are not atomically guaranteed to save password history.
        """
        UserPasswordHistory.create_for_user(user, user.password)
