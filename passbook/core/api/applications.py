"""Application API Views"""
from django.db.models import QuerySet
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework_guardian.filters import ObjectPermissionsFilter

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

    def list(self, request: Request, *_, **__) -> Response:
        """Custom list method that checks Policy based access instead of guardian"""
        queryset = self._filter_queryset_for_list(self.get_queryset())
        allowed_applications = []
        for application in queryset.order_by("name"):
            engine = PolicyEngine(application, self.request.user, self.request)
            engine.build()
            if engine.passing:
                allowed_applications.append(application)
        serializer = self.get_serializer(allowed_applications, many=True)
        return Response(serializer.data)
