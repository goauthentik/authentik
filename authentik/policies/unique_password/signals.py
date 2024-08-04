"""authentik policy signals"""

from django.db.models.signals import post_delete
from django.dispatch import receiver

from authentik.policies.models import PolicyBinding
from authentik.policies.unique_password.tasks import purge_password_history_table


@receiver(post_delete, sender=PolicyBinding)
def purge_password_history(sender, instance, **_):
    from authentik.policies.unique_password.models import UniquePasswordPolicy

    if not isinstance(instance.policy, UniquePasswordPolicy):
        return

    unique_password_policies = UniquePasswordPolicy.objects.all()

    policy_binding_qs = PolicyBinding.objects.filter(policy__in=unique_password_policies).filter(
        enabled=True
    )

    if policy_binding_qs.count() > 1:
        # No-op; A UniquePasswordPolicy binding other than the one being deleted still exists
        return
    purge_password_history_table.delay()
