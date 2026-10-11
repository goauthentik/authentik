"""RBAC Permissions"""

from typing import TYPE_CHECKING

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from guardian.shortcuts import assign_perm
from rest_framework.permissions import DjangoObjectPermissions
from rest_framework.request import Request
from structlog.stdlib import get_logger

from authentik.lib.tracing import active_tracer
from authentik.rbac.endpoint_checks import EndpointChecks
from authentik.rbac.models import InitialPermissions

if TYPE_CHECKING:
    from rest_framework.views import APIView

    from authentik.core.models import User

LOGGER = get_logger()


class ObjectPermissions(DjangoObjectPermissions):
    """Decides API access: authentik's own decision, then the final say of a permission check"""

    @active_tracer().instrument()
    def has_permission(self, request: Request, view: APIView) -> bool:
        if self.are_permission_classes_explicit(view):
            return True
        return EndpointChecks.for_request(request).has_permission(
            self.allows_request(request, view)
        )

    @active_tracer().instrument()
    def has_object_permission(self, request: Request, view: APIView, obj: Model) -> bool:
        if self.are_permission_classes_explicit(view):
            return True
        return EndpointChecks.for_request(request).has_object_permission(
            obj, self.allows_object(request, view, obj)
        )

    def allows_request(self, request: Request, view: APIView) -> bool:
        """authentik's own decision on the request. Unauthenticated users are denied, like
        `DjangoModelPermissions`. Otherwise requests for one object are decided per object:
        viewing by `ObjectFilter`, and changing by `allows_object`"""
        # Check this before the shortcuts below: `ObjectFilter` can't filter by `owner_field`
        # for an anonymous user, and fails with a server error.
        if not request.user or (
            not request.user.is_authenticated and self.authenticated_users_only
        ):
            return False
        if self.is_detail_route(view):
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

    def allows_object(self, request: Request, view: APIView, obj: Model) -> bool:
        """authentik's own decision on one object"""
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
        return super().has_object_permission(request, view, obj)

    @staticmethod
    def is_detail_route(view: APIView) -> bool:
        lookup = getattr(view, "lookup_url_kwarg", None) or getattr(view, "lookup_field", None)
        return bool(lookup and lookup in getattr(view, "kwargs", {}))

    @staticmethod
    def are_permission_classes_explicit(view: APIView) -> bool:
        """Whether the current action declares its permissions with `permission_required`"""
        handler = getattr(view, getattr(view, "action", None) or "", None)
        return getattr(handler, "permission_requirements", None) is not None


def HasPermission(*perm: str) -> type[ObjectPermissions]:
    """Permission checker for any non-object permissions, returns
    a permission class that can be used with rest_framework"""

    class checker(ObjectPermissions):
        def allows_request(self, request: Request, view: APIView) -> bool:
            return bool(request.user and request.user.has_perms(perm))

        def allows_object(self, request: Request, view: APIView, obj: Model) -> bool:
            return True

    return checker


def assign_initial_permissions(user: User, instance: Model):
    # Performance here should not be an issue, but if needed, there are many optimization routes
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
