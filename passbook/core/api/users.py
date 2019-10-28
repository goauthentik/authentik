"""User API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.core.models import User


class UserSerializer(ModelSerializer):
    """User Serializer"""

    class Meta:

        model = User
        fields = ['pk', 'username', 'name', 'email']


class UserViewSet(ModelViewSet):
    """User Viewset"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
