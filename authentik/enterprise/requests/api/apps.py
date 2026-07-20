from http import HTTPMethod
from typing import TYPE_CHECKING

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentik.api.pagination import Pagination
from authentik.core.api.applications import ApplicationSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.core.apps import AppAccessWithoutBindings
from authentik.core.models import Application, ApplicationEntitlement, User
from authentik.policies.engine import ListPolicyEngine
from authentik.policies.models import PolicyBindingModel, RequestableModel

if TYPE_CHECKING:
    from authentik.enterprise.requests.models import RequestRule


def granting_rule_bindings(
    pbms: QuerySet[PolicyBindingModel] | list[PolicyBindingModel],
    user: User,
    request: Request,
) -> QuerySet[RequestRule]:
    """The RequestRule(s) that make any of `pbms` requestable by `user`, i.e. `user`
    passes the rule's own PolicyBindings. A pbm with no rule attached at all
    contributes nothing."""
    from authentik.enterprise.requests.models import RequestRuleBinding

    rule_bindings = RequestRuleBinding.objects.filter(target__in=pbms)
    if not rule_bindings.exists():
        return rule_bindings
    engine = ListPolicyEngine(rule_bindings, user, request)
    engine.empty_result = AppAccessWithoutBindings.get()
    return engine.build().result


def user_can_request(pbm: RequestableModel, user: User, request: Request) -> bool:
    """Whether `user` is eligible to request access to `pbm`, per the
    RequestRule(s) attached to it. An object with no rule attached at all
    is never requestable"""
    return granting_rule_bindings([pbm], user, request).exists()


def _requestable(view: GenericViewSet, request: Request) -> list[RequestableModel]:
    """every object of the viewset's own model which the current user is eligible to request"""
    all_objects = view.queryset.filter(request_rules__isnull=False).prefetch_related(
        "request_rules"
    )
    return [obj for obj in all_objects if user_can_request(obj, request.user, request)]


class RequestableTargetSerializer(PassiveSerializer):
    """Generic representation of a single request target: whatever was actually
    requested (an Application, an Application Entitlement, ...), always paired with the
    parent it belongs to, so the UI/audit trail has that context even when the
    request itself was scoped narrower than the whole app."""

    pbm_uuid = CharField(source="pk", read_only=True)
    label = CharField(source="requestable_label", read_only=True)
    parent = ApplicationSerializer(source="requestable_parent", read_only=True, allow_null=True)


class ApplicationsRequestableMixin:
    queryset: QuerySet[Application]

    @extend_schema(
        responses={
            200: ApplicationSerializer(many=True),
        },
    )
    @action(methods=[HTTPMethod.GET], detail=False)
    def requestable(self, request: Request) -> Response:
        """List applications which the current user can request access to"""
        paginator: Pagination = self.paginator
        paginated = paginator.paginate_queryset(_requestable(self, request), request)
        serializer = self.get_serializer(paginated, many=True)
        return self.get_paginated_response(serializer.data)


class ApplicationEntitlementsRequestableMixin:
    queryset: QuerySet[ApplicationEntitlement]

    @extend_schema(
        responses={
            200: RequestableTargetSerializer(many=True),
        },
    )
    @action(methods=[HTTPMethod.GET], detail=False)
    def requestable(self, request: Request) -> Response:
        """List application entitlements which the current user can request access to"""
        paginator: Pagination = self.paginator
        paginated = paginator.paginate_queryset(_requestable(self, request), request)
        serializer = RequestableTargetSerializer(paginated, many=True)
        return self.get_paginated_response(serializer.data)
