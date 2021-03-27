"""Groups API Viewset"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.users import UserSerializer
from authentik.core.models import Group


class GroupSerializer(ModelSerializer):
    """Group Serializer"""

    users = UserSerializer(many=True)

    class Meta:

        model = Group
        fields = ["pk", "name", "is_superuser", "parent", "users", "attributes"]
        depth = 2


class GroupViewSet(ModelViewSet):
    """Group Viewset"""

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    search_fields = ["name", "is_superuser"]
    filterset_fields = ["name", "is_superuser"]
    ordering = ["name"]
