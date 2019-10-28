"""OTPFactor API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.factors.otp.models import OTPFactor


class OTPFactorSerializer(ModelSerializer):
    """OTPFactor Serializer"""

    class Meta:

        model = OTPFactor
        fields = ['pk', 'name', 'slug', 'order', 'enabled', 'enforced']


class OTPFactorViewSet(ModelViewSet):
    """OTPFactor Viewset"""

    queryset = OTPFactor.objects.all()
    serializer_class = OTPFactorSerializer
