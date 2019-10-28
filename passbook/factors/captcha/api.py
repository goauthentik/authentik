"""CaptchaFactor API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.factors.captcha.models import CaptchaFactor


class CaptchaFactorSerializer(ModelSerializer):
    """CaptchaFactor Serializer"""

    class Meta:

        model = CaptchaFactor
        fields = ['pk', 'name', 'slug', 'order', 'enabled', 'public_key', 'private_key']


class CaptchaFactorViewSet(ModelViewSet):
    """CaptchaFactor Viewset"""

    queryset = CaptchaFactor.objects.all()
    serializer_class = CaptchaFactorSerializer
