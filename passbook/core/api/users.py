from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.core.models import User


class UserSerializer(ModelSerializer):

    class Meta:

        model = User
        fields = ['pk', 'username', 'name', 'email']


class UserViewSet(ModelViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer
