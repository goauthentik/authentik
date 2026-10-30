"""RBAC Permissions"""

from typing import TYPE_CHECKING

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from guardian.shortcuts import assign_perm
from rest_framework.permissions import BasePermission, DjangoObjectPermissions
from rest_framework.request import Request
from structlog.stdlib import get_logger

from authentik.lib.tracing import active_tracer
from authentik.rbac.models import InitialPermissions

if TYPE_CHECKING:
    from authentik.core.models import User

LOGGER = get_logger()


class ObjectPermissions(DjangoObjectPermissions):
    """RBAC Permissions"""

    @active_tracer().instrument()
    def has_permission(self, request: Request, view) -> bool:
        """Deny unauthenticated users, like `DjangoModelPermissions`. For authenticated users,
        always grant permission for object-specific requests, as view permission checking
        is done by `ObjectFilter`, and write permission checking is done by
        `has_object_permission`"""
        # Check this before the shortcuts below: `ObjectFilter` can't filter by `owner_field`
        # for an anonymous user, and fails with a server error.
        if not request.user or (
            not request.user.is_authenticated and self.authenticated_users_only
        ):
            return False
        lookup = getattr(view, "lookup_url_kwarg", None) or getattr(view, "lookup_field", None)
        if lookup and lookup in view.kwargs:
            return True
        # Legacy behavior:
        # Allow creation of objects even without explicit permission
        queryset = self._queryset(view)
        required_perms = self.get_required_permissions(request.method, queryset.model)
        if (
            len(required_perms) == 1
            and f"{queryset.model._meta.app_label}.add_{queryset.model._meta.model_name}"
            in required_perms
            and getattr(view, "rbac_allow_create_without_perm", False)
        ):
            return True
        return super().has_permission(request, view)

    @active_tracer().instrument()
    def has_object_permission(self, request: Request, view, obj: Model) -> bool:
        queryset = self._queryset(view)
        model_cls = queryset.model
        perms = self.get_required_object_permissions(request.method, model_cls)
        # Rank global permissions higher than per-object permissions
        if request.user.has_perms(perms):
            return True
        # Allow access for owners if configured
        if owner_field := getattr(view, "owner_field", None):
            if getattr(obj, owner_field) == request.user:
                return True
        # Not `super()`, which checks the queryset model's `perms` on `obj` unchanged, see
        # `permission_for_object`. `perms_map` requires no permissions for safe methods, so
        # `super()`'s 404 case never applies here.
        return request.user.has_perms([permission_for_object(perm, obj) for perm in perms], obj)


def permission_for_object(perm: str, obj: Model) -> str:
    """Translate `perm` into the permission object-level grants on `obj` are stored under.

    Viewsets over a base model with subclasses, like `/policies/all/`, return the subclass
    from `get_object()`, and guardian stores object permissions under the subclass's content
    type. A default permission of a parent model (`authentik_policies.view_policy`) becomes
    the subclass's (`authentik_policies_expression.view_expressionpolicy`), which is what the
    subclass's own viewset checks. guardian raises `WrongAppError` for the parent's
    permission when the subclass is in another app."""
    if "." not in perm:
        return perm
    app_label, codename = perm.split(".", 1)
    # guardian files grants on a proxy model's instances under the concrete model
    opts = obj._meta.concrete_model._meta
    for parent in opts.get_parent_list():
        if parent._meta.app_label != app_label:
            continue
        for action in parent._meta.default_permissions:
            if codename == f"{action}_{parent._meta.model_name}":
                return f"{opts.app_label}.{action}_{opts.model_name}"
    return perm


def HasPermission(*perm: str) -> type[BasePermission]:
    """Permission checker for any non-object permissions, returns
    a BasePermission class that can be used with rest_framework"""

    class checker(BasePermission):
        def has_permission(self, request: Request, view):
            return bool(request.user and request.user.has_perms(perm))

    return checker


def assign_initial_permissions(user: User, instance: Model):
    # Cheap check first, as this runs for every object created in a request
    content_type = ContentType.objects.get_for_model(instance)
    if not InitialPermissions.objects.filter(permissions__content_type=content_type).exists():
        return
    initial_permissions_list = InitialPermissions.objects.filter(role__in=user.all_roles())
    for initial_permissions in initial_permissions_list:
        for permission in initial_permissions.permissions.all():
            if permission.content_type != ContentType.objects.get_for_model(instance):
                continue
            LOGGER.debug(
                "Adding initial permission",
                initial_permission=permission,
                subject=initial_permissions.role,
                object=instance,
            )
            assign_perm(permission, initial_permissions.role, instance)
