from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.core.models import Group


class GroupSerializer(ModelSerializer):

    class Meta:

        model = Group
        fields = ['pk', 'name', 'parent', 'user_set', 'attributes']


class GroupViewSet(ModelViewSet):

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
