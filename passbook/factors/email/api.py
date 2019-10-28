"""EmailFactor API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.factors.email.models import EmailFactor


class EmailFactorSerializer(ModelSerializer):
    """EmailFactor Serializer"""

    class Meta:

        model = EmailFactor
        fields = ['pk', 'name', 'slug', 'order', 'enabled', 'host',
                  'port',
                  'username',
                  'password',
                  'use_tls',
                  'use_ssl',
                  'timeout',
                  'from_address',
                  'ssl_keyfile',
                  'ssl_certfile', ]
        extra_kwargs = {
            'password': {'write_only': True}
        }


class EmailFactorViewSet(ModelViewSet):
    """EmailFactor Viewset"""

    queryset = EmailFactor.objects.all()
    serializer_class = EmailFactorSerializer
