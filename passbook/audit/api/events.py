"""Audit API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from passbook.audit.models import Event


class EventSerializer(ModelSerializer):
    """Event Serializer"""

    class Meta:

        model = Event
        fields = ['pk', 'user', 'action', 'date', 'app', 'context', 'request_ip', 'created', ]


class EventViewSet(ReadOnlyModelViewSet):
    """Event Read-Only Viewset"""

    queryset = Event.objects.all()
    serializer_class = EventSerializer
