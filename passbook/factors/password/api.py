"""PasswordFactor API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.factors.password.models import PasswordFactor


class PasswordFactorSerializer(ModelSerializer):
    """PasswordFactor Serializer"""

    class Meta:

        model = PasswordFactor
        fields = ['pk', 'name', 'slug', 'order', 'enabled',
                  'backends', 'password_policies', 'reset_factors']


class PasswordFactorViewSet(ModelViewSet):
    """PasswordFactor Viewset"""

    queryset = PasswordFactor.objects.all()
    serializer_class = PasswordFactorSerializer
