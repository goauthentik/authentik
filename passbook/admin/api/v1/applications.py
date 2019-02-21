"""passbook admin application API"""
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.core.models import Application


class ApplicationSerializer(ModelSerializer):
    """Application Serializer"""

    class Meta:
        model = Application
        fields = '__all__'


class ApplicationViewSet(ModelViewSet):
    """Application Viewset"""

    permission_classes = [IsAdminUser]
    serializer_class = ApplicationSerializer
    queryset = Application.objects.all()
