"""User API Views"""
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import (
    BooleanField,
    ModelSerializer,
    SerializerMethodField,
)
from rest_framework.viewsets import ModelViewSet

from passbook.core.models import User
from passbook.lib.templatetags.passbook_utils import avatar


class UserSerializer(ModelSerializer):
    """User Serializer"""

    is_superuser = BooleanField(read_only=True)
    avatar = SerializerMethodField()

    def get_avatar(self, user: User) -> str:
        """Add user's avatar as URL"""
        return avatar(user)

    class Meta:

        model = User
        fields = ["pk", "username", "name", "is_superuser", "email", "avatar"]


class UserViewSet(ModelViewSet):
    """User Viewset"""

    queryset = User.objects.all()
    serializer_class = UserSerializer

    @swagger_auto_schema(responses={200: UserSerializer(many=False)})
    @action(detail=False)
    # pylint: disable=invalid-name
    def me(self, request: Request) -> Response:
        """Get information about current user"""
        return Response(UserSerializer(request.user).data)
