"""Permission checks: admin-written Python that has the final say on API access"""

from functools import cached_property
from hashlib import sha256
from typing import Any

from django.core.cache import cache
from django.db.models import Model, Q, QuerySet
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.request import Request
from structlog.stdlib import BoundLogger, get_logger

from authentik.rbac.apps import EnableCustomPermissions
from authentik.rbac.endpoints import (
    HAS_OBJECT_PERMISSION,
    HAS_PERMISSION,
    HIDDEN_FIELDS,
    NARROW_LIST,
    READONLY_FIELDS,
    WIDEN_LIST,
    Endpoints,
)
from authentik.rbac.field_rules import FieldRules
from authentik.rbac.models import PermissionCheck

LOGGER = get_logger()
REQUEST_ATTRIBUTE = "endpoint_checks"
UNKNOWN_FIELDS_KEY = "goauthentik.io/rbac/permission_checks/{check}/{expression}/{endpoint}"
UNKNOWN_FIELDS_TIMEOUT = 60 * 60 * 24


class PermissionCheckSkipException(Exception):
    """Raised by has_permission or has_object_permission to immediately grant access"""


class PermissionCheckFailed(APIException):
    default_detail = _("A permission check failed.")


class EndpointChecks:
    """The permission check bound to an endpoint, as it applies to one request"""

    def __init__(self, request: Request, endpoint: str | None):
        self.request = request
        self.endpoint = endpoint
        self.field_rules_by_object: dict[Any, FieldRules] = {}
        self.reported_fields: set[str] = set()

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

    def field_rules(self, obj: Model | None = None) -> FieldRules:
        """What hidden_fields and readonly_fields protect on one object, or with `obj=None` on
        any object of the endpoint"""
        if not self.defines(HIDDEN_FIELDS, READONLY_FIELDS):
            return FieldRules()
        key = None if obj is None else obj.pk
        if key not in self.field_rules_by_object:
            rules = FieldRules(
                self.field_paths(HIDDEN_FIELDS, obj), self.field_paths(READONLY_FIELDS, obj)
            )
            if key is not None:
                hidden = FieldRules.without_selectors(rules.hidden)
                if not hidden <= FieldRules.without_selectors(self.field_rules().hidden):
                    self.logger(HIDDEN_FIELDS).warning("hidden_fields hides more on one object")
                    raise PermissionCheckFailed()
            self.field_rules_by_object[key] = rules
        return self.field_rules_by_object[key]

    def report_unknown_fields(self, fields: set[str]):
        """Log fields that paths start with but the endpoint lacks, likely typos, and note them
        for the check's form"""
        new = fields - self.reported_fields
        if not new or self.bound_check is None:
            return
        self.reported_fields |= new
        self.logger(HIDDEN_FIELDS).warning("Field rules name fields the endpoint lacks", fields=new)
        key = self.unknown_fields_key(self.bound_check, self.endpoint)
        cache.set(key, sorted(set(cache.get(key, [])) | new), UNKNOWN_FIELDS_TIMEOUT)

    @staticmethod
    def unknown_fields_key(check: PermissionCheck, endpoint: str) -> str:
        expression = sha256(check.expression.encode()).hexdigest()[:16]
        return UNKNOWN_FIELDS_KEY.format(check=check.pk, expression=expression, endpoint=endpoint)

    def field_paths(self, function: str, obj: Model | None) -> set[str]:
        if not self.defines(function):
            return set()
        try:
            paths = self.bound_check.run(function, self.request, self.endpoint, self.request, obj)
        except PermissionDenied:
            raise
        except Exception as exc:  # noqa: BLE001
            self.logger(function).warning("Permission check failed", exc=exc)
            raise PermissionCheckFailed() from None
        if not isinstance(paths, set | list | tuple) or not all(
            isinstance(path, str) for path in paths
        ):
            self.logger(function).warning("Permission check did not return a set of paths")
            raise PermissionCheckFailed()
        return set(paths)

    def logger(self, function: str) -> BoundLogger:
        return LOGGER.bind(
            check=self.bound_check.name,
            function=function,
            endpoint=self.endpoint,
            user=self.request.user.username,
        )
