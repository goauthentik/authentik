"""API endpoints permission checks can be bound to"""

from collections.abc import Iterator
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING

from django.urls import URLPattern
from rest_framework.request import Request

if TYPE_CHECKING:
    from rest_framework.viewsets import ViewSet

HAS_PERMISSION = "has_permission"
HAS_OBJECT_PERMISSION = "has_object_permission"
NARROW_LIST = "narrow_list"
WIDEN_LIST = "widen_list"
FUNCTIONS = (
    HAS_PERMISSION,
    HAS_OBJECT_PERMISSION,
    NARROW_LIST,
    WIDEN_LIST,
)

API_PREFIX = "api/v3/"


@dataclass
class Endpoint:
    id: str
    functions: tuple[str, ...]


class Endpoints:
    """
    Technical note: many functions here have late imports to avoid circular dependencies, because
    the API's URLs import this module through the views they route to.
    """

    @staticmethod
    @cache
    def router_prefixes() -> dict[type, str]:
        from authentik.api.v3.urls import router

        return {viewset: prefix for prefix, viewset, basename in router.registry}

    @classmethod
    def endpoint_id(cls, request: Request, action: str | None = None) -> str | None:
        """`<router prefix>:<action>` for viewsets and `<path>:<method>` for other views, or
        with `action` the id of that action of the requested viewset"""
        match = getattr(request, "resolver_match", None)
        if match is None:
            return None
        if prefix := cls.router_prefixes().get(getattr(match.func, "cls", None)):
            action = action or getattr(match.func, "actions", {}).get(request.method.lower())
            return f"{prefix}:{action}" if action else None
        route = match.route or ""
        if action or not route.startswith(API_PREFIX):
            return None
        return f"{route.removeprefix(API_PREFIX).strip('/')}:{request.method.lower()}"

    @classmethod
    def viewset_for(cls, endpoint: str) -> type[ViewSet]:
        prefix = endpoint.rsplit(":", 1)[0]
        return next(viewset for viewset, path in cls.router_prefixes().items() if path == prefix)

    @classmethod
    @cache
    def hookable(cls) -> dict[str, Endpoint]:
        """Every endpoint to which permission checks can be bound, by id"""
        from authentik.api.v3.urls import _other_urls, router

        routes = [pattern for pattern in router.urls if hasattr(pattern.callback, "actions")]
        endpoints = [endpoint for pattern in routes for endpoint in cls.from_route(pattern)]
        endpoints += [endpoint for pattern in _other_urls for endpoint in cls.from_view(pattern)]
        return {endpoint.id: endpoint for endpoint in endpoints}

    @classmethod
    def from_route(cls, pattern: URLPattern) -> Iterator[Endpoint]:
        view = pattern.callback
        viewset = view.cls
        options = view.initkwargs
        prefix = cls.router_prefixes()[viewset]
        permission_classes = options.get("permission_classes", viewset.permission_classes)
        backends = options.get("filter_backends", getattr(viewset, "filter_backends", ()))
        for action in dict.fromkeys(view.actions.values()):
            if not cls.is_hookable(permission_classes, getattr(viewset, action)):
                continue
            functions = [HAS_PERMISSION]
            if options.get("detail"):
                functions.append(HAS_OBJECT_PERMISSION)
            if action == "list" and any(
                issubclass(backend, cls.list_filters()) for backend in backends
            ):
                functions += [NARROW_LIST, WIDEN_LIST]
            yield Endpoint(f"{prefix}:{action}", tuple(functions))

    @classmethod
    def from_view(cls, pattern: URLPattern) -> Iterator[Endpoint]:
        """The endpoints of a view outside the router, one per HTTP method"""
        view = getattr(pattern.callback, "cls", None)
        if view is None or not cls.is_hookable(view.permission_classes, None):
            return
        path = str(pattern.pattern).strip("/")
        functions = (HAS_PERMISSION,)
        for method in view.http_method_names:
            if method != "options" and hasattr(view, method):
                yield Endpoint(f"{path}:{method}", functions)

    @staticmethod
    def is_hookable(permission_classes: list, handler) -> bool:
        from authentik.rbac.permissions import ObjectPermissions

        return getattr(handler, "permission_requirements", None) is not None or any(
            isinstance(cls, type) and issubclass(cls, ObjectPermissions)
            for cls in permission_classes
        )

    @staticmethod
    def list_filters() -> tuple[type, ...]:
        """The filters that run narrow_list and widen_list"""
        from authentik.rbac.filters import ObjectFilter, SecretKeyFilter

        return ObjectFilter, SecretKeyFilter
