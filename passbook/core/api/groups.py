"""Groups API Viewset"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.core.models import Group


class GroupSerializer(ModelSerializer):
    """Group Serializer"""

    class Meta:

        model = Group
        fields = ["pk", "name", "is_superuser", "parent", "users", "attributes"]


class GroupViewSet(ModelViewSet):
    """Group Viewset"""

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
