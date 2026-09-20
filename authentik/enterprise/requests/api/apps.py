from http import HTTPMethod
from uuid import UUID

from django.db.models import Q, QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.api.ordering import NullsAwareOrderingFilter
from authentik.api.pagination import Pagination
from authentik.api.search.ql import QLSearch
from authentik.core.api.applications import ApplicationSerializer
from authentik.core.api.utils import MetaNameSerializer, PassiveSerializer
from authentik.core.apps import AppAccessWithoutBindings
from authentik.core.models import Application, ApplicationEntitlement, User
from authentik.enterprise.requests.models import RequestRuleBinding, RequestRuleChildBinding
from authentik.policies.engine import ListPolicyEngine
from authentik.policies.models import (
    PolicyBinding,
    PolicyBindingModel,
    RequestableChildModel,
    RequestableModel,
)

REQUESTABLE_FILTER_BACKENDS = [QLSearch, DjangoFilterBackend, NullsAwareOrderingFilter]


def granting_rule_bindings(
    pbms: QuerySet[PolicyBindingModel] | list[PolicyBindingModel] | list[UUID],
    user: User,
    request: Request,
) -> QuerySet[RequestRuleBinding]:
    """The RequestRuleBinding(s) that make any of `pbms` requestable by `user`, i.e.
    `user` passes the rule's own PolicyBindings. `pbms` may be model instances or their
    `pbm_uuid`s."""
    rule_bindings = RequestRuleBinding.objects.filter(
        Q(target__in=pbms) | Q(related__in=pbms)
    ).distinct()
    if not rule_bindings.exists():
        return rule_bindings
    engine = ListPolicyEngine(rule_bindings, user, request)
    engine.empty_result = AppAccessWithoutBindings.get()
    return engine.build().result


def user_can_request(pbm: RequestableModel, user: User, request: Request) -> bool:
    """Whether `user` is eligible to request access to `pbm`, per the
    RequestRule(s) attached to it."""
    return granting_rule_bindings([pbm], user, request).exists()


def _requestable(
    base: QuerySet[RequestableModel | RequestableChildModel], request: Request
) -> QuerySet[RequestableModel]:
    """every unique object of the viewset's own model which the current user is eligible to
    request, direct or child related."""
    # RequestRuleBinding.target/related point at the PolicyBindingModel base table's own pk,
    # which can diverge from a subclass's `.pk` -- same caveat as ListPolicyEngine.build().
    target_field = PolicyBinding._meta.get_field("target").target_field.attname
    candidates = list(
        base.filter(Q(request_rules__isnull=False) | Q(request_rule_child_bindings__isnull=False))
        .values_list(target_field, flat=True)
        .distinct()
    )
    if not candidates:
        return base.none()
    # A rule binding's verdict depends only on (binding, user), never on which object
    # prompted the question, so every candidate is resolved in a single policy pass.
    granting = list(granting_rule_bindings(candidates, request.user, request))
    granted = {binding.target_id for binding in granting}
    granted |= set(
        RequestRuleChildBinding.objects.filter(
            binding__in=granting, target__in=candidates
        ).values_list("target_id", flat=True)
    )
    return base.filter(**{f"{target_field}__in": granted})


class RequestableTargetSerializer(MetaNameSerializer, PassiveSerializer):
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
    @action(methods=[HTTPMethod.GET], detail=False, filter_backends=REQUESTABLE_FILTER_BACKENDS)
    def requestable(self, request: Request) -> Response:
        """List applications which the current user can request access to"""
        paginator: Pagination = self.paginator
        paginated = paginator.paginate_queryset(
            _requestable(self.filter_queryset(self.get_queryset()), request), request
        )
        serializer = self.get_serializer(paginated, many=True)
        return self.get_paginated_response(serializer.data)


class ApplicationEntitlementsRequestableMixin:
    queryset: QuerySet[ApplicationEntitlement]

    @extend_schema(
        responses={
            200: RequestableTargetSerializer(many=True),
        },
    )
    @action(methods=[HTTPMethod.GET], detail=False, filter_backends=REQUESTABLE_FILTER_BACKENDS)
    def requestable(self, request: Request) -> Response:
        """List application entitlements which the current user can request access to"""
        paginator: Pagination = self.paginator
        paginated = paginator.paginate_queryset(
            _requestable(self.filter_queryset(self.get_queryset()), request), request
        )
        serializer = RequestableTargetSerializer(paginated, many=True)
        return self.get_paginated_response(serializer.data)
