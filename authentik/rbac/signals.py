"""rbac signals"""

from django.contrib.auth.models import Group as DjangoGroup
from django.db.models.signals import m2m_changed, pre_delete, pre_save
from django.db.transaction import atomic
from django.dispatch import receiver
from rest_framework.exceptions import ValidationError
from structlog.stdlib import get_logger

from authentik.core.models import Group
from authentik.rbac.models import Role

LOGGER = get_logger()


@receiver(pre_save, sender=Role)
def rbac_role_pre_save(sender: type[Role], instance: Role, **_):
    """Ensure role has a group object created for it"""
    if hasattr(instance, "group"):
        return
    group, _ = DjangoGroup.objects.get_or_create(name=instance.name)
    instance.group = group


@receiver(pre_delete, sender=Role)
@receiver(pre_delete, sender=Group)
def rbac_pre_delete_cleanup(sender: type[Group] | type[Role], instance: Group | Role, **_):
    """RBAC: remove permissions from users when a group is deleted"""
    if sender == Group:
        for role in instance.roles.all():
            role.group.user_set.clear()
    if sender == Role:
        instance.group.user_set.clear()


@receiver(m2m_changed, sender=Group.roles.through)
def rbac_group_role_m2m(
    sender: type[Group], action: str, instance: Group, reverse: bool, pk_set: set, **_
):
    """RBAC: Sync group members into roles when roles are assigned"""
    if action == "pre_add":
        # Validation: check that any of the added roles are not used in any other groups
        if Group.objects.filter(roles__in=pk_set).exclude(pk=instance.pk).exists():
            raise ValidationError("Roles can only be used with a single group.")
    if action not in ["post_add", "post_remove", "post_clear"]:
        return
    with atomic():
        group_users = (
            Group.objects.filter(group_uuid=instance.group_uuid)
            .with_children_recursive()
            .exclude(users__isnull=True)
            .values_list("users", flat=True)
        )
        for role in Role.objects.filter(pk__in=pk_set):
            if action == "post_add":
                role.group.user_set.add(*group_users)
            # Role(s) in pk_set were removed from group, so remove the users that we added
            if action == "post_remove":
                role.group.user_set.remove(*group_users)
        LOGGER.debug("Updated users in group", group=instance, direction=action, users=group_users)


@receiver(m2m_changed, sender=Group.users.through)
def rbac_group_users_m2m(
    sender: type[Group], action: str, instance: Group, pk_set: set, reverse: bool, **_
):
    """Handle Group/User m2m and mirror it to roles"""
    if action not in ["post_add", "post_remove"]:
        return
    # reverse: instance is a Group, pk_set is a list of user pks
    # non-reverse: instance is a User, pk_set is a list of groups
    with atomic():
        if reverse:
            for role in instance.roles.all():
                role: Role
                if action == "post_add":
                    role.group.user_set.add(*pk_set)
                elif action == "post_remove":
                    role.group.user_set.remove(*pk_set)
        else:
            for group in Group.objects.filter(pk__in=pk_set):
                for role in group.roles.all():
                    role: Role
                    if action == "post_add":
                        role.group.user_set.add(instance)
                    elif action == "post_remove":
                        role.group.user_set.remove(instance)
