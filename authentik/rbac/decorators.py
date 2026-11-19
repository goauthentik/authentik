"""API Decorators"""

from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.rbac.endpoint_checks import EndpointChecks
from authentik.rbac.permissions import ObjectPermissions


@dataclass
class ActionRequirements:
    """Permissions a custom action needs, decided before it runs"""

    obj_perm: str | None
    global_perms: tuple[str, ...]

    def authorize(self, view: ModelViewSet, request: Request) -> None:
        base = [p for p in view.get_permissions() if isinstance(p, ObjectPermissions)]
        detail = ObjectPermissions.is_detail_route(view)
        allowed = all(request.user.has_perm(perm) for perm in self.global_perms) and all(
            permission.allows_request(request, view) for permission in base
        )
        if self.obj_perm and not detail:
            allowed = allowed and request.user.has_perm(self.obj_perm)
        checks = EndpointChecks.for_request(request)
        if not checks.has_permission(allowed):
            view.permission_denied(request)
        if not detail:
            return
        obj = view.get_object()
        allowed = (not self.obj_perm or request.user.has_perm(self.obj_perm, obj)) and all(
            permission.allows_object(request, view, obj) for permission in base
        )
        if not checks.has_object_permission(obj, allowed):
            view.permission_denied(request)


def permission_required(obj_perm: str | None = None, global_perms: list[str] | None = None):
    """Check permissions for a single custom action"""
    requirements = ActionRequirements(obj_perm, tuple(global_perms or ()))

    def wrapper_outer(func: Callable):
        """Check permissions for a single custom action"""

        @wraps(func)
        def wrapper(self: ModelViewSet, request: Request, *args, **kwargs) -> Response:
            requirements.authorize(self, request)
            return func(self, request, *args, **kwargs)

        wrapper.permission_requirements = requirements
        return wrapper

    return wrapper_outer
