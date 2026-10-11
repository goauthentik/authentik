"""Permission checks: admin-written Python that has the final say on API access"""

from functools import cached_property

from django.db.models import Model, Q, QuerySet
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from structlog.stdlib import BoundLogger, get_logger

from authentik.rbac.apps import EnableCustomPermissions
from authentik.rbac.endpoints import (
    HAS_OBJECT_PERMISSION,
    HAS_PERMISSION,
    NARROW_LIST,
    WIDEN_LIST,
    Endpoints,
)
from authentik.rbac.models import PermissionCheck

LOGGER = get_logger()
REQUEST_ATTRIBUTE = "endpoint_checks"


class PermissionCheckSkipException(Exception):
    """Raised by has_permission or has_object_permission to immediately grant access"""


class EndpointChecks:
    """The permission check bound to an endpoint, as it applies to one request"""

    def __init__(self, request: Request, endpoint: str | None):
        self.request = request
        self.endpoint = endpoint

    @classmethod
    def for_request(cls, request: Request, action: str | None = None) -> EndpointChecks:
        return cls.for_endpoint(request, Endpoints.endpoint_id(request, action))

    @classmethod
    def for_endpoint(cls, request: Request, endpoint: str | None) -> EndpointChecks:
        checks = request.__dict__.setdefault(REQUEST_ATTRIBUTE, {})
        if endpoint not in checks:
            checks[endpoint] = cls(request, endpoint)
        return checks[endpoint]

    @cached_property
    def bound_check(self) -> PermissionCheck | None:
        if not self.endpoint or PermissionCheck.skipped_for(self.request.user):
            return None
        if not EnableCustomPermissions.get():
            return None
        return PermissionCheck.objects.filter(endpoints__contains=[self.endpoint]).first()

    def defines(self, *functions: str) -> bool:
        """Helper to determine whether the `EndpointCheck` defines all `functions`"""
        if self.bound_check is None:
            return False
        endpoint = Endpoints.hookable().get(self.endpoint)
        return endpoint is not None and any(
            function in endpoint.functions and self.bound_check.defines(function)
            for function in functions
        )

    def has_permission(self, allowed: bool) -> bool:
        """The final decision on the request, given whether authentik allows it"""
        return self.final_decision(HAS_PERMISSION, allowed)

    def has_object_permission(self, obj: Model, allowed: bool) -> bool:
        """The final decision on one object, given whether authentik allows it"""
        return self.final_decision(HAS_OBJECT_PERMISSION, allowed, obj)

    def final_decision(self, function: str, allowed: bool, *objects: Model) -> bool:
        """A check returning True keeps authentik's decision, False forbids, and
        PermissionCheckSkipException grants"""
        if not self.defines(function):
            return allowed
        try:
            result = self.bound_check.run(
                function, self.request, self.endpoint, self.request, *objects
            )
        except PermissionCheckSkipException:
            decision = True
        except PermissionDenied as exc:
            self.logger(function).info("Permission check denied", reason=str(exc.detail))
            raise
        except Exception as exc:  # noqa: BLE001
            self.logger(function).warning("Permission check failed", exc=exc)
            decision = False
        else:
            if not isinstance(result, bool):
                self.logger(function).warning("Permission check did not return a bool")
            decision = allowed if result is True else False
        if decision != allowed:
            self.logger(function).info("Permission check changed decision", decision=decision)
        return decision

    def filter_list(self, visible: QuerySet, everything: QuerySet) -> QuerySet:
        """authentik's list `visible`, narrowed by narrow_list, plus what widen_list picks from
        `everything` the endpoint can list"""
        if self.defines(NARROW_LIST):
            kept = self.run_list_function(NARROW_LIST, visible)
            visible = visible.filter(pk__in=kept.values("pk"))
        if self.defines(WIDEN_LIST):
            added = self.run_list_function(WIDEN_LIST, everything)
            visible = everything.filter(
                Q(pk__in=visible.values("pk")) | Q(pk__in=added.values("pk"))
            )
        return visible

    def run_list_function(self, function: str, queryset: QuerySet) -> QuerySet:
        try:
            result = self.bound_check.run(
                function, self.request, self.endpoint, self.request, queryset
            )
        except PermissionDenied:
            raise
        except Exception as exc:  # noqa: BLE001
            self.logger(function).warning("Permission check failed", exc=exc)
            raise PermissionDenied() from None
        if not isinstance(result, QuerySet) or result.model is not queryset.model:
            self.logger(function).warning("Permission check did not return a queryset of the model")
            raise PermissionDenied()
        return result

    def logger(self, function: str) -> BoundLogger:
        return LOGGER.bind(
            check=self.bound_check.name,
            function=function,
            endpoint=self.endpoint,
            user=self.request.user.username,
        )
