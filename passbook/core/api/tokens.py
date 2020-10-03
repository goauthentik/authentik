"""Tokens API Viewset"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.core.models import Token


class TokenSerializer(ModelSerializer):
    """Token Serializer"""

    class Meta:

        model = Token
        fields = ["pk", "identifier", "intent", "user", "description"]


class TokenViewSet(ModelViewSet):
    """Token Viewset"""

    queryset = Token.objects.all()
    lookup_field = "identifier"
    serializer_class = TokenSerializer
