from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.core.models import Application


class ApplicationSerializer(ModelSerializer):

    class Meta:

        model = Application
        fields = ['pk', 'name', 'slug', 'launch_url', 'icon_url',
                  'provider', 'policies', 'skip_authorization']


class ApplicationViewSet(ModelViewSet):

    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
