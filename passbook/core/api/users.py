"""User API Views"""
from rest_framework.serializers import BooleanField, ModelSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

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

    @action(detail=False)
    def me(self, request: Request) -> Response:
        """Get information about current user"""
        return Response(UserSerializer(request.user).data)
