from django.db.models import Q
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from authentik.enterprise.lifecycle.models import LifecycleRule, ReviewState


@receiver(post_save, sender=LifecycleRule)
def post_rule_save(sender, instance: LifecycleRule, created: bool, **_):
    from authentik.enterprise.lifecycle.tasks import apply_lifecycle_rule

    apply_lifecycle_rule.send_with_options(
        args=(instance.id,),
        rel_obj=instance,
    )


@receiver(pre_delete, sender=LifecycleRule)
def pre_rule_delete(sender, instance: LifecycleRule, **_):
    instance.lifecycleiteration_set.filter(
        Q(state=ReviewState.PENDING) | Q(state=ReviewState.OVERDUE)
    ).update(state=ReviewState.CANCELED)
