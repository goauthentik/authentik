"""User API Views"""
from rest_framework.serializers import BooleanField, ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.core.models import User


class UserSerializer(ModelSerializer):
    """User Serializer"""

    is_superuser = BooleanField(read_only=True)

    class Meta:

        model = User
        fields = ["pk", "username", "name", "is_superuser", "email"]


class UserViewSet(ModelViewSet):
    """User Viewset"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
