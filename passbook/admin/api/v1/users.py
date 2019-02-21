"""passbook admin user API"""
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.core.models import User


class UserSerializer(ModelSerializer):
    """User Serializer"""

    class Meta:
        model = User
        fields = ['is_superuser', 'username', 'first_name', 'last_name', 'email', 'date_joined',
                  'uuid']


class UserViewSet(ModelViewSet):
    """User Viewset"""

    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.all()
