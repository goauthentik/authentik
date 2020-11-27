"""Application API Views"""
from django.db.models import QuerySet
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework_guardian.filters import ObjectPermissionsFilter

from passbook.admin.api.overview_metrics import get_events_per_1h
from passbook.audit.models import EventAction
from passbook.core.models import Application
from passbook.policies.engine import PolicyEngine


class ApplicationSerializer(ModelSerializer):
    """Application Serializer"""

    class Meta:

        model = Application
        fields = [
            "pk",
            "name",
            "slug",
            "provider",
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
    lookup_field = "slug"

    def _filter_queryset_for_list(self, queryset: QuerySet) -> QuerySet:
        """Custom filter_queryset method which ignores guardian, but still supports sorting"""
        for backend in list(self.filter_backends):
            if backend == ObjectPermissionsFilter:
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def list(self, request: Request, *args, **kwargs) -> Response:
        """Custom list method that checks Policy based access instead of guardian"""
        if request.user.is_superuser:
            # pylint: disable=no-member
            return super().list(request, *args, **kwargs)
        queryset = self._filter_queryset_for_list(self.get_queryset())
        self.paginate_queryset(queryset)
        allowed_applications = []
        for application in queryset.order_by("name"):
            engine = PolicyEngine(application, self.request.user, self.request)
            engine.build()
            if engine.passing:
                allowed_applications.append(application)
        serializer = self.get_serializer(allowed_applications, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True)
    def metrics(self, request: Request, slug: str):
        # TODO: Check app read and audit read perms
        app = Application.objects.get(slug=slug)
        return Response(
            get_events_per_1h(
                action=EventAction.AUTHORIZE_APPLICATION,
                context__authorized_application__pk=app.pk.hex,
            )
        )
