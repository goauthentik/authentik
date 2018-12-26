"""passbook admin gorup API"""
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.viewsets import ModelViewSet

from passbook.core.models import Group


class RecursiveField(Serializer):
    """Recursive field for manytomanyfield"""

    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data

    def create(self):
        raise NotImplementedError()

    def update(self):
        raise NotImplementedError()

class GroupSerializer(ModelSerializer):
    """Group Serializer"""

    children = RecursiveField(many=True)

    class Meta:
        model = Group
        fields = '__all__'

class GroupViewSet(ModelViewSet):
    """Group Viewset"""

    permission_classes = [IsAdminUser]
    serializer_class = GroupSerializer
    queryset = Group.objects.filter(parent__isnull=True)
