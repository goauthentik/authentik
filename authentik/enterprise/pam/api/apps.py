from http import HTTPMethod

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.api.pagination import Pagination
from authentik.core.api.applications import ApplicationSerializer
from authentik.core.apps import AppAccessWithoutBindings
from authentik.core.models import Application
from authentik.policies.engine import ListPolicyEngine


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

        requestable_apps = []
        for app in all_requestable_apps:
            engine = ListPolicyEngine(app.request_rules.all())
            engine.empty_result = AppAccessWithoutBindings.get()
            applicable_rules = list(engine.evaluate_for(request.user, request))
            if len(applicable_rules) > 0:
                requestable_apps.append(app)

        paginator: Pagination = self.paginator
        paginated_apps = paginator.paginate_queryset(requestable_apps, request)

        serializer = self.get_serializer(paginated_apps, many=True)
        return self.get_paginated_response(serializer.data)
