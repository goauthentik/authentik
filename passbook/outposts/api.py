"""Outpost API Views"""
from rest_framework.serializers import JSONField, ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.outposts.models import Outpost


class OutpostSerializer(ModelSerializer):
    """Outpost Serializer"""

    config = JSONField()

    class Meta:

        model = Outpost
        fields = ["pk", "name", "providers", "config"]


class OutpostViewSet(ModelViewSet):
    """Outpost Viewset"""

    queryset = Outpost.objects.all()
    serializer_class = OutpostSerializer
