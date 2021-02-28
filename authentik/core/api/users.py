"""User API Views"""
from drf_yasg2.utils import swagger_auto_schema
from guardian.utils import get_anonymous_user
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BooleanField, ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.models import User


class UserSerializer(ModelSerializer):
    """User Serializer"""

    is_superuser = BooleanField(read_only=True)
    avatar = CharField(read_only=True)

    class Meta:

        model = User
        fields = [
            "pk",
            "username",
            "name",
            "is_active",
            "last_login",
            "is_superuser",
            "email",
            "avatar",
            "attributes",
        ]


class UserViewSet(ModelViewSet):
    """User Viewset"""

    queryset = User.objects.none()
    serializer_class = UserSerializer
    search_fields = ["username", "name", "is_active"]
    filterset_fields = ["username", "name", "is_active"]

    def get_queryset(self):
        return User.objects.all().exclude(pk=get_anonymous_user().pk)

    @swagger_auto_schema(responses={200: UserSerializer(many=False)})
    @action(detail=False)
    # pylint: disable=invalid-name
    def me(self, request: Request) -> Response:
        """Get information about current user"""
        return Response(UserSerializer(request.user).data)
