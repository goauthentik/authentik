"""Application API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.core.models import Application


class ApplicationSerializer(ModelSerializer):
    """Application Serializer"""

    class Meta:

        model = Application
        fields = [
            "pk",
            "name",
            "slug",
            "skip_authorization",
            "outlet",
            "meta_launch_url",
            "meta_icon_url",
            "meta_description",
            "meta_publisher",
            "policies",
        ]


class ApplicationViewSet(ModelViewSet):
    """Application Viewset"""

    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
