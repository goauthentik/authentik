"""Outpost API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.outposts.models import Outpost


class OutpostSerializer(ModelSerializer):
    """Outpost Serializer"""

    class Meta:

        model = Outpost
        fields = ["pk", "name", "providers"]


class OutpostViewSet(ModelViewSet):
    """Outpost Viewset"""

    queryset = Outpost.objects.all()
    serializer_class = OutpostSerializer
