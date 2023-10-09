"""authentik core signals"""
from django.contrib.auth.models import Group as DjangoGroup
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.sessions.backends.cache import KEY_PREFIX
from django.core.cache import cache
from django.core.signals import Signal
from django.db.models import Model
from django.db.models.signals import m2m_changed, post_save, pre_delete, pre_save
from django.db.transaction import atomic
from django.dispatch import receiver
from django.http.request import HttpRequest
from structlog.stdlib import get_logger

from authentik.core.models import (
    Application,
    AuthenticatedSession,
    BackchannelProvider,
    Group,
    Role,
    User,
)

# Arguments: user: User, password: str
password_changed = Signal()
# Arguments: credentials: dict[str, any], request: HttpRequest, stage: Stage
login_failed = Signal()

LOGGER = get_logger()


@receiver(post_save, sender=Application)
def post_save_application(sender: type[Model], instance, created: bool, **_):
    """Clear user's application cache upon application creation"""
    from authentik.core.api.applications import user_app_cache_key

    if not created:  # pragma: no cover
        return

    # Also delete user application cache
    keys = cache.keys(user_app_cache_key("*"))
    cache.delete_many(keys)


@receiver(user_logged_in)
def user_logged_in_session(sender, request: HttpRequest, user: User, **_):
    """Create an AuthenticatedSession from request"""

    session = AuthenticatedSession.from_request(request, user)
    if session:
        session.save()


@receiver(user_logged_out)
def user_logged_out_session(sender, request: HttpRequest, user: User, **_):
    """Delete AuthenticatedSession if it exists"""
    AuthenticatedSession.objects.filter(session_key=request.session.session_key).delete()


@receiver(pre_delete, sender=AuthenticatedSession)
def authenticated_session_delete(sender: type[Model], instance: "AuthenticatedSession", **_):
    """Delete session when authenticated session is deleted"""
    cache_key = f"{KEY_PREFIX}{instance.session_key}"
    cache.delete(cache_key)


@receiver(pre_save)
def backchannel_provider_pre_save(sender: type[Model], instance: Model, **_):
    """Ensure backchannel providers have is_backchannel set to true"""
    if not isinstance(instance, BackchannelProvider):
        return
    instance.is_backchannel = True


@receiver(pre_save, sender=Role)
def rbac_role_pre_save(sender: type[Role], instance: Role, **_):
    """Ensure role has a group object created for it"""
    if hasattr(instance, "group"):
        return
    group, _ = DjangoGroup.objects.get_or_create(name=instance.name)
    instance.group = group


@receiver(m2m_changed, sender=Group.roles.through)
def rbac_group_role_m2m(sender: type[Group], action: str, instance: Group, reverse: bool, **_):
    """RBAC: Sync group members into roles when roles are assigned"""
    if action not in ["post_add", "post_remove", "post_clear"]:
        return
    with atomic():
        group_users = list(
            instance.children_recursive()
            .exclude(users__isnull=True)
            .values_list("users", flat=True)
        )
        if not group_users:
            return
        for role in instance.roles.all():
            role: Role
            role.group.user_set.set(group_users)
        LOGGER.debug("Updated users in group", group=instance)


@receiver(m2m_changed, sender=Group.users.through)
def rbac_group_users_m2m(
    sender: type[Group], action: str, instance: Group, pk_set: set, reverse: bool, **_
):
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
