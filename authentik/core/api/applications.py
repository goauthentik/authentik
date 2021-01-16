"""Application API Views"""
from django.core.cache import cache
from django.db.models import QuerySet
from django.http.response import Http404
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import SerializerMethodField
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework_guardian.filters import ObjectPermissionsFilter

from authentik.admin.api.metrics import get_events_per_1h
from authentik.core.api.providers import ProviderSerializer
from authentik.core.models import Application
from authentik.events.models import EventAction
from authentik.policies.engine import PolicyEngine


def user_app_cache_key(user_pk: str) -> str:
    """Cache key where application list for user is saved"""
    return f"user_app_cache_{user_pk}"


class ApplicationSerializer(ModelSerializer):
    """Application Serializer"""

    launch_url = SerializerMethodField()
    provider = ProviderSerializer(source="get_provider", required=False)

    def get_launch_url(self, instance: Application) -> str:
        """Get generated launch URL"""
        return instance.get_launch_url() or ""

    class Meta:

        model = Application
        fields = [
            "pk",
            "name",
            "slug",
            "provider",
            "launch_url",
            "meta_launch_url",
            "meta_icon",
            "meta_description",
            "meta_publisher",
            "policies",
        ]


class ApplicationViewSet(ModelViewSet):
    """Application Viewset"""

    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    search_fields = [
        "name",
        "slug",
        "meta_launch_url",
        "meta_description",
        "meta_publisher",
    ]
    lookup_field = "slug"
    ordering = ["name"]

    def _filter_queryset_for_list(self, queryset: QuerySet) -> QuerySet:
        """Custom filter_queryset method which ignores guardian, but still supports sorting"""
        for backend in list(self.filter_backends):
            if backend == ObjectPermissionsFilter:
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def list(self, request: Request) -> Response:
        """Custom list method that checks Policy based access instead of guardian"""
        queryset = self._filter_queryset_for_list(self.get_queryset())
        self.paginate_queryset(queryset)
        allowed_applications = cache.get(user_app_cache_key(self.request.user.pk))
        if not allowed_applications:
            allowed_applications = []
            for application in queryset:
                engine = PolicyEngine(application, self.request.user, self.request)
                engine.build()
                if engine.passing:
                    allowed_applications.append(application)
            cache.set(user_app_cache_key(self.request.user.pk), allowed_applications)
        serializer = self.get_serializer(allowed_applications, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True)
    def metrics(self, request: Request, slug: str):
        """Metrics for application logins"""
        app = get_object_or_404(
            get_objects_for_user(request.user, "authentik_core.view_application"),
            slug=slug,
        )
        if not request.user.has_perm("authentik_events.view_event"):
            raise Http404
        return Response(
            get_events_per_1h(
                action=EventAction.AUTHORIZE_APPLICATION,
                context__authorized_application__pk=app.pk.hex,
            )
        )
