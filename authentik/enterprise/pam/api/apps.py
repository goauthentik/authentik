from http import HTTPMethod

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.api.pagination import Pagination
from authentik.core.api.applications import ApplicationSerializer
from authentik.core.apps import AppAccessWithoutBindings
from authentik.core.models import Application, User
from authentik.policies.engine import ListPolicyEngine


def user_can_request(app: Application, user: User, request: Request) -> bool:
    """Whether `user` is eligible to request access to `app`, per the
    PolicyBindingModelRequestRule(s) attached to it. An app with no rule attached at all
    is never requestable, however permissive - a rule is what makes an app requestable
    in the first place."""
    rules = app.request_rules.all()
    if not rules.exists():
        return False
    engine = ListPolicyEngine(rules)
    engine.empty_result = AppAccessWithoutBindings.get()
    return len(list(engine.evaluate_for(user, request))) > 0


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
        all_requestable_apps = self.queryset.filter(request_rules__isnull=False).prefetch_related(
            "request_rules"
        )

        requestable_apps = [
            app for app in all_requestable_apps if user_can_request(app, request.user, request)
        ]

        paginator: Pagination = self.paginator
        paginated_apps = paginator.paginate_queryset(requestable_apps, request)

        serializer = self.get_serializer(paginated_apps, many=True)
        return self.get_paginated_response(serializer.data)
